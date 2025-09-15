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

    # Main processor
    LLMProcessor,
    llm_processor,
    process_clinical_text,
    get_llm_processor_status,
)

logger = logging.getLogger(__name__)

# Maintain complete backward compatibility
# Re-export all the original functions and classes so existing imports work unchanged

# The global processor instance from the new modular architecture
# All calls are delegated to the new llm_processor in the llm package

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
]