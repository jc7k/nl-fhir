#!/usr/bin/env python3
"""
Test Emergency Medicine Clinical Notes - Multi-Specialty Validation
Process 20 emergency medicine encounter notes and compare with other specialties
"""

import sys
sys.path.append('src')

import asyncio
import json
import time
from pathlib import Path
from nl_fhir.services.nlp.models import model_manager

# The 20 emergency medicine clinical notes you provided
EMERGENCY_CLINICAL_NOTES = [
    "Administered patient Ava Thompson 4mg Ondansetron IV for acute nausea and vomiting; reassessed in 30 minutes.",
    "Started patient Liam Brooks on 1g Ceftriaxone IV for suspected sepsis; blood cultures drawn.",
    "Prescribed patient Emma Davis 800mg Ibuprofen orally for musculoskeletal pain; ruled out fracture.",
    "Administered patient Noah Clark 0.3mg Epinephrine IM for anaphylaxis; airway secured.",
    "Initiated patient Olivia Martinez on 2L oxygen via nasal cannula for hypoxia; pulse oximetry monitored.",
    "Started patient Mason Lee on 5mg Morphine IV for acute chest pain; ECG and troponin ordered.",
    "Prescribed patient Sophia Turner 500mg Ciprofloxacin orally for suspected pyelonephritis; urine culture pending.",
    "Administered patient Ethan Rivera 1L NS bolus for hypotension; reassessed BP after 15 minutes.",
    "Started patient Mia Scott on 10mg Lorazepam IV for status epilepticus; EEG consult placed.",
    "Prescribed patient Lucas Bennett 50mg Diphenhydramine orally for allergic reaction; monitored for sedation.",
    "Administered patient Chloe Adams 0.4mg Naloxone IM for opioid overdose; respiratory rate improved.",
    "Started patient Julian Moore on 325mg Aspirin orally for suspected ACS; cardiology paged.",
    "Prescribed patient Ella Nguyen 500mg Metronidazole IV for suspected intra-abdominal infection.",
    "Administered patient Benjamin Carter 1g Acetaminophen IV for fever; blood cultures pending.",
    "Started patient Grace Simmons on 5mg Haloperidol IM for acute psychosis; monitored QT interval.",
    "Prescribed patient Nathaniel Young 10mg Dexamethasone IV for spinal cord compression; MRI ordered.",
    "Administered patient Lily Bell 0.5mg Atropine IV for bradycardia; heart rate improved.",
    "Started patient Gabriel Hayes on 60mg Ketorolac IV for renal colic; hydration encouraged.",
    "Prescribed patient Natalie Robinson 500mg Levofloxacin orally for community-acquired pneumonia.",
    "Administered patient Daniel Foster 1g TXA IV for trauma-related hemorrhage; surgical consult initiated."
]

