"""
NL-FHIR Metrics Endpoints
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

from fastapi import APIRouter, Depends

from ..dependencies import get_monitoring_service
from ...services.monitoring import MonitoringService

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
async def get_metrics(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Application metrics endpoint
    Returns performance and usage statistics
    """
    return await monitoring_service.get_metrics()
