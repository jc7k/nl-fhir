#!/usr/bin/env python3
"""
Test script to investigate duplicate lab orders in FHIR bundle
"""

import requests
import json

def test_lab_order_duplication():
    """Test for duplicate lab orders in FHIR bundle"""
    
    # Test request with multiple types of orders
    test_request = {
        "clinical_text": "Order CBC with differential. Start aspirin 81mg daily. Schedule chest x-ray."
    }
    
    print(f"Testing for duplicate lab orders...")
    print(f"Request: {test_request}")
    print("-" * 50)
    
    try:
        # Make request to the /convert endpoint
        response = requests.post(
            "http://localhost:8001/convert",
            json=test_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResponse status: SUCCESS")
            print(f"Request ID: {result.get('request_id')}")
            
            # Check if FHIR bundle exists
            fhir_bundle = result.get('fhir_bundle')
            if fhir_bundle:
                print(f"\nFHIR Bundle found with {len(fhir_bundle.get('entry', []))} entries:")
                
                # Count ServiceRequests
                service_requests = []
                for i, entry in enumerate(fhir_bundle.get('entry', [])):
                    resource = entry.get('resource', {})
                    resource_type = resource.get('resourceType')
                    
                    if resource_type == 'ServiceRequest':
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
                
                print(f"\nFound {len(service_requests)} ServiceRequest resources:")
                for sr in service_requests:
                    print(f"  [{sr['index']}] ID: {sr['id']}")
                    print(f"      Code: {sr['code']}")
                    print(f"      Category: {sr['category']}")
                    print()
                
                # Check for duplicates
                codes = [sr['code'] for sr in service_requests]
                if len(codes) != len(set(codes)):
                    print(f"⚠️  DUPLICATE DETECTED: Same lab order appears multiple times!")
                    duplicates = [code for code in codes if codes.count(code) > 1]
                    print(f"   Duplicated orders: {set(duplicates)}")
                    return False
                else:
                    print(f"✅ NO DUPLICATES: Each ServiceRequest is unique")
                    return True
                    
            else:
                print(f"❌ ERROR: No FHIR bundle in response")
        else:
            print(f"Request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        
    return False

if __name__ == "__main__":
    success = test_lab_order_duplication()
    print("-" * 50)
    if success:
        print(f"✅ NO DUPLICATE LAB ORDERS FOUND")
    else:
        print(f"⚠️  DUPLICATE LAB ORDERS DETECTED - NEEDS FIX")