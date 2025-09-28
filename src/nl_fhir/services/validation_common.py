"""
Shared Validation Patterns and Constants
Consolidated from multiple validation services to eliminate duplication
REFACTOR-009A: Simple validation patterns consolidation
REFACTOR-009B: Unified validation models and response formats
"""

import re
from typing import Set, List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class ValidationPatterns:
    """Centralized validation patterns and constants"""

    # High-risk medications (consolidated from safety_validator.py and validation.py)
    HIGH_RISK_MEDICATIONS: Set[str] = {
        "warfarin",
        "insulin",
        "digoxin",
        "clozapine",
        "amiodarone",
        "chemotherapy",
        "heparin",
        "morphine",
        "fentanyl"
    }

    # Medication patterns consolidated from validation.py
    MEDICATION_DOSAGE_PATTERNS: List[str] = [
        r'\b\d+\s*mg\b',
        r'\b\d+\s*ml\b'
    ]

    MEDICATION_FORM_PATTERNS: List[str] = [
        r'\btablet\b',
        r'\bcapsule\b'
    ]

    MEDICATION_FREQUENCY_PATTERNS: List[str] = [
        r'\bdaily\b',
        r'\btwice\s+daily\b',
        r'\btid\b',
        r'\bbid\b',
        r'\bqid\b'
    ]

    # Lab test patterns from validation.py
    LAB_TEST_PATTERNS: List[str] = [
        r'\bcbc\b',
        r'\bblood\s+work\b',
        r'\blab\s+test\b',
        r'\burine\s+test\b',
        r'\bculture\b',
        r'\bx-?ray\b',
        r'\bct\s+scan\b',
        r'\bmri\b'
    ]

    # Procedure patterns from validation.py
    PROCEDURE_PATTERNS: List[str] = [
        r'\bprocedure\b',
        r'\bsurgery\b',
        r'\bbiopsy\b',
        r'\bendoscopy\b',
        r'\bcatheter\b',
        r'\binjection\b'
    ]

    @classmethod
    def get_high_risk_regex_patterns(cls) -> List[str]:
        """Get high-risk medications as regex patterns for backward compatibility with validation.py"""
        return [rf'\b{re.escape(med)}\b' for med in cls.HIGH_RISK_MEDICATIONS]

    @classmethod
    def is_high_risk_medication(cls, medication_text: str) -> bool:
        """Check if medication text contains high-risk medications (for safety_validator.py compatibility)"""
        medication_lower = medication_text.lower()
        # Use word boundary regex matching to prevent false positives (e.g., "counseling" containing "insulin")
        for med in cls.HIGH_RISK_MEDICATIONS:
            if re.search(rf'\b{re.escape(med)}\b', medication_lower):
                return True
        return False

    @classmethod
    def get_all_medication_patterns(cls) -> List[str]:
        """Get all medication-related patterns combined (for validation.py compatibility)"""
        return (cls.MEDICATION_DOSAGE_PATTERNS +
                cls.MEDICATION_FORM_PATTERNS +
                cls.MEDICATION_FREQUENCY_PATTERNS)


# Convenience constants for backward compatibility
HIGH_RISK_MEDS = ValidationPatterns.HIGH_RISK_MEDICATIONS  # For safety_validator.py

# Note: HIGH_RISK_PATTERNS now computed on-demand via ValidationPatterns.get_high_risk_regex_patterns()
# to improve module import performance and prevent regex compilation at import time


# =============================================================================
# UNIFIED VALIDATION MODELS (REFACTOR-009B)
# =============================================================================

class ValidationSeverity(str, Enum):
    """
    Unified validation severity levels for all validation services
    Consolidates ValidationSeverity from clinical_validator.py, fhir/validation_service.py, and fhir/validator.py
    """
    FATAL = "fatal"         # Cannot process at all
    ERROR = "error"         # Missing required fields or critical issues
    WARNING = "warning"     # Suboptimal but processable
    INFORMATION = "information"  # Advisory information


