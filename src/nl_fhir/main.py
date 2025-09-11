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

# FastAPI application
app = FastAPI(
    title="NL-FHIR Converter",
    description="Natural Language to FHIR R4 Bundle Converter",
    version="1.0.0"
)

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
    """Health check endpoint with performance metadata"""
    start_time = time.time()
    
    # Basic health indicators
    health_data = {
        "status": "healthy", 
        "service": "nl-fhir-converter",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    # Add response time for health monitoring
    processing_time = time.time() - start_time
    health_data["response_time_ms"] = round(processing_time * 1000, 2)
    
    return health_data


@app.post("/convert", response_model=ConvertResponse)
async def convert_to_fhir(request: ClinicalRequest):
    """
    Convert natural language clinical orders to FHIR bundle
    
    This is a stub implementation for Epic 1.
    Full NLP processing will be implemented in Epic 2.
    """
    request_id = str(uuid4())
    start_time = time.time()
    
    try:
        # Log request initiation without PHI
        logger.info(f"Processing conversion request {request_id} - "
                   f"text_length={len(request.clinical_text)} chars")
        
        # Input validation logging (security monitoring)
        if len(request.clinical_text) > 4000:  # Large input monitoring
            logger.warning(f"Request {request_id}: Large clinical text input ({len(request.clinical_text)} chars)")
        
        # Simulate processing time for performance testing
        processing_time = time.time() - start_time
        
        # Success logging with metrics
        logger.info(f"Request {request_id}: Conversion completed successfully in {processing_time:.3f}s")
        
        # Placeholder response - actual FHIR conversion in Epic 2
        return ConvertResponse(
            request_id=request_id,
            status="received",
            message="Clinical order received and queued for processing. Full FHIR conversion coming in Epic 2.",
            timestamp=datetime.now()
        )
        
    except ValueError as ve:
        # Validation errors (client-side issues)
        processing_time = time.time() - start_time
        logger.warning(f"Request {request_id}: Validation error after {processing_time:.3f}s - {str(ve)[:100]}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid input: {str(ve)}"
        )
        
    except Exception as e:
        # System errors (server-side issues)
        processing_time = time.time() - start_time
        logger.error(f"Request {request_id}: System error after {processing_time:.3f}s - {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Processing failed. Please try again."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)