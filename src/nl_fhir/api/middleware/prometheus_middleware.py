"""
Prometheus Metrics Middleware

Automatically tracks HTTP request metrics for all endpoints.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ...monitoring.metrics import MetricsCollector


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect Prometheus metrics for HTTP requests
    
    Tracks:
    - Request counts by method, endpoint, and status
    - Request duration/latency
    - System resource usage
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics"""
        # Skip metrics collection for metrics endpoint itself
        if request.url.path == "/metrics/prometheus":
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Record error and re-raise
            MetricsCollector.record_error(
                error_type=type(e).__name__,
                severity='high'
            )
            raise
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Normalize endpoint path (remove IDs and parameters for better grouping)
        endpoint = self._normalize_path(request.url.path)
        
        # Record metrics
        MetricsCollector.record_http_request(
            method=request.method,
            endpoint=endpoint,
            status=status_code,
            duration=duration
        )
        
        return response
    
    @staticmethod
    def _normalize_path(path: str) -> str:
        """
        Normalize path for better metric grouping
        
        Example:
        - /api/v1/patient/12345 -> /api/v1/patient/{id}
        - /validate/bundle/xyz -> /validate/bundle/{id}
        """
        # Replace UUIDs and IDs with placeholders
        import re
        
        # UUID pattern
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{uuid}',
            path,
            flags=re.IGNORECASE
        )
        
        # Numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Alphanumeric IDs (at least 6 chars)
        path = re.sub(r'/[a-zA-Z0-9]{6,}', '/{id}', path)
        
        return path
