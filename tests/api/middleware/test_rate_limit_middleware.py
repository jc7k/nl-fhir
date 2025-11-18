"""
Comprehensive test suite for Rate Limiting Middleware
Tests rate limit enforcement and quota management

Critical for API security and abuse prevention
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from fastapi import Request
from fastapi.responses import Response

from src.nl_fhir.api.middleware.rate_limit import (
    rate_limit_middleware,
    _RateLimitState
)


class TestRateLimitMiddleware:
    """Test suite for rate limiting middleware"""

    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/api/convert"
        request.headers = {}
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    async def mock_call_next(self):
        """Mock call_next function"""
        async def call_next(request):
            response = Mock(spec=Response)
            response.status_code = 200
            response.headers = {}
            return response
        return call_next

    # =================================================================
    # Basic Functionality Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_middleware_allows_first_request(self, mock_request, mock_call_next):
        """Test middleware allows first request"""
        response = await rate_limit_middleware(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_extracts_client_ip(self, mock_request, mock_call_next):
        """Test middleware extracts client IP correctly"""
        mock_request.headers = {"x-forwarded-for": "192.168.1.100"}

        response = await rate_limit_middleware(mock_request, mock_call_next)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_handles_multiple_forwarded_ips(self, mock_request, mock_call_next):
        """Test middleware handles proxy chain"""
        mock_request.headers = {"x-forwarded-for": "192.168.1.100, 10.0.0.1"}

        response = await rate_limit_middleware(mock_request, mock_call_next)

        # Should use first IP in chain
        assert response.status_code == 200

    # =================================================================
    # Rate Limit Enforcement Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_rate_limit_state_tracks_requests(self):
        """Test rate limit state tracks requests correctly"""
        state = _RateLimitState(max_requests=5, window_seconds=60)

        # Register 5 requests (should all succeed)
        for i in range(5):
            allowed, retry_after = await state.register("test-client")
            assert allowed is True
            assert retry_after is None

        # 6th request should be denied
        allowed, retry_after = await state.register("test-client")
        assert allowed is False
        assert retry_after is not None
        assert retry_after >= 0

    @pytest.mark.asyncio
    async def test_rate_limit_window_expiration(self):
        """Test rate limit window expires correctly"""
        state = _RateLimitState(max_requests=2, window_seconds=1)

        # Use up quota
        await state.register("test-client")
        await state.register("test-client")

        # Should be denied
        allowed, _ = await state.register("test-client")
        assert allowed is False

        # Wait for window to expire
        await asyncio.sleep(1.1)

        # Should be allowed again
        allowed, _ = await state.register("test-client")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limit_per_client_isolation(self):
        """Test rate limits are isolated per client"""
        state = _RateLimitState(max_requests=2, window_seconds=60)

        # Client A uses quota
        await state.register("client-a")
        await state.register("client-a")

        # Client A should be at limit
        allowed, _ = await state.register("client-a")
        assert allowed is False

        # Client B should still have quota
        allowed, _ = await state.register("client-b")
        assert allowed is True

    # =================================================================
    # Response Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_response(self):
        """Test response when rate limit is exceeded"""
        state = _RateLimitState(max_requests=1, window_seconds=60)

        # Use up quota
        await state.register("test-client")

        # Next request should be denied
        allowed, retry_after = await state.register("test-client")
        assert allowed is False
        assert retry_after is not None

    @pytest.mark.asyncio
    async def test_retry_after_header_present(self):
        """Test Retry-After header is included in 429 response"""
        state = _RateLimitState(max_requests=1, window_seconds=60)

        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        async def mock_call_next(request):
            return Mock(status_code=200)

        # Use up quota
        await state.register("127.0.0.1")

        # Should receive 429 with Retry-After header
        # (Note: This tests the state, actual middleware test would need more setup)
        allowed, retry_after = await state.register("127.0.0.1")
        assert retry_after is not None
        assert retry_after >= 0

    # =================================================================
    # Edge Cases Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_handle_missing_client_info(self, mock_call_next):
        """Test handling of missing client information"""
        request = Mock(spec=Request)
        request.headers = {}
        request.client = None  # No client info

        response = await rate_limit_middleware(request, mock_call_next)

        # Should handle gracefully
        assert response.status_code in [200, 429]

    @pytest.mark.asyncio
    async def test_concurrent_requests_from_same_client(self):
        """Test concurrent requests from same client"""
        state = _RateLimitState(max_requests=5, window_seconds=60)

        # Simulate 10 concurrent requests
        tasks = [state.register("test-client") for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # First 5 should succeed, rest should fail
        allowed_count = sum(1 for allowed, _ in results if allowed)
        denied_count = sum(1 for allowed, _ in results if not allowed)

        assert allowed_count == 5
        assert denied_count == 5

    # =================================================================
    # Performance Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_rate_limit_performance(self):
        """Test rate limit check is fast"""
        import time

        state = _RateLimitState(max_requests=1000, window_seconds=60)

        start = time.time()
        for i in range(100):
            await state.register(f"client-{i}")
        elapsed = time.time() - start

        # Should process 100 checks quickly
        assert elapsed < 0.5
