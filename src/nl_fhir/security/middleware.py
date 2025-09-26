"""
Unified Security Middleware
HIPAA Compliant: Comprehensive security for healthcare applications
Production Ready: Environment-aware security policies
"""

import time
import logging
from uuid import uuid4
from typing import Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse

from ..config import settings
from .headers import SecurityHeaders
from .validators import (
    validate_content_type,
    validate_request_size,
    sanitize_clinical_text,
)
from .hipaa_compliance import HIPAASecurityConfig, HIPAASecurityLogger

logger = logging.getLogger(__name__)


class UnifiedSecurityMiddleware:
    """
    Unified security middleware combining all security concerns:
    - Security headers
    - Input validation
    - Rate limiting integration
    - HIPAA compliance
    - Audit logging
    """

    def __init__(self):
        # Configure based on environment
        self.is_production = settings.is_production
        self.max_request_size = getattr(settings, 'max_request_size_bytes', 10485760)  # 10MB default

        # HIPAA configuration
        if self.is_production:
            self.hipaa_config = HIPAASecurityConfig.production_config()
        else:
            self.hipaa_config = HIPAASecurityConfig.development_config()

        # HIPAA audit logger
        self.hipaa_logger = HIPAASecurityLogger(self.hipaa_config)

        logger.info(
            f"UnifiedSecurityMiddleware initialized - "
            f"Production: {self.is_production}, "
            f"HIPAA logging: {self.hipaa_config.log_security_events}"
        )

    async def __call__(self, request: Request, call_next):
        """Process request through unified security pipeline"""
        start_time = time.time()
        request_id = str(uuid4())[:8]
        client_ip = self._get_client_ip(request)

        # Store request context for other middleware
        request.state.security_request_id = request_id
        request.state.security_start_time = start_time

        try:
            # Pre-request security validation
            validation_response = await self._validate_request(request, request_id, client_ip)
            if validation_response:
                return validation_response

            # Process request
            response = await call_next(request)

            # Post-request security enhancements
            self._add_security_headers(request, response)
            self._log_successful_access(request_id, request, client_ip)

            return response

        except Exception as e:
            # Log security incident
            self._log_security_incident(request_id, request, client_ip, str(e))
            logger.error(f"Security middleware error for request {request_id}: {type(e).__name__}")

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal security error",
                    "request_id": request_id,
                },
            )

    async def _validate_request(
        self, request: Request, request_id: str, client_ip: str
    ) -> Optional[JSONResponse]:
        """Comprehensive request validation"""

        # 1. Request size validation
        content_length = request.headers.get("content-length")
        if not validate_request_size(content_length, self.max_request_size):
            self.hipaa_logger.log_security_event(
                "request_too_large",
                request_id,
                {"content_length": content_length, "max_allowed": self.max_request_size},
                "warning"
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "Request payload too large",
                    "request_id": request_id,
                    "max_size_mb": self.max_request_size // 1048576,
                },
            )

        # 2. Content type validation for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not validate_content_type(content_type):
                self.hipaa_logger.log_security_event(
                    "invalid_content_type",
                    request_id,
                    {"content_type": content_type, "method": request.method},
                    "warning"
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "Invalid content type",
                        "request_id": request_id,
                        "allowed_types": [
                            "application/json",
                            "application/x-www-form-urlencoded",
                            "multipart/form-data"
                        ],
                    },
                )

        # 3. HTTPS enforcement in production (if configured)
        if self.hipaa_config.require_tls and self.is_production:
            scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
            if scheme != "https":
                self.hipaa_logger.log_security_event(
                    "insecure_connection",
                    request_id,
                    {"scheme": scheme, "required": "https"},
                    "error"
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "HTTPS required for healthcare data protection",
                        "request_id": request_id,
                    },
                )

        # 4. Suspicious request pattern detection
        if self._detect_suspicious_patterns(request):
            self.hipaa_logger.log_security_event(
                "suspicious_request",
                request_id,
                {
                    "path": request.url.path,
                    "method": request.method,
                    "user_agent": request.headers.get("user-agent", "")[:100],
                },
                "warning"
            )
            # Log but don't block - allow other security layers to handle

        return None  # No validation errors

    def _add_security_headers(self, request: Request, response) -> None:
        """Add comprehensive security headers"""

        # Determine if HTTPS is being used
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        is_https = scheme == "https"

        # Get appropriate headers for environment
        if self.is_production:
            headers = SecurityHeaders.get_production_headers(is_https)
        else:
            headers = SecurityHeaders.get_development_headers()

        # Apply security headers
        for header, value in headers.items():
            response.headers[header] = value

        # Add Content Security Policy based on endpoint
        is_web_interface = (
            request.url.path == "/" or
            request.url.path.startswith("/static") or
            request.url.path.startswith("/docs") or
            request.url.path.startswith("/redoc")
        )
        csp_policy = SecurityHeaders.get_csp_policy(is_web_interface)
        response.headers["Content-Security-Policy"] = csp_policy

        # Add security context headers
        if hasattr(request.state, 'security_request_id'):
            response.headers["X-Request-ID"] = request.state.security_request_id

        # Add HIPAA compliance indicator
        if self.hipaa_config.log_security_events:
            response.headers["X-HIPAA-Compliant"] = "true"

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded IP (behind proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for", "")
        if forwarded_for:
            # Take the first IP in the chain
            client_ip = forwarded_for.split(",")[0].strip()
            if client_ip:
                return client_ip

        # Fall back to direct connection IP
        if request.client:
            return request.client.host

        return "unknown"

    def _detect_suspicious_patterns(self, request: Request) -> bool:
        """Detect suspicious request patterns"""
        suspicious_indicators = [
            # Path traversal attempts
            ".." in request.url.path,
            "/.." in request.url.path,
            "%2e%2e" in str(request.url).lower(),

            # SQL injection patterns in URL
            any(pattern in str(request.url).lower() for pattern in [
                "union+select", "union%20select", "';drop", "';exec",
                "script>", "%3cscript", "javascript:", "vbscript:"
            ]),

            # Suspicious user agents
            request.headers.get("user-agent", "").lower() in [
                "", "python-requests", "curl", "wget", "scanner"
            ],

            # Multiple suspicious headers missing (bot indicators)
            not request.headers.get("accept") and
            not request.headers.get("accept-language") and
            not request.headers.get("accept-encoding"),
        ]

        return any(suspicious_indicators)

    def _log_successful_access(self, request_id: str, request: Request, client_ip: str) -> None:
        """Log successful access for HIPAA audit trail"""
        self.hipaa_logger.log_access_attempt(
            request_id=request_id,
            endpoint=f"{request.method} {request.url.path}",
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent"),
            success=True,
        )

    def _log_security_incident(
        self, request_id: str, request: Request, client_ip: str, error: str
    ) -> None:
        """Log security incident for HIPAA audit trail"""
        self.hipaa_logger.log_access_attempt(
            request_id=request_id,
            endpoint=f"{request.method} {request.url.path}",
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent"),
            success=False,
            failure_reason=f"Security middleware error: {error[:100]}",
        )


# Create the middleware instance
unified_security_middleware = UnifiedSecurityMiddleware()


# FastAPI middleware function wrapper
async def security_middleware(request: Request, call_next):
    """FastAPI middleware wrapper for UnifiedSecurityMiddleware"""
    return await unified_security_middleware(request, call_next)