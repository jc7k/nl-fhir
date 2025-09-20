#!/usr/bin/env python3
"""
Test Model Warmup Service - Story 2 Performance Optimization
Tests NLP model pre-loading for optimal first-request performance
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from src.nl_fhir.services.model_warmup import ModelWarmupService, model_warmup_service


@pytest.fixture
def warmup_service():
    """Create fresh warmup service for each test"""
    return ModelWarmupService()


class TestModelWarmupService:
    """Test model warmup functionality"""

    def test_initial_status(self, warmup_service):
        """Test initial warmup status"""
        status = warmup_service.get_warmup_status()
        assert status["status"] == "not_started"
        assert status["models_loaded"] is False
        assert not warmup_service.is_ready()

    @pytest.mark.asyncio
    async def test_warmup_medspacy_success(self, warmup_service):
        """Test successful MedSpaCy warmup"""
        # Mock the MedSpaCy manager and model
        mock_model = MagicMock()
        mock_doc = MagicMock()
        mock_doc.ents = ["entity1", "entity2"]  # Mock entities
        mock_model.return_value = mock_doc

        with patch('src.nl_fhir.services.nlp.model_managers.medspacy_manager.MedSpacyManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.load_medspacy_clinical_engine.return_value = mock_model
            mock_manager_class.return_value = mock_manager

            result = await warmup_service._warmup_medspacy()

            assert result["status"] == "success"
            assert result["model_available"] is True
            assert result["entities_detected"] == 2
            assert "load_time_seconds" in result
            mock_manager.load_medspacy_clinical_engine.assert_called_once()

    @pytest.mark.asyncio
    async def test_warmup_transformer_success(self, warmup_service):
        """Test successful Transformer NER warmup"""
        # Mock the transformer manager and model
        mock_model = MagicMock()
        mock_result = [{"entity": "MEDICATION", "score": 0.9}]
        mock_model.return_value = mock_result

        with patch('src.nl_fhir.services.nlp.model_managers.transformer_manager.TransformerManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.load_medical_ner_model.return_value = mock_model
            mock_manager_class.return_value = mock_manager

            result = await warmup_service._warmup_transformer_ner()

            assert result["status"] == "success"
            assert result["model_available"] is True
            assert result["test_entities"] == 1
            assert "load_time_seconds" in result
            mock_manager.load_medical_ner_model.assert_called_once()

    @pytest.mark.asyncio
    async def test_warmup_embeddings_success(self, warmup_service):
        """Test successful embeddings warmup"""
        # Mock the sentence transformer
        mock_model = MagicMock()
        mock_embedding = [0.1, 0.2, 0.3, 0.4]  # Mock embedding vector
        mock_model.encode.return_value = mock_embedding

        with patch('src.nl_fhir.services.nlp.model_managers.transformer_manager.TransformerManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.load_sentence_transformer.return_value = mock_model
            mock_manager_class.return_value = mock_manager

            result = await warmup_service._warmup_embeddings()

            assert result["status"] == "success"
            assert result["model_available"] is True
            assert result["embedding_dimension"] == 4
            assert "load_time_seconds" in result
            mock_manager.load_sentence_transformer.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_warmup_success(self, warmup_service):
        """Test full model warmup process with all models successful"""
        # Mock all model managers to return successful models
        mock_nlp = MagicMock()
        mock_nlp.ents = []

        mock_ner = MagicMock()
        mock_ner.return_value = []

        mock_embedder = MagicMock()
        mock_embedder.encode.return_value = [0.1, 0.2]

        with patch('src.nl_fhir.services.model_warmup.MedSpacyManager') as mock_medspacy, \
             patch('src.nl_fhir.services.nlp.model_managers.transformer_manager.TransformerManager') as mock_transformer:

            # Setup MedSpaCy mock
            mock_medspacy_instance = MagicMock()
            mock_medspacy_instance.load_medspacy_clinical_engine.return_value = mock_nlp
            mock_medspacy.return_value = mock_medspacy_instance

            # Setup Transformer mock
            mock_transformer_instance = MagicMock()
            mock_transformer_instance.load_medical_ner_model.return_value = mock_ner
            mock_transformer_instance.load_sentence_transformer.return_value = mock_embedder
            mock_transformer.return_value = mock_transformer_instance

            result = await warmup_service.warmup_models()

            assert result["warmup_complete"] is True
            assert result["models_loaded"] is True
            assert "total_time_seconds" in result
            assert "results" in result

            # Check individual model results
            assert result["results"]["medspacy_clinical"]["status"] == "success"
            assert result["results"]["transformer_ner"]["status"] == "success"
            assert result["results"]["embeddings"]["status"] == "success"

            # Check status after warmup
            status = warmup_service.get_warmup_status()
            assert status["status"] == "complete"
            assert status["models_loaded"] is True
            assert warmup_service.is_ready() is True

    @pytest.mark.asyncio
    async def test_warmup_with_model_failure(self, warmup_service):
        """Test warmup behavior when some models fail to load"""
        # Mock models where one fails
        mock_nlp = MagicMock()
        mock_nlp.ents = []

        with patch('src.nl_fhir.services.model_warmup.MedSpacyManager') as mock_medspacy, \
             patch('src.nl_fhir.services.nlp.model_managers.transformer_manager.TransformerManager') as mock_transformer:

            # MedSpaCy succeeds
            mock_medspacy_instance = MagicMock()
            mock_medspacy_instance.load_medspacy_clinical_engine.return_value = mock_nlp
            mock_medspacy.return_value = mock_medspacy_instance

            # Transformer fails
            mock_transformer_instance = MagicMock()
            mock_transformer_instance.load_medical_ner_model.return_value = None
            mock_transformer_instance.load_sentence_transformer.return_value = None
            mock_transformer.return_value = mock_transformer_instance

            result = await warmup_service.warmup_models()

            assert result["warmup_complete"] is True
            assert result["models_loaded"] is False  # Some models failed
            assert result["results"]["medspacy_clinical"]["status"] == "success"
            assert result["results"]["transformer_ner"]["status"] == "failed"
            assert result["results"]["embeddings"]["status"] == "failed"

            # Service should not be ready if models failed
            assert warmup_service.is_ready() is False

    @pytest.mark.asyncio
    async def test_warmup_exception_handling(self, warmup_service):
        """Test exception handling during warmup"""
        with patch('src.nl_fhir.services.nlp.model_managers.medspacy_manager.MedSpacyManager') as mock_medspacy:
            # Simulate import error
            mock_medspacy.side_effect = ImportError("MedSpaCy not available")

            result = await warmup_service._warmup_medspacy()

            assert result["status"] == "error"
            assert "MedSpaCy not available" in result["error"]

    def test_global_warmup_service(self):
        """Test that global warmup service instance exists"""
        from src.nl_fhir.services.model_warmup import model_warmup_service
        assert model_warmup_service is not None
        assert isinstance(model_warmup_service, ModelWarmupService)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])