#!/usr/bin/env python3
"""
Test script to see what NLP entities are being extracted
"""

import requests
import json

def test_nlp_extraction():
    """Test what entities NLP is extracting"""
    
    # Test request with multiple types of orders
    test_request = {
        "clinical_text": "Order CBC with differential. Start aspirin 81mg daily. Schedule chest x-ray."
    }
    
    print(f"Testing NLP extraction...")
    print(f"Request: {test_request}")
    print("-" * 50)
    
    # First, let's check what the NLP extracts directly
    from src.nl_fhir.services.nlp.entity_extractor import MedicalEntityExtractor
    
    extractor = MedicalEntityExtractor()
    extractor.initialize()
    
    entities = extractor.extract_entities(test_request["clinical_text"], "test-123")
    
    print("\nExtracted entities:")
    for entity in entities:
        print(f"  - Type: {entity.entity_type.value}, Text: '{entity.text}', Confidence: {entity.confidence}, Source: {entity.source}")
    
    return entities

if __name__ == "__main__":
    entities = test_nlp_extraction()