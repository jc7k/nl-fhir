"""
Shared Validation Patterns and Constants
Consolidated from multiple validation services to eliminate duplication
REFACTOR-009A: Simple validation patterns consolidation
"""

import re
from typing import Set, List


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
