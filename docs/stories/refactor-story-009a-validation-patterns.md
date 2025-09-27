# Story: Consolidate Validation Patterns and Constants

**Story ID:** REFACTOR-009A
**Epic:** Validation Cleanup (Epic 2)
**Status:** READY FOR DEVELOPMENT
**Estimated Effort:** 2 hours
**Priority:** P2 - Medium

## User Story

**As a** developer
**I want** shared validation patterns and constants in a single location
**So that** validation logic is consistent and not duplicated across multiple files

## Background & Context

Following the successful completion of REFACTOR-006, REFACTOR-007, and REFACTOR-008, this smaller-scope validation consolidation focuses on eliminating duplicate patterns and constants found across multiple validation services.

### Current Duplication Analysis

**Duplicate High-Risk Medication Lists:**
- `services/safety_validator.py`: `HIGH_RISK_MEDS = {"warfarin", "insulin", "digoxin", ...}`
- `services/validation.py`: `self.high_risk_patterns = [r'\bwarfarin\b', r'\binsulin\b', ...]`
- `services/nlp/model_managers/medspacy_manager.py`: Individual medication target rules

**Duplicate Medication Patterns:**
- `services/validation.py`: Medication dosage and frequency patterns
- `services/nlp/extractors/regex_extractor.py`: Similar medication extraction patterns
- Multiple files with medication name patterns

**Duplicate Safety Patterns:**
- Various files contain similar safety validation patterns
- Inconsistent pattern formats (regex vs. string sets)

## Proposed Simple Consolidation

### Create Shared Validation Constants Module

```python
# src/nl_fhir/services/validation_common.py

"""
Shared Validation Patterns and Constants
Consolidated from multiple validation services to eliminate duplication
REFACTOR-009A: Simple validation patterns consolidation
"""

from typing import Set, List
import re


class ValidationPatterns:
    """Centralized validation patterns and constants"""

    # High-risk medications (consolidated from multiple sources)
    HIGH_RISK_MEDICATIONS: Set[str] = {
        "warfarin",
        "insulin",
        "digoxin",
        "clozapine",
        "amiodarone",
        "morphine",
        "fentanyl",
        "heparin",
        "chemotherapy"
    }

    # Medication patterns for text analysis
    MEDICATION_DOSAGE_PATTERNS: List[str] = [
        r'\b\d+\s*mg\b',
        r'\b\d+\s*ml\b',
        r'\b\d+\s*mcg\b',
        r'\b\d+\s*units?\b'
    ]

    MEDICATION_FORM_PATTERNS: List[str] = [
        r'\btablet\b',
        r'\bcapsule\b',
        r'\binjection\b',
        r'\btopical\b',
        r'\bdrop\b'
    ]

    MEDICATION_FREQUENCY_PATTERNS: List[str] = [
        r'\bdaily\b',
        r'\btwice\s+daily\b',
        r'\btid\b',
        r'\bbid\b',
        r'\bqid\b',
        r'\bprn\b'
    ]

    # Clinical patterns
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
        """Get high-risk medications as regex patterns for backward compatibility"""
        return [rf'\b{med}\b' for med in cls.HIGH_RISK_MEDICATIONS]

    @classmethod
    def is_high_risk_medication(cls, medication_text: str) -> bool:
        """Check if medication text contains high-risk medications"""
        medication_lower = medication_text.lower()
        return any(med in medication_lower for med in cls.HIGH_RISK_MEDICATIONS)

    @classmethod
    def get_all_medication_patterns(cls) -> List[str]:
        """Get all medication-related patterns combined"""
        return (cls.MEDICATION_DOSAGE_PATTERNS +
                cls.MEDICATION_FORM_PATTERNS +
                cls.MEDICATION_FREQUENCY_PATTERNS)


# Convenience constants for backward compatibility
HIGH_RISK_MEDS = ValidationPatterns.HIGH_RISK_MEDICATIONS
HIGH_RISK_PATTERNS = ValidationPatterns.get_high_risk_regex_patterns()
```

## Implementation Plan

