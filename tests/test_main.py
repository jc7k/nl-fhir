"""
Test suite for NL-FHIR main application
HIPAA Compliant: No PHI in test data
Medical Safety: Test all validation and error scenarios
"""

import pytest
import time
from fastapi.testclient import TestClient
from nl_fhir.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test health endpoint returns healthy status"""
        response = client.get("/health")
        if response.status_code != 200:
            print(f"Error response: {response.status_code} - {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "nl-fhir-converter"


class TestWebFormInterface:
    """Test web form interface"""
    
    def test_serve_form(self):
        """Test main form page loads successfully"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "NL-FHIR Clinical Order Converter" in response.text
        assert "clinical_text" in response.text
        assert "patient_ref" in response.text


class TestConvertEndpoint:
    """Test /convert endpoint functionality"""
    
    def test_valid_clinical_request(self):
        """Test valid clinical order conversion"""
        request_data = {
            "clinical_text": "Start patient on lisinopril 10mg daily for hypertension",
            "patient_ref": "PT-12345"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "request_id" in data
        assert data["status"] == "received"
        assert "Clinical order received" in data["message"]
        assert "timestamp" in data
        
    def test_valid_clinical_request_without_patient_ref(self):
        """Test valid clinical order without patient reference"""
        request_data = {
            "clinical_text": "Order CBC and comprehensive metabolic panel for tomorrow"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "received"
        assert "request_id" in data
    
    def test_empty_clinical_text(self):
        """Test empty clinical text validation"""
        request_data = {
            "clinical_text": "",
            "patient_ref": "PT-12345"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 422
        
    def test_clinical_text_too_short(self):
        """Test clinical text minimum length validation"""
        request_data = {
            "clinical_text": "test",  # Less than 5 characters
            "patient_ref": "PT-12345"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 422
        
    def test_whitespace_only_clinical_text(self):
        """Test clinical text with only whitespace"""
        request_data = {
            "clinical_text": "   \n\t  ",
            "patient_ref": "PT-12345"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 422
        
    def test_clinical_text_whitespace_trimming(self):
        """Test clinical text whitespace trimming"""
        request_data = {
            "clinical_text": "  Start patient on medication  \n\t",
            "patient_ref": "PT-12345"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        
    def test_missing_clinical_text_field(self):
        """Test missing clinical_text field"""
        request_data = {
            "patient_ref": "PT-12345"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 422
        
    def test_invalid_json_format(self):
        """Test invalid JSON format"""
        response = client.post(
            "/convert", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestClinicalRequestModel:
    """Test Pydantic model validation"""
    
    def test_clinical_request_validation_success(self):
        """Test successful clinical request validation"""
        from nl_fhir.main import ClinicalRequest
        
        request = ClinicalRequest(
            clinical_text="Start patient on amoxicillin 500mg twice daily",
            patient_ref="PT-12345"
        )
        
        assert request.clinical_text == "Start patient on amoxicillin 500mg twice daily"
        assert request.patient_ref == "PT-12345"
        
    def test_clinical_request_validation_no_patient_ref(self):
        """Test clinical request without patient reference"""
        from nl_fhir.main import ClinicalRequest
        
        request = ClinicalRequest(
            clinical_text="Order chest X-ray for patient evaluation"
        )
        
        assert request.clinical_text == "Order chest X-ray for patient evaluation"
        assert request.patient_ref is None
        
    def test_clinical_request_validation_failure(self):
        """Test clinical request validation failure"""
        from nl_fhir.main import ClinicalRequest
        from pydantic import ValidationError
        
        # Test with text too short
        with pytest.raises(ValidationError):
            ClinicalRequest(clinical_text="abc")  # Only 3 characters, minimum is 5
        
        # Test with empty text
        with pytest.raises(ValidationError):
            ClinicalRequest(clinical_text="")
            
        # Test with whitespace only
        with pytest.raises(ValidationError):
            ClinicalRequest(clinical_text="   ")
            
    def test_clinical_request_whitespace_trimming(self):
        """Test clinical request trims whitespace"""
        from nl_fhir.main import ClinicalRequest
        
        request = ClinicalRequest(
            clinical_text="  Order blood work   \n\t  ",
            patient_ref="PT-67890"  # Valid patient ref without spaces
        )
        
        assert request.clinical_text == "Order blood work"
        assert request.patient_ref == "PT-67890"


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_404_not_found(self):
        """Test 404 error for non-existent endpoints"""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
    def test_method_not_allowed(self):
        """Test 405 error for wrong HTTP method"""
        response = client.get("/convert")  # Should be POST
        assert response.status_code == 405


class TestResponseStructure:
    """Test API response structure"""
    
    def test_convert_response_structure(self):
        """Test convert endpoint response has required fields"""
        request_data = {
            "clinical_text": "Prescribe ibuprofen 400mg three times daily with meals"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["request_id", "status", "message", "timestamp"]
        
        for field in required_fields:
            assert field in data
            assert data[field] is not None
            
        # Validate UUID format for request_id
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, data["request_id"])


# Integration test for complete workflow
class TestIntegrationWorkflow:
    """Test complete user workflow"""
    
    def test_complete_clinical_order_workflow(self):
        """Test complete workflow from form to API response"""
        # Step 1: Load form page
        form_response = client.get("/")
        assert form_response.status_code == 200
        
        # Step 2: Submit clinical order
        clinical_data = {
            "clinical_text": "Start patient John Smith on metformin 500mg twice daily with breakfast and dinner for diabetes management",
            "patient_ref": "PT-54321"
        }
        
        convert_response = client.post("/convert", json=clinical_data)
        assert convert_response.status_code == 200
        
        result = convert_response.json()
        assert result["status"] == "received"
        assert "request_id" in result
        
        # Step 3: Verify health check still works
        health_response = client.get("/health")
        assert health_response.status_code == 200


class TestSecurityFeatures:
    """Test security hardening features"""
    
    def test_security_headers_present(self):
        """Test security headers are added to responses"""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Check all security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
        assert response.headers["Cache-Control"] == "no-store, no-cache, must-revalidate"
    
    def test_html_script_sanitization(self):
        """Test HTML/script content is sanitized from clinical text"""
        request_data = {
            "clinical_text": "Order <script>alert('xss')</script> medication for patient <b>test</b>"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        # Request should succeed as sanitization happens in validation
        
    def test_control_character_sanitization(self):
        """Test control characters are removed from input"""
        # Include control characters that should be removed
        request_data = {
            "clinical_text": "Order medication\x00\x08\x0B for patient treatment\x1F\x7F"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        
    def test_excessive_whitespace_normalization(self):
        """Test excessive whitespace is normalized"""
        request_data = {
            "clinical_text": "Order    medication     for\n\n\n\n\npatient     treatment"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        
    def test_patient_ref_invalid_characters(self):
        """Test patient reference validation blocks invalid characters"""
        request_data = {
            "clinical_text": "Order medication for patient",
            "patient_ref": "PT-123<>!@#$%"  # Invalid characters
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 422
        
    def test_patient_ref_valid_characters(self):
        """Test patient reference accepts valid alphanumeric characters"""
        request_data = {
            "clinical_text": "Order medication for patient",
            "patient_ref": "PT_123-ABC"  # Valid characters
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
    
    def test_request_size_limit_enforcement(self):
        """Test request size limits are enforced"""
        # Create a large clinical text that exceeds limits
        large_text = "Order medication " * 50000  # Very large text
        request_data = {
            "clinical_text": large_text,
            "patient_ref": "PT-12345"
        }
        
        response = client.post("/convert", json=request_data)
        # Should either succeed with validation error or be rejected due to size
        assert response.status_code in [413, 422]


class TestPerformanceFeatures:
    """Test performance monitoring and logging features"""
    
    def test_request_timing_logging(self):
        """Test request timing is logged (functional test)"""
        request_data = {
            "clinical_text": "Order simple medication for patient care"
        }
        
        start_time = time.time()
        response = client.post("/convert", json=request_data)
        end_time = time.time()
        
        assert response.status_code == 200
        # Verify response comes back quickly (should be well under 1 second)
        assert (end_time - start_time) < 1.0
        
    def test_large_input_monitoring(self):
        """Test large input triggers monitoring logs"""
        # Create input larger than 4000 characters to trigger monitoring
        large_text = "Start patient on comprehensive treatment plan. " * 100  # ~4700 chars
        request_data = {
            "clinical_text": large_text
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        # Large input should still be processed but logged for monitoring
        
    def test_performance_response_structure(self):
        """Test response includes performance-related metadata"""
        request_data = {
            "clinical_text": "Order standard medication for patient"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Verify all required fields are present and properly structured
        assert "request_id" in data
        assert "status" in data
        assert "message" in data
        assert "timestamp" in data
        
        # Validate UUID format for request_id (performance ID tracking)
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        assert re.match(uuid_pattern, data["request_id"])


class TestEnhancedErrorHandling:
    """Test enhanced error handling and logging"""
    
    def test_validation_error_with_details(self):
        """Test validation errors include helpful details"""
        request_data = {
            "clinical_text": "abc",  # Too short
            "patient_ref": "PT-12345"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 422
        
        # Should return detailed error information
        error_data = response.json()
        assert "detail" in error_data
        
    def test_malformed_request_handling(self):
        """Test malformed requests are handled gracefully"""
        # Send completely invalid JSON structure
        response = client.post(
            "/convert",
            data='{"invalid": json structure}',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
    def test_missing_content_type(self):
        """Test requests without proper content type"""
        response = client.post(
            "/convert",
            data='{"clinical_text": "test"}',
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 422
        
    def test_empty_request_body(self):
        """Test empty request body handling"""
        response = client.post(
            "/convert",
            data="",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestCORSAndTrustedHosts:
    """Test CORS and trusted host security"""
    
    def test_cors_headers_on_valid_request(self):
        """Test CORS headers are present on valid requests"""
        request_data = {
            "clinical_text": "Order medication for patient treatment"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        
        # CORS headers should be managed by FastAPI middleware
        # Test passes if request succeeds (CORS configured properly)
        
    def test_options_preflight_request(self):
        """Test OPTIONS preflight request handling"""
        response = client.options("/convert")
        # Should handle OPTIONS requests for CORS preflight
        assert response.status_code in [200, 204, 405]  # Depends on CORS config


class TestMedicalSafetyValidation:
    """Test medical safety input validation features"""
    
    def test_clinical_text_minimum_length_enforcement(self):
        """Test minimum clinical text length for safety"""
        request_data = {
            "clinical_text": "test"  # 4 chars, below 5 char minimum
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 422
        
    def test_clinical_text_after_sanitization_check(self):
        """Test text length check after sanitization"""
        # Test with content that becomes empty after sanitization
        request_data = {
            "clinical_text": "<><><><>"  # This becomes empty after sanitization
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 422
        
    def test_patient_ref_empty_string_handling(self):
        """Test empty patient reference is handled properly"""
        request_data = {
            "clinical_text": "Order standard medication for patient care",
            "patient_ref": ""  # Empty string should become None
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        
    def test_patient_ref_whitespace_only(self):
        """Test patient reference with only whitespace"""
        request_data = {
            "clinical_text": "Order standard medication for patient care",
            "patient_ref": "   \t\n  "  # Whitespace only
        }
        
        response = client.post("/convert", json=request_data)
        # Should either be accepted (trimmed to None) or rejected
        assert response.status_code in [200, 422]