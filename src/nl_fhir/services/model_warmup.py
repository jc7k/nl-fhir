"""
Model Warmup Service for Performance Optimization - Story 2
Pre-loads NLP models at application startup to eliminate first-request latency.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ModelWarmupService:
    """Pre-loads and warms up NLP models at application startup for optimal performance"""

    def __init__(self):
        self.warmup_status: Dict[str, str] = {}
        self.warmup_start_time: Optional[float] = None
        self.warmup_complete_time: Optional[float] = None
        self.models_loaded = False

    async def warmup_models(self) -> Dict[str, Any]:
        """
        Warm up all NLP models during application startup
        Returns warmup status and timing information
        """
        logger.info("Starting model warmup for performance optimization...")
        self.warmup_start_time = time.time()

        warmup_results = {
            "medspacy_clinical": await self._warmup_medspacy(),
            "transformer_ner": await self._warmup_transformer_ner(),
            "embeddings": await self._warmup_embeddings(),
        }

        self.warmup_complete_time = time.time()
        total_warmup_time = self.warmup_complete_time - self.warmup_start_time

        self.models_loaded = all(
            result["status"] == "success" for result in warmup_results.values()
        )

        logger.info(
            f"Model warmup completed in {total_warmup_time:.2f}s - "
            f"Models loaded: {self.models_loaded}"
        )

        return {
            "warmup_complete": True,
            "total_time_seconds": total_warmup_time,
            "models_loaded": self.models_loaded,
            "results": warmup_results,
        }

    async def _warmup_medspacy(self) -> Dict[str, Any]:
        """Warm up MedSpaCy Clinical Intelligence Engine"""
        try:
            from ..services.nlp.model_managers.medspacy_manager import MedSpacyManager

            start_time = time.time()
            manager = MedSpacyManager()
            model = manager.load_medspacy_clinical_engine()

            load_time = time.time() - start_time

            if model is not None:
                # Warm up the model with a test clinical order
                test_text = "Start patient on lisinopril 10mg daily for hypertension"
                test_doc = model(test_text)

                self.warmup_status["medspacy"] = "loaded"
                logger.info(f"MedSpaCy Clinical Engine warmed up in {load_time:.2f}s")

                return {
                    "status": "success",
                    "load_time_seconds": load_time,
                    "entities_detected": len(test_doc.ents) if hasattr(test_doc, 'ents') else 0,
                    "model_available": True
                }
            else:
                self.warmup_status["medspacy"] = "failed"
                return {
                    "status": "failed",
                    "load_time_seconds": load_time,
                    "error": "Model loading returned None"
                }

        except Exception as e:
            logger.error(f"MedSpaCy warmup failed: {e}")
            self.warmup_status["medspacy"] = "error"
            return {"status": "error", "error": str(e)}

    async def _warmup_transformer_ner(self) -> Dict[str, Any]:
        """Warm up Transformer NER model"""
        try:
            from ..services.nlp.model_managers.transformer_manager import TransformerManager

            start_time = time.time()
            manager = TransformerManager()
            model = manager.load_medical_ner_model()

            load_time = time.time() - start_time

            if model is not None:
                # Warm up the model with a test clinical order
                test_result = model("Patient needs 500mg amoxicillin twice daily")

                self.warmup_status["transformer_ner"] = "loaded"
                logger.info(f"Transformer NER model warmed up in {load_time:.2f}s")

                return {
                    "status": "success",
                    "load_time_seconds": load_time,
                    "test_entities": len(test_result) if isinstance(test_result, list) else 0,
                    "model_available": True
                }
            else:
                self.warmup_status["transformer_ner"] = "failed"
                return {
                    "status": "failed",
                    "load_time_seconds": load_time,
                    "error": "Model loading returned None"
                }

        except Exception as e:
            logger.error(f"Transformer NER warmup failed: {e}")
            self.warmup_status["transformer_ner"] = "error"
            return {"status": "error", "error": str(e)}

    async def _warmup_embeddings(self) -> Dict[str, Any]:
        """Warm up sentence embeddings model"""
        try:
            from ..services.nlp.model_managers.transformer_manager import TransformerManager

            start_time = time.time()
            manager = TransformerManager()
            model = manager.load_sentence_transformer()

            load_time = time.time() - start_time

            if model is not None:
                # Warm up embeddings with test text
                test_embedding = model.encode("Test clinical order text")

                self.warmup_status["embeddings"] = "loaded"
                logger.info(f"Sentence embeddings model warmed up in {load_time:.2f}s")

                return {
                    "status": "success",
                    "load_time_seconds": load_time,
                    "embedding_dimension": len(test_embedding) if test_embedding is not None else 0,
                    "model_available": True
                }
            else:
                self.warmup_status["embeddings"] = "failed"
                return {
                    "status": "failed",
                    "load_time_seconds": load_time,
                    "error": "Model loading returned None"
                }

        except Exception as e:
            logger.error(f"Embeddings warmup failed: {e}")
            self.warmup_status["embeddings"] = "error"
            return {"status": "error", "error": str(e)}

    def get_warmup_status(self) -> Dict[str, Any]:
        """Get current model warmup status"""
        if self.warmup_start_time is None:
            return {"status": "not_started", "models_loaded": False}

        if self.warmup_complete_time is None:
            return {
                "status": "in_progress",
                "elapsed_seconds": time.time() - self.warmup_start_time,
                "models_loaded": False
            }

        return {
            "status": "complete",
            "total_warmup_time": self.warmup_complete_time - self.warmup_start_time,
            "models_loaded": self.models_loaded,
            "model_status": self.warmup_status,
        }

    def is_ready(self) -> bool:
        """Check if model warmup is complete and models are ready"""
        return self.models_loaded


# Global instance for application-wide use
model_warmup_service = ModelWarmupService()