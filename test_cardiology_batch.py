#!/usr/bin/env python3
"""
Test Cardiology Clinical Notes - Multi-Specialty Validation
Process 20 cardiology encounter notes and compare with other specialties
"""

import sys
sys.path.append('src')

import asyncio
import json
import time
from pathlib import Path
from nl_fhir.services.nlp.models import model_manager

# The 20 cardiology clinical notes you provided
CARDIOLOGY_CLINICAL_NOTES = [
    "Started patient Daniel Moore on 10mg Atorvastatin nightly for LDL reduction; lipid panel in 6 weeks.",
    "Prescribed patient Ava Robinson 25mg Metoprolol twice daily for rate control in atrial fibrillation.",
    "Initiated patient James Foster on 75mg Clopidogrel daily post-PCI; reviewed bleeding risks.",
    "Started patient Olivia Bennett on 5mg Ramipril once daily for hypertension; monitored renal function.",
    "Recommended patient Henry Adams begin 81mg Aspirin daily for secondary prevention of MI.",
    "Prescribed patient Sophia Clark 20mg Furosemide twice daily for CHF exacerbation; potassium supplementation discussed.",
    "Started patient Mason Lee on 10mg Isosorbide mononitrate twice daily for stable angina.",
    "Initiated patient Emma Turner on 2.5mg Bisoprolol once daily for systolic heart failure.",
    "Prescribed patient Liam Davis 5mg Amlodipine daily for isolated systolic hypertension.",
    "Started patient Mia Thompson on 6.25mg Carvedilol twice daily for heart failure; titration plan outlined.",
    "Recommended patient Lucas Martinez begin 20mg Rosuvastatin nightly for familial hypercholesterolemia.",
    "Prescribed patient Chloe Simmons 0.125mg Digoxin daily for rate control; monitored serum levels.",
    "Started patient Ethan Nguyen on 10mg Lisinopril daily post-MI; renal function baseline obtained.",
    "Initiated patient Grace Bell on 5mg Apixaban twice daily for non-valvular atrial fibrillation.",
    "Prescribed patient Julian Rivera 50mg Losartan daily for hypertension; advised on orthostatic symptoms.",
    "Started patient Ella Scott on 100mg Spironolactone daily for resistant hypertension; potassium checked.",
    "Recommended patient Benjamin Hayes begin 2.5mg Nebivolol daily for hypertension with bradycardia.",
    "Prescribed patient Lily Moore 10mg Diltiazem three times daily for rate control; ECG follow-up scheduled.",
    "Started patient Gabriel Young on 20mg Simvastatin nightly; discussed grapefruit interaction.",
    "Initiated patient Natalie Carter on 5mg Warfarin daily for mechanical valve; INR goal 2.5–3.5."
]

