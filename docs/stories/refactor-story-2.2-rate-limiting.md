# Story: Consolidate Rate Limiting Implementation

**Story ID:** REFACTOR-007
**Epic:** Middleware Consolidation (Epic 2)
**Status:** READY FOR DEVELOPMENT
**Estimated Effort:** 8 hours
**Priority:** P1 - High

## User Story

**As a** platform engineer
**I want** a unified rate limiting implementation with Redis support
**So that** rate limits are consistently enforced across all endpoints with production scalability

## Background & Context

The NL-FHIR codebase currently has **duplicate rate limiting implementations** with different algorithms and capabilities:

**Current State:**
- **Primary middleware:** `src/nl_fhir/middleware/rate_limit.py` (RateLimitMiddleware class, 138 lines)
  - Token bucket algorithm with in-memory storage
  - Comprehensive features: cleanup, retry headers, configurable limits
  - Production-ready logging and monitoring
- **API middleware:** `src/nl_fhir/api/middleware/rate_limit.py` (rate_limit_middleware function, 70 lines)
  - Sliding window algorithm with asyncio locks
  - Simpler implementation, cleaner code structure
  - Better concurrency handling

**Target State:**
- Single unified rate limiting middleware combining best features
- Redis backend support for distributed deployment
- Configurable algorithms (token bucket vs sliding window)
- Endpoint-specific rate limits
- Comprehensive monitoring and metrics

## Analysis of Current Implementations

### `/middleware/rate_limit.py` (Primary)
**Strengths:**
- Comprehensive token bucket algorithm
- Rich monitoring (retry headers, remaining requests)
- Automatic cleanup of old entries
- Health check endpoint exclusions
- Detailed error responses with retry guidance

**Issues:**
- In-memory only (not suitable for multi-instance deployment)
- Basic dictionary storage (no TTL)
- Missing async optimization
- No endpoint-specific limits

### `/api/middleware/rate_limit.py` (Duplicate)
**Strengths:**
- Async-optimized with proper locking
- Clean sliding window algorithm
- Automatic expiration with deque structure
- Memory efficient timestamp management

**Issues:**
- Simpler feature set
- No rate limit headers in response
- Basic error messages
- No monitoring/metrics

## Acceptance Criteria

### Must Have
- [ ] Single unified rate limiting middleware implementation
- [ ] Combine best features from both existing implementations
- [ ] Support both in-memory and Redis backends
- [ ] Configurable rate limiting algorithms (token bucket, sliding window)
- [ ] Endpoint-specific rate limits with pattern matching
- [ ] Comprehensive rate limit headers (limit, remaining, reset)
- [ ] Health check and static resource exclusions
- [ ] Graceful degradation when Redis unavailable
- [ ] Remove duplicate `/api/middleware/rate_limit.py` file
- [ ] 100% backward compatibility with existing rate limiting behavior

### Should Have
- [ ] Redis cluster support for high availability
- [ ] Rate limit metrics collection (Prometheus format)
- [ ] Dynamic rate limit adjustment via configuration
- [ ] IP-based and API key-based rate limiting
- [ ] Rate limit bypass for whitelisted clients
- [ ] Distributed rate limiting across multiple instances

### Could Have
- [ ] Adaptive rate limiting based on system load
- [ ] Rate limit warming for new clients
- [ ] Geographic rate limiting
- [ ] Advanced analytics and reporting

## Technical Specifications

### 1. Unified Rate Limiting Architecture

