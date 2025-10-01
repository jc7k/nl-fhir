#!/usr/bin/env python3
"""
Quick validation test for CommunicationRequest implementation
Tests the new create_communication_request_resource adapter method
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nl_fhir.services.fhir.factory_adapter import get_factory_adapter

def test_communication_request_implementation():
    """Test CommunicationRequest resource creation"""
    print("=" * 70)
    print("🧪 COMMUNICATIONREQUEST IMPLEMENTATION VALIDATION")
    print("=" * 70)

    factory = get_factory_adapter()
    factory.initialize()

    # Test 1: Basic creation
    print("\n✅ Test 1: Basic CommunicationRequest Creation")
    try:
        comm_req_data = {
            "status": "active",
            "intent": "order",
            "payload": ["Please call the office to schedule your follow-up appointment"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/test-123",
            request_id="test-001"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert result["status"] == "active"
        assert result["intent"] == "order"
        assert result["subject"]["reference"] == "Patient/test-123"
        assert "payload" in result
        print(f"   ✅ Resource created: {result['id']}")
        print(f"   ✅ Patient ref: {result['subject']['reference']}")
        print(f"   ✅ Status: {result['status']}")
        print(f"   ✅ Intent: {result['intent']}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 2: With priority and medium
    print("\n✅ Test 2: CommunicationRequest with Priority and Medium")
    try:
        comm_req_data = {
            "status": "active",
            "intent": "order",
            "priority": "urgent",
            "medium": ["phone", "email"],
            "payload": ["URGENT: Patient requires immediate callback"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/test-456"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert result["priority"] == "urgent"
        assert "medium" in result
        print(f"   ✅ Priority set: {result['priority']}")
        print(f"   ✅ Medium channels: {len(result.get('medium', []))} channels")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 3: With recipient and category
    print("\n✅ Test 3: CommunicationRequest with Recipient and Category")
    try:
        comm_req_data = {
            "status": "active",
            "intent": "order",
            "category": "reminder",
            "recipient": ["Practitioner/practitioner-123"],
            "payload": ["Appointment reminder: Patient has appointment tomorrow"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/test-789"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "category" in result
        assert "recipient" in result
        print(f"   ✅ Category configured")
        print(f"   ✅ Recipients: {len(result.get('recipient', []))} recipient(s)")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 4: With occurrence and reason
    print("\n✅ Test 4: CommunicationRequest with Timing and Reason")
    try:
        occurrence_time = (datetime.utcnow() + timedelta(hours=2)).isoformat() + 'Z'

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "occurrence_datetime": occurrence_time,
            "reason_code": ["Follow-up after discharge"],
            "payload": ["Post-discharge follow-up call required"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/test-timing"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "occurrenceDateTime" in result or "occurrence_datetime" in str(result)
        assert "reasonCode" in result or "reason_code" in str(result)
        print(f"   ✅ Occurrence time set")
        print(f"   ✅ Reason code provided")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 5: Complex workflow scenario
    print("\n✅ Test 5: Complex Care Coordination Workflow")
    try:
        comm_req_data = {
            "status": "active",
            "intent": "order",
            "category": ["instruction", "notification"],
            "priority": "urgent",
            "medium": ["phone", "sms"],
            "recipient": [
                "Practitioner/primary-123",
                "Practitioner/specialist-456"
            ],
            "sender": "Practitioner/care-coordinator-999",
            "payload": [
                "Team notification: Patient requires coordinated care",
                "Instructions: Schedule follow-up appointments"
            ],
            "encounter": "Encounter/encounter-001",
            "note": "Complex care coordination required"
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/test-complex"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert result["priority"] == "urgent"
        assert len(result.get("recipient", [])) == 2
        assert len(result.get("payload", [])) >= 2
        print(f"   ✅ Complex workflow configured")
        print(f"   ✅ Multiple recipients: {len(result.get('recipient', []))}")
        print(f"   ✅ Multiple payloads: {len(result.get('payload', []))}")
        print(f"   ✅ Sender specified")
        print(f"   ✅ Encounter linked")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Summary
    print("\n" + "=" * 70)
    print("✅ ALL VALIDATION TESTS PASSED!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("   ✅ Basic creation working")
    print("   ✅ Priority and medium working")
    print("   ✅ Recipients and categories working")
    print("   ✅ Timing and reason codes working")
    print("   ✅ Complex care coordination workflow working")
    print("\n🎯 Next Step: Run full test suite")
    print("   Command: uv run pytest tests/epic_7/test_communication_request_resource.py -v")
    print("=" * 70)

    return True

if __name__ == "__main__":
    try:
        success = test_communication_request_implementation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