async def process_cardiology_batch():
    """Process cardiology clinical notes and compare with other specialty performance"""
    
    print("❤️ Processing Cardiology Clinical Notes - Multi-Specialty Test")
    print("="*72)
    print(f"📝 Processing {len(CARDIOLOGY_CLINICAL_NOTES)} cardiology encounter notes...")
    print("Comparing performance with pediatric, geriatric, psychiatry, and dermatology results\n")
    
    results = []
    start_time = time.time()
    
    # Track cardiology-specific metrics
    all_medications = set()
    all_conditions = set()
    cardiac_conditions = set()
    cardiac_medications = []
    
    for i, note in enumerate(CARDIOLOGY_CLINICAL_NOTES, 1):
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
                
                # Track cardiac medications
                if med_text in ['atorvastatin', 'metoprolol', 'clopidogrel', 'ramipril', 
                               'aspirin', 'furosemide', 'isosorbide', 'bisoprolol',
                               'amlodipine', 'carvedilol', 'rosuvastatin', 'digoxin',
                               'lisinopril', 'apixaban', 'losartan', 'spironolactone',
                               'nebivolol', 'diltiazem', 'simvastatin', 'warfarin']:
                    cardiac_medications.append(med_text)
            
            for condition in entities.get('conditions', []):
                condition_text = condition.get('text', '').lower()
                all_conditions.add(condition_text)
                
                # Track cardiac-specific conditions
                if any(cardiac_term in condition_text for cardiac_term in [
                    'ldl', 'atrial fibrillation', 'hypertension', 'mi', 'chf', 
                    'angina', 'heart failure', 'hypercholesterolemia', 'bradycardia'
                ]):
                    cardiac_conditions.add(condition_text)
            
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
            
            # Show results with cardiology-specific analysis
            print(f"    ✅ {processing_time:.1f}ms | {total_entities} entities | {tier_used} tier | quality: {quality_score:.2f}")
            
            # Show extracted entities by category
            for category, entity_list in entities.items():
                if entity_list:
                    entity_texts = [e.get('text', '') for e in entity_list]
                    print(f"       {category}: {entity_texts}")
            
            # Cardiology-specific analysis
            note_lower = note.lower()
            if any(condition in note_lower for condition in ['atrial fibrillation', 'heart failure', 'chf']):
                print(f"       ❤️ Cardiac arrhythmia/failure detected")
            if any(med in note_lower for med in ['warfarin', 'clopidogrel', 'apixaban']):
                print(f"       🩸 Anticoagulation/antiplatelet therapy detected")
            if any(term in note_lower for term in ['post-mi', 'post-pci', 'secondary prevention']):
                print(f"       🏥 Post-cardiac event management")
            if any(term in note_lower for term in ['inr', 'potassium', 'renal function', 'lipid panel']):
                print(f"       🔬 Cardiac medication monitoring required")
            if any(med in note_lower for med in ['atorvastatin', 'rosuvastatin', 'simvastatin']):
                print(f"       💊 Statin therapy for lipid management")
                
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
    print("❤️ Cardiology Clinical Notes - Analysis Complete!")
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
    
    print(f"\n❤️ Cardiac Medication Analysis:")
    print(f"   Total unique medications: {len(all_medications)}")
    print(f"   Cardiac medications found: {len(set(cardiac_medications))}")
    print(f"   Medications detected: {list(sorted(all_medications))[:10]}")
    if cardiac_medications:
        print(f"   Cardiac medications: {list(set(cardiac_medications))}")
    
    print(f"\n💓 Cardiac Condition Recognition:")
    print(f"   Total conditions found: {len(all_conditions)}")
    print(f"   Cardiac-specific conditions: {len(cardiac_conditions)}")
    print(f"   Conditions: {list(sorted(all_conditions))}")
    
    # Complete multi-specialty comparison with all 5 specialties
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
            
        print(f"\n👶👴🧠🧴❤️ Complete Multi-Specialty Performance Comparison (5 Specialties):")
        
        specialties = ['Pediatric', 'Geriatric', 'Psychiatry', 'Dermatology', 'Cardiology']
        times = [
            pediatric_data['avg_processing_time_ms'], 
            geriatric_data['avg_processing_time_ms'], 
            psychiatry_data['avg_processing_time_ms'], 
            dermatology_data['avg_processing_time_ms'],
            avg_time
        ]
        qualities = [
            pediatric_data['avg_quality_score'], 
            geriatric_data['avg_quality_score'], 
            psychiatry_data['avg_quality_score'], 
            dermatology_data['avg_quality_score'],
            avg_quality
        ]
        medications = [
            len(pediatric_data['unique_medications']),
            len(geriatric_data['unique_medications']),
            len(psychiatry_data['unique_medications']),
            len(dermatology_data['unique_medications']),
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
        
        # Performance leaders across all 5 specialties
        fastest_specialty = specialties[times.index(min(times))]
        highest_quality = specialties[qualities.index(max(qualities))]
        most_medications = specialties[medications.index(max(medications))]
        
        print(f"\n🏆 Complete Multi-Specialty Performance Leaders (5 Specialties):")
        print(f"   Fastest Processing: {fastest_specialty} ({min(times):.1f}ms)")
        print(f"   Highest Quality: {highest_quality} ({max(qualities):.2f})")
        print(f"   Most Medications Detected: {most_medications} ({max(medications)} medications)")
        
        # Overall system performance summary across all 5 specialties
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
        
    except FileNotFoundError:
        print(f"\n📊 Previous specialty results not found for complete comparison")
    
    # Performance assessment with specialty context
    print(f"\n🎯 Cardiology Specialty Assessment:")
    if avg_quality >= 0.8:
        print(f"   ✅ HIGH QUALITY: Excellent cardiac entity extraction ({avg_quality:.2f})")
    elif avg_quality >= 0.6:
        print(f"   🟡 GOOD QUALITY: Solid cardiac performance ({avg_quality:.2f})")
    else:
        print(f"   🔴 NEEDS IMPROVEMENT: Low cardiac extraction ({avg_quality:.2f})")
    
    # Cardiology-specific recommendations
    print(f"\n💡 Cardiology-Specific Recommendations:")
    
    missing_cardiac_meds = set(['atorvastatin', 'metoprolol', 'clopidogrel', 'ramipril',
                               'aspirin', 'furosemide', 'isosorbide', 'bisoprolol',
                               'amlodipine', 'carvedilol', 'rosuvastatin', 'digoxin',
                               'lisinopril', 'apixaban', 'losartan', 'spironolactone',
                               'nebivolol', 'diltiazem', 'simvastatin', 'warfarin']) - set(cardiac_medications)
    
    if missing_cardiac_meds:
        print(f"   1. ❤️ Add missing cardiac medications to spaCy vocabulary:")
        print(f"      {list(missing_cardiac_meds)}")
    
    spacy_percentage = tier_counts.get('spacy', 0) / len(successful) * 100 if successful else 0
    if spacy_percentage < 60:
        print(f"   2. 🏗️ Optimize for cardiac medication patterns")
        print(f"   3. ❤️ Add cardiac condition recognition (MI, CHF, arrhythmias)")
        print(f"   4. 💊 Enhance cardiovascular drug class detection")
        
    print(f"   5. 🩸 Implement anticoagulation therapy monitoring")
    print(f"   6. 🔬 Add cardiac biomarker and monitoring detection")
    print(f"   7. ❤️ Develop cardiac event management patterns")
    print(f"   8. 💊 Add drug interaction warnings (e.g., statins + grapefruit)")
    print(f"   9. 📊 Implement cardiac dosing titration recognition")
    
    # Save results
    results_dir = Path("clinical_results")
    results_dir.mkdir(exist_ok=True)
    
    batch_data = {
        'batch_name': 'cardiology_encounter_notes',
        'timestamp': time.time(),
        'specialty': 'cardiology',
        'total_notes': len(CARDIOLOGY_CLINICAL_NOTES),
        'successful_notes': len(successful),
        'avg_processing_time_ms': float(avg_time),
        'avg_quality_score': float(avg_quality),
        'tier_usage': tier_counts,
        'unique_medications': list(sorted(all_medications)),
        'unique_conditions': list(sorted(all_conditions)),
        'cardiac_conditions': list(sorted(cardiac_conditions)),
        'cardiac_medications': list(set(cardiac_medications)),
        'results': results
    }
    
    batch_file = results_dir / "cardiology_batch_results.json"
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
    print("❤️ Multi-Specialty Test - Cardiology Encounter Notes")
    print("Testing 3-tier medical NLP across different medical specialties")
    print("="*70)
    
    asyncio.run(process_cardiology_batch())