### Phase 1: Create Shared Module
1. Create `src/nl_fhir/services/validation_common.py`
2. Consolidate all duplicate patterns from existing files
3. Add convenience methods for different usage patterns

### Phase 2: Update Existing Services
1. **Update `safety_validator.py`**:
   ```python
   from .validation_common import ValidationPatterns

   # Replace: HIGH_RISK_MEDS = {"warfarin", ...}
   # With: HIGH_RISK_MEDS = ValidationPatterns.HIGH_RISK_MEDICATIONS
   ```

2. **Update `validation.py`**:
   ```python
   from .validation_common import ValidationPatterns

   def __init__(self):
       self.medication_patterns = ValidationPatterns.get_all_medication_patterns()
       self.high_risk_patterns = ValidationPatterns.get_high_risk_regex_patterns()
   ```

3. **Update other files with duplicate patterns**

### Phase 3: Clean Up
1. Remove duplicate constant definitions
2. Update imports across the codebase
3. Verify all functionality preserved

## Files to Modify

**Files with Duplicate Patterns:**
- `src/nl_fhir/services/safety_validator.py` - HIGH_RISK_MEDS consolidation
- `src/nl_fhir/services/validation.py` - Pattern consolidation
- `src/nl_fhir/services/nlp/extractors/regex_extractor.py` - Medication patterns
- `src/nl_fhir/services/nlp/model_managers/medspacy_manager.py` - Target rules

**New File:**
- `src/nl_fhir/services/validation_common.py` - Consolidated patterns

## Benefits

### 1. **Eliminates Duplication**
- Single source of truth for validation patterns
- Consistent medication lists across services
- Unified pattern formats

### 2. **Improves Maintainability**
- Easy to add new high-risk medications
- Central location for pattern updates
- Consistent validation behavior

### 3. **Enhances Consistency**
- Same medication patterns used everywhere
- Consistent safety validation across services
- Unified approach to pattern matching

## Risk Assessment

**Risk Level:** Very Low
- Only consolidating existing constants and patterns
- No functional changes to validation logic
- Backward compatibility maintained with convenience methods

**Mitigation:**
- Maintain exact same validation behavior
- Add convenience methods for different usage patterns
- Comprehensive testing of all affected services

## Acceptance Criteria

### Must Have
- [ ] Shared validation patterns module created
- [ ] All duplicate HIGH_RISK_MEDICATIONS consolidated
- [ ] All duplicate medication patterns consolidated
- [ ] Existing validation services updated to use shared patterns
- [ ] All functionality preserved (no regressions)
- [ ] Zero breaking changes

### Should Have
- [ ] Convenience methods for different pattern usage styles
- [ ] Backward compatibility aliases for existing constants
- [ ] Documentation for the new shared module

### Could Have
- [ ] Additional validation utilities in the shared module
- [ ] Configuration-driven pattern definitions
- [ ] Pattern validation testing utilities

## Success Metrics

- **Lines reduced**: Target 30-50 lines of duplicate patterns
- **Files consolidated**: 4-5 files using shared patterns
- **Zero regressions**: All existing validation tests pass
- **Consistency**: All services use identical patterns

## Verification Plan

1. **Pattern Verification**: Ensure all consolidated patterns match originals
2. **Service Testing**: Verify each updated service works identically
3. **Integration Testing**: Test end-to-end validation workflows
4. **Import Testing**: Verify all imports resolve correctly

## Definition of Done

- [ ] Shared validation patterns module implemented
- [ ] All identified duplicate patterns consolidated
- [ ] Safety validator updated to use shared HIGH_RISK_MEDICATIONS
- [ ] General validation service updated to use shared patterns
- [ ] NLP extractors updated to use shared medication patterns
- [ ] All imports updated and working
- [ ] No functional regressions detected
- [ ] Meaningful code duplication eliminated

---
**Story Status:** READY FOR DEVELOPMENT
**Dependencies:** REFACTOR-006, REFACTOR-007, REFACTOR-008 (completed)
**Complexity:** Low (simple constant consolidation)
**Next Step:** REFACTOR-009B (if needed) - Additional validation consolidation