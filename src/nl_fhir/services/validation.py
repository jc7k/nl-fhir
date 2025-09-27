"""
Clinical Input Validation Service
HIPAA Compliant: No PHI in validation logic or logs  
Medical Safety: Comprehensive input validation and safety checks
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from .validation_common import ValidationPatterns

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for comprehensive clinical input validation"""

    def __init__(self):
        # Use consolidated patterns from validation_common
        self.medication_patterns = ValidationPatterns.get_all_medication_patterns()
        self.lab_patterns = ValidationPatterns.LAB_TEST_PATTERNS
        self.procedure_patterns = ValidationPatterns.PROCEDURE_PATTERNS
        self.high_risk_patterns = ValidationPatterns.get_high_risk_regex_patterns()
    
    def validate_clinical_text_comprehensive(self, text: str, request_id: str) -> Dict[str, Any]:
        """
        Comprehensive clinical text validation
        Returns detailed validation results with safety assessments
        """
        validation_result = {
            "is_valid": True,
            "confidence_score": 1.0,
            "safety_level": "standard",
            "warnings": [],
            "errors": [],
            "suggestions": [],
            "detected_categories": [],
            "risk_assessment": {}
        }
        
        try:
            # Basic format validation
            self._validate_basic_format(text, validation_result)
            
            # Content category detection
            self._detect_clinical_categories(text, validation_result)
            
            # Safety assessment
            self._assess_clinical_safety(text, validation_result)
            
            # Completeness validation
            self._validate_clinical_completeness(text, validation_result)
            
            # Risk level assessment
            self._assess_risk_level(text, validation_result, request_id)
            
            # Calculate final validation score
            self._calculate_validation_score(validation_result)
            
            # Log validation summary (no PHI)
            logger.info(f"Request {request_id}: Clinical validation completed - "
                       f"score={validation_result['confidence_score']:.2f}, "
                       f"safety={validation_result['safety_level']}, "
                       f"categories={len(validation_result['detected_categories'])}")
            
        except Exception as e:
            logger.error(f"Request {request_id}: Validation error - {type(e).__name__}")
            validation_result.update({
                "is_valid": False,
                "confidence_score": 0.0,
                "errors": ["Internal validation error occurred"]
            })
        
        return validation_result
    
    def _validate_basic_format(self, text: str, result: Dict[str, Any]):
        """Basic format and structure validation"""
        text_length = len(text.strip())
        
        # Length validation
        if text_length < 5:
            result["errors"].append("Clinical text too short")
            result["is_valid"] = False
        elif text_length < 15:
            result["warnings"].append("Clinical text is very brief")
            result["suggestions"].append("Consider providing more clinical detail")
        elif text_length > 3000:
            result["warnings"].append("Clinical text is very long")
            result["suggestions"].append("Consider breaking into multiple orders")
        
        # Character validation
        if not re.search(r'[a-zA-Z]', text):
            result["errors"].append("Clinical text must contain alphabetic characters")
            result["is_valid"] = False
        
        # Check for excessive repetition (potential input error)
        words = text.lower().split()
        if len(words) > 0:
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Only check meaningful words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Flag if any word appears more than 30% of total words
            max_repetition = max(word_freq.values()) if word_freq else 0
            if max_repetition > len(words) * 0.3:
                result["warnings"].append("Excessive word repetition detected")
                result["suggestions"].append("Review input for potential errors")
    
    def _detect_clinical_categories(self, text: str, result: Dict[str, Any]):
        """Detect clinical order categories"""
        text_lower = text.lower()
        categories = []
        
        # Medication orders
        if any(re.search(pattern, text_lower) for pattern in self.medication_patterns):
            categories.append("medication")
            result["suggestions"].append("Medication order detected - verify dosage, frequency, and route")
        
        # Laboratory orders  
        if any(re.search(pattern, text_lower) for pattern in self.lab_patterns):
            categories.append("laboratory")
            result["suggestions"].append("Laboratory order detected - verify specimen type and timing")
        
        # Procedure orders
        if any(re.search(pattern, text_lower) for pattern in self.procedure_patterns):
            categories.append("procedure")
            result["suggestions"].append("Procedure order detected - verify scheduling and preparation")
        
        # Diagnostic imaging
        if re.search(r'\b(x-?ray|ct|mri|ultrasound|scan)\b', text_lower):
            categories.append("imaging")
            result["suggestions"].append("Imaging order detected - verify anatomical area and contrast needs")
        
        result["detected_categories"] = categories
        
        # Category validation
        if not categories:
            result["warnings"].append("No specific clinical category detected")
            result["suggestions"].append("Specify if this is a medication, lab, procedure, or other order type")
    
    def _assess_clinical_safety(self, text: str, result: Dict[str, Any]):
        """Assess clinical safety indicators"""
        text_lower = text.lower()
        safety_flags = []
        
        # High-risk medication patterns
        high_risk_found = []
        for pattern in self.high_risk_patterns:
            if re.search(pattern, text_lower):
                high_risk_found.append(pattern.replace('\\b', '').replace('\\', ''))
        
        if high_risk_found:
            safety_flags.append("high_risk_medications")
            result["warnings"].append(f"High-risk medication patterns detected")
            result["suggestions"].append("Verify dosing and monitoring requirements for high-risk medications")
            result["safety_level"] = "high_risk"
        
        # Dosage validation for medications
        if "medication" in result.get("detected_categories", []):
            # Look for dosage patterns
            dosage_pattern = re.search(r'\b(\d+(?:\.\d+)?)\s*(mg|ml|g|units?)\b', text_lower)
            frequency_pattern = re.search(r'\b(daily|bid|tid|qid|twice|three times|four times)\b', text_lower)
            
            if dosage_pattern and not frequency_pattern:
                result["warnings"].append("Dosage specified but frequency unclear")
                result["suggestions"].append("Specify dosing frequency (daily, twice daily, etc.)")
            elif frequency_pattern and not dosage_pattern:
                result["warnings"].append("Frequency specified but dosage unclear")
                result["suggestions"].append("Specify medication dosage (mg, ml, etc.)")
        
        # Allergy/contraindication warnings
        if re.search(r'\b(allerg|contraindic|avoid)\b', text_lower):
            safety_flags.append("allergy_noted")
            result["warnings"].append("Allergy or contraindication mentioned")
            result["suggestions"].append("Verify allergy status and medication compatibility")
        
        result["risk_assessment"]["safety_flags"] = safety_flags
    
    def _validate_clinical_completeness(self, text: str, result: Dict[str, Any]):
        """Validate clinical completeness"""
        text_lower = text.lower()
        completeness_score = 1.0
        
        # For medication orders, check completeness
        if "medication" in result.get("detected_categories", []):
            required_elements = {
                "medication_name": bool(re.search(r'\b[a-z]+(?:cillin|mycin|prine|olol|statin)\b', text_lower)),
                "dosage": bool(re.search(r'\b\d+\s*(mg|ml|g|units?)\b', text_lower)),
                "frequency": bool(re.search(r'\b(daily|bid|tid|qid|twice|once|every)\b', text_lower)),
                "route": bool(re.search(r'\b(oral|po|iv|im|topical|sublingual)\b', text_lower))
            }
            
            missing_elements = [k for k, v in required_elements.items() if not v]
            completeness_score = (len(required_elements) - len(missing_elements)) / len(required_elements)
            
            if missing_elements:
                result["warnings"].append(f"Medication order missing: {', '.join(missing_elements)}")
                result["suggestions"].append("Ensure medication orders include drug name, dosage, frequency, and route")
        
        # For lab orders, check specimen and timing
        if "laboratory" in result.get("detected_categories", []):
            has_specimen = bool(re.search(r'\b(blood|urine|stool|sputum|csf)\b', text_lower))
            has_timing = bool(re.search(r'\b(stat|urgent|routine|fasting|morning)\b', text_lower))
            
            if not has_specimen:
                result["suggestions"].append("Specify specimen type for laboratory orders")
                completeness_score *= 0.8
            
            if not has_timing:
                result["suggestions"].append("Consider specifying timing/priority for laboratory orders")
                completeness_score *= 0.9
        
        result["risk_assessment"]["completeness_score"] = completeness_score
    
    def _assess_risk_level(self, text: str, result: Dict[str, Any], request_id: str):
        """Assess overall clinical risk level"""
        risk_factors = []
        
        # High-risk medications
        if result["risk_assessment"].get("safety_flags", []):
            risk_factors.extend(result["risk_assessment"]["safety_flags"])
        
        # Complex orders (multiple medications/procedures)
        categories = result.get("detected_categories", [])
        if len(categories) > 2:
            risk_factors.append("complex_multi_category_order")
        
        # Incomplete orders
        completeness = result["risk_assessment"].get("completeness_score", 1.0)
        if completeness < 0.7:
            risk_factors.append("incomplete_order")
        
        # Determine risk level
        if "high_risk_medications" in risk_factors or len(risk_factors) >= 3:
            result["safety_level"] = "high_risk"
            logger.warning(f"Request {request_id}: High-risk clinical order detected")
        elif len(risk_factors) >= 1:
            result["safety_level"] = "moderate_risk"
        else:
            result["safety_level"] = "standard"
        
        result["risk_assessment"]["risk_factors"] = risk_factors
        result["risk_assessment"]["total_risk_factors"] = len(risk_factors)
    
    def _calculate_validation_score(self, result: Dict[str, Any]):
        """Calculate final validation confidence score"""
        base_score = 1.0
        
        # Deduct for errors and warnings
        base_score -= len(result.get("errors", [])) * 0.3
        base_score -= len(result.get("warnings", [])) * 0.1
        
        # Factor in completeness
        completeness = result["risk_assessment"].get("completeness_score", 1.0)
        base_score = base_score * (0.7 + completeness * 0.3)
        
        # Factor in category detection (higher score for clear categorization)
        categories = len(result.get("detected_categories", []))
        if categories > 0:
            base_score = base_score * (0.9 + min(categories * 0.05, 0.1))
        else:
            base_score *= 0.8
        
        # Ensure score is within bounds
        result["confidence_score"] = max(0.0, min(1.0, base_score))
        result["is_valid"] = result["confidence_score"] >= 0.6 and len(result.get("errors", [])) == 0
    
    def validate_patient_reference(self, patient_ref: Optional[str]) -> Tuple[bool, List[str]]:
        """
        Validate patient reference format and safety
        Returns (is_valid, error_messages)
        """
        if not patient_ref:
            return True, []  # Optional field
        
        errors = []
        
        # Length validation
        if len(patient_ref) > 100:
            errors.append("Patient reference too long")
        
        # Format validation (alphanumeric, dash, underscore only)
        if not re.match(r'^[A-Za-z0-9\-_]+$', patient_ref):
            errors.append("Patient reference contains invalid characters")
        
        # Check for potential PHI patterns (basic check)
        if re.search(r'\b\d{3}-?\d{2}-?\d{4}\b', patient_ref):  # SSN pattern
            errors.append("Patient reference may contain PHI - use system identifier only")
        
        return len(errors) == 0, errors