#!/usr/bin/env python3
"""
Test NLP using the exact same import path as the server
"""

import asyncio
import sys
sys.path.append('src')

from nl_fhir.services.nlp.pipeline import get_nlp_pipeline

async def test_server_nlp_pipeline():
    """Test the exact NLP pipeline the server uses"""
    
    test_text = "Prescribed patient Daniel Foster 100mg Paclitaxel IV weekly for metastatic breast cancer; neuropathy monitored."
    
    print(f"Testing text: {test_text}")
    print("=" * 80)
    
    # Use the exact same NLP pipeline as the server
    nlp_pipeline = await get_nlp_pipeline()
    
    # Process the text
    nlp_results = await nlp_pipeline.process_clinical_text(test_text)
    
    print("NLP Results:")
    print(f"  Raw structure: {type(nlp_results)}")
    print(f"  Keys: {list(nlp_results.keys()) if hasattr(nlp_results, 'keys') else 'No keys'}")
    
    # Check extracted entities
    extracted_entities = nlp_results.get("extracted_entities", {})
    print(f"\nExtracted entities structure: {type(extracted_entities)}")
    print(f"  Keys: {list(extracted_entities.keys()) if hasattr(extracted_entities, 'keys') else 'No keys'}")
    
    for entity_type, entities in extracted_entities.items():
        entity_count = len(entities) if isinstance(entities, (list, tuple)) else "unknown"
        print(f"  {entity_type}: {entity_count} entities")
        if isinstance(entities, list) and entities:
            print(f"    Examples: {entities[:2]}")  # Show first 2 examples

if __name__ == "__main__":
    asyncio.run(test_server_nlp_pipeline())