#!/usr/bin/env python3
"""
Test what NLP extracts from the Ethan Rivera oxygen case
"""

import asyncio
from src.nl_fhir.services.conversion import ConversionService
from src.nl_fhir.services.nlp.entity_extractor import MedicalEntityExtractor

async def test_ethan_rivera_nlp():
    """Test what _basic_text_analysis extracts from Ethan Rivera case"""
    
    clinical_text = "Prescribed patient Ethan Rivera 2L oxygen via nasal cannula continuously for hypoxemia; home oxygen setup arranged."
    
    print(f"Testing Ethan Rivera NLP extraction...")
    print(f"Text: {clinical_text}")
    print("-" * 70)
    
    # Test the basic analysis directly
    service = ConversionService()
    result = await service._basic_text_analysis(clinical_text, "ethan-rivera-123")
    
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
    
    direct_entities = extractor.extract_entities(clinical_text, "ethan-rivera-123")
    
    print(f"Direct extracted entities:")
    for entity in direct_entities:
        print(f"  - Type: {entity.entity_type.value}, Text: '{entity.text}', Confidence: {entity.confidence}, Source: {entity.source}")
    
    # Test specific oxygen-related terms
    print(f"\nTesting specific oxygen-related extractions:")
    oxygen_text = "oxygen"
    oxygen_entities = extractor.extract_entities(oxygen_text, "oxygen-test")
    print(f"'oxygen' alone: {len(oxygen_entities)} entities")
    for entity in oxygen_entities:
        print(f"  - Type: {entity.entity_type.value}, Text: '{entity.text}'")
    
    nasal_cannula_text = "nasal cannula"
    cannula_entities = extractor.extract_entities(nasal_cannula_text, "cannula-test")
    print(f"'nasal cannula' alone: {len(cannula_entities)} entities")
    for entity in cannula_entities:
        print(f"  - Type: {entity.entity_type.value}, Text: '{entity.text}'")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_ethan_rivera_nlp())