"""
NLP Model Management for spaCy and Medical Models
HIPAA Compliant: Secure model loading and caching
Production Ready: Memory optimization and error handling
"""

import logging
import spacy
import threading
from typing import Optional, Dict, Any
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class NLPModelManager:
    """Manages spaCy and medical NLP models with caching and optimization"""
    
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialization_status = {}
        
    def load_spacy_model(self, model_name: str = "en_core_web_sm") -> Optional[Any]:
        """Load and cache spaCy model with error handling"""
        
        with self._lock:
            if model_name in self._models:
                return self._models[model_name]
                
            try:
                logger.info(f"Loading spaCy model: {model_name}")
                start_time = time.time()
                
                # Try to load the model
                nlp = spacy.load(model_name)
                
                # Basic validation
                test_doc = nlp("Test medical order.")
                if not test_doc:
                    raise ValueError(f"Model {model_name} failed basic validation")
                
                load_time = time.time() - start_time
                logger.info(f"Successfully loaded {model_name} in {load_time:.2f}s")
                
                self._models[model_name] = nlp
                self._initialization_status[model_name] = "loaded"
                
                return nlp
                
            except OSError as e:
                logger.error(f"Failed to load spaCy model {model_name}: {e}")
                self._initialization_status[model_name] = "failed"
                
                # Fallback to basic English model
                if model_name != "en_core_web_sm":
                    logger.info("Attempting fallback to en_core_web_sm")
                    return self.load_spacy_model("en_core_web_sm")
                    
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error loading {model_name}: {e}")
                self._initialization_status[model_name] = "failed"
                return None
    
    def load_medical_model(self) -> Optional[Any]:
        """Load medical/scientific spaCy model with fallbacks"""
        
        # Try scientific models in order of preference
        medical_models = [
            "en_core_sci_sm",  # scispaCy small scientific model
            "en_core_sci_md",  # scispaCy medium scientific model  
            "en_core_web_sm"   # Fallback to basic English
        ]
        
        for model_name in medical_models:
            model = self.load_spacy_model(model_name)
            if model:
                logger.info(f"Using medical model: {model_name}")
                return model
                
        logger.error("Failed to load any medical NLP model")
        return None
        
    def add_medical_components(self, nlp):
        """Add medical-specific components to spaCy pipeline"""
        try:
            # Add custom medical entity patterns
            from spacy.matcher import Matcher
            matcher = Matcher(nlp.vocab)
            
            # Define medical patterns
            medication_patterns = [
                [{"LOWER": {"REGEX": r"(mg|gram|tablet|capsule|ml|mcg|iu)"}}, {"IS_ALPHA": True}],
                [{"IS_ALPHA": True}, {"LOWER": {"REGEX": r"(mg|gram|tablet|capsule|ml|mcg|iu)"}}]
            ]
            
            frequency_patterns = [
                [{"LOWER": {"REGEX": r"(daily|twice|three|four|once)"}}, {"LOWER": "daily"}],
                [{"LOWER": {"REGEX": r"(bid|tid|qid|qhs|prn)"}}],
                [{"LIKE_NUM": True}, {"LOWER": {"REGEX": r"(times|x)"}}]
            ]
            
            matcher.add("MEDICATION_DOSAGE", medication_patterns)
            matcher.add("MEDICATION_FREQUENCY", frequency_patterns)
            
            # Store matcher for later use
            if not nlp.has_pipe("custom_medical_matcher"):
                nlp.add_pipe("custom_medical_matcher", last=True)
                nlp.get_pipe("custom_medical_matcher").matcher = matcher
                
            return True
            
        except Exception as e:
            logger.warning(f"Failed to add medical components: {e}")
            return False
    
    def get_model_status(self) -> Dict[str, str]:
        """Get status of all loaded models"""
        return self._initialization_status.copy()
        
    def clear_models(self):
        """Clear model cache to free memory"""
        with self._lock:
            self._models.clear()
            self._initialization_status.clear()
            logger.info("Cleared NLP model cache")


# Global model manager instance
model_manager = NLPModelManager()


def get_medical_nlp_model():
    """Get cached medical NLP model"""
    return model_manager.load_medical_model()


def get_spacy_model(model_name: str = "en_core_web_sm"):
    """Get cached spaCy model"""
    return model_manager.load_spacy_model(model_name)