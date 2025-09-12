#!/usr/bin/env python3
"""
Debug script to see what happens during conversion
"""

import asyncio
import json
from src.nl_fhir.services.conversion import ConversionService
from src.nl_fhir.models.request import ClinicalRequestAdvanced

async def test_conversion_debug():
    """Debug the conversion process"""
    
    # Create request
    request = ClinicalRequestAdvanced(
        clinical_text="Order CBC with differential. Start aspirin 81mg daily. Schedule chest x-ray.",
        priority="routine",
        ordering_provider="web-interface",
        department="general",
        context_metadata={"source": "debug", "ui_version": "1.0"}
    )
    
    print(f"Testing conversion process...")
    print(f"Text: {request.clinical_text}")
    print("-" * 70)
    
    # Use conversion service
    service = ConversionService()
    
    # Step 1: Get basic text analysis
    nlp_results = await service._basic_text_analysis(request.clinical_text, "debug-123")
    entities = nlp_results.get("extracted_entities", {})
    
    print(f"Step 1: Basic text analysis")
    print(f"  Lab tests: {entities.get('lab_tests', [])}")
    print(f"  Procedures: {entities.get('procedures', [])}")
    print(f"  Medications: {entities.get('medications', [])}")
    print()
    
    # Step 2: Check ServiceRequest creation logic
    print(f"Step 2: ServiceRequest creation logic")
    lab_tests = entities.get("lab_tests", [])
    procedures = entities.get("procedures", [])
    
    print(f"  Lab tests list: {lab_tests}")
    print(f"  Procedures list: {procedures}")
    print(f"  Combined list: {lab_tests + procedures}")
    print()
    
    for i, test in enumerate(lab_tests + procedures):
        category = "laboratory" if test in lab_tests else "procedure"
        code = test.get("text", "Unknown test")
        print(f"  Item {i}: {test}")
        print(f"    Code: '{code}'")
        print(f"    Category: {category}")
        print(f"    Is in lab_tests: {test in lab_tests}")
        print()

if __name__ == "__main__":
    asyncio.run(test_conversion_debug())