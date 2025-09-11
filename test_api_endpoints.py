#!/usr/bin/env python3
"""
Test Epic 4 API endpoints functionality
"""

import sys
import os
import asyncio

# Add the source path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fastapi.testclient import TestClient
from nl_fhir.main import app

def test_api_endpoints():
    """Test Epic 4 API endpoints"""
    print("🧪 Testing Epic 4 API Endpoints")
    
    client = TestClient(app)
    
    # Test bundle
    test_bundle = {
        "resourceType": "Bundle",
        "id": "api-test-bundle",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "test-med",
                    "medicationCodeableConcept": {
                        "text": "Metformin 500mg"
                    },
                    "dosageInstruction": [
                        {"text": "Take twice daily"}
                    ]
                }
            }
        ]
    }
    
    # Test 1: Original summarize-bundle endpoint (Story 4.1)
    print("\n1️⃣ Testing /summarize-bundle (Story 4.1)")
    response1 = client.post("/summarize-bundle", json={
        "bundle": test_bundle,
        "user_role": "clinician"
    })
    
    if response1.status_code == 200:
        print("✅ Original endpoint working")
        result1 = response1.json()
        print(f"📋 Summary length: {len(result1.get('human_readable_summary', ''))}")
    else:
        print(f"❌ Original endpoint failed: {response1.status_code}")
        print(f"Error: {response1.text}")
    
    # Test 2: Enhanced summarize-bundle endpoint (Stories 4.1-4.4)
    print("\n2️⃣ Testing /summarize-bundle-enhanced (Stories 4.1-4.4)")
    response2 = client.post("/summarize-bundle-enhanced", json={
        "bundle": test_bundle,
        "user_role": "clinician",
        "llm_enhancement": False
    })
    
    if response2.status_code == 200:
        print("✅ Enhanced endpoint working")
        result2 = response2.json()
        print(f"📋 Summary type: {result2.get('summary_type', 'unknown')}")
        print(f"🔒 Safety analysis: {len(result2.get('safety_analysis', {}).get('issues', []))} issues")
    else:
        print(f"❌ Enhanced endpoint failed: {response2.status_code}")
        print(f"Error: {response2.text}")
        
    # Test 3: Enhanced endpoint with LLM
    print("\n3️⃣ Testing /summarize-bundle-enhanced with LLM (Story 4.3)")
    response3 = client.post("/summarize-bundle-enhanced", json={
        "bundle": test_bundle,
        "user_role": "clinician", 
        "llm_enhancement": True,
        "enhancement_level": "contextual"
    })
    
    if response3.status_code == 200:
        print("✅ LLM enhanced endpoint working")
        result3 = response3.json()
        print(f"📋 Summary type: {result3.get('summary_type', 'unknown')}")
        print(f"🤖 Enhancement applied: {result3.get('enhancement_details', {}) is not None}")
    else:
        print(f"❌ LLM enhanced endpoint failed: {response3.status_code}")
        print(f"Error: {response3.text}")
    
    # Test 4: Health endpoints
    print("\n4️⃣ Testing health endpoints")
    health_response = client.get("/health")
    if health_response.status_code == 200:
        print("✅ Health endpoint working")
    else:
        print(f"❌ Health endpoint failed: {health_response.status_code}")
    
    metrics_response = client.get("/metrics")
    if metrics_response.status_code == 200:
        print("✅ Metrics endpoint working")
    else:
        print(f"❌ Metrics endpoint failed: {metrics_response.status_code}")
    
    print("\n✅ API Endpoint Testing Complete!")
    return True

if __name__ == "__main__":
    test_api_endpoints()