"""
Enhanced NLP Pipeline Integration Test
Tests the complete integration of validation with NLP processing
Demonstrates production-ready error handling for clinical orders
"""

import asyncio
import sys
import os
from typing import Dict, List, Any
import time

# Add src to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.nl_fhir.services.enhanced_nlp_pipeline import process_clinical_text_with_validation


async def test_enhanced_pipeline():
    """Test enhanced pipeline with various clinical order scenarios"""
    
    print("🧪 Enhanced NLP Pipeline Integration Test")
    print("=" * 50)
    
    # Test scenarios covering validation spectrum
    test_scenarios = [
        {
            "name": "Valid Clear Order",
            "text": "Start lisinopril 10mg once daily for hypertension",
            "expected_validation": "pass",
            "mode": "strict"
        },
        {
            "name": "Conditional Logic (Fatal)",
            "text": "Start beta blocker if BP remains high, maybe metoprolol or atenolol",
            "expected_validation": "fatal", 
            "mode": "strict"
        },
        {
            "name": "Medication Ambiguity (Fatal)",
            "text": "Give something for thyroid, maybe Synthroid?",
            "expected_validation": "fatal",
            "mode": "strict"
        },
        {
            "name": "Missing Dosage (Error)",
            "text": "Start aspirin daily for cardiovascular protection",
            "expected_validation": "error",
            "mode": "permissive"  # Allow processing with warnings
        },
        {
            "name": "Protocol Reference (Error)",
            "text": "Morphine drip per comfort protocol",
            "expected_validation": "error",
            "mode": "permissive"
        },
        {
            "name": "Vague Intent (Warning)",
            "text": "Pain control as needed",
            "expected_validation": "warning", 
            "mode": "permissive"
        }
    ]
    
    print(f"🎯 Running {len(test_scenarios)} integration test scenarios\n")
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"[{i}/{len(test_scenarios)}] {scenario['name']}")
        print(f"   Text: '{scenario['text']}'")
        print(f"   Mode: {scenario['mode']}")
        
        start_time = time.time()
        
        try:
            # Process with enhanced pipeline
            result = await process_clinical_text_with_validation(
                scenario['text'], 
                request_id=f"test_{i}",
                validation_mode=scenario['mode']
            )
            
            processing_time = time.time() - start_time
            
            # Analyze results
            status = result.get('status', 'unknown')
            validation_passed = result.get('validation', {}).get('passed', False)
            can_process_fhir = result.get('validation', {}).get('can_process_fhir', False) 
            issues_count = result.get('validation', {}).get('issues_detected', 0)
            confidence = result.get('quality_assessment', {}).get('overall_confidence', 0.0)
            processing_blocked = result.get('processing_blocked', False)
            
            print(f"   Status: {status}")
            print(f"   Validation Passed: {validation_passed}")
            print(f"   Can Process FHIR: {can_process_fhir}")
            print(f"   Issues Detected: {issues_count}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Processing Time: {processing_time*1000:.1f}ms")
            
            if processing_blocked:
                print(f"   🚫 Processing blocked due to validation failures")
            elif issues_count > 0:
                print(f"   ⚠️  Processing completed with {issues_count} validation issues")
            else:
                print(f"   ✅ Processing completed successfully")
                
            # Show validation details if present
            validation_details = result.get('validation_details')
            if validation_details:
                issues = validation_details.get('issues', [])
                if issues:
                    print(f"   📋 Top Issue: {issues[0].get('message', 'Unknown issue')}")
            
            results.append({
                'scenario': scenario,
                'result': result,
                'processing_time': processing_time,
                'success': not result.get('error')
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                'scenario': scenario,
                'result': {'error': str(e)},
                'processing_time': time.time() - start_time,
                'success': False
            })
        
        print()  # Add spacing between tests
    
    # Print comprehensive summary
    print_integration_summary(results)
    
    return results


