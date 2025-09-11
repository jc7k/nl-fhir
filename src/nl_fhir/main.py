"""
NL-FHIR Component: Main FastAPI application
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

from typing import Optional
import logging
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
from .models.response import ConvertResponse, ConvertResponseAdvanced, ErrorResponse
from .services.conversion import ConversionService
from .services.monitoring import MonitoringService
from .services.validation import ValidationService

# Enhanced logger configuration with structured logging (no PHI)
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
conversion_service = ConversionService()
monitoring_service = MonitoringService() 
validation_service = ValidationService()

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
        pattern=r'^[A-Za-z0-9\-_]*$'  # Security: alphanumeric + dash/underscore only
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
        if not re.match(r'^[A-Za-z0-9\-_]+$', sanitized):
            raise ValueError("Patient reference contains invalid characters")
            
        return sanitized


class ConvertResponse(BaseModel):
    """Response model for convert endpoint"""
    request_id: str
    status: str
    message: str
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
    Basic clinical order conversion (Story 1.1 compatibility)
    
    Converts natural language clinical orders using basic processing.
    For advanced features, use /api/v1/convert endpoint.
    
    - **clinical_text**: Free-text clinical order (required)  
    - **patient_ref**: Optional patient reference identifier
    
    Returns basic conversion response with request tracking.
    """
    request_id = str(uuid4())
    start_time = time.time()
    
    try:
        # Use conversion service for processing
        response = await conversion_service.convert_basic(request, request_id)
        
        # Record metrics
        processing_time_ms = (time.time() - start_time) * 1000
        monitoring_service.record_request(True, processing_time_ms)
        
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
        
        logger.error(f"Request {request_id}: System error after {processing_time_ms:.2f}ms - {type(e).__name__}")
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
        result = await conversion_service.bulk_convert(advanced_requests, batch_id)
        
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)