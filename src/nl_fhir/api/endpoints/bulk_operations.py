"""
NL-FHIR Bulk Operations Endpoints
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

import time
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends

from ..dependencies import get_conversion_service, get_monitoring_service
from ...models.request import BulkConversionRequest, ClinicalRequestAdvanced
from ...services.monitoring import MonitoringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Bulk Operations"])


@router.post("/bulk-convert")
async def bulk_convert(
    request: BulkConversionRequest,
    conversion_service=Depends(get_conversion_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Bulk clinical order conversion (Story 1.3 advanced feature)

    Process multiple clinical orders in a single batch operation.
    Maximum 50 orders per batch for performance optimization.

    - **orders**: List of clinical orders to process (max 50)
    - **batch_id**: Optional client-provided batch identifier
    - **processing_options**: Configuration options for processing

    Returns batch processing results with individual order outcomes.
    """
    batch_id = request.batch_id or f"batch_{str(uuid4())[:8]}"
    start_time = time.time()

    try:
        # Convert to advanced requests for processing
        advanced_requests = []
        for order in request.orders:
            advanced_request = ClinicalRequestAdvanced(
                clinical_text=order.clinical_text,
                patient_ref=order.patient_ref,
                priority="routine",  # Default for bulk processing
                context_metadata={"batch_id": batch_id, "batch_processing": True},
            )
            advanced_requests.append(advanced_request)

        # Process bulk conversion
        result = await conversion_service.bulk_convert(advanced_requests, batch_id)

        # Record batch metrics
        processing_time_ms = (time.time() - start_time) * 1000
        success_rate = result["successful_orders"] / result["total_orders"]
        monitoring_service.record_request(success_rate > 0.5, processing_time_ms)

        return result

    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)

        logger.error(
            f"Bulk conversion {batch_id}: Processing error - {type(e).__name__}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "batch_id": batch_id,
                "error": "Bulk processing failed",
                "message": "Unable to process batch request",
            },
        )
