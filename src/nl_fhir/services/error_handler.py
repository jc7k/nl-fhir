"""
FHIR-Compliant Error Response Framework
Handles clinical validation errors with structured responses and escalation workflows
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from .clinical_validator import ValidationResult, ValidationSeverity, ValidationCode

logger = logging.getLogger(__name__)


class EscalationLevel(str, Enum):
    """Escalation levels for clinical review"""
    NONE = "none"                    # Can process automatically
    CLINICAL_REVIEW = "clinical_review"    # Needs clinical clarification
    SAFETY_REVIEW = "safety_review"        # Needs safety assessment
    REJECT = "reject"                      # Cannot process safely


class ErrorResponseHandler:
    """Handles error responses and escalation workflows for clinical validation"""
    
    def __init__(self):
        self.escalation_rules = {
            ValidationSeverity.FATAL: EscalationLevel.REJECT,
            ValidationSeverity.ERROR: EscalationLevel.CLINICAL_REVIEW,
            ValidationSeverity.WARNING: EscalationLevel.CLINICAL_REVIEW,
            ValidationSeverity.INFO: EscalationLevel.NONE
        }
    
    def create_error_response(self, validation_result: ValidationResult, 
                            request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create comprehensive error response with FHIR compliance and guidance"""
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        escalation_level = self._determine_escalation_level(validation_result)
        
        # Create main response structure
        response = {
            "status": "validation_failed" if not validation_result.can_process_fhir else "validation_warnings",
            "timestamp": timestamp,
            "request_id": request_id,
            "can_process_fhir": validation_result.can_process_fhir,
            "confidence": validation_result.confidence,
            "processing_recommendation": validation_result.processing_recommendation,
            
            # Escalation information
            "escalation": {
                "level": escalation_level.value,
                "required": validation_result.escalation_required,
                "next_steps": self._get_escalation_guidance(escalation_level)
            },
            
            # Issue summary
            "validation_summary": {
                "total_issues": len(validation_result.issues),
                "fatal_issues": self._count_by_severity(validation_result.issues, ValidationSeverity.FATAL),
                "error_issues": self._count_by_severity(validation_result.issues, ValidationSeverity.ERROR),
                "warning_issues": self._count_by_severity(validation_result.issues, ValidationSeverity.WARNING)
            },
            
            # Detailed issues with guidance
            "issues": [
                {
                    "severity": issue.severity.value,
                    "code": issue.code.value,
                    "message": issue.message,
                    "guidance": issue.guidance,
                    "fhir_impact": issue.fhir_impact,
                    "suggested_fix": issue.suggested_fix,
                    "requires_clarification": issue.requires_clarification,
                    "detected_pattern": issue.detected_pattern
                }
                for issue in validation_result.issues
            ],
            
            # Clinical guidance
            "clinical_guidance": self._generate_clinical_guidance(validation_result),
            
            # FHIR OperationOutcome
            "fhir_operation_outcome": validation_result.to_fhir_operation_outcome()
        }
        
        # Add escalation-specific information
        if escalation_level != EscalationLevel.NONE:
            response["escalation_details"] = self._create_escalation_details(validation_result, escalation_level)
            
        return response
    
    def _determine_escalation_level(self, validation_result: ValidationResult) -> EscalationLevel:
        """Determine appropriate escalation level based on validation results"""
        
        # Check for fatal issues first
        fatal_issues = [i for i in validation_result.issues if i.severity == ValidationSeverity.FATAL]
        if fatal_issues:
            # Check if fatal issues are safety-related
            safety_codes = [ValidationCode.CONTRAINDICATION_LOGIC, ValidationCode.CONDITIONAL_SAFETY]
            if any(issue.code in safety_codes for issue in fatal_issues):
                return EscalationLevel.SAFETY_REVIEW
            return EscalationLevel.REJECT
        
        # Check for multiple errors
        error_issues = [i for i in validation_result.issues if i.severity == ValidationSeverity.ERROR]
        if len(error_issues) > 2:
            return EscalationLevel.CLINICAL_REVIEW
        elif len(error_issues) > 0:
            return EscalationLevel.CLINICAL_REVIEW
            
        # Check for safety warnings
        warning_issues = [i for i in validation_result.issues if i.severity == ValidationSeverity.WARNING]
        safety_warnings = [i for i in warning_issues if 'safety' in i.code.value.lower() or 'contraindication' in i.code.value.lower()]
        if safety_warnings:
            return EscalationLevel.SAFETY_REVIEW
            
        return EscalationLevel.NONE
    
    def _get_escalation_guidance(self, escalation_level: EscalationLevel) -> List[str]:
        """Get next steps guidance based on escalation level"""
        
        guidance_map = {
            EscalationLevel.NONE: [
                "Order can be processed automatically",
                "Monitor processing results for quality"
            ],
            EscalationLevel.CLINICAL_REVIEW: [
                "Clinical review required for order clarification",
                "Contact ordering physician for missing information",
                "Specify exact medication, dosage, and timing",
                "Review for clinical appropriateness"
            ],
            EscalationLevel.SAFETY_REVIEW: [
                "Safety review required before processing",
                "Assess contraindications and drug interactions",
                "Verify appropriateness for patient condition",
                "Consider alternative medications if indicated"
            ],
            EscalationLevel.REJECT: [
                "Order cannot be processed due to critical issues",
                "Return to ordering physician for complete rewrite",
                "Ensure all required fields are specified",
                "Remove conditional logic and ambiguous language"
            ]
        }
        
        return guidance_map.get(escalation_level, ["Unknown escalation level"])
    
    def _count_by_severity(self, issues: List, severity: ValidationSeverity) -> int:
        """Count issues by severity level"""
        return sum(1 for issue in issues if issue.severity == severity)
    
    def _generate_clinical_guidance(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Generate comprehensive clinical guidance for resolving issues"""
        
        guidance = {
            "priority_fixes": [],
            "recommended_actions": [],
            "fhir_requirements": [],
            "examples": {}
        }
        
        # Analyze issues for guidance
        for issue in validation_result.issues:
            if issue.severity in [ValidationSeverity.FATAL, ValidationSeverity.ERROR]:
                guidance["priority_fixes"].append({
                    "issue": issue.message,
                    "action": issue.suggested_fix or issue.guidance,
                    "fhir_field": self._get_fhir_field_from_code(issue.code)
                })
        
        # Add general recommendations
        guidance["recommended_actions"] = [
            "Specify complete medication orders with exact drug names",
            "Include all required dosing information (amount, frequency, route)",
            "Avoid conditional logic (if/unless/depending statements)",
            "Use specific medications rather than drug classes",
            "Provide discrete orders rather than protocol references"
        ]
        
        # FHIR-specific requirements
        guidance["fhir_requirements"] = [
            "MedicationRequest requires: medication, dosage, timing",
            "Medication must be codeable (specific drug name)",
            "DosageInstruction must have numeric dose and frequency",
            "Conditional logic cannot be encoded in FHIR resources"
        ]
        
        # Examples of good vs bad orders
        guidance["examples"] = {
            "good_orders": [
                "Start lisinopril 10mg once daily for hypertension",
                "Administer acetaminophen 650mg every 6 hours as needed for pain",
                "Begin omeprazole 20mg twice daily before meals for GERD"
            ],
            "problematic_orders": [
                "Start ACE inhibitor if BP remains high (class not specific drug)",
                "Give something for pain (vague intent)",
                "Maybe metoprolol or atenolol depending on availability (ambiguous choice)"
            ]
        }
        
        return guidance
    
    def _get_fhir_field_from_code(self, code: ValidationCode) -> str:
        """Map validation codes to FHIR fields"""
        
        field_mapping = {
            ValidationCode.MISSING_MEDICATION: "MedicationRequest.medication",
            ValidationCode.MISSING_DOSAGE: "MedicationRequest.dosageInstruction.doseQuantity",
            ValidationCode.MISSING_FREQUENCY: "MedicationRequest.dosageInstruction.timing",
            ValidationCode.MISSING_ROUTE: "MedicationRequest.dosageInstruction.route",
            ValidationCode.MEDICATION_AMBIGUITY: "MedicationRequest.medication",
            ValidationCode.CONDITIONAL_LOGIC: "MedicationRequest (entire resource)",
            ValidationCode.FHIR_REQUIRED_FIELD: "Various required fields"
        }
        
        return field_mapping.get(code, "Unknown field")
    
    def _create_escalation_details(self, validation_result: ValidationResult, 
                                 escalation_level: EscalationLevel) -> Dict[str, Any]:
        """Create detailed escalation information"""
        
        return {
            "escalation_reason": f"Validation issues require {escalation_level.value}",
            "estimated_resolution_time": self._estimate_resolution_time(escalation_level),
            "required_roles": self._get_required_roles(escalation_level),
            "escalation_priority": self._get_escalation_priority(validation_result),
            "contact_information": {
                "clinical_review": "Contact ordering physician or clinical pharmacist",
                "safety_review": "Contact patient safety team or clinical pharmacist",
                "technical_support": "Contact system administrator for processing issues"
            }
        }
    
    def _estimate_resolution_time(self, escalation_level: EscalationLevel) -> str:
        """Estimate time to resolve based on escalation level"""
        
        time_estimates = {
            EscalationLevel.NONE: "Immediate",
            EscalationLevel.CLINICAL_REVIEW: "15-30 minutes",
            EscalationLevel.SAFETY_REVIEW: "30-60 minutes", 
            EscalationLevel.REJECT: "Complete order rewrite required"
        }
        
        return time_estimates.get(escalation_level, "Unknown")
    
    def _get_required_roles(self, escalation_level: EscalationLevel) -> List[str]:
        """Get required roles for escalation resolution"""
        
        role_map = {
            EscalationLevel.NONE: [],
            EscalationLevel.CLINICAL_REVIEW: ["Ordering Physician", "Clinical Pharmacist"],
            EscalationLevel.SAFETY_REVIEW: ["Patient Safety Officer", "Clinical Pharmacist", "Attending Physician"],
            EscalationLevel.REJECT: ["Ordering Physician"]
        }
        
        return role_map.get(escalation_level, [])
    
    def _get_escalation_priority(self, validation_result: ValidationResult) -> str:
        """Determine escalation priority based on validation results"""
        
        fatal_count = self._count_by_severity(validation_result.issues, ValidationSeverity.FATAL)
        error_count = self._count_by_severity(validation_result.issues, ValidationSeverity.ERROR)
        
        if fatal_count > 0:
            return "HIGH"
        elif error_count > 2:
            return "MEDIUM" 
        elif error_count > 0:
            return "LOW"
        else:
            return "NONE"


# Global error handler instance
error_handler = ErrorResponseHandler()


def handle_validation_error(validation_result: ValidationResult, 
                          request_id: Optional[str] = None) -> Dict[str, Any]:
    """Handle validation errors with comprehensive response and escalation"""
    return error_handler.create_error_response(validation_result, request_id)


def get_error_handler_status() -> Dict[str, Any]:
    """Get error handler system status and capabilities"""
    return {
        "escalation_levels": [level.value for level in EscalationLevel],
        "severity_mapping": {
            "fatal": "reject",
            "error": "clinical_review", 
            "warning": "clinical_review",
            "info": "none"
        },
        "fhir_compliance": "FHIR R4 OperationOutcome format",
        "response_components": [
            "Validation summary",
            "Detailed issue analysis",
            "Clinical guidance",
            "Escalation workflows",
            "FHIR-compliant responses"
        ]
    }