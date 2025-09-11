"""
HAPI FHIR Validation Service for Story 3.3
Provides comprehensive bundle validation using HAPI FHIR server
HIPAA Compliant: Secure validation with no PHI exposure
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from .hapi_client import get_hapi_client
from .validator import get_fhir_validator

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """FHIR validation severity levels"""
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class ValidationResult(Enum):
    """Overall validation result status"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class FHIRValidationService:
    """Service for validating FHIR bundles using HAPI FHIR server"""
    
    def __init__(self):
        self.initialized = False
        self.validation_metrics = {
            "total_validations": 0,
            "successful_validations": 0,
            "validation_errors": 0,
            "validation_warnings": 0
        }
        self.cache = {}  # Simple validation cache
        
    async def initialize(self) -> bool:
        """Initialize validation service"""
        try:
            self.hapi_client = await get_hapi_client()
            self.local_validator = await get_fhir_validator()
            
            logger.info("FHIR Validation Service initialized")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize validation service: {e}")
            return False
    
    async def validate_bundle(self, bundle: Dict[str, Any], request_id: Optional[str] = None,
                             use_cache: bool = True) -> Dict[str, Any]:
        """
        Validate FHIR bundle using HAPI FHIR server with fallback to local validation
        
        Args:
            bundle: FHIR bundle to validate
            request_id: Request tracking ID
            use_cache: Whether to use cached validation results
            
        Returns:
            Validation results with issues and recommendations
        """
        
        if not self.initialized:
            await self.initialize()
        
        start_time = time.time()
        
        # Check cache if enabled
        if use_cache:
            cache_key = self._generate_cache_key(bundle)
            if cache_key in self.cache:
                logger.info(f"[{request_id}] Using cached validation result")
                return self.cache[cache_key]
        
        try:
            # Update metrics
            self.validation_metrics["total_validations"] += 1
            
            # Try HAPI FHIR validation first
            validation_result = await self._validate_with_hapi(bundle, request_id)
            
            # If HAPI validation fails, fallback to local validation
            if validation_result is None:
                logger.warning(f"[{request_id}] HAPI validation unavailable, using local validator")
                validation_result = await self._validate_locally(bundle, request_id)
            
            # Process and enhance validation results
            enhanced_result = await self._process_validation_results(validation_result, bundle, request_id)
            
            # Update metrics based on result
            if enhanced_result["validation_result"] == ValidationResult.SUCCESS.value:
                self.validation_metrics["successful_validations"] += 1
            elif enhanced_result["validation_result"] == ValidationResult.ERROR.value:
                self.validation_metrics["validation_errors"] += 1
            else:
                self.validation_metrics["validation_warnings"] += 1
            
            # Calculate validation time
            validation_time = time.time() - start_time
            enhanced_result["validation_time"] = f"{validation_time:.3f}s"
            
            # Cache result if enabled
            if use_cache and cache_key:
                self.cache[cache_key] = enhanced_result
            
            logger.info(f"[{request_id}] Bundle validation completed in {validation_time:.3f}s - "
                       f"Result: {enhanced_result['validation_result']}")
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"[{request_id}] Bundle validation failed: {e}")
            return self._create_error_response(str(e), request_id)
    
    async def _validate_with_hapi(self, bundle: Dict[str, Any], request_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Validate bundle using HAPI FHIR server"""
        
        try:
            # Call HAPI FHIR $validate operation
            hapi_result = await self.hapi_client.validate_bundle(bundle, request_id)
            
            if hapi_result and hapi_result.get("validation_source") == "hapi_fhir":
                return hapi_result
            else:
                return None
                
        except Exception as e:
            logger.warning(f"[{request_id}] HAPI validation failed: {e}")
            return None
    
    async def _validate_locally(self, bundle: Dict[str, Any], request_id: Optional[str]) -> Dict[str, Any]:
        """Validate bundle using local FHIR validator"""
        
        try:
            # Use local validator as fallback
            local_result = self.local_validator.validate_bundle(bundle, request_id)
            
            # Convert to standard format
            return {
                "is_valid": local_result.get("is_valid", False),
                "errors": local_result.get("errors", []),
                "warnings": local_result.get("warnings", []),
                "issues": local_result.get("issues", []),
                "validation_source": "local_validator"
            }
            
        except Exception as e:
            logger.error(f"[{request_id}] Local validation failed: {e}")
            return {
                "is_valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
                "validation_source": "error"
            }
    
    async def _process_validation_results(self, validation_result: Dict[str, Any], 
                                         bundle: Dict[str, Any], request_id: Optional[str]) -> Dict[str, Any]:
        """Process and enhance validation results with user-friendly messages"""
        
        # Extract issues from validation result
        issues = validation_result.get("issues", [])
        errors = validation_result.get("errors", [])
        warnings = validation_result.get("warnings", [])
        
        # Categorize issues by severity
        categorized_issues = self._categorize_issues(issues, errors, warnings)
        
        # Generate user-friendly messages
        user_messages = self._generate_user_messages(categorized_issues)
        
        # Calculate bundle quality score
        quality_score = self._calculate_quality_score(categorized_issues, bundle)
        
        # Determine overall validation result
        if len(categorized_issues["errors"]) > 0:
            validation_result_status = ValidationResult.ERROR.value
        elif len(categorized_issues["warnings"]) > 0:
            validation_result_status = ValidationResult.WARNING.value
        else:
            validation_result_status = ValidationResult.SUCCESS.value
        
        # Generate actionable recommendations
        recommendations = self._generate_recommendations(categorized_issues)
        
        return {
            "validation_result": validation_result_status,
            "is_valid": validation_result.get("is_valid", False),
            "issues": categorized_issues,
            "user_messages": user_messages,
            "recommendations": recommendations,
            "bundle_quality_score": quality_score,
            "validation_source": validation_result.get("validation_source", "unknown"),
            "entry_count": len(bundle.get("entry", [])),
            "bundle_type": bundle.get("type", "unknown")
        }
    
    def _categorize_issues(self, issues: List[Dict[str, Any]], 
                          errors: List[Any], warnings: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize validation issues by severity"""
        
        categorized = {
            "errors": [],
            "warnings": [],
            "information": []
        }
        
        # Process structured issues
        for issue in issues:
            severity = issue.get("severity", "information")
            
            if severity in ["error", "fatal"]:
                categorized["errors"].append(issue)
            elif severity == "warning":
                categorized["warnings"].append(issue)
            else:
                categorized["information"].append(issue)
        
        # Add any additional errors/warnings
        for error in errors:
            if isinstance(error, str):
                categorized["errors"].append({
                    "severity": "error",
                    "message": error,
                    "location": "unknown"
                })
        
        for warning in warnings:
            if isinstance(warning, str):
                categorized["warnings"].append({
                    "severity": "warning",
                    "message": warning,
                    "location": "unknown"
                })
        
        return categorized
    
    def _generate_user_messages(self, categorized_issues: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[str]]:
        """Generate user-friendly messages from technical validation issues"""
        
        user_messages = {
            "errors": [],
            "warnings": [],
            "information": []
        }
        
        # Process errors
        for error in categorized_issues["errors"]:
            user_msg = self._transform_technical_message(error.get("message", ""), error.get("location", ""))
            user_messages["errors"].append(user_msg)
        
        # Process warnings
        for warning in categorized_issues["warnings"]:
            user_msg = self._transform_technical_message(warning.get("message", ""), warning.get("location", ""))
            user_messages["warnings"].append(user_msg)
        
        # Process information
        for info in categorized_issues["information"]:
            user_messages["information"].append(info.get("message", ""))
        
        return user_messages
    
    def _transform_technical_message(self, technical_msg: str, location: str) -> str:
        """Transform technical FHIR error messages to user-friendly format"""
        
        # Common FHIR error patterns and their user-friendly versions
        transformations = {
            r"Unable to resolve reference.*Patient.*": "Patient information is missing or invalid. Please ensure patient details are included.",
            r"minimum allowed value": "The specified value is below the minimum allowed. Please check dosage and quantity values.",
            r"Invalid resource type": "The order type is not recognized. Please verify the clinical order format.",
            r"Missing required field": "Required information is missing. Please complete all mandatory fields.",
            r"dosageInstruction.*required": "Medication dosage instructions are required. Please specify dosage and frequency.",
            r"subject.*required": "Patient reference is required for all clinical orders.",
            r"status.*required": "Order status must be specified (e.g., 'active', 'completed').",
            r"intent.*required": "Order intent must be specified (e.g., 'order', 'proposal')."
        }
        
        # Try to match and transform the message
        import re
        for pattern, friendly_msg in transformations.items():
            if re.search(pattern, technical_msg, re.IGNORECASE):
                if location and location != "unknown":
                    return f"{friendly_msg} (Location: {location})"
                return friendly_msg
        
        # If no transformation found, simplify the technical message
        if location and location != "unknown":
            return f"{technical_msg} at {location}"
        return technical_msg
    
    def _calculate_quality_score(self, categorized_issues: Dict[str, List[Dict[str, Any]]], 
                                bundle: Dict[str, Any]) -> float:
        """Calculate bundle quality score based on validation results"""
        
        # Start with perfect score
        score = 1.0
        
        # Deduct for errors (heavy penalty)
        error_count = len(categorized_issues["errors"])
        score -= (error_count * 0.2)
        
        # Deduct for warnings (lighter penalty)
        warning_count = len(categorized_issues["warnings"])
        score -= (warning_count * 0.05)
        
        # Consider bundle completeness
        entries = bundle.get("entry", [])
        if len(entries) == 0:
            score -= 0.3
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        return round(score, 2)
    
    def _generate_recommendations(self, categorized_issues: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Generate actionable recommendations based on validation issues"""
        
        recommendations = []
        
        # Analyze error patterns
        error_types = {}
        for error in categorized_issues["errors"]:
            msg = error.get("message", "")
            
            if "reference" in msg.lower():
                error_types["reference"] = error_types.get("reference", 0) + 1
            elif "required" in msg.lower():
                error_types["required"] = error_types.get("required", 0) + 1
            elif "invalid" in msg.lower():
                error_types["invalid"] = error_types.get("invalid", 0) + 1
        
        # Generate recommendations based on patterns
        if error_types.get("reference", 0) > 0:
            recommendations.append("Review resource references to ensure all referenced resources are included in the bundle")
        
        if error_types.get("required", 0) > 0:
            recommendations.append("Complete all required fields for clinical orders (status, intent, subject)")
        
        if error_types.get("invalid", 0) > 0:
            recommendations.append("Verify data formats and value ranges for all clinical parameters")
        
        # Warning-based recommendations
        if len(categorized_issues["warnings"]) > 3:
            recommendations.append("Consider reviewing warnings to improve bundle quality")
        
        # General recommendations
        if len(recommendations) == 0 and len(categorized_issues["errors"]) == 0:
            recommendations.append("Bundle validation successful - ready for submission")
        
        return recommendations
    
    def _generate_cache_key(self, bundle: Dict[str, Any]) -> Optional[str]:
        """Generate cache key for bundle validation results"""
        
        try:
            # Use bundle ID and entry count for simple caching
            bundle_id = bundle.get("id", "")
            entry_count = len(bundle.get("entry", []))
            
            if bundle_id:
                return f"{bundle_id}_{entry_count}"
            return None
            
        except Exception:
            return None
    
    def _create_error_response(self, error_msg: str, request_id: Optional[str]) -> Dict[str, Any]:
        """Create error response for validation failures"""
        
        return {
            "validation_result": ValidationResult.ERROR.value,
            "is_valid": False,
            "issues": {
                "errors": [{
                    "severity": "error",
                    "message": error_msg,
                    "location": "validation_service"
                }],
                "warnings": [],
                "information": []
            },
            "user_messages": {
                "errors": [f"Validation service error: {error_msg}"],
                "warnings": [],
                "information": []
            },
            "recommendations": ["Please try again or contact support if the issue persists"],
            "bundle_quality_score": 0.0,
            "validation_source": "error"
        }
    
    def get_validation_metrics(self) -> Dict[str, Any]:
        """Get validation service metrics"""
        
        total = self.validation_metrics["total_validations"]
        successful = self.validation_metrics["successful_validations"]
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "total_validations": total,
            "successful_validations": successful,
            "validation_errors": self.validation_metrics["validation_errors"],
            "validation_warnings": self.validation_metrics["validation_warnings"],
            "success_rate_percentage": round(success_rate, 2),
            "meets_target": success_rate >= 95.0,  # ≥95% target
            "cache_size": len(self.cache)
        }
    
    def clear_cache(self):
        """Clear validation cache"""
        self.cache.clear()
        logger.info("Validation cache cleared")


# Global validation service instance
_validation_service = None

async def get_validation_service() -> FHIRValidationService:
    """Get initialized validation service instance"""
    global _validation_service
    
    if _validation_service is None:
        _validation_service = FHIRValidationService()
        await _validation_service.initialize()
    
    return _validation_service