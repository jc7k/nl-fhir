#!/usr/bin/env python3
"""
Test complex clinical case for LinkedIn screenshots
"""

import requests
import json
from datetime import datetime

# Complex clinical note for demonstration
complex_clinical_note = """
Patient Emma Rodriguez, 67-year-old female, presents to ED with acute chest pain and shortness of breath.
Started on dual antiplatelet therapy: aspirin 81mg daily and clopidogrel 75mg twice daily for acute coronary syndrome.
Also initiating atorvastatin 40mg once daily at bedtime for hyperlipidemia.
Patient has history of type 2 diabetes - continue metformin 500mg twice daily with meals.
For hypertension, start lisinopril 10mg once daily, monitor BP closely.
Order CBC, comprehensive metabolic panel, lipid panel, and troponin levels STAT.
Patient counseled on dietary modifications and smoking cessation.
"""

def test_api_conversion():
    """Test the /convert endpoint with complex clinical note"""
    print("🏥 Testing NL-FHIR Conversion API")
    print("=" * 50)

    url = "http://localhost:8001/convert"
    payload = {
        "clinical_text": complex_clinical_note,
        "patient_id": "emma-rodriguez-67"
    }

    print(f"📝 Clinical Note Input:")
    print(f"Patient: Emma Rodriguez, 67-year-old female")
    print(f"Medications: 5 medications with specific dosages")
    print(f"Conditions: 4 medical conditions")
    print(f"Orders: Multiple lab orders")
    print()

    try:
        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            result = response.json()

            print("✅ CONVERSION SUCCESSFUL")
            print("=" * 30)

            # Display summary
            if 'processing_info' in result:
                info = result['processing_info']
                print(f"⏱️  Processing Time: {info.get('processing_time_ms', 0):.1f}ms")
                print(f"🧠 Processing Tier: {info.get('tier_used', 'Unknown')}")
                print(f"📊 Confidence Score: {info.get('confidence_score', 0):.2f}")
                print()

            # Display extracted entities
            if 'entities' in result:
                entities = result['entities']
                print("🔍 EXTRACTED ENTITIES:")
                print(f"   Medications: {len(entities.get('medications', []))}")
                print(f"   Conditions: {len(entities.get('conditions', []))}")
                print(f"   Lab Orders: {len(entities.get('lab_tests', []))}")
                print()

                # Show medications
                if entities.get('medications'):
                    print("💊 Medications:")
                    for med in entities['medications'][:3]:  # Show first 3
                        name = med.get('name', 'Unknown')
                        dosage = med.get('dosage', 'Unknown')
                        frequency = med.get('frequency', 'Unknown')
                        print(f"   • {name} {dosage} {frequency}")
                    print()

            # FHIR Bundle info
            if 'fhir_bundle' in result:
                bundle = result['fhir_bundle']
                print("📋 FHIR R4 BUNDLE CREATED:")
                print(f"   Resource Type: {bundle.get('resourceType', 'Unknown')}")
                print(f"   Bundle Type: {bundle.get('type', 'Unknown')}")
                print(f"   Total Resources: {len(bundle.get('entry', []))}")
                print()

                # Show resource types
                resource_types = {}
                for entry in bundle.get('entry', []):
                    res_type = entry.get('resource', {}).get('resourceType', 'Unknown')
                    resource_types[res_type] = resource_types.get(res_type, 0) + 1

                print("📊 FHIR Resources Generated:")
                for res_type, count in resource_types.items():
                    print(f"   • {res_type}: {count}")
                print()

            print("🎯 SUCCESS: Clinical note converted to FHIR R4 bundle")

            # Save detailed JSON for screenshot
            with open('docs/screenshots/api_response.json', 'w') as f:
                json.dump(result, f, indent=2)

            print("💾 Full API response saved to docs/screenshots/api_response.json")

        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_api_conversion()