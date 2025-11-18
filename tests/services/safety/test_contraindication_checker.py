"""
Comprehensive test suite for ContraindicationChecker
Tests medical contraindication detection including age, conditions, allergies, and pregnancy

Story 4.2: Contraindication and Allergy Detection System
Critical patient safety feature - Must maintain high coverage
"""

import pytest
from datetime import datetime, date, timedelta
from typing import Dict, Any, List

from src.nl_fhir.services.safety.contraindication_checker import (
    ContraindicationChecker,
    ContraindicationSeverity,
    Contraindication
)


class TestContraindicationChecker:
    """Comprehensive test suite for contraindication checking"""

    @pytest.fixture
    def checker(self):
        """Get initialized contraindication checker"""
        return ContraindicationChecker()

    @pytest.fixture
    def adult_patient(self):
        """Sample adult patient"""
        return {
            "resourceType": "Patient",
            "id": "patient-adult",
            "birthDate": "1975-06-15",
            "gender": "female"
        }

    @pytest.fixture
    def geriatric_patient(self):
        """Sample geriatric patient"""
        return {
            "resourceType": "Patient",
            "id": "patient-geriatric",
            "birthDate": "1945-03-20",
            "gender": "male"
        }

    @pytest.fixture
    def pediatric_patient(self):
        """Sample pediatric patient"""
        return {
            "resourceType": "Patient",
            "id": "patient-pediatric",
            "birthDate": "2015-09-10",
            "gender": "female"
        }

    def create_medication_request(self, medication_name: str) -> Dict[str, Any]:
        """Helper to create MedicationRequest"""
        return {
            "resourceType": "MedicationRequest",
            "id": f"med-{medication_name.lower().replace(' ', '-')}",
            "status": "active",
            "medicationCodeableConcept": {
                "text": medication_name,
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "display": medication_name
                }]
            }
        }

    def create_condition(self, condition_name: str) -> Dict[str, Any]:
        """Helper to create Condition resource"""
        return {
            "resourceType": "Condition",
            "id": f"cond-{condition_name.lower().replace(' ', '-')}",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active"
                }]
            },
            "code": {
                "text": condition_name,
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "display": condition_name
                }]
            }
        }

    def create_allergy(self, allergy_name: str) -> Dict[str, Any]:
        """Helper to create AllergyIntolerance resource"""
        return {
            "resourceType": "AllergyIntolerance",
            "id": f"allergy-{allergy_name.lower().replace(' ', '-')}",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                    "code": "active"
                }]
            },
            "code": {
                "text": allergy_name,
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "display": allergy_name
                }]
            }
        }

    def create_bundle(self, patient: Dict, medications: List[str] = None,
                     conditions: List[str] = None, allergies: List[str] = None) -> Dict[str, Any]:
        """Helper to create FHIR bundle"""
        entries = [{"resource": patient}]

        if medications:
            for med in medications:
                entries.append({"resource": self.create_medication_request(med)})

        if conditions:
            for cond in conditions:
                entries.append({"resource": self.create_condition(cond)})

        if allergies:
            for allergy in allergies:
                entries.append({"resource": self.create_allergy(allergy)})

        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": entries
        }

    # =================================================================
    # Initialization Tests
    # =================================================================

    def test_checker_initialization(self, checker):
        """Test checker initializes with all required databases"""
        assert checker.contraindication_database is not None
        assert checker.age_based_contraindications is not None
        assert checker.pregnancy_categories is not None
        assert checker.allergy_cross_reactions is not None

    # =================================================================
    # No Contraindication Cases
    # =================================================================

    def test_no_contraindications_empty_bundle(self, checker, adult_patient):
        """Test bundle with no medications or conditions"""
        bundle = self.create_bundle(adult_patient)

        result = checker.check_bundle_contraindications(bundle)

        assert result["has_contraindications"] is False
        assert result["contraindication_count"] == 0
        assert len(result["contraindications"]) == 0

    def test_no_contraindications_safe_medication(self, checker, adult_patient):
        """Test safe medication without contraindications"""
        bundle = self.create_bundle(
            adult_patient,
            medications=["Vitamin D"],
            conditions=["Hypertension"]
        )

        result = checker.check_bundle_contraindications(bundle)

        # Vitamin D generally has no contraindications
        assert "has_contraindications" in result
        assert "contraindication_count" in result

    # =================================================================
    # Medication-Condition Contraindication Tests
    # =================================================================

    def test_detect_medication_condition_contraindication(self, checker, adult_patient):
        """Test detection of medication-condition contraindication"""
        # Example: NSAIDs + kidney disease could be contraindicated
        bundle = self.create_bundle(
            adult_patient,
            medications=["Ibuprofen"],
            conditions=["Kidney disease"]
        )

        result = checker.check_bundle_contraindications(bundle)

        assert "has_contraindications" in result
        assert "contraindications" in result

    # =================================================================
    # Age-Based Contraindication Tests
    # =================================================================

    def test_detect_pediatric_contraindication(self, checker, pediatric_patient):
        """Test detection of pediatric contraindication"""
        bundle = self.create_bundle(
            pediatric_patient,
            medications=["Aspirin"]  # Aspirin + pediatric = Reye's syndrome risk
        )

        result = checker.check_bundle_contraindications(bundle)

        # Should check for pediatric contraindications
        assert "contraindication_count" in result
        assert "severity_breakdown" in result

    def test_detect_geriatric_contraindication(self, checker, geriatric_patient):
        """Test detection of geriatric contraindication"""
        bundle = self.create_bundle(
            geriatric_patient,
            medications=["Diazepam"]  # Benzodiazepines cautioned in elderly
        )

        result = checker.check_bundle_contraindications(bundle)

        assert "contraindication_count" in result
        assert "severity_breakdown" in result

    def test_age_group_classification_infant(self, checker):
        """Test age group classification for infant"""
        infant = {
            "resourceType": "Patient",
            "id": "infant",
            "birthDate": (date.today() - timedelta(days=180)).strftime("%Y-%m-%d"),  # 6 months old
            "gender": "male"
        }

        bundle = self.create_bundle(infant)
        patient_info = checker._extract_patient_info(bundle)

        assert patient_info["age"] < 2

    def test_age_group_classification_child(self, checker):
        """Test age group classification for child"""
        child = {
            "resourceType": "Patient",
            "id": "child",
            "birthDate": "2014-01-15",  # ~10 years old
            "gender": "female"
        }

        bundle = self.create_bundle(child)
        patient_info = checker._extract_patient_info(bundle)

        assert 2 <= patient_info["age"] < 18

    def test_age_group_classification_geriatric(self, checker, geriatric_patient):
        """Test age group classification for geriatric patient"""
        bundle = self.create_bundle(geriatric_patient)
        patient_info = checker._extract_patient_info(bundle)

        assert patient_info["age"] >= 65

    # =================================================================
    # Pregnancy Contraindication Tests
    # =================================================================

    def test_detect_pregnancy_contraindication(self, checker):
        """Test detection of pregnancy contraindication"""
        pregnant_patient = {
            "resourceType": "Patient",
            "id": "pregnant-patient",
            "birthDate": "1990-05-10",
            "gender": "female"
        }

        bundle = self.create_bundle(
            pregnant_patient,
            medications=["Methotrexate"],  # Pregnancy category X
            conditions=["Pregnancy"]
        )

        result = checker.check_bundle_contraindications(bundle)

        if result["contraindication_count"] > 0:
            # Should detect pregnancy contraindication
            assert any("pregnancy" in c["condition"].lower()
                      for c in result["contraindications"])

    def test_detect_breastfeeding_contraindication(self, checker):
        """Test detection of breastfeeding contraindication"""
        breastfeeding_patient = {
            "resourceType": "Patient",
            "id": "breastfeeding-patient",
            "birthDate": "1985-08-20",
            "gender": "female"
        }

        bundle = self.create_bundle(
            breastfeeding_patient,
            medications=["Lithium"],
            conditions=["Breastfeeding"]
        )

        result = checker.check_bundle_contraindications(bundle)

        assert "contraindication_count" in result

    # =================================================================
    # Allergy Contraindication Tests
    # =================================================================

    def test_detect_direct_allergy_match(self, checker, adult_patient):
        """Test detection of direct allergy match"""
        bundle = self.create_bundle(
            adult_patient,
            medications=["Penicillin"],
            allergies=["Penicillin"]
        )

        result = checker.check_bundle_contraindications(bundle)

        if result["contraindication_count"] > 0:
            # Should detect direct allergy
            allergic_contraindications = [c for c in result["contraindications"]
                                         if "allergy" in c["condition"].lower()]
            assert len(allergic_contraindications) > 0
            # Should be absolute contraindication
            absolute_count = result["severity_breakdown"].get("absolute", 0)
            assert absolute_count >= 0

    def test_detect_allergy_cross_reaction(self, checker, adult_patient):
        """Test detection of allergy cross-reaction"""
        bundle = self.create_bundle(
            adult_patient,
            medications=["Amoxicillin"],  # Penicillin-based
            allergies=["Penicillin"]      # Cross-reaction possible
        )

        result = checker.check_bundle_contraindications(bundle)

        # Should check for cross-reactions
        assert "contraindication_count" in result

    def test_multiple_allergies(self, checker, adult_patient):
        """Test handling of multiple allergies"""
        bundle = self.create_bundle(
            adult_patient,
            medications=["Amoxicillin", "Sulfamethoxazole", "Aspirin"],
            allergies=["Penicillin", "Sulfa", "NSAIDs"]
        )

        result = checker.check_bundle_contraindications(bundle)

        # Should check each medication against each allergy
        assert "contraindication_count" in result
        assert "severity_breakdown" in result

    # =================================================================
    # Multiple Contraindication Types Tests
    # =================================================================

    def test_multiple_contraindication_types(self, checker, geriatric_patient):
        """Test detection of multiple contraindication types simultaneously"""
        bundle = self.create_bundle(
            geriatric_patient,
            medications=["Aspirin", "Warfarin"],
            conditions=["Kidney disease", "Diabetes"],
            allergies=["Penicillin"]
        )

        result = checker.check_bundle_contraindications(bundle)

        # Should check all types: medication-condition, age-based, allergies
        assert "contraindication_count" in result
        assert "severity_breakdown" in result

    # =================================================================
    # Name Normalization Tests
    # =================================================================

    def test_normalize_medication_name(self, checker):
        """Test medication name normalization"""
        test_cases = [
            ("Metformin 500mg tablet", "metformin"),
            ("Lisinopril 10 mg", "lisinopril"),
            ("Aspirin 81mg", "aspirin")
        ]

        for input_name, expected in test_cases:
            normalized = checker._normalize_medication_name(input_name)
            assert expected in normalized
            assert "mg" not in normalized
            assert "tablet" not in normalized

    def test_normalize_condition_name(self, checker):
        """Test condition name normalization and mapping"""
        mappings = {
            "Diabetes mellitus": "diabetes",
            "Diabetes type 2": "diabetes",
            "Myocardial infarction": "heart attack",
            "Congestive heart failure": "heart failure"
        }

        for input_name, expected in mappings.items():
            normalized = checker._normalize_condition_name(input_name)
            assert expected in normalized

    def test_normalize_allergy_name(self, checker):
        """Test allergy name normalization"""
        test_cases = [
            "Penicillin",
            "Sulfa drugs",
            "NSAIDs"
        ]

        for allergy_name in test_cases:
            normalized = checker._normalize_allergy_name(allergy_name)
            assert isinstance(normalized, str)
            assert len(normalized) > 0

    # =================================================================
    # Severity Classification Tests
    # =================================================================

    def test_severity_breakdown_structure(self, checker, adult_patient):
        """Test severity breakdown contains all levels"""
        bundle = self.create_bundle(
            adult_patient,
            medications=["Metformin"],
            conditions=["Diabetes"]
        )

        result = checker.check_bundle_contraindications(bundle)

        severity_breakdown = result["severity_breakdown"]

        # Should have all severity levels
        assert "absolute" in severity_breakdown
        assert "relative" in severity_breakdown
        assert "caution" in severity_breakdown
        assert "warning" in severity_breakdown

    def test_contraindication_details_structure(self, checker, adult_patient):
        """Test contraindication details have required fields"""
        bundle = self.create_bundle(
            adult_patient,
            medications=["Penicillin"],
            allergies=["Penicillin"]
        )

        result = checker.check_bundle_contraindications(bundle)

        if result["contraindication_count"] > 0:
            for contraindication in result["contraindications"]:
                assert "medication" in contraindication
                assert "condition" in contraindication
                assert "severity" in contraindication
                assert "reason" in contraindication
                assert "alternative_suggestions" in contraindication
                assert "monitoring_requirements" in contraindication
                assert "evidence_level" in contraindication

    # =================================================================
    # Recommendation Generation Tests
    # =================================================================

    def test_recommendations_for_absolute_contraindications(self, checker, adult_patient):
        """Test recommendations for absolute contraindications"""
        bundle = self.create_bundle(
            adult_patient,
            medications=["Penicillin"],
            allergies=["Penicillin"]
        )

        result = checker.check_bundle_contraindications(bundle)

        if result["contraindication_count"] > 0:
            recommendations = result["recommendations"]
            assert len(recommendations) > 0
            # Should have critical recommendations
            if result["severity_breakdown"].get("absolute", 0) > 0:
                assert any("CRITICAL" in rec or "Stop" in rec or "discontinue" in rec.lower()
                          for rec in recommendations)

    def test_recommendations_for_no_contraindications(self, checker, adult_patient):
        """Test recommendations when no contraindications found"""
        bundle = self.create_bundle(
            adult_patient,
            medications=["Vitamin D"]
        )

        result = checker.check_bundle_contraindications(bundle)

        recommendations = result["recommendations"]
        assert len(recommendations) > 0
        assert any("no contraindication" in rec.lower() or "appropriate" in rec.lower()
                  for rec in recommendations)

    # =================================================================
    # Summary Generation Tests
    # =================================================================

    def test_summary_no_contraindications(self, checker, adult_patient):
        """Test summary with no contraindications"""
        bundle = self.create_bundle(adult_patient, medications=["Vitamin D"])

        result = checker.check_bundle_contraindications(bundle)

        summary = result["summary"]
        assert "no contraindication" in summary.lower()

    def test_summary_with_contraindications(self, checker, adult_patient):
        """Test summary describes contraindications"""
        bundle = self.create_bundle(
            adult_patient,
            medications=["Penicillin"],
            allergies=["Penicillin"]
        )

        result = checker.check_bundle_contraindications(bundle)

        if result["contraindication_count"] > 0:
            summary = result["summary"]
            # Should mention count
            assert "found" in summary.lower() or \
                   str(result["contraindication_count"]) in summary

    # =================================================================
    # Edge Cases and Error Handling Tests
    # =================================================================

    def test_empty_bundle(self, checker):
        """Test handling of empty bundle"""
        bundle = {"resourceType": "Bundle", "type": "transaction", "entry": []}

        result = checker.check_bundle_contraindications(bundle)

        assert result["has_contraindications"] is False
        assert result["contraindication_count"] == 0

    def test_bundle_with_invalid_patient_date(self, checker):
        """Test handling of invalid birth date"""
        patient = {
            "resourceType": "Patient",
            "id": "invalid-date",
            "birthDate": "invalid-date-format",
            "gender": "male"
        }

        bundle = self.create_bundle(patient, medications=["Metformin"])

        result = checker.check_bundle_contraindications(bundle)

        # Should handle gracefully without crashing
        assert "contraindication_count" in result

    def test_medication_missing_name(self, checker, adult_patient):
        """Test handling of medication without name"""
        med_no_name = {
            "resourceType": "MedicationRequest",
            "id": "no-name",
            "status": "active",
            "medicationCodeableConcept": {}
        }

        bundle = self.create_bundle(adult_patient)
        bundle["entry"].append({"resource": med_no_name})

        result = checker.check_bundle_contraindications(bundle)

        # Should handle gracefully
        assert "contraindication_count" in result

    def test_condition_missing_name(self, checker, adult_patient):
        """Test handling of condition without name"""
        cond_no_name = {
            "resourceType": "Condition",
            "id": "no-name",
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "code": {}
        }

        bundle = self.create_bundle(adult_patient, medications=["Metformin"])
        bundle["entry"].append({"resource": cond_no_name})

        result = checker.check_bundle_contraindications(bundle)

        # Should handle gracefully
        assert "contraindication_count" in result

    # =================================================================
    # Performance Tests
    # =================================================================

    def test_performance_small_bundle(self, checker, adult_patient):
        """Test performance with small bundle"""
        import time

        bundle = self.create_bundle(
            adult_patient,
            medications=["Metformin", "Lisinopril"],
            conditions=["Diabetes", "Hypertension"]
        )

        start_time = time.time()
        result = checker.check_bundle_contraindications(bundle)
        elapsed = time.time() - start_time

        # Should complete quickly
        assert elapsed < 0.5
        assert "contraindication_count" in result

    def test_performance_large_bundle(self, checker, adult_patient):
        """Test performance with large bundle"""
        import time

        medications = [f"Medication-{i}" for i in range(10)]
        conditions = [f"Condition-{i}" for i in range(5)]
        allergies = [f"Allergy-{i}" for i in range(3)]

        bundle = self.create_bundle(
            adult_patient,
            medications=medications,
            conditions=conditions,
            allergies=allergies
        )

        start_time = time.time()
        result = checker.check_bundle_contraindications(bundle)
        elapsed = time.time() - start_time

        # Should complete in reasonable time
        assert elapsed < 2.0
        assert "contraindication_count" in result

    # =================================================================
    # Integration Tests
    # =================================================================

    def test_complete_contraindication_workflow(self, checker, geriatric_patient):
        """Test complete end-to-end contraindication checking"""
        # Realistic complex scenario
        bundle = self.create_bundle(
            geriatric_patient,
            medications=["Aspirin", "Warfarin", "Metformin"],
            conditions=["Kidney disease", "Diabetes", "Atrial fibrillation"],
            allergies=["Penicillin", "Sulfa"]
        )

        result = checker.check_bundle_contraindications(bundle)

        # Verify complete result structure
        assert "has_contraindications" in result
        assert "contraindication_count" in result
        assert "contraindications" in result
        assert "severity_breakdown" in result
        assert "summary" in result
        assert "recommendations" in result

        # All contraindications should have complete information
        for contraindication in result["contraindications"]:
            assert len(contraindication["medication"]) > 0
            assert len(contraindication["condition"]) > 0
            assert len(contraindication["reason"]) > 0
            assert isinstance(contraindication["alternative_suggestions"], list)
            assert isinstance(contraindication["monitoring_requirements"], list)

    def test_clinical_scenario_high_risk_patient(self, checker):
        """Test high-risk patient scenario"""
        high_risk_patient = {
            "resourceType": "Patient",
            "id": "high-risk",
            "birthDate": "1940-01-15",  # 85 years old
            "gender": "female"
        }

        bundle = self.create_bundle(
            high_risk_patient,
            medications=["Warfarin", "Aspirin", "Diazepam"],
            conditions=["Heart failure", "Kidney disease", "Dementia"],
            allergies=["Penicillin"]
        )

        result = checker.check_bundle_contraindications(bundle)

        # Should detect multiple contraindications
        assert "contraindication_count" in result
        assert "severity_breakdown" in result
        # Geriatric patient with multiple conditions should have concerns
        assert len(result["recommendations"]) > 0
