"""
Comprehensive test suite for Request Timing Middleware
Tests request timing, size validation, and SLA monitoring

Critical for API reliability and performance monitoring
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request
from fastapi.responses import Response

from src.nl_fhir.api.middleware.timing import (
    request_timing_and_validation,
    _performance_metrics
)


class TestRequestTimingMiddleware:
    """Test suite for request timing middleware"""

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
    def mock_response(self):
        """Create mock response"""
        response = Mock(spec=Response)
        response.status_code = 200
        response.headers = {}
        return response

    @pytest.fixture
    async def mock_call_next_fast(self, mock_response):
        """Mock call_next that returns quickly"""
        async def call_next(request):
            await asyncio.sleep(0.01)  # 10ms response
            return mock_response
        return call_next

    @pytest.fixture
    async def mock_call_next_slow(self, mock_response):
        """Mock call_next that exceeds SLA"""
        async def call_next(request):
            await asyncio.sleep(2.5)  # 2.5s response - exceeds 2s SLA
            return mock_response
        return call_next

    # =================================================================
    # Basic Functionality Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_middleware_processes_request(self, mock_request, mock_call_next_fast):
        """Test middleware processes request successfully"""
        response = await request_timing_and_validation(mock_request, mock_call_next_fast)

        assert response is not None
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_adds_timing_headers(self, mock_request, mock_call_next_fast):
        """Test middleware adds response time headers"""
        response = await request_timing_and_validation(mock_request, mock_call_next_fast)

        assert "X-Response-Time" in response.headers
        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_response_time_header_format(self, mock_request, mock_call_next_fast):
        """Test response time header is properly formatted"""
        response = await request_timing_and_validation(mock_request, mock_call_next_fast)

        response_time = response.headers["X-Response-Time"]
        assert response_time.endswith("ms")
        # Should be numeric value
        numeric_value = float(response_time.replace("ms", ""))
        assert numeric_value > 0

    @pytest.mark.asyncio
    async def test_request_id_generated(self, mock_request, mock_call_next_fast):
        """Test unique request ID is generated"""
        response1 = await request_timing_and_validation(mock_request, mock_call_next_fast)
        response2 = await request_timing_and_validation(mock_request, mock_call_next_fast)

        request_id1 = response1.headers["X-Request-ID"]
        request_id2 = response2.headers["X-Request-ID"]

        assert len(request_id1) == 8  # Short request ID
        assert len(request_id2) == 8
        assert request_id1 != request_id2  # Should be unique

    # =================================================================
    # Request Size Validation Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_reject_oversized_request(self, mock_request, mock_call_next_fast):
        """Test middleware rejects requests exceeding size limit"""
        # Simulate large request (10 MB)
        mock_request.headers = {"content-length": str(10 * 1024 * 1024)}

        response = await request_timing_and_validation(mock_request, mock_call_next_fast)

        assert response.status_code == 413  # Request Entity Too Large

    @pytest.mark.asyncio
    async def test_accept_normal_sized_request(self, mock_request, mock_call_next_fast):
        """Test middleware accepts normal-sized requests"""
        # Simulate normal request (1 KB)
        mock_request.headers = {"content-length": "1024"}

        response = await request_timing_and_validation(mock_request, mock_call_next_fast)

        assert response.status_code == 200

    # =================================================================
    # SLA Violation Detection Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_detect_sla_violation(self, mock_request, mock_call_next_slow):
        """Test middleware detects SLA violations"""
        response = await request_timing_and_validation(mock_request, mock_call_next_slow)

        # Should add SLA violation header
        assert "X-SLA-Violation" in response.headers
        assert response.headers["X-SLA-Violation"] == "true"

    @pytest.mark.asyncio
    async def test_no_sla_violation_for_fast_requests(self, mock_request, mock_call_next_fast):
        """Test no SLA violation for fast requests"""
        response = await request_timing_and_validation(mock_request, mock_call_next_fast)

        # Should not have SLA violation header
        assert "X-SLA-Violation" not in response.headers

    # =================================================================
    # Error Handling Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_middleware_handles_exceptions(self, mock_request):
        """Test middleware handles exceptions gracefully"""
        async def call_next_with_error(request):
            raise Exception("Simulated error")

        response = await request_timing_and_validation(mock_request, call_next_with_error)

        # Should return error response
        assert response.status_code == 500

    # =================================================================
    # Performance Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_middleware_overhead_minimal(self, mock_request, mock_call_next_fast):
        """Test middleware adds minimal overhead"""
        import time

        start = time.time()
        response = await request_timing_and_validation(mock_request, mock_call_next_fast)
        elapsed = time.time() - start

        # Middleware overhead should be negligible (<100ms)
        assert elapsed < 0.1
        assert response.status_code == 200