class ValidationCode(str, Enum):
    """
    Unified validation error codes across all validation services
    Consolidates codes from clinical_validator.py and adds new standardized codes
    """
    # Critical structural issues
    CONDITIONAL_LOGIC = "CONDITIONAL_LOGIC"
    MEDICATION_AMBIGUITY = "MEDICATION_AMBIGUITY"
    MISSING_MEDICATION = "MISSING_MEDICATION"
    MISSING_DOSAGE = "MISSING_DOSAGE"
    MISSING_FREQUENCY = "MISSING_FREQUENCY"
    MISSING_ROUTE = "MISSING_ROUTE"

    # Protocol and reference issues
    PROTOCOL_REFERENCE = "PROTOCOL_REFERENCE"
    EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"
    DISCRETIONARY_DOSING = "DISCRETIONARY_DOSING"

    # Clinical safety issues
    CONTRAINDICATION_LOGIC = "CONTRAINDICATION_LOGIC"
    CONDITIONAL_SAFETY = "CONDITIONAL_SAFETY"
    INCOMPLETE_ORDER = "INCOMPLETE_ORDER"
    VAGUE_INTENT = "VAGUE_INTENT"
    HIGH_RISK_MEDICATION = "HIGH_RISK_MEDICATION"

    # FHIR compliance issues
    FHIR_REQUIRED_FIELD = "FHIR_REQUIRED_FIELD"
    FHIR_ENCODING_IMPOSSIBLE = "FHIR_ENCODING_IMPOSSIBLE"
    FHIR_RESOURCE_INCOMPLETE = "FHIR_RESOURCE_INCOMPLETE"
    FHIR_VALIDATION_ERROR = "FHIR_VALIDATION_ERROR"

    # Input validation issues
    INPUT_TOO_SHORT = "INPUT_TOO_SHORT"
    INPUT_TOO_LONG = "INPUT_TOO_LONG"
    INPUT_INVALID_CHARACTERS = "INPUT_INVALID_CHARACTERS"
    INPUT_REPETITION = "INPUT_REPETITION"

    # General validation issues
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class ValidationResult(str, Enum):
    """Overall validation result status"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass
class ValidationIssue:
    """
    Unified validation issue structure for all validation services
    Replaces different issue formats across clinical_validator.py, validation.py, etc.
    """
    severity: ValidationSeverity
    code: ValidationCode
    message: str
    context: Optional[str] = None
    suggestions: Optional[List[str]] = None
    resource_type: Optional[str] = None
    field: Optional[str] = None
    location: Optional[str] = None


@dataclass
class UnifiedValidationResult:
    """
    Unified validation result structure for all validation services
    Consolidates different result formats from:
    - clinical_validator.py (ValidationResult class)
    - validation.py (dict-based results)
    - safety_validator.py (dict-based results)
    - fhir/validation_service.py (custom format)
    """
    # Core result information
    is_valid: bool
    overall_result: ValidationResult
    confidence_score: float = 1.0

    # Issues and messages
    issues: List[ValidationIssue] = None
    warnings: List[str] = None
    errors: List[str] = None
    suggestions: List[str] = None

    # Categorization and metadata
    detected_categories: List[str] = None
    safety_level: str = "standard"  # "standard", "moderate_risk", "high_risk"

    # Risk assessment details
    risk_assessment: Dict[str, Any] = None

    # Processing metadata
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    processing_time_ms: Optional[float] = None
    validator_name: Optional[str] = None

    # Summary statistics
    summary: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize default values"""
        if self.issues is None:
            self.issues = []
        if self.warnings is None:
            self.warnings = []
        if self.errors is None:
            self.errors = []
        if self.suggestions is None:
            self.suggestions = []
        if self.detected_categories is None:
            self.detected_categories = []
        if self.risk_assessment is None:
            self.risk_assessment = {}
        if self.summary is None:
            self.summary = {}
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def get_issue_counts(self) -> Dict[str, int]:
        """Get count of issues by severity"""
        counts = {
            "fatal": 0,
            "error": 0,
            "warning": 0,
            "information": 0
        }
        for issue in self.issues:
            counts[issue.severity.value] += 1
        return counts

    def has_blocking_issues(self) -> bool:
        """Check if there are any fatal or error-level issues"""
        return any(issue.severity in [ValidationSeverity.FATAL, ValidationSeverity.ERROR]
                  for issue in self.issues)

    def to_legacy_dict(self) -> Dict[str, Any]:
        """
        Convert to legacy dict format for backward compatibility
        Supports migration from dict-based validation results
        """
        issue_counts = self.get_issue_counts()

        # Convert structured issues to legacy format strings for backward compatibility
        legacy_issues = []
        legacy_warnings = list(self.warnings)  # Copy existing warnings

        for issue in self.issues:
            if issue.severity == ValidationSeverity.ERROR:
                legacy_issues.append(issue.message)
            elif issue.severity == ValidationSeverity.WARNING:
                legacy_warnings.append(issue.message)

        return {
            # New unified fields
            "is_valid": self.is_valid,
            "confidence_score": self.confidence_score,
            "safety_level": self.safety_level,
            "warnings": legacy_warnings,
            "errors": self.errors,
            "suggestions": self.suggestions,
            "detected_categories": self.detected_categories,
            "risk_assessment": self.risk_assessment,

            # Legacy compatibility fields
            "is_safe": self.is_valid,  # safety_validator.py expects this
            "issues": legacy_issues,   # Convert structured issues to string list

            # Structured issues for new consumers
            "structured_issues": [
                {
                    "severity": issue.severity.value,
                    "code": issue.code.value,
                    "message": issue.message,
                    "context": issue.context,
                    "suggestions": issue.suggestions,
                    "resource_type": issue.resource_type,
                    "field": issue.field,
                    "location": issue.location
                }
                for issue in self.issues
            ],

            "summary": {
                "issues_count": len(legacy_issues),  # Legacy string issues count
                "warnings_count": len(legacy_warnings),
                "errors_count": len(self.errors),
                "fatal_count": issue_counts["fatal"],
                "error_count": issue_counts["error"],
                "warning_count": issue_counts["warning"],
                "information_count": issue_counts["information"],
                **self.summary
            }
        }


def create_validation_issue(
    severity: ValidationSeverity,
    code: ValidationCode,
    message: str,
    **kwargs
) -> ValidationIssue:
    """Convenience function for creating validation issues"""
    return ValidationIssue(
        severity=severity,
        code=code,
        message=message,
        **kwargs
    )


def create_validation_result(
    is_valid: bool,
    validator_name: str,
    issues: Optional[List[ValidationIssue]] = None,
    **kwargs
) -> UnifiedValidationResult:
    """Convenience function for creating unified validation results"""
    if issues is None:
        issues = []

    # Determine overall result based on issues
    if any(issue.severity == ValidationSeverity.FATAL for issue in issues):
        overall_result = ValidationResult.FATAL
    elif any(issue.severity == ValidationSeverity.ERROR for issue in issues):
        overall_result = ValidationResult.ERROR
    elif any(issue.severity == ValidationSeverity.WARNING for issue in issues):
        overall_result = ValidationResult.WARNING
    else:
        overall_result = ValidationResult.SUCCESS

    return UnifiedValidationResult(
        is_valid=is_valid,
        overall_result=overall_result,
        issues=issues,
        validator_name=validator_name,
        **kwargs
    )
