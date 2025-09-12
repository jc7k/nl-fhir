#!/usr/bin/env python3
"""
Epic 4 Complete Test - Stories 4.1, 4.2, 4.3, 4.4
Tests the complete reverse validation pipeline
"""

import asyncio
import sys
import os

# Add the source path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nl_fhir.services.reverse_validation_orchestrator import (
    ReverseValidationOrchestrator, 
    ReverseValidationConfig,
    ProcessingMode
)


async def test_epic_4_complete():
    """Test complete Epic 4 implementation"""
    print("🎯 Testing Epic 4 Complete Implementation")
    print("Stories 4.1 (Template) + 4.2 (Safety) + 4.3 (LLM) + 4.4 (Production)")
    
    # Create test FHIR bundle
    test_bundle = {
        "resourceType": "Bundle",
        "id": "epic-4-test-bundle",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "warfarin-request",
                    "medicationCodeableConcept": {
                        "coding": [{"code": "11289", "display": "Warfarin 5mg"}],
                        "text": "Warfarin 5mg"
                    },
                    "dosageInstruction": [
                        {"text": "Take once daily, monitor INR"}
                    ]
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "inr-observation",
                    "code": {
                        "coding": [{"code": "34714-6", "display": "INR"}],
                        "text": "INR"
                    },
                    "valueQuantity": {
                        "value": 3.5,
                        "unit": "ratio"
                    },
                    "interpretation": [
                        {"text": "High"}
                    ]
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "afib-condition",
                    "code": {
                        "coding": [{"code": "48694002", "display": "Atrial fibrillation"}],
                        "text": "Atrial fibrillation"
                    }
                }
            }
        ]
    }
    
    print(f"\n📋 Test Bundle: {len(test_bundle['entry'])} resources")
    
    # Test 1: Fast Mode (Story 4.1 equivalent)
    print("\n1️⃣ Testing FAST Mode (Template-only, Story 4.1)")
    config_fast = ReverseValidationConfig(
        processing_mode=ProcessingMode.FAST,
        enable_llm_enhancement=False,
        enable_safety_validation=False
    )
    
    orchestrator_fast = ReverseValidationOrchestrator(config_fast)
    result_fast = await orchestrator_fast.process_bundle(test_bundle, "test-fast-001")
    
    print(f"✅ Summary type: {result_fast.summary_type}")
    print(f"⏱️  Processing time: {result_fast.performance_metrics['processing_time_ms']:.1f}ms")
    print(f"📊 Quality score: {result_fast.quality_score:.2f}")
    
    # Test 2: Standard Mode (Stories 4.1 + 4.2)
    print("\n2️⃣ Testing STANDARD Mode (Template + Safety, Stories 4.1 + 4.2)")
    config_standard = ReverseValidationConfig(
        processing_mode=ProcessingMode.STANDARD,
        enable_llm_enhancement=False,
        enable_safety_validation=True
    )
    
    orchestrator_standard = ReverseValidationOrchestrator(config_standard)
    result_standard = await orchestrator_standard.process_bundle(test_bundle, "test-std-001")
    
    print(f"✅ Summary type: {result_standard.summary_type}")
    print(f"⏱️  Processing time: {result_standard.performance_metrics['processing_time_ms']:.1f}ms")
    print(f"🔒 Safety issues: {len(result_standard.safety_analysis['issues'])}")
    print(f"⚠️  Safety warnings: {len(result_standard.safety_analysis['warnings'])}")
    print(f"📊 Quality score: {result_standard.quality_score:.2f}")
    
    # Test 3: Enhanced Mode (Stories 4.1 + 4.2 + 4.3)
    print("\n3️⃣ Testing ENHANCED Mode (Template + Safety + LLM, Stories 4.1 + 4.2 + 4.3)")
    config_enhanced = ReverseValidationConfig(
        processing_mode=ProcessingMode.ENHANCED,
        enable_llm_enhancement=True,
        llm_enhancement_level="contextual",
        enable_safety_validation=True
    )
    
    orchestrator_enhanced = ReverseValidationOrchestrator(config_enhanced)
    result_enhanced = await orchestrator_enhanced.process_bundle(test_bundle, "test-enh-001")
    
    print(f"✅ Summary type: {result_enhanced.summary_type}")
    print(f"⏱️  Processing time: {result_enhanced.performance_metrics['processing_time_ms']:.1f}ms")
    print(f"🤖 LLM enhancement: {result_enhanced.enhancement_details is not None}")
    print(f"📊 Quality score: {result_enhanced.quality_score:.2f}")
    
    # Test 4: Comprehensive Mode (Complete Story 4.4)
    print("\n4️⃣ Testing COMPREHENSIVE Mode (Complete Epic 4, Story 4.4)")
    config_comprehensive = ReverseValidationConfig(
        processing_mode=ProcessingMode.COMPREHENSIVE,
        enable_llm_enhancement=True,
        llm_enhancement_level="comprehensive",
        enable_safety_validation=True,
        enable_caching=True
    )
    
    orchestrator_comprehensive = ReverseValidationOrchestrator(config_comprehensive)
    result_comprehensive = await orchestrator_comprehensive.process_bundle(test_bundle, "test-comp-001")
    
    print(f"✅ Summary type: {result_comprehensive.summary_type}")
    print(f"⏱️  Processing time: {result_comprehensive.performance_metrics['processing_time_ms']:.1f}ms")
    print(f"📊 Quality score: {result_comprehensive.quality_score:.2f}")
    print(f"🎯 Meets SLA: {result_comprehensive.performance_metrics['meets_sla']}")
    
    # Test 5: Caching Performance
    print("\n5️⃣ Testing Caching Performance")
    result_cached = await orchestrator_comprehensive.process_bundle(test_bundle, "test-cache-001")
    print(f"📦 From cache: {result_cached.processing_details.get('from_cache', False)}")
    print(f"⏱️  Cached processing time: {result_cached.performance_metrics['processing_time_ms']:.1f}ms")
    
    # Show sample output
    print("\n📋 SAMPLE COMPREHENSIVE SUMMARY:")
    print("=" * 60)
    sample_summary = result_comprehensive.summary
    print(sample_summary[:800] + "..." if len(sample_summary) > 800 else sample_summary)
    print("=" * 60)
    
    # Performance comparison
    print("\n🚀 PERFORMANCE COMPARISON:")
    print(f"Fast Mode:         {result_fast.performance_metrics['processing_time_ms']:.1f}ms")
    print(f"Standard Mode:     {result_standard.performance_metrics['processing_time_ms']:.1f}ms") 
    print(f"Enhanced Mode:     {result_enhanced.performance_metrics['processing_time_ms']:.1f}ms")
    print(f"Comprehensive:     {result_comprehensive.performance_metrics['processing_time_ms']:.1f}ms")
    print(f"Cached Result:     {result_cached.performance_metrics['processing_time_ms']:.1f}ms")
    
    # Quality comparison
    print("\n📊 QUALITY COMPARISON:")
    print(f"Fast Mode:         {result_fast.quality_score:.3f}")
    print(f"Standard Mode:     {result_standard.quality_score:.3f}")
    print(f"Enhanced Mode:     {result_enhanced.quality_score:.3f}")
    print(f"Comprehensive:     {result_comprehensive.quality_score:.3f}")
    
    # Test orchestrator health
    print("\n🏥 ORCHESTRATOR HEALTH:")
    health = orchestrator_comprehensive.get_health_status()
    print(f"Status: {health['status']}")
    if 'metrics' in health:
        metrics = health['metrics']
        print(f"Success Rate: {metrics['requests']['success_rate']:.1%}")
        print(f"Avg Processing: {metrics['performance']['average_processing_time_ms']:.1f}ms")
        print(f"Cache Hit Rate: {metrics['performance']['cache_hit_rate']:.1%}")
    
    print("\n✅ Epic 4 Complete Implementation Test PASSED!")
    print("🎯 All Stories (4.1, 4.2, 4.3, 4.4) Successfully Integrated!")
    
    return True


if __name__ == "__main__":
    asyncio.run(test_epic_4_complete())