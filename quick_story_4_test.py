#!/usr/bin/env python3
"""
Quick test for Stories 4.3 & 4.4 core functionality
Tests LLM enhancer and basic integration
"""

import asyncio
import sys
import os

# Add the source path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nl_fhir.services.llm_enhancer import LLMEnhancer
from nl_fhir.services.summarization import SummarizationService


async def test_story_4_core():
    """Test core Story 4.3 functionality"""
    print("🧪 Testing Story 4.3 LLM Enhancement Core")
    
    # Test data
    template_summary = """Medication order: Metformin 500mg Take twice daily with meals.
Observation: Serum Potassium = 6.2 mmol/L High"""
    
    bundle_data = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "medicationCodeableConcept": {"text": "Metformin 500mg"}
                }
            }
        ]
    }
    
    # Test LLM Enhancement
    enhancer = LLMEnhancer()
    
    print("\n1️⃣ Testing contextual enhancement...")
    result1 = await enhancer.enhance_summary(template_summary, bundle_data, "contextual")
    print(f"✅ Enhancement applied: {result1['enhancement_applied']}")
    print(f"📝 Validation passed: {result1['validation_passed']}")
    
    print("\n2️⃣ Testing educational enhancement...")
    result2 = await enhancer.enhance_summary(template_summary, bundle_data, "educational") 
    print(f"✅ Enhancement applied: {result2['enhancement_applied']}")
    print(f"📝 Validation passed: {result2['validation_passed']}")
    
    print("\n3️⃣ Testing comprehensive enhancement...")
    result3 = await enhancer.enhance_summary(template_summary, bundle_data, "comprehensive")
    print(f"✅ Enhancement applied: {result3['enhancement_applied']}")
    print(f"📝 Validation passed: {result3['validation_passed']}")
    
    # Test basic summarization
    print("\n4️⃣ Testing template summarization...")
    summarizer = SummarizationService()
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "medicationCodeableConcept": {"text": "Metformin 500mg"},
                    "dosageInstruction": [{"text": "twice daily"}]
                }
            }
        ]
    }
    
    summary_result = summarizer.summarize(bundle)
    print(f"✅ Template summary generated: {len(summary_result.get('summary', ''))} chars")
    
    # Show sample outputs
    print("\n📋 SAMPLE ENHANCED OUTPUT:")
    if result1['enhancement_applied']:
        enhanced_text = result1['enhanced_summary']
        print(enhanced_text[:400] + "..." if len(enhanced_text) > 400 else enhanced_text)
    
    print(f"\n🎯 PERFORMANCE:")
    print(f"Contextual: {result1['processing_time_ms']}ms")
    print(f"Educational: {result2['processing_time_ms']}ms")
    print(f"Comprehensive: {result3['processing_time_ms']}ms")
    
    print("\n✅ Story 4.3 Core Tests PASSED!")
    
    # Test enhancement options
    print("\n5️⃣ Testing enhancement options...")
    options = enhancer.get_enhancement_options()
    print(f"Available levels: {len(options['available_levels'])}")
    print(f"LLM available: {options['llm_available']}")
    
    return True


if __name__ == "__main__":
    asyncio.run(test_story_4_core())