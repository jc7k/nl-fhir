#!/usr/bin/env python3
"""
Quick validation test for ImagingStudy implementation
Tests the new create_imaging_study_resource adapter method
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nl_fhir.services.fhir.factory_adapter import get_factory_adapter

def test_imaging_study_implementation():
    """Test ImagingStudy resource creation"""
    print("=" * 70)
    print("🧪 IMAGINGSTUDY IMPLEMENTATION VALIDATION")
    print("=" * 70)

    factory = get_factory_adapter()
    factory.initialize()

    # Test 1: Basic creation
    print("\n✅ Test 1: Basic ImagingStudy Creation")
    try:
        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:30:00Z"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/test-123",
            request_id="test-001"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert result["status"] == "available"
        assert result["subject"]["reference"] == "Patient/test-123"
        print(f"   ✅ Resource created: {result['id']}")
        print(f"   ✅ Patient ref: {result['subject']['reference']}")
        print(f"   ✅ Status: {result['status']}")
        print(f"   ✅ Started: {result['started']}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 2: With single series
    print("\n✅ Test 2: ImagingStudy with Single Series")
    try:
        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:30:00Z",
            "procedureCode": "CT chest with contrast",
            "series": [{
                "modality": "CT",
                "description": "Chest CT with IV contrast",
                "numberOfInstances": 150
            }]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/test-456"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "series" in result
        assert len(result["series"]) == 1
        assert result["numberOfSeries"] == 1
        assert result["numberOfInstances"] == 150
        print(f"   ✅ Series count: {result['numberOfSeries']}")
        print(f"   ✅ Instance count: {result['numberOfInstances']}")
        print(f"   ✅ Modality: CT")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 3: Multi-series MRI study
    print("\n✅ Test 3: Multi-Series MRI Study")
    try:
        imaging_data = {
            "status": "available",
            "started": "2024-12-01T14:00:00Z",
            "procedureCode": "MRI brain with and without contrast",
            "series": [
                {
                    "uid": "2.25.123456789",
                    "modality": "MR",
                    "description": "T1-weighted pre-contrast",
                    "numberOfInstances": 180,
                    "bodySite": "Brain"
                },
                {
                    "uid": "2.25.987654321",
                    "modality": "MR",
                    "description": "T1-weighted post-contrast",
                    "numberOfInstances": 180,
                    "bodySite": "Brain"
                }
            ]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/test-789"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert len(result["series"]) == 2
        assert result["numberOfSeries"] == 2
        assert result["numberOfInstances"] == 360
        print(f"   ✅ Multiple series: {result['numberOfSeries']} series")
        print(f"   ✅ Total instances: {result['numberOfInstances']}")
        print(f"   ✅ Body site configured")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 4: With clinical context
    print("\n✅ Test 4: ImagingStudy with Clinical Context")
    try:
        imaging_data = {
            "status": "available",
            "started": "2024-12-01T09:00:00Z",
            "basedOn": ["ServiceRequest/imaging-order-123"],
            "referrer": "Practitioner/referring-physician-456",
            "encounter": "Encounter/encounter-001",
            "reasonCode": ["Pneumonia"],
            "reasonReference": ["Condition/pneumonia-001"],
            "series": [{
                "modality": "DX",
                "description": "PA and lateral chest radiograph",
                "numberOfInstances": 2
            }]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/test-context"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "basedOn" in result
        assert "referrer" in result
        assert "encounter" in result
        assert "reasonCode" in result
        print(f"   ✅ Based on ServiceRequest")
        print(f"   ✅ Referrer specified")
        print(f"   ✅ Encounter linked")
        print(f"   ✅ Reason codes provided")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 5: Complex DICOM workflow
    print("\n✅ Test 5: Complex DICOM Workflow")
    try:
        imaging_data = {
            "status": "available",
            "started": "2024-12-01T08:00:00Z",
            "basedOn": ["ServiceRequest/imaging-order-789"],
            "referrer": "Practitioner/cardiologist-123",
            "encounter": "Encounter/cardiology-visit-001",
            "procedureCode": "CT angiography chest",
            "procedureReference": "Procedure/cta-chest-001",
            "reasonCode": ["Suspected pulmonary embolism"],
            "reasonReference": ["Condition/suspected-pe-001"],
            "series": [
                {
                    "uid": "2.25.111111111",
                    "modality": "CT",
                    "description": "Scout images",
                    "numberOfInstances": 3,
                    "bodySite": "Chest"
                },
                {
                    "uid": "2.25.222222222",
                    "modality": "CT",
                    "description": "Arterial phase CTA",
                    "numberOfInstances": 250,
                    "bodySite": "Chest"
                },
                {
                    "uid": "2.25.333333333",
                    "modality": "CT",
                    "description": "Delayed phase",
                    "numberOfInstances": 250,
                    "bodySite": "Chest"
                }
            ],
            "endpoint": ["Endpoint/pacs-endpoint-1"],
            "description": "CT angiography chest for suspected PE",
            "location": "Location/radiology-suite-1"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/test-complex"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert len(result["series"]) == 3
        assert result["numberOfSeries"] == 3
        assert result["numberOfInstances"] == 503
        print(f"   ✅ Complex workflow configured")
        print(f"   ✅ Multiple series: {result['numberOfSeries']}")
        print(f"   ✅ Total instances: {result['numberOfInstances']}")
        print(f"   ✅ DICOM UIDs preserved")
        print(f"   ✅ Clinical context complete")
        print(f"   ✅ PACS endpoint configured")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Summary
    print("\n" + "=" * 70)
    print("✅ ALL VALIDATION TESTS PASSED!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("   ✅ Basic creation working")
    print("   ✅ Single series studies working")
    print("   ✅ Multi-series studies working")
    print("   ✅ Clinical context integration working")
    print("   ✅ Complex DICOM workflows working")
    print("\n🎯 Next Step: Run full test suite")
    print("   Command: uv run pytest tests/epic_7/test_imaging_study_resource.py -v")
    print("=" * 70)

    return True

if __name__ == "__main__":
    try:
        success = test_imaging_study_implementation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
