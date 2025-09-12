#!/usr/bin/env python3
"""
Test the Liam Brooks Hydroxyurea prescription case
"""

import requests
import json

def test_liam_brooks_case():
    """Test the specific Hydroxyurea prescription clinical note"""
    
    clinical_text = "Prescribed patient Liam Brooks 100mg Hydroxyurea daily for sickle cell disease; CBC tracked."
    
    print(f"Testing Liam Brooks case...")
    print(f"Text: {clinical_text}")
    print("-" * 80)
    
    try:
        # Make API request  
        response = requests.post(
            'http://localhost:8001/convert',
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
            
            # Analysis
            expected_medication = "Hydroxyurea"
            expected_lab = "CBC"
            
            found_hydroxyurea = any("hydroxyurea" in mr['medication'].lower() for mr in medication_requests)
            found_cbc = any("cbc" in sr['code'].lower() for sr in service_requests)
            
            print("ANALYSIS:")
            if found_hydroxyurea:
                print(f"✅ Found Hydroxyurea medication")
            else:
                print(f"⚠️  Hydroxyurea NOT found in medications")
                
            if found_cbc:
                print(f"✅ Found CBC lab test")  
            else:
                print(f"⚠️  CBC NOT found in lab tests")
            
            if len(medication_requests) == 0 and len(service_requests) == 0:
                print("⚠️  NO CLINICAL ORDERS EXTRACTED")
            else:
                print(f"✅ Found {len(medication_requests)} medications and {len(service_requests)} lab tests")
                    
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_liam_brooks_case()