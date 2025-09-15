#!/usr/bin/env python3
"""
Single Case NLP Test - Isolate performance issue
"""

import sys
sys.path.append('../../src')

import time
from nl_fhir.services.nlp.models import model_manager

def test_single_case():
    """Test NLP processing with a single case"""

    print("🔬 SINGLE CASE NLP TEST")
    print("="*30)

    # Test simple positive case
    positive_text = "Give patient John Smith 1mg IV push of epinephrine for NSTEMI."
    print(f"🧪 Testing positive case: {positive_text}")

    start_time = time.time()
    try:
        result = model_manager.extract_medical_entities(positive_text)
        end_time = time.time()

        print(f"✅ Positive case completed in {end_time - start_time:.3f} seconds")
        print(f"📊 Result structure: {list(result.keys())}")
        for category, entities in result.items():
            if entities:
                print(f"   {category}: {len(entities)} entities")
    except Exception as e:
        print(f"❌ Positive case failed: {e}")

    print()

    # Test negative case
    negative_text = "Patient allergic to penicillin, prescribe amoxicillin 500mg TID."
    print(f"🧪 Testing negative case: {negative_text}")

    start_time = time.time()
    try:
        result = model_manager.extract_medical_entities(negative_text)
        end_time = time.time()

        print(f"✅ Negative case completed in {end_time - start_time:.3f} seconds")
        print(f"📊 Result structure: {list(result.keys())}")
        for category, entities in result.items():
            if entities:
                print(f"   {category}: {len(entities)} entities")
    except Exception as e:
        print(f"❌ Negative case failed: {e}")

if __name__ == "__main__":
    test_single_case()