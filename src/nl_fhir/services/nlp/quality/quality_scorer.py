"""
Quality Scorer for Medical Entity Extraction
Calculates quality scores for extracted medical entities.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class QualityScorer:
    """Calculates quality scores for medical entity extraction results"""

    def calculate_quality_score(self, entities: Dict[str, List[Dict[str, Any]]], text: str) -> float:
        """
        Calculate quality score for extracted entities

        Args:
            entities: Dictionary of extracted entities by type
            text: Original input text

        Returns:
            float: Quality score between 0.0 and 1.0
        """
        try:
            # Count total entities
            total_entities = sum(len(entity_list) for entity_list in entities.values())

            # Base score based on entity count
            if total_entities == 0:
                return 0.0

            # Calculate confidence-weighted score
            confidence_scores = []
            medical_entity_count = 0

            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    confidence = entity.get('confidence', 0.0)
                    confidence_scores.append(confidence)

                    # Weight medical entities more heavily
                    if entity_type in ['medications', 'conditions', 'procedures', 'lab_tests']:
                        medical_entity_count += 1
                        confidence_scores.append(confidence)  # Double weight for medical entities

            if not confidence_scores:
                return 0.0

            # Average confidence score
            avg_confidence = sum(confidence_scores) / len(confidence_scores)

            # Bonus for having medical entities
            medical_bonus = min(0.2, medical_entity_count * 0.05)

            # Text length consideration - longer texts might have more entities
            text_length_bonus = min(0.1, len(text.split()) / 100)

            # Calculate final score
            quality_score = avg_confidence + medical_bonus + text_length_bonus

            # Ensure score is between 0.0 and 1.0
            return min(1.0, max(0.0, quality_score))

        except Exception as e:
            logger.warning(f"Error calculating quality score: {e}")
            return 0.5  # Return neutral score on error

    def calculate_confidence_metrics(self, entities: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """
        Calculate detailed confidence metrics for entities

        Args:
            entities: Dictionary of extracted entities by type

        Returns:
            Dict with confidence metrics
        """

        metrics = {
            "average_confidence": 0.0,
            "weighted_confidence": 0.0,
            "minimum_confidence": 1.0,
            "medical_entity_confidence": 0.0,
            "total_entities": 0
        }

        try:
            total_entities = 0
            total_confidence_sum = 0.0
            confidence_values = []
            medical_confidence_sum = 0.0
            medical_entity_count = 0
            weighted_sum = 0.0
            weight_sum = 0.0

            for category, entity_list in entities.items():
                for entity in entity_list:
                    confidence = entity.get('confidence', 0.0)
                    total_entities += 1
                    total_confidence_sum += confidence
                    confidence_values.append(confidence)

                    # Calculate weighted confidence
                    if category in ['medications', 'conditions']:
                        weight = 3.0  # Critical for medical safety
                        medical_confidence_sum += confidence
                        medical_entity_count += 1
                    elif category in ['dosages', 'frequencies']:
                        weight = 2.0  # Important for medication safety
                    else:
                        weight = 1.0  # Standard weight

                    weighted_sum += confidence * weight
                    weight_sum += weight

            if total_entities > 0:
                metrics["average_confidence"] = total_confidence_sum / total_entities
                metrics["total_entities"] = total_entities

            if confidence_values:
                metrics["minimum_confidence"] = min(confidence_values)

            if weight_sum > 0:
                metrics["weighted_confidence"] = weighted_sum / weight_sum

            if medical_entity_count > 0:
                metrics["medical_entity_confidence"] = medical_confidence_sum / medical_entity_count

        except Exception as e:
            logger.warning(f"Error calculating confidence metrics: {e}")

        return metrics

    def assess_extraction_completeness(self, entities: Dict[str, List[Dict[str, Any]]], text: str) -> Dict[str, Any]:
        """
        Assess completeness of medical entity extraction

        Args:
            entities: Dictionary of extracted entities by type
            text: Original input text

        Returns:
            Dict with completeness assessment
        """

        assessment = {
            "is_complete": False,
            "missing_categories": [],
            "entity_density": 0.0,
            "expected_entities": 0,
            "found_entities": 0,
            "completeness_score": 0.0
        }

        try:
            text_lower = text.lower()
            total_entities = sum(len(entity_list) for entity_list in entities.values())
            words = len(text.split())

            # Calculate entity density
            assessment["entity_density"] = total_entities / max(words, 1)
            assessment["found_entities"] = total_entities

            # Check for expected categories based on text content
            expected_categories = []

            # Check for medication indicators
            if any(word in text_lower for word in ["prescribe", "medication", "mg", "daily", "tablet", "capsule"]):
                expected_categories.extend(["medications", "dosages", "frequencies"])

            # Check for patient indicators
            if any(word in text_lower for word in ["patient", "mr.", "mrs.", "ms."]):
                expected_categories.append("patients")

            # Check for lab/procedure indicators
            if any(word in text_lower for word in ["order", "lab", "test", "cbc", "x-ray", "scan"]):
                expected_categories.extend(["lab_tests", "procedures"])

            # Check for condition indicators
            if any(word in text_lower for word in ["diagnosis", "condition", "disease", "diabetes", "hypertension"]):
                expected_categories.append("conditions")

            assessment["expected_entities"] = len(expected_categories)

            # Check which expected categories are missing
            missing_categories = []
            for category in expected_categories:
                if len(entities.get(category, [])) == 0:
                    missing_categories.append(category)

            assessment["missing_categories"] = missing_categories

            # Calculate completeness score
            if expected_categories:
                found_categories = len(expected_categories) - len(missing_categories)
                assessment["completeness_score"] = found_categories / len(expected_categories)
            else:
                # If no specific categories expected, base on entity density
                assessment["completeness_score"] = min(1.0, assessment["entity_density"] * 20)

            # Determine if extraction is complete
            assessment["is_complete"] = (
                len(missing_categories) == 0 and
                assessment["completeness_score"] >= 0.8 and
                total_entities > 0
            )

        except Exception as e:
            logger.warning(f"Error assessing extraction completeness: {e}")

        return assessment