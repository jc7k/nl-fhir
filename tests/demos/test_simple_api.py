#!/usr/bin/env python3
"""
Simple API test for demonstration
"""

import requests
import json

def test_simple_case():
    """Test with a simple case that should work"""

    simple_note = "Start patient on aspirin 81mg daily for chest pain. Also order CBC."

    url = "http://localhost:8001/convert"
    payload = {
        "clinical_text": simple_note,
        "patient_id": "demo-patient"
    }

    try:
        print("🔄 Testing simple clinical note...")
        print(f"Input: {simple_note}")
        print()

        response = requests.post(url, json=payload, timeout=10)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")

            # Save successful response
            with open('docs/screenshots/sample_api_response.json', 'w') as f:
                json.dump(result, f, indent=2)

            print("📄 Response saved to docs/screenshots/sample_api_response.json")

        else:
            print("❌ Error response:")
            print(response.text)

    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_simple_case()