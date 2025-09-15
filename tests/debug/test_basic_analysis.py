#!/usr/bin/env python3
"""
Test script to see what _basic_text_analysis extracts
"""

import asyncio
from src.nl_fhir.services.conversion import ConversionService

async def test_basic_analysis():
    """Test what _basic_text_analysis extracts"""
    
    clinical_text = "Order CBC with differential. Start aspirin 81mg daily. Schedule chest x-ray."
    
    print(f"Testing _basic_text_analysis...")
    print(f"Text: {clinical_text}")
    print("-" * 50)
    
    # Test the basic analysis directly
    service = ConversionService()
    result = await service._basic_text_analysis(clinical_text, "test-123")
    
    print(f"\nBasic analysis result:")
    print(f"Extracted entities: {result['extracted_entities']}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_basic_analysis())