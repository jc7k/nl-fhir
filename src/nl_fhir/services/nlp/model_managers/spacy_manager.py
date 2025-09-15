"""
spaCy Model Management
Handles loading and caching of spaCy models for enhanced medical NLP.
"""

import logging
import threading
import time
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

try:
    import spacy
    SPACY_AVAILABLE = True
    logger.info("spaCy available for enhanced medical NLP")
except ImportError:
    logger.warning("spaCy not available - falling back to regex")
    SPACY_AVAILABLE = False


class SpacyManager:
    """Manages spaCy models with caching and optimization"""

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialization_status = {}

    def load_spacy_medical_nlp(self, model_name: str = "en_core_web_sm") -> Optional[Any]:
        """Load spaCy model for enhanced medical NLP"""

        if not SPACY_AVAILABLE:
            logger.warning("spaCy not available, returning None")
            return None

        with self._lock:
            spacy_key = f"spacy_{model_name}"
            if spacy_key in self._models:
                return self._models[spacy_key]

            try:
                logger.info(f"Loading spaCy medical NLP model: {model_name}")
                start_time = time.time()

                nlp = spacy.load(model_name)

                # Test basic functionality
                test_doc = nlp("Test patient John Doe on 5mg Lisinopril daily")
                if not test_doc:
                    raise ValueError(f"spaCy model {model_name} failed validation")

                load_time = time.time() - start_time
                logger.info(f"Successfully loaded spaCy model in {load_time:.2f}s")

                self._models[spacy_key] = nlp
                self._initialization_status[spacy_key] = "loaded"

                return nlp

            except Exception as e:
                logger.error(f"Failed to load spaCy model {model_name}: {e}")
                self._initialization_status[spacy_key] = "failed"
                return None

    def is_available(self) -> bool:
        """Check if spaCy is available"""
        return SPACY_AVAILABLE

    def get_model_status(self) -> Dict[str, str]:
        """Get status of all loaded spaCy models"""
        return {k: v for k, v in self._initialization_status.items()
                if k.startswith("spacy_")}

    def clear_models(self):
        """Clear spaCy model cache to free memory"""
        with self._lock:
            spacy_keys = [k for k in self._models.keys() if k.startswith("spacy_")]
            for key in spacy_keys:
                self._models.pop(key, None)
                self._initialization_status.pop(key, None)
            logger.info("Cleared spaCy model cache")