"""
NL-FHIR Component: Main FastAPI application
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

from typing import Optional
import logging
import logging.config
import importlib
import re
import time
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, field_validator

# Import new models and services
from .models.request import ClinicalRequest, ClinicalRequestAdvanced, BulkConversionRequest
from .models.request import SummarizeBundleRequest
from .models.response import ConvertResponse, ConvertResponseAdvanced, ErrorResponse
from .models.response import SummarizeBundleResponse, ProcessingStatus
from .services.monitoring import MonitoringService 
from .services.validation import ValidationService
from .services.summarization_old import SummarizationService  # Legacy service
from .services.epic4_summarization_adapter import Epic4SummarizationAdapter
from .services.safety_validator import SafetyValidator
from .services.hybrid_summarizer import HybridSummarizer
from .config import settings

# Story 3.3: Import HAPI FHIR services
from .services.fhir.validation_service import get_validation_service
from .services.fhir.execution_service import get_execution_service
from .services.fhir.failover_manager import get_failover_manager

# Story 3.4: Import production FHIR services
from .services.fhir.unified_pipeline import get_unified_fhir_pipeline, FHIRProcessingResult
from .services.fhir.quality_optimizer import get_quality_optimizer
from .services.fhir.performance_manager import get_performance_manager

# Enhanced logger configuration with structured logging (no PHI)
try:
    logging.config.dictConfig(settings.get_log_config())
except Exception:
    # Fallback to basic config if dictConfig fails for any reason
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s'
    )
logger = logging.getLogger(__name__)

# Security and performance metrics
REQUEST_TIMEOUT_SECONDS = 30.0
MAX_REQUEST_SIZE_BYTES = 1024 * 1024  # 1MB
RATE_LIMIT_REQUESTS = 100  # per minute

# FastAPI application with enhanced metadata for Story 1.2
app = FastAPI(
    title="NL-FHIR Converter",
    description="Natural Language to FHIR R4 Bundle Converter - Epic 1 Complete",
    version="1.0.0",
    docs_url="/docs",  # OpenAPI documentation
    redoc_url="/redoc",  # Alternative documentation
    contact={
        "name": "NL-FHIR Development Team",
        "email": "dev@nl-fhir.example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Initialize services
monitoring_service = MonitoringService() 
validation_service = ValidationService()
summarization_service = SummarizationService()  # Legacy service for compatibility
epic4_summarization_service = Epic4SummarizationAdapter()  # New Epic 4 adaptive architecture
safety_validator = SafetyValidator()
hybrid_summarizer = HybridSummarizer()

# Lazy loader for ConversionService to avoid importing NLP stack at startup
_conversion_service = None

def get_conversion_service():
    global _conversion_service
    if _conversion_service is None:
        module = importlib.import_module("src.nl_fhir.services.conversion")
        _conversion_service = module.ConversionService()
    return _conversion_service

# Security middleware - trusted host protection
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.railway.app", "testserver"]  # testserver for tests
)

# CORS configuration - restricted for production security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://*.railway.app",  # Production deployment
    ],
    allow_credentials=False,  # Security: disable credentials
    allow_methods=["GET", "POST"],  # Restrict to required methods
    allow_headers=["content-type"],  # Restrict headers
)

# Request timing and size validation middleware
@app.middleware("http")
async def request_timing_and_validation(request: Request, call_next):
    """Request timing, size validation, and security monitoring"""
    start_time = time.time()
    request_id = str(uuid4())[:8]  # Short request ID for logging (no PHI)
    
    try:
        # Check request size for security
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE_BYTES:
            logger.warning(f"Request {request_id}: Payload too large ({content_length} bytes)")
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": "Request payload too large", "request_id": request_id}
            )
        
        # Process request with timeout monitoring
        response = await call_next(request)
        
        # Log performance metrics (no PHI)
        processing_time = time.time() - start_time
        logger.info(f"Request {request_id}: {request.method} {request.url.path} - "
                   f"{response.status_code} - {processing_time:.3f}s")
        
        # Alert on slow requests
        if processing_time > REQUEST_TIMEOUT_SECONDS:
            logger.warning(f"Request {request_id}: Slow response ({processing_time:.3f}s)")
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Request {request_id}: Error after {processing_time:.3f}s - {type(e).__name__}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "request_id": request_id}
        )

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def sanitize_clinical_text(text: str) -> str:
    """
    Sanitize clinical text input for security and safety
    Removes potentially harmful characters while preserving medical content
    """
    if not text:
        return text
    
    # Remove potentially harmful HTML/script content
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove control characters except newlines, tabs, and carriage returns  
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Limit excessive whitespace
    text = re.sub(r'\s{4,}', '   ', text)  # Max 3 consecutive spaces
    text = re.sub(r'\n{4,}', '\n\n\n', text)  # Max 3 consecutive newlines
    
    return text


class ClinicalRequest(BaseModel):
    """HIPAA-compliant clinical request model"""
    clinical_text: str = Field(
        ..., 
        description="Free-text clinical order",
        max_length=5000  # Security: limit input size
    )
    patient_ref: Optional[str] = Field(
        None, 
        description="Patient reference ID",
        max_length=100,  # Security: limit patient ref size
        pattern=r'^[A-Za-z0-9\-_/]*$'  # Security: alphanumeric + dash/underscore/slash for FHIR references
    )
    
    @field_validator('clinical_text')
    @classmethod
    def validate_clinical_text(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("Clinical text must be at least 5 characters")
        
        # Sanitize input for security
        sanitized = sanitize_clinical_text(v.strip())
        
        if len(sanitized) < 5:
            raise ValueError("Clinical text too short after sanitization")
        
        return sanitized
    
    @field_validator('patient_ref')
    @classmethod
    def validate_patient_ref(cls, v):
        if v is None:
            return v
        
        # Sanitize patient reference
        sanitized = v.strip()
        if not sanitized:
            return None
            
        # Validate pattern (already enforced by Field pattern, but double-check)
        if not re.match(r'^[A-Za-z0-9\-_/]+$', sanitized):
            raise ValueError("Patient reference contains invalid characters")
            
        return sanitized


# Story 3.3: HAPI FHIR validation and execution models
class ValidateBundleRequest(BaseModel):
    """Request model for FHIR bundle validation"""
    bundle: dict = Field(..., description="FHIR Bundle resource to validate")
    use_cache: bool = Field(True, description="Whether to use cached validation results")
    
    @field_validator('bundle')
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
    validate_first: bool = Field(True, description="Whether to validate bundle before execution")
    force_execution: bool = Field(False, description="Execute even if validation warnings exist")
    
    @field_validator('bundle')
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


@app.get("/", response_class=HTMLResponse)
async def serve_form(request: Request):
    """Serve the main web form interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """
    Production health check endpoint
    Returns comprehensive system health status
    """
    return await monitoring_service.get_health()

