"""
Tests for Medical Entity Extraction Service
HIPAA Compliant: No PHI in test data
Medical Safety: Test all entity extraction scenarios
"""

import pytest
from src.nl_fhir.services.nlp.entity_extractor import MedicalEntityExtractor, EntityType


class TestMedicalEntityExtractor:
    """Test medical entity extraction functionality"""
    
    @pytest.fixture
    def extractor(self):
        """Create entity extractor instance"""
        extractor = MedicalEntityExtractor()
        extractor.initialize()
        return extractor
    
    def test_extractor_initialization(self):
        """Test entity extractor initializes successfully"""
        extractor = MedicalEntityExtractor()
        assert extractor.initialize() == True
        assert extractor.nlp is None  # Rule-based for now
        
    def test_medication_extraction(self, extractor):
        """Test medication entity extraction"""
        text = "Start patient on metformin 500mg twice daily"
        entities = extractor.extract_entities(text, "test_request_1")
        
        # Should extract medication
        medication_entities = [e for e in entities if e.entity_type == EntityType.MEDICATION]
        assert len(medication_entities) > 0
        assert any("metformin" in e.text.lower() for e in medication_entities)
        
    def test_dosage_extraction(self, extractor):
        """Test dosage entity extraction"""
        text = "Prescribe amoxicillin 500mg three times daily"
        entities = extractor.extract_entities(text, "test_request_2")
        
        # Should extract dosage
        dosage_entities = [e for e in entities if e.entity_type == EntityType.DOSAGE]
        assert len(dosage_entities) > 0
        assert any("500mg" in e.text for e in dosage_entities)
        
    def test_frequency_extraction(self, extractor):
        """Test frequency entity extraction"""
        text = "Take medication twice daily with meals"
        entities = extractor.extract_entities(text, "test_request_3")
        
        # Should extract frequency
        frequency_entities = [e for e in entities if e.entity_type == EntityType.FREQUENCY]
        assert len(frequency_entities) > 0
        assert any("twice daily" in e.text.lower() for e in frequency_entities)
        
    def test_lab_test_extraction(self, extractor):
        """Test lab test entity extraction"""
        text = "Order CBC and comprehensive metabolic panel"
        entities = extractor.extract_entities(text, "test_request_4")
        
        # Should extract lab tests
        lab_entities = [e for e in entities if e.entity_type == EntityType.LAB_TEST]
        assert len(lab_entities) > 0
        assert any("cbc" in e.text.lower() for e in lab_entities)
        
    def test_complex_clinical_text(self, extractor):
        """Test extraction from complex clinical text"""
        text = """
        Start patient on metformin 500mg twice daily for diabetes management.
        Order CBC, BMP, and HbA1c for monitoring.
        Schedule follow-up in 3 months.
        Patient should take medication with meals.
        """
        entities = extractor.extract_entities(text, "test_request_5")
        
        # Should extract multiple entity types
        entity_types = set(e.entity_type for e in entities)
        assert EntityType.MEDICATION in entity_types
        assert EntityType.DOSAGE in entity_types
        assert EntityType.LAB_TEST in entity_types
        
    def test_abbreviation_normalization(self, extractor):
        """Test medical abbreviation normalization"""
        text = "Take medication b.i.d. and check labs q.d."
        
        # Test preprocessing
        cleaned_text = extractor._preprocess_text(text)
        assert "twice daily" in cleaned_text
        assert "once daily" in cleaned_text
        
    def test_entity_confidence_scoring(self, extractor):
        """Test entity confidence scoring"""
        text = "Prescribe ibuprofen 400mg three times daily"
        entities = extractor.extract_entities(text, "test_request_6")
        
        # All entities should have confidence scores
        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0
            assert entity.source in ["pattern", "keyword"]
            
    def test_overlapping_entity_merging(self, extractor):
        """Test merging of overlapping entities"""
        # Create test entities with overlap
        from src.nl_fhir.services.nlp.entity_extractor import MedicalEntity
        
        entities = [
            MedicalEntity("metformin", EntityType.MEDICATION, 0, 9, 0.8, {}, "keyword"),
            MedicalEntity("metformin 500", EntityType.MEDICATION, 0, 13, 0.6, {}, "pattern")
        ]
        
        merged = extractor._merge_overlapping_entities(entities)
        
        # Should keep higher confidence entity
        assert len(merged) == 1
        assert merged[0].confidence == 0.8
        
    def test_empty_text_handling(self, extractor):
        """Test handling of empty or invalid text"""
        entities = extractor.extract_entities("", "test_request_7")
        assert entities == []
        
        entities = extractor.extract_entities("   ", "test_request_8")
        assert entities == []
        
    def test_medical_keyword_recognition(self, extractor):
        """Test medical keyword recognition"""
        # Test multiple medications
        text = "Patient takes lisinopril, aspirin, and warfarin daily"
        entities = extractor.extract_entities(text, "test_request_9")
        
        med_entities = [e for e in entities if e.entity_type == EntityType.MEDICATION]
        med_texts = [e.text.lower() for e in med_entities]
        
        assert "lisinopril" in med_texts
        assert "aspirin" in med_texts
        assert "warfarin" in med_texts
        
    def test_route_extraction(self, extractor):
        """Test route of administration extraction"""
        text = "Give medication IV push or oral if tolerated"
        entities = extractor.extract_entities(text, "test_request_10")
        
        route_entities = [e for e in entities if e.entity_type == EntityType.ROUTE]
        assert len(route_entities) > 0
        
    def test_temporal_extraction(self, extractor):
        """Test temporal expression extraction"""
        text = "Start medication tomorrow morning and continue for one week"
        entities = extractor.extract_entities(text, "test_request_11")
        
        temporal_entities = [e for e in entities if e.entity_type == EntityType.TEMPORAL]
        assert len(temporal_entities) > 0
        
    def test_performance_within_limits(self, extractor):
        """Test extraction performance stays within limits"""
        import time
        
        text = "Patient needs comprehensive workup including CBC, CMP, lipid panel, HbA1c, TSH, and urinalysis. Start metformin 500mg twice daily, lisinopril 10mg once daily, and aspirin 81mg daily. Schedule follow-up in 3 months."
        
        start_time = time.time()
        entities = extractor.extract_entities(text, "test_request_12")
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert processing_time < 1.0  # Less than 1 second
        assert len(entities) > 0  # Should extract entities