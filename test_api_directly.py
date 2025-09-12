#!/usr/bin/env python3
"""
Test API directly to verify entity detection is working
"""

import requests
import json

def test_api_endpoints():
    """Test the /convert endpoint directly"""
    
    base_url = "http://localhost:8000/api/v1"
    
    test_cases = [
        {
            "name": "CBC and Metabolic Panel Test",
            "clinical_text": "Order CBC and comprehensive metabolic panel for routine health screening"
        },
        {
            "name": "Sertraline Medication",  
            "clinical_text": "Start patient on Sertraline 100mg daily for depression"
        },
        {
            "name": "Multiple Medications",
            "clinical_text": "Prescribe Albuterol inhaler 2 puffs every 6 hours and Prednisone 20mg daily"
        }
    ]
    
    print("🌐 Testing API Endpoints Directly")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Input: {test_case['clinical_text']}")
        
        # Test with the standard convert endpoint
        try:
            response = requests.post(
                f"{base_url}/convert",
                json={"clinical_text": test_case['clinical_text']},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ API Response OK")
                
                # Check for extracted entities
                if "extracted_entities" in data:
                    entities = data["extracted_entities"]
                    medications = entities.get("medications", [])
                    lab_tests = entities.get("lab_tests", [])
                    procedures = entities.get("procedures", [])
                    conditions = entities.get("conditions", [])
                    
                    total_entities = len(medications) + len(lab_tests) + len(procedures) + len(conditions)
                    
                    print(f"   📊 Entities found:")
                    print(f"      Medications: {len(medications)}")
                    print(f"      Lab Tests: {len(lab_tests)}")
                    print(f"      Procedures: {len(procedures)}")
                    print(f"      Conditions: {len(conditions)}")
                    print(f"      Total: {total_entities}")
                    
                    if medications:
                        print(f"      Found medications: {[med.get('text', 'unknown') for med in medications]}")
                    if lab_tests:
                        print(f"      Found lab tests: {[lab.get('text', 'unknown') for lab in lab_tests]}")
                    
                    if total_entities > 0:
                        print(f"   ✅ SUCCESS - Entities detected!")
                    else:
                        print(f"   ❌ PROBLEM - No entities in API response")
                else:
                    print(f"   ❌ PROBLEM - No extracted_entities in response")
                    print(f"   Response keys: {list(data.keys())}")
            else:
                print(f"   ❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    test_api_endpoints()