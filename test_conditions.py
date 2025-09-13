import json
import requests
import time

# Test cases with various clinical conditions
test_cases = [
    {
        "id": 1,
        "text": "Started patient John Smith on metformin 500mg twice daily for type 2 diabetes mellitus.",
        "expected_condition": "type 2 diabetes mellitus"
    },
    {
        "id": 2,
        "text": "Prescribed patient Mary Johnson amoxicillin 500mg three times daily for acute bacterial sinusitis.",
        "expected_condition": "acute bacterial sinusitis"
    },
    {
        "id": 3,
        "text": "Initiated patient Robert Brown on lisinopril 10mg daily for essential hypertension.",
        "expected_condition": "essential hypertension"
    },
    {
        "id": 4,
        "text": "Patient Sarah Davis started on albuterol inhaler 2 puffs every 4 hours for acute asthma exacerbation.",
        "expected_condition": "acute asthma exacerbation"
    },
    {
        "id": 5,
        "text": "Administered patient Michael Wilson morphine 5mg IV for severe chest pain secondary to myocardial infarction.",
        "expected_condition": "myocardial infarction"
    },
    {
        "id": 6,
        "text": "Started patient Emily Thompson on sertraline 50mg daily for major depressive disorder.",
        "expected_condition": "major depressive disorder"
    },
    {
        "id": 7,
        "text": "Prescribed patient James Garcia prednisone 20mg daily for rheumatoid arthritis flare.",
        "expected_condition": "rheumatoid arthritis flare"
    },
    {
        "id": 8,
        "text": "Patient Lisa Martinez on insulin glargine 20 units at bedtime for type 1 diabetes.",
        "expected_condition": "type 1 diabetes"
    }
]

def test_condition_extraction():
    url = "http://localhost:8001/convert"
    headers = {"Content-Type": "application/json"}
    
    print("=" * 80)
    print("CONDITION EXTRACTION TEST RESULTS")
    print("=" * 80)
    print()
    
    results = []
    
    for test in test_cases:
        print(f"Test {test['id']}: {test['text'][:50]}...")
        
        try:
            response = requests.post(url, json={"clinical_text": test["text"]}, headers=headers, timeout=15)
            response_data = response.json()
            
            # Extract patient name
            patient_name = "Unknown"
            medication_name = "Unknown"
            condition_text = "Unknown"
            
            if "fhir_bundle" in response_data and "entry" in response_data["fhir_bundle"]:
                for entry in response_data["fhir_bundle"]["entry"]:
                    resource = entry.get("resource", {})
                    
                    if resource.get("resourceType") == "Patient":
                        names = resource.get("name", [])
                        if names:
                            patient_name = names[0].get("text", "Unknown")
                    
                    elif resource.get("resourceType") == "MedicationRequest":
                        med_concept = resource.get("medicationCodeableConcept", {})
                        medication_name = med_concept.get("text", "Unknown")
                    
                    elif resource.get("resourceType") == "Condition":
                        code = resource.get("code", {})
                        condition_text = code.get("text", "Unknown")
            
            result = {
                "test_id": test["id"],
                "patient": patient_name,
                "medication": medication_name,
                "extracted_condition": condition_text,
                "expected_condition": test["expected_condition"],
                "match": condition_text.lower() == test["expected_condition"].lower()
            }
            
            results.append(result)
            
            print(f"  Patient: {patient_name}")
            print(f"  Medication: {medication_name}")
            print(f"  Condition: {condition_text}")
            print(f"  Expected: {test['expected_condition']}")
            print(f"  Match: {'✅' if result['match'] else '❌'}")
            print()
            
            # Small delay to avoid overwhelming the API
            time.sleep(1)
            
        except Exception as e:
            print(f"  Error: {e}")
            print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total_tests = len(results)
    successful_conditions = sum(1 for r in results if r["match"])
    successful_patients = sum(1 for r in results if r["patient"] != "Unknown")
    successful_medications = sum(1 for r in results if r["medication"] != "Unknown")
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful Condition Extraction: {successful_conditions}/{total_tests} ({successful_conditions/total_tests*100:.1f}%)")
    print(f"Successful Patient Extraction: {successful_patients}/{total_tests} ({successful_patients/total_tests*100:.1f}%)")
    print(f"Successful Medication Extraction: {successful_medications}/{total_tests} ({successful_medications/total_tests*100:.1f}%)")
    
    print("\nFailed Conditions:")
    for r in results:
        if not r["match"]:
            print(f"  Test {r['test_id']}: Got '{r['extracted_condition']}', Expected '{r['expected_condition']}'")

if __name__ == "__main__":
    test_condition_extraction()
