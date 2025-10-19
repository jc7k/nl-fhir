"""
Integration Tests for Epic 2 NLP Pipeline
HIPAA Compliant: No PHI in test data
End-to-End: Test complete NLP processing workflow
"""

import pytest
import asyncio
from src.nl_fhir.services.nlp.pipeline import NLPPipeline, get_nlp_pipeline


class TestNLPIntegration:
    """Test end-to-end NLP pipeline integration"""
    
    @pytest.fixture
    async def pipeline(self):
        """Create and initialize NLP pipeline"""
        pipeline = await get_nlp_pipeline()
        return pipeline
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self):
        """Test NLP pipeline initializes all components"""
        pipeline = NLPPipeline()
        assert pipeline.initialize() == True
        assert pipeline.initialized == True
        
    @pytest.mark.asyncio
    async def test_complete_nlp_processing(self, pipeline):
        """Test complete NLP processing workflow"""
        clinical_text = "Start patient on metformin 500mg twice daily for diabetes. Order CBC and HbA1c."
        
        result = await pipeline.process_clinical_text(clinical_text, "integration_test_1")
        
        # Check response structure
        assert "status" in result
        assert result["status"] == "completed"
        assert "extracted_entities" in result
        assert "structured_output" in result
        assert "terminology_mappings" in result
        
    @pytest.mark.asyncio
    async def test_entity_extraction_stage(self, pipeline):
        """Test entity extraction stage"""
        clinical_text = "Prescribe amoxicillin 500mg three times daily"
        
        result = await pipeline.process_clinical_text(clinical_text, "integration_test_2")
        
        entities = result["extracted_entities"]["entities"]
        assert len(entities) > 0
        
        # Should extract medication and dosage
        entity_types = [e["type"] for e in entities]
        assert "medication" in entity_types
        assert "dosage" in entity_types
        
    @pytest.mark.asyncio
    async def test_rag_enhancement_stage(self, pipeline):
        """Test RAG enhancement stage"""
        clinical_text = "Order complete blood count and glucose test"
        
        result = await pipeline.process_clinical_text(clinical_text, "integration_test_3")
        
        enhanced_entities = result["extracted_entities"]["enhanced_entities"]
        assert len(enhanced_entities) > 0
        
        # Check for medical code mappings
        for entity in enhanced_entities:
            if entity.get("medical_codes"):
                assert isinstance(entity["medical_codes"], list)
                
    @pytest.mark.asyncio
    async def test_structured_output_stage(self, pipeline):
        """Test structured output generation"""
        clinical_text = "Start metformin 500mg BID, order labs, schedule follow-up"
        
        result = await pipeline.process_clinical_text(clinical_text, "integration_test_4")
        
        structured = result["structured_output"]["structured_output"]
        
        # Check structured output format
        assert "medications" in structured
        assert "lab_tests" in structured
        assert "clinical_instructions" in structured
        
    @pytest.mark.asyncio
    async def test_terminology_mappings(self, pipeline):
        """Test medical terminology mappings"""
        clinical_text = "Patient needs CBC, metformin, and diabetes monitoring"
        
        result = await pipeline.process_clinical_text(clinical_text, "integration_test_5")
        
        mappings = result["terminology_mappings"]
        
        # Check mapping structure
        assert "medications" in mappings
        assert "lab_tests" in mappings
        assert "conditions" in mappings
        
    @pytest.mark.asyncio
    async def test_performance_within_limits(self, pipeline):
        """Test NLP processing performance"""
        clinical_text = """
        Patient presents with type 2 diabetes mellitus requiring medication management.
        Start metformin 500mg twice daily with meals.
        Order comprehensive metabolic panel, HbA1c, and lipid panel.
        Schedule follow-up appointment in 3 months for reassessment.
        Patient should monitor blood glucose levels daily.
        """
        
        import time
        start_time = time.time()
        
        result = await pipeline.process_clinical_text(clinical_text, "performance_test_1")
        
        processing_time = time.time() - start_time
        
        # Should complete within 2 seconds (Epic requirement)
        assert processing_time < 2.0
        assert result["status"] == "completed"
        
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, pipeline):
        """Test concurrent NLP processing"""
        clinical_texts = [
            "Order CBC and basic metabolic panel",
            "Start lisinopril 10mg daily for hypertension", 
            "Schedule chest X-ray for cough evaluation"
        ]
        
        # Process concurrently
        tasks = [
            pipeline.process_clinical_text(text, f"concurrent_test_{i}")
            for i, text in enumerate(clinical_texts)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All should complete successfully
        assert len(results) == 3
        for result in results:
            assert result["status"] == "completed"
            
    @pytest.mark.asyncio
    async def test_error_handling(self, pipeline):
        """Test NLP pipeline error handling"""
        # Test with empty text
        result = await pipeline.process_clinical_text("", "error_test_1")
        
        # Should handle gracefully
        assert "status" in result
        # May be completed with empty results or error status
        
    @pytest.mark.asyncio
    async def test_pipeline_metrics(self, pipeline):
        """Test pipeline performance metrics"""
        clinical_text = "Prescribe medication and order tests"
        
        result = await pipeline.process_clinical_text(clinical_text, "metrics_test_1")
        
        # Check metrics
        assert "pipeline_metrics" in result
        metrics = result["pipeline_metrics"]
        
        assert "total_entities" in metrics
        assert "processing_stages" in metrics
        assert "performance_score" in metrics
        assert 0.0 <= metrics["performance_score"] <= 1.0
        
    @pytest.mark.asyncio
    async def test_pipeline_status(self, pipeline):
        """Test pipeline status reporting"""
        status = pipeline.get_pipeline_status()
        
        assert "initialized" in status
        assert "components" in status
        assert status["initialized"] == True
        
        components = status["components"]
        assert "entity_extractor" in components
        assert "rag_service" in components
        assert "llm_processor" in components
        
    @pytest.mark.asyncio
    async def test_complex_medication_order(self, pipeline):
        """Test complex medication order processing"""
        clinical_text = """
        Start comprehensive diabetes management:
        - Metformin 500mg twice daily with meals
        - Monitor blood glucose 4x daily
        - HbA1c every 3 months
        - Annual eye exam
        - Dietary consultation
        """
        
        result = await pipeline.process_clinical_text(clinical_text, "complex_test_1")
        
        # Should extract multiple components
        entities = result["extracted_entities"]["entities"]
        structured = result["structured_output"]["structured_output"]
        
        assert len(entities) > 3  # Multiple entities
        assert len(structured["medications"]) > 0
        assert len(structured["clinical_instructions"]) > 0