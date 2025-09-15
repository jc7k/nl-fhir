#!/usr/bin/env python3
"""
Corrected LLM vs Pipeline comparison showing true accuracy
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

async def corrected_comparison():
    # Test case from sample notes
    test_text = "Prescribed patient Liam Brooks 100mg Hydroxyurea daily for sickle cell disease; CBC tracked."
    
    print("=" * 80)
    print("CORRECTED COMPARISON: LLM vs PIPELINE")
    print("=" * 80)
    print(f"Test: {test_text}")
    print("-" * 80)
    
    # Expected entities
    expected = {
        "medications": ["Hydroxyurea"],
        "dosages": ["100mg"],
        "frequencies": ["daily"],
        "conditions": ["sickle cell disease"],
        "lab_tests": ["CBC"]
    }
    
    # Test pipeline
    print("\n🔬 CURRENT PIPELINE:")
    pipeline_results = extract_medical_entities(test_text)
    
    pipeline_entities = []
    for category, entities in pipeline_results.items():
        for entity in entities:
            pipeline_entities.append({
                "category": category,
                "text": entity['text'],
                "confidence": entity.get('confidence', 0.0)
            })
    
    print(f"Found {len(pipeline_entities)} entities:")
    for entity in pipeline_entities:
        print(f"  ✓ {entity['category']}: '{entity['text']}' ({entity['confidence']:.1%})")
    
    # Test LLM
    print(f"\n🤖 LLM ESCALATION:")
    llm_processor = LLMProcessor()
    if not llm_processor.initialized:
        llm_processor.initialize()
    
    llm_results = llm_processor.process_clinical_text(test_text, [], "debug-test")
    structured_output = llm_results.get("structured_output", {})
    
    llm_entities = []
    
    # Extract from structured LLM output
    if "medications" in structured_output:
        for med in structured_output["medications"]:
            if isinstance(med, dict):
                llm_entities.append({
                    "category": "medications",
                    "text": med.get("name", str(med)),
                    "confidence": 0.9,
                    "extra_data": {
                        "dosage": med.get("dosage"),
                        "frequency": med.get("frequency"),
                        "route": str(med.get("route", ""))
                    }
                })
    
    if "lab_tests" in structured_output:
        for lab in structured_output["lab_tests"]:
            if isinstance(lab, dict):
                llm_entities.append({
                    "category": "lab_tests", 
                    "text": lab.get("name", str(lab)),
                    "confidence": 0.9,
                    "extra_data": {
                        "test_type": lab.get("test_type"),
                        "urgency": str(lab.get("urgency", ""))
                    }
                })
    
    if "conditions" in structured_output:
        for condition in structured_output["conditions"]:
            if isinstance(condition, dict):
                llm_entities.append({
                    "category": "conditions",
                    "text": condition.get("name", str(condition)),
                    "confidence": 0.9,
                    "extra_data": {
                        "status": condition.get("status"),
                        "severity": condition.get("severity")
                    }
                })
    
    print(f"Found {len(llm_entities)} entities:")
    for entity in llm_entities:
        print(f"  ✓ {entity['category']}: '{entity['text']}' ({entity['confidence']:.1%})")
        if "extra_data" in entity:
            for key, value in entity["extra_data"].items():
                if value:
                    print(f"    └─ {key}: {value}")
    
    # Accuracy comparison
    print(f"\n🎯 ACCURACY COMPARISON:")
    print("-" * 40)
    
    def check_expected_matches(entities, expected_dict):
        matches = []
        misses = []
        
        for exp_category, exp_items in expected_dict.items():
            for exp_item in exp_items:
                found = False
                for entity in entities:
                    if entity["category"] == exp_category or entity["category"] + "s" == exp_category or exp_category == entity["category"] + "s":
                        if exp_item.lower() in entity["text"].lower() or entity["text"].lower() in exp_item.lower():
                            matches.append({
                                "expected": f"{exp_category}: {exp_item}",
                                "found": f"{entity['category']}: {entity['text']}",
                                "confidence": entity["confidence"]
                            })
                            found = True
                            break
                
                if not found:
                    misses.append(f"{exp_category}: {exp_item}")
        
        return matches, misses
    
    pipeline_matches, pipeline_misses = check_expected_matches(pipeline_entities, expected)
    llm_matches, llm_misses = check_expected_matches(llm_entities, expected)
    
    print(f"PIPELINE ACCURACY:")
    print(f"  ✅ Correct: {len(pipeline_matches)}/{len(expected['medications']) + len(expected['dosages']) + len(expected['frequencies']) + len(expected['conditions']) + len(expected['lab_tests'])}")
    for match in pipeline_matches:
        print(f"    ✓ {match['found']} ({match['confidence']:.1%})")
    for miss in pipeline_misses:
        print(f"    ❌ MISSED: {miss}")
    
    print(f"\nLLM ACCURACY:")
    print(f"  ✅ Correct: {len(llm_matches)}/{len(expected['medications']) + len(expected['dosages']) + len(expected['frequencies']) + len(expected['conditions']) + len(expected['lab_tests'])}")
    for match in llm_matches:
        print(f"    ✓ {match['found']} ({match['confidence']:.1%})")
    for miss in llm_misses:
        print(f"    ❌ MISSED: {miss}")
    
    print(f"\n📊 FINAL VERDICT:")
    if len(llm_matches) > len(pipeline_matches):
        print(f"✅ LLM WINS: {len(llm_matches)} vs {len(pipeline_matches)} correct entities")
        print(f"   + LLM provides structured data with metadata")
        print(f"   + LLM found entities pipeline missed: {set(m['expected'] for m in llm_matches) - set(m['expected'] for m in pipeline_matches)}")
    elif len(pipeline_matches) > len(llm_matches):
        print(f"✅ PIPELINE WINS: {len(pipeline_matches)} vs {len(llm_matches)} correct entities")
    else:
        print(f"🤝 TIE: Both found {len(pipeline_matches)} correct entities")
        print(f"   But LLM provides richer structured data")

if __name__ == "__main__":
    asyncio.run(corrected_comparison())