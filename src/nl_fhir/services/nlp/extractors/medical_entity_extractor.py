"""
Medical Entity Extractor
Coordinates 4-tier extraction approach: MedSpaCy -> Transformers -> Regex -> LLM Escalation
"""

import logging
import re
from typing import Dict, List, Any

from ..model_managers.medspacy_manager import MedSpacyManager
from ..model_managers.spacy_manager import SpacyManager
from ..model_managers.transformer_manager import TransformerManager
from .regex_extractor import RegexExtractor
from .llm_extractor import LLMExtractor

logger = logging.getLogger(__name__)


class MedicalEntityExtractor:
    """Coordinates 4-tier medical entity extraction with LLM escalation"""

    def __init__(self):
        self.medspacy_manager = MedSpacyManager()
        self.spacy_manager = SpacyManager()
        self.transformer_manager = TransformerManager()
        self.regex_extractor = RegexExtractor()
        self.llm_extractor = LLMExtractor()

    def extract_medical_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract medical entities using 4-tier approach with LLM escalation:
        Tier 1: spaCy → Tier 2: Transformers NER → Tier 3: Regex → Tier 3.5: LLM Escalation

        The LLM escalation tier (3.5) is triggered when confidence is below the medical safety
        threshold (default 85%), providing high-accuracy structured output for critical medical data.
        """

        # TIER 1: MedSpaCy Clinical Intelligence Engine (Enhanced for Epic 2.5)
        medspacy_nlp = self.medspacy_manager.load_medspacy_clinical_engine()
        if medspacy_nlp and self.medspacy_manager.is_available():
            result = self._extract_with_medspacy_clinical(text, medspacy_nlp)
            if self._is_extraction_sufficient(result, text):
                from ..quality.escalation_manager import EscalationManager
                escalation_manager = EscalationManager()
                if not escalation_manager.should_escalate_to_llm(result, text):
                    logger.info("Tier 1 (MedSpaCy Clinical) successful: sufficient confidence for medical safety")
                    return result
                else:
                    logger.info("Tier 1 (MedSpaCy Clinical) insufficient confidence, continuing to Tier 2")
        else:
            # Fallback to basic spaCy if MedSpaCy unavailable
            spacy_nlp = self.spacy_manager.load_spacy_medical_nlp()
            if spacy_nlp:
                result = self._extract_with_spacy_medical(text, spacy_nlp)
                if self._is_extraction_sufficient(result, text):
                    from ..quality.escalation_manager import EscalationManager
                    escalation_manager = EscalationManager()
                    if not escalation_manager.should_escalate_to_llm(result, text):
                        logger.info("Tier 1 (spaCy fallback) successful: sufficient confidence for medical safety")
                        return result
                    else:
                        logger.info("Tier 1 (spaCy fallback) insufficient confidence, continuing to Tier 2")

        # TIER 2: Specialized medical NER model (slower, sophisticated medical entity recognition)
        ner_model = self.transformer_manager.load_medical_ner_model()
        if ner_model and not isinstance(ner_model, dict):
            result = self._extract_with_transformers(text, ner_model)
            if self._is_extraction_sufficient(result, text):
                from ..quality.escalation_manager import EscalationManager
                escalation_manager = EscalationManager()
                if not escalation_manager.should_escalate_to_llm(result, text):
                    logger.info("Tier 2 (Transformers) successful: sufficient confidence for medical safety")
                    return result
                else:
                    logger.info("Tier 2 (Transformers) insufficient confidence, continuing to Tier 3")

        # TIER 3: Regex fallback patterns (fastest, most basic)
        result = self.regex_extractor.extract_entities(text)

        # TIER 3.5: LLM ESCALATION (triggered by low confidence for medical safety)
        from ..quality.escalation_manager import EscalationManager
        escalation_manager = EscalationManager()

        if escalation_manager.should_escalate_to_llm(result, text):
            logger.info("Tier 3.5: Escalating to LLM for medical safety and accuracy")

            # Generate unique request ID for tracking
            import uuid
            request_id = f"escalation-{str(uuid.uuid4())[:8]}"

            llm_result = self.llm_extractor.extract_entities_with_llm(text, request_id)

            # Validate LLM result has better entity coverage
            llm_entity_count = sum(len(entities) for entities in llm_result.values())
            regex_entity_count = sum(len(entities) for entities in result.values())

            if llm_entity_count >= regex_entity_count:
                logger.info(f"LLM escalation successful: {llm_entity_count} entities vs {regex_entity_count} from regex")
                return llm_result
            else:
                logger.warning(f"LLM escalation yielded fewer entities ({llm_entity_count} vs {regex_entity_count}), using regex result")
                return result
        else:
            logger.info("Tier 3 (Regex) sufficient: confidence meets medical safety threshold")
            return result

    def _extract_with_medspacy_clinical(self, text: str, nlp) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract medical entities using MedSpaCy Clinical Intelligence Engine
        This method implements the core Epic 2.5 enhancement with clinical context detection
        """

        result = {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "patients": [],
            "conditions": [],
            "procedures": [],
            "lab_tests": [],
            "weights": []
        }

        try:
            # Process text with MedSpaCy clinical pipeline
            doc = nlp(text)

            # Extract entities with clinical context
            for ent in doc.ents:
                # Get clinical context information
                clinical_context = self._get_clinical_context(ent)

                entity_info = {
                    "text": ent.text,
                    "confidence": 0.8,  # Base confidence for MedSpaCy entities
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "method": "medspacy_clinical",
                    "clinical_context": clinical_context
                }

                # Adjust confidence based on clinical context
                entity_info["confidence"] = self._adjust_confidence_for_clinical_context(
                    entity_info["confidence"], clinical_context
                )

                # Map MedSpaCy entity labels to our categories
                if ent.label_ == "MEDICATION":
                    result["medications"].append(entity_info)
                elif ent.label_ == "CONDITION":
                    result["conditions"].append(entity_info)
                elif ent.label_ == "LAB_TEST":
                    result["lab_tests"].append(entity_info)
                elif ent.label_ == "PROCEDURE":
                    result["procedures"].append(entity_info)
                elif ent.label_ == "VITAL_SIGN":
                    result["procedures"].append(entity_info)  # Classify vital signs as procedures

            # Extract additional entities using spaCy's NER for persons
            for ent in doc.ents:
                if ent.label_ in ["PERSON"]:
                    entity_info = {
                        "text": ent.text,
                        "confidence": 0.9,  # High confidence for person entities
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "method": "medspacy_clinical_spacy_ner"
                    }
                    result["patients"].append(entity_info)

            # Enhanced pattern-based extraction for dosages and frequencies
            self._extract_dosages_and_frequencies_medspacy(text, result)

            # Extract weights using regex patterns (pediatric dosing support)
            self._extract_weights_with_regex(text, result)

            logger.info(f"MedSpaCy clinical extraction found {sum(len(entities) for entities in result.values())} entities")

            return result

        except Exception as e:
            logger.error(f"MedSpaCy clinical extraction failed: {e}")
            # Fallback to basic spaCy extraction
            return self._extract_with_spacy_medical(text, nlp)

    def _get_clinical_context(self, entity) -> Dict[str, Any]:
        """Extract clinical context information from MedSpaCy entity"""
        context = {
            "is_negated": False,
            "is_hypothetical": False,
            "is_historical": False,
            "certainty": "certain"
        }

        try:
            # Check for clinical context attributes added by ConText component
            if hasattr(entity, 'negation'):
                context["is_negated"] = entity.negation
            if hasattr(entity, 'hypothetical'):
                context["is_hypothetical"] = entity.hypothetical
            if hasattr(entity, 'historical'):
                context["is_historical"] = entity.historical
            if hasattr(entity, 'certainty'):
                context["certainty"] = entity.certainty

        except Exception as e:
            logger.warning(f"Failed to extract clinical context: {e}")

        return context

    def _adjust_confidence_for_clinical_context(self, base_confidence: float, clinical_context: Dict[str, Any]) -> float:
        """Adjust entity confidence based on clinical context"""

        adjusted_confidence = base_confidence

        # Reduce confidence for negated entities (still important for clinical record)
        if clinical_context.get("is_negated", False):
            adjusted_confidence *= 0.7

        # Reduce confidence for hypothetical entities
        if clinical_context.get("is_hypothetical", False):
            adjusted_confidence *= 0.6

        # Slightly reduce confidence for historical entities
        if clinical_context.get("is_historical", False):
            adjusted_confidence *= 0.85

        # Adjust based on certainty
        certainty = clinical_context.get("certainty", "certain")
        if certainty == "uncertain":
            adjusted_confidence *= 0.7
        elif certainty == "possible":
            adjusted_confidence *= 0.8

        return min(adjusted_confidence, 1.0)

    def _extract_dosages_and_frequencies_medspacy(self, text: str, result: Dict) -> None:
        """Enhanced dosage and frequency extraction with clinical patterns"""

        # Clinical dosage patterns (enhanced for medical accuracy)
        dosage_pattern = re.compile(
            r'(\d+(?:\.\d+)?)\s*(mg|gram|g|tablet|capsule|ml|mcg|iu|units?|milligrams?|grams?|milliliters?)',
            re.IGNORECASE
        )

        # Clinical frequency patterns with medical abbreviations
        frequency_pattern = re.compile(
            r'(?:daily|twice\s+(?:a\s+)?daily|three\s+times|four\s+times|once|weekly|monthly|'
            r'bid|tid|qid|qhs|prn|q\d+h|every\s+\d+\s+(?:hours?|days?|weeks?)|'
            r'\d+\s*(?:times?|x)\s*(?:per|/)?\s*(?:day|week|month|d|wk))',
            re.IGNORECASE
        )

        # Extract dosages
        for match in dosage_pattern.finditer(text):
            dosage_info = {
                "text": match.group(0),
                "confidence": 0.85,  # High confidence for pattern-based extraction
                "start": match.start(),
                "end": match.end(),
                "method": "medspacy_clinical_pattern"
            }
            result["dosages"].append(dosage_info)

        # Extract frequencies
        for match in frequency_pattern.finditer(text):
            frequency_info = {
                "text": match.group(0),
                "confidence": 0.85,  # High confidence for pattern-based extraction
                "start": match.start(),
                "end": match.end(),
                "method": "medspacy_clinical_pattern"
            }
            result["frequencies"].append(frequency_info)

    def _extract_with_transformers(self, text: str, ner_pipeline) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities using transformers NER pipeline"""
        try:
            entities = ner_pipeline(text)

            result = {
                "medications": [],
                "dosages": [],
                "frequencies": [],
                "patients": [],
                "conditions": [],
                "procedures": [],
                "lab_tests": [],
                "weights": []
            }

            for entity in entities:
                entity_type = entity.get("entity_group", "").lower()
                entity_text = entity.get("word", "").strip()
                confidence = entity.get("score", 0.0)

                # Quality filtering: Skip entities that are clearly noise
                if self._should_skip_entity(entity_type, entity_text, confidence):
                    continue

                entity_info = {
                    "text": entity_text,
                    "confidence": confidence,
                    "start": entity.get("start", 0),
                    "end": entity.get("end", 0),
                    "method": "transformers_ner"
                }

                # Map entity types (enhanced mapping for medical accuracy)
                self._map_entity_to_category(entity_type, entity_text, entity_info, result)

            return result

        except Exception as e:
            logger.error(f"Transformers extraction failed: {e}")
            return self.regex_extractor.extract_entities(text)

    def _should_skip_entity(self, entity_type: str, entity_text: str, confidence: float) -> bool:
        """Determine if entity should be skipped based on quality filters"""

        entity_type_lower = entity_type.lower()

        # Apply type-specific thresholds
        if "drug" in entity_type_lower or "medication" in entity_type_lower:
            # Higher threshold for medications (false positives dangerous)
            if confidence < 0.6:
                return True
        elif "diagnostic_procedure" in entity_type_lower:
            # Lower threshold for diagnostic procedures (false negatives costly)
            if confidence < 0.4:
                return True
        else:
            # Standard threshold for other types
            if confidence < 0.5:
                return True

        # Length-based filtering (medical terms are rarely 1-2 characters)
        if len(entity_text) <= 2:
            return True

        # Common word filtering (avoid medical terms that are too generic)
        generic_words = {'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
        if entity_text.lower() in generic_words:
            return True

        return False

    def _map_entity_to_category(self, entity_type: str, entity_text: str, entity_info: Dict, result: Dict) -> None:
        """Map entity types to result categories"""

        if "drug" in entity_type or "medication" in entity_type:
            result["medications"].append(entity_info)
        elif "dosage" in entity_type or "dose" in entity_type:
            result["dosages"].append(entity_info)
        elif "frequency" in entity_type:
            result["frequencies"].append(entity_info)
        elif "patient" in entity_type or "person" in entity_type:
            result["patients"].append(entity_info)
        elif "condition" in entity_type or "disease" in entity_type:
            result["conditions"].append(entity_info)
        elif "diagnostic_procedure" in entity_type:
            # Classify diagnostic procedures as lab tests or procedures based on medical context
            text_lower = entity_text.lower()
            lab_indicators = {'cbc', 'blood', 'urine', 'glucose', 'cholesterol', 'creatinine', 'troponin', 'hba1c', 'panel'}

            if any(indicator in text_lower for indicator in lab_indicators):
                result["lab_tests"].append(entity_info)
            else:
                result["procedures"].append(entity_info)

    def _extract_with_spacy_medical(self, text: str, nlp) -> Dict[str, List[Dict[str, Any]]]:
        """Extract medical entities using enhanced spaCy with medical patterns"""

        result = {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "patients": [],
            "conditions": [],
            "procedures": [],
            "lab_tests": [],
            "weights": []
        }

        try:
            doc = nlp(text)

            # Enhanced medical terminology lists
            medical_terms = self._get_medical_terminology()

            # Extract using spaCy's linguistic analysis
            self._extract_spacy_entities(doc, medical_terms, result)

            # Extract multi-word medical terms using noun phrases
            self._extract_spacy_phrases(doc, medical_terms, result)

            # Extract patient names using NER
            self._extract_spacy_persons(doc, result)

        except Exception as e:
            logger.error(f"spaCy medical extraction failed: {e}")

        return result

    def _get_medical_terminology(self) -> Dict[str, set]:
        """Get medical terminology dictionaries"""

        return {
            "medication_terms": {
                "tadalafil", "lisinopril", "metformin", "aspirin", "warfarin",
                "atorvastatin", "amlodipine", "omeprazole", "losartan", "gabapentin"
            },
            "condition_terms": {
                "dysfunction", "hypertension", "diabetes", "pain", "bleeding",
                "heart failure", "depression", "anxiety", "arthritis", "copd"
            },
            "procedure_terms": {
                "ekg", "ecg", "troponins", "cbc", "metabolic panel", "x-ray",
                "mri", "ct scan", "ultrasound", "biopsy"
            },
            "lab_terms": {
                "troponins", "cbc", "comprehensive metabolic panel", "lipid panel",
                "hba1c", "creatinine", "glucose", "cholesterol"
            },
            "frequency_terms": {
                "daily", "twice daily", "three times", "as needed", "prn",
                "bid", "tid", "qid", "once", "weekly"
            }
        }

    def _extract_spacy_entities(self, doc, medical_terms: Dict, result: Dict) -> None:
        """Extract entities using spaCy token analysis"""

        for token in doc:
            token_lower = token.text.lower()

            # Medications (look for proper nouns that are medical terms)
            if (token.pos_ == "PROPN" or token.pos_ == "NOUN") and not token.is_stop:
                if token_lower in medical_terms["medication_terms"]:
                    result["medications"].append({
                        'text': token.text,
                        'confidence': 0.9,
                        'start': token.idx,
                        'end': token.idx + len(token.text),
                        'method': 'spacy_medical'
                    })

            # Dosages (numbers followed by units)
            if token.like_num and token.i + 1 < len(doc):
                next_token = doc[token.i + 1]
                if next_token.text.lower() in ["mg", "gram", "ml", "mcg", "tablet", "capsule"]:
                    dosage_text = f"{token.text}{next_token.text}"
                    result["dosages"].append({
                        'text': dosage_text,
                        'confidence': 0.9,
                        'start': token.idx,
                        'end': next_token.idx + len(next_token.text),
                        'method': 'spacy_medical'
                    })

            # Frequencies and conditions
            if token_lower in medical_terms["frequency_terms"]:
                result["frequencies"].append({
                    'text': token.text,
                    'confidence': 0.8,
                    'start': token.idx,
                    'end': token.idx + len(token.text),
                    'method': 'spacy_medical'
                })

            if token_lower in medical_terms["condition_terms"]:
                result["conditions"].append({
                    'text': token.text,
                    'confidence': 0.8,
                    'start': token.idx,
                    'end': token.idx + len(token.text),
                    'method': 'spacy_medical'
                })

    def _extract_spacy_phrases(self, doc, medical_terms: Dict, result: Dict) -> None:
        """Extract multi-word medical terms using noun phrases"""

        for chunk in doc.noun_chunks:
            chunk_lower = chunk.text.lower()

            if chunk_lower in medical_terms["procedure_terms"] or chunk_lower in medical_terms["lab_terms"]:
                category = "procedures" if chunk_lower in medical_terms["procedure_terms"] else "lab_tests"
                result[category].append({
                    'text': chunk.text,
                    'confidence': 0.85,
                    'start': chunk.start_char,
                    'end': chunk.end_char,
                    'method': 'spacy_medical_phrase'
                })

    def _extract_spacy_persons(self, doc, result: Dict) -> None:
        """Extract patient names using NER"""

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                result["patients"].append({
                    'text': ent.text,
                    'confidence': 0.9,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'method': 'spacy_ner'
                })

    def _is_extraction_sufficient(self, result: Dict[str, List[Dict[str, Any]]], text: str) -> bool:
        """Check if extraction quality is sufficient to avoid escalation"""

        total_entities = sum(len(entities) for entities in result.values())

        # Rule 1: Must have at least one entity for clinical text
        if total_entities == 0:
            return False

        # Rule 2: For medication-related text, must have BOTH medication AND dosage
        text_lower = text.lower()
        if any(med_word in text_lower for med_word in ["prescribe", "medication", "mg", "daily", "tablet"]):
            has_medication = len(result.get("medications", [])) > 0
            has_dosage = len(result.get("dosages", [])) > 0
            if not (has_medication and has_dosage):
                return False

        # Rule 3: Quality threshold - expect reasonable entity count
        words = len(text.split())
        entity_density = total_entities / max(words, 1)

        # Should have at least 1 entity per 20 words for clinical text
        if entity_density < 0.05:
            return False

        return True

    def _extract_weights_with_regex(self, text: str, result: Dict) -> None:
        """Extract patient weights using regex patterns (for pediatric dosing)"""

        # Use the same regex extractor for consistency
        regex_results = self.regex_extractor.extract_entities(text)

        # Merge weight entities from regex extractor
        if "weights" in regex_results:
            for weight in regex_results["weights"]:
                # Avoid duplicates
                weight_text = weight.get("text", "").lower()
                existing_weights = [w.get("text", "").lower() for w in result.get("weights", [])]

                if weight_text not in existing_weights:
                    result["weights"].append({
                        "text": weight["text"],
                        "confidence": weight.get("confidence", 0.8),
                        "start": weight.get("start", 0),
                        "end": weight.get("end", 0),
                        "method": "medspacy_regex_weight"
                    })