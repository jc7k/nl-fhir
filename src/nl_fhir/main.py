"""
NL-FHIR Component: Main FastAPI application
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

import logging
import logging.config
import re
from contextlib import asynccontextmanager
from typing import List, Optional

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
    rate_limit_middleware,
)

from .config import settings
from .services.model_warmup import model_warmup_service

# Story 2: Performance Optimization - Model Warmup with Modern Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern FastAPI lifespan handler for startup/shutdown events
    Performance Optimization: Pre-load NLP models at application startup
    """
    # Startup: Model warmup
    logger = logging.getLogger(__name__)
    logger.info("Starting application with model warmup for optimal performance...")
    warmup_result = await model_warmup_service.warmup_models()

    if warmup_result["models_loaded"]:
        logger.info(
            f"✅ Model warmup successful - Application ready in {warmup_result['total_time_seconds']:.2f}s"
        )
    else:
        logger.warning(
            f"⚠️ Model warmup completed with errors in {warmup_result['total_time_seconds']:.2f}s - "
            "Some models may not be available"
        )

    yield  # Application runs here

    # Shutdown: Cleanup
    logger.info("Application shutting down - cleaning up resources...")
    # Model cleanup is handled automatically by garbage collection


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

# FastAPI application with enhanced metadata and performance optimization
docs_url = "/docs" if not settings.is_production else None
redoc_url = "/redoc" if not settings.is_production else None
openapi_url = "/openapi.json" if not settings.is_production else None
app = FastAPI(
    title="NL-FHIR Converter",
    description="Natural Language to FHIR R4 Bundle Converter - Story 2 Performance Optimized",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    contact={
        "name": "NL-FHIR Development Team",
        "email": "dev@nl-fhir.example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,  # Story 2: Modern lifespan with model warmup
)

# Security middleware - trusted host protection
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts,
)

# CORS configuration - restricted for production security
def _split_cors_origins(origins: List[str]) -> tuple[List[str], Optional[str]]:
    explicit: List[str] = []
    regex_patterns: List[str] = []

    for origin in origins:
        if "*" in origin:
            pattern = "^" + re.escape(origin).replace("\\*", ".*") + "$"
            regex_patterns.append(pattern)
        else:
            explicit.append(origin)

    regex = "|".join(regex_patterns) if regex_patterns else None
    return explicit, regex


cors_origins, cors_regex = _split_cors_origins(settings.cors_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_regex,
    allow_credentials=False,  # Security: disable credentials
    allow_methods=["GET", "POST"],  # Restrict to required methods
    allow_headers=["content-type"],  # Restrict headers
)

# Register custom middleware in order so validation runs before headers are added
app.middleware("http")(rate_limit_middleware)
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
