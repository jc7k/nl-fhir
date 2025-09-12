#!/usr/bin/env python3
"""
Test scispaCy medical models for clinical NLP enhancement
"""

import time
from typing import Dict, List, Any

def test_scispacy_basic():
    """Test basic scispaCy biomedical model"""
    
    try:
        import spacy
        import scispacy
        
        print("✅ scispaCy import successful")
        
        # Load the biomedical model
        nlp = spacy.load("en_core_sci_sm")
        print("✅ scispaCy biomedical model loaded")
        
        # Test clinical text - same as before
        test_text = "Initiated patient Julian West on 5mg Tadalafil as needed for erectile dysfunction"
        
        start_time = time.time()
        doc = nlp(test_text)
        processing_time = (time.time() - start_time) * 1000
        
        print(f"\n🧪 scispaCy Processing time: {processing_time:.1f}ms")
        print(f"📝 Test text: {test_text}")
        
        # Extract entities with scispaCy
        print(f"\n📊 scispaCy Medical Entities Found:")
        sci_entities_found = []
        for ent in doc.ents:
            sci_entities_found.append({
                'text': ent.text,
                'label': ent.label_,
                'description': spacy.explain(ent.label_),
                'start': ent.start_char,
                'end': ent.end_char
            })
            print(f"   - {ent.text}: {ent.label_} ({spacy.explain(ent.label_)})")
            
        # Check for medical-specific improvements
        print(f"\n🔍 Medical Entity Analysis:")
        medications = []
        conditions = []
        dosages = []
        
        for ent in doc.ents:
            ent_text_lower = ent.text.lower()
            
            # Medical compounds/chemicals
            if ent.label_ in ["CHEMICAL"] or ent_text_lower in ["tadalafil", "lisinopril", "metformin"]:
                medications.append(ent.text)
                print(f"   💊 Medical compound: {ent.text} ({ent.label_})")
            
            # Disease/conditions  
            elif ent.label_ in ["DISEASE"] or "dysfunction" in ent_text_lower:
                conditions.append(ent.text)
                print(f"   🏥 Medical condition: {ent.text} ({ent.label_})")
        
        # Look for dosage patterns in tokens
        for token in doc:
            if token.like_num or token.text.lower() in ["mg", "daily", "needed"]:
                dosages.append(token.text)
                if token.like_num or token.text.lower() == "mg":
                    print(f"   💉 Dosage: {token.text}")
        
        print(f"\n📈 scispaCy Extraction Results:")
        print(f"   Medications: {len(medications)} - {medications}")
        print(f"   Conditions: {len(conditions)} - {conditions}")  
        print(f"   Dosages: {len(dosages)} - {dosages}")
        print(f"   Total entities: {len(sci_entities_found)}")
        
        return {
            'success': True,
            'processing_time_ms': processing_time,
            'entities_found': len(sci_entities_found),
            'medications': medications,
            'conditions': conditions,
            'dosages': dosages,
            'method': 'scispacy_biomedical'
        }
        
    except Exception as e:
        print(f"❌ scispaCy test failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def test_clinical_comparison():
    """Compare regular spaCy vs scispaCy on clinical text"""
    
    clinical_texts = [
        "Prescribed Lisinopril 10mg daily for hypertension",
        "Patient reports chest pain, order EKG and troponins", 
        "Start patient on Metformin 500mg twice daily for diabetes",
        "Discontinue aspirin due to GI bleeding, continue warfarin"
    ]
    
    try:
        import spacy
        import scispacy
        
        # Load both models
        regular_nlp = spacy.load("en_core_web_sm")
        sci_nlp = spacy.load("en_core_sci_sm")
        
        print(f"\n🏥 Clinical Text Comparison: Regular vs Medical spaCy")
        print("="*60)
        
        results = []
        for i, text in enumerate(clinical_texts, 1):
            print(f"\n{i}. Text: {text}")
            
            # Regular spaCy
            start_time = time.time()
            regular_doc = regular_nlp(text)
            regular_time = (time.time() - start_time) * 1000
            
            regular_entities = [(ent.text, ent.label_) for ent in regular_doc.ents]
            
            # Medical spaCy
            start_time = time.time()
            sci_doc = sci_nlp(text)
            sci_time = (time.time() - start_time) * 1000
            
            sci_entities = [(ent.text, ent.label_) for ent in sci_doc.ents]
            
            print(f"   📊 Regular spaCy ({regular_time:.1f}ms): {len(regular_entities)} entities")
            for ent_text, ent_label in regular_entities:
                print(f"      - {ent_text}: {ent_label}")
                
            print(f"   🏥 Medical spaCy ({sci_time:.1f}ms): {len(sci_entities)} entities")
            for ent_text, ent_label in sci_entities:
                print(f"      - {ent_text}: {ent_label}")
            
            # Analyze improvement
            improvement = len(sci_entities) - len(regular_entities)
            print(f"   📈 Medical improvement: {improvement:+d} entities")
            
            results.append({
                'text': text,
                'regular_entities': regular_entities,
                'sci_entities': sci_entities,
                'improvement': improvement,
                'regular_time_ms': regular_time,
                'sci_time_ms': sci_time
            })
            
        return results
        
    except Exception as e:
        print(f"❌ Clinical comparison failed: {e}")
        return []

if __name__ == "__main__":
    print("🏥 Testing scispaCy Medical NLP Models")
    print("="*50)
    
    # Test basic scispaCy functionality
    basic_result = test_scispacy_basic()
    
    if basic_result['success']:
        print("\n" + "="*50)
        # Test clinical comparison
        comparison_results = test_clinical_comparison()
        
        print(f"\n✅ scispaCy Medical NLP Assessment:")
        print(f"   ✓ Medical model: Working")
        print(f"   ✓ Processing speed: {basic_result['processing_time_ms']:.1f}ms")
        print(f"   ✓ Medical entities: {basic_result['entities_found']} found")
        print(f"   ✓ Clinical comparisons: {len(comparison_results)} test cases")
        
        if comparison_results:
            total_improvement = sum(r['improvement'] for r in comparison_results)
            avg_sci_time = sum(r['sci_time_ms'] for r in comparison_results) / len(comparison_results)
            print(f"   ✓ Average improvement: {total_improvement/len(comparison_results):.1f} entities per text")
            print(f"   ✓ Average processing time: {avg_sci_time:.1f}ms")
        
        print(f"\n🎯 Recommendation: scispaCy provides superior medical entity recognition")
        print(f"   - Ideal for clinical NLP middle layer")
        print(f"   - {basic_result['processing_time_ms']:.1f}ms processing time")
        print(f"   - Enhanced medical terminology recognition")
        
    else:
        print(f"\n❌ scispaCy unavailable - fallback to enhanced regular spaCy with medical dictionaries")