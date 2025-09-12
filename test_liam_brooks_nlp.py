#!/usr/bin/env python3
"""
Test what NLP extracts from the Liam Brooks Hydroxyurea case
"""

import asyncio
from src.nl_fhir.services.conversion import ConversionService
from src.nl_fhir.services.nlp.entity_extractor import MedicalEntityExtractor

async def test_liam_brooks_nlp():
    """Test what _basic_text_analysis extracts from Liam Brooks case"""
    
    clinical_text = "Prescribed patient Liam Brooks 100mg Hydroxyurea daily for sickle cell disease; CBC tracked."
    
    print(f"Testing Liam Brooks NLP extraction...")
    print(f"Text: {clinical_text}")
    print("-" * 70)
    
    # Test the basic analysis directly
    service = ConversionService()
    result = await service._basic_text_analysis(clinical_text, "liam-brooks-123")
    
    print(f"\nBasic analysis result:")
    entities = result['extracted_entities']
    
    print(f"Lab tests: {entities.get('lab_tests', [])}")
    print(f"Procedures: {entities.get('procedures', [])}")
    print(f"Medications: {entities.get('medications', [])}")
    print(f"Conditions: {entities.get('conditions', [])}")
    
    # Also test direct entity extraction
    print(f"\nDirect entity extraction:")
    extractor = MedicalEntityExtractor()
    extractor.initialize()
    
    direct_entities = extractor.extract_entities(clinical_text, "liam-brooks-123")
    
    print(f"Direct extracted entities:")
    for entity in direct_entities:
        print(f"  - Type: {entity.entity_type.value}, Text: '{entity.text}', Confidence: {entity.confidence}, Source: {entity.source}")
    
    # Test specific terms
    print(f"\nTesting specific term extractions:")
    
    # Test Hydroxyurea
    hydroxyurea_entities = extractor.extract_entities("Hydroxyurea", "hydroxyurea-test")
    print(f"'Hydroxyurea' alone: {len(hydroxyurea_entities)} entities")
    for entity in hydroxyurea_entities:
        print(f"  - Type: {entity.entity_type.value}, Text: '{entity.text}'")
    
    # Test CBC
    cbc_entities = extractor.extract_entities("CBC tracked", "cbc-test")
    print(f"'CBC tracked' alone: {len(cbc_entities)} entities")
    for entity in cbc_entities:
        print(f"  - Type: {entity.entity_type.value}, Text: '{entity.text}'")
    
    # Test dosage pattern
    dosage_entities = extractor.extract_entities("100mg daily", "dosage-test")
    print(f"'100mg daily': {len(dosage_entities)} entities")
    for entity in dosage_entities:
        print(f"  - Type: {entity.entity_type.value}, Text: '{entity.text}'")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_liam_brooks_nlp())