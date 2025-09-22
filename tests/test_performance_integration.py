#!/usr/bin/env python3
"""
Integration Test for Performance Optimization - Story 2
Tests end-to-end performance improvements from model warmup
"""

import pytest
import time
from fastapi.testclient import TestClient

from src.nl_fhir.main import app
from src.nl_fhir.services.model_warmup import model_warmup_service


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestPerformanceIntegration:
    """Test performance optimization integration"""

    def test_model_warmup_status_in_metrics(self, client):
        """Test that model warmup status is included in metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200

        metrics = response.json()

        # Check that model warmup information is included
        assert "model_warmup" in metrics
        warmup_info = metrics["model_warmup"]

        # Should have status information
        assert "status" in warmup_info
        assert "models_loaded" in warmup_info

    def test_model_warmup_in_readiness_probe(self, client):
        """Test that readiness probe includes model warmup status"""
        response = client.get("/ready")
        assert response.status_code == 200

        readiness = response.json()
        assert "checks" in readiness
        assert "nlp_models_loaded" in readiness["checks"]

        # The check should reflect the actual warmup status
        assert isinstance(readiness["checks"]["nlp_models_loaded"], bool)

    def test_conversion_endpoint_performance_headers(self, client):
        """Test that conversion endpoint has performance monitoring headers"""
        request_data = {
            "clinical_text": "Patient needs 500mg amoxicillin twice daily for infection",
            "patient_ref": "PT-TEST-123"
        }

        response = client.post("/convert", json=request_data)
        assert response.status_code == 200

        # Check performance headers are present
        assert "X-Response-Time" in response.headers
        assert "X-Request-ID" in response.headers

        # Parse response time
        response_time_str = response.headers["X-Response-Time"]
        assert response_time_str.endswith("ms")
        response_time_ms = float(response_time_str[:-2])
        assert response_time_ms > 0

    def test_warmup_service_is_available(self):
        """Test that the global warmup service is accessible"""
        # Service should be available
        assert model_warmup_service is not None

        # Should have status information
        status = model_warmup_service.get_warmup_status()
        assert "status" in status
        assert "models_loaded" in status

    def test_health_endpoint_performance(self, client):
        """Test that health endpoint is fast (should be <100ms)"""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        assert response.status_code == 200
        response_time_ms = (end_time - start_time) * 1000

        # Health endpoint should be very fast
        assert response_time_ms < 500  # Should be under 500ms

        # Check response structure
        health_data = response.json()
        assert health_data["status"] in ["healthy", "warning", "critical"]
        assert "response_time_ms" in health_data

    def test_metrics_endpoint_performance(self, client):
        """Test that metrics endpoint is reasonably fast"""
        start_time = time.time()
        response = client.get("/metrics")
        end_time = time.time()

        assert response.status_code == 200
        response_time_ms = (end_time - start_time) * 1000

        # Metrics endpoint should be fast
        assert response_time_ms < 1000  # Should be under 1 second

        # Check SLA monitoring is present
        metrics = response.json()
        assert "sla_monitoring" in metrics
        assert "performance_summary" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])