"""
LLM-based Medical Entity Extractor
High-accuracy extraction using Large Language Models for escalation scenarios.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class LLMExtractor:
    """LLM-based entity extraction for high-accuracy medical scenarios"""

    def __init__(self):
        self._llm_processor = None

    def extract_entities_with_llm(self, text: str, request_id: str = "llm-extraction") -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract medical entities using LLM escalation with CORRECT parsing methodology.

        CRITICAL: This method implements the corrected LLM parsing that properly extracts
        embedded data from structured Pydantic objects. Previous parsing errors have been
        fixed to prevent misinterpretation of LLM performance.

        Args:
            text: Clinical text to process
            request_id: Request identifier for logging

        Returns:
            Dictionary of extracted entities with proper structure and confidence scores
        """

        # Initialize LLM processor if needed
        if not self._initialize_llm_processor():
            logger.error("Failed to initialize LLM processor")
            return self._empty_result()

        try:
            # Process with LLM using structured output
            llm_results = self._llm_processor.process_clinical_text(text, [], request_id)
            structured_output = llm_results.get("structured_output", {})

            if not structured_output:
                logger.warning(f"LLM returned empty structured output for request {request_id}")
                return self._empty_result()

            # CORRECTED PARSING METHODOLOGY:
            # Extract ALL data including embedded fields from LLM structured objects
            extracted_entities = self._empty_result()

            # Extract medications AND their embedded dosage/frequency data
            self._extract_medications_from_llm(structured_output, extracted_entities)

            # Extract medical conditions
            self._extract_conditions_from_llm(structured_output, extracted_entities)

            # Extract lab tests with proper categorization
            self._extract_lab_tests_from_llm(structured_output, extracted_entities)

            # Extract procedures
            self._extract_procedures_from_llm(structured_output, extracted_entities)

            # Extract patients if present
            self._extract_patients_from_llm(structured_output, extracted_entities)

            # Log successful extraction
            total_extracted = sum(len(entities) for entities in extracted_entities.values())
            logger.info(f"LLM escalation successful: extracted {total_extracted} entities from text")

            return extracted_entities

        except Exception as e:
            logger.error(f"LLM escalation failed for request {request_id}: {e}")
            return self._empty_result()

    def _initialize_llm_processor(self) -> bool:
        """Initialize LLM processor if not already done"""

        if self._llm_processor is not None:
            return self._llm_processor.initialized

        try:
            from ..llm_processor import LLMProcessor
            self._llm_processor = LLMProcessor()

            if not self._llm_processor.initialized:
                return self._llm_processor.initialize()

            return True

        except ImportError as e:
            logger.error(f"Failed to import LLMProcessor: {e}")
            return False

    def _empty_result(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return empty result structure"""
        return {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "patients": [],
            "conditions": [],
            "procedures": [],
            "lab_tests": []
        }

    def _extract_medications_from_llm(self, structured_output: Dict, extracted_entities: Dict) -> None:
        """Extract medications and embedded dosage/frequency data from LLM output"""

        for med in structured_output.get("medications", []):
            if isinstance(med, dict):
                # Add the medication name
                med_name = med.get("name", "")
                if med_name:
                    extracted_entities["medications"].append({
                        "text": med_name,
                        "confidence": 0.9,
                        "start": 0,  # LLM doesn't provide position info
                        "end": 0,
                        "method": "llm_escalation",
                        "source": "llm"
                    })

                # CRITICAL FIX: Extract embedded dosage
                dosage = med.get("dosage", "")
                if dosage:
                    extracted_entities["dosages"].append({
                        "text": str(dosage),
                        "confidence": 0.9,
                        "start": 0,
                        "end": 0,
                        "method": "llm_escalation",
                        "source": "llm_embedded"
                    })

                # CRITICAL FIX: Extract embedded frequency
                frequency = med.get("frequency", "")
                if frequency:
                    extracted_entities["frequencies"].append({
                        "text": str(frequency),
                        "confidence": 0.9,
                        "start": 0,
                        "end": 0,
                        "method": "llm_escalation",
                        "source": "llm_embedded"
                    })

                # Extract embedded route if available
                route = med.get("route", "")
                if route and str(route).strip() and str(route) != "None":
                    # Add route as procedure for FHIR mapping
                    extracted_entities["procedures"].append({
                        "text": f"Administration route: {route}",
                        "confidence": 0.8,
                        "start": 0,
                        "end": 0,
                        "method": "llm_escalation",
                        "source": "llm_embedded"
                    })

    def _extract_conditions_from_llm(self, structured_output: Dict, extracted_entities: Dict) -> None:
        """Extract medical conditions from LLM output"""

        for condition in structured_output.get("conditions", []):
            if isinstance(condition, dict):
                condition_name = condition.get("name", "")
                if condition_name:
                    extracted_entities["conditions"].append({
                        "text": condition_name,
                        "confidence": 0.9,
                        "start": 0,
                        "end": 0,
                        "method": "llm_escalation",
                        "source": "llm"
                    })

    def _extract_lab_tests_from_llm(self, structured_output: Dict, extracted_entities: Dict) -> None:
        """Extract lab tests from LLM output"""

        for lab in structured_output.get("lab_tests", []):
            if isinstance(lab, dict):
                lab_name = lab.get("name", "")
                if lab_name:
                    extracted_entities["lab_tests"].append({
                        "text": lab_name,
                        "confidence": 0.9,
                        "start": 0,
                        "end": 0,
                        "method": "llm_escalation",
                        "source": "llm"
                    })

    def _extract_procedures_from_llm(self, structured_output: Dict, extracted_entities: Dict) -> None:
        """Extract procedures from LLM output"""

        for proc in structured_output.get("procedures", []):
            if isinstance(proc, dict):
                proc_name = proc.get("name", "")
                if proc_name:
                    extracted_entities["procedures"].append({
                        "text": proc_name,
                        "confidence": 0.9,
                        "start": 0,
                        "end": 0,
                        "method": "llm_escalation",
                        "source": "llm"
                    })

    def _extract_patients_from_llm(self, structured_output: Dict, extracted_entities: Dict) -> None:
        """Extract patients from LLM output"""

        for patient in structured_output.get("patients", []):
            if isinstance(patient, dict):
                patient_name = patient.get("name", "")
                if patient_name:
                    extracted_entities["patients"].append({
                        "text": patient_name,
                        "confidence": 0.9,
                        "start": 0,
                        "end": 0,
                        "method": "llm_escalation",
                        "source": "llm"
                    })
            elif isinstance(patient, str) and patient.strip():
                extracted_entities["patients"].append({
                    "text": patient.strip(),
                    "confidence": 0.9,
                    "start": 0,
                    "end": 0,
                    "method": "llm_escalation",
                    "source": "llm"
                })

    def is_available(self) -> bool:
        """Check if LLM processor is available and initialized"""
        return self._initialize_llm_processor()