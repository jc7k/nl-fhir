"""
Instructor-based LLM processor for structured clinical output
"""

import logging
import os
from typing import Dict, Any, Optional

from ..models import ClinicalStructure
from .prompt_builder import PromptBuilder
from ..utils.validation_helpers import ValidationHelpers

logger = logging.getLogger(__name__)

# Import Instructor and OpenAI with error handling
try:
    import instructor
    import openai
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    logger.warning("Instructor/OpenAI not available - using fallback")
    INSTRUCTOR_AVAILABLE = False


class InstructorProcessor:
    """Handles LLM processing using Instructor for structured output"""

    def __init__(self):
        self.client = None
        self.api_key = None
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.0'))
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
        self.timeout_seconds = int(os.getenv('OPENAI_TIMEOUT_SECONDS', '30'))
        self.prompt_builder = PromptBuilder()
        self.validation_helpers = ValidationHelpers()

    def initialize(self) -> bool:
        """Initialize Instructor client"""
        try:
            self.api_key = os.getenv('OPENAI_API_KEY')

            if INSTRUCTOR_AVAILABLE and self.api_key:
                openai_client = openai.OpenAI(api_key=self.api_key)
                self.client = instructor.from_openai(openai_client)
                logger.info("Instructor processor initialized successfully")
                return True
            else:
                logger.info("Instructor unavailable - no API key or import failed")
                return False

        except Exception as e:
            logger.error(f"Failed to initialize Instructor processor: {e}")
            return False

    def extract_clinical_structure(self, text: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Extract clinical structure using Instructor-enhanced LLM"""

        if not self.client:
            raise RuntimeError("Instructor client not initialized")

        try:
            # Create prompts
            system_prompt = self.prompt_builder.build_system_prompt()
            user_prompt = self.prompt_builder.build_user_prompt(text)

            # Use Instructor to get structured output
            response = self.client.chat.completions.create(
                model=self.model,
                response_model=ClinicalStructure,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout_seconds,
            )

            logger.info(f"[{request_id}] Instructor extraction successful")

            # Validate extracted content against original text to prevent hallucination
            extracted_data = response.model_dump()
            validated_data = self.validation_helpers.validate_against_source(extracted_data, text, request_id)
            return validated_data

        except Exception as e:
            logger.error(f"[{request_id}] Instructor extraction failed: {e}")
            raise

    def is_available(self) -> bool:
        """Check if Instructor processing is available"""
        return bool(self.client and self.api_key and INSTRUCTOR_AVAILABLE)