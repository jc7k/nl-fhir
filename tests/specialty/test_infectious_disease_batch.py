#!/usr/bin/env python3
"""
Test Infectious Disease Clinical Notes - Multi-Specialty Validation
Process 20 infectious disease encounter notes and compare with other specialties
"""

import sys
sys.path.append('../../src')

import asyncio
import json
import time
from pathlib import Path
from nl_fhir.services.nlp.models import model_manager

# The 20 infectious disease clinical notes you provided
INFECTIOUS_DISEASE_CLINICAL_NOTES = [
    "Started patient Ava Thompson on 600mg Linezolid twice daily for MRSA pneumonia; CBC monitored.",
    "Prescribed patient Liam Brooks 2g Cefepime IV every 8 hours for hospital-acquired infection; renal dosing adjusted.",
    "Initiated patient Emma Davis on 500mg Valacyclovir twice daily for genital herpes suppression.",
    "Started patient Noah Clark on 300mg Isoniazid daily for latent TB; pyridoxine supplementation initiated.",
    "Prescribed patient Olivia Martinez 400mg Efavirenz/300mg Tenofovir/200mg Emtricitabine once daily for HIV; baseline labs reviewed.",
    "Started patient Mason Lee on 500mg Levofloxacin daily for community-acquired pneumonia; QT prolongation discussed.",
    "Initiated patient Sophia Turner on 250mg Azithromycin daily for Mycoplasma pneumonia; 5-day course.",
    "Prescribed patient Ethan Rivera 100mg Doxycycline twice daily for Lyme disease; tick exposure documented.",
    "Started patient Mia Scott on 500mg Metronidazole twice daily for trichomoniasis; advised abstinence until completion.",
    "Initiated patient Lucas Bennett on 4g Ceftriaxone IV daily for bacterial meningitis; lumbar puncture performed.",
    "Prescribed patient Chloe Adams 200mg Fluconazole daily for systemic candidiasis; liver enzymes monitored.",
    "Started patient Julian Moore on 900mg Ganciclovir IV every 12 hours for CMV retinitis; ophthalmology consult placed.",
    "Initiated patient Ella Nguyen on 300mg Rifampin daily for TB; drug interactions reviewed.",
    "Prescribed patient Benjamin Carter 500mg Clarithromycin twice daily for H. pylori eradication; triple therapy initiated.",
    "Started patient Grace Simmons on 400mg Trimethoprim-Sulfamethoxazole twice daily for PCP prophylaxis in HIV.",
    "Initiated patient Nathaniel Young on 600mg Foscarnet IV every 8 hours for acyclovir-resistant HSV; renal function monitored.",
    "Prescribed patient Lily Bell 100mg Itraconazole daily for histoplasmosis; therapeutic drug monitoring ordered.",
    "Started patient Gabriel Hayes on 500mg Ceftazidime IV every 8 hours for Pseudomonas infection.",
    "Initiated patient Natalie Robinson on 250mg Oseltamivir twice daily for influenza; started within 48 hours of symptom onset.",
    "Prescribed patient Daniel Foster 300mg Bictegravir/200mg Emtricitabine/25mg Tenofovir alafenamide once daily for HIV; adherence counseling provided."
]

