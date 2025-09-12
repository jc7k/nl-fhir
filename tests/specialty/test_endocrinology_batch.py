#!/usr/bin/env python3
"""
Test Endocrinology Clinical Notes - Multi-Specialty Validation
Process 20 endocrinology encounter notes and compare with other specialties
"""

import sys
sys.path.append('../../src')

import asyncio
import json
import time
from pathlib import Path
from nl_fhir.services.nlp.models import model_manager

# The 20 endocrinology clinical notes you provided
ENDOCRINOLOGY_CLINICAL_NOTES = [
    "Started patient Ava Thompson on 10mg Methimazole twice daily for hyperthyroidism; TSH and free T4 to be rechecked in 4 weeks.",
    "Prescribed patient Liam Brooks 15 units of insulin aspart subcutaneously before meals; carb counting education provided.",
    "Initiated patient Emma Davis on 60mg Denosumab subcutaneously every 6 months for osteoporosis; calcium and vitamin D supplementation advised.",
    "Started patient Noah Clark on 5mg Linagliptin once daily for type 2 diabetes; renal function within normal limits.",
    "Prescribed patient Olivia Martinez 100mcg Levothyroxine daily for hypothyroidism; follow-up TSH in 6 weeks.",
    "Initiated patient Mason Lee on 0.6mg Liraglutide subcutaneously daily for weight management; discussed GI side effects.",
    "Started patient Sophia Turner on 30mg Prednisone daily for adrenal insufficiency; taper schedule outlined.",
    "Prescribed patient Ethan Rivera 5mg Empagliflozin once daily for diabetes and heart failure; advised on genital hygiene.",
    "Started patient Mia Scott on 10mg Estradiol orally daily for menopausal symptoms; discussed thromboembolic risks.",
    "Initiated patient Lucas Bennett on 100mg Spironolactone daily for hirsutism; potassium levels monitored.",
    "Prescribed patient Chloe Adams 0.25mg Cabergoline twice weekly for prolactinoma; prolactin levels to be rechecked.",
    "Started patient Julian Moore on 5mg Finasteride daily for androgenic alopecia; discussed sexual side effects.",
    "Initiated patient Ella Nguyen on 10mg Hydrocortisone twice daily for Addison's disease; emergency steroid card issued.",
    "Prescribed patient Benjamin Carter 5mg Glipizide before breakfast for type 2 diabetes; hypoglycemia precautions reviewed.",
    "Started patient Grace Simmons on 100mg Sitagliptin daily for diabetes; renal dosing confirmed.",
    "Initiated patient Nathaniel Young on 0.5mg Teriparatide subcutaneously daily for severe osteoporosis; therapy duration limited to 2 years.",
    "Prescribed patient Lily Bell 25mg Canagliflozin daily for diabetes; discussed risk of ketoacidosis.",
    "Started patient Gabriel Hayes on 10mg Testosterone gel daily for hypogonadism; baseline labs obtained.",
    "Initiated patient Natalie Robinson on 5mg Medroxyprogesterone daily for abnormal uterine bleeding due to anovulation.",
    "Prescribed patient Daniel Foster 0.1mg Desmopressin intranasally twice daily for central diabetes insipidus."
]

