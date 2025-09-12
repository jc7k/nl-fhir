#!/usr/bin/env python3
"""
Test Geriatric Clinical Notes - Multi-Specialty Validation
Process 20 geriatric encounter notes and compare with pediatric results
"""

import sys
sys.path.append('src')

import asyncio
import json
import time
from pathlib import Path
from nl_fhir.services.nlp.models import model_manager

# The 20 geriatric clinical notes you provided
GERIATRIC_CLINICAL_NOTES = [
    "Started patient Margaret Hill on 10mg Donepezil once daily for mild Alzheimer's disease; discussed GI side effects.",
    "Prescribed patient George Allen 25mg Hydrochlorothiazide once daily for hypertension; monitored electrolytes.",
    "Initiated patient Ruth Simmons on 5mg Warfarin daily; INR to be checked in 3 days.",
    "Started patient Harold Wright on 10mg Rosuvastatin nightly for hyperlipidemia; advised on muscle pain.",
    "Prescribed patient Dorothy King 0.125mg Digoxin once daily for atrial fibrillation; ordered renal panel.",
    "Recommended patient Edward Baker begin 500mg Calcium with vitamin D twice daily for osteoporosis.",
    "Started patient Betty Turner on 5mg Amlodipine once daily for blood pressure control.",
    "Prescribed patient Frank Mitchell 10mg Citalopram once daily for depressive symptoms; follow-up in 2 weeks.",
    "Initiated patient Nancy Carter on 5mg Oxybutynin twice daily for urinary incontinence; discussed dry mouth.",
    "Started patient Walter Perez on 10mg Rivaroxaban once daily for stroke prevention in atrial fibrillation.",
    "Prescribed patient Helen Morris 0.5mg Lorazepam at bedtime for insomnia; advised on fall risk.",
    "Started patient Arthur Reed on 500mg Metformin twice daily for type 2 diabetes; monitored renal function.",
    "Initiated patient Barbara Jenkins on 25mg Sertraline once daily for anxiety; discussed delayed onset of action.",
    "Prescribed patient Charles Foster 1 drop of Latanoprost in both eyes nightly for glaucoma.",
    "Started patient Gloria Sanders on 75mg Clopidogrel once daily post-stroke; reviewed bleeding precautions.",
    "Recommended patient Henry Powell begin 10mg Memantine twice daily for moderate Alzheimer's disease.",
    "Prescribed patient Joan Rivera 5mg Bisacodyl orally as needed for constipation; encouraged hydration.",
    "Started patient Donald Hayes on 0.5mg Tamsulosin nightly for BPH; advised on orthostatic hypotension.",
    "Initiated patient Rose Bennett on 10mg Pantoprazole once daily for GERD; discussed long-term risks.",
    "Prescribed patient Paul Griffin 1 patch of Fentanyl 25mcg/hr every 72 hours for chronic pain; monitored for sedation."
]

