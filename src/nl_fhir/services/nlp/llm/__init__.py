"""
LLM Package - Structured Clinical Output Processing
Compatibility shim for existing imports
"""

# Import all models for backward compatibility
from .models import (
    MedicationRoute,
    UrgencyLevel,
    ClinicalSetting,
    MedicationOrder,
    LabTest,
    DiagnosticProcedure,
    MedicalCondition,
    ClinicalStructure,
)

# Import the main processor and functions
from .llm_processor import (
    LLMProcessor,
    llm_processor,
    process_clinical_text,
    get_llm_processor_status,
)

# Import processors for advanced usage
from .processors import (
    InstructorProcessor,
    StructuredOutputProcessor,
    FallbackProcessor,
    PromptBuilder,
)

# Import utilities
from .utils import (
    ValidationHelpers,
    TokenCounter,
)

__all__ = [
    # Enums - backward compatibility
    'MedicationRoute',
    'UrgencyLevel',
    'ClinicalSetting',

    # Models - backward compatibility
    'MedicationOrder',
    'LabTest',
    'DiagnosticProcedure',
    'MedicalCondition',
    'ClinicalStructure',

    # Main processor - backward compatibility
    'LLMProcessor',
    'llm_processor',
    'process_clinical_text',
    'get_llm_processor_status',

    # Advanced components
    'InstructorProcessor',
    'StructuredOutputProcessor',
    'FallbackProcessor',
    'PromptBuilder',
    'ValidationHelpers',
    'TokenCounter',
]