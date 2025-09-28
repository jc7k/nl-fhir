"""
Clinical Order Validation System
Comprehensive error detection for ambiguous, incomplete, and problematic clinical orders
FHIR-compliant error responses with structured guidance for clinical clarification
REFACTOR-009C: Updated to use unified validation models
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from .validation_common import (
    ValidationSeverity, ValidationCode,
    ValidationIssue as BaseValidationIssue,
    UnifiedValidationResult,
    create_validation_issue, create_validation_result
)

logger = logging.getLogger(__name__)


@dataclass
class ClinicalValidationIssue(BaseValidationIssue):
    """Extended validation issue with clinical-specific fields"""
    guidance: Optional[str] = None
    fhir_impact: Optional[str] = None
    detected_pattern: Optional[str] = None
    suggested_fix: Optional[str] = None
    requires_clarification: bool = True


@dataclass
class ClinicalValidationResult:
    """Clinical validation result with FHIR OperationOutcome support"""
    unified_result: UnifiedValidationResult
    can_process_fhir: bool
    processing_recommendation: str
    escalation_required: bool

    @property
    def is_valid(self) -> bool:
        """Delegate to unified result"""
        return self.unified_result.is_valid

    @property
    def issues(self) -> List[ClinicalValidationIssue]:
        """Return issues as clinical validation issues

        Note: Only returns issues that are ClinicalValidationIssue instances.
        For all issues, access unified_result.issues directly.
        """
        return [issue for issue in self.unified_result.issues if isinstance(issue, ClinicalValidationIssue)]

    @property
    def all_issues(self) -> List[BaseValidationIssue]:
        """Return all issues including base validation issues"""
        return self.unified_result.issues

    @property
    def confidence(self) -> float:
        """Delegate to unified result confidence score"""
        return self.unified_result.confidence_score

    def to_fhir_operation_outcome(self) -> Dict[str, Any]:
        """Convert to FHIR OperationOutcome response

        Only includes ClinicalValidationIssue instances which have the extended
        fields needed for proper FHIR OperationOutcome generation.
        """
        fhir_issues = []

        for issue in self.unified_result.issues:
            if isinstance(issue, ClinicalValidationIssue):
                # Direct attribute access for ClinicalValidationIssue
                diagnostics_parts = []
                if issue.guidance:
                    diagnostics_parts.append(issue.guidance)
                if issue.fhir_impact:
                    diagnostics_parts.append(f"FHIR Impact: {issue.fhir_impact}")

                fhir_issue = {
                    "severity": issue.severity.value,
                    "code": "processing",
                    "details": {
                        "coding": [
                            {
                                "system": "http://nl-fhir.com/validation-codes",
                                "code": issue.code.value,
                                "display": issue.message
                            }
                        ]
                    },
                    "diagnostics": " | ".join(diagnostics_parts) if diagnostics_parts else issue.message
                }

                # Only add expression if detected_pattern exists
                if issue.detected_pattern:
                    fhir_issue["expression"] = [issue.detected_pattern]

                fhir_issues.append(fhir_issue)
            else:
                # Fallback for base ValidationIssue instances
                fhir_issues.append({
                    "severity": issue.severity.value,
                    "code": "processing",
                    "details": {
                        "coding": [
                            {
                                "system": "http://nl-fhir.com/validation-codes",
                                "code": issue.code.value,
                                "display": issue.message
                            }
                        ]
                    },
                    "diagnostics": issue.message
                })

        return {
            "resourceType": "OperationOutcome",
            "issue": fhir_issues
        }

    def to_legacy_dict(self) -> Dict[str, Any]:
        """Convert to legacy dict format for backward compatibility"""
        base_dict = self.unified_result.to_legacy_dict()

        # Add clinical-specific fields
        base_dict.update({
            "can_process_fhir": self.can_process_fhir,
            "processing_recommendation": self.processing_recommendation,
            "escalation_required": self.escalation_required,
            "confidence": self.confidence  # Alias for confidence_score
        })

        return base_dict


def create_clinical_validation_issue(
    severity: ValidationSeverity,
    code: ValidationCode,
    message: str,
    guidance: str = "",
    fhir_impact: str = "",
    detected_pattern: Optional[str] = None,
    suggested_fix: Optional[str] = None,
    requires_clarification: bool = True,
    **kwargs
) -> ClinicalValidationIssue:
    """Create clinical validation issue with extended fields"""
    # Filter kwargs to only include base ValidationIssue fields
    base_kwargs = {k: v for k, v in kwargs.items()
                   if k in ['context', 'suggestions', 'resource_type', 'field', 'location']}

    base_issue = create_validation_issue(severity, code, message, **base_kwargs)

    return ClinicalValidationIssue(
        severity=base_issue.severity,
        code=base_issue.code,
        message=base_issue.message,
        context=base_issue.context,
        suggestions=base_issue.suggestions,
        resource_type=base_issue.resource_type,
        field=base_issue.field,
        location=base_issue.location,
        guidance=guidance,
        fhir_impact=fhir_impact,
        detected_pattern=detected_pattern,
        suggested_fix=suggested_fix,
        requires_clarification=requires_clarification
    )


class ClinicalOrderValidator:
    """Comprehensive clinical order validation system"""
    
    def __init__(self):
        self.conditional_patterns = [
            r'\bif\b.*(?:high|low|positive|negative|develops|worsens|persists)',
            r'\bunless\b.*(?:contraindicated|refuses|agrees|develops)',
            r'\bdepending on\b.*(?:availability|insurance|response|tolerance)',
            r'\bper\b.*(?:discretion|judgment|response|tolerance)',
            r'\bbased on\b.*(?:weight|labs|creatinine|bp|response)'
        ]
        
        self.ambiguity_patterns = [
            r'\bmaybe\b.*\bor\b',
            r'\beither\b.*\bor\b',
            r'\bwhichever\b.*(?:covers|works|available|approved)',
            r'\bsomething for\b',
            r'\bappropriate\b.*(?:treatment|medication|therapy)',
            r'\bper protocol\b',
            r'\bstanding orders\b'
        ]
        
        self.incomplete_patterns = [
            r'\btbd\b|\bto be determined\b',
            r'\bdose unclear\b|\bdosage unclear\b',
            r'\bfrequency not stated\b|\btiming unclear\b',
            r'\bagent unclear\b|\bmedication undecided\b',
            r'\bstrength not specified\b|\bconcentration missing\b'
        ]
        
        self.vague_intent_patterns = [
            r'\bpain control\b(?!\s+with\s+\w+)',
            r'\bcomfort care\b(?!\s+with\s+\w+)',
            r'\bsedation\b(?!\s+with\s+\w+)',
            r'\bantibiotic\b(?!\s+\w+)',
            r'\bsomething for\b.*(?:pain|anxiety|thyroid|infection)',
            r'\bstart\b.*(?:meds|medication)(?!\s+\w+)'
        ]

    def validate_clinical_order(self, clinical_text: str, request_id: Optional[str] = None) -> ClinicalValidationResult:
        """Main validation entry point"""

        logger.info(f"[{request_id}] Validating clinical order: {clinical_text[:100]}...")

        issues = []
        text_lower = clinical_text.lower()

        # 1. Detect conditional logic (CRITICAL - cannot encode in FHIR)
        conditional_issues = self._detect_conditional_logic(clinical_text, text_lower)
        issues.extend(conditional_issues)

        # 2. Detect medication ambiguity (CRITICAL - FHIR requires single medication)
        ambiguity_issues = self._detect_medication_ambiguity(clinical_text, text_lower)
        issues.extend(ambiguity_issues)

        # 3. Detect missing critical fields (ERROR - FHIR required fields)
        missing_field_issues = self._detect_missing_fields(clinical_text, text_lower)
        issues.extend(missing_field_issues)

        # 4. Detect protocol dependencies (ERROR - cannot resolve externally)
        protocol_issues = self._detect_protocol_dependencies(clinical_text, text_lower)
        issues.extend(protocol_issues)

        # 5. Detect vague intent (WARNING - insufficient specificity)
        vague_issues = self._detect_vague_intent(clinical_text, text_lower)
        issues.extend(vague_issues)

        # 6. Clinical safety validation
        safety_issues = self._detect_safety_concerns(clinical_text, text_lower)
        issues.extend(safety_issues)

        # Calculate overall validation result
        validation_result = self._calculate_validation_result(issues, clinical_text)

        logger.info(f"[{request_id}] Validation complete: {len(issues)} issues found, can_process_fhir={validation_result.can_process_fhir}")

        return validation_result
    
    def _detect_conditional_logic(self, text: str, text_lower: str) -> List[ClinicalValidationIssue]:
        """Detect conditional logic that cannot be encoded in FHIR"""

        issues = []

        for pattern in self.conditional_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                issues.append(create_clinical_validation_issue(
                    severity=ValidationSeverity.FATAL,
                    code=ValidationCode.CONDITIONAL_LOGIC,
                    message="Order contains conditional logic that cannot be encoded in FHIR MedicationRequest",
                    guidance="Please specify discrete medication, dosage, and timing without conditional logic",
                    fhir_impact="FHIR MedicationRequest cannot encode if/unless/depending conditions",
                    detected_pattern=pattern,
                    suggested_fix="Create separate orders for each condition or specify single concrete order",
                    requires_clarification=True
                ))
                break  # Don't duplicate for multiple pattern matches

        return issues
    
    def _detect_medication_ambiguity(self, text: str, text_lower: str) -> List[ClinicalValidationIssue]:
        """Detect multiple medication options or unclear medication selection"""

        issues = []

        # Check for explicit multiple options
        for pattern in self.ambiguity_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                issues.append(create_clinical_validation_issue(
                    severity=ValidationSeverity.FATAL,
                    code=ValidationCode.MEDICATION_AMBIGUITY,
                    message="Multiple medication options detected - FHIR requires single medication choice",
                    guidance="Please specify single medication with exact name, strength, and formulation",
                    fhir_impact="Cannot populate medicationCodeableConcept with multiple options",
                    detected_pattern=pattern,
                    suggested_fix="Choose one specific medication (e.g., 'metoprolol 50mg' not 'maybe metoprolol or atenolol')",
                    requires_clarification=True
                ))
                break

        # Check for medication class without specific drug
        class_patterns = [
            r'\b(?:beta blocker|ace inhibitor|statin|ppi|nsaid|ssri|antibiotic|diuretic)\b'
        ]

        for pattern in class_patterns:
            if re.search(pattern, text_lower) and not self._has_specific_medication(text_lower):
                issues.append(create_clinical_validation_issue(
                    severity=ValidationSeverity.ERROR,
                    code=ValidationCode.MISSING_MEDICATION,
                    message="Medication class specified but no specific drug identified",
                    guidance="Please specify exact medication name (e.g., 'lisinopril 10mg' not 'ACE inhibitor')",
                    fhir_impact="Cannot populate medicationCodeableConcept without specific drug name",
                    detected_pattern=pattern,
                    suggested_fix="Replace medication class with specific drug name and strength",
                    requires_clarification=True
                ))
                break

        return issues
    
    def _detect_missing_fields(self, text: str, text_lower: str) -> List[ClinicalValidationIssue]:
        """Detect missing critical FHIR required fields"""

        issues = []

        # Check for incomplete dosing information
        for pattern in self.incomplete_patterns:
            if re.search(pattern, text_lower):
                if 'tbd' in pattern or 'unclear' in pattern:
                    if 'dose' in pattern or 'dosage' in pattern:
                        issues.append(create_clinical_validation_issue(
                            severity=ValidationSeverity.ERROR,
                            code=ValidationCode.MISSING_DOSAGE,
                            message="Dosage information missing or unclear",
                            guidance="Please specify exact dose with units (e.g., '20mg', '1 tablet', '5ml')",
                            fhir_impact="Cannot populate dosageInstruction.doseQuantity without numeric dose",
                            detected_pattern=pattern,
                            suggested_fix="Add specific dosage amount with units",
                            requires_clarification=True
                        ))
                    elif 'frequency' in pattern or 'timing' in pattern:
                        issues.append(create_clinical_validation_issue(
                            severity=ValidationSeverity.ERROR,
                            code=ValidationCode.MISSING_FREQUENCY,
                            message="Frequency or timing information missing",
                            guidance="Please specify frequency (e.g., 'twice daily', 'every 6 hours', 'as needed')",
                            fhir_impact="Cannot populate dosageInstruction.timing without frequency",
                            detected_pattern=pattern,
                            suggested_fix="Add specific frequency or timing instructions",
                            requires_clarification=True
                        ))
                    elif 'agent' in pattern or 'medication' in pattern:
                        issues.append(create_clinical_validation_issue(
                            severity=ValidationSeverity.FATAL,
                            code=ValidationCode.MISSING_MEDICATION,
                            message="Medication name missing or undecided",
                            guidance="Please specify exact medication name",
                            fhir_impact="Cannot create MedicationRequest without medication identifier",
                            detected_pattern=pattern,
                            suggested_fix="Specify exact medication name",
                            requires_clarification=True
                        ))

        return issues
    
    def _detect_protocol_dependencies(self, text: str, text_lower: str) -> List[ClinicalValidationIssue]:
        """Detect references to external protocols or standing orders"""

        issues = []

        protocol_patterns = [
            r'\bper protocol\b',
            r'\bstanding orders\b',
            r'\bnursing protocol\b',
            r'\bhospice protocol\b',
            r'\bper discretion\b',
            r'\bper judgment\b'
        ]

        for pattern in protocol_patterns:
            if re.search(pattern, text_lower):
                issues.append(create_clinical_validation_issue(
                    severity=ValidationSeverity.ERROR,
                    code=ValidationCode.PROTOCOL_REFERENCE,
                    message="Order references external protocol or clinical discretion",
                    guidance="Please specify discrete medication orders instead of protocol references",
                    fhir_impact="Cannot resolve external protocols into specific FHIR resources",
                    detected_pattern=pattern,
                    suggested_fix="Replace protocol reference with specific medication orders",
                    requires_clarification=True
                ))
                break

        return issues
    
    def _detect_vague_intent(self, text: str, text_lower: str) -> List[ClinicalValidationIssue]:
        """Detect vague clinical intent without specific orders"""

        issues = []

        for pattern in self.vague_intent_patterns:
            if re.search(pattern, text_lower):
                issues.append(create_clinical_validation_issue(
                    severity=ValidationSeverity.WARNING,
                    code=ValidationCode.VAGUE_INTENT,
                    message="Clinical intent unclear - insufficient specificity for FHIR encoding",
                    guidance="Please provide specific medication name, dose, and frequency",
                    fhir_impact="Cannot create specific FHIR resources from general clinical intent",
                    detected_pattern=pattern,
                    suggested_fix="Replace general intent with specific medication orders",
                    requires_clarification=True
                ))
                break

        return issues
    
    def _detect_safety_concerns(self, text: str, text_lower: str) -> List[ClinicalValidationIssue]:
        """Detect clinical safety concerns that need attention"""

        issues = []

        # Check for contraindication logic mixed with orders
        contraindication_patterns = [
            r'\bavoid if\b.*(?:hypertensive|cardiac|renal|hepatic)',
            r'\bcontraindicated if\b',
            r'\bunless contraindicated\b'
        ]

        for pattern in contraindication_patterns:
            if re.search(pattern, text_lower):
                issues.append(create_clinical_validation_issue(
                    severity=ValidationSeverity.WARNING,
                    code=ValidationCode.CONTRAINDICATION_LOGIC,
                    message="Contraindication logic detected within order",
                    guidance="Consider separating medication order from contraindication checking",
                    fhir_impact="FHIR MedicationRequest cannot encode contraindication logic directly",
                    detected_pattern=pattern,
                    suggested_fix="Create separate clinical decision support rules for contraindications",
                    requires_clarification=False
                ))
                break

        return issues
    
    def _has_specific_medication(self, text_lower: str) -> bool:
        """Check if text contains a specific medication name"""
        
        # Common medication names (subset for validation)
        specific_meds = [
            'metoprolol', 'atenolol', 'lisinopril', 'amlodipine', 'simvastatin',
            'omeprazole', 'lansoprazole', 'ibuprofen', 'acetaminophen', 'aspirin',
            'fluoxetine', 'sertraline', 'amoxicillin', 'azithromycin', 'ciprofloxacin'
        ]
        
        return any(med in text_lower for med in specific_meds)
    
    def _calculate_validation_result(self, issues: List[ClinicalValidationIssue], clinical_text: str) -> ClinicalValidationResult:
        """Calculate overall validation result"""

        # Count issues by severity
        fatal_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.FATAL)
        error_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.ERROR)
        warning_count = sum(1 for issue in issues if issue.severity == ValidationSeverity.WARNING)

        # Determine if can process
        is_valid = fatal_count == 0 and error_count == 0
        can_process_fhir = fatal_count == 0 and error_count <= 1  # Allow some errors with warnings

        # Calculate confidence (inverse of issue severity)
        if fatal_count > 0:
            confidence = 0.0
        elif error_count > 0:
            confidence = 0.3
        elif warning_count > 0:
            confidence = 0.7
        else:
            confidence = 1.0

        # Processing recommendation
        if fatal_count > 0:
            processing_recommendation = "REJECT - Cannot process due to critical issues requiring clarification"
        elif error_count > 2:
            processing_recommendation = "ESCALATE - Multiple errors require clinical review"
        elif error_count > 0:
            processing_recommendation = "PROCESS_WITH_WARNINGS - Can attempt FHIR creation with limitations"
        else:
            processing_recommendation = "PROCESS - Can create valid FHIR resources"

        escalation_required = fatal_count > 0 or error_count > 1

        # Create unified validation result
        unified_result = create_validation_result(
            is_valid=is_valid,
            validator_name="clinical_validator",
            issues=issues,
            confidence_score=confidence,
            safety_level="high_risk" if fatal_count > 0 else "moderate_risk" if error_count > 0 else "standard"
        )

        return ClinicalValidationResult(
            unified_result=unified_result,
            can_process_fhir=can_process_fhir,
            processing_recommendation=processing_recommendation,
            escalation_required=escalation_required
        )


# Global validator instance
clinical_validator = ClinicalOrderValidator()


def validate_clinical_order(clinical_text: str, request_id: Optional[str] = None) -> ClinicalValidationResult:
    """Main validation function for clinical orders"""
    return clinical_validator.validate_clinical_order(clinical_text, request_id)


# Backward compatibility wrapper
def validate_clinical_order_legacy(clinical_text: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    """Legacy validation function returning dict format for backward compatibility"""
    result = clinical_validator.validate_clinical_order(clinical_text, request_id)
    return result.to_legacy_dict()


def get_validation_summary() -> Dict[str, Any]:
    """Get validation system summary and capabilities"""
    return {
        "validation_categories": [
            "Conditional Logic Detection",
            "Medication Ambiguity Detection",
            "Missing Critical Fields",
            "Protocol Dependencies",
            "Vague Intent Detection",
            "Clinical Safety Concerns"
        ],
        "fhir_compliance": "FHIR R4 OperationOutcome responses",
        "severity_levels": ["fatal", "error", "warning", "information"],
        "escalation_triggers": [
            "Fatal validation errors",
            "Multiple error conditions",
            "Clinical safety concerns"
        ]
    }


# ====================================================================================
# BACKWARD COMPATIBILITY ALIASES
# ====================================================================================

# For modules that import the old class names (e.g., error_handler.py)
ValidationResult = ClinicalValidationResult  # Backward compatibility alias
ValidationIssue = ClinicalValidationIssue    # Backward compatibility alias

# Note: ValidationSeverity and ValidationCode are now imported from validation_common