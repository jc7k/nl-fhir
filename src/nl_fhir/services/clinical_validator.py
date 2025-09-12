"""
Clinical Order Validation System
Comprehensive error detection for ambiguous, incomplete, and problematic clinical orders
FHIR-compliant error responses with structured guidance for clinical clarification
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """FHIR-compliant validation severity levels"""
    FATAL = "fatal"      # Cannot process at all
    ERROR = "error"      # Missing required fields
    WARNING = "warning"  # Suboptimal but processable
    INFO = "information" # Advisory information


class ValidationCode(str, Enum):
    """Structured validation error codes"""
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
    
    # FHIR compliance issues
    FHIR_REQUIRED_FIELD = "FHIR_REQUIRED_FIELD"
    FHIR_ENCODING_IMPOSSIBLE = "FHIR_ENCODING_IMPOSSIBLE"
    FHIR_RESOURCE_INCOMPLETE = "FHIR_RESOURCE_INCOMPLETE"


@dataclass
class ValidationIssue:
    """Structured validation issue with FHIR compliance"""
    severity: ValidationSeverity
    code: ValidationCode
    message: str
    guidance: str
    fhir_impact: str
    detected_pattern: Optional[str] = None
    suggested_fix: Optional[str] = None
    requires_clarification: bool = True


@dataclass
class ValidationResult:
    """Complete validation result for clinical order"""
    is_valid: bool
    can_process_fhir: bool
    issues: List[ValidationIssue]
    confidence: float
    processing_recommendation: str
    escalation_required: bool
    
    def to_fhir_operation_outcome(self) -> Dict[str, Any]:
        """Convert to FHIR OperationOutcome response"""
        return {
            "resourceType": "OperationOutcome",
            "issue": [
                {
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
                    "diagnostics": f"{issue.guidance} | FHIR Impact: {issue.fhir_impact}",
                    "expression": [issue.detected_pattern] if issue.detected_pattern else []
                }
                for issue in self.issues
            ]
        }


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

    def validate_clinical_order(self, clinical_text: str, request_id: Optional[str] = None) -> ValidationResult:
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
    
    def _detect_conditional_logic(self, text: str, text_lower: str) -> List[ValidationIssue]:
        """Detect conditional logic that cannot be encoded in FHIR"""
        
        issues = []
        
        for pattern in self.conditional_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                issues.append(ValidationIssue(
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
    
    def _detect_medication_ambiguity(self, text: str, text_lower: str) -> List[ValidationIssue]:
        """Detect multiple medication options or unclear medication selection"""
        
        issues = []
        
        # Check for explicit multiple options
        for pattern in self.ambiguity_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                issues.append(ValidationIssue(
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
                issues.append(ValidationIssue(
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
    
    def _detect_missing_fields(self, text: str, text_lower: str) -> List[ValidationIssue]:
        """Detect missing critical FHIR required fields"""
        
        issues = []
        
        # Check for incomplete dosing information
        for pattern in self.incomplete_patterns:
            if re.search(pattern, text_lower):
                if 'tbd' in pattern or 'unclear' in pattern:
                    if 'dose' in pattern or 'dosage' in pattern:
                        issues.append(ValidationIssue(
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
                        issues.append(ValidationIssue(
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
                        issues.append(ValidationIssue(
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
    
    def _detect_protocol_dependencies(self, text: str, text_lower: str) -> List[ValidationIssue]:
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
                issues.append(ValidationIssue(
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
    
    def _detect_vague_intent(self, text: str, text_lower: str) -> List[ValidationIssue]:
        """Detect vague clinical intent without specific orders"""
        
        issues = []
        
        for pattern in self.vague_intent_patterns:
            if re.search(pattern, text_lower):
                issues.append(ValidationIssue(
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
    
    def _detect_safety_concerns(self, text: str, text_lower: str) -> List[ValidationIssue]:
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
                issues.append(ValidationIssue(
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
    
    def _calculate_validation_result(self, issues: List[ValidationIssue], clinical_text: str) -> ValidationResult:
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
        
        return ValidationResult(
            is_valid=is_valid,
            can_process_fhir=can_process_fhir,
            issues=issues,
            confidence=confidence,
            processing_recommendation=processing_recommendation,
            escalation_required=escalation_required
        )


# Global validator instance
clinical_validator = ClinicalOrderValidator()


def validate_clinical_order(clinical_text: str, request_id: Optional[str] = None) -> ValidationResult:
    """Main validation function for clinical orders"""
    return clinical_validator.validate_clinical_order(clinical_text, request_id)


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