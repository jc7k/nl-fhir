"""
Enhanced NLP Pipeline with Clinical Validation
Integrates comprehensive error detection with existing 3-tier NLP processing
Production-ready validation for ambiguous and faulty clinical orders
"""

import logging
import time
from typing import Dict, List, Any, Optional
import asyncio

from .nlp.pipeline import NLPPipeline
from .clinical_validator import validate_clinical_order
from .error_handler import handle_validation_error

logger = logging.getLogger(__name__)


class EnhancedNLPPipeline:
    """NLP Pipeline with integrated clinical validation and error handling"""
    
    def __init__(self):
        self.nlp_pipeline = NLPPipeline()
        self.validation_enabled = True
        self.validation_mode = "strict"  # strict, permissive, or disabled
        self.initialized = False
    
    def initialize(self) -> bool:
        """Initialize enhanced pipeline with validation"""
        try:
            # Initialize base NLP pipeline
            if not self.nlp_pipeline.initialize():
                logger.error("Failed to initialize base NLP pipeline")
                return False
            
            self.initialized = True
            logger.info("Enhanced NLP pipeline with validation initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced NLP pipeline: {e}")
            return False
    
    async def process_clinical_text_enhanced(self, text: str, 
                                           request_id: Optional[str] = None,
                                           validation_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhanced clinical text processing with comprehensive validation
        
        Args:
            text: Clinical text to process
            request_id: Optional request identifier
            validation_mode: Override default validation mode (strict/permissive/disabled)
        
        Returns:
            Comprehensive response with validation, NLP results, and FHIR data
        """
        
        if not self.initialized:
            if not self.initialize():
                return self._create_initialization_error(request_id)
        
        start_time = time.time()
        mode = validation_mode or self.validation_mode
        
        logger.info(f"[{request_id}] Starting enhanced processing with validation mode: {mode}")
        
        try:
            # PHASE 1: Clinical Validation (Pre-processing)
            validation_result = None
            error_response = None
            
            if mode != "disabled" and self.validation_enabled:
                logger.info(f"[{request_id}] Phase 1: Clinical validation")
                validation_start = time.time()
                
                validation_result = validate_clinical_order(text, request_id)
                validation_time = time.time() - validation_start
                
                logger.info(f"[{request_id}] Validation complete in {validation_time*1000:.1f}ms: "
                          f"{len(validation_result.issues)} issues, can_process={validation_result.can_process_fhir}")
                
                # Handle validation failures based on mode
                if mode == "strict" and not validation_result.can_process_fhir:
                    logger.warning(f"[{request_id}] STRICT MODE: Blocking processing due to validation failures")
                    error_response = handle_validation_error(validation_result, request_id)
                    
                    return {
                        "status": "validation_failed",
                        "processing_blocked": True,
                        "validation_result": validation_result,
                        "error_response": error_response,
                        "processing_time_ms": (time.time() - start_time) * 1000,
                        "phase_completed": "validation_only"
                    }
                
                elif validation_result.escalation_required:
                    logger.info(f"[{request_id}] Escalation required but proceeding with processing")
                    error_response = handle_validation_error(validation_result, request_id)
            
            # PHASE 2: NLP Processing
            logger.info(f"[{request_id}] Phase 2: NLP processing")
            nlp_start = time.time()
            
            nlp_result = await self.nlp_pipeline.process_clinical_text(text, request_id)
            nlp_time = time.time() - nlp_start
            
            logger.info(f"[{request_id}] NLP processing complete in {nlp_time*1000:.1f}ms")
            
            # PHASE 3: Results Integration
            logger.info(f"[{request_id}] Phase 3: Results integration")
            
            total_time = time.time() - start_time
            
            # Create comprehensive response
            response = self._create_enhanced_response(
                nlp_result, validation_result, error_response, total_time, request_id, mode
            )
            
            logger.info(f"[{request_id}] Enhanced processing complete in {total_time*1000:.1f}ms")
            return response
            
        except Exception as e:
            logger.error(f"[{request_id}] Enhanced processing failed: {e}")
            return self._create_processing_error(str(e), request_id, time.time() - start_time)
    
    def _create_enhanced_response(self, nlp_result: Dict[str, Any], 
                                validation_result, error_response: Optional[Dict],
                                total_time: float, request_id: str, mode: str) -> Dict[str, Any]:
        """Create comprehensive enhanced response"""
        
        # Determine overall status
        if validation_result and not validation_result.can_process_fhir:
            status = "validation_failed"
        elif validation_result and validation_result.escalation_required:
            status = "processed_with_warnings"
        elif nlp_result.get("status") == "completed":
            status = "completed"
        else:
            status = "processing_failed"
        
        # Base response structure
        response = {
            "status": status,
            "request_id": request_id,
            "processing_time_ms": total_time * 1000,
            "validation_mode": mode,
            
            # Validation results
            "validation": {
                "enabled": self.validation_enabled and mode != "disabled",
                "passed": validation_result.is_valid if validation_result else True,
                "can_process_fhir": validation_result.can_process_fhir if validation_result else True,
                "issues_detected": len(validation_result.issues) if validation_result else 0,
                "escalation_required": validation_result.escalation_required if validation_result else False,
                "confidence": validation_result.confidence if validation_result else 1.0
            },
            
            # NLP results (preserve existing structure)
            "nlp_results": nlp_result,
            
            # Enhanced metadata
            "processing_phases": {
                "validation_completed": validation_result is not None,
                "nlp_completed": nlp_result.get("status") == "completed",
                "integration_completed": True
            },
            
            # Quality indicators
            "quality_assessment": {
                "overall_confidence": self._calculate_overall_confidence(nlp_result, validation_result),
                "fhir_compliance": validation_result.can_process_fhir if validation_result else True,
                "processing_method": nlp_result.get("extracted_entities", {}).get("status", "unknown"),
                "validation_issues": len(validation_result.issues) if validation_result else 0
            }
        }
        
        # Add validation details if issues exist
        if validation_result and validation_result.issues:
            response["validation_details"] = {
                "issues": [
                    {
                        "severity": issue.severity.value,
                        "code": issue.code.value,
                        "message": issue.message,
                        "guidance": issue.guidance
                    }
                    for issue in validation_result.issues
                ],
                "escalation_info": error_response["escalation"] if error_response else None
            }
        
        # Add FHIR operation outcome if validation failed
        if validation_result and error_response:
            response["fhir_operation_outcome"] = error_response.get("fhir_operation_outcome")
        
        return response
    
    def _calculate_overall_confidence(self, nlp_result: Dict[str, Any], validation_result) -> float:
        """Calculate overall processing confidence combining NLP and validation"""
        
        # Get NLP confidence (based on processing method and results)
        nlp_confidence = 0.95  # Default high confidence for successful processing
        processing_method = nlp_result.get("extracted_entities", {}).get("status", "completed")
        
        if processing_method == "failed":
            nlp_confidence = 0.0
        elif "llm" in processing_method.lower():
            nlp_confidence = 0.85  # LLM processing indicates some ambiguity
        
        # Get validation confidence
        validation_confidence = validation_result.confidence if validation_result else 1.0
        
        # Combined confidence (weighted average)
        overall_confidence = (nlp_confidence * 0.6) + (validation_confidence * 0.4)
        
        return round(overall_confidence, 2)
    
    def _create_initialization_error(self, request_id: str) -> Dict[str, Any]:
        """Create initialization error response"""
        return {
            "status": "initialization_failed",
            "request_id": request_id,
            "error": "Enhanced NLP pipeline initialization failed",
            "processing_time_ms": 0,
            "validation": {"enabled": False, "passed": False},
            "nlp_results": {"status": "failed", "error": "Pipeline not initialized"}
        }
    
    def _create_processing_error(self, error_message: str, request_id: str, processing_time: float) -> Dict[str, Any]:
        """Create processing error response"""
        return {
            "status": "processing_failed",
            "request_id": request_id,
            "error": error_message,
            "processing_time_ms": processing_time * 1000,
            "validation": {"enabled": False, "passed": False},
            "nlp_results": {"status": "failed", "error": error_message}
        }
    
    def get_enhanced_pipeline_status(self) -> Dict[str, Any]:
        """Get comprehensive pipeline status including validation capabilities"""
        
        base_status = self.nlp_pipeline.get_pipeline_status()
        
        return {
            "enhanced_pipeline": {
                "initialized": self.initialized,
                "validation_enabled": self.validation_enabled,
                "validation_mode": self.validation_mode,
                "version": "1.0.0"
            },
            "base_nlp_pipeline": base_status,
            "validation_capabilities": {
                "conditional_logic_detection": True,
                "medication_ambiguity_detection": True,
                "missing_fields_detection": True,
                "protocol_dependency_detection": True,
                "clinical_safety_validation": True,
                "fhir_compliance_checking": True
            },
            "error_handling": {
                "fhir_operation_outcome": True,
                "escalation_workflows": True,
                "clinical_guidance": True,
                "structured_responses": True
            }
        }
    
    def set_validation_mode(self, mode: str):
        """Set validation mode: strict, permissive, or disabled"""
        if mode in ["strict", "permissive", "disabled"]:
            self.validation_mode = mode
            logger.info(f"Validation mode set to: {mode}")
        else:
            raise ValueError("Mode must be 'strict', 'permissive', or 'disabled'")
    
    def disable_validation(self):
        """Temporarily disable validation"""
        self.validation_enabled = False
        logger.info("Clinical validation disabled")
    
    def enable_validation(self):
        """Enable validation"""
        self.validation_enabled = True
        logger.info("Clinical validation enabled")


# Global enhanced pipeline instance
enhanced_nlp_pipeline = EnhancedNLPPipeline()


async def process_clinical_text_with_validation(text: str, request_id: Optional[str] = None,
                                              validation_mode: Optional[str] = None) -> Dict[str, Any]:
    """Enhanced clinical text processing with comprehensive validation"""
    return await enhanced_nlp_pipeline.process_clinical_text_enhanced(text, request_id, validation_mode)


def get_enhanced_pipeline_status() -> Dict[str, Any]:
    """Get enhanced pipeline status"""
    return enhanced_nlp_pipeline.get_enhanced_pipeline_status()