```python
# src/nl_fhir/middleware/rate_limit.py (Enhanced)

"""
Unified Rate Limiting Middleware for NL-FHIR
Combines token bucket and sliding window algorithms
Supports both in-memory and Redis backends
"""

import asyncio
import time
import logging
from abc import ABC, abstractmethod
from collections import deque
from typing import Dict, Tuple, Optional, Union, List
from dataclasses import dataclass
from enum import Enum

from fastapi import Request, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis

from ..config import settings

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(Enum):
    """Supported rate limiting algorithms"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"


@dataclass
class RateLimitRule:
    """Configuration for a rate limiting rule"""
    pattern: str  # URL pattern (regex or glob)
    requests_per_minute: int
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    burst_limit: Optional[int] = None  # For token bucket
    enabled: bool = True


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    retry_after: float
    remaining_requests: int
    reset_time: float
    rule_used: str


class RateLimitBackend(ABC):
    """Abstract base for rate limiting backends"""

    @abstractmethod
    async def check_rate_limit(
        self,
        client_id: str,
        rule: RateLimitRule
    ) -> RateLimitResult:
        """Check if request is allowed under rate limit"""
        pass

    @abstractmethod
    async def cleanup(self):
        """Clean up expired entries"""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, int]:
        """Get backend statistics"""
        pass


class InMemoryRateLimitBackend(RateLimitBackend):
    """In-memory rate limiting backend"""

    def __init__(self):
        self._token_buckets: Dict[str, Tuple[float, int]] = {}
        self._sliding_windows: Dict[str, deque] = {}
        self._lock = asyncio.Lock()
        self.last_cleanup = time.time()

    async def check_rate_limit(
        self,
        client_id: str,
        rule: RateLimitRule
    ) -> RateLimitResult:
        """Check rate limit using specified algorithm"""

        async with self._lock:
            if rule.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                return await self._check_token_bucket(client_id, rule)
            else:
                return await self._check_sliding_window(client_id, rule)

    async def _check_token_bucket(
        self,
        client_id: str,
        rule: RateLimitRule
    ) -> RateLimitResult:
        """Token bucket algorithm implementation"""

        current_time = time.time()
        key = f"{client_id}:{rule.pattern}"

        if key not in self._token_buckets:
            self._token_buckets[key] = (current_time, rule.requests_per_minute)

        last_update, tokens = self._token_buckets[key]

        # Calculate tokens to add based on time passed
        time_passed = current_time - last_update
        tokens_to_add = int(time_passed * (rule.requests_per_minute / 60.0))
        tokens = min(rule.requests_per_minute, tokens + tokens_to_add)

        if tokens >= 1:
            # Request allowed
            self._token_buckets[key] = (current_time, tokens - 1)
            return RateLimitResult(
                allowed=True,
                retry_after=0.0,
                remaining_requests=tokens - 1,
                reset_time=current_time + 60.0,
                rule_used=rule.pattern
            )
        else:
            # Rate limit exceeded
            retry_after = 60.0 / rule.requests_per_minute
            return RateLimitResult(
                allowed=False,
                retry_after=retry_after,
                remaining_requests=0,
                reset_time=current_time + retry_after,
                rule_used=rule.pattern
            )

    async def _check_sliding_window(
        self,
        client_id: str,
        rule: RateLimitRule
    ) -> RateLimitResult:
        """Sliding window algorithm implementation"""

        current_time = time.time()
        window_start = current_time - 60.0  # 1 minute window
        key = f"{client_id}:{rule.pattern}"

        if key not in self._sliding_windows:
            self._sliding_windows[key] = deque()

        timestamps = self._sliding_windows[key]

        # Remove expired timestamps
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= rule.requests_per_minute:
            # Rate limit exceeded
            retry_after = timestamps[0] + 60.0 - current_time
            return RateLimitResult(
                allowed=False,
                retry_after=max(retry_after, 0.0),
                remaining_requests=0,
                reset_time=timestamps[0] + 60.0,
                rule_used=rule.pattern
            )
        else:
            # Request allowed
            timestamps.append(current_time)
            return RateLimitResult(
                allowed=True,
                retry_after=0.0,
                remaining_requests=rule.requests_per_minute - len(timestamps),
                reset_time=current_time + 60.0,
                rule_used=rule.pattern
            )

    async def cleanup(self):
        """Clean up expired entries"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # 1 hour

        # Clean token buckets
        expired_buckets = [
            key for key, (last_update, _) in self._token_buckets.items()
            if last_update < cutoff_time
        ]
        for key in expired_buckets:
            del self._token_buckets[key]

        # Clean sliding windows
        expired_windows = []
        for key, timestamps in self._sliding_windows.items():
            if not timestamps or timestamps[-1] < cutoff_time:
                expired_windows.append(key)

        for key in expired_windows:
            del self._sliding_windows[key]

        if expired_buckets or expired_windows:
            logger.info(
                f"Cleaned up {len(expired_buckets)} token buckets "
                f"and {len(expired_windows)} sliding windows"
            )

    async def get_stats(self) -> Dict[str, int]:
        """Get backend statistics"""
        return {
            "token_buckets": len(self._token_buckets),
            "sliding_windows": len(self._sliding_windows),
            "backend_type": "in_memory"
        }


class RedisRateLimitBackend(RateLimitBackend):
    """Redis-backed rate limiting backend"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self._connected = False

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection with automatic reconnection"""
        if not self._redis or not self._connected:
            try:
                self._redis = redis.from_url(self.redis_url)
                await self._redis.ping()
                self._connected = True
                logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._connected = False
                raise

        return self._redis

    async def check_rate_limit(
        self,
        client_id: str,
        rule: RateLimitRule
    ) -> RateLimitResult:
        """Check rate limit using Redis"""

        try:
            redis_client = await self._get_redis()

            if rule.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                return await self._redis_token_bucket(redis_client, client_id, rule)
            else:
                return await self._redis_sliding_window(redis_client, client_id, rule)

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fallback to allow request if Redis fails
            return RateLimitResult(
                allowed=True,
                retry_after=0.0,
                remaining_requests=rule.requests_per_minute,
                reset_time=time.time() + 60.0,
                rule_used=f"{rule.pattern}:fallback"
            )

    async def _redis_sliding_window(
        self,
        redis_client: redis.Redis,
        client_id: str,
        rule: RateLimitRule
    ) -> RateLimitResult:
        """Sliding window implementation using Redis"""

        current_time = time.time()
        window_start = current_time - 60.0
        key = f"rate_limit:{client_id}:{rule.pattern}"

        # Use Redis sorted set for sliding window
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # Remove expired
        pipe.zadd(key, {str(current_time): current_time})  # Add current request
        pipe.zcard(key)  # Count requests in window
        pipe.expire(key, 120)  # Set TTL for cleanup

        results = await pipe.execute()
        request_count = results[2]

        if request_count > rule.requests_per_minute:
            # Get oldest request time for retry calculation
            oldest = await redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                retry_after = oldest[0][1] + 60.0 - current_time
            else:
                retry_after = 1.0

            return RateLimitResult(
                allowed=False,
                retry_after=max(retry_after, 0.0),
                remaining_requests=0,
                reset_time=current_time + retry_after,
                rule_used=rule.pattern
            )
        else:
            return RateLimitResult(
                allowed=True,
                retry_after=0.0,
                remaining_requests=rule.requests_per_minute - request_count,
                reset_time=current_time + 60.0,
                rule_used=rule.pattern
            )

    async def cleanup(self):
        """Cleanup handled automatically by Redis TTL"""
        pass

    async def get_stats(self) -> Dict[str, int]:
        """Get Redis backend statistics"""
        try:
            redis_client = await self._get_redis()
            info = await redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "backend_type": "redis"
            }
        except Exception as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {"backend_type": "redis", "error": str(e)}


class UnifiedRateLimitMiddleware:
    """
    Unified rate limiting middleware combining best practices.
    Supports multiple backends and algorithms.
    """

    def __init__(self, app):
        self.app = app
        self._initialize_backend()
        self._initialize_rules()
        self.excluded_paths = {"/health", "/metrics", "/ready", "/live"}

    def _initialize_backend(self):
        """Initialize rate limiting backend"""
        if settings.redis_url and settings.use_redis_rate_limiting:
            self.backend = RedisRateLimitBackend(settings.redis_url)
            logger.info("Using Redis backend for rate limiting")
        else:
            self.backend = InMemoryRateLimitBackend()
            logger.info("Using in-memory backend for rate limiting")

    def _initialize_rules(self):
        """Initialize rate limiting rules"""
        self.rules = [
            RateLimitRule(
                pattern="/api/.*",
                requests_per_minute=settings.api_rate_limit_per_minute,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW
            ),
            RateLimitRule(
                pattern="/convert",
                requests_per_minute=settings.convert_rate_limit_per_minute,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET
            ),
            RateLimitRule(
                pattern=".*",  # Default rule
                requests_per_minute=settings.default_rate_limit_per_minute,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW
            )
        ]

    async def __call__(self, request: Request, call_next):
        """Process request with unified rate limiting"""

        # Skip rate limiting for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)

        # Find matching rule
        rule = self._find_matching_rule(request.url.path)

        # Check rate limit
        result = await self.backend.check_rate_limit(client_id, rule)

        if not result.allowed:
            logger.warning(
                f"Rate limit exceeded for {client_id[:8]}... "
                f"on {request.url.path} (rule: {result.rule_used})"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please retry after {result.retry_after:.1f} seconds",
                    "retry_after": result.retry_after,
                    "rule": result.rule_used
                },
                headers={
                    "Retry-After": str(int(result.retry_after)),
                    "X-RateLimit-Limit": str(rule.requests_per_minute),
                    "X-RateLimit-Remaining": str(result.remaining_requests),
                    "X-RateLimit-Reset": str(int(result.reset_time))
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(rule.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining_requests)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_time))

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Check for API key first (future enhancement)
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key_{api_key[:8]}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip_{client_ip}"

    def _find_matching_rule(self, path: str) -> RateLimitRule:
        """Find the first matching rate limit rule"""
        import re

        for rule in self.rules:
            if re.match(rule.pattern, path):
                return rule

        # Should not happen due to catch-all rule, but fallback
        return RateLimitRule(
            pattern="fallback",
            requests_per_minute=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        )


# Factory function for FastAPI middleware registration
def create_rate_limit_middleware():
    """Create rate limit middleware instance for FastAPI registration"""

    async def rate_limit_middleware(request: Request, call_next):
        """FastAPI middleware function"""
        middleware = UnifiedRateLimitMiddleware(None)
        return await middleware(request, call_next)

    return rate_limit_middleware
```

