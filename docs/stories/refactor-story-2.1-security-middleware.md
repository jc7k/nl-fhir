# Story: Unify Security Middleware Implementation

**Story ID:** REFACTOR-006
**Epic:** Middleware Consolidation (Epic 2)
**Status:** READY FOR DEVELOPMENT
**Estimated Effort:** 6 hours
**Priority:** P1 - High

## User Story

**As a** security engineer
**I want** a single, unified security middleware implementation
**So that** security policies are consistently applied across all endpoints without duplication

## Background & Context

The NL-FHIR codebase currently has **duplicate security middleware implementations** that create maintenance overhead and security risks:

**Current State:**
- **Primary middleware:** `src/nl_fhir/middleware/security.py` (SecurityMiddleware class, 76 lines)
- **API middleware:** `src/nl_fhir/api/middleware/security.py` (add_security_headers function, 49 lines)
- **Inconsistent policies:** Different CSP rules, HSTS handling, and header sets
- **Maintenance burden:** Security updates must be made in two places

**Target State:**
- Single unified security middleware in `/middleware/security.py`
- Consistent security headers across all endpoints
- Production/development environment awareness
- Single source of truth for all security policies

## Analysis of Current Implementations

### `/middleware/security.py` (Primary)
**Strengths:**
- Class-based middleware with comprehensive validation
- Content-type validation for POST/PUT requests
- Conditional CSP for web interface vs API
- Production-ready security headers

**Issues:**
- Hardcoded CSP policy
- No environment-specific configuration
- Missing some modern security headers

### `/api/middleware/security.py` (Duplicate)
**Strengths:**
- Environment-aware HSTS handling
- Clean function-based implementation
- Uses settings configuration

**Issues:**
- Shorter, less comprehensive header set
- No content-type validation
- Simpler CSP policy

## Acceptance Criteria

### Must Have
- [ ] Single unified security middleware implementation
- [ ] Consolidate best features from both existing implementations
- [ ] Environment-aware configuration (production vs development)
- [ ] Comprehensive security headers (HSTS, CSP, XSS protection, etc.)
- [ ] Content-type validation for state-changing requests
- [ ] Conditional CSP policies for web interface vs API endpoints
- [ ] Remove duplicate `/api/middleware/security.py` file
- [ ] Update all middleware registration to use unified implementation
- [ ] 100% backward compatibility with existing security behavior

### Should Have
- [ ] Configuration-driven security policies
- [ ] Security header customization via settings
- [ ] Request size validation
- [ ] Rate limiting integration hooks
- [ ] Comprehensive unit tests covering all security scenarios

### Could Have
- [ ] Security audit logging
- [ ] Dynamic CSP nonce generation
- [ ] Advanced threat detection hooks

## Technical Specifications

### 1. Unified Security Middleware Implementation

