#!/usr/bin/env python3
"""
Corrected LLM parsing that extracts ALL structured data properly
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

async def test_correct_llm_parsing():
    # Test case from sample notes
    test_text = "Prescribed patient Liam Brooks 100mg Hydroxyurea daily for sickle cell disease; CBC tracked."
    
    print("=" * 80)
    print("CORRECTED LLM PARSING TEST")
    print("=" * 80)
    print(f"Test Text: {test_text}")
    print("-" * 80)
    
    # Expected entities
    expected = {
        "medications": ["Hydroxyurea"],
        "dosages": ["100mg"],
        "frequencies": ["daily"],
        "conditions": ["sickle cell disease"],
        "lab_tests": ["CBC"]
    }
    
    # Test LLM
    print("\n🤖 LLM ESCALATION WITH CORRECT PARSING:")
    llm_processor = LLMProcessor()
    if not llm_processor.initialized:
        llm_processor.initialize()
    
    start_time = time.time()
    llm_results = llm_processor.process_clinical_text(test_text, [], "debug-test")
    llm_time = time.time() - start_time
    
    structured_output = llm_results.get("structured_output", {})
    
    print(f"Processing Time: {llm_time:.3f}s")
    print("Raw LLM Structured Output:")
    print(json.dumps(structured_output, indent=2, default=str))
    
    # CORRECTED PARSING: Extract ALL data properly
    extracted_entities = []
    
    # Extract medications AND their embedded dosage/frequency
    for med in structured_output.get("medications", []):
        if isinstance(med, dict):
            # Add the medication name
            med_name = med.get("name", "")
            if med_name:
                extracted_entities.append({
                    "category": "medications",
                    "text": med_name,
                    "confidence": 0.9,
                    "source": "llm"
                })
            
            # Extract embedded dosage
            dosage = med.get("dosage", "")
            if dosage:
                extracted_entities.append({
                    "category": "dosages", 
                    "text": str(dosage),
                    "confidence": 0.9,
                    "source": "llm_embedded"
                })
            
            # Extract embedded frequency
            frequency = med.get("frequency", "")
            if frequency:
                extracted_entities.append({
                    "category": "frequencies",
                    "text": str(frequency),
                    "confidence": 0.9,
                    "source": "llm_embedded"
                })
            
            # Extract embedded route if needed
            route = str(med.get("route", ""))
            if route and route != "None":
                extracted_entities.append({
                    "category": "routes",
                    "text": route,
                    "confidence": 0.9,
                    "source": "llm_embedded"
                })
    
    # Extract conditions
    for condition in structured_output.get("conditions", []):
        if isinstance(condition, dict):
            condition_name = condition.get("name", "")
            if condition_name:
                extracted_entities.append({
                    "category": "conditions",
                    "text": condition_name,
                    "confidence": 0.9,
                    "source": "llm"
                })
    
    # Extract lab tests
    for lab in structured_output.get("lab_tests", []):
        if isinstance(lab, dict):
            lab_name = lab.get("name", "")
            if lab_name:
                extracted_entities.append({
                    "category": "lab_tests",
                    "text": lab_name,
                    "confidence": 0.9,
                    "source": "llm"
                })
    
    # Extract procedures
    for proc in structured_output.get("procedures", []):
        if isinstance(proc, dict):
            proc_name = proc.get("name", "")
            if proc_name:
                extracted_entities.append({
                    "category": "procedures",
                    "text": proc_name,
                    "confidence": 0.9,
                    "source": "llm"
                })
    
    print(f"\n✅ CORRECTLY EXTRACTED {len(extracted_entities)} ENTITIES:")
    for entity in extracted_entities:
        print(f"  ✓ {entity['category']}: '{entity['text']}' ({entity['confidence']:.1%}) [{entity['source']}]")
    
    # Now test pipeline for comparison
    print(f"\n🔬 CURRENT PIPELINE:")
    pipeline_start = time.time()
    pipeline_results = extract_medical_entities(test_text)
    pipeline_time = time.time() - pipeline_start
    
    pipeline_entities = []
    for category, entities in pipeline_results.items():
        for entity in entities:
            pipeline_entities.append({
                "category": category,
                "text": entity['text'],
                "confidence": entity.get('confidence', 0.0),
                "source": "pipeline"
            })
    
    print(f"Processing Time: {pipeline_time:.3f}s")
    print(f"Found {len(pipeline_entities)} entities:")
    for entity in pipeline_entities:
        print(f"  ✓ {entity['category']}: '{entity['text']}' ({entity['confidence']:.1%}) [{entity['source']}]")
    
    # Accuracy comparison
    print(f"\n🎯 CORRECTED ACCURACY COMPARISON:")
    print("-" * 50)
    
    def calculate_correct_matches(entities, expected_dict):
        matches = []
        misses = []
        
        for exp_category, exp_items in expected_dict.items():
            for exp_item in exp_items:
                found = False
                for entity in entities:
                    # Handle plural/singular category matching
                    entity_cat = entity["category"]
                    if (entity_cat == exp_category or 
                        entity_cat + "s" == exp_category or 
                        exp_category == entity_cat + "s" or
                        (entity_cat == "dosages" and exp_category == "dosages") or
                        (entity_cat == "frequencies" and exp_category == "frequencies")):
                        
                        # Case-insensitive text matching
                        if (exp_item.lower() in entity["text"].lower() or 
                            entity["text"].lower() in exp_item.lower() or
                            exp_item.lower() == entity["text"].lower()):
                            matches.append({
                                "expected": f"{exp_category}: {exp_item}",
                                "found": f"{entity_cat}: {entity['text']}",
                                "confidence": entity["confidence"],
                                "source": entity["source"]
                            })
                            found = True
                            break
                
                if not found:
                    misses.append(f"{exp_category}: {exp_item}")
        
        return matches, misses
    
    pipeline_matches, pipeline_misses = calculate_correct_matches(pipeline_entities, expected)
    llm_matches, llm_misses = calculate_correct_matches(extracted_entities, expected)
    
    total_expected = sum(len(items) for items in expected.values())
    
    print(f"PIPELINE RESULTS:")
    print(f"  ✅ Correct: {len(pipeline_matches)}/{total_expected} ({len(pipeline_matches)/total_expected:.1%})")
    for match in pipeline_matches:
        print(f"    ✓ {match['found']} [{match['source']}]")
    for miss in pipeline_misses:
        print(f"    ❌ MISSED: {miss}")
    
    print(f"\nLLM RESULTS:")
    print(f"  ✅ Correct: {len(llm_matches)}/{total_expected} ({len(llm_matches)/total_expected:.1%})")
    for match in llm_matches:
        print(f"    ✓ {match['found']} [{match['source']}]")
    for miss in llm_misses:
        print(f"    ❌ MISSED: {miss}")
    
    # Performance comparison
    print(f"\n⚡ PERFORMANCE COMPARISON:")
    print(f"Pipeline: {pipeline_time:.3f}s ({pipeline_time/llm_time:.1f}x faster)" if llm_time > 0 else f"Pipeline: {pipeline_time:.3f}s")
    print(f"LLM:      {llm_time:.3f}s")
    
    print(f"\n📊 FINAL VERDICT:")
    if len(llm_matches) > len(pipeline_matches):
        print(f"✅ LLM WINS: {len(llm_matches)} vs {len(pipeline_matches)} correct entities")
        print(f"   + LLM provides structured data with embedded metadata")
        llm_extras = set(m['expected'] for m in llm_matches) - set(m['expected'] for m in pipeline_matches)
        if llm_extras:
            print(f"   + LLM found entities pipeline missed: {llm_extras}")
    elif len(pipeline_matches) > len(llm_matches):
        print(f"✅ PIPELINE WINS: {len(pipeline_matches)} vs {len(llm_matches)} correct entities")
    else:
        print(f"🤝 TIE: Both found {len(pipeline_matches)} correct entities")
        print(f"   But LLM provides richer structured data and embedded relationships")

if __name__ == "__main__":
    asyncio.run(test_correct_llm_parsing())