### 2. Configuration Enhancement

```python
# src/nl_fhir/config.py (additions)

class Settings:
    # ... existing settings ...

    # Rate limiting configuration
    use_redis_rate_limiting: bool = False
    redis_url: str = "redis://localhost:6379"

    # Default rate limits
    default_rate_limit_per_minute: int = 100
    api_rate_limit_per_minute: int = 60
    convert_rate_limit_per_minute: int = 30

    # Rate limiting features
    enable_rate_limit_metrics: bool = True
    rate_limit_cleanup_interval: int = 300  # 5 minutes

    # Client identification
    enable_api_key_rate_limiting: bool = False
    rate_limit_whitelist: List[str] = []  # IPs to whitelist
```

## Test Requirements

### Unit Tests

```python
# tests/middleware/test_unified_rate_limit.py

import pytest
import asyncio
import time
from unittest.mock import Mock, patch

from src.nl_fhir.middleware.rate_limit import (
    UnifiedRateLimitMiddleware,
    InMemoryRateLimitBackend,
    RateLimitRule,
    RateLimitAlgorithm
)


class TestInMemoryRateLimitBackend:

    @pytest.fixture
    def backend(self):
        return InMemoryRateLimitBackend()

    @pytest.fixture
    def sliding_window_rule(self):
        return RateLimitRule(
            pattern="/api/test",
            requests_per_minute=5,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        )

    @pytest.fixture
    def token_bucket_rule(self):
        return RateLimitRule(
            pattern="/api/convert",
            requests_per_minute=3,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )

    @pytest.mark.asyncio
    async def test_sliding_window_allows_initial_requests(self, backend, sliding_window_rule):
        """Initial requests should be allowed"""
        client_id = "test_client"

        for i in range(5):
            result = await backend.check_rate_limit(client_id, sliding_window_rule)
            assert result.allowed is True
            assert result.remaining_requests == 4 - i

    @pytest.mark.asyncio
    async def test_sliding_window_blocks_excess_requests(self, backend, sliding_window_rule):
        """Requests exceeding limit should be blocked"""
        client_id = "test_client"

        # Use up the limit
        for _ in range(5):
            await backend.check_rate_limit(client_id, sliding_window_rule)

        # Next request should be blocked
        result = await backend.check_rate_limit(client_id, sliding_window_rule)
        assert result.allowed is False
        assert result.retry_after > 0

    @pytest.mark.asyncio
    async def test_token_bucket_allows_burst(self, backend, token_bucket_rule):
        """Token bucket should allow initial burst"""
        client_id = "test_client"

        # Should allow 3 immediate requests
        for i in range(3):
            result = await backend.check_rate_limit(client_id, token_bucket_rule)
            assert result.allowed is True

    @pytest.mark.asyncio
    async def test_token_bucket_refills_over_time(self, backend, token_bucket_rule):
        """Token bucket should refill tokens over time"""
        client_id = "test_client"

        # Use up all tokens
        for _ in range(3):
            await backend.check_rate_limit(client_id, token_bucket_rule)

        # Should be blocked
        result = await backend.check_rate_limit(client_id, token_bucket_rule)
        assert result.allowed is False

        # Mock time advancement
        with patch('time.time', return_value=time.time() + 30):
            result = await backend.check_rate_limit(client_id, token_bucket_rule)
            assert result.allowed is True  # Should have refilled some tokens

    @pytest.mark.asyncio
    async def test_different_clients_independent(self, backend, sliding_window_rule):
        """Different clients should have independent rate limits"""
        result1 = await backend.check_rate_limit("client1", sliding_window_rule)
        result2 = await backend.check_rate_limit("client2", sliding_window_rule)

        assert result1.allowed is True
        assert result2.allowed is True
        assert result1.remaining_requests == result2.remaining_requests


class TestUnifiedRateLimitMiddleware:

    @pytest.fixture
    def app(self):
        from fastapi import FastAPI
        app = FastAPI()

        @app.get("/api/test")
        async def test_endpoint():
            return {"message": "test"}

        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}

        return app

    @pytest.fixture
    def middleware(self, app):
        return UnifiedRateLimitMiddleware(app)

    @pytest.mark.asyncio
    async def test_health_endpoint_excluded(self, middleware):
        """Health endpoints should be excluded from rate limiting"""
        from fastapi import Request

        request = Mock(spec=Request)
        request.url.path = "/health"

        # Mock call_next
        async def mock_call_next(req):
            response = Mock()
            response.headers = {}
            return response

        response = await middleware(request, mock_call_next)

        # Should not add rate limit headers to excluded endpoints
        assert "X-RateLimit-Limit" not in response.headers

    @pytest.mark.asyncio
    async def test_rate_limit_headers_added(self, middleware):
        """Rate limit headers should be added to responses"""
        from fastapi import Request

        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.client.host = "127.0.0.1"
        request.headers = {}

        async def mock_call_next(req):
            response = Mock()
            response.headers = {}
            return response

        response = await middleware(request, mock_call_next)

        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
```