@app.get("/readiness")
async def readiness_check():
    """
    Readiness probe endpoint
    Indicates whether the service is ready to receive traffic.
    """
    return await monitoring_service.get_readiness()

@app.get("/liveness")
async def liveness_check():
    """
    Liveness probe endpoint
    Indicates whether the service should be restarted.
    """
    return await monitoring_service.get_liveness()

@app.get("/metrics")
async def get_metrics():
    """
    Application metrics endpoint
    Returns performance and usage statistics
    """
    return await monitoring_service.get_metrics()

@app.get("/ready")
async def readiness_probe():
    """
    Kubernetes/Railway readiness probe
    Checks if service is ready to receive traffic
    """
    return await monitoring_service.get_readiness()

@app.get("/live")
async def liveness_probe():
    """
    Kubernetes/Railway liveness probe  
    Checks if service is alive and should not be restarted
    """
    return await monitoring_service.get_liveness()


@app.post("/convert", response_model=ConvertResponse)
async def convert_to_fhir(request: ClinicalRequest):
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
            context_metadata={"source": "web_form", "ui_version": "1.0"}
        )
        
        # Use advanced conversion service with full Epic 2-3 processing
        full_response = await get_conversion_service().convert_advanced(advanced_request, request_id)
        
        # Debug: Check if FHIR bundle exists
        logger.info(f"Request {request_id}: FHIR bundle exists: {full_response.fhir_bundle is not None}")
        if full_response.fhir_bundle:
            logger.info(f"Request {request_id}: FHIR bundle entries: {len(full_response.fhir_bundle.get('entry', []))}")
            logger.info(f"Request {request_id}: FHIR bundle type: {type(full_response.fhir_bundle)}")
        
        # Prepare full FHIR bundle for UI display with datetime serialization
        fhir_bundle_dict = None
        if full_response.fhir_bundle:
            try:
                import json
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
                logger.info(f"Request {request_id}: Full FHIR bundle serialized for UI display")
                
            except Exception as e:
                logger.warning(f"Request {request_id}: Failed to serialize FHIR bundle: {e}")
                # Fallback to basic info
                bundle = full_response.fhir_bundle
                fhir_bundle_dict = {
                    "id": bundle.get("id"),
                    "type": bundle.get("type", "transaction"), 
                    "resource_count": len(bundle.get("entry", [])),
                    "error": f"Full bundle serialization failed: {str(e)}"
                }
        
        # Convert advanced response back to basic response format with FHIR bundle for visual validation
        response = ConvertResponse(
            request_id=full_response.request_id,
            status=full_response.status.value if hasattr(full_response.status, 'value') else str(full_response.status),
            message=f"Clinical order processed successfully with full FHIR conversion. "
                   f"Generated {len(full_response.fhir_bundle.get('entry', [])) if full_response.fhir_bundle else 0} FHIR resources. "
                   f"Bundle validation: {'PASSED' if full_response.fhir_validation_results and full_response.fhir_validation_results.get('is_valid') else 'PENDING'}",
            timestamp=full_response.metadata.server_timestamp,
            fhir_bundle=fhir_bundle_dict  # Include serialized FHIR bundle for user visibility
        )
        
        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(True, processing_time_ms)
        
        logger.info(f"Request {request_id}: Full Epic 2-3 conversion completed - "
                   f"FHIR resources: {len(full_response.fhir_bundle.get('entry', [])) if full_response.fhir_bundle else 0}, "
                   f"Valid: {full_response.fhir_validation_results.get('is_valid', False) if full_response.fhir_validation_results else False}")
        
        # Debug: Check if response has FHIR bundle
        logger.info(f"Request {request_id}: Response fhir_bundle is None: {response.fhir_bundle is None}")
        
        return response
        
    except ValueError as ve:
        # Validation errors (client-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)
        
        logger.warning(f"Request {request_id}: Validation error after {processing_time_ms:.2f}ms")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid input: {str(ve)}"
        )
        
    except Exception as e:
        # System errors (server-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)
        
        logger.error(f"Request {request_id}: System error after {processing_time_ms:.2f}ms - {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Processing failed. Please try again."
        )


