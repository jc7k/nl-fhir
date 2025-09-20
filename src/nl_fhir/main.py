"""
NL-FHIR Component: Main FastAPI application
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

import logging
import logging.config
from typing import Optional
import re

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, field_validator

# Import API routers and middleware
from .api import (
    conversion_router,
    validation_router,
    summarization_router,
    health_router,
    metrics_router,
    fhir_pipeline_router,
    bulk_operations_router,
)
from .api.middleware import (
    request_timing_and_validation,
    add_security_headers,
    sanitize_clinical_text,
)

from .config import settings

# Enhanced logger configuration with structured logging (no PHI)
try:
    logging.config.dictConfig(settings.get_log_config())
except Exception:
    # Fallback to basic config if dictConfig fails for any reason
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s",
    )
logger = logging.getLogger(__name__)

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
    },
)

# Security middleware - trusted host protection
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "*.railway.app",
        "testserver",
    ],  # testserver for tests
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

# Register custom middleware in order so validation runs before headers are added
app.middleware("http")(request_timing_and_validation)
app.middleware("http")(add_security_headers)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class ClinicalRequest(BaseModel):
    """HIPAA-compliant clinical request model"""

    clinical_text: str = Field(
        ...,
        description="Free-text clinical order",
        max_length=5000,  # Security: limit input size
    )
    patient_ref: Optional[str] = Field(
        None,
        description="Patient reference ID",
        max_length=100,  # Security: limit patient ref size
        pattern=r"^[A-Za-z0-9\-_/]*$",  # Security: alphanumeric + dash/underscore/slash for FHIR references
    )

    @field_validator("clinical_text")
    @classmethod
    def validate_clinical_text(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("Clinical text must be at least 5 characters")

        # Sanitize input for security
        sanitized = sanitize_clinical_text(v.strip())

        if len(sanitized) < 5:
            raise ValueError("Clinical text too short after sanitization")

        return sanitized

    @field_validator("patient_ref")
    @classmethod
    def validate_patient_ref(cls, v):
        if v is None:
            return v

        # Sanitize patient reference
        sanitized = v.strip()
        if not sanitized:
            return None

        # Validate pattern (already enforced by Field pattern, but double-check)
        if not re.match(r"^[A-Za-z0-9\-_/]+$", sanitized):
            raise ValueError("Patient reference contains invalid characters")

        return sanitized


@app.get("/", response_class=HTMLResponse)
async def serve_form(request: Request):
    """Serve the main web form interface"""
    return templates.TemplateResponse("index.html", {"request": request})


# Include API routers with proper organization
app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(conversion_router)
app.include_router(bulk_operations_router)
app.include_router(validation_router)
app.include_router(summarization_router)
app.include_router(fhir_pipeline_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
