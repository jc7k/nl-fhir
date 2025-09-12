#!/usr/bin/env python3
"""
Debug script to test Enhanced NLP entity extraction
"""

import sys
sys.path.append('src')

from nl_fhir.services.nlp.models import NLPModelManager

def test_paclitaxel_extraction():
    """Test if the enhanced NLP can extract Paclitaxel"""
    
    test_text = "Prescribed patient Daniel Foster 100mg Paclitaxel IV weekly for metastatic breast cancer; neuropathy monitored."
    
    print(f"Testing text: {test_text}")
    print("=" * 80)
    
    model_manager = NLPModelManager()
    
    # Test direct entity extraction
    extracted = model_manager.extract_medical_entities(test_text)
    
    print("Extracted entities:")
    for entity_type, entities in extracted.items():
        print(f"  {entity_type}: {entities}")
    
    print("\n" + "=" * 80)
    
    # Test fallback regex patterns directly
    fallback_nlp = model_manager.load_fallback_nlp()
    
    print("Testing fallback regex patterns directly:")
    
    # Test medication pattern
    med_matches = list(fallback_nlp["medication_pattern"].finditer(test_text))
    print(f"Medication pattern matches: {len(med_matches)}")
    for i, match in enumerate(med_matches):
        print(f"  Match {i+1}: {match.groups()}")
        print(f"    Full match: '{match.group()}'")
    
    # Test alternative pattern
    alt_matches = list(fallback_nlp["alt_medication_pattern"].finditer(test_text))
    print(f"Alt medication pattern matches: {len(alt_matches)}")
    for i, match in enumerate(alt_matches):
        print(f"  Match {i+1}: {match.groups()}")
        print(f"    Full match: '{match.group()}'")
    
    # Test frequency pattern
    freq_matches = list(fallback_nlp["frequency_pattern"].finditer(test_text))
    print(f"Frequency pattern matches: {len(freq_matches)}")
    for i, match in enumerate(freq_matches):
        print(f"  Match {i+1}: {match.groups()}")
    
    # Test patient pattern
    patient_matches = list(fallback_nlp["patient_pattern"].finditer(test_text))
    print(f"Patient pattern matches: {len(patient_matches)}")
    for i, match in enumerate(patient_matches):
        print(f"  Match {i+1}: {match.groups()}")
    
    # Test condition pattern
    if "condition_pattern" in fallback_nlp:
        condition_matches = list(fallback_nlp["condition_pattern"].finditer(test_text))
        print(f"Condition pattern matches: {len(condition_matches)}")
        for i, match in enumerate(condition_matches):
            print(f"  Match {i+1}: {match.groups()}")

if __name__ == "__main__":
    test_paclitaxel_extraction()