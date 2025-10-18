"""
NL-FHIR Metrics Endpoints
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

from fastapi import APIRouter, Depends, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from ..dependencies import get_monitoring_service
from ...services.monitoring import MonitoringService
from ...monitoring.metrics import MetricsCollector

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
async def get_metrics_json(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Application metrics endpoint (JSON format)
    Returns performance and usage statistics
    """
    return await monitoring_service.get_metrics()


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """
    Prometheus metrics endpoint
    Returns metrics in Prometheus exposition format

    This endpoint is scraped by Prometheus for monitoring.
    Metrics include:
    - HTTP request counts and latencies
    - FHIR conversion and validation metrics
    - System resource usage
    - Application health status
    """
    # Update system metrics before returning
    MetricsCollector.update_system_metrics()

    # Generate Prometheus format
    metrics_output = generate_latest()
    return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)
