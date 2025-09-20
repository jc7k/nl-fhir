"""
NL-FHIR Request Timing and Validation Middleware
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
Performance SLA: 2-second response time monitoring
"""

import time
import logging
from uuid import uuid4
from typing import Dict, Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Security and performance metrics
REQUEST_TIMEOUT_SECONDS = 30.0
MAX_REQUEST_SIZE_BYTES = 1024 * 1024  # 1MB

# Performance SLA Configuration - Story 1
SLA_RESPONSE_TIME_SECONDS = 2.0
SLA_ALERT_THRESHOLD = 2.0  # Alert when response time exceeds 2 seconds

# Global performance metrics storage
_performance_metrics: Dict[str, Any] = {
    "total_requests": 0,
    "sla_violations": 0,
    "endpoint_metrics": {},
    "recent_violations": []
}


async def request_timing_and_validation(request: Request, call_next):
    """Request timing, size validation, and SLA monitoring"""
    start_time = time.time()
    request_id = str(uuid4())[:8]  # Short request ID for logging (no PHI)
    endpoint = f"{request.method} {request.url.path}"

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

        # Calculate response time
        processing_time = time.time() - start_time
        processing_time_ms = processing_time * 1000

        # Record metrics for SLA monitoring
        _record_endpoint_metrics(endpoint, processing_time, response.status_code >= 400)

        # Log performance metrics (no PHI)
        logger.info(
            f"Request {request_id}: {endpoint} - "
            f"{response.status_code} - {processing_time:.3f}s"
        )

        # SLA violation alerting - Story 1 requirement
        if processing_time > SLA_ALERT_THRESHOLD:
            _record_sla_violation(request_id, endpoint, processing_time)
            logger.warning(
                f"SLA VIOLATION: Request {request_id}: {endpoint} - "
                f"Response time {processing_time:.3f}s exceeds {SLA_ALERT_THRESHOLD}s threshold"
            )

        # Legacy timeout alerting
        if processing_time > REQUEST_TIMEOUT_SECONDS:
            logger.warning(
                f"Request {request_id}: Slow response ({processing_time:.3f}s)"
            )

        # Add performance headers for monitoring
        response.headers["X-Response-Time"] = f"{processing_time_ms:.2f}ms"
        response.headers["X-Request-ID"] = request_id
        if processing_time > SLA_ALERT_THRESHOLD:
            response.headers["X-SLA-Violation"] = "true"

        return response

    except Exception as e:
        processing_time = time.time() - start_time

        # Record error metrics
        _record_endpoint_metrics(endpoint, processing_time, True)

        logger.error(
            f"Request {request_id}: Error after {processing_time:.3f}s - {type(e).__name__}"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "request_id": request_id},
        )


def _record_endpoint_metrics(endpoint: str, response_time: float, is_error: bool):
    """Record metrics for individual endpoints"""
    _performance_metrics["total_requests"] += 1

    if endpoint not in _performance_metrics["endpoint_metrics"]:
        _performance_metrics["endpoint_metrics"][endpoint] = {
            "request_count": 0,
            "error_count": 0,
            "response_times": [],
            "sla_violations": 0,
            "avg_response_time": 0.0,
            "p95_response_time": 0.0,
            "last_violation": None
        }

    endpoint_metrics = _performance_metrics["endpoint_metrics"][endpoint]
    endpoint_metrics["request_count"] += 1

    if is_error:
        endpoint_metrics["error_count"] += 1

    # Store response times (keep last 100 for calculations)
    endpoint_metrics["response_times"].append(response_time)
    if len(endpoint_metrics["response_times"]) > 100:
        endpoint_metrics["response_times"].pop(0)

    # Update calculated metrics
    response_times = endpoint_metrics["response_times"]
    endpoint_metrics["avg_response_time"] = sum(response_times) / len(response_times)
    sorted_times = sorted(response_times)
    if len(sorted_times) > 0:
        p95_index = int(len(sorted_times) * 0.95)
        endpoint_metrics["p95_response_time"] = sorted_times[min(p95_index, len(sorted_times) - 1)]


def _record_sla_violation(request_id: str, endpoint: str, response_time: float):
    """Record SLA violation for alerting and metrics"""
    _performance_metrics["sla_violations"] += 1

    if endpoint in _performance_metrics["endpoint_metrics"]:
        _performance_metrics["endpoint_metrics"][endpoint]["sla_violations"] += 1
        _performance_metrics["endpoint_metrics"][endpoint]["last_violation"] = time.time()

    # Keep recent violations for dashboard (last 50)
    violation_record = {
        "timestamp": time.time(),
        "request_id": request_id,
        "endpoint": endpoint,
        "response_time": response_time
    }

    _performance_metrics["recent_violations"].append(violation_record)
    if len(_performance_metrics["recent_violations"]) > 50:
        _performance_metrics["recent_violations"].pop(0)


def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics for /metrics endpoint"""
    current_time = time.time()

    # Calculate overall SLA compliance
    total_requests = _performance_metrics["total_requests"]
    total_violations = _performance_metrics["sla_violations"]
    sla_compliance_rate = (
        ((total_requests - total_violations) / total_requests * 100)
        if total_requests > 0 else 100.0
    )

    # Recent violations (last 5 minutes)
    five_minutes_ago = current_time - 300
    recent_violations = [
        v for v in _performance_metrics["recent_violations"]
        if v["timestamp"] > five_minutes_ago
    ]

    return {
        "sla_monitoring": {
            "sla_threshold_seconds": SLA_ALERT_THRESHOLD,
            "total_requests": total_requests,
            "total_violations": total_violations,
            "compliance_rate_percent": round(sla_compliance_rate, 2),
            "recent_violations_5min": len(recent_violations)
        },
        "endpoint_metrics": _performance_metrics["endpoint_metrics"],
        "recent_violations": _performance_metrics["recent_violations"][-10:]  # Last 10 for display
    }
