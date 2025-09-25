"""NL-FHIR security header middleware."""

from __future__ import annotations

from typing import Final

from fastapi import Request

from ...config import settings

_CSP_POLICY: Final[str] = (
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


async def add_security_headers(request: Request, call_next):
    """Add hardened security headers to all responses."""

    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = _CSP_POLICY

    if settings.is_production:
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        if scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
    else:
        # Remove HSTS header in development (use del if present)
        if "Strict-Transport-Security" in response.headers:
            del response.headers["Strict-Transport-Security"]

    return response