```python
# src/nl_fhir/middleware/security.py (Enhanced)

"""
Unified Security Middleware for NL-FHIR
Combines best practices from both existing implementations
Environment-aware and configuration-driven
"""

import logging
from typing import Dict, Set, Optional
from fastapi import Request
from fastapi.responses import JSONResponse

from ..config import settings

logger = logging.getLogger(__name__)


class UnifiedSecurityMiddleware:
    """
    Unified security middleware combining best practices from both implementations.
    Provides comprehensive security headers and validation.
    """

    def __init__(self, app):
        self.app = app
        self._initialize_policies()

    def _initialize_policies(self):
        """Initialize security policies based on configuration"""

        # Base security headers (always applied)
        self.base_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

        # Content Security Policies
        self.csp_api = (
            "default-src 'self'; "
            "script-src 'none'; "
            "style-src 'none'; "
            "img-src 'none'; "
            "font-src 'none'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'none'; "
            "base-uri 'self'"
        )

        self.csp_web = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Valid content types for state-changing requests
        self.valid_content_types = {
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data"
        }

    async def __call__(self, request: Request, call_next):
        """Process request with unified security policies"""

        # Pre-request security validation
        validation_response = self._validate_request(request)
        if validation_response:
            return validation_response

        # Process request
        response = await call_next(request)

        # Apply security headers
        self._apply_security_headers(request, response)

        return response

    def _validate_request(self, request: Request) -> Optional[JSONResponse]:
        """Validate request security requirements"""

        # Content-type validation for state-changing requests
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            if not self._validate_content_type(request):
                logger.warning(
                    f"Invalid content type: {request.headers.get('content-type', 'missing')} "
                    f"from {self._get_client_identifier(request)}"
                )
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid content type",
                        "message": "Content-Type header must be application/json, "
                                 "application/x-www-form-urlencoded, or multipart/form-data"
                    }
                )

        # Request size validation (prevent DoS)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size:
            logger.warning(
                f"Request size {content_length} exceeds limit from "
                f"{self._get_client_identifier(request)}"
            )
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request too large",
                    "message": f"Request size exceeds {settings.max_request_size} bytes"
                }
            )

        return None

    def _validate_content_type(self, request: Request) -> bool:
        """Validate content type for state-changing requests"""
        content_type = request.headers.get("content-type", "").lower()

        # Check if content type starts with any valid type
        return any(content_type.startswith(vt) for vt in self.valid_content_types)

    def _apply_security_headers(self, request: Request, response):
        """Apply comprehensive security headers"""

        # Apply base security headers
        for header, value in self.base_headers.items():
            response.headers[header] = value

        # Apply HSTS based on environment and protocol
        self._apply_hsts_header(request, response)

        # Apply appropriate CSP based on endpoint
        self._apply_csp_header(request, response)

    def _apply_hsts_header(self, request: Request, response):
        """Apply HSTS header based on environment and protocol"""

        if settings.is_production:
            # Check actual protocol (handle reverse proxy headers)
            scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
            if scheme == "https":
                response.headers["Strict-Transport-Security"] = (
                    "max-age=63072000; includeSubDomains; preload"
                )
        else:
            # Development environment - remove HSTS if present
            if "Strict-Transport-Security" in response.headers:
                del response.headers["Strict-Transport-Security"]

    def _apply_csp_header(self, request: Request, response):
        """Apply Content Security Policy based on endpoint type"""

        path = request.url.path

        # Determine if this is a web interface or API endpoint
        if path == "/" or path.startswith("/static") or path.endswith(".html"):
            # Web interface - allow inline scripts/styles for functionality
            response.headers["Content-Security-Policy"] = self.csp_web
        else:
            # API endpoints - strict CSP
            response.headers["Content-Security-Policy"] = self.csp_api

    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for logging (HIPAA-safe)"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Return truncated IP for privacy
        return f"{client_ip[:8]}..."


# Factory function for FastAPI middleware registration
def create_security_middleware():
    """Create security middleware instance for FastAPI registration"""

    async def security_middleware(request: Request, call_next):
        """FastAPI middleware function"""
        middleware = UnifiedSecurityMiddleware(None)
        return await middleware(request, call_next)

    return security_middleware
```

### 2. Configuration Integration

```python
# src/nl_fhir/config.py (additions)

class Settings:
    # ... existing settings ...

    # Security configuration
    max_request_size: int = 1024 * 1024  # 1MB default
    enable_security_audit_logging: bool = False
    custom_security_headers: Dict[str, str] = {}

    # CSP customization
    csp_report_uri: Optional[str] = None
    enable_csp_reporting: bool = False

    @property
    def is_production(self) -> bool:
        """Determine if running in production environment"""
        return self.environment.lower() in ["production", "prod"]
```

### 3. Migration Plan

**Phase 1: Create Unified Implementation**
1. Enhance `src/nl_fhir/middleware/security.py` with unified implementation
2. Add comprehensive test suite
3. Validate against existing security requirements

**Phase 2: Update Registration**
1. Update FastAPI app to use unified middleware
2. Remove registration of duplicate middleware
3. Test all endpoints for consistent security headers

**Phase 3: Remove Duplicate**
1. Delete `src/nl_fhir/api/middleware/security.py`
2. Update any imports or references
3. Clean up related test files

## Test Requirements

### Unit Tests

