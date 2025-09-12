#!/usr/bin/env python3
"""
Debug NLP processing directly
"""

import asyncio
import sys
sys.path.append('/home/user/projects/nl-fhir/src')

from nl_fhir.services.conversion import ConversionService

async def debug_nlp():
    """Debug direct NLP calls"""
    
    conversion_service = ConversionService()
    
    test_text = "Start patient on Sertraline 100mg daily for depression"
    
    try:
        print(f"Testing: {test_text}")
        result = await conversion_service._basic_text_analysis(test_text, "debug-1")
        
        print(f"Result: {result}")
        
        medications = result.get('medications', [])
        lab_tests = result.get('lab_tests', [])
        procedures = result.get('procedures', [])
        conditions = result.get('conditions', [])
        
        print(f"Medications: {len(medications)}")
        print(f"Lab Tests: {len(lab_tests)}")
        print(f"Procedures: {len(procedures)}")
        print(f"Conditions: {len(conditions)}")
        
        if medications:
            print(f"Found medications: {[med['text'] for med in medications]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_nlp())