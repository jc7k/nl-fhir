#!/usr/bin/env python3
"""
Integration Tests for DiagnosticReport Implementation (Story DR-002)
Tests end-to-end DiagnosticReport functionality from clinical text to FHIR bundle
"""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add src path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nl_fhir.services.conversion import ConversionService
from nl_fhir.models.request import ClinicalRequestAdvanced


class TestDiagnosticReportIntegration:
    """Integration tests for complete DiagnosticReport workflow"""

    @pytest.fixture(scope="class")
    def conversion_service(self):
        """Create conversion service instance for testing"""
        return ConversionService()

    @pytest.fixture(scope="class")
    def sample_clinical_texts(self):
        """Sample clinical texts containing diagnostic reports"""
        return {
            "laboratory_cbc": {
                "text": "Patient John Doe presents for routine follow-up. Lab results from 01/15/2024: CBC shows WBC 7.5 K/uL (normal 4.5-11.0), RBC 4.8 M/uL (normal 4.2-5.4), Hemoglobin 14.2 g/dL (normal 12.0-16.0), Hematocrit 42.5% (normal 37-48). All values within normal limits. Recommend routine screening in 1 year.",
                "expected_category": "laboratory",
                "expected_procedure": "cbc"
            },
            "radiology_chest_xray": {
                "text": "Patient underwent chest X-ray examination. Chest X-ray shows clear lung fields with no acute cardiopulmonary abnormalities. Heart size is normal. No pleural effusion or pneumothorax. Impression: Normal chest X-ray.",
                "expected_category": "radiology",
                "expected_procedure": "chest x-ray"
            },
            "cardiology_ecg": {
                "text": "Patient had ECG performed in clinic. ECG shows normal sinus rhythm at 72 bpm with normal axis and intervals. No ST changes or arrhythmias noted. QTc interval is normal at 420 ms. Impression: Normal ECG.",
                "expected_category": "cardiology",
                "expected_procedure": "ecg"
            },
            "pathology_biopsy": {
                "text": "Pathology results from skin biopsy of left arm lesion. Microscopic examination reveals benign seborrheic keratosis with no evidence of malignancy. Mild chronic inflammation present. Impression: Benign seborrheic keratosis, no malignancy.",
                "expected_category": "pathology",
                "expected_procedure": "skin biopsy"
            },
            "multiple_reports": {
                "text": "Patient completed multiple studies today. Lab work shows normal CBC and basic metabolic panel. Chest X-ray demonstrates clear lung fields. ECG shows normal sinus rhythm. All studies normal, patient stable for discharge.",
                "expected_reports": 3  # Should detect lab, radiology, and cardiology reports
            }
        }

    @pytest.mark.asyncio
    async def test_laboratory_diagnostic_report_integration(self, conversion_service, sample_clinical_texts):
        """Test complete laboratory DiagnosticReport integration"""

        # Create clinical request
        sample = sample_clinical_texts["laboratory_cbc"]
        request = ClinicalRequestAdvanced(
            clinical_text=sample["text"],
            priority="routine",
            department="internal-medicine"
        )

        # Process through conversion service
        response = await conversion_service.convert_advanced(request, "test-lab-integration")

        # Verify response success
        assert response.status == "completed"
        assert response.fhir_bundle is not None

        # Check bundle contains DiagnosticReport
        bundle_entries = response.fhir_bundle.get("entry", [])
        diagnostic_reports = [
            entry["resource"] for entry in bundle_entries
            if entry.get("resource", {}).get("resourceType") == "DiagnosticReport"
        ]

        assert len(diagnostic_reports) >= 1, f"Expected at least 1 DiagnosticReport, got {len(diagnostic_reports)}"

        # Verify DiagnosticReport properties
        report = diagnostic_reports[0]
        assert report["resourceType"] == "DiagnosticReport"
        assert report["status"] == "final"

        # Check category
        categories = report.get("category", [])
        assert len(categories) > 0
        category_coding = categories[0].get("coding", [])
        assert len(category_coding) > 0
        assert category_coding[0]["code"] == "LAB"

        # Check subject reference
        assert "subject" in report
        assert report["subject"]["reference"].startswith("Patient/")

        # Verify bundle ordering (DiagnosticReport should come after ServiceRequest)
        resource_types = [entry["resource"]["resourceType"] for entry in bundle_entries]
        if "ServiceRequest" in resource_types and "DiagnosticReport" in resource_types:
            service_request_index = resource_types.index("ServiceRequest")
            diagnostic_report_index = resource_types.index("DiagnosticReport")
            assert diagnostic_report_index > service_request_index, "DiagnosticReport should come after ServiceRequest in bundle"

    @pytest.mark.asyncio
    async def test_radiology_diagnostic_report_integration(self, conversion_service, sample_clinical_texts):
        """Test radiology DiagnosticReport integration"""

        sample = sample_clinical_texts["radiology_chest_xray"]
        request = ClinicalRequestAdvanced(
            clinical_text=sample["text"],
            priority="routine",
            department="radiology"
        )

        response = await conversion_service.convert_advanced(request, "test-radiology-integration")

        assert response.status == "completed"
        assert response.fhir_bundle is not None

        # Find DiagnosticReport
        bundle_entries = response.fhir_bundle.get("entry", [])
        diagnostic_reports = [
            entry["resource"] for entry in bundle_entries
            if entry.get("resource", {}).get("resourceType") == "DiagnosticReport"
        ]

        assert len(diagnostic_reports) >= 1

        report = diagnostic_reports[0]
        categories = report.get("category", [])
        category_coding = categories[0].get("coding", [])
        assert category_coding[0]["code"] == "RAD"  # Radiology category

    @pytest.mark.asyncio
    async def test_cardiology_diagnostic_report_integration(self, conversion_service, sample_clinical_texts):
        """Test cardiology DiagnosticReport integration"""

        sample = sample_clinical_texts["cardiology_ecg"]
        request = ClinicalRequestAdvanced(
            clinical_text=sample["text"],
            priority="stat",
            department="cardiology"
        )

        response = await conversion_service.convert_advanced(request, "test-cardiology-integration")

        assert response.status == "completed"

        # Find DiagnosticReport
        bundle_entries = response.fhir_bundle.get("entry", [])
        diagnostic_reports = [
            entry["resource"] for entry in bundle_entries
            if entry.get("resource", {}).get("resourceType") == "DiagnosticReport"
        ]

        assert len(diagnostic_reports) >= 1

        report = diagnostic_reports[0]
        categories = report.get("category", [])
        if categories:  # May be categorized as cardiology or general
            category_coding = categories[0].get("coding", [])
            assert category_coding[0]["code"] in ["CARDIO", "LAB"]  # Allow flexibility

    @pytest.mark.asyncio
    async def test_pathology_diagnostic_report_integration(self, conversion_service, sample_clinical_texts):
        """Test pathology DiagnosticReport integration"""

        sample = sample_clinical_texts["pathology_biopsy"]
        request = ClinicalRequestAdvanced(
            clinical_text=sample["text"],
            priority="routine",
            department="pathology"
        )

        response = await conversion_service.convert_advanced(request, "test-pathology-integration")

        assert response.status == "completed"

        # Find DiagnosticReport
        bundle_entries = response.fhir_bundle.get("entry", [])
        diagnostic_reports = [
            entry["resource"] for entry in bundle_entries
            if entry.get("resource", {}).get("resourceType") == "DiagnosticReport"
        ]

        assert len(diagnostic_reports) >= 1

        report = diagnostic_reports[0]
        categories = report.get("category", [])
        if categories:
            category_coding = categories[0].get("coding", [])
            assert category_coding[0]["code"] == "PAT"  # Pathology category

    @pytest.mark.asyncio
    async def test_multiple_diagnostic_reports_integration(self, conversion_service, sample_clinical_texts):
        """Test processing multiple diagnostic reports from single clinical text"""

        sample = sample_clinical_texts["multiple_reports"]
        request = ClinicalRequestAdvanced(
            clinical_text=sample["text"],
            priority="routine",
            department="internal-medicine"
        )

        response = await conversion_service.convert_advanced(request, "test-multiple-reports-integration")

        assert response.status == "completed"

        # Find all DiagnosticReports
        bundle_entries = response.fhir_bundle.get("entry", [])
        diagnostic_reports = [
            entry["resource"] for entry in bundle_entries
            if entry.get("resource", {}).get("resourceType") == "DiagnosticReport"
        ]

        # Should have multiple reports
        assert len(diagnostic_reports) >= 2, f"Expected at least 2 DiagnosticReports for multiple reports text, got {len(diagnostic_reports)}"

        # Verify different categories are present
        categories_found = set()
        for report in diagnostic_reports:
            categories = report.get("category", [])
            if categories:
                category_coding = categories[0].get("coding", [])
                if category_coding:
                    categories_found.add(category_coding[0]["code"])

        assert len(categories_found) >= 2, f"Expected multiple diagnostic categories, found: {categories_found}"

    @pytest.mark.asyncio
    async def test_diagnostic_report_fhir_compliance(self, conversion_service, sample_clinical_texts):
        """Test FHIR R4 compliance of created DiagnosticReports"""

        sample = sample_clinical_texts["laboratory_cbc"]
        request = ClinicalRequestAdvanced(
            clinical_text=sample["text"],
            priority="routine",
            department="internal-medicine"
        )

        response = await conversion_service.convert_advanced(request, "test-fhir-compliance")

        assert response.status == "completed"

        # Find DiagnosticReport
        bundle_entries = response.fhir_bundle.get("entry", [])
        diagnostic_reports = [
            entry["resource"] for entry in bundle_entries
            if entry.get("resource", {}).get("resourceType") == "DiagnosticReport"
        ]

        assert len(diagnostic_reports) >= 1

        report = diagnostic_reports[0]

        # Verify required FHIR R4 fields
        required_fields = ["resourceType", "id", "status", "category", "code", "subject", "effectiveDateTime"]
        for field in required_fields:
            assert field in report, f"Missing required FHIR field: {field}"

        # Verify field formats
        assert report["resourceType"] == "DiagnosticReport"
        assert report["status"] in ["registered", "partial", "preliminary", "final", "amended", "corrected", "cancelled", "entered-in-error", "unknown"]
        assert isinstance(report["category"], list) and len(report["category"]) > 0
        assert "reference" in report["subject"]
        assert report["subject"]["reference"].startswith("Patient/")

    @pytest.mark.asyncio
    async def test_diagnostic_report_nlp_pipeline_integration(self, conversion_service, sample_clinical_texts):
        """Test DiagnosticReport extraction through NLP pipeline"""

        sample = sample_clinical_texts["laboratory_cbc"]
        request = ClinicalRequestAdvanced(
            clinical_text=sample["text"],
            priority="routine",
            department="internal-medicine"
        )

        response = await conversion_service.convert_advanced(request, "test-nlp-pipeline")

        # Verify NLP results contain diagnostic reports
        assert hasattr(response, 'nlp_results') or hasattr(response, 'processing_metadata')

        # Check that conversion was successful (indicates NLP pipeline worked)
        assert response.status == "completed"

        # Verify DiagnosticReport was created from NLP extraction
        bundle_entries = response.fhir_bundle.get("entry", [])
        diagnostic_reports = [
            entry["resource"] for entry in bundle_entries
            if entry.get("resource", {}).get("resourceType") == "DiagnosticReport"
        ]

        assert len(diagnostic_reports) >= 1, "DiagnosticReport should be created from NLP extraction"

        # Verify the report contains extracted information
        report = diagnostic_reports[0]
        assert "code" in report
        code_text = report["code"].get("text", "").lower()
        assert "cbc" in code_text or "complete blood count" in code_text or "lab" in code_text

    @pytest.mark.asyncio
    async def test_diagnostic_report_error_handling(self, conversion_service):
        """Test error handling when DiagnosticReport extraction fails"""

        # Use clinical text that should not generate diagnostic reports
        request = ClinicalRequestAdvanced(
            clinical_text="Patient needs routine medication refill for hypertension.",
            priority="routine",
            department="internal-medicine"
        )

        response = await conversion_service.convert_advanced(request, "test-no-diagnostic-reports")

        # Should still succeed even with no diagnostic reports
        assert response.status == "completed"

        # May or may not have DiagnosticReports depending on NLP detection
        # Main test is that the system doesn't crash
        bundle_entries = response.fhir_bundle.get("entry", [])
        assert len(bundle_entries) >= 1  # Should have at least Patient resource

    def test_diagnostic_report_bundle_ordering(self):
        """Test that bundle assembly orders DiagnosticReports correctly"""

        from nl_fhir.services.fhir.bundle_assembler import FHIRBundleAssembler

        # Create mock bundle entries with different resource types
        mock_entries = [
            {"resource": {"resourceType": "DiagnosticReport", "id": "dr-1"}},
            {"resource": {"resourceType": "Patient", "id": "patient-1"}},
            {"resource": {"resourceType": "ServiceRequest", "id": "sr-1"}},
            {"resource": {"resourceType": "Practitioner", "id": "prac-1"}},
            {"resource": {"resourceType": "Task", "id": "task-1"}}
        ]

        mock_bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": mock_entries
        }

        assembler = FHIRBundleAssembler()
        assembler.initialize()

        optimized_bundle = assembler.optimize_bundle(mock_bundle, "test-ordering")

        # Check ordering
        resource_types = [
            entry["resource"]["resourceType"]
            for entry in optimized_bundle["entry"]
        ]

        # Patient should be first
        assert resource_types[0] == "Patient"

        # DiagnosticReport should come after ServiceRequest if both present
        if "ServiceRequest" in resource_types and "DiagnosticReport" in resource_types:
            sr_index = resource_types.index("ServiceRequest")
            dr_index = resource_types.index("DiagnosticReport")
            assert dr_index > sr_index, f"DiagnosticReport index {dr_index} should be after ServiceRequest index {sr_index}"


if __name__ == "__main__":
    # Run tests directly
    import subprocess
    import os

    # Change to project directory
    os.chdir(Path(__file__).parent.parent)

    # Run pytest with this specific test file
    result = subprocess.run([
        "uv", "run", "pytest",
        "tests/test_diagnostic_report_integration.py",
        "-v", "--tb=short"
    ], capture_output=True, text=True)

    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    print("Return code:", result.returncode)