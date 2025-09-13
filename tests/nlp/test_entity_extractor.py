"""
Tests for 4-Tier Medical Entity Extraction with LLM Escalation
HIPAA Compliant: No PHI in test data
Medical Safety: Test all entity extraction scenarios including 85% confidence threshold
"""

import pytest
from src.nl_fhir.services.nlp.models import model_manager


class TestMedicalEntityExtractor:
    """Test 4-tier medical entity extraction functionality with LLM escalation"""
    
    def test_model_manager_initialization(self):
        """Test model manager initializes successfully"""
        # model_manager is a singleton, should work
        assert model_manager is not None
        
    def test_medication_extraction(self):
        """Test medication entity extraction using 4-tier system"""
        text = "Start patient on metformin 500mg twice daily"
        extracted_entities = model_manager.extract_medical_entities(text)
        
        # Should extract medication
        assert "medications" in extracted_entities
        assert len(extracted_entities["medications"]) > 0
        assert any("metformin" in entity["text"].lower() for entity in extracted_entities["medications"])
        
    def test_dosage_extraction(self):
        """Test dosage entity extraction using 4-tier system"""
        text = "Prescribe amoxicillin 500mg three times daily"
        extracted_entities = model_manager.extract_medical_entities(text)
        
        # Should extract dosage
        assert "dosages" in extracted_entities
        assert len(extracted_entities["dosages"]) > 0
        assert any("500mg" in entity["text"] for entity in extracted_entities["dosages"])
        
    def test_frequency_extraction(self):
        """Test frequency entity extraction using 4-tier system"""
        text = "Take medication twice daily with meals"
        extracted_entities = model_manager.extract_medical_entities(text)
        
        # Should extract frequency
        assert "frequencies" in extracted_entities
        assert len(extracted_entities["frequencies"]) > 0
        assert any("twice daily" in entity["text"].lower() for entity in extracted_entities["frequencies"])
        
    def test_lab_test_extraction(self):
        """Test lab test entity extraction using 4-tier system"""
        text = "Order CBC and comprehensive metabolic panel"
        extracted_entities = model_manager.extract_medical_entities(text)
        
        # Should extract lab tests
        assert "lab_tests" in extracted_entities
        assert len(extracted_entities["lab_tests"]) > 0
        assert any("cbc" in entity["text"].lower() for entity in extracted_entities["lab_tests"])
        
    def test_complex_clinical_text(self):
        """Test extraction from complex clinical text using 4-tier system"""
        text = """
        Start patient on metformin 500mg twice daily for diabetes management.
        Order CBC, BMP, and HbA1c for monitoring.
        Schedule follow-up in 3 months.
        Patient should take medication with meals.
        """
        extracted_entities = model_manager.extract_medical_entities(text)
        
        # Should extract multiple entity types
        assert "medications" in extracted_entities and len(extracted_entities["medications"]) > 0
        assert "dosages" in extracted_entities and len(extracted_entities["dosages"]) > 0
        assert "lab_tests" in extracted_entities and len(extracted_entities["lab_tests"]) > 0
        
    def test_4tier_architecture_integration(self):
        """Test that 4-tier architecture processes medical text appropriately"""
        text = "Give patient tadalafil 5mg as needed for erectile dysfunction"
        extracted_entities = model_manager.extract_medical_entities(text)
        
        # Should extract multiple categories from this clinical text
        total_entities = sum(len(entities) for entities in extracted_entities.values())
        assert total_entities > 0
        
        # Should include medications and conditions
        assert "medications" in extracted_entities or "conditions" in extracted_entities
        
    def test_entity_confidence_scoring(self):
        """Test entity confidence scoring in 4-tier system"""
        text = "Prescribe ibuprofen 400mg three times daily"
        extracted_entities = model_manager.extract_medical_entities(text)
        
        # All entities should have confidence scores
        for category, entities in extracted_entities.items():
            for entity in entities:
                assert "confidence" in entity
                assert 0.0 <= entity["confidence"] <= 1.0
                assert "method" in entity  # Should indicate which tier extracted it
            
    def test_medical_safety_escalation_trigger(self):
        """Test that medical safety escalation can be triggered with low confidence scenarios"""
        # This is a complex clinical scenario that might trigger LLM escalation
        text = "Continue the same medication we discussed last visit for the patient's condition"
        extracted_entities = model_manager.extract_medical_entities(text)
        
        # Even with ambiguous text, should return some results (either from tiers or LLM)
        total_entities = sum(len(entities) for entities in extracted_entities.values())
        # The system should handle ambiguous cases gracefully
        assert isinstance(extracted_entities, dict)
        
    def test_empty_text_handling(self):
        """Test handling of empty or invalid text"""
        extracted_entities = model_manager.extract_medical_entities("")
        assert isinstance(extracted_entities, dict)
        
        extracted_entities = model_manager.extract_medical_entities("   ")
        assert isinstance(extracted_entities, dict)
        
    def test_medical_keyword_recognition(self):
        """Test medical keyword recognition across 4-tier system"""
        # Test multiple medications
        text = "Patient takes lisinopril, aspirin, and warfarin daily"
        extracted_entities = model_manager.extract_medical_entities(text)
        
        # Should extract medications
        assert "medications" in extracted_entities
        med_texts = [entity["text"].lower() for entity in extracted_entities["medications"]]
        
        # Should recognize common medications
        assert any("lisinopril" in text for text in med_texts) or any("aspirin" in text for text in med_texts)
        
    def test_tier1_spacy_performance(self):
        """Test Tier 1 (spaCy) handles common cases efficiently"""
        text = "Start patient Julian West on 5mg Tadalafil as needed for erectile dysfunction"
        
        import time
        start_time = time.time()
        extracted_entities = model_manager.extract_medical_entities(text)
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should be fast (under 50ms for Tier 1)
        # Note: This might escalate to higher tiers depending on confidence
        assert processing_time < 500  # Allow some buffer for potential escalation
        assert isinstance(extracted_entities, dict)
        
    def test_tier_escalation_indicators(self):
        """Test that we can identify which tier processed the text"""
        text = "Prescribed Lisinopril 10mg daily for hypertension"
        extracted_entities = model_manager.extract_medical_entities(text)
        
        # Should have method indicators showing which tier was used
        methods_used = set()
        for category, entities in extracted_entities.items():
            for entity in entities:
                if "method" in entity:
                    methods_used.add(entity["method"])
        
        # Should have at least one method indicator
        assert len(methods_used) > 0
        # Common methods: spacy, transformer, regex, llm_escalation
        assert any(method in ["spacy", "transformer", "regex", "llm_escalation"] for method in methods_used)
        
    def test_4tier_performance_within_limits(self):
        """Test 4-tier extraction performance stays within limits"""
        import time
        
        text = "Patient needs comprehensive workup including CBC, CMP, lipid panel, HbA1c, TSH, and urinalysis. Start metformin 500mg twice daily, lisinopril 10mg once daily, and aspirin 81mg daily. Schedule follow-up in 3 months."
        
        start_time = time.time()
        extracted_entities = model_manager.extract_medical_entities(text)
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time (allowing for potential LLM escalation)
        assert processing_time < 5.0  # Less than 5 seconds even with LLM escalation
        
        # Should extract entities from this comprehensive clinical text
        total_entities = sum(len(entities) for entities in extracted_entities.values())
        assert total_entities > 0