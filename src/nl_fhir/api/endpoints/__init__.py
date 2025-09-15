"""
NL-FHIR API Endpoints Package
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

from .conversion import router as conversion_router
from .validation import router as validation_router
from .summarization import router as summarization_router
from .health import router as health_router
from .metrics import router as metrics_router
from .fhir_pipeline import router as fhir_pipeline_router
from .bulk_operations import router as bulk_operations_router

__all__ = [
    "conversion_router",
    "validation_router",
    "summarization_router",
    "health_router",
    "metrics_router",
    "fhir_pipeline_router",
    "bulk_operations_router",
]
