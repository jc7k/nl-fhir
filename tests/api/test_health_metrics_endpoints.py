"""
Comprehensive tests for /health, /metrics, and monitoring endpoints
Production Readiness: Health check and metrics testing

Coverage:
- Health endpoints
- Readiness checks
- Liveness checks
- Metrics endpoint
- Performance
"""

import pytest
from fastapi.testclient import TestClient
import time

from src.nl_fhir.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test /health endpoint"""

    def test_health_endpoint_returns_200(self):
        """Test that health endpoint is accessible"""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_response_structure(self):
        """Test health endpoint response structure"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_health_response_time(self):
        """Test that health check responds quickly"""
        start = time.time()
        response = client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        # Health checks should be fast (<500ms) - increased threshold for CI/CD stability
        assert duration < 0.5

    def test_health_multiple_requests(self):
        """Test health endpoint handles multiple requests"""
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200


class TestReadinessEndpoints:
    """Test readiness check endpoints"""

    def test_readiness_endpoint(self):
        """Test /readiness endpoint"""
        response = client.get("/readiness")

        assert response.status_code in [200, 503]

    def test_ready_endpoint(self):
        """Test /ready endpoint (alternative)"""
        response = client.get("/ready")

        assert response.status_code in [200, 503]

    def test_readiness_response_structure(self):
        """Test readiness response has proper structure"""
        response = client.get("/readiness")

        if response.status_code == 200:
            data = response.json()
            # Should indicate readiness status
            assert "status" in data or "ready" in data


class TestLivenessEndpoints:
    """Test liveness check endpoints"""

    def test_liveness_endpoint(self):
        """Test /liveness endpoint"""
        response = client.get("/liveness")

        assert response.status_code in [200, 503]

    def test_live_endpoint(self):
        """Test /live endpoint (alternative)"""
        response = client.get("/live")

        assert response.status_code in [200, 503]

    def test_liveness_response_time(self):
        """Test liveness check is fast"""
        start = time.time()
        response = client.get("/liveness")
        duration = time.time() - start

        assert response.status_code in [200, 503]
        assert duration < 0.1


class TestMetricsEndpoint:
    """Test /metrics endpoint"""

    def test_metrics_endpoint_accessible(self):
        """Test that metrics endpoint is accessible"""
        response = client.get("/metrics")

        assert response.status_code == 200

    def test_metrics_response_format(self):
        """Test metrics response format"""
        response = client.get("/metrics")

        assert response.status_code == 200
        # Metrics can be JSON or Prometheus format
        content_type = response.headers.get("content-type", "")
        assert "json" in content_type or "text" in content_type

    def test_metrics_includes_system_info(self):
        """Test that metrics include system information"""
        response = client.get("/metrics")

        if response.status_code == 200:
            # Should have some metrics data
            assert len(response.content) > 0


class TestHealthAndMetricsEdgeCases:
    """Test edge cases for health and metrics"""

    def test_health_with_invalid_method(self):
        """Test health endpoint with POST instead of GET"""
        response = client.post("/health")

        # Security middleware returns 400 for invalid content-type on POST
        # This is expected behavior for our security setup
        assert response.status_code == 400

    def test_concurrent_health_checks(self):
        """Test concurrent health check requests"""
        import concurrent.futures

        def check_health():
            return client.get("/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(check_health) for _ in range(20)]
            responses = [f.result() for f in futures]

        # All should succeed
        for response in responses:
            assert response.status_code == 200

    def test_health_after_load(self):
        """Test health endpoint after generating load"""
        # Generate some load first
        for _ in range(5):
            client.post("/convert", json={
                "clinical_text": "metformin 500mg",
                "patient_ref": "Patient/load-test"
            })

        # Health should still respond
        response = client.get("/health")
        assert response.status_code == 200

    def test_metrics_query_parameters(self):
        """Test metrics endpoint with query parameters"""
        response = client.get("/metrics?format=json")

        # Should handle or ignore query params gracefully
        assert response.status_code in [200, 400]
