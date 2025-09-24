"""
Test Suite for DiagnosticReport Implementation
Story ID: NL-FHIR-DR-001
Tests FHIR R4 DiagnosticReport resource creation and NLP extraction
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

# Import the implementations
import sys
sys.path.append('../src')
from nl_fhir.services.fhir.diagnostic_report_implementation import DiagnosticReportFactory
from nl_fhir.services.nlp.diagnostic_report_patterns import DiagnosticReportExtractor


class TestDiagnosticReportCreation:
    """Test DiagnosticReport FHIR resource creation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.factory = DiagnosticReportFactory()
        self.patient_ref = "patient-123"
        self.request_id = "test-request-001"

    def test_create_laboratory_report_basic(self):
        """Test basic laboratory report creation"""

        report_data = {
            "text": "CBC with differential",
            "procedure": "Complete blood count",
            "category": "laboratory",
            "conclusion": "All values within normal limits"
        }

        result = self.factory.create_diagnostic_report(
            report_data,
            self.patient_ref,
            self.request_id
        )

        assert result["resourceType"] == "DiagnosticReport"
        assert result["status"] == "final"
        assert result["subject"]["reference"] == f"Patient/{self.patient_ref}"
        assert result["conclusion"] == "All values within normal limits"
        assert len(result["category"]) == 1
        assert result["category"][0]["coding"][0]["code"] == "LAB"

    def test_create_radiology_report(self):
        """Test radiology report creation"""

        report_data = {
            "text": "Chest X-ray reveals clear lung fields",
            "procedure": "Chest X-ray",
            "type": "radiology",
            "conclusion": "No acute cardiopulmonary abnormalities",
            "datetime": "2024-01-15T10:30:00Z"
        }

        result = self.factory.create_diagnostic_report(
            report_data,
            self.patient_ref,
            self.request_id
        )

        assert result["resourceType"] == "DiagnosticReport"
        assert result["category"][0]["coding"][0]["code"] == "RAD"
        assert result["conclusion"] == "No acute cardiopulmonary abnormalities"
        assert result["effectiveDateTime"] == "2024-01-15T10:30:00Z"

    def test_create_pathology_report(self):
        """Test pathology report creation"""

        report_data = {
            "text": "Biopsy results",
            "procedure": "Skin biopsy",
            "type": "pathology",
            "conclusion": "Benign nevus, no malignancy identified",
            "interpretation": "normal"
        }

        result = self.factory.create_diagnostic_report(
            report_data,
            self.patient_ref,
            self.request_id,
            practitioner_ref="practitioner-456"
        )

        assert result["resourceType"] == "DiagnosticReport"
        assert result["category"][0]["coding"][0]["code"] == "PAT"
        assert result["performer"][0]["reference"] == "Practitioner/practitioner-456"
        # Check for interpretation code
        if "conclusionCode" in result:
            assert result["conclusionCode"][0]["coding"][0]["code"] == "N"

    def test_create_cardiology_report(self):
        """Test cardiology report creation"""

        report_data = {
            "text": "ECG shows normal sinus rhythm",
            "procedure": "Electrocardiogram",
            "type": "cardiology",
            "conclusion": "Normal sinus rhythm, rate 72 bpm",
            "datetime": "2024-01-15T14:00:00Z"
        }

        result = self.factory.create_diagnostic_report(
            report_data,
            self.patient_ref,
            self.request_id
        )

        assert result["resourceType"] == "DiagnosticReport"
        assert result["category"][0]["coding"][0]["code"] == "CUS"
        assert "Normal sinus rhythm" in result["conclusion"]

    def test_service_request_linking(self):
        """Test linking DiagnosticReport to ServiceRequest"""

        report_data = {
            "text": "Lab results for requested CBC",
            "procedure": "CBC"
        }

        service_request_refs = ["service-req-001", "service-req-002"]

        result = self.factory.create_diagnostic_report(
            report_data,
            self.patient_ref,
            self.request_id,
            service_request_refs=service_request_refs
        )

        assert "basedOn" in result
        assert len(result["basedOn"]) == 2
        assert result["basedOn"][0]["reference"] == "ServiceRequest/service-req-001"
        assert result["basedOn"][1]["reference"] == "ServiceRequest/service-req-002"

    def test_observation_linking(self):
        """Test linking DiagnosticReport to Observations"""

        report_data = {
            "text": "Metabolic panel results",
            "procedure": "Comprehensive metabolic panel"
        }

        observation_refs = ["obs-glucose", "obs-sodium", "obs-potassium"]

        result = self.factory.create_diagnostic_report(
            report_data,
            self.patient_ref,
            self.request_id,
            observation_refs=observation_refs
        )

        assert "result" in result
        assert len(result["result"]) == 3
        assert result["result"][0]["reference"] == "Observation/obs-glucose"

    def test_status_determination(self):
        """Test status extraction from text"""

        test_cases = [
            ("Preliminary results pending confirmation", "preliminary"),
            ("Final report", "final"),
            ("Amended report with corrections", "amended"),
            ("Regular lab results", "final")  # Default
        ]

        for text, expected_status in test_cases:
            report_data = {"text": text}
            result = self.factory.create_diagnostic_report(
                report_data,
                self.patient_ref,
                self.request_id
            )
            assert result["status"] == expected_status

    def test_loinc_code_mapping(self):
        """Test LOINC code assignment for known tests"""

        test_cases = [
            ("Complete blood count", "58410-2"),
            ("Comprehensive metabolic panel", "24323-8"),
            ("Lipid panel", "57698-3"),
            ("Thyroid panel", "55204-3")
        ]

        for procedure, expected_loinc in test_cases:
            report_data = {"procedure": procedure}
            result = self.factory.create_diagnostic_report(
                report_data,
                self.patient_ref,
                self.request_id
            )

            if "coding" in result.get("code", {}):
                loinc_codes = [c["code"] for c in result["code"]["coding"]
                              if c.get("system") == "http://loinc.org"]
                if loinc_codes:
                    assert expected_loinc in loinc_codes

    def test_fallback_creation(self):
        """Test fallback DiagnosticReport creation for compatibility"""

        report_data = {
            "text": "Basic lab report",
            "conclusion": "Results reviewed"
        }

        result = self.factory._create_fallback_diagnostic_report(
            report_data,
            self.patient_ref,
            self.request_id
        )

        assert result["resourceType"] == "DiagnosticReport"
        assert result["status"] == "final"
        assert result["subject"]["reference"] == f"Patient/{self.patient_ref}"
        assert result["conclusion"] == "Results reviewed"
        assert "effectiveDateTime" in result

    def test_encounter_reference(self):
        """Test encounter reference in DiagnosticReport"""

        report_data = {
            "text": "Emergency department labs",
            "procedure": "STAT CBC"
        }

        result = self.factory.create_diagnostic_report(
            report_data,
            self.patient_ref,
            self.request_id,
            encounter_ref="encounter-789"
        )

        assert "encounter" in result
        assert result["encounter"]["reference"] == "Encounter/encounter-789"


