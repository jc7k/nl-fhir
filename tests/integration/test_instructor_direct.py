#!/usr/bin/env python3
"""
Direct test of Instructor/OpenAI integration
"""

import os
from src.nl_fhir.services.nlp.llm_processor import LLMProcessor, INSTRUCTOR_AVAILABLE
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def test_instructor_integration():
    """Test Instructor with OpenAI API directly"""
    
    llm_processor = LLMProcessor()
    
    print("🔑 OpenAI API Key configured:", bool(llm_processor.api_key))
    print("📦 Instructor available:", INSTRUCTOR_AVAILABLE)
    print("🤖 Client initialized:", bool(llm_processor.client))
    
    # Initialize the processor
    llm_processor.initialize()
    
    print("🔄 After initialization:")
    print("   API Key:", bool(llm_processor.api_key))
    print("   Client:", bool(llm_processor.client))
    print("   Initialized:", llm_processor.initialized)
    
    # Test with a complex medication that was failing
    test_text_1 = "Initiated patient Julian West on 5mg Tadalafil as needed for erectile dysfunction"
    
    # Test case that should escalate to LLM (very ambiguous/complex)  
    test_text_2 = "Patient needs something for the heart condition we discussed last time"
    
    # Test both scenarios
    test_cases = [
        ("Regex Success", test_text_1),
        ("Should Escalate", test_text_2)
    ]
    
    for test_name, test_text in test_cases:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}: {test_text}")
        
        try:
            result = llm_processor.process_clinical_text(test_text, [], f"test-{test_name.lower()}")
        
            # Check results - get from structured_output not extracted_entities
            structured_output = result.get('structured_output', {})
            medications = structured_output.get('medications', [])
            conditions = structured_output.get('conditions', [])
        
            print(f"\n📊 Results:")
            print(f"   Method used: {result.get('method', 'unknown')}")
            print(f"   Processing time: {result.get('processing_time_ms', 0):.1f}ms")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Medications found: {len(medications)}")
            print(f"   Conditions found: {len(conditions)}")
            
            # Test escalation logic
            should_escalate = llm_processor._should_escalate_to_llm(structured_output, test_text)
            print(f"   Should have escalated to LLM: {should_escalate}")
            
            if medications:
                med_names = [med.get('name', med.get('text', 'unknown')) for med in medications]
                print(f"   Medications: {med_names}")
                
            if conditions:
                cond_names = [cond.get('name', cond.get('text', 'unknown')) for cond in conditions]  
                print(f"   Conditions: {cond_names}")
            
            # Success criteria - check both 'name' and 'text' fields
            has_medication = len(medications) > 0 and any(
                'tadalafil' in str(med.get('name', med.get('text', ''))).lower() 
                for med in medications
            )
            has_condition = len(conditions) > 0 and any(
                'dysfunction' in str(cond.get('name', cond.get('text', ''))).lower() or 
                'erectile' in str(cond.get('name', cond.get('text', ''))).lower() 
                for cond in conditions
            )
        
            if has_medication and has_condition:
                print("\n✅ SUCCESS: Both Tadalafil and erectile dysfunction detected!")
            elif has_medication:
                print("\n🟡 PARTIAL: Tadalafil detected but missing condition")
            elif has_condition:
                print("\n🟡 PARTIAL: Condition detected but missing Tadalafil")  
            else:
                print("\n❌ FAILED: Neither medication nor condition detected properly")
                
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    result = test_instructor_integration()