@app.post("/api/v1/convert", response_model=ConvertResponseAdvanced)
async def convert_advanced(request: ClinicalRequestAdvanced):
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
        response = await get_conversion_service().convert_advanced(request, request_id)
        
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
            suggestions=["Check clinical text format", "Verify required fields"]
        )
        
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_response.dict()
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
            suggestions=["Try again later", "Contact support if problem persists"]
        )
        
        logger.error(f"Request {request_id}: Advanced conversion error - {type(e).__name__}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@app.post("/api/v1/bulk-convert")
async def bulk_convert(request: BulkConversionRequest):
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
                context_metadata={"batch_id": batch_id, "batch_processing": True}
            )
            advanced_requests.append(advanced_request)
        
        # Process bulk conversion
        result = await get_conversion_service().bulk_convert(advanced_requests, batch_id)
        
        # Record batch metrics
        processing_time_ms = (time.time() - start_time) * 1000
        success_rate = result["successful_orders"] / result["total_orders"]
        monitoring_service.record_request(success_rate > 0.5, processing_time_ms)
        
        return result
        
    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)
        
        logger.error(f"Bulk conversion {batch_id}: Processing error - {type(e).__name__}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "batch_id": batch_id,
                "error": "Bulk processing failed",
                "message": "Unable to process batch request"
            }
        )


