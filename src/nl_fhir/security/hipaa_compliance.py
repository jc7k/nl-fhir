"""
HIPAA Compliance Configuration
Healthcare Security: HIPAA-specific security measures
Audit Trail: Comprehensive logging without PHI exposure
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .validators import detect_potential_phi

logger = logging.getLogger(__name__)


@dataclass
class HIPAASecurityConfig:
    """HIPAA compliance configuration for healthcare applications"""

    # Encryption requirements
    require_tls: bool = True
    min_tls_version: str = "1.2"

    # Access control
    require_authentication: bool = True
    session_timeout_minutes: int = 15
    max_failed_attempts: int = 3

    # Audit logging
    log_access_attempts: bool = True
    log_data_access: bool = True
    log_security_events: bool = True

    # Data protection
    mask_phi_in_logs: bool = True
    encrypt_at_rest: bool = True
    secure_deletion: bool = True

    @classmethod
    def production_config(cls) -> HIPAASecurityConfig:
        """Get production HIPAA configuration"""
        return cls(
            require_tls=True,
            min_tls_version="1.2",
            require_authentication=True,
            session_timeout_minutes=15,
            max_failed_attempts=3,
            log_access_attempts=True,
            log_data_access=True,
            log_security_events=True,
            mask_phi_in_logs=True,
            encrypt_at_rest=True,
            secure_deletion=True,
        )

    @classmethod
    def development_config(cls) -> HIPAASecurityConfig:
        """Get development HIPAA configuration"""
        return cls(
            require_tls=False,  # Allow HTTP in development
            min_tls_version="1.2",
            require_authentication=False,  # Relaxed for development
            session_timeout_minutes=60,  # Longer timeout for development
            max_failed_attempts=10,  # More lenient in development
            log_access_attempts=True,
            log_data_access=True,
            log_security_events=True,
            mask_phi_in_logs=True,  # Always mask PHI
            encrypt_at_rest=False,  # May be disabled in development
            secure_deletion=False,  # May be disabled in development
        )


class HIPAASecurityLogger:
    """HIPAA-compliant security event logging"""

    def __init__(self, config: HIPAASecurityConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.security_audit")

    def log_access_attempt(
        self,
        request_id: str,
        endpoint: str,
        client_ip: str,
        user_agent: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
    ) -> None:
        """Log access attempts for HIPAA audit trail"""
        if not self.config.log_access_attempts:
            return

        event_data = {
            "event_type": "access_attempt",
            "request_id": request_id,
            "endpoint": self._sanitize_endpoint(endpoint),
            "client_ip": self._sanitize_ip(client_ip),
            "success": success,
            "timestamp": None,  # Will be added by logging formatter
        }

        if user_agent:
            event_data["user_agent"] = self._sanitize_user_agent(user_agent)

        if failure_reason:
            event_data["failure_reason"] = failure_reason

        if success:
            self.logger.info("Access granted", extra=event_data)
        else:
            self.logger.warning("Access denied", extra=event_data)

    def log_data_access(
        self,
        request_id: str,
        resource_type: str,
        operation: str,
        success: bool = True,
        error_details: Optional[str] = None,
    ) -> None:
        """Log data access events for HIPAA audit trail"""
        if not self.config.log_data_access:
            return

        event_data = {
            "event_type": "data_access",
            "request_id": request_id,
            "resource_type": resource_type,
            "operation": operation,
            "success": success,
        }

        if not success and error_details:
            # Ensure error details don't contain PHI
            sanitized_error = self._sanitize_error_message(error_details)
            event_data["error"] = sanitized_error

        if success:
            self.logger.info("Data access", extra=event_data)
        else:
            self.logger.error("Data access failed", extra=event_data)

    def log_security_event(
        self,
        event_type: str,
        request_id: str,
        details: Dict[str, Any],
        severity: str = "info",
    ) -> None:
        """Log security events for HIPAA audit trail"""
        if not self.config.log_security_events:
            return

        event_data = {
            "event_type": f"security_{event_type}",
            "request_id": request_id,
            "details": self._sanitize_event_details(details),
        }

        log_method = getattr(self.logger, severity.lower(), self.logger.info)
        log_method(f"Security event: {event_type}", extra=event_data)

    def _sanitize_endpoint(self, endpoint: str) -> str:
        """Sanitize endpoint paths to remove potential PHI"""
        if not endpoint:
            return endpoint

        # Remove patient IDs and other sensitive path parameters
        import re
        # Replace patterns that might be patient IDs
        sanitized = re.sub(r'/Patient/[^/]+', '/Patient/[ID]', endpoint)
        sanitized = re.sub(r'/\d{6,}', '/[ID]', sanitized)
        return sanitized

    def _sanitize_ip(self, ip: str) -> str:
        """Sanitize IP address for logging"""
        if not ip:
            return "unknown"

        # In production, you might want to hash or partially mask IPs
        # For now, we'll log them as-is but this can be configured
        return ip

    def _sanitize_user_agent(self, user_agent: str) -> str:
        """Sanitize user agent string"""
        if not user_agent:
            return "unknown"

        # Remove potential identifying information
        # Keep browser type but remove specific versions/details
        import re
        sanitized = re.sub(r'\d+\.\d+\.\d+', 'X.X.X', user_agent)
        return sanitized[:200]  # Limit length

    def _sanitize_error_message(self, error_message: str) -> str:
        """Sanitize error messages to remove potential PHI"""
        if not error_message:
            return error_message

        if self.config.mask_phi_in_logs and detect_potential_phi(error_message):
            return "[ERROR MESSAGE CONTAINS POTENTIAL PHI - MASKED]"

        return error_message[:500]  # Limit length

    def _sanitize_event_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize event details to remove potential PHI"""
        sanitized = {}

        for key, value in details.items():
            if isinstance(value, str):
                if self.config.mask_phi_in_logs and detect_potential_phi(value):
                    sanitized[key] = "[MASKED - POTENTIAL PHI]"
                else:
                    sanitized[key] = value[:200]  # Limit string length
            elif isinstance(value, (int, float, bool)):
                sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_event_details(value)
            else:
                sanitized[key] = str(value)[:100]  # Convert to string and limit

        return sanitized