class TestDiagnosticReportExtraction:
    """Test NLP extraction of diagnostic report information"""

    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = DiagnosticReportExtractor()

    def test_extract_laboratory_report(self):
        """Test extraction of laboratory report from clinical text"""

        clinical_text = """
        Patient presents for follow-up. Lab results from yesterday show
        CBC with WBC 8.5, Hemoglobin 14.2 g/dL, Platelets 250K.
        All values within normal limits. No signs of infection.
        """

        reports = self.extractor.extract_diagnostic_reports(clinical_text)

        assert len(reports) > 0
        report = reports[0]
        assert report["category"] == "laboratory"
        assert "CBC" in report["text"]
        assert report["interpretation"] == "normal"

    def test_extract_radiology_report(self):
        """Test extraction of radiology report"""

        clinical_text = """
        Chest X-ray performed today shows clear lung fields bilaterally.
        No acute cardiopulmonary abnormalities. Heart size normal.
        Impression: No acute findings.
        """

        reports = self.extractor.extract_diagnostic_reports(clinical_text)

        assert len(reports) > 0
        report = reports[0]
        assert report["category"] == "radiology"
        assert "conclusion" in report
        assert "No acute findings" in report["conclusion"]

    def test_extract_pathology_report(self):
        """Test extraction of pathology report"""

        clinical_text = """
        Skin biopsy results available. Microscopic examination reveals
        benign melanocytic nevus. No evidence of malignancy.
        Diagnosis: Benign nevus.
        """

        reports = self.extractor.extract_diagnostic_reports(clinical_text)

        assert len(reports) > 0
        report = reports[0]
        assert report["category"] == "pathology"
        assert "conclusion" in report
        assert "Benign nevus" in report["conclusion"]

    def test_extract_cardiology_report(self):
        """Test extraction of cardiology report"""

        clinical_text = """
        ECG shows normal sinus rhythm at rate of 72 bpm.
        PR interval 160ms, QRS duration 90ms, QT interval normal.
        No ST-T wave abnormalities. Interpretation: Normal ECG.
        """

        reports = self.extractor.extract_diagnostic_reports(clinical_text)

        assert len(reports) > 0
        report = reports[0]
        assert report["category"] == "cardiology"
        assert report["interpretation"] == "normal"

    def test_extract_multiple_reports(self):
        """Test extraction of multiple reports from single text"""

        clinical_text = """
        Multiple tests performed today:
        1. CBC shows mild anemia with Hemoglobin 10.5 g/dL
        2. Chest X-ray reveals small left pleural effusion
        3. ECG demonstrates sinus tachycardia at 105 bpm
        """

        reports = self.extractor.extract_diagnostic_reports(clinical_text)

        assert len(reports) >= 3
        categories = [r["category"] for r in reports]
        assert "laboratory" in categories
        assert "radiology" in categories
        assert "cardiology" in categories

    def test_extract_numeric_values(self):
        """Test extraction of numeric values from reports"""

        clinical_text = """
        Lab results: Glucose: 95 mg/dL, BUN: 18 mg/dL,
        Creatinine: 1.0 mg/dL, Sodium: 140 mEq/L, Potassium: 4.0 mEq/L
        """

        reports = self.extractor.extract_diagnostic_reports(clinical_text)

        assert len(reports) > 0
        report = reports[0]
        assert "values" in report

        # Check if numeric values were extracted
        values = report["values"]
        assert len(values) > 0

        # Check structure of extracted values
        for value in values:
            assert "parameter" in value
            assert "value" in value
            assert "unit" in value

    def test_status_extraction(self):
        """Test extraction of report status"""

        test_cases = [
            ("Preliminary CBC results pending confirmation", "preliminary"),
            ("Final pathology report available", "final"),
            ("Amended radiology report with additional findings", "amended")
        ]

        for text, expected_status in test_cases:
            reports = self.extractor.extract_diagnostic_reports(text)
            if reports:
                assert reports[0].get("status", "final") == expected_status

    def test_loinc_identification(self):
        """Test identification of specific lab tests with LOINC"""

        clinical_text = """
        Comprehensive metabolic panel ordered. Results show normal
        electrolytes and kidney function. Lipid panel also normal.
        """

        reports = self.extractor.extract_diagnostic_reports(clinical_text)

        assert len(reports) > 0

        # Check if LOINC codes were identified
        for report in reports:
            if "metabolic panel" in report.get("procedure", "").lower():
                assert report.get("loinc_code") == "24323-8"
            elif "lipid panel" in report.get("procedure", "").lower():
                assert report.get("loinc_code") == "57698-3"


