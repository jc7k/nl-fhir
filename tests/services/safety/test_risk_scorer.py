"""
Comprehensive test suite for SafetyRiskScorer
Tests multi-factor risk assessment and alert generation

Story 4.2: Safety Risk Scoring and Alert Generation System
Critical patient safety feature - integrates all safety checks
"""

import pytest
from typing import Dict, Any

from src.nl_fhir.services.safety.risk_scorer import SafetyRiskScorer
from src.nl_fhir.services.safety.risk_models import RiskLevel


class TestSafetyRiskScorer:
    """Test suite for safety risk scoring"""

    @pytest.fixture
    def scorer(self):
        """Get initialized risk scorer"""
        return SafetyRiskScorer()

    @pytest.fixture
    def sample_bundle(self):
        """Sample FHIR bundle with patient and medications"""
        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {"resource": {
                    "resourceType": "Patient",
                    "id": "patient-123",
                    "birthDate": "1970-05-15",
                    "gender": "male"
                }},
                {"resource": {
                    "resourceType": "MedicationRequest",
                    "id": "med-1",
                    "status": "active",
                    "medicationCodeableConcept": {"text": "Warfarin"},
                    "subject": {"reference": "Patient/patient-123"}
                }}
            ]
        }

    @pytest.fixture
    def mock_interaction_results(self):
        """Mock interaction check results"""
        return {
            "has_interactions": True,
            "interaction_count": 2,
            "interactions": [
                {"severity": "major", "drug_a": "Warfarin", "drug_b": "Aspirin"}
            ],
            "severity_breakdown": {
                "contraindicated": 0,
                "major": 2,
                "moderate": 0,
                "minor": 0
            }
        }

    @pytest.fixture
    def mock_contraindication_results(self):
        """Mock contraindication check results"""
        return {
            "has_contraindications": False,
            "contraindication_count": 0,
            "contraindications": [],
            "severity_breakdown": {
                "absolute": 0,
                "relative": 0,
                "caution": 0,
                "warning": 0
            }
        }

    @pytest.fixture
    def mock_dosage_results(self):
        """Mock dosage validation results"""
        return {
            "has_dosage_violations": False,
            "violation_count": 0,
            "violations": [],
            "severity_breakdown": {
                "critical": 0,
                "high": 0,
                "moderate": 0,
                "low": 0
            }
        }

    # =================================================================
    # Initialization Tests
    # =================================================================

    def test_scorer_initialization(self, scorer):
        """Test scorer initializes with risk weights"""
        assert scorer.risk_weights is not None
        assert len(scorer.risk_weights) > 0

    # =================================================================
    # Risk Score Calculation Tests
    # =================================================================

    def test_calculate_risk_score_low_risk(self, scorer, sample_bundle,
                                           mock_contraindication_results,
                                           mock_dosage_results):
        """Test risk score calculation for low-risk scenario"""
        # No interactions, contraindications, or dosage issues
        interaction_results = {
            "has_interactions": False,
            "interaction_count": 0,
            "interactions": [],
            "severity_breakdown": {"contraindicated": 0, "major": 0, "moderate": 0, "minor": 0}
        }

        risk_score = scorer.calculate_safety_risk_score(
            sample_bundle,
            interaction_results,
            mock_contraindication_results,
            mock_dosage_results
        )

        assert risk_score.overall_score >= 0
        assert risk_score.overall_score <= 100
        assert risk_score.risk_level in [RiskLevel.MINIMAL, RiskLevel.LOW]
        assert len(risk_score.recommendations) > 0

    def test_calculate_risk_score_high_risk(self, scorer, sample_bundle,
                                            mock_contraindication_results):
        """Test risk score calculation for high-risk scenario"""
        # High-risk interactions and dosage violations
        interaction_results = {
            "has_interactions": True,
            "interaction_count": 3,
            "interactions": [],
            "severity_breakdown": {"contraindicated": 2, "major": 1, "moderate": 0, "minor": 0}
        }

        dosage_results = {
            "has_dosage_violations": True,
            "violation_count": 2,
            "violations": [],
            "severity_breakdown": {"critical": 1, "high": 1, "moderate": 0, "low": 0}
        }

        risk_score = scorer.calculate_safety_risk_score(
            sample_bundle,
            interaction_results,
            mock_contraindication_results,
            dosage_results
        )

        assert risk_score.overall_score > 50  # Should be high risk
        assert risk_score.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    # =================================================================
    # Risk Component Scoring Tests
    # =================================================================

    def test_score_drug_interactions_none(self, scorer):
        """Test scoring with no drug interactions"""
        results = {
            "has_interactions": False,
            "interactions": [],
            "severity_breakdown": {"contraindicated": 0, "major": 0, "moderate": 0, "minor": 0}
        }

        score_data = scorer._score_drug_interactions(results)

        assert score_data["score"] == 0
        assert "no" in score_data["description"].lower()

    def test_score_drug_interactions_major(self, scorer, mock_interaction_results):
        """Test scoring with major drug interactions"""
        score_data = scorer._score_drug_interactions(mock_interaction_results)

        assert score_data["score"] > 0
        assert len(score_data["risk_factors"]) > 0

    def test_score_contraindications_none(self, scorer, mock_contraindication_results):
        """Test scoring with no contraindications"""
        score_data = scorer._score_contraindications(mock_contraindication_results)

        assert score_data["score"] == 0

    def test_score_dosage_safety_violations(self, scorer):
        """Test scoring with dosage violations"""
        results = {
            "has_dosage_violations": True,
            "violation_count": 2,
            "violations": [],
            "severity_breakdown": {"critical": 1, "high": 0, "moderate": 1, "low": 0}
        }

        score_data = scorer._score_dosage_safety(results)

        assert score_data["score"] > 0
        assert len(score_data["risk_factors"]) > 0

    # =================================================================
    # Patient Complexity Scoring Tests
    # =================================================================

    def test_score_patient_complexity_geriatric(self, scorer):
        """Test patient complexity scoring for geriatric patient"""
        patient_info = {"age": 80, "gender": "female"}
        conditions = [{"normalized_name": "diabetes"}, {"normalized_name": "heart failure"}]
        medications = [{"normalized_name": "warfarin"}]

        score_data = scorer._score_patient_complexity(patient_info, conditions, medications)

        assert score_data["score"] > 0  # Geriatric + multiple conditions
        assert len(score_data["risk_factors"]) > 0

    def test_score_patient_complexity_pediatric(self, scorer):
        """Test patient complexity scoring for pediatric patient"""
        patient_info = {"age": 10, "gender": "male"}
        conditions = []
        medications = []

        score_data = scorer._score_patient_complexity(patient_info, conditions, medications)

        assert score_data["score"] > 0  # Pediatric = specialized dosing

    def test_score_patient_complexity_multiple_comorbidities(self, scorer):
        """Test scoring with multiple comorbidities"""
        patient_info = {"age": 65, "gender": "male"}
        conditions = [
            {"normalized_name": "diabetes"},
            {"normalized_name": "hypertension"},
            {"normalized_name": "kidney disease"},
            {"normalized_name": "heart failure"},
            {"normalized_name": "copd"}
        ]
        medications = []

        score_data = scorer._score_patient_complexity(patient_info, conditions, medications)

        assert score_data["score"] > 0
        assert "comorbidities" in score_data["description"].lower()

    # =================================================================
    # Medication Burden Tests
    # =================================================================

    def test_score_medication_burden_minimal(self, scorer):
        """Test medication burden scoring with few medications"""
        medications = [{"normalized_name": "metformin"}]

        score_data = scorer._score_medication_burden(medications)

        assert score_data["score"] == 0
        assert "minimal" in score_data["description"].lower()

    def test_score_medication_burden_polypharmacy(self, scorer):
        """Test medication burden scoring with polypharmacy"""
        medications = [{"normalized_name": f"med-{i}"} for i in range(10)]

        score_data = scorer._score_medication_burden(medications)

        assert score_data["score"] > 0
        assert "polypharmacy" in score_data["description"].lower()

    # =================================================================
    # Risk Level Classification Tests
    # =================================================================

    def test_classify_risk_level_minimal(self, scorer):
        """Test risk level classification for minimal risk"""
        assert scorer._classify_risk_level(10) == RiskLevel.MINIMAL

    def test_classify_risk_level_low(self, scorer):
        """Test risk level classification for low risk"""
        assert scorer._classify_risk_level(30) == RiskLevel.LOW

    def test_classify_risk_level_moderate(self, scorer):
        """Test risk level classification for moderate risk"""
        assert scorer._classify_risk_level(50) == RiskLevel.MODERATE

    def test_classify_risk_level_high(self, scorer):
        """Test risk level classification for high risk"""
        assert scorer._classify_risk_level(70) == RiskLevel.HIGH

    def test_classify_risk_level_critical(self, scorer):
        """Test risk level classification for critical risk"""
        assert scorer._classify_risk_level(90) == RiskLevel.CRITICAL

    # =================================================================
    # Recommendation Generation Tests
    # =================================================================

    def test_generate_recommendations_low_risk(self, scorer):
        """Test recommendations for low-risk scenario"""
        risk_components = {
            "drug_interactions": {"score": 5, "description": "test"},
            "contraindications": {"score": 0, "description": "test"},
            "dosage_concerns": {"score": 0, "description": "test"},
            "patient_complexity": {"score": 0, "description": "test"},
            "monitoring_requirements": {"score": 0, "description": "test"},
            "medication_burden": {"score": 0, "description": "test"}
        }

        recommendations = scorer._generate_risk_recommendations(risk_components, RiskLevel.LOW)

        assert isinstance(recommendations, list)

    def test_generate_recommendations_critical_risk(self, scorer):
        """Test recommendations for critical-risk scenario"""
        risk_components = {
            "drug_interactions": {"score": 60, "description": "test"},
            "contraindications": {"score": 25, "description": "test"},
            "dosage_concerns": {"score": 50, "description": "test"},
            "patient_complexity": {"score": 30, "description": "test"},
            "monitoring_requirements": {"score": 25, "description": "test"},
            "medication_burden": {"score": 20, "description": "test"}
        }

        recommendations = scorer._generate_risk_recommendations(risk_components, RiskLevel.CRITICAL)

        assert len(recommendations) > 0
        # Should have urgent recommendation
        assert any("URGENT" in rec for rec in recommendations)

    # =================================================================
    # Integration Tests
    # =================================================================

    def test_complete_risk_scoring_workflow(self, scorer, sample_bundle,
                                           mock_interaction_results,
                                           mock_contraindication_results,
                                           mock_dosage_results):
        """Test complete end-to-end risk scoring"""
        risk_score = scorer.calculate_safety_risk_score(
            sample_bundle,
            mock_interaction_results,
            mock_contraindication_results,
            mock_dosage_results
        )

        # Verify complete structure
        assert risk_score.overall_score >= 0
        assert risk_score.overall_score <= 100
        assert isinstance(risk_score.risk_level, RiskLevel)
        assert isinstance(risk_score.contributing_factors, dict)
        assert isinstance(risk_score.recommendations, list)
        assert isinstance(risk_score.monitoring_requirements, list)
        assert isinstance(risk_score.escalation_triggers, list)

    def test_performance(self, scorer, sample_bundle,
                        mock_interaction_results,
                        mock_contraindication_results,
                        mock_dosage_results):
        """Test performance of risk scoring"""
        import time

        start_time = time.time()
        risk_score = scorer.calculate_safety_risk_score(
            sample_bundle,
            mock_interaction_results,
            mock_contraindication_results,
            mock_dosage_results
        )
        elapsed = time.time() - start_time

        assert elapsed < 0.5  # Should be fast
        assert risk_score.overall_score >= 0
