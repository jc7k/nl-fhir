"""
/metrics/prometheus must not block on CPU sampling.

psutil.cpu_percent(interval=X) with X > 0 sleeps for X seconds, stalling the
event loop (and every other in-flight request) on each Prometheus scrape.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.nl_fhir.main import app


def _assert_non_blocking(mock_cpu_percent):
    assert mock_cpu_percent.called
    for call in mock_cpu_percent.call_args_list:
        interval = call.kwargs.get("interval", call.args[0] if call.args else None)
        assert not interval, f"blocking cpu_percent(interval={interval!r})"


def test_update_system_metrics_samples_cpu_without_blocking():
    from src.nl_fhir.monitoring.metrics import MetricsCollector

    with patch(
        "src.nl_fhir.monitoring.metrics.psutil.cpu_percent", return_value=42.0
    ) as mock_cpu_percent:
        MetricsCollector.update_system_metrics()

    _assert_non_blocking(mock_cpu_percent)


def test_prometheus_endpoint_samples_cpu_without_blocking():
    with patch(
        "src.nl_fhir.monitoring.metrics.psutil.cpu_percent", return_value=42.0
    ) as mock_cpu_percent:
        response = TestClient(app).get("/metrics/prometheus")

    assert response.status_code == 200
    assert "nl_fhir_system_cpu_usage_percent 42.0" in response.text
    _assert_non_blocking(mock_cpu_percent)