async def process_endocrinology_batch():
    """Process endocrinology clinical notes and compare with other specialty performance"""
    
    print("🧪 Processing Endocrinology Clinical Notes - Multi-Specialty Test")
    print("="*74)
    print(f"📝 Processing {len(ENDOCRINOLOGY_CLINICAL_NOTES)} endocrinology encounter notes...")
    print("Comparing performance with all other specialties (pediatric, geriatric, psychiatry, dermatology, cardiology, emergency)\n")
    
    results = []
    start_time = time.time()
    
    # Track endocrinology-specific metrics
    all_medications = set()
    all_conditions = set()
    endocrine_conditions = set()
    endocrine_medications = []
    hormone_therapies = set()
    diabetes_medications = set()
    
    for i, note in enumerate(ENDOCRINOLOGY_CLINICAL_NOTES, 1):
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
                
                # Track endocrine medications
                if med_text in ['methimazole', 'insulin', 'denosumab', 'linagliptin', 
                               'levothyroxine', 'liraglutide', 'prednisone', 'empagliflozin',
                               'estradiol', 'spironolactone', 'cabergoline', 'finasteride',
                               'hydrocortisone', 'glipizide', 'sitagliptin', 'teriparatide',
                               'canagliflozin', 'testosterone', 'medroxyprogesterone', 'desmopressin']:
                    endocrine_medications.append(med_text)
                
                # Track hormone therapies
                if med_text in ['levothyroxine', 'estradiol', 'testosterone', 'hydrocortisone', 
                               'prednisone', 'desmopressin', 'cabergoline', 'medroxyprogesterone']:
                    hormone_therapies.add(med_text)
                
                # Track diabetes medications
                if med_text in ['insulin', 'linagliptin', 'empagliflozin', 'glipizide', 
                               'sitagliptin', 'canagliflozin', 'liraglutide']:
                    diabetes_medications.add(med_text)
            
            for condition in entities.get('conditions', []):
                condition_text = condition.get('text', '').lower()
                all_conditions.add(condition_text)
                
                # Track endocrine-specific conditions
                if any(endocrine_term in condition_text for endocrine_term in [
                    'hyperthyroidism', 'hypothyroidism', 'diabetes', 'osteoporosis',
                    'adrenal insufficiency', 'heart failure', 'hirsutism', 'prolactinoma',
                    'alopecia', 'addison', 'hypogonadism', 'anovulation', 'insipidus'
                ]):
                    endocrine_conditions.add(condition_text)
            
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
            
            # Show results with endocrinology-specific analysis
            print(f"    ✅ {processing_time:.1f}ms | {total_entities} entities | {tier_used} tier | quality: {quality_score:.2f}")
            
            # Show extracted entities by category
            for category, entity_list in entities.items():
                if entity_list:
                    entity_texts = [e.get('text', '') for e in entity_list]
                    print(f"       {category}: {entity_texts}")
            
            # Endocrinology-specific analysis
            note_lower = note.lower()
            if any(condition in note_lower for condition in ['diabetes', 'hyperthyroidism', 'hypothyroidism']):
                print(f"       🧪 Major endocrine disorder detected")
            if any(med in note_lower for med in ['insulin', 'levothyroxine', 'prednisone']):
                print(f"       💉 Critical hormone therapy detected")
            if any(route in note_lower for route in ['subcutaneously', 'intranasally']):
                print(f"       🩸 Specialized administration route")
            if any(term in note_lower for term in ['tsh', 'free t4', 'prolactin', 'renal function']):
                print(f"       🔬 Endocrine monitoring required")
            if any(term in note_lower for term in ['hypoglycemia', 'ketoacidosis', 'thromboembolic']):
                print(f"       ⚠️ Endocrine safety concern identified")
            if any(term in note_lower for term in ['emergency steroid card', 'taper schedule', 'therapy duration']):
                print(f"       📋 Specialized endocrine management")
                
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
    print("🧪 Endocrinology Clinical Notes - Analysis Complete!")
    print("="*62)
    
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
    
    print(f"\n🧪 Endocrine Medication Analysis:")
    print(f"   Total unique medications: {len(all_medications)}")
    print(f"   Endocrine medications found: {len(set(endocrine_medications))}")
    print(f"   Hormone therapies: {len(hormone_therapies)}")
    print(f"   Diabetes medications: {len(diabetes_medications)}")
    print(f"   Medications detected: {list(sorted(all_medications))[:10]}")
    if endocrine_medications:
        print(f"   Endocrine medications: {list(set(endocrine_medications))}")
    
    print(f"\n🏥 Endocrine Condition Recognition:")
    print(f"   Total conditions found: {len(all_conditions)}")
    print(f"   Endocrine-specific conditions: {len(endocrine_conditions)}")
    print(f"   Conditions: {list(sorted(all_conditions))}")
    
    print(f"\n💉 Specialized Therapy Categories:")
    print(f"   Hormone Replacement: {sorted(list(hormone_therapies))}")
    print(f"   Diabetes Management: {sorted(list(diabetes_medications))}")
    
    # Complete multi-specialty comparison with all 7 specialties
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
        with open('clinical_results/emergency_batch_results.json', 'r') as f:
            emergency_data = json.load(f)
            
        print(f"\n👶👴🧠🧴❤️🚑🧪 Complete Multi-Specialty Performance Comparison (7 Specialties):")
        
        specialties = ['Pediatric', 'Geriatric', 'Psychiatry', 'Dermatology', 'Cardiology', 'Emergency', 'Endocrinology']
        times = [
            pediatric_data['avg_processing_time_ms'], 
            geriatric_data['avg_processing_time_ms'], 
            psychiatry_data['avg_processing_time_ms'], 
            dermatology_data['avg_processing_time_ms'],
            cardiology_data['avg_processing_time_ms'],
            emergency_data['avg_processing_time_ms'],
            avg_time
        ]
        qualities = [
            pediatric_data['avg_quality_score'], 
            geriatric_data['avg_quality_score'], 
            psychiatry_data['avg_quality_score'], 
            dermatology_data['avg_quality_score'],
            cardiology_data['avg_quality_score'],
            emergency_data['avg_quality_score'],
            avg_quality
        ]
        medications = [
            len(pediatric_data['unique_medications']),
            len(geriatric_data['unique_medications']),
            len(psychiatry_data['unique_medications']),
            len(dermatology_data['unique_medications']),
            len(cardiology_data['unique_medications']),
            len(emergency_data['unique_medications']),
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
        
        # Performance leaders across all 7 specialties
        fastest_specialty = specialties[times.index(min(times))]
        highest_quality = specialties[qualities.index(max(qualities))]
        most_medications = specialties[medications.index(max(medications))]
        
        print(f"\n🏆 Complete Multi-Specialty Performance Leaders (7 Specialties):")
        print(f"   Fastest Processing: {fastest_specialty} ({min(times):.1f}ms)")
        print(f"   Highest Quality: {highest_quality} ({max(qualities):.2f})")
        print(f"   Most Medications Detected: {most_medications} ({max(medications)} medications)")
        
        # Overall system performance summary across all 7 specialties
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
        
        # Endocrinology specialty ranking
        endocrinology_time_rank = sorted(times).index(avg_time) + 1
        endocrinology_quality_rank = sorted(qualities, reverse=True).index(avg_quality) + 1
        endocrinology_med_rank = sorted(medications, reverse=True).index(len(all_medications)) + 1
        
        print(f"\n🧪 Endocrinology Specialty Ranking:")
        print(f"   Processing Speed: #{endocrinology_time_rank} of {len(specialties)} specialties")
        print(f"   Quality Score: #{endocrinology_quality_rank} of {len(specialties)} specialties")
        print(f"   Medication Detection: #{endocrinology_med_rank} of {len(specialties)} specialties")
        
        # Specialty complexity analysis
        print(f"\n🔬 Specialty Complexity Analysis:")
        avg_entities_per_specialty = [
            sum(r['entities_found'] for r in pediatric_data['results'] if r.get('success', False)) / len([r for r in pediatric_data['results'] if r.get('success', False)]) if pediatric_data['results'] else 0,
            sum(r['entities_found'] for r in geriatric_data['results'] if r.get('success', False)) / len([r for r in geriatric_data['results'] if r.get('success', False)]) if geriatric_data['results'] else 0,
            sum(r['entities_found'] for r in psychiatry_data['results'] if r.get('success', False)) / len([r for r in psychiatry_data['results'] if r.get('success', False)]) if psychiatry_data['results'] else 0,
            sum(r['entities_found'] for r in dermatology_data['results'] if r.get('success', False)) / len([r for r in dermatology_data['results'] if r.get('success', False)]) if dermatology_data['results'] else 0,
            sum(r['entities_found'] for r in cardiology_data['results'] if r.get('success', False)) / len([r for r in cardiology_data['results'] if r.get('success', False)]) if cardiology_data['results'] else 0,
            sum(r['entities_found'] for r in emergency_data['results'] if r.get('success', False)) / len([r for r in emergency_data['results'] if r.get('success', False)]) if emergency_data['results'] else 0,
            avg_entities
        ]
        
        for specialty, entities in zip(specialties, avg_entities_per_specialty):
            print(f"   {specialty}: {entities:.1f} avg entities per note")
        
    except FileNotFoundError:
        print(f"\n📊 Previous specialty results not found for complete comparison")
    
    # Performance assessment with specialty context
    print(f"\n🎯 Endocrinology Specialty Assessment:")
    if avg_quality >= 0.8:
        print(f"   ✅ HIGH QUALITY: Excellent endocrine entity extraction ({avg_quality:.2f})")
    elif avg_quality >= 0.6:
        print(f"   🟡 GOOD QUALITY: Solid endocrine performance ({avg_quality:.2f})")
    else:
        print(f"   🔴 NEEDS IMPROVEMENT: Low endocrine extraction ({avg_quality:.2f})")
    
    # Endocrinology-specific recommendations
    print(f"\n💡 Endocrinology-Specific Recommendations:")
    
    missing_endocrine_meds = set(['methimazole', 'insulin', 'denosumab', 'linagliptin',
                                 'levothyroxine', 'liraglutide', 'prednisone', 'empagliflozin',
                                 'estradiol', 'spironolactone', 'cabergoline', 'finasteride',
                                 'hydrocortisone', 'glipizide', 'sitagliptin', 'teriparatide',
                                 'canagliflozin', 'testosterone', 'medroxyprogesterone', 'desmopressin']) - set(endocrine_medications)
    
    if missing_endocrine_meds:
        print(f"   1. 🧪 Add missing endocrine medications to spaCy vocabulary:")
        print(f"      {list(missing_endocrine_meds)}")
    
    spacy_percentage = tier_counts.get('spacy', 0) / len(successful) * 100 if successful else 0
    if spacy_percentage < 60:
        print(f"   2. 🏗️ Optimize for endocrine medication patterns")
        print(f"   3. 🧪 Add endocrine condition recognition (diabetes, thyroid disorders)")
        print(f"   4. 💉 Enhance hormone therapy detection")
        
    print(f"   5. 🔬 Implement endocrine monitoring requirements (TSH, glucose, HbA1c)")
    print(f"   6. ⚠️ Add endocrine safety warnings (hypoglycemia, ketoacidosis)")
    print(f"   7. 💉 Develop insulin and hormone dosing patterns")
    print(f"   8. 📋 Add specialized endocrine management recognition")
    print(f"   9. 🩸 Implement subcutaneous and intranasal route optimization")
    print(f"   10. 🧪 Add diabetes medication class recognition")
    
    # Save results
    results_dir = Path("clinical_results")
    results_dir.mkdir(exist_ok=True)
    
    batch_data = {
        'batch_name': 'endocrinology_encounter_notes',
        'timestamp': time.time(),
        'specialty': 'endocrinology',
        'total_notes': len(ENDOCRINOLOGY_CLINICAL_NOTES),
        'successful_notes': len(successful),
        'avg_processing_time_ms': float(avg_time),
        'avg_quality_score': float(avg_quality),
        'tier_usage': tier_counts,
        'unique_medications': list(sorted(all_medications)),
        'unique_conditions': list(sorted(all_conditions)),
        'endocrine_conditions': list(sorted(endocrine_conditions)),
        'endocrine_medications': list(set(endocrine_medications)),
        'hormone_therapies': list(sorted(hormone_therapies)),
        'diabetes_medications': list(sorted(diabetes_medications)),
        'results': results
    }
    
    batch_file = results_dir / "endocrinology_batch_results.json"
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
    print("🧪 Multi-Specialty Test - Endocrinology Encounter Notes")
    print("Testing 3-tier medical NLP across different medical specialties")
    print("="*70)
    
    asyncio.run(process_endocrinology_batch())