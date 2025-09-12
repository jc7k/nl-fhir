#!/usr/bin/env python3
"""
Test Psychiatry Clinical Notes - Multi-Specialty Validation
Process 20 psychiatry encounter notes and compare with pediatric and geriatric results
"""

import sys
sys.path.append('../../src')

import asyncio
import json
import time
from pathlib import Path
from nl_fhir.services.nlp.models import model_manager

# The 20 psychiatry clinical notes you provided
PSYCHIATRY_CLINICAL_NOTES = [
    "Started patient Alex Morgan on 20mg Fluoxetine once daily for major depressive disorder; follow-up in 4 weeks.",
    "Prescribed patient Rachel Kim 5mg Aripiprazole once daily for bipolar disorder stabilization.",
    "Initiated patient Jordan Lee on 0.5mg Clonazepam twice daily for panic disorder; discussed dependency risks.",
    "Started patient Taylor Brooks on 150mg Venlafaxine XR once daily for generalized anxiety disorder.",
    "Prescribed patient Casey Nguyen 300mg Lithium carbonate twice daily for mood stabilization; ordered lithium level.",
    "Started patient Jamie Foster on 10mg Buspirone three times daily for anxiety; advised on delayed onset.",
    "Initiated patient Morgan Davis on 20mg Paroxetine once daily for PTSD; discussed sexual side effects.",
    "Prescribed patient Drew Thompson 2mg Risperidone nightly for schizophrenia; monitored for extrapyramidal symptoms.",
    "Started patient Sydney Clark on 36mg Concerta once daily for ADHD; advised on appetite suppression.",
    "Initiated patient Avery Martinez on 100mg Lamotrigine once daily for bipolar depression; titration schedule provided.",
    "Prescribed patient Riley Adams 25mg Quetiapine at bedtime for insomnia and mood stabilization.",
    "Started patient Peyton Bell on 10mg Olanzapine once daily for psychosis; monitored weight gain.",
    "Initiated patient Cameron Reed on 50mg Sertraline once daily for OCD; discussed behavioral therapy adjunct.",
    "Prescribed patient Skylar Bennett 5mg Haloperidol IM every 4 hours as needed for acute agitation.",
    "Started patient Dakota Simmons on 20mg Citalopram once daily for postpartum depression.",
    "Initiated patient Reese Young on 200mg Carbamazepine twice daily for schizoaffective disorder; monitored CBC.",
    "Prescribed patient Quinn Hayes 0.5mg Alprazolam three times daily for acute anxiety; short-term use only.",
    "Started patient Finley Rivera on 10mg Lurasidone once daily for bipolar depression; advised with food intake.",
    "Initiated patient Kendall Morris on 25mg Nortriptyline nightly for chronic pain and depression.",
    "Prescribed patient Rowan Parker 5mg Diazepam orally every 6 hours as needed for alcohol withdrawal symptoms."
]

