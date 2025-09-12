#!/usr/bin/env python3
"""
Test the Mia Scott clinical note case
"""

import requests
import json

def test_mia_scott_case():
    """Test the specific clinical note that may have issues"""
    
    clinical_text = "Started patient Mia Scott on 500mg Ciprofloxacin twice daily for traveler's diarrhea; advised on hydration and rest."
    
    print(f"Testing Mia Scott case...")
    print(f"Text: {clinical_text}")
    print("-" * 70)
    
    try:
        # Make API request  
        response = requests.post(
            'http://localhost:8001/api/v1/convert',
            json={'clinical_text': clinical_text},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            request_id = result.get('request_id')
            fhir_bundle = result.get('fhir_bundle', {})
            
            print(f"Response status: SUCCESS")
            print(f"Request ID: {request_id}")
            print(f"FHIR Bundle found with {len(fhir_bundle.get('entry', []))} entries:")
            print()
            
            # Analyze all resources
            medication_requests = []
            service_requests = []
            
            for i, entry in enumerate(fhir_bundle.get('entry', [])):
                resource = entry.get('resource', {})
                resource_type = resource.get('resourceType')
                
                print(f"[{i}] {resource_type}: {resource.get('id')}")
                
                if resource_type == 'MedicationRequest':
                    med_concept = resource.get('medicationCodeableConcept', {})
                    medication_name = med_concept.get('text', 'No text')
                    medication_requests.append({
                        'index': i,
                        'id': resource.get('id'),
                        'medication': medication_name,
                        'status': resource.get('status')
                    })
                
                elif resource_type == 'ServiceRequest':
                    # Check both possible code structures: direct text or concept.text
                    code_section = resource.get('code', {})
                    code_text = (
                        code_section.get('text') or 
                        code_section.get('concept', {}).get('text') or
                        'No text'
                    )
                    
                    service_requests.append({
                        'index': i,
                        'id': resource.get('id'),
                        'code': code_text,
                        'category': resource.get('category', [{}])[0].get('coding', [{}])[0].get('display', 'No category')
                    })
            
            print()
            print(f"Found {len(medication_requests)} MedicationRequest resources:")
            for mr in medication_requests:
                print(f"  [{mr['index']}] ID: {mr['id']}")
                print(f"      Medication: {mr['medication']}")
                print(f"      Status: {mr['status']}")
                print()
            
            print(f"Found {len(service_requests)} ServiceRequest resources:")
            for sr in service_requests:
                print(f"  [{sr['index']}] ID: {sr['id']}")
                print(f"      Code: {sr['code']}")
                print(f"      Category: {sr['category']}")
                print()
            
            # Check for duplicates in medications
            medication_names = [mr['medication'] for mr in medication_requests]
            unique_medications = set(medication_names)
            if len(medication_names) > len(unique_medications):
                duplicates = []
                seen = set()
                for med in medication_names:
                    if med in seen:
                        duplicates.append(med)
                    seen.add(med)
                print(f"⚠️  MEDICATION DUPLICATES: {duplicates}")
            else:
                print("✅ No medication duplicates found")
            
            # Check for duplicates in service requests
            service_codes = [sr['code'] for sr in service_requests]
            unique_codes = set(service_codes)
            if len(service_codes) > len(unique_codes):
                duplicates = []
                seen = set()
                for code in service_codes:
                    if code in seen:
                        duplicates.append(code)
                    seen.add(code)
                print(f"⚠️  SERVICE REQUEST DUPLICATES: {duplicates}")
            else:
                print("✅ No service request duplicates found")
                    
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_mia_scott_case()