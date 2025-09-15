"""
NL-FHIR Conversion Endpoints
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

import time
import logging
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends

from ..dependencies import get_conversion_service, get_monitoring_service
from ...models.request import ClinicalRequest, ClinicalRequestAdvanced
from ...models.response import ConvertResponse, ConvertResponseAdvanced, ErrorResponse
from ...services.monitoring import MonitoringService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Conversion"])


@router.post("/convert", response_model=ConvertResponse)
async def convert_to_fhir(
    request: ClinicalRequest,
    conversion_service=Depends(get_conversion_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Clinical order conversion with full Epic 2 NLP processing

    Converts natural language clinical orders using advanced NLP processing
    and FHIR resource generation. Now includes full Epic 2-3 integration.

    - **clinical_text**: Free-text clinical order (required)
    - **patient_ref**: Optional patient reference identifier

    Returns conversion response with FHIR bundle and processing results.
    """
    request_id = str(uuid4())
    start_time = time.time()

    try:
        # Convert basic request to advanced request for full processing
        advanced_request = ClinicalRequestAdvanced(
            clinical_text=request.clinical_text,
            patient_ref=request.patient_ref,
            priority="routine",  # Default priority
            ordering_provider="web-interface",
            department="general",
            context_metadata={"source": "web_form", "ui_version": "1.0"},
        )

        # Use advanced conversion service with full Epic 2-3 processing
        full_response = await conversion_service.convert_advanced(
            advanced_request, request_id
        )

        # Debug: Check if FHIR bundle exists
        logger.info(
            f"Request {request_id}: FHIR bundle exists: {full_response.fhir_bundle is not None}"
        )
        if full_response.fhir_bundle:
            logger.info(
                f"Request {request_id}: FHIR bundle entries: {len(full_response.fhir_bundle.get('entry', []))}"
            )
            logger.info(
                f"Request {request_id}: FHIR bundle type: {type(full_response.fhir_bundle)}"
            )

        # Prepare full FHIR bundle for UI display with datetime serialization
        fhir_bundle_dict = None
        if full_response.fhir_bundle:
            try:
                from datetime import datetime

                def convert_datetimes(obj):
                    """Recursively convert datetime objects to ISO strings for JSON serialization"""
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    elif isinstance(obj, dict):
                        return {k: convert_datetimes(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_datetimes(item) for item in obj]
                    else:
                        return obj

                # Convert the full bundle with datetime handling
                fhir_bundle_dict = convert_datetimes(full_response.fhir_bundle)
                logger.info(
                    f"Request {request_id}: Full FHIR bundle serialized for UI display"
                )

            except Exception as e:
                logger.warning(
                    f"Request {request_id}: Failed to serialize FHIR bundle: {e}"
                )
                # Fallback to basic info
                bundle = full_response.fhir_bundle
                fhir_bundle_dict = {
                    "id": bundle.get("id"),
                    "type": bundle.get("type", "transaction"),
                    "resource_count": len(bundle.get("entry", [])),
                    "error": f"Full bundle serialization failed: {str(e)}",
                }

        # Convert advanced response back to basic response format with FHIR bundle for visual validation
        response = ConvertResponse(
            request_id=full_response.request_id,
            status=full_response.status.value
            if hasattr(full_response.status, "value")
            else str(full_response.status),
            message=f"Clinical order processed successfully with full FHIR conversion. "
            f"Generated {len(full_response.fhir_bundle.get('entry', [])) if full_response.fhir_bundle else 0} FHIR resources. "
            f"Bundle validation: {'PASSED' if full_response.fhir_validation_results and full_response.fhir_validation_results.get('is_valid') else 'PENDING'}",
            timestamp=full_response.metadata.server_timestamp,
            fhir_bundle=fhir_bundle_dict,  # Include serialized FHIR bundle for user visibility
            bundle_summary=full_response.bundle_summary,  # Include bundle summary (Epic 4)
        )

        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(True, processing_time_ms)

        logger.info(
            f"Request {request_id}: Full Epic 2-3 conversion completed - "
            f"FHIR resources: {len(full_response.fhir_bundle.get('entry', [])) if full_response.fhir_bundle else 0}, "
            f"Valid: {full_response.fhir_validation_results.get('is_valid', False) if full_response.fhir_validation_results else False}"
        )

        # Debug: Check if response has FHIR bundle
        logger.info(
            f"Request {request_id}: Response fhir_bundle is None: {response.fhir_bundle is None}"
        )

        return response

    except ValueError as ve:
        # Validation errors (client-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)

        logger.warning(
            f"Request {request_id}: Validation error after {processing_time_ms:.2f}ms"
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid input: {str(ve)}",
        )

    except Exception as e:
        # System errors (server-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)

        logger.error(
            f"Request {request_id}: System error after {processing_time_ms:.2f}ms - {type(e).__name__}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Processing failed. Please try again.",
        )


@router.post("/api/v1/convert", response_model=ConvertResponseAdvanced)
async def convert_advanced(
    request: ClinicalRequestAdvanced,
    conversion_service=Depends(get_conversion_service),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Advanced clinical order conversion (Story 1.2 implementation)

    Converts natural language clinical orders with comprehensive validation,
    Epic integration placeholders, and detailed response metadata.

    - **clinical_text**: Free-text clinical order (required)
    - **patient_ref**: Optional patient reference identifier
    - **priority**: Order priority (routine, urgent, stat, asap)
    - **ordering_provider**: Provider identifier
    - **department**: Ordering department
    - **context_metadata**: Additional context for processing

    Returns detailed conversion response with validation results and Epic placeholders.
    """
    request_id = str(uuid4())
    start_time = time.time()

    try:
        # Use advanced conversion service
        response = await conversion_service.convert_advanced(request, request_id)

        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(True, processing_time_ms)

        return response

    except ValueError as ve:
        # Validation errors
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)

        error_response = ErrorResponse(
            request_id=request_id,
            error_code="VALIDATION_ERROR",
            error_type="client_error",
            message=str(ve),
            timestamp=datetime.now(),
            suggestions=["Check clinical text format", "Verify required fields"],
        )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response.dict(),
        )

    except Exception as e:
        # System errors
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)

        error_response = ErrorResponse(
            request_id=request_id,
            error_code="PROCESSING_ERROR",
            error_type="server_error",
            message="Internal processing error occurred",
            timestamp=datetime.now(),
            suggestions=["Try again later", "Contact support if problem persists"],
        )

        logger.error(
            f"Request {request_id}: Advanced conversion error - {type(e).__name__}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict(),
        )
