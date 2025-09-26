"""
Tests for Unified Security Middleware
REFACTOR-006: Comprehensive security middleware testing
HIPAA Compliant: Healthcare security validation
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse

from src.nl_fhir.security import UnifiedSecurityMiddleware, security_middleware
from src.nl_fhir.security.validators import (
    sanitize_clinical_text,
    validate_content_type,
    validate_request_size,
    validate_patient_reference,
    detect_potential_phi,
)
from src.nl_fhir.security.headers import SecurityHeaders
from src.nl_fhir.security.hipaa_compliance import HIPAASecurityConfig


@pytest.fixture
def test_app():
    """Create test FastAPI app with unified security middleware"""
    app = FastAPI()

    # Add unified security middleware
    app.middleware("http")(security_middleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.post("/convert")
    async def convert_endpoint(request: Request):
        body = await request.body()
        return {"received": len(body)}

    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


class TestUnifiedSecurityMiddleware:
    """Test unified security middleware functionality"""

    def test_security_headers_applied(self, client):
        """Test that security headers are properly applied"""
        response = client.get("/test")

        assert response.status_code == 200

        # Check core security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Cache-Control" in response.headers
        assert "Referrer-Policy" in response.headers
        assert "Permissions-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers

        # Check request ID header
        assert "X-Request-ID" in response.headers

        # Check HIPAA compliance indicator
        assert response.headers.get("X-HIPAA-Compliant") == "true"

    def test_content_type_validation(self, client):
        """Test content type validation for POST requests"""
        # Valid content type
        response = client.post(
            "/convert",
            json={"test": "data"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200

        # Invalid content type
        response = client.post(
            "/convert",
            data="test data",
            headers={"Content-Type": "text/xml"}
        )
        assert response.status_code == 400
        assert "Invalid content type" in response.json()["error"]

    def test_request_size_validation(self, client):
        """Test request size validation"""
        # Large payload should be rejected
        large_data = "x" * (11 * 1024 * 1024)  # 11MB

        response = client.post(
            "/convert",
            content=large_data,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(large_data))
            }
        )
        assert response.status_code == 413
        assert "Request payload too large" in response.json()["error"]

    def test_suspicious_request_detection(self, client):
        """Test detection of suspicious request patterns"""
        # Path traversal attempt
        response = client.get("/test/../../../etc/passwd")
        assert response.status_code == 200  # Doesn't block but logs

        # SQL injection in query params
        response = client.get("/test?id=1'; DROP TABLE users; --")
        assert response.status_code == 200  # Doesn't block but logs

    def test_csp_policy_web_interface(self, client):
        """Test CSP policy for web interface"""
        response = client.get("/")
        csp = response.headers.get("Content-Security-Policy", "")

        # Should allow inline styles for web interface
        assert "'unsafe-inline'" in csp
        assert "default-src 'self'" in csp

    def test_csp_policy_api_only(self, client):
        """Test CSP policy for API endpoints"""
        response = client.get("/test")
        csp = response.headers.get("Content-Security-Policy", "")

        # Should be restrictive for API endpoints
        assert "default-src 'none'" in csp


class TestSecurityValidators:
    """Test security validation functions"""

    def test_sanitize_clinical_text(self):
        """Test clinical text sanitization"""
        # Test HTML removal
        text = "Patient has <script>alert('xss')</script> symptoms"
        sanitized = sanitize_clinical_text(text)
        assert "<script>" not in sanitized
        assert "alert" not in sanitized
        assert "symptoms" in sanitized

        # Test control character removal
        text = "Patient\x00\x01 has symptoms"
        sanitized = sanitize_clinical_text(text)
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized
        assert "Patient has symptoms" == sanitized.strip()

        # Test whitespace normalization
        text = "Patient    has\n\n\n\n symptoms"
        sanitized = sanitize_clinical_text(text)
        assert "    " not in sanitized  # No more than 3 spaces
        assert "\n\n\n\n" not in sanitized  # No more than 3 newlines

        # Test SQL injection removal
        text = "Patient'; DROP TABLE patients; --"
        sanitized = sanitize_clinical_text(text)
        assert "DROP" not in sanitized
        assert "'" not in sanitized
        assert "--" not in sanitized

    def test_validate_content_type(self):
        """Test content type validation"""
        # Valid types
        assert validate_content_type("application/json")
        assert validate_content_type("application/json; charset=utf-8")
        assert validate_content_type("application/x-www-form-urlencoded")
        assert validate_content_type("multipart/form-data; boundary=xxx")

        # Invalid types
        assert not validate_content_type("text/xml")
        assert not validate_content_type("application/xml")
        assert not validate_content_type("")
        assert not validate_content_type(None)

    def test_validate_request_size(self):
        """Test request size validation"""
        # Valid sizes
        assert validate_request_size("1000", 10000)
        assert validate_request_size("5000", 10000)
        assert validate_request_size(None)  # No content-length is OK

        # Invalid sizes
        assert not validate_request_size("15000", 10000)
        assert not validate_request_size("invalid")

    def test_validate_patient_reference(self):
        """Test FHIR patient reference validation"""
        # Valid references
        assert validate_patient_reference("Patient/123")
        assert validate_patient_reference("Patient-456")
        assert validate_patient_reference("Patient_789")
        assert validate_patient_reference("Organization/Hospital-1/Patient/123")

        # Invalid references
        assert not validate_patient_reference("")
        assert not validate_patient_reference("Patient/<script>")
        assert not validate_patient_reference("Patient/123; DROP TABLE")
        assert not validate_patient_reference("Patient 123")  # Space not allowed

    def test_detect_potential_phi(self):
        """Test PHI pattern detection"""
        # Should detect potential PHI
        assert detect_potential_phi("SSN: 123-45-6789")
        assert detect_potential_phi("DOB: 01/15/1980")
        assert detect_potential_phi("MRN: 1234567890")
        assert detect_potential_phi("Insurance: AB123456789")

        # Should not detect regular clinical text
        assert not detect_potential_phi("Patient has fever")
        assert not detect_potential_phi("Administer 10mg medication")
        assert not detect_potential_phi("Temperature 98.6F")


class TestSecurityHeaders:
    """Test security headers configuration"""

    def test_production_headers(self):
        """Test production security headers"""
        headers = SecurityHeaders.get_production_headers(is_https=True)

        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in headers
        assert "private" in headers["Cache-Control"]

    def test_development_headers(self):
        """Test development security headers"""
        headers = SecurityHeaders.get_development_headers()

        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" not in headers
        assert headers["Cache-Control"] == "no-cache"

    def test_csp_policies(self):
        """Test CSP policy generation"""
        web_csp = SecurityHeaders.get_csp_policy(is_web_interface=True)
        api_csp = SecurityHeaders.get_csp_policy(is_web_interface=False)

        assert "'self'" in web_csp
        assert "'unsafe-inline'" in web_csp
        assert "'none'" in api_csp
        assert "'unsafe-inline'" not in api_csp


class TestHIPAACompliance:
    """Test HIPAA compliance configuration"""

    def test_production_config(self):
        """Test production HIPAA configuration"""
        config = HIPAASecurityConfig.production_config()

        assert config.require_tls is True
        assert config.min_tls_version == "1.2"
        assert config.session_timeout_minutes == 15
        assert config.mask_phi_in_logs is True
        assert config.log_security_events is True

    def test_development_config(self):
        """Test development HIPAA configuration"""
        config = HIPAASecurityConfig.development_config()

        assert config.require_tls is False  # Relaxed for development
        assert config.session_timeout_minutes == 60  # Longer timeout
        assert config.mask_phi_in_logs is True  # Always mask PHI
        assert config.log_security_events is True


class TestIntegrationSecurity:
    """Test security middleware integration"""

    def test_middleware_order_and_context(self, client):
        """Test that middleware properly sets request context"""
        response = client.get("/test")

        # Should have request ID
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) == 8  # Short UUID format

    def test_error_handling_security(self, client):
        """Test security error handling doesn't leak information"""
        # Force an error condition
        response = client.post(
            "/nonexistent",
            headers={"Content-Length": "999999999999"}  # Invalid size
        )

        # Should not reveal internal error details
        if response.status_code >= 400:
            assert "request_id" in response.json()
            # Should not contain stack traces or internal paths
            error_text = str(response.json())
            assert "/src/" not in error_text
            assert "Traceback" not in error_text

    def test_security_audit_logging(self, client):
        """Test that security events are properly logged"""
        # This would be tested with log capture in a real scenario
        # For now, verify the middleware doesn't crash on logging
        response = client.post(
            "/convert",
            data="test",
            headers={"Content-Type": "invalid/type"}
        )
        assert response.status_code == 400