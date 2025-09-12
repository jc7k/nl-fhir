#!/usr/bin/env python3
"""
Test Epic 3 - FHIR Integration with Enhanced Medical NLP
Complete end-to-end test of the clinical text → FHIR conversion pipeline
"""

import sys
sys.path.append('../../src')

import asyncio
import json
import time
from nl_fhir.services.conversion import convert_clinical_text_to_fhir

async def test_epic3_fhir_integration():
    """Test the complete clinical text to FHIR conversion with enhanced medical NLP"""
    
    print("🏥 Epic 3 - FHIR Integration Test with Enhanced Medical NLP")
    print("="*70)
    
    # Comprehensive test cases representing different clinical scenarios
    test_cases = [
        {
            "name": "Standard Medication Order",
            "input": "Initiated patient Julian West on 5mg Tadalafil as needed for erectile dysfunction",
            "expected_resources": ["Patient", "MedicationRequest", "Condition"],
            "expected_codes": ["tadalafil", "erectile dysfunction"]
        },
        {
            "name": "Hypertension Management",
            "input": "Prescribed Lisinopril 10mg daily for hypertension",
            "expected_resources": ["MedicationRequest", "Condition"],
            "expected_codes": ["lisinopril", "hypertension"]
        },
        {
            "name": "Lab Orders",
            "input": "Order CBC and comprehensive metabolic panel, check troponins",
            "expected_resources": ["DiagnosticReport", "Observation"],
            "expected_codes": ["cbc", "metabolic panel", "troponins"]
        },
        {
            "name": "Complex Clinical Order",
            "input": "Start patient on Metformin 500mg twice daily for diabetes, follow up in 2 weeks",
            "expected_resources": ["Patient", "MedicationRequest", "Condition", "Appointment"],
            "expected_codes": ["metformin", "diabetes"]
        },
        {
            "name": "Medication Discontinuation",
            "input": "Discontinue aspirin due to GI bleeding, continue warfarin",
            "expected_resources": ["MedicationRequest"],
            "expected_codes": ["aspirin", "warfarin", "bleeding"]
        }
    ]
    
    print(f"Running {len(test_cases)} comprehensive FHIR integration tests...")
    print(f"Testing: Clinical Text → Enhanced NLP → FHIR Bundle Generation\n")
    
    results = []
    total_start_time = time.time()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print(f"   Input: {test_case['input']}")
        
        start_time = time.time()
        
        try:
            # Convert clinical text to FHIR using our enhanced pipeline
            result = await convert_clinical_text_to_fhir(
                clinical_text=test_case['input'],
                patient_id="test-patient-123",
                practitioner_id="test-practitioner-456"
            )
            
            processing_time = (time.time() - start_time) * 1000
            
            # Parse the result
            if result.get('success'):
                fhir_bundle = result.get('fhir_bundle', {})
                validation_result = result.get('validation_result', {})
                
                # Count resources in bundle
                resources = fhir_bundle.get('entry', [])
                resource_types = [entry.get('resource', {}).get('resourceType') for entry in resources]
                resource_count = len(resources)
                
                # Check validation
                is_valid = validation_result.get('valid', False)
                validation_errors = validation_result.get('errors', [])
                
                print(f"   ✅ SUCCESS - Processing time: {processing_time:.1f}ms")
                print(f"      📦 FHIR Bundle: {resource_count} resources")
                print(f"      📋 Resource types: {resource_types}")
                print(f"      ✓ FHIR Validation: {'PASSED' if is_valid else 'FAILED'}")
                
                if validation_errors:
                    print(f"      ⚠️  Validation errors: {len(validation_errors)}")
                    for error in validation_errors[:3]:  # Show first 3 errors
                        print(f"         - {error}")
                
                # Check if expected resources were created
                expected_found = sum(1 for expected in test_case['expected_resources'] 
                                   if expected in resource_types)
                completeness_score = expected_found / len(test_case['expected_resources'])
                
                print(f"      📊 Completeness: {completeness_score:.2f} ({expected_found}/{len(test_case['expected_resources'])} expected resources)")
                
                results.append({
                    'name': test_case['name'],
                    'success': True,
                    'processing_time_ms': processing_time,
                    'resource_count': resource_count,
                    'resource_types': resource_types,
                    'is_valid': is_valid,
                    'validation_errors': len(validation_errors),
                    'completeness_score': completeness_score,
                    'fhir_bundle': fhir_bundle
                })
                
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"   ❌ FAILED - {error_msg}")
                
                results.append({
                    'name': test_case['name'],
                    'success': False,
                    'error': error_msg,
                    'processing_time_ms': processing_time,
                    'resource_count': 0,
                    'completeness_score': 0.0
                })
                
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            print(f"   ❌ EXCEPTION - {str(e)}")
            
            results.append({
                'name': test_case['name'],
                'success': False,
                'error': str(e),
                'processing_time_ms': processing_time,
                'resource_count': 0,
                'completeness_score': 0.0
            })
        
        print()  # Empty line between tests
    
    total_processing_time = (time.time() - total_start_time) * 1000
    
    # Summary Analysis
    print("🏥 Epic 3 - FHIR Integration Test Results")
    print("="*50)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"✅ Successful conversions: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed conversions: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        avg_processing_time = sum(r['processing_time_ms'] for r in successful_tests) / len(successful_tests)
        avg_resources = sum(r['resource_count'] for r in successful_tests) / len(successful_tests)
        avg_completeness = sum(r['completeness_score'] for r in successful_tests) / len(successful_tests)
        valid_bundles = sum(1 for r in successful_tests if r.get('is_valid', False))
        
        print(f"\n📊 Performance Metrics:")
        print(f"   Average processing time: {avg_processing_time:.1f}ms")
        print(f"   Average resources per bundle: {avg_resources:.1f}")
        print(f"   Average completeness score: {avg_completeness:.2f}")
        print(f"   Valid FHIR bundles: {valid_bundles}/{len(successful_tests)}")
        print(f"   Total processing time: {total_processing_time:.1f}ms")
        
        # Performance targets
        print(f"\n🎯 Performance Target Assessment:")
        target_response_time = 2000  # 2 seconds
        target_validation_rate = 0.95  # 95% validation success
        target_completeness = 0.80  # 80% completeness
        
        if avg_processing_time <= target_response_time:
            print(f"   ✅ Response time: {avg_processing_time:.1f}ms ≤ {target_response_time}ms")
        else:
            print(f"   ❌ Response time: {avg_processing_time:.1f}ms > {target_response_time}ms")
        
        validation_rate = valid_bundles / len(successful_tests)
        if validation_rate >= target_validation_rate:
            print(f"   ✅ Validation rate: {validation_rate:.2%} ≥ {target_validation_rate:.2%}")
        else:
            print(f"   ❌ Validation rate: {validation_rate:.2%} < {target_validation_rate:.2%}")
        
        if avg_completeness >= target_completeness:
            print(f"   ✅ Completeness: {avg_completeness:.2%} ≥ {target_completeness:.2%}")
        else:
            print(f"   ❌ Completeness: {avg_completeness:.2%} < {target_completeness:.2%}")
        
    # Architecture Assessment
    print(f"\n🏗️  Enhanced Medical NLP Integration Assessment:")
    if len(successful_tests) >= 4:
        print(f"   ✅ EXCELLENT: Enhanced NLP pipeline handling most clinical scenarios")
    elif len(successful_tests) >= 3:
        print(f"   ✅ GOOD: Enhanced NLP pipeline working for common scenarios")
    elif len(successful_tests) >= 2:
        print(f"   ⚠️  MODERATE: Some clinical scenarios working, needs improvement")
    else:
        print(f"   ❌ POOR: Enhanced NLP pipeline needs significant work")
    
    # Recommendations
    print(f"\n💡 Recommendations for >95% Success Rate:")
    if len(failed_tests) > 0:
        print(f"   1. Debug failed conversions: {[r['name'] for r in failed_tests]}")
    
    if successful_tests and sum(r['validation_errors'] for r in successful_tests) > 0:
        print(f"   2. Fix FHIR validation errors in successful conversions")
    
    if successful_tests and avg_completeness < 0.8:
        print(f"   3. Improve medical entity extraction completeness")
    
    print(f"   4. Expand medical terminology dictionaries")
    print(f"   5. Add more sophisticated clinical pattern recognition")
    print(f"   6. Implement context-aware medical relationship extraction")
    
    return results

if __name__ == "__main__":
    print("🚀 Starting Epic 3 - FHIR Integration Test with Enhanced Medical NLP")
    print("Testing complete clinical text → FHIR conversion pipeline")
    print("="*70)
    
    # Run the async test
    results = asyncio.run(test_epic3_fhir_integration())
    
    if results:
        success_rate = sum(1 for r in results if r['success']) / len(results)
        print(f"\n🎉 Epic 3 Integration Test Complete!")
        print(f"   Success rate: {success_rate:.2%}")
        print(f"   Enhanced medical NLP architecture {'✅ READY' if success_rate >= 0.6 else '❌ NEEDS WORK'}")
    else:
        print(f"\n❌ Epic 3 Integration Test Failed!")