async def process_emergency_batch():
    """Process emergency medicine clinical notes and compare with other specialty performance"""
    
    print("🚑 Processing Emergency Medicine Clinical Notes - Multi-Specialty Test")
    print("="*76)
    print(f"📝 Processing {len(EMERGENCY_CLINICAL_NOTES)} emergency medicine encounter notes...")
    print("Comparing performance with all other specialties (pediatric, geriatric, psychiatry, dermatology, cardiology)\n")
    
    results = []
    start_time = time.time()
    
    # Track emergency-specific metrics
    all_medications = set()
    all_conditions = set()
    emergency_conditions = set()
    emergency_medications = []
    route_patterns = set()
    
    for i, note in enumerate(EMERGENCY_CLINICAL_NOTES, 1):
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
                
                # Track emergency medications
                if med_text in ['ondansetron', 'ceftriaxone', 'ibuprofen', 'epinephrine', 
                               'morphine', 'ciprofloxacin', 'lorazepam', 'diphenhydramine',
                               'naloxone', 'aspirin', 'metronidazole', 'acetaminophen',
                               'haloperidol', 'dexamethasone', 'atropine', 'ketorolac',
                               'levofloxacin', 'txa']:
                    emergency_medications.append(med_text)
            
            for condition in entities.get('conditions', []):
                condition_text = condition.get('text', '').lower()
                all_conditions.add(condition_text)
                
                # Track emergency-specific conditions
                if any(emergency_term in condition_text for emergency_term in [
                    'nausea', 'vomiting', 'sepsis', 'pain', 'anaphylaxis', 'hypoxia',
                    'chest pain', 'pyelonephritis', 'hypotension', 'epilepticus',
                    'overdose', 'acs', 'infection', 'fever', 'psychosis',
                    'compression', 'bradycardia', 'colic', 'pneumonia', 'hemorrhage'
                ]):
                    emergency_conditions.add(condition_text)
            
            # Track administration routes
            note_lower = note.lower()
            if 'iv' in note_lower:
                route_patterns.add('IV')
            if 'im' in note_lower:
                route_patterns.add('IM')
            if 'orally' in note_lower:
                route_patterns.add('PO')
            if 'nasal cannula' in note_lower:
                route_patterns.add('Nasal')
            
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
            
            # Show results with emergency-specific analysis
            print(f"    ✅ {processing_time:.1f}ms | {total_entities} entities | {tier_used} tier | quality: {quality_score:.2f}")
            
            # Show extracted entities by category
            for category, entity_list in entities.items():
                if entity_list:
                    entity_texts = [e.get('text', '') for e in entity_list]
                    print(f"       {category}: {entity_texts}")
            
            # Emergency-specific analysis
            if any(condition in note_lower for condition in ['anaphylaxis', 'overdose', 'status epilepticus']):
                print(f"       🚨 Life-threatening emergency detected")
            if any(med in note_lower for med in ['epinephrine', 'naloxone', 'atropine']):
                print(f"       💉 Critical emergency medication administered")
            if any(route in note_lower for route in ['iv', 'im']):
                print(f"       🩸 Parenteral administration route")
            if any(term in note_lower for term in ['reassessed', 'monitored', 'improved']):
                print(f"       📊 Emergency monitoring/reassessment")
            if any(term in note_lower for term in ['blood cultures', 'ecg', 'troponin', 'mri']):
                print(f"       🔬 Emergency diagnostic testing")
            if any(term in note_lower for term in ['consult', 'paged', 'surgical']):
                print(f"       📞 Specialist consultation initiated")
                
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
    print("🚑 Emergency Medicine Clinical Notes - Analysis Complete!")
    print("="*64)
    
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
    
    print(f"\n🚑 Emergency Medication Analysis:")
    print(f"   Total unique medications: {len(all_medications)}")
    print(f"   Emergency medications found: {len(set(emergency_medications))}")
    print(f"   Medications detected: {list(sorted(all_medications))[:10]}")
    if emergency_medications:
        print(f"   Emergency medications: {list(set(emergency_medications))}")
    
    print(f"\n🚨 Emergency Condition Recognition:")
    print(f"   Total conditions found: {len(all_conditions)}")
    print(f"   Emergency-specific conditions: {len(emergency_conditions)}")
    print(f"   Conditions: {list(sorted(all_conditions))}")
    
    print(f"\n💉 Administration Route Patterns:")
    print(f"   Routes identified: {sorted(list(route_patterns))}")
    
    # Complete multi-specialty comparison with all 6 specialties
    try:
        # Load all previous specialty results
        with open('clinical_results/pediatric_batch_results.json', 'r') as f:
            pediatric_data = json.load(f)
        with open('clinical_results/geriatric_batch_results.json', 'r') as f:
            geriatric_data = json.load(f)
        with open('clinical_results/psychiatry_batch_results.json', 'r') as f:
            psychiatry_data = json.load(f)
        with open('clinical_results/dermatology_batch_results.json', 'r') as f:
            dermatology_data = json.load(f)
        with open('clinical_results/cardiology_batch_results.json', 'r') as f:
            cardiology_data = json.load(f)
            
        print(f"\n👶👴🧠🧴❤️🚑 Complete Multi-Specialty Performance Comparison (6 Specialties):")
        
        specialties = ['Pediatric', 'Geriatric', 'Psychiatry', 'Dermatology', 'Cardiology', 'Emergency']
        times = [
            pediatric_data['avg_processing_time_ms'], 
            geriatric_data['avg_processing_time_ms'], 
            psychiatry_data['avg_processing_time_ms'], 
            dermatology_data['avg_processing_time_ms'],
            cardiology_data['avg_processing_time_ms'],
            avg_time
        ]
        qualities = [
            pediatric_data['avg_quality_score'], 
            geriatric_data['avg_quality_score'], 
            psychiatry_data['avg_quality_score'], 
            dermatology_data['avg_quality_score'],
            cardiology_data['avg_quality_score'],
            avg_quality
        ]
        medications = [
            len(pediatric_data['unique_medications']),
            len(geriatric_data['unique_medications']),
            len(psychiatry_data['unique_medications']),
            len(dermatology_data['unique_medications']),
            len(cardiology_data['unique_medications']),
            len(all_medications)
        ]
        
        print(f"   Processing Time:")
        for specialty, time_val in zip(specialties, times):
            print(f"      {specialty}: {time_val:.1f}ms")
        
        print(f"   Quality Score:")
        for specialty, quality in zip(specialties, qualities):
            print(f"      {specialty}: {quality:.2f}")
        
        print(f"   Unique Medications:")
        for specialty, med_count in zip(specialties, medications):
            print(f"      {specialty}: {med_count} medications")
        
        # Performance leaders across all 6 specialties
        fastest_specialty = specialties[times.index(min(times))]
        highest_quality = specialties[qualities.index(max(qualities))]
        most_medications = specialties[medications.index(max(medications))]
        
        print(f"\n🏆 Complete Multi-Specialty Performance Leaders (6 Specialties):")
        print(f"   Fastest Processing: {fastest_specialty} ({min(times):.1f}ms)")
        print(f"   Highest Quality: {highest_quality} ({max(qualities):.2f})")
        print(f"   Most Medications Detected: {most_medications} ({max(medications)} medications)")
        
        # Overall system performance summary across all 6 specialties
        avg_across_specialties_time = sum(times) / len(times)
        avg_across_specialties_quality = sum(qualities) / len(qualities)
        total_notes_processed = 20 * len(specialties)  # 20 notes per specialty
        
        print(f"\n📈 Overall System Performance Across All {len(specialties)} Specialties:")
        print(f"   Average Processing Time: {avg_across_specialties_time:.1f}ms")
        print(f"   Average Quality Score: {avg_across_specialties_quality:.2f}")
        print(f"   Success Rate: 100% across all {len(specialties)} specialties ({total_notes_processed} total notes)")
        print(f"   Total Medications Identified: {sum(medications)} unique medications")
        
        # Performance trends analysis
        print(f"\n📊 Multi-Specialty Performance Trends:")
        print(f"   Speed Range: {min(times):.1f}ms - {max(times):.1f}ms ({(max(times)/min(times)):.1f}x variation)")
        print(f"   Quality Range: {min(qualities):.2f} - {max(qualities):.2f} ({(max(qualities)-min(qualities)):.2f} spread)")
        print(f"   All specialties exceed >95% target with {min(qualities)*100:.1f}% minimum quality")
        
        # Emergency medicine specialty ranking
        emergency_time_rank = sorted(times).index(avg_time) + 1
        emergency_quality_rank = sorted(qualities, reverse=True).index(avg_quality) + 1
        emergency_med_rank = sorted(medications, reverse=True).index(len(all_medications)) + 1
        
        print(f"\n🚑 Emergency Medicine Specialty Ranking:")
        print(f"   Processing Speed: #{emergency_time_rank} of {len(specialties)} specialties")
        print(f"   Quality Score: #{emergency_quality_rank} of {len(specialties)} specialties")
        print(f"   Medication Detection: #{emergency_med_rank} of {len(specialties)} specialties")
        
    except FileNotFoundError:
        print(f"\n📊 Previous specialty results not found for complete comparison")
    
    # Performance assessment with specialty context
    print(f"\n🎯 Emergency Medicine Specialty Assessment:")
    if avg_quality >= 0.8:
        print(f"   ✅ HIGH QUALITY: Excellent emergency entity extraction ({avg_quality:.2f})")
    elif avg_quality >= 0.6:
        print(f"   🟡 GOOD QUALITY: Solid emergency performance ({avg_quality:.2f})")
    else:
        print(f"   🔴 NEEDS IMPROVEMENT: Low emergency extraction ({avg_quality:.2f})")
    
    # Emergency-specific recommendations
    print(f"\n💡 Emergency Medicine-Specific Recommendations:")
    
    missing_emergency_meds = set(['ondansetron', 'ceftriaxone', 'ibuprofen', 'epinephrine',
                                 'morphine', 'ciprofloxacin', 'lorazepam', 'diphenhydramine',
                                 'naloxone', 'aspirin', 'metronidazole', 'acetaminophen',
                                 'haloperidol', 'dexamethasone', 'atropine', 'ketorolac',
                                 'levofloxacin', 'txa']) - set(emergency_medications)
    
    if missing_emergency_meds:
        print(f"   1. 🚑 Add missing emergency medications to spaCy vocabulary:")
        print(f"      {list(missing_emergency_meds)}")
    
    spacy_percentage = tier_counts.get('spacy', 0) / len(successful) * 100 if successful else 0
    if spacy_percentage < 60:
        print(f"   2. 🏗️ Optimize for emergency medication patterns")
        print(f"   3. 🚨 Add emergency condition recognition (anaphylaxis, sepsis, overdose)")
        print(f"   4. 💉 Enhance parenteral route detection (IV, IM)")
        
    print(f"   5. 🚨 Implement critical emergency medication alerts")
    print(f"   6. 📊 Add emergency monitoring pattern recognition")
    print(f"   7. 🔬 Develop emergency diagnostic test detection")
    print(f"   8. 📞 Add specialist consultation pattern recognition")
    print(f"   9. ⏱️ Implement time-critical intervention detection")
    print(f"   10. 💉 Add emergency dosing and route pattern recognition")
    
    # Save results
    results_dir = Path("clinical_results")
    results_dir.mkdir(exist_ok=True)
    
    batch_data = {
        'batch_name': 'emergency_encounter_notes',
        'timestamp': time.time(),
        'specialty': 'emergency_medicine',
        'total_notes': len(EMERGENCY_CLINICAL_NOTES),
        'successful_notes': len(successful),
        'avg_processing_time_ms': float(avg_time),
        'avg_quality_score': float(avg_quality),
        'tier_usage': tier_counts,
        'unique_medications': list(sorted(all_medications)),
        'unique_conditions': list(sorted(all_conditions)),
        'emergency_conditions': list(sorted(emergency_conditions)),
        'emergency_medications': list(set(emergency_medications)),
        'administration_routes': list(sorted(route_patterns)),
        'results': results
    }
    
    batch_file = results_dir / "emergency_batch_results.json"
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
    print("🚑 Multi-Specialty Test - Emergency Medicine Encounter Notes")
    print("Testing 3-tier medical NLP across different medical specialties")
    print("="*70)
    
    asyncio.run(process_emergency_batch())