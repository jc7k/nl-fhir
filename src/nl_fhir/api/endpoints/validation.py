"""
NL-FHIR Validation Endpoints
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

import time
import logging
from datetime import datetime
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator

from ..dependencies import get_monitoring_service
from ...services.monitoring import MonitoringService
from ...services.fhir.validation_service import get_validation_service
from ...services.fhir.execution_service import get_execution_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Validation"])


# Validation request/response models
class ValidateBundleRequest(BaseModel):
    """Request model for FHIR bundle validation"""

    bundle: dict = Field(..., description="FHIR Bundle resource to validate")
    use_cache: bool = Field(
        True, description="Whether to use cached validation results"
    )

    @field_validator("bundle")
    @classmethod
    def validate_bundle(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Bundle must be a JSON object")

        if v.get("resourceType") != "Bundle":
            raise ValueError("Resource must be a FHIR Bundle")

        return v


class ValidateBundleResponse(BaseModel):
    """Response model for bundle validation"""

    request_id: str
    validation_result: str  # success, warning, error
    is_valid: bool
    issues: dict
    user_messages: dict
    recommendations: list
    bundle_quality_score: float
    validation_source: str
    validation_time: str
    timestamp: datetime


class ExecuteBundleRequest(BaseModel):
    """Request model for FHIR bundle execution"""

    bundle: dict = Field(..., description="FHIR Bundle resource to execute")
    validate_first: bool = Field(
        True, description="Whether to validate bundle before execution"
    )
    force_execution: bool = Field(
        False, description="Execute even if validation warnings exist"
    )

    @field_validator("bundle")
    @classmethod
    def validate_bundle(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Bundle must be a JSON object")

        if v.get("resourceType") != "Bundle":
            raise ValueError("Resource must be a FHIR Bundle")

        if v.get("type") != "transaction":
            raise ValueError("Bundle must be a transaction bundle for execution")

        return v


class ExecuteBundleResponse(BaseModel):
    """Response model for bundle execution"""

    request_id: str
    execution_result: str  # success, partial, failure
    success: bool
    total_resources: int
    successful_resources: int
    failed_resources: int
    created_resources: list
    execution_summary: dict
    rollback_info: Optional[dict]
    execution_source: str
    transaction_id: Optional[str]
    execution_time: str
    timestamp: datetime


@router.post("/validate", response_model=ValidateBundleResponse)
async def validate_fhir_bundle(
    request: ValidateBundleRequest,
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Story 3.3: Validate FHIR bundle using HAPI FHIR server

    Validates FHIR R4 transaction bundles against FHIR specifications using
    HAPI FHIR server with automatic failover to local validation.

    - **bundle**: FHIR Bundle resource to validate (required)
    - **use_cache**: Whether to use cached validation results (default: true)

    Returns comprehensive validation results with user-friendly error messages
    and actionable recommendations for bundle improvement.
    """
    request_id = str(uuid4())
    start_time = time.time()

    try:
        # Get validation service
        validation_service = await get_validation_service()

        # Validate bundle using HAPI FHIR
        validation_result = await validation_service.validate_bundle(
            request.bundle, request_id=request_id, use_cache=request.use_cache
        )

        # Create response
        response = ValidateBundleResponse(
            request_id=request_id,
            validation_result=validation_result["validation_result"],
            is_valid=validation_result["is_valid"],
            issues=validation_result["issues"],
            user_messages=validation_result["user_messages"],
            recommendations=validation_result["recommendations"],
            bundle_quality_score=validation_result["bundle_quality_score"],
            validation_source=validation_result["validation_source"],
            validation_time=validation_result.get("validation_time", "N/A"),
            timestamp=datetime.now(),
        )

        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(
            validation_result["is_valid"], processing_time_ms
        )

        logger.info(
            f"[{request_id}] Bundle validation completed - "
            f"Result: {response.validation_result} - "
            f"Quality: {response.bundle_quality_score}"
        )

        return response

    except ValueError as ve:
        # Validation errors (client-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)

        logger.warning(f"Request {request_id}: Bundle validation error")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid bundle: {str(ve)}",
        )

    except Exception as e:
        # System errors (server-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)

        logger.error(
            f"Request {request_id}: Bundle validation system error - {type(e).__name__}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation service error. Please try again.",
        )


@router.post("/execute", response_model=ExecuteBundleResponse)
async def execute_fhir_bundle(
    request: ExecuteBundleRequest,
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
):
    """
    Story 3.3: Execute FHIR transaction bundle on HAPI FHIR server

    Submits validated FHIR R4 transaction bundles to HAPI FHIR server for
    execution with optional pre-execution validation and audit logging.

    - **bundle**: FHIR transaction Bundle resource to execute (required)
    - **validate_first**: Whether to validate bundle before execution (default: true)
    - **force_execution**: Execute even if validation warnings exist (default: false)

    Returns execution results with transaction tracking, resource creation details,
    and rollback information for failed/partial executions.
    """
    request_id = str(uuid4())
    start_time = time.time()

    try:
        # Get execution service
        execution_service = await get_execution_service()

        # Execute bundle on HAPI FHIR server
        execution_result = await execution_service.execute_bundle(
            request.bundle,
            request_id=request_id,
            validate_first=request.validate_first,
            force_execution=request.force_execution,
        )

        # Create response
        response = ExecuteBundleResponse(
            request_id=request_id,
            execution_result=execution_result["execution_result"],
            success=execution_result["success"],
            total_resources=execution_result["total_resources"],
            successful_resources=execution_result["successful_resources"],
            failed_resources=execution_result["failed_resources"],
            created_resources=execution_result["created_resources"],
            execution_summary=execution_result["execution_summary"],
            rollback_info=execution_result.get("rollback_info"),
            execution_source=execution_result["execution_source"],
            transaction_id=execution_result.get("transaction_id"),
            execution_time=execution_result.get("execution_time", "N/A"),
            timestamp=datetime.now(),
        )

        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(
            execution_result["success"], processing_time_ms
        )

        logger.info(
            f"[{request_id}] Bundle execution completed - "
            f"Result: {response.execution_result} - "
            f"Resources: {response.successful_resources}/{response.total_resources}"
        )

        return response

    except ValueError as ve:
        # Validation errors (client-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)

        logger.warning(f"Request {request_id}: Bundle execution validation error")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid bundle for execution: {str(ve)}",
        )

    except Exception as e:
        # System errors (server-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)

        logger.error(
            f"Request {request_id}: Bundle execution system error - {type(e).__name__}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Execution service error. Please try again.",
        )
