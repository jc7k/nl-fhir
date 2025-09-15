"""
Validation helpers for LLM output
"""

import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ValidationHelpers:
    """Helper class for validating LLM output against source text"""

    def validate_against_source(self, extracted_data: Dict[str, Any], source_text: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate extracted content exists in source text to prevent hallucination"""

        logger.info(f"[{request_id}] Validating extracted content against source text")

        # Normalize text for comparison (lowercase, remove extra spaces)
        normalized_source = source_text.lower().strip()
        normalized_source = re.sub(r'\s+', ' ', normalized_source)

        validated_data = extracted_data.copy()

        # Validate medications
        if 'medications' in validated_data and validated_data['medications']:
            validated_data['medications'] = self._validate_medications(
                validated_data['medications'], normalized_source, request_id
            )

        # Validate conditions
        if 'conditions' in validated_data and validated_data['conditions']:
            validated_data['conditions'] = self._validate_conditions(
                validated_data['conditions'], normalized_source, request_id
            )

        # Validate patient names (strict validation - must be exact)
        if 'patient_name' in validated_data and validated_data['patient_name']:
            validated_data['patient_name'] = self._validate_patient_name(
                validated_data['patient_name'], normalized_source, request_id
            )

        # Validate lab tests
        if 'lab_tests' in validated_data and validated_data['lab_tests']:
            validated_data['lab_tests'] = self._validate_lab_tests(
                validated_data['lab_tests'], normalized_source, request_id
            )

        # Validate procedures
        if 'procedures' in validated_data and validated_data['procedures']:
            validated_data['procedures'] = self._validate_procedures(
                validated_data['procedures'], normalized_source, request_id
            )

        logger.info(f"[{request_id}] Validation complete - removed hallucinated content")
        return validated_data

    def _validate_medications(self, medications: list, normalized_source: str, request_id: Optional[str]) -> list:
        """Validate medication list against source text"""
        validated_meds = []

        for med in medications:
            if isinstance(med, dict):
                med_name = med.get('name', '').lower().strip()
                # Check if medication name exists in source
                if med_name and med_name in normalized_source:
                    # Validate dosage if present
                    if 'dosage' in med and med['dosage']:
                        dosage = str(med['dosage']).lower().strip()
                        if dosage not in normalized_source:
                            logger.warning(f"[{request_id}] Removing hallucinated dosage '{dosage}' for {med_name}")
                            med['dosage'] = None

                    # Validate frequency if present
                    if 'frequency' in med and med['frequency']:
                        freq = str(med['frequency']).lower().strip()
                        if freq not in normalized_source:
                            logger.warning(f"[{request_id}] Removing hallucinated frequency '{freq}' for {med_name}")
                            med['frequency'] = None

                    validated_meds.append(med)
                else:
                    logger.warning(f"[{request_id}] Removing hallucinated medication '{med_name}'")

        return validated_meds

    def _validate_conditions(self, conditions: list, normalized_source: str, request_id: Optional[str]) -> list:
        """Validate conditions list against source text"""
        validated_conditions = []

        for condition in conditions:
            if isinstance(condition, dict):
                condition_name = condition.get('name', '').lower().strip()
                if condition_name:
                    # Check for exact or close match in source
                    # Allow for slight variations (e.g., "type 2 diabetes" vs "type 2 diabetes mellitus")
                    condition_words = condition_name.split()

                    # Check if all significant words exist in source
                    significant_words = [w for w in condition_words if len(w) > 2]  # Skip small words
                    all_present = all(word in normalized_source for word in significant_words)

                    if all_present:
                        # Additional check: words should be relatively close together
                        # Create a pattern that allows up to 3 words between condition words
                        pattern = r'\b' + r'\b.{0,20}\b'.join(re.escape(word) for word in significant_words) + r'\b'
                        if re.search(pattern, normalized_source):
                            validated_conditions.append(condition)
                        else:
                            logger.warning(f"[{request_id}] Removing hallucinated condition '{condition_name}' - words too far apart")
                    else:
                        logger.warning(f"[{request_id}] Removing hallucinated condition '{condition_name}'")

        return validated_conditions

    def _validate_patient_name(self, patient_name: str, normalized_source: str, request_id: Optional[str]) -> Optional[str]:
        """Validate patient name against source text"""
        patient_name_lower = patient_name.lower().strip()

        if patient_name_lower and patient_name_lower not in normalized_source:
            # Check if it might be split across lines or have different spacing
            patient_words = patient_name_lower.split()
            if not all(word in normalized_source for word in patient_words):
                logger.warning(f"[{request_id}] Removing hallucinated patient name '{patient_name}'")
                return None

        return patient_name

    def _validate_lab_tests(self, lab_tests: list, normalized_source: str, request_id: Optional[str]) -> list:
        """Validate lab tests list against source text"""
        validated_tests = []

        for test in lab_tests:
            if isinstance(test, dict):
                test_name = test.get('name', '').lower().strip()
                if test_name and test_name in normalized_source:
                    validated_tests.append(test)
                else:
                    logger.warning(f"[{request_id}] Removing hallucinated lab test '{test_name}'")

        return validated_tests

    def _validate_procedures(self, procedures: list, normalized_source: str, request_id: Optional[str]) -> list:
        """Validate procedures list against source text"""
        validated_procedures = []

        for proc in procedures:
            if isinstance(proc, dict):
                proc_name = proc.get('name', '').lower().strip()
                if proc_name and proc_name in normalized_source:
                    validated_procedures.append(proc)
                else:
                    logger.warning(f"[{request_id}] Removing hallucinated procedure '{proc_name}'")

        return validated_procedures