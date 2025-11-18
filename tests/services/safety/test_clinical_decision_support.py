"""
Comprehensive test suite for ClinicalDecisionSupport
Tests evidence-based clinical recommendations

Story 4.2: Clinical Decision Support System
Critical for evidence-based clinical guidance
"""

import pytest
from typing import Dict, Any

from src.nl_fhir.services.safety.clinical_decision_support import (
    ClinicalDecisionSupport,
    RecommendationType,
    EvidenceLevel,
    ClinicalRecommendation
)


class TestClinicalDecisionSupport:
    """Test suite for clinical decision support"""

    @pytest.fixture
    def cds(self):
        """Get initialized clinical decision support system"""
        return ClinicalDecisionSupport()

    @pytest.fixture
    def sample_bundle_with_context(self):
        """Sample bundle with patient, medications, and conditions"""
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
                    "id": "med-warfarin",
                    "status": "active",
                    "medicationCodeableConcept": {"text": "Warfarin"},
                    "dosageInstruction": [{"text": "5 mg daily"}]
                }},
                {"resource": {
                    "resourceType": "Condition",
                    "id": "cond-afib",
                    "code": {"text": "Atrial fibrillation"}
                }},
                {"resource": {
                    "resourceType": "Observation",
                    "id": "obs-inr",
                    "status": "final",
                    "code": {"text": "INR"},
                    "valueQuantity": {"value": 2.5, "unit": "ratio"}
                }}
            ]
        }

    # =================================================================
    # Initialization Tests
    # =================================================================

    def test_cds_initialization(self, cds):
        """Test CDS initializes with all required databases"""
        assert cds.guideline_database is not None
        assert cds.monitoring_protocols is not None
        assert cds.alternative_therapies is not None
        assert cds.drug_food_interactions is not None

    # =================================================================
    # Recommendation Generation Tests
    # =================================================================

    def test_generate_clinical_recommendations_basic(self, cds, sample_bundle_with_context):
        """Test basic recommendation generation"""
        result = cds.generate_clinical_recommendations(sample_bundle_with_context)

        assert "has_recommendations" in result
        assert "recommendation_count" in result
        assert "recommendations" in result
        assert "categorized_recommendations" in result
        assert "summary" in result
        assert "implementation_priority" in result

    def test_recommendations_structure(self, cds, sample_bundle_with_context):
        """Test recommendation structure"""
        result = cds.generate_clinical_recommendations(sample_bundle_with_context)

        if result["recommendation_count"] > 0:
            for rec in result["recommendations"]:
                assert "medication" in rec or "type" in rec
                assert "recommendation" in rec
                assert "rationale" in rec
                assert "evidence_level" in rec
                assert "priority" in rec

    def test_generate_recommendations_no_medications(self, cds):
        """Test with bundle containing no medications"""
        bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [{"resource": {
                "resourceType": "Patient",
                "id": "patient-no-meds",
                "birthDate": "1980-01-01",
                "gender": "female"
            }}]
        }

        result = cds.generate_clinical_recommendations(bundle)

        assert "recommendation_count" in result
        # Should still provide general recommendations

    # =================================================================
    # Patient Information Extraction Tests
    # =================================================================

    def test_extract_patient_age_group_adult(self, cds):
        """Test age group extraction for adult"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [{"resource": {
                "resourceType": "Patient",
                "birthDate": "1970-01-01",
                "gender": "male"
            }}]
        }

        patient_info = cds._extract_patient_info(bundle)

        assert "age" in patient_info
        assert patient_info["age_group"] == "adult"

    def test_extract_patient_age_group_geriatric(self, cds):
        """Test age group extraction for geriatric"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [{"resource": {
                "resourceType": "Patient",
                "birthDate": "1950-01-01",
                "gender": "female"
            }}]
        }

        patient_info = cds._extract_patient_info(bundle)

        assert patient_info["age_group"] == "geriatric"

    def test_extract_patient_age_group_pediatric(self, cds):
        """Test age group extraction for pediatric"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [{"resource": {
                "resourceType": "Patient",
                "birthDate": "2015-01-01",
                "gender": "male"
            }}]
        }

        patient_info = cds._extract_patient_info(bundle)

        assert patient_info["age_group"] == "pediatric"

    # =================================================================
    # Lab Results Extraction Tests
    # =================================================================

    def test_extract_lab_results(self, cds, sample_bundle_with_context):
        """Test extraction of relevant lab results"""
        lab_results = cds._extract_lab_results(sample_bundle_with_context)

        # Sample bundle has INR observation
        assert isinstance(lab_results, list)

    # =================================================================
    # Edge Cases Tests
    # =================================================================

    def test_empty_bundle(self, cds):
        """Test handling of empty bundle"""
        bundle = {"resourceType": "Bundle", "type": "transaction", "entry": []}

        result = cds.generate_clinical_recommendations(bundle)

        assert "recommendation_count" in result
        assert result["recommendation_count"] >= 0

    def test_bundle_missing_patient(self, cds):
        """Test bundle without patient resource"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [{"resource": {
                "resourceType": "MedicationRequest",
                "medicationCodeableConcept": {"text": "Metformin"}
            }}]
        }

        result = cds.generate_clinical_recommendations(bundle)

        # Should handle gracefully
        assert "recommendation_count" in result

    # =================================================================
    # Performance Tests
    # =================================================================

    def test_performance(self, cds, sample_bundle_with_context):
        """Test performance of recommendation generation"""
        import time

        start_time = time.time()
        result = cds.generate_clinical_recommendations(sample_bundle_with_context)
        elapsed = time.time() - start_time

        assert elapsed < 1.0  # Should complete quickly
        assert "recommendation_count" in result

    # =================================================================
    # Integration Tests
    # =================================================================

    def test_complete_cds_workflow(self, cds, sample_bundle_with_context):
        """Test complete CDS workflow"""
        result = cds.generate_clinical_recommendations(sample_bundle_with_context)

        # Verify complete structure
        assert isinstance(result["has_recommendations"], bool)
        assert isinstance(result["recommendation_count"], int)
        assert isinstance(result["recommendations"], list)
        assert isinstance(result["categorized_recommendations"], dict)
        assert isinstance(result["summary"], str)
        assert isinstance(result["implementation_priority"], list)
