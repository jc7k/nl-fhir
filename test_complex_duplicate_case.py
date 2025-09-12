#!/usr/bin/env python3
"""
Test complex cases to ensure duplicate fix is robust
"""

import requests
import json

def test_complex_cases():
    """Test various complex clinical text scenarios"""
    
    test_cases = [
        {
            "name": "Multiple similar labs",
            "text": "Order CBC with differential, CBC without differential, and complete blood count."
        },
        {
            "name": "Mixed medications and procedures", 
            "text": "Start aspirin 81mg daily, order chest x-ray, prescribe aspirin for cardio protection, schedule chest radiograph."
        },
        {
            "name": "Compound procedures",
            "text": "Schedule chest x-ray, abdominal x-ray, and pelvic x-ray for tomorrow."
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test_case['name']}")
        print(f"Text: {test_case['text']}")
        print('-' * 60)
        
        try:
            # Make API request  
            response = requests.post(
                'http://localhost:8001/api/v1/convert',
                json={'clinical_text': test_case['text']},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                fhir_bundle = result.get('fhir_bundle', {})
                
                # Count ServiceRequests
                service_requests = []
                for entry in fhir_bundle.get('entry', []):
                    resource = entry.get('resource', {})
                    if resource.get('resourceType') == 'ServiceRequest':
                        code_section = resource.get('code', {})
                        code_text = (
                            code_section.get('text') or 
                            code_section.get('concept', {}).get('text') or
                            'No text'
                        )
                        service_requests.append(code_text)
                
                print(f"ServiceRequests found: {len(service_requests)}")
                for i, code in enumerate(service_requests):
                    print(f"  {i+1}. {code}")
                
                # Check for duplicates
                unique_codes = set(service_requests)
                if len(service_requests) > len(unique_codes):
                    duplicates = []
                    seen = set()
                    for code in service_requests:
                        if code in seen:
                            duplicates.append(code)
                        seen.add(code)
                    print(f"⚠️  DUPLICATES FOUND: {duplicates}")
                else:
                    print("✅ No duplicates found")
                    
            else:
                print(f"❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_complex_cases()