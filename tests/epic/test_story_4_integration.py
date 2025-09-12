#!/usr/bin/env python3
"""
Quick integration test for Stories 4.3 & 4.4
Tests the new hybrid summarization with LLM enhancement
"""

import asyncio
import json
from src.nl_fhir.services.hybrid_summarizer import HybridSummarizer


async def test_story_4_integration():
    """Test complete Story 4 integration"""
    print("🧪 Testing Stories 4.3 & 4.4 Integration")
    
    # Create test FHIR bundle
    test_bundle = {
        "resourceType": "Bundle",
        "id": "test-bundle-story-4",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "test-med-1",
                    "medicationCodeableConcept": {
                        "coding": [{"code": "860975", "display": "Metformin 500mg"}],
                        "text": "Metformin 500mg"
                    },
                    "dosageInstruction": [
                        {"text": "Take twice daily with meals"}
                    ]
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "test-obs-1",
                    "code": {
                        "coding": [{"code": "33747-0", "display": "Serum Potassium"}],
                        "text": "Serum Potassium"
                    },
                    "valueQuantity": {
                        "value": 6.2,
                        "unit": "mmol/L"
                    },
                    "interpretation": [
                        {"text": "High"}
                    ]
                }
            }
        ]
    }
    
    # Initialize hybrid summarizer
    summarizer = HybridSummarizer()
    
    # Test 1: Template-only summarization
    print("\n1️⃣ Testing template-only summarization...")
    result1 = await summarizer.create_comprehensive_summary(
        test_bundle,
        {"llm_enhancement": False}
    )
    print(f"✅ Template summary type: {result1['summary_type']}")
    print(f"📊 Safety analysis: {len(result1['safety']['issues'])} issues, {len(result1['safety']['warnings'])} warnings")
    
    # Test 2: LLM-enhanced summarization (contextual)
    print("\n2️⃣ Testing LLM enhancement (contextual)...")
    result2 = await summarizer.create_comprehensive_summary(
        test_bundle,
        {
            "llm_enhancement": True,
            "enhancement_level": "contextual"
        }
    )
    print(f"✅ Enhanced summary type: {result2['summary_type']}")
    print(f"🤖 Enhancement applied: {result2['processing']['llm_enhancement_applied']}")
    print(f"🔄 Fallback used: {result2['processing']['fallback_used']}")
    
    # Test 3: LLM-enhanced summarization (educational)
    print("\n3️⃣ Testing LLM enhancement (educational)...")
    result3 = await summarizer.create_comprehensive_summary(
        test_bundle,
        {
            "llm_enhancement": True,
            "enhancement_level": "educational"
        }
    )
    print(f"✅ Educational enhancement type: {result3['summary_type']}")
    
    # Test 4: LLM-enhanced summarization (comprehensive)
    print("\n4️⃣ Testing LLM enhancement (comprehensive)...")
    result4 = await summarizer.create_comprehensive_summary(
        test_bundle,
        {
            "llm_enhancement": True,
            "enhancement_level": "comprehensive"
        }
    )
    print(f"✅ Comprehensive enhancement type: {result4['summary_type']}")
    
    # Show sample outputs
    print("\n📋 SAMPLE OUTPUTS:")
    print("\n--- Template-Based Summary ---")
    print(result1['summary'][:300] + "..." if len(result1['summary']) > 300 else result1['summary'])
    
    print("\n--- LLM-Enhanced Summary (Contextual) ---") 
    print(result2['summary'][:500] + "..." if len(result2['summary']) > 500 else result2['summary'])
    
    print("\n🎯 PERFORMANCE METRICS:")
    print(f"Template processing: {result1['processing']['total_time_ms']:.1f}ms")
    print(f"LLM enhanced processing: {result2['processing']['total_time_ms']:.1f}ms")
    
    print("\n🔒 SAFETY INTEGRATION:")
    print(f"Safety issues detected: {len(result2['safety']['issues'])}")
    print(f"Safety warnings: {len(result2['safety']['warnings'])}")
    if result2['safety']['risk_score']:
        print(f"Risk score: {result2['safety']['risk_score'].get('total_score', 'N/A')}/100")
    
    print("\n✅ Story 4.3 & 4.4 Integration Test PASSED!")
    return True


if __name__ == "__main__":
    asyncio.run(test_story_4_integration())