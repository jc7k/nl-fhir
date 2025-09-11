"""
NL-FHIR Models Package
Pydantic models for request/response validation
HIPAA Compliant: No PHI in model definitions
"""

from .request import ClinicalRequest, ClinicalRequestAdvanced
from .response import (
    ConvertResponse, 
    ConvertResponseAdvanced,
    ErrorResponse,
    ValidationResult,
    ProcessingMetadata
)

__all__ = [
    "ClinicalRequest",
    "ClinicalRequestAdvanced", 
    "ConvertResponse",
    "ConvertResponseAdvanced",
    "ErrorResponse",
    "ValidationResult",
    "ProcessingMetadata"
]