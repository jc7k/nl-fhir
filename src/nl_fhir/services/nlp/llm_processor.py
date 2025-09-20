"""LLM Processor for Structured Clinical Output - COMPATIBILITY SHIM
HIPAA Compliant: Secure LLM integration with PHI protection
Production Ready: Fast structured output with Instructor validation

This module provides backward compatibility for the refactored LLM processor.
All functionality has been moved to the llm/ package with modular architecture.

REFACTORING COMPLETE:
- Original file: 1,143 lines → New coordinator: 157 lines
- All models extracted to llm/models/ package
- All processors extracted to llm/processors/ package
- All utilities extracted to llm/utils/ package
- Zero breaking changes - all imports work unchanged
"""

import logging
from typing import Dict, List, Any, Optional

# Import all components from the new modular structure
from .llm import (
    # Models - maintain backward compatibility
    MedicationRoute,
    UrgencyLevel,
    ClinicalSetting,
    MedicationOrder,
    LabTest,
    DiagnosticProcedure,
    MedicalCondition,
    ClinicalStructure,

    # Main processor base
    LLMProcessor as _BaseLLMProcessor,
    llm_processor as _base_llm_processor,
    process_clinical_text,
    get_llm_processor_status,
)

logger = logging.getLogger(__name__)

# Back-compat: expose whether 'instructor' package is installed
try:
    import instructor  # noqa: F401
    INSTRUCTOR_AVAILABLE = True
except Exception:
    INSTRUCTOR_AVAILABLE = False

class LLMProcessor(_BaseLLMProcessor):
    """Back-compat wrapper exposing api_key and client attributes.

    Older tests introspect these attributes directly. We forward them to the
    underlying InstructorProcessor instance.
    """

    @property
    def api_key(self):  # type: ignore[override]
        try:
            return getattr(self.instructor_processor, "api_key", None)
        except Exception:
            return None

    @property
    def client(self):  # type: ignore[override]
        try:
            return getattr(self.instructor_processor, "client", None)
        except Exception:
            return None


# Global instance for back-compat name
llm_processor = LLMProcessor()

# Export all the functions that were previously defined in this file
__all__ = [
    # Enums
    'MedicationRoute',
    'UrgencyLevel',
    'ClinicalSetting',

    # Models
    'MedicationOrder',
    'LabTest',
    'DiagnosticProcedure',
    'MedicalCondition',
    'ClinicalStructure',

    # Processor class and functions
    'LLMProcessor',
    'llm_processor',
    'process_clinical_text',
    'get_llm_processor_status',
    'INSTRUCTOR_AVAILABLE',
]
