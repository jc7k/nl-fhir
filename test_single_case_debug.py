#!/usr/bin/env python3
"""
Debug single case to show exactly what LLM vs Pipeline produces
"""

import asyncio
import time
import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nl_fhir.services.nlp.models import extract_medical_entities
from nl_fhir.services.nlp.llm_processor import LLMProcessor

async def debug_single_case():
    # Random case from sample notes
    test_text = "Prescribed patient Liam Brooks 100mg Hydroxyurea daily for sickle cell disease; CBC tracked."
    
    print("=" * 80)
    print("DETAILED COMPARISON: SINGLE CASE DEBUG")
    print("=" * 80)
    print(f"Test Text: {test_text}")
    print("-" * 80)
    
    # Test current pipeline
    print("\n🔬 CURRENT PIPELINE RESULTS:")
    start_time = time.time()
    pipeline_results = extract_medical_entities(test_text)
    pipeline_time = time.time() - start_time
    
    print(f"Processing Time: {pipeline_time:.3f}s")
    print("Raw Results:")
    for category, entities in pipeline_results.items():
        if entities:  # Only show categories with results
            print(f"  {category}:")
            for entity in entities:
                print(f"    - Text: '{entity['text']}'")
                print(f"      Confidence: {entity.get('confidence', 0.0):.1%}")
                print(f"      Source: {entity.get('source', 'unknown')}")
    
    # Test LLM escalation
    print("\n🤖 LLM ESCALATION RESULTS:")
    llm_processor = LLMProcessor()
    if not llm_processor.initialized:
        llm_processor.initialize()
    
    start_time = time.time()
    llm_results = llm_processor.process_clinical_text(test_text, [], "debug-test")
    llm_time = time.time() - start_time
    
    print(f"Processing Time: {llm_time:.3f}s")
    print("Raw LLM Response:")
    print(json.dumps(llm_results, indent=2))
    
    # Show what we expect vs what we get
    print("\n📊 EXPECTED vs ACTUAL:")
    print("-" * 40)
    expected = {
        "medications": ["Hydroxyurea"],
        "dosages": ["100mg"],
        "frequencies": ["daily"],
        "conditions": ["sickle cell disease"],
        "lab_tests": ["CBC"]
    }
    
    print("EXPECTED ENTITIES:")
    for cat, items in expected.items():
        print(f"  {cat}: {items}")
    
    print(f"\nPIPELINE FOUND:")
    pipeline_found = {}
    for category, entities in pipeline_results.items():
        if entities:
            pipeline_found[category] = [e['text'] for e in entities]
    for cat, items in pipeline_found.items():
        print(f"  {cat}: {items}")
    
    print(f"\nLLM FOUND:")
    llm_structured = llm_results.get("structured_output", {})
    llm_found = {}
    for cat in expected.keys():
        if cat in llm_structured and llm_structured[cat]:
            llm_found[cat] = llm_structured[cat] if isinstance(llm_structured[cat], list) else [llm_structured[cat]]
    for cat, items in llm_found.items():
        print(f"  {cat}: {items}")
    
    # Accuracy analysis
    print("\n🎯 ACCURACY ANALYSIS:")
    print("-" * 30)
    
    def calculate_matches(found_dict, expected_dict):
        total_expected = sum(len(items) for items in expected_dict.values())
        total_found = sum(len(items) for items in found_dict.values())
        correct_matches = 0
        
        for cat, expected_items in expected_dict.items():
            found_items = found_dict.get(cat, [])
            for expected_item in expected_items:
                for found_item in found_items:
                    if expected_item.lower() in found_item.lower() or found_item.lower() in expected_item.lower():
                        correct_matches += 1
                        break
        
        precision = correct_matches / total_found if total_found > 0 else 0
        recall = correct_matches / total_expected if total_expected > 0 else 0
        return precision, recall, correct_matches, total_found, total_expected
    
    pipeline_precision, pipeline_recall, pipeline_matches, pipeline_total, expected_total = calculate_matches(pipeline_found, expected)
    llm_precision, llm_recall, llm_matches, llm_total, expected_total = calculate_matches(llm_found, expected)
    
    print(f"PIPELINE: {pipeline_matches}/{expected_total} correct ({pipeline_precision:.1%} precision, {pipeline_recall:.1%} recall)")
    print(f"LLM:      {llm_matches}/{expected_total} correct ({llm_precision:.1%} precision, {llm_recall:.1%} recall)")
    
    print(f"\n⚡ SPEED COMPARISON:")
    print(f"Pipeline: {pipeline_time:.3f}s ({pipeline_time/llm_time:.1f}x faster)" if llm_time > 0 else f"Pipeline: {pipeline_time:.3f}s")
    print(f"LLM:      {llm_time:.3f}s")
    
    if llm_matches > pipeline_matches:
        print(f"\n✅ LLM IS BETTER: Found {llm_matches - pipeline_matches} more correct entities")
    elif pipeline_matches > llm_matches:
        print(f"\n✅ PIPELINE IS BETTER: Found {pipeline_matches - llm_matches} more correct entities")
    else:
        print(f"\n🤝 TIE: Both found {pipeline_matches} correct entities")

if __name__ == "__main__":
    asyncio.run(debug_single_case())