async def process_geriatric_batch():
    """Process geriatric clinical notes and compare with pediatric performance"""
    
    print("👵 Processing Geriatric Clinical Notes - Multi-Specialty Test")
    print("="*68)
    print(f"📝 Processing {len(GERIATRIC_CLINICAL_NOTES)} geriatric encounter notes...")
    print("Comparing performance with pediatric results from previous batch\n")
    
    results = []
    start_time = time.time()
    
    # Track geriatric-specific metrics
    all_medications = set()
    all_conditions = set()
    geriatric_conditions = set()
    complex_medications = []
    
    for i, note in enumerate(GERIATRIC_CLINICAL_NOTES, 1):
        print(f"{i:2d}. {note}")
        
        note_start = time.time()
        
        try:
            # Extract medical entities using our 3-tier system
            entities = model_manager.extract_medical_entities(note)
            
            processing_time = (time.time() - note_start) * 1000
            
            # Count entities
            total_entities = sum(len(entity_list) for entity_list in entities.values())
            
            # Determine tier used
            methods_used = set()
            for entity_list in entities.values():
                for entity in entity_list:
                    if entity.get('method'):
                        methods_used.add(entity['method'])
            
            if any('spacy' in method for method in methods_used):
                tier_used = "spacy"
            elif any('transformer' in method for method in methods_used):
                tier_used = "transformers"  
            else:
                tier_used = "regex"
            
            # Calculate quality score
            words = len(note.split())
            quality_score = min(1.0, total_entities / max(1, words * 0.1))
            
            # Collect medications and conditions for analysis
            for med in entities.get('medications', []):
                med_text = med.get('text', '').lower()
                all_medications.add(med_text)
                
                # Track complex geriatric medications
                if med_text in ['donepezil', 'hydrochlorothiazide', 'warfarin', 'rosuvastatin', 
                               'digoxin', 'rivaroxaban', 'lorazepam', 'clopidogrel', 'memantine',
                               'tamsulosin', 'pantoprazole', 'fentanyl']:
                    complex_medications.append(med_text)
            
            for condition in entities.get('conditions', []):
                condition_text = condition.get('text', '').lower()
                all_conditions.add(condition_text)
                
                # Track geriatric-specific conditions
                if any(geriatric_term in condition_text for geriatric_term in [
                    'alzheimer', 'dementia', 'hypertension', 'hyperlipidemia', 
                    'atrial fibrillation', 'osteoporosis', 'incontinence', 'insomnia',
                    'diabetes', 'anxiety', 'glaucoma', 'stroke', 'constipation', 
                    'bph', 'gerd', 'chronic pain'
                ]):
                    geriatric_conditions.add(condition_text)
            
            result = {
                'note_number': i,
                'patient_name': extract_patient_name(note),
                'clinical_text': note,
                'processing_time_ms': processing_time,
                'entities_found': total_entities,
                'tier_used': tier_used,
                'quality_score': quality_score,
                'entities': entities,
                'success': True
            }
            
            # Show results with geriatric-specific analysis
            print(f"    ✅ {processing_time:.1f}ms | {total_entities} entities | {tier_used} tier | quality: {quality_score:.2f}")
            
            # Show extracted entities by category
            for category, entity_list in entities.items():
                if entity_list:
                    entity_texts = [e.get('text', '') for e in entity_list]
                    print(f"       {category}: {entity_texts}")
            
            # Geriatric-specific analysis
            note_lower = note.lower()
            if any(condition in note_lower for condition in ['alzheimer', 'dementia']):
                print(f"       🧠 Neurocognitive disorder detected")
            if any(med in note_lower for med in ['warfarin', 'rivaroxaban', 'clopidogrel']):
                print(f"       🩸 Anticoagulation therapy detected")
            if 'fall risk' in note_lower or 'orthostatic' in note_lower:
                print(f"       ⚠️  Fall risk factors identified")
                
        except Exception as e:
            processing_time = (time.time() - note_start) * 1000
            result = {
                'note_number': i,
                'clinical_text': note,
                'processing_time_ms': processing_time,
                'error': str(e),
                'success': False
            }
            print(f"    ❌ Error: {str(e)}")
        
        results.append(result)
        print()  # Empty line between notes
    
    # Calculate comprehensive statistics
    total_time = (time.time() - start_time) * 1000
    successful = [r for r in results if r.get('success', False)]
    
    if successful:
        avg_time = sum(r['processing_time_ms'] for r in successful) / len(successful)
        avg_entities = sum(r['entities_found'] for r in successful) / len(successful)
        avg_quality = sum(r['quality_score'] for r in successful) / len(successful)
        
        # Tier usage analysis
        tier_counts = {}
        for r in successful:
            tier = r.get('tier_used', 'unknown')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
    else:
        avg_time = avg_entities = avg_quality = 0
        tier_counts = {}
    
    # Print comprehensive results with pediatric comparison
    print("👵 Geriatric Clinical Notes - Analysis Complete!")
    print("="*58)
    
    print(f"📊 Processing Results:")
    print(f"   ✅ Success rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"   ⏱️  Average processing time: {avg_time:.1f}ms")
    print(f"   📈 Average entities per note: {avg_entities:.1f}")
    print(f"   🎯 Average quality score: {avg_quality:.2f}")
    print(f"   🚀 Total batch time: {total_time:.1f}ms")
    print(f"   📊 Throughput: {len(results)/(total_time/1000):.1f} notes/second")
    
    print(f"\n🏗️  3-Tier Architecture Performance:")
    for tier, count in tier_counts.items():
        percentage = count / len(successful) * 100 if successful else 0
        efficiency = "🟢 Excellent" if tier == "spacy" else "🟡 Good" if tier == "transformers" else "🔴 Expensive"
        print(f"   {tier.title()} Tier: {count} notes ({percentage:.1f}%) {efficiency}")
    
    print(f"\n💊 Geriatric Medication Analysis:")
    print(f"   Total unique medications: {len(all_medications)}")
    print(f"   Complex geriatric drugs found: {len(set(complex_medications))}")
    print(f"   Medications detected: {list(sorted(all_medications))[:10]}")
    if complex_medications:
        print(f"   High-risk geriatric meds: {list(set(complex_medications))}")
    
    print(f"\n🏥 Geriatric Condition Recognition:")
    print(f"   Total conditions found: {len(all_conditions)}")
    print(f"   Geriatric-specific conditions: {len(geriatric_conditions)}")
    print(f"   Conditions: {list(sorted(all_conditions))}")
    
    # Specialty comparison (if pediatric results exist)
    try:
        with open('clinical_results/pediatric_batch_results.json', 'r') as f:
            pediatric_data = json.load(f)
            
        print(f"\n👶👵 Pediatric vs Geriatric Comparison:")
        print(f"   Processing Time: Pediatric {pediatric_data['avg_processing_time_ms']:.1f}ms vs Geriatric {avg_time:.1f}ms")
        print(f"   Quality Score: Pediatric {pediatric_data['avg_quality_score']:.2f} vs Geriatric {avg_quality:.2f}")
        print(f"   Entities/Note: Pediatric {len(pediatric_data['unique_medications'])} vs Geriatric {len(all_medications)} meds")
        
        # Performance difference
        time_diff = ((avg_time - pediatric_data['avg_processing_time_ms']) / pediatric_data['avg_processing_time_ms']) * 100
        quality_diff = avg_quality - pediatric_data['avg_quality_score']
        
        print(f"   Performance: {time_diff:+.1f}% time, {quality_diff:+.2f} quality difference")
        
    except FileNotFoundError:
        print(f"\n📊 No pediatric results found for comparison")
    
    # Performance assessment with specialty context
    print(f"\n🎯 Geriatric Specialty Assessment:")
    if avg_quality >= 0.8:
        print(f"   ✅ HIGH QUALITY: Excellent geriatric entity extraction ({avg_quality:.2f})")
    elif avg_quality >= 0.6:
        print(f"   🟡 GOOD QUALITY: Solid geriatric performance ({avg_quality:.2f})")
    else:
        print(f"   🔴 NEEDS IMPROVEMENT: Low geriatric extraction ({avg_quality:.2f})")
    
    # Geriatric-specific recommendations
    print(f"\n💡 Geriatric-Specific Recommendations:")
    
    missing_geriatric_meds = set(['donepezil', 'hydrochlorothiazide', 'rosuvastatin', 'digoxin', 
                                 'rivaroxaban', 'lorazepam', 'clopidogrel', 'memantine', 
                                 'tamsulosin', 'pantoprazole', 'fentanyl']) - set(complex_medications)
    
    if missing_geriatric_meds:
        print(f"   1. 💊 Add missing geriatric medications to spaCy vocabulary:")
        print(f"      {list(missing_geriatric_meds)}")
    
    spacy_percentage = tier_counts.get('spacy', 0) / len(successful) * 100 if successful else 0
    if spacy_percentage < 60:
        print(f"   2. 🏗️ Optimize for geriatric medication patterns")
        print(f"   3. 🧠 Add cognitive disorder recognition (Alzheimer's, dementia)")
        print(f"   4. 💓 Enhance cardiovascular condition detection")
        
    print(f"   5. ⚠️ Implement fall risk and drug interaction warnings")
    print(f"   6. 🩸 Add anticoagulation therapy pattern recognition")
    print(f"   7. 👴 Develop geriatric polypharmacy detection")
    
    # Save results
    results_dir = Path("clinical_results")
    results_dir.mkdir(exist_ok=True)
    
    batch_data = {
        'batch_name': 'geriatric_encounter_notes',
        'timestamp': time.time(),
        'specialty': 'geriatrics',
        'total_notes': len(GERIATRIC_CLINICAL_NOTES),
        'successful_notes': len(successful),
        'avg_processing_time_ms': float(avg_time),
        'avg_quality_score': float(avg_quality),
        'tier_usage': tier_counts,
        'unique_medications': list(sorted(all_medications)),
        'unique_conditions': list(sorted(all_conditions)),
        'geriatric_conditions': list(sorted(geriatric_conditions)),
        'complex_medications': list(set(complex_medications)),
        'results': results
    }
    
    batch_file = results_dir / "geriatric_batch_results.json"
    with open(batch_file, 'w') as f:
        json.dump(batch_data, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {batch_file}")
    
    return batch_data

def extract_patient_name(note):
    """Extract patient name from clinical note"""
    import re
    # Look for "patient [Name Name]" pattern
    match = re.search(r'patient\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', note)
    return match.group(1) if match else "Unknown"

if __name__ == "__main__":
    print("👵 Multi-Specialty Test - Geriatric Encounter Notes")
    print("Testing 3-tier medical NLP across different medical specialties")
    print("="*70)
    
    asyncio.run(process_geriatric_batch())