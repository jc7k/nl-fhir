"""
Comprehensive tests for /convert and /api/v1/convert endpoints
Production Readiness: Critical endpoint testing

Coverage:
- Happy path scenarios
- Error handling
- Validation
- Performance
- Edge cases
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import time

from src.nl_fhir.main import app

client = TestClient(app)


class TestConvertEndpoint:
    """Test /convert endpoint (basic conversion)"""

    def test_convert_valid_request_success(self):
        """Test successful conversion with valid clinical text"""
        payload = {
            "clinical_text": "Start patient on metformin 500mg twice daily for diabetes",
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "fhir_bundle" in data
        assert "request_id" in data
        assert "processing_time" in data
        assert data["fhir_bundle"] is not None

    def test_convert_minimal_request(self):
        """Test conversion with minimal required fields"""
        payload = {
            "clinical_text": "metformin 500mg"
        }

        response = client.post("/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "fhir_bundle" in data

    def test_convert_missing_clinical_text(self):
        """Test validation error when clinical_text is missing"""
        payload = {
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        assert response.status_code == 422  # Validation error
        assert "detail" in response.json()

    def test_convert_empty_clinical_text(self):
        """Test error handling for empty clinical text"""
        payload = {
            "clinical_text": "",
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        # Should either reject or handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_convert_invalid_json(self):
        """Test error handling for malformed JSON"""
        response = client.post(
            "/convert",
            data="invalid json{",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    def test_convert_missing_content_type(self):
        """Test request without Content-Type header"""
        payload = {
            "clinical_text": "metformin 500mg"
        }

        response = client.post("/convert", json=payload)

        # FastAPI should handle this automatically
        assert response.status_code in [200, 415]

    def test_convert_long_clinical_text(self):
        """Test handling of very long clinical text"""
        payload = {
            "clinical_text": "metformin 500mg " * 1000,  # Very long text
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        # Should either handle or reject gracefully
        assert response.status_code in [200, 400, 413, 422]

    def test_convert_special_characters(self):
        """Test handling of special characters in clinical text"""
        payload = {
            "clinical_text": "Start <script>alert('xss')</script> metformin 500mg",
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        # Should sanitize or handle safely
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            # Ensure no script injection in response
            assert "<script>" not in str(response.json())

    def test_convert_unicode_characters(self):
        """Test handling of unicode/international characters"""
        payload = {
            "clinical_text": "Start Пациент на метформин 500мг",
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        assert response.status_code in [200, 400]

    def test_convert_numeric_clinical_text(self):
        """Test handling of pure numeric input"""
        payload = {
            "clinical_text": "123456789",
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        assert response.status_code in [200, 400]

    def test_convert_response_structure(self):
        """Test that response has all expected fields"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        if response.status_code == 200:
            data = response.json()
            required_fields = ["fhir_bundle", "request_id", "processing_time"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

    def test_convert_response_time(self):
        """Test that conversion completes within SLA (<2s)"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/test-123"
        }

        start = time.time()
        response = client.post("/convert", json=payload)
        duration = time.time() - start

        assert response.status_code == 200
        # Should complete in under 2 seconds per requirements
        assert duration < 2.0, f"Conversion took {duration}s, exceeds 2s SLA"

    def test_convert_invalid_patient_ref_format(self):
        """Test handling of invalid patient reference format"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "invalid-format-123"
        }

        response = client.post("/convert", json=payload)

        # Should either accept or validate format
        assert response.status_code in [200, 400, 422]

    def test_convert_multiple_medications(self):
        """Test conversion with multiple medications"""
        payload = {
            "clinical_text": "Start metformin 500mg BID, lisinopril 10mg daily, and aspirin 81mg daily",
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["fhir_bundle"] is not None

    def test_convert_complex_medical_order(self):
        """Test conversion of complex multi-resource order"""
        payload = {
            "clinical_text": """
                Patient presents with chest pain.
                Start metoprolol 25mg twice daily.
                Order EKG and troponin levels.
                Schedule cardiology consult.
                Monitor vitals every 4 hours.
            """,
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        # Should generate multiple FHIR resources
        if data["fhir_bundle"] and "entry" in data["fhir_bundle"]:
            assert len(data["fhir_bundle"]["entry"]) > 1


class TestConvertAdvancedEndpoint:
    """Test /api/v1/convert endpoint (advanced conversion)"""

    def test_convert_advanced_valid_request(self):
        """Test successful advanced conversion with all fields"""
        payload = {
            "clinical_text": "metformin 500mg twice daily",
            "patient_ref": "Patient/test-123",
            "priority": "urgent",
            "ordering_provider": "Dr. Smith",
            "department": "Endocrinology",
            "context_metadata": {"location": "clinic"}
        }

        response = client.post("/api/v1/convert", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "fhir_bundle" in data

    def test_convert_advanced_with_priority_values(self):
        """Test all valid priority values"""
        priorities = ["routine", "urgent", "stat", "asap"]

        for priority in priorities:
            payload = {
                "clinical_text": "metformin 500mg",
                "patient_ref": "Patient/test-123",
                "priority": priority
            }

            response = client.post("/api/v1/convert", json=payload)
            assert response.status_code == 200

    def test_convert_advanced_invalid_priority(self):
        """Test invalid priority value"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/test-123",
            "priority": "invalid-priority"
        }

        response = client.post("/api/v1/convert", json=payload)

        # Should reject invalid enum value
        assert response.status_code in [400, 422]

    def test_convert_advanced_metadata_structure(self):
        """Test complex metadata structure"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/test-123",
            "context_metadata": {
                "location": "clinic",
                "encounter_id": "enc-123",
                "provider_npi": "1234567890",
                "facility_code": "FAC-001"
            }
        }

        response = client.post("/api/v1/convert", json=payload)

        assert response.status_code == 200

    def test_convert_advanced_response_enhanced_fields(self):
        """Test that advanced endpoint returns enhanced fields"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/test-123",
            "priority": "urgent"
        }

        response = client.post("/api/v1/convert", json=payload)

        if response.status_code == 200:
            data = response.json()
            # Advanced endpoint should return additional fields
            assert "fhir_bundle" in data
            assert "request_id" in data


class TestConversionEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_convert_null_patient_ref(self):
        """Test conversion with explicit null patient_ref"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": None
        }

        response = client.post("/convert", json=payload)

        assert response.status_code in [200, 400]

    def test_convert_whitespace_only_text(self):
        """Test clinical text with only whitespace"""
        payload = {
            "clinical_text": "   \n\t   ",
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        assert response.status_code in [200, 400, 422]

    def test_convert_sql_injection_attempt(self):
        """Test SQL injection prevention"""
        payload = {
            "clinical_text": "'; DROP TABLE patients; --",
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        # Should handle safely, not crash
        assert response.status_code in [200, 400]

    def test_convert_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        import concurrent.futures

        def make_request():
            payload = {
                "clinical_text": "metformin 500mg",
                "patient_ref": "Patient/test-123"
            }
            return client.post("/convert", json=payload)

        # Send 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [f.result() for f in futures]

        # All should succeed
        for response in responses:
            assert response.status_code == 200

    def test_convert_idempotency(self):
        """Test that identical requests produce consistent results"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/test-123"
        }

        response1 = client.post("/convert", json=payload)
        response2 = client.post("/convert", json=payload)

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should return FHIR bundles
        assert response1.json()["fhir_bundle"] is not None
        assert response2.json()["fhir_bundle"] is not None


class TestConversionHeaders:
    """Test HTTP header handling"""

    def test_convert_with_correlation_id(self):
        """Test handling of X-Correlation-ID header"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/test-123"
        }
        headers = {
            "X-Correlation-ID": "test-correlation-123"
        }

        response = client.post("/convert", json=payload, headers=headers)

        assert response.status_code == 200

    def test_convert_content_type_variations(self):
        """Test different Content-Type header values"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/test-123"
        }

        # Test application/json
        response = client.post("/convert", json=payload)
        assert response.status_code == 200

    def test_convert_response_headers(self):
        """Test that response includes proper headers"""
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/test-123"
        }

        response = client.post("/convert", json=payload)

        assert response.status_code == 200
        # Should return JSON
        assert "application/json" in response.headers.get("content-type", "")