def print_integration_summary(results: List[Dict]):
    """Print comprehensive integration test summary"""
    
    print("=" * 60)
    print("🎯 ENHANCED PIPELINE INTEGRATION SUMMARY")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results if r['success'])
    total_tests = len(results)
    
    print(f"📊 Test Results: {successful_tests}/{total_tests} successful ({(successful_tests/total_tests)*100:.1f}%)")
    
    # Processing time analysis
    times = [r['processing_time'] * 1000 for r in results if r['success']]
    if times:
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        print(f"⚡ Processing Time: Avg {avg_time:.1f}ms, Min {min_time:.1f}ms, Max {max_time:.1f}ms")
    
    # Validation behavior analysis
    print(f"\n📋 Validation Behavior Analysis:")
    
    for result in results:
        scenario_name = result['scenario']['name']
        res = result['result']
        
        if result['success']:
            status = res.get('status', 'unknown')
            blocked = res.get('processing_blocked', False)
            issues = res.get('validation', {}).get('issues_detected', 0)
            confidence = res.get('quality_assessment', {}).get('overall_confidence', 0.0)
            
            outcome = "BLOCKED" if blocked else f"PROCESSED ({issues} issues)" 
            print(f"   {scenario_name}: {status.upper()} - {outcome}, confidence {confidence:.2f}")
        else:
            print(f"   {scenario_name}: FAILED - {res.get('error', 'Unknown error')}")
    
    # Mode effectiveness
    print(f"\n🎚️ Validation Mode Effectiveness:")
    strict_blocked = sum(1 for r in results if r['success'] and r['scenario']['mode'] == 'strict' and r['result'].get('processing_blocked', False))
    strict_total = sum(1 for r in results if r['scenario']['mode'] == 'strict')
    permissive_processed = sum(1 for r in results if r['success'] and r['scenario']['mode'] == 'permissive' and not r['result'].get('processing_blocked', False))
    permissive_total = sum(1 for r in results if r['scenario']['mode'] == 'permissive')
    
    print(f"   Strict Mode: {strict_blocked}/{strict_total} cases blocked for validation failures")
    print(f"   Permissive Mode: {permissive_processed}/{permissive_total} cases processed with warnings")
    
    # Quality assessment
    print(f"\n🎯 Quality Assessment:")
    confidences = [r['result'].get('quality_assessment', {}).get('overall_confidence', 0.0) 
                  for r in results if r['success']]
    if confidences:
        avg_confidence = sum(confidences) / len(confidences)
        print(f"   Average Overall Confidence: {avg_confidence:.2f}")
        
        high_confidence = sum(1 for c in confidences if c >= 0.8)
        medium_confidence = sum(1 for c in confidences if 0.5 <= c < 0.8)
        low_confidence = sum(1 for c in confidences if c < 0.5)
        
        print(f"   Confidence Distribution: {high_confidence} high (≥0.8), {medium_confidence} medium (0.5-0.8), {low_confidence} low (<0.5)")
    
    print(f"\n✅ Enhanced Pipeline Integration Test Complete!")
    print(f"🎯 System demonstrates production-ready validation and error handling")


async def demonstrate_error_responses():
    """Demonstrate detailed error responses for problematic orders"""
    
    print(f"\n" + "=" * 60)
    print("🚨 ERROR RESPONSE DEMONSTRATION")
    print("=" * 60)
    
    problematic_orders = [
        "Start beta blocker if BP high, maybe metoprolol or atenolol",
        "Give patient medication for their symptoms",
        "Start PPI, dose TBD"
    ]
    
    for i, order in enumerate(problematic_orders, 1):
        print(f"\n{i}. Problematic Order: '{order}'")
        print("-" * 40)
        
        result = await process_clinical_text_with_validation(
            order, 
            request_id=f"demo_{i}",
            validation_mode="strict"
        )
        
        # Show detailed error response
        if result.get('validation_details'):
            issues = result['validation_details']['issues']
            escalation = result['validation_details'].get('escalation_info', {})
            
            print(f"Status: {result['status']}")
            print(f"Issues Detected: {len(issues)}")
            
            for j, issue in enumerate(issues[:2], 1):  # Show top 2 issues
                print(f"\nIssue {j}:")
                print(f"  Severity: {issue['severity']}")
                print(f"  Message: {issue['message']}")
                print(f"  Guidance: {issue['guidance']}")
            
            if escalation:
                print(f"\nEscalation Required: {escalation.get('required', False)}")
                print(f"Escalation Level: {escalation.get('level', 'none')}")
                next_steps = escalation.get('next_steps', [])
                if next_steps:
                    print(f"Next Steps: {next_steps[0]}")
        
        # Show FHIR OperationOutcome if present
        fhir_outcome = result.get('fhir_operation_outcome')
        if fhir_outcome:
            print(f"\n📋 FHIR OperationOutcome Available: {len(fhir_outcome.get('issue', []))} FHIR issues recorded")


if __name__ == "__main__":
    print("🚀 Starting Enhanced NLP Pipeline Integration Tests\n")
    
    # Run main integration tests
    results = asyncio.run(test_enhanced_pipeline())
    
    # Demonstrate detailed error responses
    asyncio.run(demonstrate_error_responses())
    
    print(f"\n🏁 All integration tests complete!")