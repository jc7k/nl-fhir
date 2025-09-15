"""
NL-FHIR Summarization Endpoints
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

import time
import logging
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends

from ..dependencies import (
    get_epic4_summarization_service,
    get_safety_validator_dep,
    get_hybrid_summarizer_dep,
    get_monitoring_service,
)
from ...models.request import SummarizeBundleRequest
from ...models.response import SummarizeBundleResponse, ProcessingStatus
from ...services.epic4_summarization_adapter import Epic4SummarizationAdapter
from ...services.safety_validator import SafetyValidator
from ...services.hybrid_summarizer import HybridSummarizer
from ...services.monitoring import MonitoringService
from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Summarization"])


@router.post("/summarize-bundle", response_model=SummarizeBundleResponse)
async def summarize_bundle(
    request: SummarizeBundleRequest,
    epic4_service: Epic4SummarizationAdapter = Depends(get_epic4_summarization_service),
    safety_validator: SafetyValidator = Depends(get_safety_validator_dep),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Story 4.1: Generate plain-English summary of a validated FHIR Bundle.
    Feature-gated via SUMMARIZATION_ENABLED flag. Optionally attaches safety checks
    when SAFETY_VALIDATION_ENABLED is true (Story 4.2).
    """
    if not settings.summarization_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bundle summarization disabled",
        )

    req_id = str(uuid4())
    start = time.time()
    try:
        # Use Epic 4 adaptive architecture for enhanced summarization
        result = await epic4_service.async_summarize(
            bundle=request.bundle,
            role=request.user_role or "clinician",
            context=request.context,
        )

        safety = None
        if settings.safety_validation_enabled:
            safety = safety_validator.evaluate(request.bundle)

        response = SummarizeBundleResponse(
            request_id=req_id,
            status=ProcessingStatus.COMPLETED,
            timestamp=datetime.now(),
            human_readable_summary=result["human_readable_summary"],
            bundle_summary=result["bundle_summary"],
            confidence_indicators=result["confidence_indicators"],
            safety_checks=safety,
        )

        # Record as successful request
        processing_time_ms = (time.time() - start) * 1000
        monitoring_service.record_request(True, processing_time_ms)
        return response

    except Exception as e:
        processing_time_ms = (time.time() - start) * 1000
        monitoring_service.record_request(False, processing_time_ms)
        logger.error(f"Summarization error for request {req_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to summarize bundle"
        )


@router.post("/summarize-bundle-enhanced")
async def summarize_bundle_enhanced(
    request: SummarizeBundleRequest,
    hybrid_summarizer: HybridSummarizer = Depends(get_hybrid_summarizer_dep),
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Stories 4.3 & 4.4: Enhanced bundle summarization with optional LLM enhancement
    and integrated safety validation. Returns comprehensive summary with all Epic 4 features.
    """
    if not settings.summarization_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bundle summarization disabled",
        )

    req_id = str(uuid4())
    start = time.time()

    try:
        # Prepare options for hybrid summarizer
        options = {
            "role": request.user_role or "clinician",
            "context": request.context,
            "llm_enhancement": request.llm_enhancement or False,
            "enhancement_level": request.enhancement_level or "contextual",
        }

        # Use hybrid summarizer for comprehensive results
        result = await hybrid_summarizer.create_comprehensive_summary(
            request.bundle, options
        )

        # Create response using enhanced data
        response = {
            "request_id": req_id,
            "status": "completed",
            "timestamp": datetime.now(),
            "enhanced_summary": result["summary"],
            "summary_type": result["summary_type"],
            "bundle_stats": result["bundle_stats"],
            "confidence": result["confidence"],
            "safety_analysis": result["safety"],
            "processing_details": result["processing"],
            "enhancement_details": result.get("enhancement_details"),
        }

        # Record as successful request
        processing_time_ms = (time.time() - start) * 1000
        monitoring_service.record_request(True, processing_time_ms)
        return response

    except Exception as e:
        processing_time_ms = (time.time() - start) * 1000
        monitoring_service.record_request(False, processing_time_ms)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create enhanced summary: {str(e)}",
        )
