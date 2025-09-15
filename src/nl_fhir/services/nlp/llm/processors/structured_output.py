"""
Structured output processing and escalation logic
"""

import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class StructuredOutputProcessor:
    """Handles structured output processing and escalation decisions"""

    def should_escalate_to_llm(self, structured_output: Dict[str, Any], text: str) -> bool:
        """Determine if expensive LLM escalation is needed based on regex results"""

        # Get entity counts
        medications = structured_output.get("medications", [])
        lab_tests = structured_output.get("lab_tests", [])
        procedures = structured_output.get("procedures", [])
        conditions = structured_output.get("conditions", [])

        total_entities = len(medications) + len(lab_tests) + len(procedures) + len(conditions)
        text_lower = text.lower()

        # Escalation Rule 1: Zero entities found (complete failure)
        if total_entities == 0:
            logger.info("LLM escalation: No entities found by regex")
            return True

        # Escalation Rule 2: Low quality extraction (noise words only)
        # Check if we only found very short/common words that are likely noise
        noise_words = {'the', 'a', 'an', 'to', 'for', 'with', 'of', 'in', 'on', 'at', 'by', 'from'}
        quality_entities = 0

        for entity_list in [medications, lab_tests, procedures, conditions]:
            for entity in entity_list:
                entity_name = entity.get('name', entity.get('text', '')).lower().strip()
                if entity_name and len(entity_name) > 2 and entity_name not in noise_words:
                    quality_entities += 1

        if total_entities > 0 and quality_entities == 0:
            logger.info("LLM escalation: Only noise words found, no quality entities")
            return True

        # Escalation Rule 3: Complex medication names that regex typically misses
        complex_med_patterns = [
            'tadalafil', 'triamcinolone', 'epinephrine', 'risperidone',
            'azithromycin', 'methotrexate', 'pramipexole', 'bupropion',
            'clonidine', 'spironolactone', 'metronidazole', 'propranolol',
            'cabergoline', 'gabapentin', 'hydroxychloroquine', 'levetiracetam',
            'diclofenac', 'cinacalcet', 'desmopressin', 'pirfenidone'  # Add common medications that fail regex
        ]

        for med_name in complex_med_patterns:
            if med_name in text_lower:
                # Check if this specific medication was properly extracted
                medication_names = [med.get('name', '').lower() for med in medications]
                if med_name not in medication_names:
                    logger.info(f"LLM escalation: Complex medication '{med_name}' detected but not properly extracted")
                    return True

        # Escalation Rule 4: Medication context without medication extraction
        # If we see medication dosing patterns but extracted no medications
        has_dosing_patterns = bool(
            any(pattern in text_lower for pattern in ['mg', 'daily', 'twice', 'three times', 'orally', 'iv', 'prn', 'as needed'])
        )

        if has_dosing_patterns and len(medications) == 0:
            logger.info("LLM escalation: Dosing patterns detected but no medications extracted")
            return True

        # Escalation Rule 5: Medical action verbs without proper extraction
        medical_actions = ['prescribe', 'administer', 'give', 'start', 'initiate', 'order', 'discontinue', 'increase', 'decrease']
        has_medical_actions = any(action in text_lower for action in medical_actions)

        if has_medical_actions and quality_entities < 2:
            logger.info("LLM escalation: Medical action verbs present but insufficient quality entities")
            return True

        # Escalation Rule 6: Patient names mentioned but not extracted (CRITICAL for FHIR)
        # Look for patient name patterns like "patient [Name]" or "Started patient [Name]"
        patient_patterns = [
            r'\bpatient\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
            r'\b(?:started|initiated|prescribed)\s+patient\s+([A-Z][a-z]+\s+[A-Z][a-z]+)\b'
        ]

        has_patient_name_pattern = False
        for pattern in patient_patterns:
            if re.search(pattern, text):
                has_patient_name_pattern = True
                break

        # Get current patients from structured output
        patients = structured_output.get("patients", [])

        if has_patient_name_pattern and len(patients) == 0:
            logger.info("LLM escalation: Patient name pattern detected but no patients extracted")
            return True

        # Debug logging
        logger.info(f"LLM escalation check: {total_entities} total entities, {quality_entities} quality entities, has_dosing: {has_dosing_patterns}, has_medical_actions: {has_medical_actions}")

        # Default: regex extraction was sufficient
        return False

    def format_processing_result(self, structured_output: Dict[str, Any], processing_time: float, method: str, status: str = "completed", error: str = None) -> Dict[str, Any]:
        """Format processing result with metadata"""
        result = {
            "structured_output": structured_output,
            "processing_time_ms": processing_time * 1000,
            "method": method,
            "status": status
        }

        if error:
            result["error"] = error

        return result