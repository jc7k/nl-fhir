"""
Response Models for NL-FHIR Converter
HIPAA Compliant: No PHI in response structures
Medical Safety: Structured response validation
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    """Status values for conversion processing"""
    RECEIVED = "received"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class ValidationResult(BaseModel):
    """Validation results for clinical input"""
    is_valid: bool = Field(..., description="Overall validation status")
    validation_score: Optional[float] = Field(
        None, 
        description="Validation confidence score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-critical validation warnings"
    )
    errors: List[str] = Field(
        default_factory=list, 
        description="Critical validation errors"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for input improvement"
    )


class ProcessingMetadata(BaseModel):
    """Metadata about the processing operation"""
    request_id: str = Field(..., description="Unique request identifier")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    server_timestamp: datetime = Field(..., description="Server processing timestamp")
    version: str = Field(default="1.0.0", description="API version used")
    model_version: Optional[str] = Field(None, description="NLP model version (Future Epic 2)")
    
    # Performance metrics
    input_length: int = Field(..., description="Input text character count")
    complexity_score: Optional[float] = Field(
        None,
        description="Input complexity assessment (Future)",
        ge=0.0,
        le=10.0
    )


class ConvertResponse(BaseModel):
    """Basic response model for convert endpoint"""
    model_config = {"use_enum_values": True}
    
    request_id: str = Field(..., description="Unique request identifier")
    status: ProcessingStatus = Field(..., description="Processing status")
    message: str = Field(..., description="Human-readable status message")
    timestamp: datetime = Field(..., description="Response timestamp")
    fhir_bundle: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Generated FHIR R4 bundle for visual validation"
    )
    bundle_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Bundle composition summary (Epic 4)"
    )


class ConvertResponseAdvanced(BaseModel):
    """Advanced response model with full Epic integration placeholders"""
    model_config = {"use_enum_values": True}

    # Core response fields
    request_id: str = Field(..., description="Unique request identifier") 
    status: ProcessingStatus = Field(..., description="Processing status")
    message: str = Field(..., description="Human-readable status message")
    
    # Processing metadata
    metadata: ProcessingMetadata = Field(..., description="Processing metadata")
    
    # Validation results
    validation: ValidationResult = Field(..., description="Input validation results")
    
    # Epic 2 - NLP Pipeline Integration (Placeholders)
    extracted_entities: Optional[Dict[str, Any]] = Field(
        None,
        description="Extracted clinical entities (Epic 2: spaCy/medspaCy output)"
    )
    structured_output: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured clinical data (Epic 2: PydanticAI output)"
    )
    terminology_mappings: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Medical terminology codes (Epic 2: RxNorm, LOINC, ICD-10)"
    )
    
    # Epic 3 - FHIR Bundle Assembly (Placeholders)
    fhir_bundle: Optional[Dict[str, Any]] = Field(
        None,
        description="Generated FHIR R4 bundle (Epic 3 output)"
    )
    fhir_validation_results: Optional[Dict[str, Any]] = Field(
        None,
        description="HAPI FHIR validation results (Epic 3)"
    )
    bundle_summary: Optional[Dict[str, Any]] = Field(
        None,
        description="Bundle composition summary (Epic 4)"
    )
    
    # Epic 4 - Reverse Validation (Placeholders)
    safety_checks: Optional[Dict[str, Any]] = Field(
        None,
        description="Clinical safety validation results (Epic 4)"
    )
    human_readable_summary: Optional[str] = Field(
        None,
        description="Human-readable bundle summary (Epic 4)"
    )


class ErrorResponse(BaseModel):
    """Standardized error response model"""
    request_id: str = Field(..., description="Request identifier for error correlation")
    error_code: str = Field(..., description="Machine-readable error code")
    error_type: str = Field(..., description="Error category")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    timestamp: datetime = Field(..., description="Error timestamp")
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for resolving the error"
    )


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    response_time_ms: float = Field(..., description="Health check response time")
    
    # Component health details
    components: Optional[Dict[str, str]] = Field(
        None,
        description="Individual component health status"
    )
    dependencies: Optional[Dict[str, str]] = Field(
        None,
        description="External dependency status (Future: HAPI FHIR, etc.)"
    )


class MetricsResponse(BaseModel):
    """Metrics endpoint response model"""
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    total_requests: int = Field(..., description="Total requests processed")
    successful_requests: int = Field(..., description="Successful requests")
    failed_requests: int = Field(..., description="Failed requests")
    average_response_time_ms: float = Field(..., description="Average response time")
    current_load: float = Field(..., description="Current load percentage")
    memory_usage_mb: Optional[float] = Field(None, description="Memory usage in MB")


class BulkConversionResponse(BaseModel):
    """Response model for bulk conversion operations"""
    batch_id: str = Field(..., description="Batch processing identifier")
    total_orders: int = Field(..., description="Total orders in batch")
    successful_orders: int = Field(..., description="Successfully processed orders")
    failed_orders: int = Field(..., description="Failed order count")
    processing_time_ms: float = Field(..., description="Total batch processing time")
    
    # Individual order results
    results: List[Union[ConvertResponseAdvanced, ErrorResponse]] = Field(
        ...,
        description="Individual order processing results"
    )
    
    # Batch summary
    batch_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Batch processing summary and statistics"
    )


class SummarizeBundleResponse(BaseModel):
    """Response model for bundle summarization (Epic 4)"""
    model_config = {"use_enum_values": True}

    request_id: str = Field(..., description="Unique request identifier")
    status: ProcessingStatus = Field(..., description="Processing status")
    timestamp: datetime = Field(..., description="Response timestamp")
    
    # Summary outputs
    human_readable_summary: str = Field(..., description="Plain-English summary of bundle")
    bundle_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Bundle composition statistics and details"
    )
    confidence_indicators: Dict[str, Any] = Field(
        default_factory=dict,
        description="Confidence and quality indicators"
    )
    
    # Optional safety evaluation
    safety_checks: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Clinical safety validation results if enabled"
    )