## Performance Requirements

- Rate limit check: <2ms per request (in-memory), <10ms (Redis)
- Memory usage (in-memory): <50MB for 10,000 active clients
- Redis operations: <5ms per operation
- Cleanup overhead: <100ms every 5 minutes
- No impact on non-rate-limited requests

## Migration & Rollback Plan

### Migration Steps
1. **Phase 1:** Create unified implementation with feature flags
2. **Phase 2:** Test with small percentage of traffic
3. **Phase 3:** Gradually migrate all endpoints
4. **Phase 4:** Remove duplicate implementation

### Rollback Plan
- Feature flag to switch back to original implementation
- Redis fallback to in-memory on connection failure
- Graceful degradation (allow requests) on backend failure

## Dependencies

**Technical Dependencies:**
- Redis (optional, for distributed rate limiting)
- FastAPI middleware system
- asyncio support

**Depends On:**
- REFACTOR-006: Security middleware consolidation (should complete first)

**Blocks:**
- Future distributed deployment enhancements
- API key authentication system

## File List

**Files to Create:**
- `tests/middleware/test_unified_rate_limit.py` - Comprehensive unit tests
- `tests/integration/test_rate_limit_integration.py` - Integration tests

**Files to Modify:**
- `src/nl_fhir/middleware/rate_limit.py` - Enhanced unified implementation
- `src/nl_fhir/config.py` - Rate limiting configuration
- `src/nl_fhir/main.py` - Middleware registration updates
- `requirements.txt` - Add redis dependency

**Files to Delete:**
- `src/nl_fhir/api/middleware/rate_limit.py` - Duplicate implementation

## Definition of Done

- [ ] Unified rate limiting middleware implemented with both algorithms
- [ ] Redis backend support with fallback to in-memory
- [ ] Endpoint-specific rate limits working
- [ ] All existing rate limiting behavior maintained
- [ ] Comprehensive unit and integration tests
- [ ] Performance benchmarks met
- [ ] Redis cluster support tested
- [ ] Graceful degradation validated
- [ ] Duplicate middleware removed
- [ ] Monitoring and metrics collection working
- [ ] Documentation updated

---
**Story Status:** READY FOR DEVELOPMENT
**Dependencies:** REFACTOR-006 (Security Middleware Consolidation)
**Next Story:** REFACTOR-008 - Epic 3: Code Organization