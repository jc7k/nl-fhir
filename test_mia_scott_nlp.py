#!/usr/bin/env python3
"""
Test what NLP extracts from the Mia Scott case
"""

import asyncio
from src.nl_fhir.services.conversion import ConversionService
from src.nl_fhir.services.nlp.entity_extractor import MedicalEntityExtractor

async def test_mia_scott_nlp():
    """Test what _basic_text_analysis extracts from Mia Scott case"""
    
    clinical_text = "Started patient Mia Scott on 500mg Ciprofloxacin twice daily for traveler's diarrhea; advised on hydration and rest."
    
    print(f"Testing Mia Scott NLP extraction...")
    print(f"Text: {clinical_text}")
    print("-" * 70)
    
    # Test the basic analysis directly
    service = ConversionService()
    result = await service._basic_text_analysis(clinical_text, "mia-scott-123")
    
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
    
    direct_entities = extractor.extract_entities(clinical_text, "mia-scott-123")
    
    print(f"Direct extracted entities:")
    for entity in direct_entities:
        print(f"  - Type: {entity.entity_type.value}, Text: '{entity.text}', Confidence: {entity.confidence}, Source: {entity.source}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_mia_scott_nlp())