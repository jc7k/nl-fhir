"""
NL-FHIR Pipeline Endpoints
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

import time
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...services.fhir.unified_pipeline import get_unified_fhir_pipeline
from ...services.fhir.quality_optimizer import get_quality_optimizer
from ...services.fhir.performance_manager import get_performance_manager
from ...services.fhir.failover_manager import get_failover_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fhir", tags=["FHIR Pipeline"])


# Request/Response models for FHIR pipeline
class UnifiedPipelineRequest(BaseModel):
    """Request model for unified FHIR pipeline processing"""

    nlp_entities: dict = Field(
        ..., description="Structured medical data from NLP processing"
    )
    validate_bundle: bool = Field(
        True, description="Whether to validate bundle with HAPI FHIR"
    )
    execute_bundle: bool = Field(
        False, description="Whether to execute bundle on HAPI FHIR server"
    )
    request_id: Optional[str] = Field(None, description="Optional request identifier")


class UnifiedPipelineResponse(BaseModel):
    """Response model for unified FHIR pipeline processing"""

    request_id: str
    success: bool
    processing_metadata: dict
    fhir_resources: list
    fhir_bundle: Optional[dict]
    validation_results: Optional[dict]
    execution_results: Optional[dict]
    quality_metrics: dict
    bundle_summary_data: dict
    errors: list
    warnings: list


@router.post("/pipeline", response_model=UnifiedPipelineResponse)
async def process_unified_fhir_pipeline(request: UnifiedPipelineRequest):
    """
    Story 3.4: Complete end-to-end FHIR pipeline processing

    Processes NLP entities through the complete FHIR pipeline:
    - Creates FHIR resources from structured medical data
    - Assembles transaction bundles with proper references
    - Validates bundles using HAPI FHIR with quality optimization
    - Optionally executes bundles on HAPI FHIR server
    - Returns comprehensive processing results for Epic 4 integration
    """

    start_time = time.time()

    try:
        # Get unified pipeline
        pipeline = await get_unified_fhir_pipeline()

        # Process through complete pipeline
        result = await pipeline.process_nlp_to_fhir(
            nlp_entities=request.nlp_entities,
            request_id=request.request_id,
            validate_bundle=request.validate_bundle,
            execute_bundle=request.execute_bundle,
        )

        processing_time = time.time() - start_time

        # Log performance
        logger.info(
            f"[{result.request_id}] Unified pipeline completed in {processing_time:.3f}s - Success: {result.success}"
        )

        # Convert to response model
        return UnifiedPipelineResponse(**result.to_dict())

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            f"Unified pipeline processing failed after {processing_time:.3f}s: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FHIR pipeline processing failed: {str(e)}",
        )


@router.get("/pipeline/status")
async def get_fhir_pipeline_status():
    """
    Story 3.4: Get comprehensive FHIR pipeline status and metrics

    Returns current status of the unified FHIR pipeline including:
    - Service initialization status
    - Performance metrics and targets
    - Quality metrics and validation success rates
    - Cache performance and optimization status
    """
    try:
        # Get pipeline status
        pipeline = await get_unified_fhir_pipeline()
        pipeline_status = pipeline.get_pipeline_status()

        # Get quality optimizer status
        quality_optimizer = get_quality_optimizer()
        quality_trends = quality_optimizer.get_quality_trends()

        # Get performance manager status
        performance_manager = get_performance_manager()
        performance_summary = performance_manager.get_performance_summary()
        real_time_metrics = performance_manager.get_real_time_metrics()

        return {
            "timestamp": datetime.now().isoformat(),
            "pipeline_status": pipeline_status,
            "quality_trends": quality_trends,
            "performance_summary": performance_summary,
            "real_time_metrics": real_time_metrics,
            "production_readiness": {
                "validation_target_met": quality_trends.get("target_met", False),
                "performance_target_met": performance_summary.get(
                    "overall_statistics", {}
                ).get("performance_target_met", False),
                "uptime_target_met": pipeline_status.get("pipeline_initialized", False),
                "epic4_ready": (
                    quality_trends.get("target_met", False)
                    and performance_summary.get("overall_statistics", {}).get(
                        "performance_target_met", False
                    )
                    and pipeline_status.get("pipeline_initialized", False)
                ),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve pipeline status",
        )


@router.post("/optimize")
async def optimize_fhir_bundle(bundle: dict):
    """
    Story 3.4: Optimize FHIR bundle for higher validation success

    Analyzes and optimizes FHIR bundles to improve validation success rates:
    - Identifies validation issues and improvement opportunities
    - Applies optimization rules for better FHIR compliance
    - Provides quality analysis and improvement suggestions
    """
    try:
        # Get quality optimizer
        quality_optimizer = get_quality_optimizer()

        # Optimize bundle for validation success
        optimized_bundle = quality_optimizer.optimize_bundle_for_validation(bundle)

        # Analyze bundle quality
        quality_analysis = {
            "original_bundle_quality": quality_optimizer._analyze_bundle_quality(
                bundle
            ),
            "optimized_bundle_quality": quality_optimizer._analyze_bundle_quality(
                optimized_bundle
            ),
            "optimization_summary": optimized_bundle.get("meta", {}).get(
                "optimization", {}
            ),
            "improvement_recommendations": quality_optimizer._generate_improvement_suggestions(
                {}, bundle
            ),
        }

        return {
            "optimized_bundle": optimized_bundle,
            "quality_analysis": quality_analysis,
            "validation_prediction": {
                "estimated_success_probability": min(
                    quality_analysis["optimized_bundle_quality"][
                        "bundle_structure_score"
                    ]
                    * 100,
                    95.0,
                ),
                "confidence": "high"
                if quality_analysis["optimized_bundle_quality"]["has_required_fields"]
                else "medium",
            },
        }

    except Exception as e:
        logger.error(f"Bundle optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bundle optimization failed: {str(e)}",
        )


@router.get("/quality/trends")
async def get_quality_trends():
    """
    Story 3.4: Get FHIR validation quality trends and analytics

    Returns comprehensive quality analytics including:
    - Validation success rate trends over time
    - Common error patterns and improvement opportunities
    - Quality score distributions and target achievement
    """
    try:
        quality_optimizer = get_quality_optimizer()
        trends = quality_optimizer.get_quality_trends()

        return {
            "timestamp": datetime.now().isoformat(),
            "quality_trends": trends,
            "recommendations": {
                "immediate_actions": [
                    "Focus on reducing most common error patterns",
                    "Implement pre-validation quality checks",
                    "Consider bundle optimization before validation",
                ]
                if trends.get("current_success_rate", 0) < 95
                else [
                    "Continue current quality practices",
                    "Monitor for quality regression",
                    "Prepare for Epic 4 integration",
                ],
                "long_term_goals": [
                    "Maintain ≥95% validation success rate",
                    "Reduce validation response times",
                    "Improve bundle quality scores",
                ],
            },
        }

    except Exception as e:
        logger.error(f"Failed to get quality trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve quality trends",
        )


@router.get("/performance/metrics")
async def get_performance_metrics():
    """
    Story 3.4: Get detailed FHIR pipeline performance metrics

    Returns comprehensive performance analytics including:
    - Operation-specific timing breakdowns
    - Cache performance and hit rates
    - Resource utilization and optimization recommendations
    """
    try:
        performance_manager = get_performance_manager()

        # Get comprehensive metrics
        performance_summary = performance_manager.get_performance_summary()
        real_time_metrics = performance_manager.get_real_time_metrics()

        # Auto-optimize if needed
        optimization_result = performance_manager.optimize_performance_settings()

        return {
            "timestamp": datetime.now().isoformat(),
            "performance_summary": performance_summary,
            "real_time_metrics": real_time_metrics,
            "auto_optimization": optimization_result,
            "performance_health": {
                "overall_status": "healthy"
                if performance_summary.get("overall_statistics", {}).get(
                    "performance_target_met", False
                )
                else "needs_attention",
                "cache_efficiency": "good"
                if performance_summary.get("cache_performance", {}).get(
                    "target_met", False
                )
                else "poor",
                "recommendation_priority": "high"
                if len(performance_summary.get("optimization_recommendations", [])) > 3
                else "low",
            },
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve performance metrics",
        )


@router.post("/performance/clear-cache")
async def clear_performance_cache():
    """
    Story 3.4: Clear FHIR pipeline caches for troubleshooting

    Clears all performance and validation caches to reset performance state.
    Useful for troubleshooting cache-related issues or starting fresh metrics collection.
    """
    try:
        performance_manager = get_performance_manager()
        cleared_counts = performance_manager.clear_caches()

        logger.info(f"Performance caches cleared: {cleared_counts}")

        return {
            "timestamp": datetime.now().isoformat(),
            "cache_clear_results": cleared_counts,
            "message": "All FHIR pipeline caches have been cleared",
            "next_steps": [
                "Performance metrics will reset",
                "Cache hit rates will rebuild over time",
                "Monitor performance for optimization opportunities",
            ],
        }

    except Exception as e:
        logger.error(f"Failed to clear caches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to clear performance caches",
        )


@router.get("/status")
async def get_hapi_status():
    """
    Story 3.3: Get HAPI FHIR endpoint status and failover information

    Returns current status of all configured HAPI FHIR endpoints including
    health status, performance metrics, and failover events.
    """
    try:
        # Get failover manager
        failover_manager = await get_failover_manager()

        # Get endpoint status
        endpoint_status = failover_manager.get_endpoint_status()
        failover_metrics = failover_manager.get_failover_metrics()

        # Get validation service metrics
        from ...services.fhir.validation_service import get_validation_service

        validation_service = await get_validation_service()
        validation_metrics = validation_service.get_validation_metrics()

        # Get execution service metrics
        from ...services.fhir.execution_service import get_execution_service

        execution_service = await get_execution_service()
        execution_metrics = execution_service.get_execution_metrics()

        return {
            "timestamp": datetime.now().isoformat(),
            "hapi_endpoints": endpoint_status,
            "failover_metrics": failover_metrics,
            "validation_metrics": validation_metrics,
            "execution_metrics": execution_metrics,
            "overall_status": {
                "primary_endpoint_healthy": failover_metrics["healthy_endpoints"] > 0,
                "failover_available": failover_metrics["total_endpoints"] > 1,
                "meets_availability_target": failover_metrics[
                    "meets_availability_target"
                ],
                "meets_validation_target": validation_metrics["meets_target"],
            },
        }

    except Exception as e:
        logger.error(f"HAPI status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve HAPI status",
        )