@app.post("/summarize-bundle", response_model=SummarizeBundleResponse)
async def summarize_bundle(request: SummarizeBundleRequest):
    """
    Story 4.1: Generate plain-English summary of a validated FHIR Bundle.
    Feature-gated via SUMMARIZATION_ENABLED flag. Optionally attaches safety checks
    when SAFETY_VALIDATION_ENABLED is true (Story 4.2).
    """
    if not settings.summarization_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle summarization disabled")

    req_id = str(uuid4())
    start = time.time()
    try:
        # Use Epic 4 adaptive architecture for enhanced summarization
        result = await epic4_summarization_service.async_summarize(
            bundle=request.bundle, 
            role=request.user_role or "clinician", 
            context=request.context
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to summarize bundle")


@app.post("/summarize-bundle-enhanced")
async def summarize_bundle_enhanced(request: SummarizeBundleRequest):
    """
    Stories 4.3 & 4.4: Enhanced bundle summarization with optional LLM enhancement
    and integrated safety validation. Returns comprehensive summary with all Epic 4 features.
    """
    if not settings.summarization_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle summarization disabled")

    req_id = str(uuid4())
    start = time.time()
    
    try:
        # Prepare options for hybrid summarizer
        options = {
            "role": request.user_role or "clinician",
            "context": request.context,
            "llm_enhancement": request.llm_enhancement or False,
            "enhancement_level": request.enhancement_level or "contextual"
        }
        
        # Use hybrid summarizer for comprehensive results
        result = await hybrid_summarizer.create_comprehensive_summary(request.bundle, options)
        
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
            "enhancement_details": result.get("enhancement_details")
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
            detail=f"Failed to create enhanced summary: {str(e)}"
        )


# Story 3.3: HAPI FHIR Integration Endpoints

@app.post("/validate", response_model=ValidateBundleResponse)
async def validate_fhir_bundle(request: ValidateBundleRequest):
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
            request.bundle, 
            request_id=request_id,
            use_cache=request.use_cache
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
            timestamp=datetime.now()
        )
        
        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(validation_result["is_valid"], processing_time_ms)
        
        logger.info(f"[{request_id}] Bundle validation completed - "
                   f"Result: {response.validation_result} - "
                   f"Quality: {response.bundle_quality_score}")
        
        return response
        
    except ValueError as ve:
        # Validation errors (client-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)
        
        logger.warning(f"Request {request_id}: Bundle validation error")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid bundle: {str(ve)}"
        )
        
    except Exception as e:
        # System errors (server-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)
        
        logger.error(f"Request {request_id}: Bundle validation system error - {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Validation service error. Please try again."
        )


@app.post("/execute", response_model=ExecuteBundleResponse)
async def execute_fhir_bundle(request: ExecuteBundleRequest):
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
            force_execution=request.force_execution
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
            timestamp=datetime.now()
        )
        
        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(execution_result["success"], processing_time_ms)
        
        logger.info(f"[{request_id}] Bundle execution completed - "
                   f"Result: {response.execution_result} - "
                   f"Resources: {response.successful_resources}/{response.total_resources}")
        
        return response
        
    except ValueError as ve:
        # Validation errors (client-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)
        
        logger.warning(f"Request {request_id}: Bundle execution validation error")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid bundle for execution: {str(ve)}"
        )
        
    except Exception as e:
        # System errors (server-side issues)
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(False, processing_time_ms)
        
        logger.error(f"Request {request_id}: Bundle execution system error - {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Execution service error. Please try again."
        )