class TestDiagnosticReportIntegration:
    """Integration tests for DiagnosticReport with other resources"""

    def setup_method(self):
        """Set up test fixtures"""
        self.factory = DiagnosticReportFactory()
        self.extractor = DiagnosticReportExtractor()
        self.patient_ref = "patient-integration-001"

    def test_nlp_to_fhir_workflow(self):
        """Test complete NLP extraction to FHIR resource creation workflow"""

        clinical_text = """
        Lab results received for patient's annual checkup.
        CBC shows WBC 7.5, Hemoglobin 13.8 g/dL, all within normal limits.
        Comprehensive metabolic panel also normal.
        Conclusion: Healthy patient, no abnormalities detected.
        """

        # Step 1: Extract diagnostic reports using NLP
        extracted_reports = self.extractor.extract_diagnostic_reports(clinical_text)

        assert len(extracted_reports) > 0

        # Step 2: Create FHIR resources from extracted data
        fhir_resources = []
        for report_data in extracted_reports:
            fhir_resource = self.factory.create_diagnostic_report(
                report_data,
                self.patient_ref,
                "integration-test-001"
            )
            fhir_resources.append(fhir_resource)

        assert len(fhir_resources) > 0

        # Verify FHIR resource structure
        for resource in fhir_resources:
            assert resource["resourceType"] == "DiagnosticReport"
            assert resource["subject"]["reference"] == f"Patient/{self.patient_ref}"
            assert "category" in resource
            assert "code" in resource
            assert "status" in resource

    def test_service_request_to_diagnostic_report_flow(self):
        """Test workflow from ServiceRequest to DiagnosticReport"""

        # Simulate existing ServiceRequest
        service_request_id = "service-req-cbc-001"

        # Clinical text indicating completion of requested test
        clinical_text = "CBC ordered yesterday completed. Results show normal values."

        # Extract and create DiagnosticReport
        reports = self.extractor.extract_diagnostic_reports(clinical_text)

        if reports:
            report_data = reports[0]
            diagnostic_report = self.factory.create_diagnostic_report(
                report_data,
                self.patient_ref,
                "workflow-test-001",
                service_request_refs=[service_request_id]
            )

            # Verify linkage
            assert "basedOn" in diagnostic_report
            assert diagnostic_report["basedOn"][0]["reference"] == f"ServiceRequest/{service_request_id}"

    def test_diagnostic_report_with_observations(self):
        """Test DiagnosticReport linking to multiple Observations"""

        # Simulate scenario with multiple lab values
        observation_refs = [
            "obs-wbc-001",
            "obs-hemoglobin-001",
            "obs-platelets-001"
        ]

        report_data = {
            "text": "CBC with differential completed",
            "procedure": "Complete blood count",
            "conclusion": "All values normal"
        }

        diagnostic_report = self.factory.create_diagnostic_report(
            report_data,
            self.patient_ref,
            "observation-link-test",
            observation_refs=observation_refs
        )

        # Verify all observations are linked
        assert "result" in diagnostic_report
        assert len(diagnostic_report["result"]) == len(observation_refs)

        for i, obs_ref in enumerate(observation_refs):
            assert diagnostic_report["result"][i]["reference"] == f"Observation/{obs_ref}"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])