async def process_psychiatry_batch():
    """Process psychiatry clinical notes and compare with pediatric and geriatric performance"""
    
    print("🧠 Processing Psychiatry Clinical Notes - Multi-Specialty Test")
    print("="*70)
    print(f"📝 Processing {len(PSYCHIATRY_CLINICAL_NOTES)} psychiatry encounter notes...")
    print("Comparing performance with pediatric and geriatric results from previous batches\n")
    
    results = []
    start_time = time.time()
    
    # Track psychiatry-specific metrics
    all_medications = set()
    all_conditions = set()
    psychiatric_conditions = set()
    complex_psychiatric_meds = []
    
    for i, note in enumerate(PSYCHIATRY_CLINICAL_NOTES, 1):
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
                
                # Track complex psychiatric medications
                if med_text in ['fluoxetine', 'aripiprazole', 'clonazepam', 'venlafaxine', 
                               'lithium', 'buspirone', 'paroxetine', 'risperidone',
                               'concerta', 'lamotrigine', 'quetiapine', 'olanzapine',
                               'sertraline', 'haloperidol', 'citalopram', 'carbamazepine',
                               'alprazolam', 'lurasidone', 'nortriptyline', 'diazepam']:
                    complex_psychiatric_meds.append(med_text)
            
            for condition in entities.get('conditions', []):
                condition_text = condition.get('text', '').lower()
                all_conditions.add(condition_text)
                
                # Track psychiatric-specific conditions
                if any(psych_term in condition_text for psych_term in [
                    'depression', 'depressive', 'bipolar', 'panic', 'anxiety', 
                    'ptsd', 'schizophrenia', 'adhd', 'psychosis', 'ocd',
                    'schizoaffective', 'withdrawal', 'mood', 'insomnia'
                ]):
                    psychiatric_conditions.add(condition_text)
            
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
            
            # Show results with psychiatry-specific analysis
            print(f"    ✅ {processing_time:.1f}ms | {total_entities} entities | {tier_used} tier | quality: {quality_score:.2f}")
            
            # Show extracted entities by category
            for category, entity_list in entities.items():
                if entity_list:
                    entity_texts = [e.get('text', '') for e in entity_list]
                    print(f"       {category}: {entity_texts}")
            
            # Psychiatry-specific analysis
            note_lower = note.lower()
            if any(condition in note_lower for condition in ['depression', 'depressive', 'bipolar']):
                print(f"       🧠 Mood disorder detected")
            if any(med in note_lower for med in ['clonazepam', 'alprazolam', 'diazepam']):
                print(f"       ⚠️  Controlled substance (benzodiazepine) detected")
            if any(term in note_lower for term in ['dependency', 'withdrawal', 'addiction']):
                print(f"       🚨 Substance use concern identified")
            if any(term in note_lower for term in ['extrapyramidal', 'weight gain', 'sexual side effects']):
                print(f"       💊 Side effect monitoring noted")
                
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
    
    # Print comprehensive results with multi-specialty comparison
    print("🧠 Psychiatry Clinical Notes - Analysis Complete!")
    print("="*60)
    
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
    
    print(f"\n💊 Psychiatric Medication Analysis:")
    print(f"   Total unique medications: {len(all_medications)}")
    print(f"   Complex psychiatric drugs found: {len(set(complex_psychiatric_meds))}")
    print(f"   Medications detected: {list(sorted(all_medications))[:10]}")
    if complex_psychiatric_meds:
        print(f"   Psychiatric medications: {list(set(complex_psychiatric_meds))}")
    
    print(f"\n🧠 Psychiatric Condition Recognition:")
    print(f"   Total conditions found: {len(all_conditions)}")
    print(f"   Psychiatric-specific conditions: {len(psychiatric_conditions)}")
    print(f"   Conditions: {list(sorted(all_conditions))}")
    
    # Multi-specialty comparison (if previous results exist)
    try:
        # Load pediatric results
        with open('clinical_results/pediatric_batch_results.json', 'r') as f:
            pediatric_data = json.load(f)
        
        # Load geriatric results
        with open('clinical_results/geriatric_batch_results.json', 'r') as f:
            geriatric_data = json.load(f)
            
        print(f"\n👶👴🧠 Multi-Specialty Performance Comparison:")
        print(f"   Processing Time:")
        print(f"      Pediatric: {pediatric_data['avg_processing_time_ms']:.1f}ms")
        print(f"      Geriatric: {geriatric_data['avg_processing_time_ms']:.1f}ms") 
        print(f"      Psychiatry: {avg_time:.1f}ms")
        
        print(f"   Quality Score:")
        print(f"      Pediatric: {pediatric_data['avg_quality_score']:.2f}")
        print(f"      Geriatric: {geriatric_data['avg_quality_score']:.2f}")
        print(f"      Psychiatry: {avg_quality:.2f}")
        
        print(f"   Unique Medications:")
        print(f"      Pediatric: {len(pediatric_data['unique_medications'])} medications")
        print(f"      Geriatric: {len(geriatric_data['unique_medications'])} medications")
        print(f"      Psychiatry: {len(all_medications)} medications")
        
        # Best performer analysis
        times = [pediatric_data['avg_processing_time_ms'], geriatric_data['avg_processing_time_ms'], avg_time]
        qualities = [pediatric_data['avg_quality_score'], geriatric_data['avg_quality_score'], avg_quality]
        
        fastest_specialty = ['Pediatric', 'Geriatric', 'Psychiatry'][times.index(min(times))]
        highest_quality = ['Pediatric', 'Geriatric', 'Psychiatry'][qualities.index(max(qualities))]
        
        print(f"\n🏆 Multi-Specialty Performance Leaders:")
        print(f"   Fastest Processing: {fastest_specialty} ({min(times):.1f}ms)")
        print(f"   Highest Quality: {highest_quality} ({max(qualities):.2f})")
        
    except FileNotFoundError:
        print(f"\n📊 Previous specialty results not found for comparison")
    
    # Performance assessment with specialty context
    print(f"\n🎯 Psychiatry Specialty Assessment:")
    if avg_quality >= 0.8:
        print(f"   ✅ HIGH QUALITY: Excellent psychiatric entity extraction ({avg_quality:.2f})")
    elif avg_quality >= 0.6:
        print(f"   🟡 GOOD QUALITY: Solid psychiatric performance ({avg_quality:.2f})")
    else:
        print(f"   🔴 NEEDS IMPROVEMENT: Low psychiatric extraction ({avg_quality:.2f})")
    
    # Psychiatry-specific recommendations
    print(f"\n💡 Psychiatry-Specific Recommendations:")
    
    missing_psychiatric_meds = set(['fluoxetine', 'aripiprazole', 'clonazepam', 'venlafaxine',
                                   'lithium', 'buspirone', 'paroxetine', 'risperidone',
                                   'concerta', 'lamotrigine', 'quetiapine', 'olanzapine',
                                   'sertraline', 'haloperidol', 'citalopram', 'carbamazepine',
                                   'alprazolam', 'lurasidone', 'nortriptyline', 'diazepam']) - set(complex_psychiatric_meds)
    
    if missing_psychiatric_meds:
        print(f"   1. 💊 Add missing psychiatric medications to spaCy vocabulary:")
        print(f"      {list(missing_psychiatric_meds)}")
    
    spacy_percentage = tier_counts.get('spacy', 0) / len(successful) * 100 if successful else 0
    if spacy_percentage < 60:
        print(f"   2. 🏗️ Optimize for psychiatric medication patterns")
        print(f"   3. 🧠 Add psychiatric condition recognition (depression, bipolar, ADHD)")
        print(f"   4. 💊 Enhance psychopharmacology detection")
        
    print(f"   5. ⚠️ Implement controlled substance monitoring (benzodiazepines)")
    print(f"   6. 🚨 Add substance use disorder pattern recognition")
    print(f"   7. 💊 Develop psychiatric side effect monitoring")
    print(f"   8. 🧠 Add mood disorder classification")
    
    # Save results
    results_dir = Path("clinical_results")
    results_dir.mkdir(exist_ok=True)
    
    batch_data = {
        'batch_name': 'psychiatry_encounter_notes',
        'timestamp': time.time(),
        'specialty': 'psychiatry',
        'total_notes': len(PSYCHIATRY_CLINICAL_NOTES),
        'successful_notes': len(successful),
        'avg_processing_time_ms': float(avg_time),
        'avg_quality_score': float(avg_quality),
        'tier_usage': tier_counts,
        'unique_medications': list(sorted(all_medications)),
        'unique_conditions': list(sorted(all_conditions)),
        'psychiatric_conditions': list(sorted(psychiatric_conditions)),
        'complex_medications': list(set(complex_psychiatric_meds)),
        'results': results
    }
    
    batch_file = results_dir / "psychiatry_batch_results.json"
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
    print("🧠 Multi-Specialty Test - Psychiatry Encounter Notes")
    print("Testing 3-tier medical NLP across different medical specialties")
    print("="*70)
    
    asyncio.run(process_psychiatry_batch())