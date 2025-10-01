#!/usr/bin/env python3
"""
Quick validation test for RelatedPerson implementation
Tests the new create_related_person_resource adapter method
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nl_fhir.services.fhir.factory_adapter import get_factory_adapter

def test_related_person_implementation():
    """Test RelatedPerson resource creation"""
    print("=" * 70)
    print("🧪 RELATEDPERSON IMPLEMENTATION VALIDATION")
    print("=" * 70)

    factory = get_factory_adapter()
    factory.initialize()

    # Test 1: Basic creation
    print("\n✅ Test 1: Basic RelatedPerson Creation")
    try:
        related_data = {
            "name": "Jane Doe",
            "relationship": "spouse",
            "gender": "female"
        }

        result = factory.create_related_person_resource(
            related_data,
            "Patient/test-123",
            request_id="test-001"
        )

        assert result["resourceType"] == "RelatedPerson"
        assert result["patient"]["reference"] == "Patient/test-123"
        assert "relationship" in result
        print(f"   ✅ Resource created: {result['id']}")
        print(f"   ✅ Patient ref: {result['patient']['reference']}")
        print(f"   ✅ Relationship: {result.get('relationship', 'N/A')}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 2: With contact info
    print("\n✅ Test 2: RelatedPerson with Contact Info")
    try:
        related_data = {
            "name": {
                "given": "John",
                "family": "Smith"
            },
            "relationship": "father",
            "gender": "male",
            "telecom": [
                {
                    "system": "phone",
                    "value": "555-123-4567",
                    "use": "home"
                }
            ]
        }

        result = factory.create_related_person_resource(
            related_data,
            "Patient/test-456"
        )

        assert result["resourceType"] == "RelatedPerson"
        assert "telecom" in result
        assert len(result["telecom"]) == 1
        print(f"   ✅ Resource created with telecom")
        print(f"   ✅ Phone: {result['telecom'][0].get('value', 'N/A')}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 3: Emergency contact
    print("\n✅ Test 3: Emergency Contact")
    try:
        related_data = {
            "name": "Emergency Contact - Mary Johnson",
            "relationship": "emergency",
            "telecom": [
                {
                    "system": "phone",
                    "value": "555-911-1234",
                    "use": "mobile",
                    "rank": 1
                }
            ],
            "gender": "female"
        }

        result = factory.create_related_person_resource(
            related_data,
            "Patient/emergency-test"
        )

        assert result["resourceType"] == "RelatedPerson"
        print(f"   ✅ Emergency contact created")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 4: With period
    print("\n✅ Test 4: RelatedPerson with Period")
    try:
        related_data = {
            "name": "Temporary Guardian",
            "relationship": "guardian",
            "period": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            },
            "gender": "female"
        }

        result = factory.create_related_person_resource(
            related_data,
            "Patient/period-test"
        )

        assert result["resourceType"] == "RelatedPerson"
        assert "period" in result
        assert result["period"]["start"] == "2024-01-01"
        print(f"   ✅ Period tracking working")
        print(f"   ✅ Start: {result['period']['start']}")
        print(f"   ✅ End: {result['period']['end']}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 5: Multiple relationships
    print("\n✅ Test 5: Multiple Relationships")
    try:
        related_data = {
            "name": "Multi-Role Contact",
            "relationship": ["spouse", "emergency"],
            "gender": "other"
        }

        result = factory.create_related_person_resource(
            related_data,
            "Patient/multi-test"
        )

        assert result["resourceType"] == "RelatedPerson"
        assert isinstance(result["relationship"], list)
        assert len(result["relationship"]) == 2
        print(f"   ✅ Multiple relationships supported")
        print(f"   ✅ Count: {len(result['relationship'])}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Summary
    print("\n" + "=" * 70)
    print("✅ ALL VALIDATION TESTS PASSED!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("   ✅ Basic creation working")
    print("   ✅ Contact info (telecom) working")
    print("   ✅ Emergency contacts working")
    print("   ✅ Period tracking working")
    print("   ✅ Multiple relationships working")
    print("\n🎯 Next Step: Run full test suite")
    print("   Command: uv run pytest tests/epic_7/test_related_person_resource.py -v")
    print("=" * 70)

    return True

if __name__ == "__main__":
    try:
        success = test_related_person_implementation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
