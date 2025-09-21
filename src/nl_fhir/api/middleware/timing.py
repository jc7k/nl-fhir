"""
NL-FHIR Request Timing and Validation Middleware
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

import time
import logging
from uuid import uuid4

from fastapi import Request, status
from fastapi.responses import JSONResponse

from ...config import settings

logger = logging.getLogger(__name__)

# Security and performance metrics (configurable via settings)
REQUEST_TIMEOUT_SECONDS = settings.request_timeout_seconds
MAX_REQUEST_SIZE_BYTES = settings.max_request_size_bytes


async def request_timing_and_validation(request: Request, call_next):
    """Request timing, size validation, and security monitoring"""
    start_time = time.time()
    request_id = str(uuid4())[:8]  # Short request ID for logging (no PHI)

    try:
        # Check request size for security
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE_BYTES:
            logger.warning(
                f"Request {request_id}: Payload too large ({content_length} bytes)"
            )
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "Request payload too large",
                    "request_id": request_id,
                },
            )

        # Process request with timeout monitoring
        response = await call_next(request)

        # Log performance metrics (no PHI)
        processing_time = time.time() - start_time
        logger.info(
            f"Request {request_id}: {request.method} {request.url.path} - "
            f"{response.status_code} - {processing_time:.3f}s"
        )

        # Alert on slow requests
        if processing_time > REQUEST_TIMEOUT_SECONDS:
            logger.warning(
                f"Request {request_id}: Slow response ({processing_time:.3f}s)"
            )

        return response

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            f"Request {request_id}: Error after {processing_time:.3f}s - {type(e).__name__}"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "request_id": request_id},
        )
