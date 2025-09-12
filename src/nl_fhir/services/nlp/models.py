"""
NLP Model Management for Transformers and Medical Models
HIPAA Compliant: Secure model loading and caching
Production Ready: Memory optimization and error handling
"""

import logging
import threading
import re
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import time

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("Transformers not available - using basic NLP")
    TRANSFORMERS_AVAILABLE = False


class NLPModelManager:
    """Manages Transformers and medical NLP models with caching and optimization"""
    
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialization_status = {}
        
    def load_medical_ner_model(self, model_name: str = "clinical-ai-apollo/Medical-NER") -> Optional[Any]:
        """Load and cache medical NER model with error handling"""
        
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available, using fallback NLP")
            return None
            
        with self._lock:
            if model_name in self._models:
                return self._models[model_name]
                
            try:
                logger.info(f"Loading medical NER model: {model_name}")
                start_time = time.time()
                
                # Load NER pipeline for medical entities
                ner_pipeline = pipeline(
                    "ner", 
                    model=model_name,
                    aggregation_strategy="simple",
                    device=-1  # CPU inference
                )
                
                # Basic validation
                test_result = ner_pipeline("Test medical order: 50mg Prozac daily")
                if not isinstance(test_result, list):
                    raise ValueError(f"Model {model_name} failed basic validation")
                
                load_time = time.time() - start_time
                logger.info(f"Successfully loaded {model_name} in {load_time:.2f}s")
                
                self._models[model_name] = ner_pipeline
                self._initialization_status[model_name] = "loaded"
                
                return ner_pipeline
                
            except Exception as e:
                logger.error(f"Failed to load medical NER model {model_name}: {e}")
                self._initialization_status[model_name] = "failed"
                
                # Fallback to basic regex-based NLP
                logger.info("Using fallback regex-based NLP")
                return self.load_fallback_nlp()
                
    def load_fallback_nlp(self) -> Dict[str, Any]:
        """Fallback regex-based NLP when transformers fail"""
        
        fallback_nlp = {
            "type": "regex_fallback",
            "medication_pattern": re.compile(r'(\d+\s*(?:mg|gram|tablet|capsule|ml|mcg|iu))\s+(\w+)', re.IGNORECASE),
            "frequency_pattern": re.compile(r'(daily|twice\s+daily|three\s+times|four\s+times|once|bid|tid|qid|qhs|prn)', re.IGNORECASE),
            "patient_pattern": re.compile(r'patient\s+(\w+\s+\w+)', re.IGNORECASE),
            "dosage_pattern": re.compile(r'(\d+\.?\d*)\s*(mg|gram|tablet|capsule|ml|mcg|iu)', re.IGNORECASE)
        }
        
        self._models["fallback_nlp"] = fallback_nlp
        self._initialization_status["fallback_nlp"] = "loaded"
        
        return fallback_nlp
        
    def load_sentence_transformer(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Optional[Any]:
        """Load sentence transformer for embeddings"""
        
        if not TRANSFORMERS_AVAILABLE:
            return None
            
        with self._lock:
            if f"embeddings_{model_name}" in self._models:
                return self._models[f"embeddings_{model_name}"]
                
            try:
                logger.info(f"Loading sentence transformer: {model_name}")
                start_time = time.time()
                
                embedder = SentenceTransformer(model_name)
                
                # Test embeddings
                test_embedding = embedder.encode("Test medical text")
                if test_embedding is None or len(test_embedding) == 0:
                    raise ValueError(f"Embeddings model {model_name} failed validation")
                
                load_time = time.time() - start_time
                logger.info(f"Successfully loaded embeddings model in {load_time:.2f}s")
                
                self._models[f"embeddings_{model_name}"] = embedder
                self._initialization_status[f"embeddings_{model_name}"] = "loaded"
                
                return embedder
                
            except Exception as e:
                logger.error(f"Failed to load sentence transformer {model_name}: {e}")
                self._initialization_status[f"embeddings_{model_name}"] = "failed"
                return None
    
    def extract_medical_entities(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract medical entities using available NLP model"""
        
        # Try medical NER model first
        ner_model = self.load_medical_ner_model()
        
        if ner_model and isinstance(ner_model, dict) and ner_model.get("type") == "regex_fallback":
            return self._extract_with_regex(text, ner_model)
        elif ner_model:
            return self._extract_with_transformers(text, ner_model)
        else:
            # Ultimate fallback
            return self._extract_with_regex(text, self.load_fallback_nlp())
    
    def _extract_with_transformers(self, text: str, ner_pipeline) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities using transformers NER pipeline"""
        try:
            entities = ner_pipeline(text)
            
            result = {
                "medications": [],
                "dosages": [], 
                "frequencies": [],
                "patients": [],
                "conditions": []
            }
            
            for entity in entities:
                entity_type = entity.get("entity_group", "").lower()
                entity_text = entity.get("word", "")
                confidence = entity.get("score", 0.0)
                
                entity_info = {
                    "text": entity_text,
                    "confidence": confidence,
                    "start": entity.get("start", 0),
                    "end": entity.get("end", 0)
                }
                
                # Map entity types
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
                    
            return result
            
        except Exception as e:
            logger.error(f"Transformers extraction failed: {e}")
            return self._extract_with_regex(text, self.load_fallback_nlp())
    
    def _extract_with_regex(self, text: str, regex_nlp: Dict) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities using regex patterns"""
        
        result = {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "patients": [],
            "conditions": []
        }
        
        try:
            # Extract medications with dosages
            med_matches = regex_nlp["medication_pattern"].finditer(text)
            for match in med_matches:
                result["medications"].append({
                    "text": match.group(2),
                    "confidence": 0.8,
                    "start": match.start(2),
                    "end": match.end(2)
                })
                result["dosages"].append({
                    "text": match.group(1),
                    "confidence": 0.8,
                    "start": match.start(1),
                    "end": match.end(1)
                })
            
            # Extract frequencies
            freq_matches = regex_nlp["frequency_pattern"].finditer(text)
            for match in freq_matches:
                result["frequencies"].append({
                    "text": match.group(1),
                    "confidence": 0.8,
                    "start": match.start(1),
                    "end": match.end(1)
                })
            
            # Extract patient names
            patient_matches = regex_nlp["patient_pattern"].finditer(text)
            for match in patient_matches:
                result["patients"].append({
                    "text": match.group(1),
                    "confidence": 0.7,
                    "start": match.start(1),
                    "end": match.end(1)
                })
                
        except Exception as e:
            logger.error(f"Regex extraction failed: {e}")
            
        return result
    
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
    return model_manager.load_medical_ner_model()


def extract_medical_entities(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """Extract medical entities from text"""
    return model_manager.extract_medical_entities(text)


def get_sentence_transformer(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """Get cached sentence transformer model"""
    return model_manager.load_sentence_transformer(model_name)