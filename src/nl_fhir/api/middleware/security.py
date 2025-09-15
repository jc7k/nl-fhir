"""
NL-FHIR Security Headers Middleware
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

from fastapi import Request


async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response
