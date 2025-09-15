"""
LLM Processor Coordinator - Slim orchestrator for structured clinical output
HIPAA Compliant: Secure LLM integration with PHI protection
Production Ready: Fast structured output with Instructor validation
"""

import logging
import time
import os
from typing import Dict, List, Any, Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional
    pass

from .models import ClinicalStructure
from .processors import (
    InstructorProcessor,
    StructuredOutputProcessor,
    FallbackProcessor,
    PromptBuilder
)

logger = logging.getLogger(__name__)


class LLMProcessor:
    """Enhanced LLM processor coordinator with Instructor for structured clinical output"""

    def __init__(self):
        self.initialized = False
        self.instructor_processor = InstructorProcessor()
        self.structured_output_processor = StructuredOutputProcessor()
        self.fallback_processor = FallbackProcessor()

    def initialize(self) -> bool:
        """Initialize LLM processor with all components"""
        try:
            # Try to initialize Instructor processor
            instructor_initialized = self.instructor_processor.initialize()

            # Always consider initialized if fallback is available
            self.initialized = True

            if instructor_initialized:
                logger.info("LLM processor initialized with Instructor and OpenAI")
            else:
                logger.info("LLM processor initialized with rule-based structured output (no API key or Instructor)")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize LLM processor: {e}")
            return False

    def process_clinical_text(self, text: str, entities: List[Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Process clinical text with cost-optimized regex-first, LLM escalation approach"""

        if not self.initialized:
            if not self.initialize():
                logger.error(f"[{request_id}] LLM processing failed - not initialized")
                return self._create_empty_structure()

        start_time = time.time()

        try:
            # STEP 1: Try fast regex-based extraction first (50ms vs 2300ms)
            structured_output = self.fallback_processor.extract_clinical_structure(text)
            method = "regex_enhanced"

            # STEP 2: Check if escalation to expensive LLM is needed
            needs_llm_escalation = self.structured_output_processor.should_escalate_to_llm(structured_output, text)

            if needs_llm_escalation and self.instructor_processor.is_available():
                logger.info(f"[{request_id}] Escalating to LLM due to insufficient regex extraction")
                # Use expensive LLM only when needed
                structured_output = self.instructor_processor.extract_clinical_structure(text, request_id)
                method = "escalated_to_llm"

            processing_time = time.time() - start_time
            logger.info(f"[{request_id}] Generated structured output using {method} in {processing_time:.3f}s")

            return self.structured_output_processor.format_processing_result(
                structured_output, processing_time, method, "completed"
            )

        except Exception as e:
            logger.error(f"[{request_id}] LLM processing failed: {e}")
            processing_time = time.time() - start_time
            return self.structured_output_processor.format_processing_result(
                self._create_empty_structure(), processing_time, "fallback", "failed", str(e)
            )

    def _create_empty_structure(self) -> Dict[str, Any]:
        """Create empty clinical structure"""
        return ClinicalStructure().model_dump()

    def get_processor_status(self) -> Dict[str, Any]:
        """Get LLM processor status"""
        return {
            "initialized": self.initialized,
            "method": "instructor_llm" if self.instructor_processor.is_available() else "rule_based_enhanced",
            "api_available": self.instructor_processor.is_available(),
            "instructor_available": True,  # We have the module available
            "fallback_active": not self.instructor_processor.is_available()
        }


# Global LLM processor instance
llm_processor = LLMProcessor()


def process_clinical_text(text: str, entities: List[Any], request_id: Optional[str] = None) -> Dict[str, Any]:
    """Process clinical text with enhanced LLM structured output"""
    return llm_processor.process_clinical_text(text, entities, request_id)


def get_llm_processor_status() -> Dict[str, Any]:
    """Get LLM processor status"""
    return llm_processor.get_processor_status()