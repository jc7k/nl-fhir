#!/usr/bin/env python3
"""
Test Performance Monitoring and SLA Alerting - Story 1
Tests comprehensive response time monitoring with 2-second SLA alerts
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from src.nl_fhir.main import app
from src.nl_fhir.api.middleware.timing import (
    get_performance_metrics,
    _performance_metrics,
    SLA_ALERT_THRESHOLD
)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def reset_metrics():
    """Reset performance metrics before each test"""
    _performance_metrics["total_requests"] = 0
    _performance_metrics["sla_violations"] = 0
    _performance_metrics["endpoint_metrics"] = {}
    _performance_metrics["recent_violations"] = []
    yield
    # Clean up after test
    _performance_metrics["total_requests"] = 0
    _performance_metrics["sla_violations"] = 0
    _performance_metrics["endpoint_metrics"] = {}
    _performance_metrics["recent_violations"] = []


class TestSLAMonitoring:
    """Test SLA monitoring and alerting functionality"""

    def test_sla_threshold_configuration(self, reset_metrics):
        """Test SLA threshold is properly configured at 2 seconds"""
        assert SLA_ALERT_THRESHOLD == 2.0

    def test_fast_request_no_violation(self, client, reset_metrics):
        """Test fast requests don't trigger SLA violations"""
        # Test health endpoint (should be fast)
        response = client.get("/health")
        assert response.status_code == 200

        # Check response headers
        assert "X-Response-Time" in response.headers
        assert "X-Request-ID" in response.headers
        assert "X-SLA-Violation" not in response.headers

        # Check metrics
        metrics = get_performance_metrics()
        assert metrics["sla_monitoring"]["total_violations"] == 0
        assert metrics["sla_monitoring"]["compliance_rate_percent"] == 100.0

    def test_sla_violation_detection(self, client, reset_metrics):
        """Test SLA violation detection and alerting"""
        # Mock a slow response that exceeds 2s threshold
        with patch('src.nl_fhir.api.middleware.timing.time.time') as mock_time:
            # Simulate request taking 3 seconds
            start_time = 1000.0
            end_time = 1003.0  # 3 seconds later
            # Create an iterator that yields start_time once, then end_time indefinitely
            def time_values():
                yield start_time
                while True:
                    yield end_time

            mock_time.side_effect = time_values()

            response = client.get("/health")
            assert response.status_code == 200

            # Check SLA violation header
            assert "X-SLA-Violation" in response.headers
            assert response.headers["X-SLA-Violation"] == "true"

    def test_metrics_endpoint_with_sla_data(self, client, reset_metrics):
        """Test /metrics endpoint includes SLA monitoring data"""
        # Make a few requests to generate metrics
        for _ in range(3):
            client.get("/health")

        # Check metrics endpoint
        response = client.get("/metrics")
        assert response.status_code == 200

        metrics = response.json()

        # Verify SLA monitoring section exists
        assert "sla_monitoring" in metrics
        sla_data = metrics["sla_monitoring"]

        assert "sla_threshold_seconds" in sla_data
        assert sla_data["sla_threshold_seconds"] == 2.0
        assert "total_requests" in sla_data
        assert "total_violations" in sla_data
        assert "compliance_rate_percent" in sla_data
        assert "recent_violations_5min" in sla_data

        # Verify endpoint performance tracking
        assert "endpoint_performance" in metrics
        assert "recent_sla_violations" in metrics
        assert "performance_summary" in metrics

    def test_endpoint_specific_metrics(self, client, reset_metrics):
        """Test endpoint-specific performance tracking"""
        # Make requests to different endpoints
        client.get("/health")
        client.get("/metrics")

        metrics = get_performance_metrics()
        endpoint_metrics = metrics["endpoint_metrics"]

        # Should have metrics for both endpoints
        assert "GET /health" in endpoint_metrics
        assert "GET /metrics" in endpoint_metrics

        # Check metric structure
        health_metrics = endpoint_metrics["GET /health"]
        assert "request_count" in health_metrics
        assert "error_count" in health_metrics
        assert "response_times" in health_metrics
        assert "sla_violations" in health_metrics
        assert "avg_response_time" in health_metrics
        assert "p95_response_time" in health_metrics

    def test_sla_violation_logging(self, client, reset_metrics, caplog):
        """Test SLA violation logging for alerting"""
        with patch('src.nl_fhir.api.middleware.timing.time.time') as mock_time:
            # Simulate request taking 3 seconds
            start_time = 1000.0
            end_time = 1003.0
            # Create an iterator that yields start_time once, then end_time indefinitely
            def time_values():
                yield start_time
                while True:
                    yield end_time

            mock_time.side_effect = time_values()

            client.get("/health")

            # Check SLA violation was logged
            assert "SLA VIOLATION" in caplog.text
            assert "exceeds 2.0s threshold" in caplog.text

    def test_performance_metrics_calculation(self, reset_metrics):
        """Test performance metrics calculations"""
        from src.nl_fhir.api.middleware.timing import _record_endpoint_metrics

        # Record some test metrics
        _record_endpoint_metrics("GET /test", 1.5, False)  # Fast request
        _record_endpoint_metrics("GET /test", 2.5, False)  # SLA violation
        _record_endpoint_metrics("GET /test", 0.8, False)  # Fast request

        metrics = get_performance_metrics()
        test_metrics = metrics["endpoint_metrics"]["GET /test"]

        # Check calculations
        assert test_metrics["request_count"] == 3
        assert test_metrics["error_count"] == 0
        assert len(test_metrics["response_times"]) == 3

        # Average should be (1.5 + 2.5 + 0.8) / 3 = 1.6
        expected_avg = (1.5 + 2.5 + 0.8) / 3
        assert abs(test_metrics["avg_response_time"] - expected_avg) < 0.01

    def test_recent_violations_tracking(self, reset_metrics):
        """Test recent violations tracking for dashboard"""
        from src.nl_fhir.api.middleware.timing import _record_sla_violation

        # Record some violations
        _record_sla_violation("req1", "GET /slow", 3.0)
        _record_sla_violation("req2", "GET /slower", 4.0)

        metrics = get_performance_metrics()
        violations = metrics["recent_violations"]

        assert len(violations) == 2
        assert violations[0]["request_id"] == "req1"
        assert violations[0]["endpoint"] == "GET /slow"
        assert violations[0]["response_time"] == 3.0
        assert violations[1]["request_id"] == "req2"

    def test_compliance_rate_calculation(self, reset_metrics):
        """Test SLA compliance rate calculation"""
        from src.nl_fhir.api.middleware.timing import _record_endpoint_metrics, _record_sla_violation

        # Record 10 requests, 2 violations
        for i in range(8):
            _record_endpoint_metrics("GET /test", 1.0, False)  # Fast

        for i in range(2):
            _record_endpoint_metrics("GET /test", 3.0, False)  # Slow
            _record_sla_violation(f"req{i}", "GET /test", 3.0)

        metrics = get_performance_metrics()
        sla_data = metrics["sla_monitoring"]

        # Should be 80% compliance (8/10 requests under SLA)
        assert sla_data["total_requests"] == 10
        assert sla_data["total_violations"] == 2
        assert sla_data["compliance_rate_percent"] == 80.0

    def test_error_request_handling(self, client, reset_metrics):
        """Test error requests are properly tracked"""
        # Request non-existent endpoint
        response = client.get("/nonexistent")
        assert response.status_code == 404

        # Should still have performance headers
        assert "X-Response-Time" in response.headers
        assert "X-Request-ID" in response.headers

        # Check metrics recorded the error
        metrics = get_performance_metrics()
        endpoint_metrics = metrics["endpoint_metrics"]["GET /nonexistent"]
        assert endpoint_metrics["error_count"] >= 1


class TestResponseTimeHeaders:
    """Test response time headers for monitoring"""

    def test_response_time_header_format(self, client):
        """Test response time header is properly formatted"""
        response = client.get("/health")

        assert "X-Response-Time" in response.headers
        response_time = response.headers["X-Response-Time"]

        # Should be in format "123.45ms"
        assert response_time.endswith("ms")
        time_value = float(response_time[:-2])
        assert time_value > 0

    def test_request_id_header(self, client):
        """Test request ID header for tracing"""
        response = client.get("/health")

        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]

        # Should be 8-character UUID prefix
        assert len(request_id) == 8
        assert request_id.replace("-", "").isalnum()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])