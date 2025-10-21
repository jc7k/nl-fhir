"""
Compatibility Shim for NLP Models
This module provides backward compatibility after refactoring the monolithic models.py
into smaller, focused modules. All original APIs are preserved.
"""

import logging
from typing import Optional, Dict, Any, List

from .model_managers.transformer_manager import TransformerManager
from .model_managers.spacy_manager import SpacyManager
from .model_managers.medspacy_manager import MedSpacyManager
from .extractors.medical_entity_extractor import MedicalEntityExtractor
from .extractors.regex_extractor import RegexExtractor
from .quality.quality_scorer import QualityScorer

logger = logging.getLogger(__name__)


class NLPModelManager:
    """
    Compatibility wrapper that maintains the original NLPModelManager API
    while delegating to the new modular architecture.
    """

    def __init__(self):
        # Initialize the new modular components
        self.transformer_manager = TransformerManager()
        self.spacy_manager = SpacyManager()
        self.medspacy_manager = MedSpacyManager()
        self.medical_extractor = MedicalEntityExtractor()
        self.regex_extractor = RegexExtractor()
        self.quality_scorer = QualityScorer()

    # Model loading methods - delegate to appropriate managers
    def load_medical_ner_model(self, model_name: str = "clinical-ai-apollo/Medical-NER") -> Optional[Any]:
        """Load and cache medical NER model with error handling"""
        return self.transformer_manager.load_medical_ner_model(model_name)

    def load_spacy_medical_nlp(self, model_name: str = "en_core_web_sm") -> Optional[Any]:
        """Load spaCy model for enhanced medical NLP"""
        return self.spacy_manager.load_spacy_medical_nlp(model_name)

    def load_medspacy_clinical_engine(self, base_model: str = "en_core_web_sm") -> Optional[Any]:
        """Load MedSpaCy Clinical Intelligence Engine with ConText and clinical NER"""
        return self.medspacy_manager.load_medspacy_clinical_engine(base_model)

    def load_sentence_transformer(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Optional[Any]:
        """Load sentence transformer for embeddings"""
        return self.transformer_manager.load_sentence_transformer(model_name)

    def load_fallback_nlp(self) -> Dict[str, Any]:
        """Enhanced fallback regex-based NLP for medical entity extraction"""
        # The regex extractor handles pattern management internally
        # For compatibility, return a dict with pattern info
        return {
            "type": "regex_fallback_patterns",
            "patterns": self.regex_extractor.get_pattern_info()
        }

    # Main extraction method - delegate to medical extractor
    def extract_medical_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract medical entities using 4-tier approach with LLM escalation:
        Tier 1: spaCy → Tier 2: Transformers NER → Tier 3: Regex → Tier 3.5: LLM Escalation
        """
        return self.medical_extractor.extract_medical_entities(text)

    # Quality and status methods
    def _calculate_quality_score(self, entities: Dict[str, List[Dict[str, Any]]], text: str) -> float:
        """Calculate quality score for extracted entities"""
        return self.quality_scorer.calculate_quality_score(entities, text)

    def _calculate_weighted_confidence(self, entities: Dict[str, List[Dict[str, Any]]]) -> float:
        """
        Calculate weighted confidence for medical entities (medical safety critical).

        Weighting:
        - medications/conditions: 3x (critical for medical safety)
        - dosages/frequencies: 2x (important for medication safety)
        - others: 1x (standard weight)

        Args:
            entities: Dictionary of extracted entities by category

        Returns:
            float: Weighted confidence score between 0.0 and 1.0
        """
        metrics = self.quality_scorer.calculate_confidence_metrics(entities)
        return metrics.get("weighted_confidence", 0.0)

    def get_model_status(self) -> Dict[str, str]:
        """Get status of all loaded models"""
        status = {}
        status.update(self.transformer_manager.get_model_status())
        status.update(self.spacy_manager.get_model_status())
        status.update(self.medspacy_manager.get_model_status())
        return status

    def clear_models(self):
        """Clear model cache to free memory"""
        self.transformer_manager.clear_models()
        self.spacy_manager.clear_models()
        self.medspacy_manager.clear_models()
        logger.info("Cleared all NLP model caches")

    # Legacy methods for backward compatibility (these delegate to the medical extractor)
    def _extract_with_medspacy_clinical(self, text: str, nlp) -> Dict[str, List[Dict[str, Any]]]:
        """Legacy method - delegates to medical extractor"""
        return self.medical_extractor._extract_with_medspacy_clinical(text, nlp)

    def _extract_with_transformers(self, text: str, ner_pipeline) -> Dict[str, List[Dict[str, Any]]]:
        """Legacy method - delegates to medical extractor"""
        return self.medical_extractor._extract_with_transformers(text, ner_pipeline)

    def _extract_with_spacy_medical(self, text: str, nlp) -> Dict[str, List[Dict[str, Any]]]:
        """Legacy method - delegates to medical extractor"""
        return self.medical_extractor._extract_with_spacy_medical(text, nlp)

    def _extract_with_regex(self, text: str, regex_nlp: Dict) -> Dict[str, List[Dict[str, Any]]]:
        """Legacy method - delegates to regex extractor"""
        return self.regex_extractor.extract_entities(text)

    def _is_extraction_sufficient(self, result: Dict[str, List[Dict[str, Any]]], text: str) -> bool:
        """Legacy method - delegates to medical extractor"""
        return self.medical_extractor._is_extraction_sufficient(result, text)

    def _should_escalate_to_llm(self, result: Dict[str, List[Dict[str, Any]]], text: str) -> bool:
        """Legacy method - delegates to escalation manager"""
        from .quality.escalation_manager import EscalationManager
        escalation_manager = EscalationManager()
        return escalation_manager.should_escalate_to_llm(result, text)

    def _extract_with_llm_escalation(self, text: str, request_id: str = "llm-escalation") -> Dict[str, List[Dict[str, Any]]]:
        """Legacy method - delegates to LLM extractor"""
        from .extractors.llm_extractor import LLMExtractor
        llm_extractor = LLMExtractor()
        return llm_extractor.extract_entities_with_llm(text, request_id)

    # Clinical context methods (delegate to medical extractor)
    def _get_clinical_context(self, entity) -> Dict[str, Any]:
        """Legacy method - delegates to medical extractor"""
        return self.medical_extractor._get_clinical_context(entity)

    def _adjust_confidence_for_clinical_context(self, base_confidence: float, clinical_context: Dict[str, Any]) -> float:
        """Legacy method - delegates to medical extractor"""
        return self.medical_extractor._adjust_confidence_for_clinical_context(base_confidence, clinical_context)

    def _extract_dosages_and_frequencies_medspacy(self, text: str, result: Dict) -> None:
        """Legacy method - delegates to medical extractor"""
        return self.medical_extractor._extract_dosages_and_frequencies_medspacy(text, result)

    # MedSpaCy configuration method (delegate to MedSpaCy manager)
    def _configure_medspacy_pipeline(self, nlp) -> Any:
        """Legacy method - delegates to MedSpaCy manager"""
        self.medspacy_manager._configure_enhanced_clinical_rules(nlp)
        return nlp


# Global model manager instance (maintains compatibility)
model_manager = NLPModelManager()


# Module-level functions (maintain compatibility)
def get_medical_nlp_model():
    """Get cached medical NLP model"""
    return model_manager.load_medical_ner_model()


def extract_medical_entities(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Extract medical entities from text"""
    return model_manager.extract_medical_entities(text)


def get_sentence_transformer(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """Get cached sentence transformer model"""
    return model_manager.load_sentence_transformer(model_name)


# Export availability constants for backward compatibility
try:
    from transformers import pipeline
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    import medspacy
    from medspacy.ner import TargetRule
    MEDSPACY_AVAILABLE = True
except ImportError:
    MEDSPACY_AVAILABLE = False