"""
NL-FHIR Health Check Endpoints
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required

Health Check Architecture:
- /health: Comprehensive health status with Prometheus integration
- /readiness | /ready: Service readiness for traffic (Kubernetes)
- /liveness | /live: Service liveness check (Kubernetes)
"""

from fastapi import APIRouter, Depends, Response, status

from ...monitoring.metrics import MetricsCollector
from ...services.monitoring import MonitoringService
from ..dependencies import get_monitoring_service

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    response: Response,
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Production health check endpoint

    Returns comprehensive system health status including:
    - Application status
    - HAPI FHIR connectivity
    - System resources (CPU, memory)
    - NLP model status

    Updates Prometheus health metrics for monitoring.
    """
    health_data = await monitoring_service.get_health()

    # Update Prometheus health metric
    # health_data is a HealthResponse Pydantic model, access via attributes
    is_healthy = health_data.status == "healthy"
    MetricsCollector.set_health_status(is_healthy)

    # Set HTTP status code based on health
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return health_data


@router.get("/readiness")
async def readiness_check(
    response: Response,
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Readiness probe endpoint (Kubernetes standard)

    Indicates whether the service is ready to receive traffic.
    Returns 200 if ready, 503 if not ready.

    Checks:
    - NLP models loaded
    - Database connectivity (if applicable)
    - External service availability
    """
    readiness_data = await monitoring_service.get_readiness()

    # Set HTTP status based on readiness
    is_ready = readiness_data.get("ready", False)
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return readiness_data


@router.get("/liveness")
async def liveness_check(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Liveness probe endpoint (Kubernetes standard)

    Indicates whether the service should be restarted.
    Returns 200 if alive, 503 if should be restarted.

    This is a lightweight check - only verifies the process is responsive.
    """
    return await monitoring_service.get_liveness()


@router.get("/ready")
async def readiness_probe(
    response: Response,
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Kubernetes/Railway readiness probe (alias for /readiness)

    Checks if service is ready to receive traffic.
    This is the preferred endpoint for container orchestrators.
    """
    readiness_data = await monitoring_service.get_readiness()

    is_ready = readiness_data.get("ready", False)
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return readiness_data


@router.get("/live")
async def liveness_probe(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Kubernetes/Railway liveness probe (alias for /liveness)

    Checks if service is alive and should not be restarted.
    This is the preferred endpoint for container orchestrators.
    """
    return await monitoring_service.get_liveness()
