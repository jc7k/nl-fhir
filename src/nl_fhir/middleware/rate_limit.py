"""
Rate Limiting Middleware for Production
HIPAA Compliant: No PHI in rate limiting logic
Production Ready: Token bucket algorithm with Redis support (future)
"""

import time
import logging
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Rate limiting middleware using token bucket algorithm
    In-memory implementation for Epic 1, Redis support in Epic 3
    """
    
    def __init__(self, app, requests_per_minute: int = 100):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.request_interval = 60.0 / requests_per_minute
        
        # In-memory storage (will be replaced with Redis in production)
        self.clients: Dict[str, Tuple[float, int]] = defaultdict(lambda: (time.time(), 0))
        self.cleanup_interval = 300  # Clean up old entries every 5 minutes
        self.last_cleanup = time.time()
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics", "/ready", "/live"]:
            return await call_next(request)
        
        # Get client identifier (IP address or API key in future)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        allowed, retry_after = self._check_rate_limit(client_id)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for client {client_id[:8]}...")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please retry after {retry_after:.1f} seconds",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(int(retry_after)),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Reset": str(int(time.time() + retry_after))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(self._get_remaining_requests(client_id))
        
        # Periodic cleanup of old entries
        self._cleanup_if_needed()
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Use IP address for now, can add API key support later
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip_{client_ip}"
    
    def _check_rate_limit(self, client_id: str) -> Tuple[bool, float]:
        """
        Check if request is allowed under rate limit
        Returns (allowed, retry_after_seconds)
        """
        current_time = time.time()
        last_request_time, request_count = self.clients[client_id]
        
        # Calculate time since last request
        time_passed = current_time - last_request_time
        
        # Token bucket algorithm
        if time_passed >= self.request_interval:
            # Enough time has passed, reset the counter
            self.clients[client_id] = (current_time, 1)
            return True, 0.0
        
        # Check if we're within the current window
        if request_count < self.requests_per_minute:
            # Still have tokens available
            self.clients[client_id] = (last_request_time, request_count + 1)
            return True, 0.0
        
        # Rate limit exceeded, calculate retry time
        retry_after = self.request_interval - time_passed
        return False, retry_after
    
    def _get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        if client_id not in self.clients:
            return self.requests_per_minute
        
        _, request_count = self.clients[client_id]
        return max(0, self.requests_per_minute - request_count)
    
    def _cleanup_if_needed(self):
        """Clean up old client entries to prevent memory leak"""
        current_time = time.time()
        
        if current_time - self.last_cleanup > self.cleanup_interval:
            # Remove entries older than 1 hour
            cutoff_time = current_time - 3600
            old_clients = [
                client_id for client_id, (last_time, _) in self.clients.items()
                if last_time < cutoff_time
            ]
            
            for client_id in old_clients:
                del self.clients[client_id]
            
            if old_clients:
                logger.info(f"Cleaned up {len(old_clients)} old rate limit entries")
            
            self.last_cleanup = current_time