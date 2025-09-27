"""
Security Headers Configuration
HIPAA Compliant: Healthcare-grade security headers
Production Ready: Environment-specific security policies
"""

from __future__ import annotations

from typing import Dict, Final


class SecurityHeaders:
    """Centralized security headers configuration"""

    # Core security headers (always applied)
    CORE_HEADERS: Final[Dict[str, str]] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Cache-Control": "no-store, no-cache, must-revalidate, private",
        "Pragma": "no-cache",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    # HIPAA-specific headers for healthcare data protection
    HIPAA_HEADERS: Final[Dict[str, str]] = {
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store, no-cache, must-revalidate, private, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "X-Robots-Tag": "noindex, nofollow, noarchive, nosnippet",
    }

    # Content Security Policy configurations
    CSP_WEB_INTERFACE: Final[str] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'; "
        "base-uri 'self'"
    )

    CSP_API_ONLY: Final[str] = (
        "default-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'none'"
    )

    @classmethod
    def get_production_headers(cls, is_https: bool = False) -> Dict[str, str]:
        """Get production-ready security headers"""
        headers = cls.CORE_HEADERS.copy()
        headers.update(cls.HIPAA_HEADERS)

        if is_https:
            headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        return headers

    @classmethod
    def get_development_headers(cls) -> Dict[str, str]:
        """Get development-friendly security headers"""
        headers = cls.CORE_HEADERS.copy()
        # Remove strict caching in development
        headers["Cache-Control"] = "no-cache"
        return headers

    @classmethod
    def get_csp_policy(cls, is_web_interface: bool = False) -> str:
        """Get appropriate Content Security Policy"""
        return cls.CSP_WEB_INTERFACE if is_web_interface else cls.CSP_API_ONLY