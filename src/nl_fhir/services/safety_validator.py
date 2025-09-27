"""
Story 4.2: Enhanced Safety Validation for FHIR Bundles
Comprehensive safety framework with backward compatibility
"""

from typing import Any, Dict, List, Optional
from .safety.enhanced_safety_validator import EnhancedSafetyValidator
from .validation_common import HIGH_RISK_MEDS


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
        """
        issues: List[str] = []
        warnings: List[str] = []

        entries = bundle.get("entry", []) or []

        for e in entries:
            r = e.get("resource", {}) if isinstance(e, dict) else {}
            rt = r.get("resourceType")

            if rt == "MedicationRequest":
                med_text = self._get_med_text(r).lower()
                if any(hr in med_text for hr in HIGH_RISK_MEDS):
                    issues.append(f"High-risk medication detected: {med_text}")

                # Missing dosage
                if not r.get("dosageInstruction"):
                    warnings.append(f"MedicationRequest missing dosageInstruction for {med_text}")

            if rt == "AllergyIntolerance":
                desc = self._get_allergy_text(r)
                warnings.append(f"Allergy noted: {desc}")

            if rt == "Observation":
                interp = self._get_obs_interpretation(r)
                if interp and str(interp).upper() in {"H", "HIGH", "L", "LOW", "HH", "LL", "CRIT", "CRITICAL"}:
                    warnings.append(f"Observation flagged as {interp}")

        return {
            "is_safe": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "summary": {
                "issues_count": len(issues),
                "warnings_count": len(warnings),
            },
        }

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
