"""
Transformer Model Management
Handles loading and caching of Hugging Face transformer models for medical NER.
"""

import logging
import threading
import time
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

try:
    from transformers import pipeline
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("Transformers not available - using fallback")
    TRANSFORMERS_AVAILABLE = False


class TransformerManager:
    """Manages Hugging Face transformer models with caching and optimization"""

    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialization_status = {}

    def load_medical_ner_model(self, model_name: str = "clinical-ai-apollo/Medical-NER") -> Optional[Any]:
        """Load and cache medical NER model with error handling"""

        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers not available, returning None")
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
                return None

    def load_sentence_transformer(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> Optional[Any]:
        """Load sentence transformer for embeddings"""

        if not TRANSFORMERS_AVAILABLE:
            return None

        with self._lock:
            embedding_key = f"embeddings_{model_name}"
            if embedding_key in self._models:
                return self._models[embedding_key]

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

                self._models[embedding_key] = embedder
                self._initialization_status[embedding_key] = "loaded"

                return embedder

            except Exception as e:
                logger.error(f"Failed to load sentence transformer {model_name}: {e}")
                self._initialization_status[embedding_key] = "failed"
                return None

    def get_model_status(self) -> Dict[str, str]:
        """Get status of all loaded transformer models"""
        return {k: v for k, v in self._initialization_status.items()
                if k in self._models or v == "failed"}

    def clear_models(self):
        """Clear transformer model cache to free memory"""
        with self._lock:
            transformer_keys = [k for k in self._models.keys()
                               if k.startswith("embeddings_") or k in self._initialization_status]
            for key in transformer_keys:
                self._models.pop(key, None)
                self._initialization_status.pop(key, None)
            logger.info("Cleared transformer model cache")