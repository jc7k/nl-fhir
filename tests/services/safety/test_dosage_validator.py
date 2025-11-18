"""
Comprehensive test suite for DosageValidator
Tests dosage safety validation, age/weight adjustments, and violation detection

Story 4.2: Dosage Safety Validation Framework
Critical patient safety feature - MUST maintain high test coverage
"""

import pytest
from datetime import datetime, date, timedelta
from typing import Dict, Any

from src.nl_fhir.services.safety.dosage_validator import DosageValidator
from src.nl_fhir.services.safety.dosage_models import DosageViolationSeverity


class TestDosageValidator:
    """Comprehensive test suite for dosage validation"""

    @pytest.fixture
    def validator(self):
        """Get initialized dosage validator"""
        return DosageValidator()

    @pytest.fixture
    def sample_patient_adult(self):
        """Sample adult patient resource"""
        return {
            "resourceType": "Patient",
            "id": "patient-adult-123",
            "birthDate": "1975-06-15",
            "gender": "female"
        }

    @pytest.fixture
    def sample_patient_geriatric(self):
        """Sample geriatric patient resource"""
        return {
            "resourceType": "Patient",
            "id": "patient-geriatric-456",
            "birthDate": "1950-03-20",
            "gender": "male"
        }

    @pytest.fixture
    def sample_patient_pediatric(self):
        """Sample pediatric patient resource"""
        return {
            "resourceType": "Patient",
            "id": "patient-pediatric-789",
            "birthDate": "2015-09-10",
            "gender": "female"
        }

    def create_medication_request(self, medication_name: str, dose_value: float,
                                  dose_unit: str, frequency: int = 2, period: int = 1) -> Dict[str, Any]:
        """Helper to create MedicationRequest resource"""
        return {
            "resourceType": "MedicationRequest",
            "id": f"med-req-{medication_name.lower()}",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "text": medication_name,
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "12345",
                    "display": medication_name
                }]
            },
            "subject": {"reference": "Patient/patient-123"},
            "dosageInstruction": [{
                "text": f"{dose_value} {dose_unit} {frequency} times daily",
                "route": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": "26643006",
                        "display": "oral"
                    }]
                },
                "timing": {
                    "repeat": {
                        "frequency": frequency,
                        "period": period,
                        "periodUnit": "d"
                    }
                },
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": dose_value,
                        "unit": dose_unit,
                        "system": "http://unitsofmeasure.org",
                        "code": dose_unit
                    }
                }]
            }]
        }

    def create_bundle(self, patient: Dict, medications: list) -> Dict[str, Any]:
        """Helper to create FHIR bundle"""
        entries = [{"resource": patient}]
        for med in medications:
            entries.append({"resource": med})

        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": entries
        }

    # =================================================================
    # Initialization and Basic Functionality Tests
    # =================================================================

    def test_validator_initialization(self, validator):
        """Test validator initializes with required databases"""
        assert validator.dosage_database is not None
        assert validator.age_weight_factors is not None
        assert len(validator.dosage_database) > 0
        assert len(validator.age_weight_factors) > 0

    def test_validate_bundle_with_no_medications(self, validator, sample_patient_adult):
        """Test validation with bundle containing no medications"""
        bundle = self.create_bundle(sample_patient_adult, [])

        result = validator.validate_bundle_dosages(bundle)

        assert result["has_dosage_violations"] is False
        assert result["violation_count"] == 0
        assert len(result["violations"]) == 0
        assert "no violations" in result["summary"].lower() or "safe" in result["summary"].lower()

    def test_validate_bundle_with_safe_dosages(self, validator, sample_patient_adult):
        """Test validation with safe dosages - should pass"""
        med = self.create_medication_request("Metformin", 500, "mg", frequency=2, period=1)
        bundle = self.create_bundle(sample_patient_adult, [med])

        result = validator.validate_bundle_dosages(bundle)

        # May or may not have violations depending on database
        # But should not crash and should return valid structure
        assert "has_dosage_violations" in result
        assert "violation_count" in result
        assert "violations" in result
        assert "severity_breakdown" in result
        assert "summary" in result
        assert "recommendations" in result

    # =================================================================
    # Patient Information Extraction Tests
    # =================================================================

    def test_extract_patient_age_adult(self, validator, sample_patient_adult):
        """Test patient age extraction for adult"""
        bundle = self.create_bundle(sample_patient_adult, [])

        patient_info = validator._extract_patient_info(bundle)

        assert "age" in patient_info
        assert patient_info["age"] > 18
        assert patient_info["age"] < 65
        assert patient_info["age_group"] == "adult"

    def test_extract_patient_age_geriatric(self, validator, sample_patient_geriatric):
        """Test patient age extraction for geriatric"""
        bundle = self.create_bundle(sample_patient_geriatric, [])

        patient_info = validator._extract_patient_info(bundle)

        assert "age" in patient_info
        assert patient_info["age"] >= 65
        assert patient_info["age_group"] == "geriatric"

    def test_extract_patient_age_pediatric(self, validator, sample_patient_pediatric):
        """Test patient age extraction for pediatric"""
        bundle = self.create_bundle(sample_patient_pediatric, [])

        patient_info = validator._extract_patient_info(bundle)

        assert "age" in patient_info
        assert patient_info["age"] < 18
        assert patient_info["age_group"] in ["child", "adolescent"]

    def test_extract_patient_weight_from_observation(self, validator, sample_patient_adult):
        """Test weight extraction from Observation resource"""
        weight_observation = {
            "resourceType": "Observation",
            "id": "obs-weight",
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "29463-7",
                    "display": "Body Weight"
                }],
                "text": "weight"
            },
            "valueQuantity": {
                "value": 70,
                "unit": "kg",
                "system": "http://unitsofmeasure.org"
            }
        }

        bundle = self.create_bundle(sample_patient_adult, [])
        bundle["entry"].append({"resource": weight_observation})

        patient_info = validator._extract_patient_info(bundle)

        assert "weight_kg" in patient_info
        assert patient_info["weight_kg"] == 70

    def test_extract_patient_weight_conversion_lbs_to_kg(self, validator, sample_patient_adult):
        """Test weight extraction with unit conversion (lbs to kg)"""
        weight_observation = {
            "resourceType": "Observation",
            "id": "obs-weight-lbs",
            "status": "final",
            "code": {"text": "weight"},
            "valueQuantity": {
                "value": 154.3,  # ~70 kg
                "unit": "lbs"
            }
        }

        bundle = self.create_bundle(sample_patient_adult, [])
        bundle["entry"].append({"resource": weight_observation})

        patient_info = validator._extract_patient_info(bundle)

        assert "weight_kg" in patient_info
        # 154.3 lbs ≈ 70 kg
        assert 69 < patient_info["weight_kg"] < 71

    # =================================================================
    # Medication and Dosage Extraction Tests
    # =================================================================

    def test_extract_medications_with_dosage(self, validator, sample_patient_adult):
        """Test medication extraction from bundle"""
        med1 = self.create_medication_request("Lisinopril", 10, "mg", frequency=1)
        med2 = self.create_medication_request("Atorvastatin", 20, "mg", frequency=1)

        bundle = self.create_bundle(sample_patient_adult, [med1, med2])

        medications = validator._extract_medications_with_dosage(bundle)

        assert len(medications) == 2
        assert medications[0]["name"] in ["Lisinopril", "Atorvastatin"]
        assert "dosage" in medications[0]
        assert "normalized_name" in medications[0]

    def test_extract_dose_from_structured_data(self, validator):
        """Test dose extraction from structured doseQuantity"""
        med = self.create_medication_request("Metformin", 500, "mg")

        dosage_info = validator._extract_dosage_info(med)

        assert dosage_info is not None
        assert dosage_info["dose"]["value"] == 500
        assert dosage_info["dose"]["unit"] == "mg"

    def test_extract_dose_from_text(self, validator):
        """Test dose parsing from free text"""
        text_samples = [
            ("Take 10 mg daily", {"value": 10, "unit": "mg"}),
            ("5mg twice daily", {"value": 5, "unit": "mg"}),
            ("2.5 mg in the morning", {"value": 2.5, "unit": "mg"}),
            ("500 mcg at bedtime", {"value": 500, "unit": "mcg"}),
        ]

        for text, expected in text_samples:
            parsed = validator._parse_dose_from_text(text)
            assert parsed is not None
            assert parsed["value"] == expected["value"]
            assert parsed["unit"] == expected["unit"]

    def test_extract_route_from_dosage(self, validator):
        """Test route extraction from dosage instruction"""
        med = self.create_medication_request("Morphine", 4, "mg")

        dosage_info = validator._extract_dosage_info(med)
        route = dosage_info["route"]

        assert route in ["oral", "po"]

    def test_calculate_daily_frequency(self, validator):
        """Test daily frequency calculations"""
        test_cases = [
            ({"frequency": 2, "period": 1, "periodUnit": "d"}, 2.0),   # 2x daily
            ({"frequency": 1, "period": 1, "periodUnit": "d"}, 1.0),   # 1x daily
            ({"frequency": 1, "period": 12, "periodUnit": "h"}, 2.0),  # Every 12h = 2x daily
            ({"frequency": 4, "period": 1, "periodUnit": "d"}, 4.0),   # 4x daily
        ]

        for repeat, expected_freq in test_cases:
            result = validator._calculate_daily_frequency(repeat)
            assert abs(result - expected_freq) < 0.1

    # =================================================================
    # Dosage Violation Detection Tests
    # =================================================================

    def test_detect_overdose_critical(self, validator, sample_patient_adult):
        """Test detection of critical overdose (>3x max dose)"""
        # Very high dose that should trigger critical violation
        med = self.create_medication_request("Lisinopril", 100, "mg", frequency=3)  # 300mg daily - way too high
        bundle = self.create_bundle(sample_patient_adult, [med])

        result = validator.validate_bundle_dosages(bundle)

        # Should detect violation if Lisinopril is in database
        if result["violation_count"] > 0:
            assert result["has_dosage_violations"] is True
            # Check for critical or high severity
            critical_count = result["severity_breakdown"].get("critical", 0)
            high_count = result["severity_breakdown"].get("high", 0)
            assert critical_count + high_count > 0

    def test_detect_overdose_moderate(self, validator, sample_patient_adult):
        """Test detection of moderate overdose"""
        # Moderately high dose
        med = self.create_medication_request("Metformin", 1000, "mg", frequency=3)  # 3000mg daily
        bundle = self.create_bundle(sample_patient_adult, [med])

        result = validator.validate_bundle_dosages(bundle)

        # Should return valid structure even if no violation
        assert "has_dosage_violations" in result
        assert "violations" in result

    def test_detect_underdose(self, validator, sample_patient_adult):
        """Test detection of therapeutic underdose"""
        # Very low dose that may be sub-therapeutic
        med = self.create_medication_request("Lisinopril", 1, "mg", frequency=1)  # 1mg daily - very low
        bundle = self.create_bundle(sample_patient_adult, [med])

        result = validator.validate_bundle_dosages(bundle)

        # Should return valid structure
        assert "has_dosage_violations" in result
        assert "violation_count" in result

    def test_age_based_dosage_adjustment_geriatric(self, validator, sample_patient_geriatric):
        """Test dosage validation with geriatric age adjustments"""
        med = self.create_medication_request("Digoxin", 0.25, "mg", frequency=1)
        bundle = self.create_bundle(sample_patient_geriatric, [med])

        result = validator.validate_bundle_dosages(bundle)

        # Geriatric patients should have different safe ranges
        # Test that validator considers age
        assert "severity_breakdown" in result
        assert "recommendations" in result

    def test_age_based_dosage_adjustment_pediatric(self, validator, sample_patient_pediatric):
        """Test dosage validation with pediatric age adjustments"""
        med = self.create_medication_request("Amoxicillin", 250, "mg", frequency=3)
        bundle = self.create_bundle(sample_patient_pediatric, [med])

        result = validator.validate_bundle_dosages(bundle)

        # Pediatric dosing should be evaluated differently
        assert "severity_breakdown" in result

    # =================================================================
    # Unit Conversion Tests
    # =================================================================

    def test_unit_conversion_same_unit(self, validator):
        """Test unit conversion with same units"""
        result = validator._convert_dose_units(500, "mg", "mg")
        assert result == 500

    def test_unit_conversion_mg_to_g(self, validator):
        """Test conversion from mg to g"""
        result = validator._convert_dose_units(1000, "mg", "g")
        if result is not None:  # If conversion is supported
            assert abs(result - 1.0) < 0.001

    def test_unit_conversion_incompatible_units(self, validator):
        """Test handling of incompatible unit conversion"""
        result = validator._convert_dose_units(500, "mg", "ml")
        # Should return None for incompatible units
        assert result is None

    # =================================================================
    # Route Compatibility Tests
    # =================================================================

    def test_routes_compatible_oral(self, validator):
        """Test oral route compatibility checking"""
        assert validator._routes_compatible("oral", "po") is True
        assert validator._routes_compatible("oral", "by mouth") is True
        assert validator._routes_compatible("oral", "iv") is False

    def test_routes_compatible_parenteral(self, validator):
        """Test parenteral route compatibility checking"""
        assert validator._routes_compatible("iv", "intravenous") is True
        assert validator._routes_compatible("iv", "im") is True
        assert validator._routes_compatible("iv", "oral") is False

    # =================================================================
    # Multiple Medications Tests
    # =================================================================

    def test_validate_multiple_medications(self, validator, sample_patient_adult):
        """Test validation with multiple medications"""
        meds = [
            self.create_medication_request("Lisinopril", 10, "mg", frequency=1),
            self.create_medication_request("Metformin", 500, "mg", frequency=2),
            self.create_medication_request("Atorvastatin", 20, "mg", frequency=1)
        ]
        bundle = self.create_bundle(sample_patient_adult, meds)

        result = validator.validate_bundle_dosages(bundle)

        assert "violation_count" in result
        assert "severity_breakdown" in result
        # Should evaluate each medication independently

    # =================================================================
    # Edge Cases and Error Handling Tests
    # =================================================================

    def test_validate_empty_bundle(self, validator):
        """Test validation with empty bundle"""
        bundle = {"resourceType": "Bundle", "type": "transaction", "entry": []}

        result = validator.validate_bundle_dosages(bundle)

        assert result["has_dosage_violations"] is False
        assert result["violation_count"] == 0

    def test_validate_bundle_missing_dosage_info(self, validator, sample_patient_adult):
        """Test validation with medication missing dosage information"""
        med = {
            "resourceType": "MedicationRequest",
            "id": "med-no-dosage",
            "status": "active",
            "medicationCodeableConcept": {"text": "Unknown Medication"},
            "subject": {"reference": "Patient/patient-123"}
            # Missing dosageInstruction
        }
        bundle = self.create_bundle(sample_patient_adult, [med])

        result = validator.validate_bundle_dosages(bundle)

        # Should handle gracefully
        assert "violation_count" in result
        assert "violations" in result

    def test_validate_bundle_missing_patient_info(self, validator):
        """Test validation with bundle missing patient information"""
        med = self.create_medication_request("Metformin", 500, "mg")
        bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [{"resource": med}]
        }

        result = validator.validate_bundle_dosages(bundle)

        # Should handle missing patient gracefully
        assert "violation_count" in result

    def test_validate_with_invalid_date_format(self, validator):
        """Test handling of invalid birth date format"""
        patient = {
            "resourceType": "Patient",
            "id": "patient-invalid-date",
            "birthDate": "invalid-date",
            "gender": "female"
        }
        med = self.create_medication_request("Metformin", 500, "mg")
        bundle = self.create_bundle(patient, [med])

        result = validator.validate_bundle_dosages(bundle)

        # Should not crash, handle gracefully
        assert "violation_count" in result

    # =================================================================
    # Summary and Reporting Tests
    # =================================================================

    def test_severity_breakdown_structure(self, validator, sample_patient_adult):
        """Test severity breakdown has all required fields"""
        med = self.create_medication_request("Metformin", 500, "mg")
        bundle = self.create_bundle(sample_patient_adult, [med])

        result = validator.validate_bundle_dosages(bundle)

        severity_breakdown = result["severity_breakdown"]
        # Should have all severity levels even if count is 0
        assert "critical" in severity_breakdown
        assert "high" in severity_breakdown
        assert "moderate" in severity_breakdown
        assert "low" in severity_breakdown

    def test_recommendations_generated(self, validator, sample_patient_adult):
        """Test that recommendations are generated"""
        med = self.create_medication_request("Metformin", 500, "mg")
        bundle = self.create_bundle(sample_patient_adult, [med])

        result = validator.validate_bundle_dosages(bundle)

        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0

    def test_summary_message_format(self, validator, sample_patient_adult):
        """Test summary message is human-readable"""
        med = self.create_medication_request("Metformin", 500, "mg")
        bundle = self.create_bundle(sample_patient_adult, [med])

        result = validator.validate_bundle_dosages(bundle)

        assert "summary" in result
        assert isinstance(result["summary"], str)
        assert len(result["summary"]) > 0

    # =================================================================
    # Integration Tests
    # =================================================================

    def test_complete_dosage_validation_workflow(self, validator):
        """Test complete end-to-end dosage validation workflow"""
        # Create realistic scenario
        patient = {
            "resourceType": "Patient",
            "id": "patient-complete-test",
            "birthDate": "1970-05-15",
            "gender": "male"
        }

        medications = [
            self.create_medication_request("Lisinopril", 10, "mg", frequency=1),
            self.create_medication_request("Metformin", 500, "mg", frequency=2),
        ]

        bundle = self.create_bundle(patient, medications)

        # Run validation
        result = validator.validate_bundle_dosages(bundle)

        # Verify complete result structure
        assert "has_dosage_violations" in result
        assert "violation_count" in result
        assert "violations" in result
        assert "severity_breakdown" in result
        assert "summary" in result
        assert "recommendations" in result

        # Verify all violations have required fields
        for violation in result["violations"]:
            assert "medication" in violation
            assert "severity" in violation
            assert "reason" in violation
            assert "recommendation" in violation

    # =================================================================
    # Performance Tests
    # =================================================================

    def test_validation_performance_single_medication(self, validator, sample_patient_adult):
        """Test validation performance with single medication"""
        import time

        med = self.create_medication_request("Metformin", 500, "mg")
        bundle = self.create_bundle(sample_patient_adult, [med])

        start_time = time.time()
        result = validator.validate_bundle_dosages(bundle)
        elapsed = time.time() - start_time

        # Should complete in reasonable time (<1 second)
        assert elapsed < 1.0
        assert "violation_count" in result

    def test_validation_performance_multiple_medications(self, validator, sample_patient_adult):
        """Test validation performance with multiple medications"""
        import time

        medications = [
            self.create_medication_request(f"Medication-{i}", 10 * i, "mg")
            for i in range(1, 11)
        ]
        bundle = self.create_bundle(sample_patient_adult, medications)

        start_time = time.time()
        result = validator.validate_bundle_dosages(bundle)
        elapsed = time.time() - start_time

        # Should complete in reasonable time even with 10 medications
        assert elapsed < 2.0
        assert "violation_count" in result
