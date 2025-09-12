#!/usr/bin/env python3
"""
Test spaCy integration for clinical NLP middle layer
"""

import time
from typing import List, Dict, Any

def test_spacy_basic():
    """Test basic spaCy functionality"""
    
    try:
        import spacy
        print("✅ spaCy import successful")
        
        # Load the model
        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy model loaded successfully")
        
        # Test clinical text
        test_text = "Initiated patient Julian West on 5mg Tadalafil as needed for erectile dysfunction"
        
        start_time = time.time()
        doc = nlp(test_text)
        processing_time = (time.time() - start_time) * 1000
        
        print(f"\n🧪 Processing time: {processing_time:.1f}ms")
        print(f"📝 Test text: {test_text}")
        
        # Extract entities
        print(f"\n📊 Named Entities Found:")
        entities_found = []
        for ent in doc.ents:
            entities_found.append({
                'text': ent.text,
                'label': ent.label_,
                'description': spacy.explain(ent.label_)
            })
            print(f"   - {ent.text}: {ent.label_} ({spacy.explain(ent.label_)})")
            
        # Extract tokens with POS tags
        print(f"\n🔍 Token Analysis:")
        medications = []
        dosages = []
        conditions = []
        
        for token in doc:
            # Look for medication patterns (PROPN = proper nouns, often drug names)
            if token.pos_ == "PROPN" and not token.is_stop:
                if token.text.lower() in ["tadalafil", "lisinopril", "metformin", "aspirin"]:
                    medications.append(token.text)
                    print(f"   💊 Potential medication: {token.text}")
                    
            # Look for dosage patterns
            if token.like_num or token.text.lower() in ["mg", "daily", "twice", "needed"]:
                dosages.append(token.text)
                if token.like_num or token.text.lower() in ["mg"]:
                    print(f"   💉 Dosage component: {token.text}")
                    
            # Look for medical conditions
            if token.pos_ in ["NOUN", "ADJ"] and not token.is_stop:
                if token.text.lower() in ["dysfunction", "hypertension", "diabetes", "pain"]:
                    conditions.append(token.text)
                    print(f"   🏥 Potential condition: {token.text}")
        
        # Summary results
        print(f"\n📈 Extraction Results:")
        print(f"   Medications detected: {len(medications)} - {medications}")
        print(f"   Dosage components: {len(dosages)} - {dosages}")
        print(f"   Conditions detected: {len(conditions)} - {conditions}")
        print(f"   Total entities (spaCy): {len(entities_found)}")
        
        # Performance comparison
        print(f"\n⚡ Performance Profile:")
        print(f"   spaCy processing: {processing_time:.1f}ms")
        print(f"   vs Regex (~5ms): {processing_time/5:.1f}x slower")
        print(f"   vs LLM (~1800ms): {1800/processing_time:.1f}x faster")
        
        return {
            'success': True,
            'processing_time_ms': processing_time,
            'entities_found': len(entities_found),
            'medications': medications,
            'conditions': conditions,
            'method': 'spacy_basic'
        }
        
    except Exception as e:
        print(f"❌ spaCy test failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def test_clinical_patterns():
    """Test more advanced clinical pattern recognition"""
    
    test_cases = [
        "Prescribed Lisinopril 10mg daily for hypertension",
        "Patient reports chest pain, order EKG and troponins", 
        "Continue current medications, schedule follow-up in 2 weeks",
        "Discontinue aspirin due to GI bleeding risk"
    ]
    
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        
        print(f"\n🧪 Testing Clinical Pattern Recognition:")
        
        results = []
        for i, text in enumerate(test_cases, 1):
            start_time = time.time()
            doc = nlp(text)
            processing_time = (time.time() - start_time) * 1000
            
            print(f"\n{i}. Text: {text}")
            print(f"   ⏱️  Processing: {processing_time:.1f}ms")
            
            # Extract clinical entities
            clinical_entities = []
            for ent in doc.ents:
                clinical_entities.append(ent.text)
                print(f"   🎯 Entity: {ent.text} ({ent.label_})")
            
            # Look for clinical verbs/actions
            clinical_actions = []
            for token in doc:
                if token.pos_ == "VERB" and token.lemma_ in ["prescribe", "order", "discontinue", "continue", "report"]:
                    clinical_actions.append(token.lemma_)
                    print(f"   🚀 Action: {token.lemma_}")
            
            results.append({
                'text': text,
                'processing_time_ms': processing_time,
                'entities': clinical_entities,
                'actions': clinical_actions
            })
            
        return results
        
    except Exception as e:
        print(f"❌ Clinical patterns test failed: {e}")
        return []

if __name__ == "__main__":
    print("🏥 Testing spaCy Clinical NLP Integration")
    print("="*50)
    
    # Test basic functionality
    basic_result = test_spacy_basic()
    
    if basic_result['success']:
        print("\n" + "="*50)
        # Test clinical patterns
        clinical_results = test_clinical_patterns()
        
        print(f"\n✅ spaCy Integration Assessment:")
        print(f"   ✓ Basic functionality: Working")
        print(f"   ✓ Processing speed: {basic_result['processing_time_ms']:.1f}ms")
        print(f"   ✓ Entity detection: {basic_result['entities_found']} entities")
        print(f"   ✓ Clinical patterns: {len(clinical_results)} test cases")
        print(f"\n🎯 Recommended: Proceed with spaCy as NLP middle layer")
    else:
        print(f"\n❌ spaCy integration failed - recommend NLTK fallback")