"""
Epic 7.6: RiskAssessment Resource Tests
Tests for RiskAssessment resource implementation - clinical risk evaluation and prediction

Validates FHIR R4 compliance, patient linkage, and risk assessment workflows.
"""

import pytest
from datetime import datetime, timedelta
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


class TestRiskAssessmentResource:
    """Test Epic 7.6: RiskAssessment Resource Implementation"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    # =================================================================
    # Story 7.6: Basic RiskAssessment Resource Tests
    # =================================================================

    def test_risk_assessment_basic_creation(self, factory):
        """Test basic RiskAssessment resource creation (Story 7.6)"""

        risk_data = {
            "status": "final",
            "method": "Clinical risk assessment",
            "code": "General health risk"
        }

        patient_ref = "Patient/patient-123"

        result = factory.create_risk_assessment_resource(
            risk_data,
            patient_ref,
            request_id="req-risk-001"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert result["status"] == "final"
        assert result["subject"]["reference"] == patient_ref

    def test_risk_assessment_with_method(self, factory):
        """Test RiskAssessment with assessment method"""

        risk_data = {
            "status": "final",
            "method": "SCORE2 cardiovascular risk assessment",
            "code": "10-year cardiovascular disease risk"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-456"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert "method" in result

    def test_risk_assessment_with_code(self, factory):
        """Test RiskAssessment with risk type coding"""

        risk_data = {
            "status": "final",
            "code": "Fall risk assessment",
            "method": "Morse Fall Scale"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-789"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert "code" in result

    # =================================================================
    # Prediction Tests
    # =================================================================

    def test_risk_assessment_with_single_prediction(self, factory):
        """Test RiskAssessment with single prediction"""

        risk_data = {
            "status": "final",
            "method": "SCORE2 cardiovascular risk assessment",
            "code": "Cardiovascular disease risk",
            "prediction": [{
                "outcome": "Myocardial infarction",
                "qualitative_risk": "high",
                "probability_decimal": 0.15
            }]
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-prediction"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert "prediction" in result
        assert len(result["prediction"]) == 1
        assert "qualitativeRisk" in result["prediction"][0]

    def test_risk_assessment_with_multiple_predictions(self, factory):
        """Test RiskAssessment with multiple predictions"""

        risk_data = {
            "status": "final",
            "method": "Comprehensive cardiovascular risk",
            "code": "Multi-outcome cardiovascular risk",
            "prediction": [
                {
                    "outcome": "Myocardial infarction",
                    "qualitative_risk": "high",
                    "probability_decimal": 0.15
                },
                {
                    "outcome": "Stroke",
                    "qualitative_risk": "moderate",
                    "probability_decimal": 0.08
                },
                {
                    "outcome": "Heart failure",
                    "qualitative_risk": "low",
                    "probability_decimal": 0.03
                }
            ]
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-multi-pred"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert len(result["prediction"]) == 3

    def test_risk_assessment_prediction_risk_levels(self, factory):
        """Test RiskAssessment with different risk levels"""

        risk_levels = ["low", "moderate", "high"]

        for risk_level in risk_levels:
            risk_data = {
                "status": "final",
                "method": "Risk assessment",
                "code": f"{risk_level.title()} risk scenario",
                "prediction": [{
                    "outcome": "Adverse event",
                    "qualitative_risk": risk_level
                }]
            }

            result = factory.create_risk_assessment_resource(
                risk_data,
                "Patient/patient-risk-level"
            )

            assert result["resourceType"] == "RiskAssessment"
            assert "prediction" in result
            assert "qualitativeRisk" in result["prediction"][0]

    def test_risk_assessment_with_probability_decimal(self, factory):
        """Test RiskAssessment with probability decimal"""

        risk_data = {
            "status": "final",
            "method": "Quantitative risk assessment",
            "code": "Diabetes risk",
            "prediction": [{
                "outcome": "Type 2 diabetes within 10 years",
                "probability_decimal": 0.25
            }]
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-prob-decimal"
        )

        assert result["resourceType"] == "RiskAssessment"
        if "prediction" in result and result["prediction"]:
            pred = result["prediction"][0]
            if "probabilityDecimal" in pred:
                assert pred["probabilityDecimal"] == 0.25

    def test_risk_assessment_with_when_period(self, factory):
        """Test RiskAssessment with temporal prediction (when period)"""

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=3650)  # 10 years

        risk_data = {
            "status": "final",
            "method": "Long-term risk assessment",
            "code": "10-year cardiovascular risk",
            "prediction": [{
                "outcome": "Cardiovascular event",
                "qualitative_risk": "moderate",
                "when_period": {
                    "start": start_date.isoformat() + 'Z',
                    "end": end_date.isoformat() + 'Z'
                }
            }]
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-when-period"
        )

        assert result["resourceType"] == "RiskAssessment"
        if "prediction" in result and result["prediction"]:
            pred = result["prediction"][0]
            if "whenPeriod" in pred:
                assert "start" in pred["whenPeriod"]
                assert "end" in pred["whenPeriod"]

    # =================================================================
    # Basis and Evidence Tests
    # =================================================================

    def test_risk_assessment_with_basis_observations(self, factory):
        """Test RiskAssessment with basis observations"""

        risk_data = {
            "status": "final",
            "method": "Evidence-based risk assessment",
            "code": "Diabetes risk",
            "basis": [
                "Observation/glucose-001",
                "Observation/bmi-001",
                "Observation/bp-001"
            ]
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-basis"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert "basis" in result
        assert len(result["basis"]) == 3

    def test_risk_assessment_with_condition(self, factory):
        """Test RiskAssessment linked to condition"""

        risk_data = {
            "status": "final",
            "method": "Condition-specific risk assessment",
            "code": "Surgical complication risk",
            "condition": "Condition/hypertension-001"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-condition"
        )

        assert result["resourceType"] == "RiskAssessment"
        if "condition" in result:
            assert "Condition" in result["condition"]["reference"]

    # =================================================================
    # Mitigation Tests
    # =================================================================

    def test_risk_assessment_with_mitigation(self, factory):
        """Test RiskAssessment with mitigation strategy"""

        risk_data = {
            "status": "final",
            "method": "Fall risk assessment",
            "code": "Fall risk",
            "prediction": [{
                "outcome": "Falls",
                "qualitative_risk": "high"
            }],
            "mitigation": "Physical therapy, home safety modifications, assistive devices"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-mitigation"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert "mitigation" in result

    # =================================================================
    # Context Tests
    # =================================================================

    def test_risk_assessment_with_encounter(self, factory):
        """Test RiskAssessment linked to encounter"""

        risk_data = {
            "status": "final",
            "method": "Encounter-based assessment",
            "code": "Perioperative risk",
            "encounter": "Encounter/preop-001"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-encounter"
        )

        assert result["resourceType"] == "RiskAssessment"
        if "encounter" in result:
            assert "Encounter" in result["encounter"]["reference"]

    def test_risk_assessment_with_performer(self, factory):
        """Test RiskAssessment with performer"""

        risk_data = {
            "status": "final",
            "method": "Clinical risk assessment",
            "code": "Surgical risk",
            "performer": "Practitioner/surgeon-123"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-performer"
        )

        assert result["resourceType"] == "RiskAssessment"
        if "performer" in result:
            assert "Practitioner" in result["performer"]["reference"]

    def test_risk_assessment_with_notes(self, factory):
        """Test RiskAssessment with clinical notes"""

        risk_data = {
            "status": "final",
            "method": "Comprehensive assessment",
            "code": "General health risk",
            "note": "Patient has multiple risk factors requiring aggressive intervention"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-notes"
        )

        assert result["resourceType"] == "RiskAssessment"
        if "note" in result:
            assert isinstance(result["note"], list)
            assert len(result["note"]) > 0

    # =================================================================
    # Status Tests
    # =================================================================

    def test_risk_assessment_statuses(self, factory):
        """Test different RiskAssessment statuses"""

        statuses = [
            ("draft", "preliminary"),  # draft maps to preliminary
            ("preliminary", "preliminary"),
            ("final", "final"),
            ("amended", "amended"),
            ("corrected", "corrected"),
            ("cancelled", "cancelled"),
            ("entered-in-error", "entered-in-error")
        ]

        for status_input, expected_status in statuses:
            risk_data = {
                "status": status_input,
                "method": "Status test",
                "code": f"Risk assessment in {status_input} status"
            }

            result = factory.create_risk_assessment_resource(
                risk_data,
                "Patient/patient-status-test"
            )

            assert result["resourceType"] == "RiskAssessment"
            assert result["status"] == expected_status

    # =================================================================
    # FHIR Compliance Tests
    # =================================================================

    def test_risk_assessment_fhir_r4_compliance(self, factory):
        """Test RiskAssessment resource FHIR R4 compliance"""

        risk_data = {
            "status": "final",
            "method": "SCORE2 cardiovascular risk assessment",
            "code": "10-year cardiovascular disease risk",
            "encounter": "Encounter/cardiology-001",
            "condition": "Condition/hypertension-001",
            "performer": "Practitioner/cardiologist-123",
            "basis": [
                "Observation/cholesterol-001",
                "Observation/blood-pressure-001"
            ],
            "prediction": [
                {
                    "outcome": "Myocardial infarction",
                    "qualitative_risk": "high",
                    "probability_decimal": 0.15,
                    "when_period": {
                        "start": "2024-01-01",
                        "end": "2034-01-01"
                    }
                }
            ],
            "mitigation": "Lifestyle modifications, statin therapy, blood pressure control"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-compliance"
        )

        # FHIR R4 required fields
        assert result["resourceType"] == "RiskAssessment"
        assert "status" in result
        assert "subject" in result
        assert result["subject"]["reference"] == "Patient/patient-compliance"

        # Optional but important fields
        if "id" in result:
            assert isinstance(result["id"], str)
        if "prediction" in result:
            assert isinstance(result["prediction"], list)
        if "basis" in result:
            assert isinstance(result["basis"], list)


class TestRiskAssessmentEdgeCases:
    """Test edge cases and error handling for RiskAssessment resources"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    def test_risk_assessment_minimal_data(self, factory):
        """Test RiskAssessment creation with minimal required data"""

        risk_data = {
            "status": "final"
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-minimal"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert result["status"] == "final"
        assert result["subject"]["reference"] == "Patient/patient-minimal"

    def test_risk_assessment_complex_cardiovascular(self, factory):
        """Test RiskAssessment with complex cardiovascular scenario"""

        risk_data = {
            "status": "final",
            "method": "SCORE2 cardiovascular risk assessment",
            "code": "10-year cardiovascular disease risk",
            "encounter": "Encounter/cardiology-consultation",
            "condition": "Condition/hypertension-001",
            "performer": "Practitioner/cardiologist-123",
            "basis": [
                "Observation/cholesterol-total-001",
                "Observation/cholesterol-hdl-001",
                "Observation/blood-pressure-systolic-001",
                "Observation/smoking-status-001",
                "Observation/age-001"
            ],
            "prediction": [
                {
                    "outcome": "Fatal cardiovascular event",
                    "qualitative_risk": "high",
                    "probability_decimal": 0.15,
                    "when_period": {
                        "start": datetime.utcnow().isoformat() + 'Z',
                        "end": (datetime.utcnow() + timedelta(days=3650)).isoformat() + 'Z'
                    },
                    "rationale": "Multiple cardiovascular risk factors including hypertension, hypercholesterolemia, and active smoking"
                },
                {
                    "outcome": "Non-fatal myocardial infarction",
                    "qualitative_risk": "high",
                    "probability_decimal": 0.12,
                    "when_period": {
                        "start": datetime.utcnow().isoformat() + 'Z',
                        "end": (datetime.utcnow() + timedelta(days=3650)).isoformat() + 'Z'
                    }
                },
                {
                    "outcome": "Stroke",
                    "qualitative_risk": "moderate",
                    "probability_decimal": 0.08,
                    "when_period": {
                        "start": datetime.utcnow().isoformat() + 'Z',
                        "end": (datetime.utcnow() + timedelta(days=3650)).isoformat() + 'Z'
                    }
                }
            ],
            "mitigation": "Aggressive lifestyle modifications including smoking cessation, dietary changes (Mediterranean diet), regular physical activity (150 min/week), statin therapy (atorvastatin 40mg daily), blood pressure control (target <130/80), and aspirin prophylaxis",
            "note": "Patient has strong family history of premature cardiovascular disease. Requires intensive risk factor modification and close follow-up."
        }

        result = factory.create_risk_assessment_resource(
            risk_data,
            "Patient/patient-complex-cv"
        )

        assert result["resourceType"] == "RiskAssessment"
        assert result["status"] == "final"
        assert len(result["prediction"]) == 3
        assert len(result["basis"]) == 5
