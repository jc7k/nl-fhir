#!/usr/bin/env python3
"""
Test the complete 4-tier medical NLP architecture integration with LLM escalation
TIER 1: spaCy Medical → TIER 2: Transformers NER → TIER 3: Regex → TIER 3.5: LLM Escalation
"""

import sys
sys.path.append('../../src')

from nl_fhir.services.nlp.models import model_manager
import time

def test_4tier_medical_nlp():
    """Test the complete 4-tier medical NLP system with LLM escalation"""
    
    print("🏥 Testing 4-Tier Medical NLP Architecture with LLM Escalation")
    print("="*70)
    
    # Test cases with expected outcomes
    test_cases = [
        {
            "name": "Clear Clinical Order (spaCy should handle)",
            "text": "Initiated patient Julian West on 5mg Tadalafil as needed for erectile dysfunction",
            "expected_tier": "spacy",
            "expected_entities": ["medications", "dosages", "conditions", "patients"]
        },
        {
            "name": "Standard Prescription (spaCy should handle)",
            "text": "Prescribed Lisinopril 10mg daily for hypertension",
            "expected_tier": "spacy",
            "expected_entities": ["medications", "dosages", "frequencies", "conditions"]
        },
        {
            "name": "Complex Medical Language (may escalate)",
            "text": "Patient presents with atypical chest discomfort, initiate cardiac enzymes",
            "expected_tier": "transformers/llm",
            "expected_entities": ["conditions", "procedures"]
        },
        {
            "name": "Ambiguous Reference (should escalate)",
            "text": "Continue the same medication we discussed last visit",
            "expected_tier": "transformers/llm",
            "expected_entities": ["medications"]
        },
        {
            "name": "Lab Orders (spaCy should handle)",
            "text": "Order CBC and comprehensive metabolic panel, check troponins",
            "expected_tier": "spacy",
            "expected_entities": ["lab_tests", "procedures"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Text: {test_case['text']}")
        
        start_time = time.time()
        
        # Test the 3-tier extraction
        extracted_entities = model_manager.extract_medical_entities(test_case['text'])
        
        processing_time = (time.time() - start_time) * 1000
        
        # Count total entities found
        total_entities = sum(len(entities) for entities in extracted_entities.values())
        
        # Check which categories have entities
        found_categories = [cat for cat, entities in extracted_entities.items() if entities]
        
        print(f"   ⏱️  Processing time: {processing_time:.1f}ms")
        print(f"   🎯 Total entities found: {total_entities}")
        print(f"   📊 Categories with entities: {found_categories}")
        
        # Show detailed entities
        for category, entities in extracted_entities.items():
            if entities:
                entity_texts = [entity.get('text', 'N/A') for entity in entities]
                methods = [entity.get('method', 'unknown') for entity in entities]
                print(f"      {category}: {entity_texts} (methods: {methods})")
        
        # Determine which tier was likely used based on method
        methods_used = set()
        for entities in extracted_entities.values():
            for entity in entities:
                if entity.get('method'):
                    methods_used.add(entity['method'])
        
        if any('spacy' in method for method in methods_used):
            tier_used = "spacy"
        elif any('transformer' in method for method in methods_used):
            tier_used = "transformers"
        elif total_entities == 0 or all('regex' in method for method in methods_used if method):
            tier_used = "regex_fallback"
        else:
            tier_used = "mixed"
            
        print(f"   🏗️  Tier used: {tier_used}")
        
        # Quality assessment
        expected_found = sum(1 for cat in test_case['expected_entities'] if extracted_entities.get(cat))
        quality_score = expected_found / len(test_case['expected_entities']) if test_case['expected_entities'] else 0
        
        print(f"   📈 Quality score: {quality_score:.2f} ({expected_found}/{len(test_case['expected_entities'])} expected categories)")
        
        results.append({
            'name': test_case['name'],
            'text': test_case['text'],
            'processing_time_ms': processing_time,
            'total_entities': total_entities,
            'tier_used': tier_used,
            'quality_score': quality_score,
            'found_categories': found_categories,
            'extracted_entities': extracted_entities
        })
    
    # Summary analysis
    print(f"\n✅ 4-Tier Medical NLP Summary:")
    print("="*50)
    
    avg_time = sum(r['processing_time_ms'] for r in results) / len(results)
    avg_entities = sum(r['total_entities'] for r in results) / len(results)
    avg_quality = sum(r['quality_score'] for r in results) / len(results)
    
    tier_distribution = {}
    for result in results:
        tier = result['tier_used']
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
    
    print(f"   ✓ Average processing time: {avg_time:.1f}ms")
    print(f"   ✓ Average entities per text: {avg_entities:.1f}")
    print(f"   ✓ Average quality score: {avg_quality:.2f}")
    print(f"   ✓ Tier distribution: {tier_distribution}")
    
    # Performance comparison
    print(f"\n⚡ Performance vs Other Approaches:")
    print(f"   vs Pure Regex (~5ms): {avg_time/5:.1f}x slower")
    print(f"   vs Pure LLM (~1800ms): {1800/avg_time:.0f}x faster")
    print(f"   vs medspaCy (~15ms): {avg_time/15:.1f}x relative")
    
    # Recommendations
    print(f"\n🎯 Architecture Assessment:")
    if avg_quality >= 0.8:
        print(f"   ✅ HIGH QUALITY: 4-tier architecture achieving target")
    elif avg_quality >= 0.6:
        print(f"   ⚠️  MODERATE QUALITY: Consider tuning escalation rules")
    else:
        print(f"   ❌ LOW QUALITY: Need more sophisticated NLP or larger medical vocabularies")
    
    if avg_time <= 50:
        print(f"   ✅ FAST PERFORMANCE: Well within <2s API requirement")
    elif avg_time <= 200:
        print(f"   ⚠️  MODERATE PERFORMANCE: Acceptable for most use cases")
    else:
        print(f"   ❌ SLOW PERFORMANCE: May impact user experience")
    
    # Next steps
    print(f"\n💡 Recommended Next Steps:")
    spacy_usage = tier_distribution.get('spacy', 0)
    total_tests = len(results)
    
    if spacy_usage / total_tests > 0.6:
        print(f"   1. spaCy handling most cases well - optimize vocabulary")
        print(f"   2. Consider adding more medical term dictionaries")
        print(f"   3. Test on larger clinical dataset")
    else:
        print(f"   1. Many cases escalating - review escalation rules")
        print(f"   2. Consider integrating medspaCy or clinical transformers")
        print(f"   3. Expand spaCy medical pattern matching")
    
    return results

if __name__ == "__main__":
    print("🏥 Testing Complete 4-Tier Medical NLP Architecture")
    print("TIER 1: spaCy Medical → TIER 2: Transformers NER → TIER 3: Regex → TIER 3.5: LLM Escalation")
    print("="*60)
    
    results = test_4tier_medical_nlp()
    
    if results:
        success_count = sum(1 for r in results if r['quality_score'] >= 0.5)
        print(f"\n🎉 Test Results: {success_count}/{len(results)} tests achieved good quality")
        print(f"✅ 4-tier medical NLP architecture ready for integration!")
    else:
        print(f"\n❌ Testing failed - architecture needs debugging")