@app.get("/hapi/status")
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
        validation_service = await get_validation_service()
        validation_metrics = validation_service.get_validation_metrics()
        
        # Get execution service metrics
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
                "meets_availability_target": failover_metrics["meets_availability_target"],
                "meets_validation_target": validation_metrics["meets_target"]
            }
        }
        
    except Exception as e:
        logger.error(f"HAPI status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve HAPI status"
        )


# Story 3.4: Production FHIR Pipeline Endpoints

class UnifiedPipelineRequest(BaseModel):
    """Request model for unified FHIR pipeline processing"""
    nlp_entities: dict = Field(..., description="Structured medical data from NLP processing")
    validate_bundle: bool = Field(True, description="Whether to validate bundle with HAPI FHIR")
    execute_bundle: bool = Field(False, description="Whether to execute bundle on HAPI FHIR server")
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


@app.post("/fhir/pipeline", response_model=UnifiedPipelineResponse)
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
            execute_bundle=request.execute_bundle
        )
        
        processing_time = time.time() - start_time
        
        # Log performance
        logger.info(f"[{result.request_id}] Unified pipeline completed in {processing_time:.3f}s - Success: {result.success}")
        
        # Convert to response model
        return UnifiedPipelineResponse(**result.to_dict())
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Unified pipeline processing failed after {processing_time:.3f}s: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"FHIR pipeline processing failed: {str(e)}"
        )


@app.get("/fhir/pipeline/status")
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
                "performance_target_met": performance_summary.get("overall_statistics", {}).get("performance_target_met", False),
                "uptime_target_met": pipeline_status.get("pipeline_initialized", False),
                "epic4_ready": (
                    quality_trends.get("target_met", False) and
                    performance_summary.get("overall_statistics", {}).get("performance_target_met", False) and
                    pipeline_status.get("pipeline_initialized", False)
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get pipeline status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve pipeline status"
        )


@app.post("/fhir/optimize")
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
            "original_bundle_quality": quality_optimizer._analyze_bundle_quality(bundle),
            "optimized_bundle_quality": quality_optimizer._analyze_bundle_quality(optimized_bundle),
            "optimization_summary": optimized_bundle.get("meta", {}).get("optimization", {}),
            "improvement_recommendations": quality_optimizer._generate_improvement_suggestions({}, bundle)
        }
        
        return {
            "optimized_bundle": optimized_bundle,
            "quality_analysis": quality_analysis,
            "validation_prediction": {
                "estimated_success_probability": min(
                    quality_analysis["optimized_bundle_quality"]["bundle_structure_score"] * 100,
                    95.0
                ),
                "confidence": "high" if quality_analysis["optimized_bundle_quality"]["has_required_fields"] else "medium"
            }
        }
        
    except Exception as e:
        logger.error(f"Bundle optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bundle optimization failed: {str(e)}"
        )


@app.get("/fhir/quality/trends")
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
                    "Consider bundle optimization before validation"
                ] if trends.get("current_success_rate", 0) < 95 else [
                    "Continue current quality practices",
                    "Monitor for quality regression",
                    "Prepare for Epic 4 integration"
                ],
                "long_term_goals": [
                    "Maintain ≥95% validation success rate",
                    "Reduce validation response times",
                    "Improve bundle quality scores"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get quality trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve quality trends"
        )


@app.get("/fhir/performance/metrics")
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
                "overall_status": "healthy" if performance_summary.get("overall_statistics", {}).get("performance_target_met", False) else "needs_attention",
                "cache_efficiency": "good" if performance_summary.get("cache_performance", {}).get("target_met", False) else "poor",
                "recommendation_priority": "high" if len(performance_summary.get("optimization_recommendations", [])) > 3 else "low"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve performance metrics"
        )


@app.post("/fhir/performance/clear-cache")
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
                "Monitor performance for optimization opportunities"
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to clear caches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to clear performance caches"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