```python
# tests/middleware/test_unified_security.py

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.nl_fhir.middleware.security import UnifiedSecurityMiddleware


class TestUnifiedSecurityMiddleware:

    @pytest.fixture
    def app_with_middleware(self):
        """Create test app with unified security middleware"""
        app = FastAPI()

        @app.get("/api/test")
        async def api_endpoint():
            return {"message": "API response"}

        @app.get("/")
        async def web_interface():
            return {"message": "Web interface"}

        # Add unified security middleware
        app.add_middleware(UnifiedSecurityMiddleware)

        return app

    @pytest.fixture
    def client(self, app_with_middleware):
        return TestClient(app_with_middleware)

    def test_api_security_headers(self, client):
        """API endpoints should have strict security headers"""
        response = client.get("/api/test")

        assert response.status_code == 200
        headers = response.headers

        # Base security headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-XSS-Protection"] == "1; mode=block"
        assert "no-store" in headers["Cache-Control"]

        # API-specific CSP (strict)
        csp = headers["Content-Security-Policy"]
        assert "script-src 'none'" in csp
        assert "style-src 'none'" in csp

    def test_web_security_headers(self, client):
        """Web interface should allow inline scripts/styles"""
        response = client.get("/")

        assert response.status_code == 200
        headers = response.headers

        # Base security headers present
        assert headers["X-Content-Type-Options"] == "nosniff"

        # Web-specific CSP (allows inline)
        csp = headers["Content-Security-Policy"]
        assert "script-src 'self' 'unsafe-inline'" in csp
        assert "style-src 'self' 'unsafe-inline'" in csp

    def test_content_type_validation(self, client):
        """Invalid content types should be rejected"""
        response = client.post(
            "/api/test",
            data="invalid",
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 400
        assert "Invalid content type" in response.json()["error"]

    def test_valid_content_types(self, client):
        """Valid content types should be accepted"""
        valid_types = [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data"
        ]

        for content_type in valid_types:
            response = client.post(
                "/api/test",
                json={"test": "data"},
                headers={"Content-Type": content_type}
            )
            # May fail due to endpoint logic, but not content-type validation
            assert response.status_code != 400 or "Invalid content type" not in str(response.content)

    @pytest.mark.parametrize("environment,has_hsts", [
        ("production", True),
        ("development", False),
        ("test", False)
    ])
    def test_hsts_environment_handling(self, environment, has_hsts, monkeypatch):
        """HSTS should only be applied in production"""
        from src.nl_fhir.config import settings
        monkeypatch.setattr(settings, "environment", environment)

        app = FastAPI()
        app.add_middleware(UnifiedSecurityMiddleware)
        client = TestClient(app)

        response = client.get("/", headers={"x-forwarded-proto": "https"})

        if has_hsts:
            assert "Strict-Transport-Security" in response.headers
        else:
            assert "Strict-Transport-Security" not in response.headers
```

### Integration Tests

```python
# tests/integration/test_security_middleware_integration.py

def test_security_consistency_across_endpoints():
    """All endpoints should have consistent base security headers"""

    endpoints = ["/", "/api/convert", "/health", "/docs"]

    for endpoint in endpoints:
        response = client.get(endpoint)

        if response.status_code < 400:  # Successful responses
            headers = response.headers

            # All endpoints must have base security headers
            assert headers["X-Content-Type-Options"] == "nosniff"
            assert headers["X-Frame-Options"] == "DENY"
            assert "Content-Security-Policy" in headers

def test_backward_compatibility():
    """Unified middleware should maintain existing security behavior"""

    # Test critical endpoints maintain previous security posture
    critical_endpoints = ["/convert", "/api/convert"]

    for endpoint in critical_endpoints:
        response = client.post(endpoint, json={"test": "data"})

        # Should maintain same security headers as before
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "no-store" in response.headers["Cache-Control"]
```

## Performance Requirements

- Middleware processing overhead: <1ms per request
- Memory usage: <5MB for middleware state
- No degradation in response time
- Header application: <0.1ms per response

## Security Requirements

- All endpoints must receive base security headers
- API endpoints must have strict CSP
- Web interface must allow necessary inline content
- Content-type validation for state-changing requests
- Environment-appropriate HSTS handling
- No security header regression

## Migration & Rollback Plan

### Migration Steps
1. **Phase 1:** Deploy unified middleware alongside existing (feature flag)
2. **Phase 2:** Switch traffic to unified middleware gradually
3. **Phase 3:** Remove duplicate implementation after validation

### Rollback Plan
- Feature flag to switch back to original middleware
- Original files preserved during migration period
- Automated rollback if security tests fail

## Dependencies

**Technical Dependencies:**
- FastAPI middleware system
- Current settings/configuration system
- Existing test framework

**Blocked By:**
- None (can implement immediately)

**Blocks:**
- REFACTOR-007: Story 2.2 (Rate Limiting consolidation)
- Any future middleware enhancements

## File List

**Files to Create:**
- `tests/middleware/test_unified_security.py` - Comprehensive unit tests
- `tests/integration/test_security_middleware_integration.py` - Integration tests

**Files to Modify:**
- `src/nl_fhir/middleware/security.py` - Enhanced unified implementation
- `src/nl_fhir/config.py` - Security configuration additions
- `src/nl_fhir/main.py` - Middleware registration updates

**Files to Delete:**
- `src/nl_fhir/api/middleware/security.py` - Duplicate implementation
- `tests/api/middleware/test_security.py` - Duplicate tests (if exists)

## Definition of Done

- [ ] Unified security middleware implemented with all features from both sources
- [ ] All existing security behavior maintained (backward compatibility)
- [ ] Environment-aware configuration working
- [ ] 100% unit test coverage for new middleware
- [ ] Integration tests validating consistency across endpoints
- [ ] Performance benchmarks met (<1ms overhead)
- [ ] Duplicate middleware removed
- [ ] All endpoint registrations updated
- [ ] Security audit confirms no regression
- [ ] Documentation updated

---
**Story Status:** READY FOR DEVELOPMENT
**Next Story:** REFACTOR-007 - Consolidate Rate Limiting Implementation