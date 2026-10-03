"""
/health HTTP status mapping: only "critical" returns 503.

A "warning" (e.g. CPU >= 80% while serving load) must keep returning 200,
otherwise a busy but working instance is pulled from the load balancer.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from src.nl_fhir.api.dependencies import get_monitoring_service
from src.nl_fhir.main import app
from src.nl_fhir.models.response import HealthResponse


class _StubMonitoringService:
    def __init__(self, health_status: str):
        self.health_status = health_status

    async def get_health(self) -> HealthResponse:
        return HealthResponse(
            status=self.health_status,
            service="nl-fhir-converter",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            response_time_ms=1.0,
            components={"cpu": self.health_status},
        )


@pytest.fixture
def client_with_health():
    def _client(health_status: str) -> TestClient:
        stub = _StubMonitoringService(health_status)
        app.dependency_overrides[get_monitoring_service] = lambda: stub
        return TestClient(app)

    yield _client
    app.dependency_overrides.pop(get_monitoring_service, None)


@pytest.mark.parametrize(
    ("health_status", "expected_code"),
    [("healthy", 200), ("warning", 200), ("critical", 503)],
)
def test_health_status_code(client_with_health, health_status, expected_code):
    response = client_with_health(health_status).get("/health")

    assert response.status_code == expected_code
    assert response.json()["status"] == health_status
