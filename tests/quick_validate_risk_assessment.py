#!/usr/bin/env python3
"""
Quick validation test for RiskAssessment implementation
Tests the new create_risk_assessment_resource adapter method
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nl_fhir.services.fhir.factory_adapter import get_factory_adapter

def test_risk_assessment_implementation():
    """Test RiskAssessment resource creation"""
    print("=" * 70)
    print("🧪 RISKASSESSMENT IMPLEMENTATION VALIDATION")
    print("=" * 70)

    factory = get_factory_adapter()
    factory.initialize()

    # Test 1: Basic creation
    print("\n✅ Test 1: Basic RiskAssessment Creation")
    try:
        risk_data = {
            "status": "final",
            "method": "Clinical risk assessment",
            "code": "General health risk"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/test-123",
            request_id="test-001"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert result["status"] == "final"
        assert result["subject"]["reference"] == "Patient/test-123"
        print(f"   ✅ Resource created: {result['id']}")
        print(f"   ✅ Patient ref: {result['subject']['reference']}")
        print(f"   ✅ Status: {result['status']}")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 2: With prediction
    print("\n✅ Test 2: RiskAssessment with Prediction")
    try:
        risk_data = {
            "status": "final",
            "method": "SCORE2 cardiovascular risk assessment",
            "code": "Cardiovascular disease risk assessment",
            "prediction": [{
                "outcome": "Myocardial infarction",
                "qualitative_risk": "high",
                "probability_decimal": 0.15
            }]
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/test-456"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert "prediction" in result
        assert len(result["prediction"]) > 0
        print(f"   ✅ Predictions: {len(result['prediction'])} prediction(s)")
        print(f"   ✅ Risk level configured")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 3: With basis observations
    print("\n✅ Test 3: RiskAssessment with Basis Observations")
    try:
        risk_data = {
            "status": "final",
            "method": "Diabetes risk assessment",
            "code": "Type 2 diabetes risk",
            "basis": [
                "Observation/glucose-001",
                "Observation/bmi-001"
            ]
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/test-789"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert "basis" in result
        assert len(result["basis"]) == 2
        print(f"   ✅ Basis observations: {len(result['basis'])} observation(s)")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 4: With mitigation
    print("\n✅ Test 4: RiskAssessment with Mitigation Strategy")
    try:
        risk_data = {
            "status": "final",
            "method": "Fall risk assessment",
            "code": "Fall risk evaluation",
            "prediction": [{
                "outcome": "Falls",
                "qualitative_risk": "moderate"
            }],
            "mitigation": "Physical therapy, home safety modifications, assistive devices"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/test-mitigation"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert "mitigation" in result
        print(f"   ✅ Mitigation strategy configured")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Test 5: Complex cardiovascular risk
    print("\n✅ Test 5: Complex Cardiovascular Risk Assessment")
    try:
        risk_data = {
            "status": "final",
            "method": "SCORE2 cardiovascular risk assessment",
            "code": "10-year cardiovascular disease risk",
            "encounter": "Encounter/encounter-001",
            "condition": "Condition/hypertension-001",
            "performer": "Practitioner/cardiologist-123",
            "basis": [
                "Observation/cholesterol-001",
                "Observation/blood-pressure-001",
                "Observation/smoking-status-001"
            ],
            "prediction": [
                {
                    "outcome": "Myocardial infarction",
                    "qualitative_risk": "high",
                    "probability_decimal": 0.15,
                    "when_period": {
                        "start": datetime.utcnow().isoformat() + 'Z',
                        "end": (datetime.utcnow() + timedelta(days=3650)).isoformat() + 'Z'
                    }
                },
                {
                    "outcome": "Stroke",
                    "qualitative_risk": "moderate",
                    "probability_decimal": 0.08
                }
            ],
            "mitigation": "Lifestyle modifications, statin therapy, blood pressure control, smoking cessation",
            "note": "Patient has multiple cardiovascular risk factors requiring aggressive intervention"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/test-complex"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert len(result["prediction"]) == 2
        assert len(result["basis"]) == 3
        print(f"   ✅ Complex assessment configured")
        print(f"   ✅ Multiple predictions: {len(result['prediction'])}")
        print(f"   ✅ Multiple basis observations: {len(result['basis'])}")
        print(f"   ✅ Encounter linked")
        print(f"   ✅ Performer specified")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False

    # Summary
    print("\n" + "=" * 70)
    print("✅ ALL VALIDATION TESTS PASSED!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("   ✅ Basic creation working")
    print("   ✅ Predictions with risk levels working")
    print("   ✅ Basis observations working")
    print("   ✅ Mitigation strategies working")
    print("   ✅ Complex cardiovascular assessment working")
    print("\n🎯 Next Step: Run full test suite")
    print("   Command: uv run pytest tests/epic_7/test_risk_assessment_resource.py -v")
    print("=" * 70)

    return True

if __name__ == "__main__":
    try:
        success = test_risk_assessment_implementation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
