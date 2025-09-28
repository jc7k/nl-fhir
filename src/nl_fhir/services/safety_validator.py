"""
Story 4.2: Enhanced Safety Validation for FHIR Bundles
Comprehensive safety framework with backward compatibility
REFACTOR-009B: Updated to use unified validation models
"""

from typing import Any, Dict, List, Optional, Union
from .safety.enhanced_safety_validator import EnhancedSafetyValidator
from .validation_common import (
    HIGH_RISK_MEDS, ValidationPatterns,
    ValidationSeverity, ValidationCode, ValidationIssue,
    UnifiedValidationResult, create_validation_issue, create_validation_result
)


class SafetyValidator:
    """Enhanced safety validator with backward compatibility for Story 4.1"""
    
    def __init__(self):
        # Initialize enhanced safety validator for comprehensive analysis
        self.enhanced_validator = EnhancedSafetyValidator()

    def evaluate(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced safety evaluation with backward compatibility
        
        Returns both basic safety check (Story 4.1 compatibility) and enhanced analysis (Story 4.2)
        """
        # Use enhanced safety validator for comprehensive analysis
        enhanced_results = self.enhanced_validator.enhanced_safety_check(bundle)
        
        # Return enhanced results with Story 4.1 compatibility
        return enhanced_results
    
    def basic_evaluate(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        Basic safety evaluation (original Story 4.1 implementation)

        Maintained for backward compatibility and fallback scenarios
        REFACTOR-009B: Updated to use unified validation models and fixed regex patterns
        """
        validation_issues: List[ValidationIssue] = []
        warnings: List[str] = []

        entries = bundle.get("entry", []) or []

        for e in entries:
            r = e.get("resource", {}) if isinstance(e, dict) else {}
            rt = r.get("resourceType")

            if rt == "MedicationRequest":
                med_text = self._get_med_text(r)

                # Use fixed high-risk medication detection (no false positives)
                if ValidationPatterns.is_high_risk_medication(med_text):
                    validation_issues.append(create_validation_issue(
                        severity=ValidationSeverity.ERROR,
                        code=ValidationCode.HIGH_RISK_MEDICATION,
                        message=f"High-risk medication detected: {med_text}",
                        resource_type="MedicationRequest",
                        context=med_text
                    ))

                # Missing dosage
                if not r.get("dosageInstruction"):
                    validation_issues.append(create_validation_issue(
                        severity=ValidationSeverity.WARNING,
                        code=ValidationCode.MISSING_DOSAGE,
                        message=f"MedicationRequest missing dosageInstruction for {med_text}",
                        resource_type="MedicationRequest",
                        field="dosageInstruction"
                    ))

            if rt == "AllergyIntolerance":
                desc = self._get_allergy_text(r)
                warnings.append(f"Allergy noted: {desc}")

            if rt == "Observation":
                interp = self._get_obs_interpretation(r)
                if interp and str(interp).upper() in {"H", "HIGH", "L", "LOW", "HH", "LL", "CRIT", "CRITICAL"}:
                    warnings.append(f"Observation flagged as {interp}")

        # Create unified validation result
        unified_result = create_validation_result(
            is_valid=len(validation_issues) == 0 or not any(
                issue.severity == ValidationSeverity.ERROR for issue in validation_issues
            ),
            validator_name="safety_validator",
            issues=validation_issues,
            warnings=warnings,
            safety_level="high_risk" if any(
                issue.code == ValidationCode.HIGH_RISK_MEDICATION for issue in validation_issues
            ) else "standard"
        )

        # Return legacy dict format for backward compatibility
        return unified_result.to_legacy_dict()

    def evaluate_unified(self, bundle: Dict[str, Any]) -> UnifiedValidationResult:
        """
        Modern safety evaluation using unified validation models

        Returns UnifiedValidationResult instead of dict for new integrations
        REFACTOR-009B: New method providing structured validation results
        """
        validation_issues: List[ValidationIssue] = []
        warnings: List[str] = []

        entries = bundle.get("entry", []) or []

        for e in entries:
            r = e.get("resource", {}) if isinstance(e, dict) else {}
            rt = r.get("resourceType")

            if rt == "MedicationRequest":
                med_text = self._get_med_text(r)

                # Use fixed high-risk medication detection (no false positives)
                if ValidationPatterns.is_high_risk_medication(med_text):
                    validation_issues.append(create_validation_issue(
                        severity=ValidationSeverity.ERROR,
                        code=ValidationCode.HIGH_RISK_MEDICATION,
                        message=f"High-risk medication detected: {med_text}",
                        resource_type="MedicationRequest",
                        context=med_text
                    ))

                # Missing dosage
                if not r.get("dosageInstruction"):
                    validation_issues.append(create_validation_issue(
                        severity=ValidationSeverity.WARNING,
                        code=ValidationCode.MISSING_DOSAGE,
                        message=f"MedicationRequest missing dosageInstruction for {med_text}",
                        resource_type="MedicationRequest",
                        field="dosageInstruction"
                    ))

            if rt == "AllergyIntolerance":
                desc = self._get_allergy_text(r)
                # Convert allergy warning to structured issue
                validation_issues.append(create_validation_issue(
                    severity=ValidationSeverity.INFORMATION,
                    code=ValidationCode.CONTRAINDICATION_LOGIC,
                    message=f"Allergy noted: {desc}",
                    resource_type="AllergyIntolerance",
                    context=desc
                ))

            if rt == "Observation":
                interp = self._get_obs_interpretation(r)
                if interp and str(interp).upper() in {"H", "HIGH", "L", "LOW", "HH", "LL", "CRIT", "CRITICAL"}:
                    validation_issues.append(create_validation_issue(
                        severity=ValidationSeverity.WARNING,
                        code=ValidationCode.CONDITIONAL_SAFETY,
                        message=f"Observation flagged as {interp}",
                        resource_type="Observation",
                        context=interp
                    ))

        # Create unified validation result
        return create_validation_result(
            is_valid=not any(
                issue.severity == ValidationSeverity.ERROR for issue in validation_issues
            ),
            validator_name="safety_validator",
            issues=validation_issues,
            warnings=warnings,
            safety_level="high_risk" if any(
                issue.code == ValidationCode.HIGH_RISK_MEDICATION for issue in validation_issues
            ) else "standard"
        )

    def _get_med_text(self, r: Dict[str, Any]) -> str:
        cc = r.get("medicationCodeableConcept", {})
        if cc.get("text"):
            return cc["text"]
        codings = cc.get("coding", [])
        if codings:
            return codings[0].get("display") or codings[0].get("code") or "medication"
        return "medication"

    def _get_allergy_text(self, r: Dict[str, Any]) -> str:
        code = r.get("code", {})
        if code.get("text"):
            return code["text"]
        codings = code.get("coding", [])
        if codings:
            return codings[0].get("display") or codings[0].get("code") or "allergy"
        return "allergy"

    def _get_obs_interpretation(self, r: Dict[str, Any]) -> str | None:
        interp = r.get("interpretation")
        if isinstance(interp, dict):
            if interp.get("text"):
                return interp["text"]
            codings = interp.get("coding", [])
            if codings:
                return codings[0].get("display") or codings[0].get("code")
        elif isinstance(interp, list) and interp:
            first = interp[0]
            if first.get("text"):
                return first["text"]
            codings = first.get("coding", [])
            if codings:
                return codings[0].get("display") or codings[0].get("code")
        return None
