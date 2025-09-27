"""
NL-FHIR Shared Dependencies
HIPAA Compliant: No PHI logging
Medical Safety: Input validation required
"""

import importlib
from typing import Any

from ..services.monitoring import MonitoringService
from ..services.validation import ValidationService
from ..services.summarization_compatibility import SummarizationService
from ..services.epic4_summarization_adapter import Epic4SummarizationAdapter
from ..services.safety_validator import SafetyValidator
from ..services.hybrid_summarizer import HybridSummarizer

# Story 3.3: Import HAPI FHIR services

# Story 3.4: Import production FHIR services

# Initialize shared services
monitoring_service = MonitoringService()
validation_service = ValidationService()
summarization_service = SummarizationService()  # Legacy service for compatibility
epic4_summarization_service = (
    Epic4SummarizationAdapter()
)  # New Epic 4 adaptive architecture
safety_validator = SafetyValidator()
hybrid_summarizer = HybridSummarizer()

# Lazy loader for ConversionService to avoid importing NLP stack at startup
_conversion_service = None


def get_conversion_service() -> Any:
    """Lazy load conversion service to avoid startup delays"""
    global _conversion_service
    if _conversion_service is None:
        module = importlib.import_module("src.nl_fhir.services.conversion")
        _conversion_service = module.ConversionService()
    return _conversion_service


# FastAPI dependency functions for injection
async def get_monitoring_service() -> MonitoringService:
    """Get monitoring service dependency"""
    return monitoring_service


async def get_validation_service_dep() -> ValidationService:
    """Get validation service dependency"""
    return validation_service


async def get_conversion_service_dep() -> Any:
    """Get conversion service dependency"""
    return get_conversion_service()


async def get_epic4_summarization_service() -> Epic4SummarizationAdapter:
    """Get Epic 4 summarization service dependency"""
    return epic4_summarization_service


async def get_safety_validator_dep() -> SafetyValidator:
    """Get safety validator dependency"""
    return safety_validator


async def get_hybrid_summarizer_dep() -> HybridSummarizer:
    """Get hybrid summarizer dependency"""
    return hybrid_summarizer
