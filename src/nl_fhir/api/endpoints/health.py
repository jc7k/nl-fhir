"""
NL-FHIR Health Check Endpoints
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

from fastapi import APIRouter, Depends

from ..dependencies import get_monitoring_service
from ...services.monitoring import MonitoringService

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Production health check endpoint
    Returns comprehensive system health status
    """
    return await monitoring_service.get_health()


@router.get("/readiness")
async def readiness_check(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Readiness probe endpoint
    Indicates whether the service is ready to receive traffic.
    """
    return await monitoring_service.get_readiness()


@router.get("/liveness")
async def liveness_check(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Liveness probe endpoint
    Indicates whether the service should be restarted.
    """
    return await monitoring_service.get_liveness()


@router.get("/ready")
async def readiness_probe(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Kubernetes/Railway readiness probe
    Checks if service is ready to receive traffic
    """
    return await monitoring_service.get_readiness()


@router.get("/live")
async def liveness_probe(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Kubernetes/Railway liveness probe
    Checks if service is alive and should not be restarted
    """
    return await monitoring_service.get_liveness()
