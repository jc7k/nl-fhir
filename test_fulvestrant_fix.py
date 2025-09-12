#!/usr/bin/env python3
"""
Test Fulvestrant medication recognition fix
"""

import asyncio
import sys
sys.path.append('src')

from nl_fhir.services.nlp.pipeline import get_nlp_pipeline

async def test_fulvestrant_recognition():
    """Test that Fulvestrant is now properly recognized as a medication"""
    
    test_text = "Prescribed patient Lily Bell 100mg Fulvestrant IM every 2 weeks for ER+ breast cancer; injection site reactions discussed."
    
    print(f"Testing Fulvestrant recognition:")
    print(f"Input: {test_text}")
    print("=" * 80)
    
    # Use the exact same NLP pipeline as the server
    nlp_pipeline = await get_nlp_pipeline()
    
    # Process the text
    nlp_results = await nlp_pipeline.process_clinical_text(test_text)
    
    print("NLP Results:")
    print(f"  Keys: {list(nlp_results.keys()) if hasattr(nlp_results, 'keys') else 'No keys'}")
    
    # Check extracted entities
    extracted_entities = nlp_results.get("extracted_entities", {})
    print(f"\nExtracted entities:")
    
    for entity_type, entities in extracted_entities.items():
        entity_count = len(entities) if isinstance(entities, (list, tuple)) else "unknown"
        print(f"  {entity_type}: {entity_count} entities")
        if isinstance(entities, list) and entities:
            print(f"    Examples: {entities[:3]}")  # Show first 3 examples
    
    # Check for medications in the enhanced_entities
    enhanced_entities = extracted_entities.get("enhanced_entities", [])
    medications = [entity for entity in enhanced_entities if entity.get("entity_type") == "medication"]
    procedures = [entity for entity in enhanced_entities if entity.get("entity_type") in ["procedure", "lab_test"]]
    
    if medications:
        print(f"\n✅ SUCCESS: Found {len(medications)} medication(s)")
        for med in medications:
            print(f"   - {med.get('text', 'Unknown')} (confidence: {med.get('confidence', 'N/A')})")
    else:
        print(f"\n❌ FAILED: No medications found!")
    
    # Check for incorrect procedure detection
    if procedures:
        print(f"\n⚠️  WARNING: Found {len(procedures)} procedure(s) - should be 0 for medication text")
        for proc in procedures:
            print(f"   - {proc.get('text', 'Unknown')} (type: {proc.get('entity_type', 'Unknown')})")
    else:
        print(f"\n✅ Good: No incorrect procedure detection")
    
    return len(medications) > 0 and len(procedures) == 0

if __name__ == "__main__":
    success = asyncio.run(test_fulvestrant_recognition())
    if success:
        print(f"\n🎉 Fulvestrant recognition FIXED!")
    else:
        print(f"\n💥 Fulvestrant recognition still broken")
    sys.exit(0 if success else 1)