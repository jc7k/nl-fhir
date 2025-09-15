"""
Escalation Manager for Medical Entity Extraction
Determines when to escalate to LLM based on confidence thresholds and medical safety requirements.
"""

import logging
import os
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class EscalationManager:
    """Manages escalation decisions for medical entity extraction"""

    def __init__(self):
        # Load escalation configuration from environment
        self.escalation_enabled = os.getenv('LLM_ESCALATION_ENABLED', 'true').lower() == 'true'
        self.escalation_threshold = float(os.getenv('LLM_ESCALATION_THRESHOLD', '0.85'))
        self.confidence_check_method = os.getenv('LLM_ESCALATION_CONFIDENCE_CHECK', 'weighted_average')
        self.min_entities_required = int(os.getenv('LLM_ESCALATION_MIN_ENTITIES', '3'))

    def should_escalate_to_llm(self, result: Dict[str, List[Dict[str, Any]]], text: str) -> bool:
        """
        Determine if results should be escalated to LLM based on confidence thresholds.

        For medical applications, we need high confidence (default 85% threshold).
        This prevents dangerous misinterpretations in clinical settings.

        Args:
            result: Dictionary of extracted entities by category
            text: Original text being processed

        Returns:
            bool: True if should escalate to LLM for higher accuracy
        """

        if not self.escalation_enabled:
            return False

        # Calculate overall confidence based on chosen method
        total_entities = 0
        total_confidence_sum = 0.0
        confidence_values = []

        for category, entities in result.items():
            for entity in entities:
                total_entities += 1
                confidence = entity.get('confidence', 0.0)
                total_confidence_sum += confidence
                confidence_values.append(confidence)

        # If no entities found, definitely escalate to LLM
        if total_entities == 0:
            logger.info("Escalating to LLM: No entities found in text")
            return True

        # If too few entities for clinical text, escalate
        if total_entities < self.min_entities_required:
            text_lower = text.lower()
            # Check if this looks like clinical text that should have more entities
            clinical_indicators = ['prescribe', 'medication', 'patient', 'mg', 'daily', 'order', 'diagnosis']
            if any(indicator in text_lower for indicator in clinical_indicators):
                logger.info(f"Escalating to LLM: Only {total_entities} entities found, expected more for clinical text")
                return True

        # Force escalation if patient names are mentioned but not extracted (medical safety critical)
        if self._should_escalate_for_missing_patients(result, text):
            return True

        # Calculate confidence score based on method
        overall_confidence = self._calculate_overall_confidence(
            result, total_entities, total_confidence_sum, confidence_values
        )

        # Decision: escalate if confidence below medical safety threshold
        should_escalate = overall_confidence < self.escalation_threshold

        if should_escalate:
            logger.info(f"Escalating to LLM: Overall confidence {overall_confidence:.3f} below threshold {self.escalation_threshold}")
        else:
            logger.info(f"Pipeline sufficient: Overall confidence {overall_confidence:.3f} meets threshold {self.escalation_threshold}")

        return should_escalate

    def _should_escalate_for_missing_patients(self, result: Dict[str, List[Dict[str, Any]]], text: str) -> bool:
        """Check if escalation needed for missing patient entities"""

        text_lower = text.lower()
        patient_indicators = ['patient', 'mr.', 'mrs.', 'ms.', 'dr.']
        has_patient_mention = any(indicator in text_lower for indicator in patient_indicators)
        has_patient_entities = len(result.get('patients', [])) > 0

        if has_patient_mention and not has_patient_entities:
            logger.info("Escalating to LLM: Patient mentioned but no patient entities extracted")
            return True

        return False

    def _calculate_overall_confidence(self, result: Dict[str, List[Dict[str, Any]]],
                                    total_entities: int, total_confidence_sum: float,
                                    confidence_values: List[float]) -> float:
        """Calculate overall confidence based on configured method"""

        if self.confidence_check_method == 'weighted_average':
            # Weighted by entity importance (medications and conditions are more critical)
            weighted_sum = 0.0
            weight_sum = 0.0

            for category, entities in result.items():
                # Medical safety: Higher weights for critical entity types
                if category in ['medications', 'conditions']:
                    weight = 3.0  # Critical for medical safety
                elif category in ['dosages', 'frequencies']:
                    weight = 2.0  # Important for medication safety
                else:
                    weight = 1.0  # Standard weight

                for entity in entities:
                    confidence = entity.get('confidence', 0.0)
                    weighted_sum += confidence * weight
                    weight_sum += weight

            return weighted_sum / weight_sum if weight_sum > 0 else 0.0

        elif self.confidence_check_method == 'minimum':
            # Use minimum confidence (most conservative)
            return min(confidence_values) if confidence_values else 0.0

        elif self.confidence_check_method == 'average':
            # Simple average
            return total_confidence_sum / total_entities if total_entities > 0 else 0.0

        else:
            # Default to weighted average
            logger.warning(f"Unknown confidence check method: {self.confidence_check_method}, using weighted_average")
            return total_confidence_sum / total_entities if total_entities > 0 else 0.0

    def get_escalation_config(self) -> Dict[str, Any]:
        """Get current escalation configuration"""

        return {
            "escalation_enabled": self.escalation_enabled,
            "escalation_threshold": self.escalation_threshold,
            "confidence_check_method": self.confidence_check_method,
            "min_entities_required": self.min_entities_required
        }

    def update_escalation_config(self, **kwargs) -> None:
        """Update escalation configuration"""

        if 'escalation_enabled' in kwargs:
            self.escalation_enabled = kwargs['escalation_enabled']

        if 'escalation_threshold' in kwargs:
            threshold = float(kwargs['escalation_threshold'])
            if 0.0 <= threshold <= 1.0:
                self.escalation_threshold = threshold
            else:
                logger.warning(f"Invalid escalation threshold: {threshold}, must be between 0.0 and 1.0")

        if 'confidence_check_method' in kwargs:
            method = kwargs['confidence_check_method']
            valid_methods = ['weighted_average', 'minimum', 'average']
            if method in valid_methods:
                self.confidence_check_method = method
            else:
                logger.warning(f"Invalid confidence check method: {method}, must be one of {valid_methods}")

        if 'min_entities_required' in kwargs:
            min_entities = int(kwargs['min_entities_required'])
            if min_entities >= 0:
                self.min_entities_required = min_entities
            else:
                logger.warning(f"Invalid min entities required: {min_entities}, must be >= 0")