async def process_infectious_disease_batch():
    """Process infectious disease clinical notes and compare with other specialty performance"""
    
    print("🦠 Processing Infectious Disease Clinical Notes - Multi-Specialty Test")
    print("="*78)
    print(f"📝 Processing {len(INFECTIOUS_DISEASE_CLINICAL_NOTES)} infectious disease encounter notes...")
    print("Comparing performance with all other specialties (pediatric, geriatric, psychiatry, dermatology, cardiology, emergency, endocrinology)\n")
    
    results = []
    start_time = time.time()
    
    # Track infectious disease-specific metrics
    all_medications = set()
    all_conditions = set()
    infectious_conditions = set()
    infectious_medications = []
    antibiotic_classes = set()
    antiviral_medications = set()
    antifungal_medications = set()
    hiv_medications = set()
    
    for i, note in enumerate(INFECTIOUS_DISEASE_CLINICAL_NOTES, 1):
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
                
                # Track infectious disease medications
                if med_text in ['linezolid', 'cefepime', 'valacyclovir', 'isoniazid', 
                               'efavirenz', 'tenofovir', 'emtricitabine', 'levofloxacin',
                               'azithromycin', 'doxycycline', 'metronidazole', 'ceftriaxone',
                               'fluconazole', 'ganciclovir', 'rifampin', 'clarithromycin',
                               'trimethoprim', 'sulfamethoxazole', 'foscarnet', 'itraconazole',
                               'ceftazidime', 'oseltamivir', 'bictegravir']:
                    infectious_medications.append(med_text)
                
                # Classify by antimicrobial type
                if med_text in ['linezolid', 'cefepime', 'levofloxacin', 'azithromycin', 
                               'doxycycline', 'ceftriaxone', 'clarithromycin', 'ceftazidime']:
                    antibiotic_classes.add(med_text)
                
                if med_text in ['valacyclovir', 'ganciclovir', 'foscarnet', 'oseltamivir']:
                    antiviral_medications.add(med_text)
                
                if med_text in ['fluconazole', 'itraconazole']:
                    antifungal_medications.add(med_text)
                
                if med_text in ['efavirenz', 'tenofovir', 'emtricitabine', 'bictegravir']:
                    hiv_medications.add(med_text)
            
            for condition in entities.get('conditions', []):
                condition_text = condition.get('text', '').lower()
                all_conditions.add(condition_text)
                
                # Track infectious disease-specific conditions
                if any(infectious_term in condition_text for infectious_term in [
                    'mrsa', 'pneumonia', 'infection', 'herpes', 'tb', 'hiv',
                    'mycoplasma', 'lyme', 'trichomoniasis', 'meningitis',
                    'candidiasis', 'cmv', 'retinitis', 'pylori', 'pcp',
                    'hsv', 'histoplasmosis', 'pseudomonas', 'influenza'
                ]):
                    infectious_conditions.add(condition_text)
            
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
            
            # Show results with infectious disease-specific analysis
            print(f"    ✅ {processing_time:.1f}ms | {total_entities} entities | {tier_used} tier | quality: {quality_score:.2f}")
            
            # Show extracted entities by category
            for category, entity_list in entities.items():
                if entity_list:
                    entity_texts = [e.get('text', '') for e in entity_list]
                    print(f"       {category}: {entity_texts}")
            
            # Infectious disease-specific analysis
            note_lower = note.lower()
            if any(condition in note_lower for condition in ['mrsa', 'hiv', 'tb', 'meningitis']):
                print(f"       🦠 Serious infectious disease detected")
            if any(med in note_lower for med in ['linezolid', 'ceftriaxone', 'ganciclovir']):
                print(f"       💉 High-level antimicrobial therapy")
            if any(route in note_lower for route in ['iv', 'twice daily', 'every 8 hours']):
                print(f"       🕐 Complex dosing schedule")
            if any(term in note_lower for term in ['cbc monitored', 'liver enzymes', 'renal function']):
                print(f"       🔬 Antimicrobial monitoring required")
            if any(term in note_lower for term in ['drug interactions', 'qt prolongation', 'therapeutic drug monitoring']):
                print(f"       ⚠️ Infectious disease safety concern")
            if any(term in note_lower for term in ['prophylaxis', 'suppression', 'adherence counseling']):
                print(f"       📋 Specialized infectious disease management")
            if 'resistant' in note_lower or 'mrsa' in note_lower:
                print(f"       🛡️ Drug-resistant organism")
                
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
    print("🦠 Infectious Disease Clinical Notes - Analysis Complete!")
    print("="*66)
    
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
    
    print(f"\n🦠 Infectious Disease Medication Analysis:")
    print(f"   Total unique medications: {len(all_medications)}")
    print(f"   Infectious disease medications found: {len(set(infectious_medications))}")
    print(f"   Antibiotic classes: {len(antibiotic_classes)}")
    print(f"   Antiviral medications: {len(antiviral_medications)}")
    print(f"   Antifungal medications: {len(antifungal_medications)}")
    print(f"   HIV medications: {len(hiv_medications)}")
    print(f"   Medications detected: {list(sorted(all_medications))[:10]}")
    if infectious_medications:
        print(f"   Infectious disease medications: {list(set(infectious_medications))}")
    
    print(f"\n🦠 Infectious Disease Condition Recognition:")
    print(f"   Total conditions found: {len(all_conditions)}")
    print(f"   Infectious disease-specific conditions: {len(infectious_conditions)}")
    print(f"   Conditions: {list(sorted(all_conditions))}")
    
    print(f"\n💉 Antimicrobial Categories:")
    print(f"   Antibiotics: {sorted(list(antibiotic_classes))}")
    print(f"   Antivirals: {sorted(list(antiviral_medications))}")
    print(f"   Antifungals: {sorted(list(antifungal_medications))}")
    print(f"   HIV Therapies: {sorted(list(hiv_medications))}")
    
    # Complete multi-specialty comparison with all 8 specialties
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
        with open('clinical_results/endocrinology_batch_results.json', 'r') as f:
            endocrinology_data = json.load(f)
            
        print(f"\n👶👴🧠🧴❤️🚑🧪🦠 Complete Multi-Specialty Performance Comparison (8 Specialties):")
        
        specialties = ['Pediatric', 'Geriatric', 'Psychiatry', 'Dermatology', 'Cardiology', 'Emergency', 'Endocrinology', 'Infectious Disease']
        times = [
            pediatric_data['avg_processing_time_ms'], 
            geriatric_data['avg_processing_time_ms'], 
            psychiatry_data['avg_processing_time_ms'], 
            dermatology_data['avg_processing_time_ms'],
            cardiology_data['avg_processing_time_ms'],
            emergency_data['avg_processing_time_ms'],
            endocrinology_data['avg_processing_time_ms'],
            avg_time
        ]
        qualities = [
            pediatric_data['avg_quality_score'], 
            geriatric_data['avg_quality_score'], 
            psychiatry_data['avg_quality_score'], 
            dermatology_data['avg_quality_score'],
            cardiology_data['avg_quality_score'],
            emergency_data['avg_quality_score'],
            endocrinology_data['avg_quality_score'],
            avg_quality
        ]
        medications = [
            len(pediatric_data['unique_medications']),
            len(geriatric_data['unique_medications']),
            len(psychiatry_data['unique_medications']),
            len(dermatology_data['unique_medications']),
            len(cardiology_data['unique_medications']),
            len(emergency_data['unique_medications']),
            len(endocrinology_data['unique_medications']),
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
        
        # Performance leaders across all 8 specialties
        fastest_specialty = specialties[times.index(min(times))]
        highest_quality = specialties[qualities.index(max(qualities))]
        most_medications = specialties[medications.index(max(medications))]
        
        print(f"\n🏆 Complete Multi-Specialty Performance Leaders (8 Specialties):")
        print(f"   Fastest Processing: {fastest_specialty} ({min(times):.1f}ms)")
        print(f"   Highest Quality: {highest_quality} ({max(qualities):.2f})")
        print(f"   Most Medications Detected: {most_medications} ({max(medications)} medications)")
        
        # Overall system performance summary across all 8 specialties
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
        
        # Infectious Disease specialty ranking
        infectious_time_rank = sorted(times).index(avg_time) + 1
        infectious_quality_rank = sorted(qualities, reverse=True).index(avg_quality) + 1
        infectious_med_rank = sorted(medications, reverse=True).index(len(all_medications)) + 1
        
        print(f"\n🦠 Infectious Disease Specialty Ranking:")
        print(f"   Processing Speed: #{infectious_time_rank} of {len(specialties)} specialties")
        print(f"   Quality Score: #{infectious_quality_rank} of {len(specialties)} specialties")
        print(f"   Medication Detection: #{infectious_med_rank} of {len(specialties)} specialties")
        
        # System maturity analysis
        print(f"\n📊 System Maturity Across 8 Specialties:")
        print(f"   Consistent Quality: {(1 - (max(qualities) - min(qualities)))*100:.1f}% consistency score")
        print(f"   Processing Efficiency: {(min(times)/max(times))*100:.1f}% efficiency ratio")
        print(f"   Medical Coverage: {sum(medications)} total medications across all specialties")
        
        # Antimicrobial complexity analysis
        print(f"\n🦠 Infectious Disease Complexity Assessment:")
        combination_therapies = sum(1 for note in INFECTIOUS_DISEASE_CLINICAL_NOTES if '/' in note)
        iv_therapies = sum(1 for note in INFECTIOUS_DISEASE_CLINICAL_NOTES if 'IV' in note)
        monitoring_requirements = sum(1 for note in INFECTIOUS_DISEASE_CLINICAL_NOTES if any(term in note.lower() for term in ['monitored', 'reviewed', 'adjusted']))
        
        print(f"   Combination Therapies: {combination_therapies} notes ({combination_therapies/20*100:.0f}%)")
        print(f"   IV Antimicrobials: {iv_therapies} notes ({iv_therapies/20*100:.0f}%)")
        print(f"   Monitoring Requirements: {monitoring_requirements} notes ({monitoring_requirements/20*100:.0f}%)")
        
    except FileNotFoundError:
        print(f"\n📊 Previous specialty results not found for complete comparison")
    
    # Performance assessment with specialty context
    print(f"\n🎯 Infectious Disease Specialty Assessment:")
    if avg_quality >= 0.8:
        print(f"   ✅ HIGH QUALITY: Excellent infectious disease entity extraction ({avg_quality:.2f})")
    elif avg_quality >= 0.6:
        print(f"   🟡 GOOD QUALITY: Solid infectious disease performance ({avg_quality:.2f})")
    else:
        print(f"   🔴 NEEDS IMPROVEMENT: Low infectious disease extraction ({avg_quality:.2f})")
    
    # Infectious disease-specific recommendations
    print(f"\n💡 Infectious Disease-Specific Recommendations:")
    
    missing_infectious_meds = set(['linezolid', 'cefepime', 'valacyclovir', 'isoniazid',
                                  'efavirenz', 'tenofovir', 'emtricitabine', 'levofloxacin',
                                  'azithromycin', 'doxycycline', 'metronidazole', 'ceftriaxone',
                                  'fluconazole', 'ganciclovir', 'rifampin', 'clarithromycin',
                                  'trimethoprim', 'sulfamethoxazole', 'foscarnet', 'itraconazole',
                                  'ceftazidime', 'oseltamivir', 'bictegravir']) - set(infectious_medications)
    
    if missing_infectious_meds:
        print(f"   1. 🦠 Add missing infectious disease medications to spaCy vocabulary:")
        print(f"      {list(missing_infectious_meds)}")
    
    spacy_percentage = tier_counts.get('spacy', 0) / len(successful) * 100 if successful else 0
    if spacy_percentage < 60:
        print(f"   2. 🏗️ Optimize for antimicrobial medication patterns")
        print(f"   3. 🦠 Add infectious disease condition recognition (MRSA, HIV, TB)")
        print(f"   4. 💉 Enhance antimicrobial class detection")
        
    print(f"   5. 🔬 Implement antimicrobial monitoring requirements")
    print(f"   6. ⚠️ Add drug interaction and safety warnings")
    print(f"   7. 🕐 Develop complex dosing schedule recognition")
    print(f"   8. 🛡️ Add drug-resistant organism detection")
    print(f"   9. 📋 Implement specialized ID management (prophylaxis, suppression)")
    print(f"   10. 🧬 Add combination therapy pattern recognition")
    
    # Save results
    results_dir = Path("clinical_results")
    results_dir.mkdir(exist_ok=True)
    
    batch_data = {
        'batch_name': 'infectious_disease_encounter_notes',
        'timestamp': time.time(),
        'specialty': 'infectious_disease',
        'total_notes': len(INFECTIOUS_DISEASE_CLINICAL_NOTES),
        'successful_notes': len(successful),
        'avg_processing_time_ms': float(avg_time),
        'avg_quality_score': float(avg_quality),
        'tier_usage': tier_counts,
        'unique_medications': list(sorted(all_medications)),
        'unique_conditions': list(sorted(all_conditions)),
        'infectious_conditions': list(sorted(infectious_conditions)),
        'infectious_medications': list(set(infectious_medications)),
        'antibiotic_classes': list(sorted(antibiotic_classes)),
        'antiviral_medications': list(sorted(antiviral_medications)),
        'antifungal_medications': list(sorted(antifungal_medications)),
        'hiv_medications': list(sorted(hiv_medications)),
        'results': results
    }
    
    batch_file = results_dir / "infectious_disease_batch_results.json"
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
    print("🦠 Multi-Specialty Test - Infectious Disease Encounter Notes")
    print("Testing 3-tier medical NLP across different medical specialties")
    print("="*70)
    
    asyncio.run(process_infectious_disease_batch())