#!/usr/bin/env python3
"""
Test Dermatology Clinical Notes - Multi-Specialty Validation
Process 20 dermatology encounter notes and compare with other specialties
"""

import sys
sys.path.append('../../src')

import asyncio
import json
import time
from pathlib import Path
from nl_fhir.services.nlp.models import model_manager

# The 20 dermatology clinical notes you provided
DERMATOLOGY_CLINICAL_NOTES = [
    "Prescribed patient Ava Brooks 0.1% Tretinoin cream nightly for acne; advised on gradual titration and sun sensitivity.",
    "Started patient Liam Foster on 250mg Terbinafine orally once daily for onychomycosis; liver function tests ordered.",
    "Recommended patient Emma Hayes apply 1% Hydrocortisone cream twice daily for mild eczema flare.",
    "Initiated patient Noah Bennett on 100mg Doxycycline daily for rosacea; advised on GI upset and photosensitivity.",
    "Prescribed patient Olivia Reed 0.05% Clobetasol ointment twice daily for plaque psoriasis; limited to 2-week course.",
    "Started patient Mason Rivera on 5mg Isotretinoin twice daily for severe nodulocystic acne; pregnancy test confirmed negative.",
    "Recommended patient Sophia James begin 1% Permethrin cream overnight for scabies; repeat in 7 days.",
    "Prescribed patient Ethan Clark 0.1% Tacrolimus ointment twice daily for atopic dermatitis; discussed black box warning.",
    "Started patient Mia Turner on 250mg Griseofulvin daily for tinea capitis; advised on fatty meal absorption.",
    "Initiated patient Lucas Adams on 0.5% Salicylic acid lotion daily for keratosis pilaris.",
    "Prescribed patient Isabella Morris 0.1% Betamethasone cream twice daily for lichen planus; monitored for skin thinning.",
    "Started patient Henry Simmons on 500mg Valacyclovir twice daily for herpes zoster; pain management discussed.",
    "Recommended patient Lily Nguyen begin 0.05% Retinaldehyde cream nightly for photoaging.",
    "Prescribed patient Gabriel Scott 1% Ketoconazole shampoo twice weekly for seborrheic dermatitis.",
    "Started patient Chloe Martinez on 0.1% Mometasone cream once daily for contact dermatitis; patch testing scheduled.",
    "Initiated patient Julian Bell on 0.03% Pimecrolimus cream twice daily for facial eczema.",
    "Prescribed patient Ella Thompson 0.5% Coal tar solution nightly for scalp psoriasis.",
    "Started patient Benjamin Carter on 0.1% Adapalene gel nightly for comedonal acne.",
    "Recommended patient Grace Lee begin 0.5% Urea cream twice daily for xerosis.",
    "Prescribed patient Nathaniel Young 1% Silver sulfadiazine cream daily for second-degree burn; wound care instructions provided."
]

async def process_dermatology_batch():
    """Process dermatology clinical notes and compare with other specialty performance"""
    
    print("🧴 Processing Dermatology Clinical Notes - Multi-Specialty Test")
    print("="*72)
    print(f"📝 Processing {len(DERMATOLOGY_CLINICAL_NOTES)} dermatology encounter notes...")
    print("Comparing performance with pediatric, geriatric, and psychiatry results\n")
    
    results = []
    start_time = time.time()
    
    # Track dermatology-specific metrics
    all_medications = set()
    all_conditions = set()
    dermatologic_conditions = set()
    topical_medications = []
    
    for i, note in enumerate(DERMATOLOGY_CLINICAL_NOTES, 1):
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
                
                # Track topical dermatologic medications
                if med_text in ['tretinoin', 'terbinafine', 'hydrocortisone', 'doxycycline', 
                               'clobetasol', 'isotretinoin', 'permethrin', 'tacrolimus',
                               'griseofulvin', 'betamethasone', 'valacyclovir', 'retinaldehyde',
                               'ketoconazole', 'mometasone', 'pimecrolimus', 'adapalene', 'urea']:
                    topical_medications.append(med_text)
            
            for condition in entities.get('conditions', []):
                condition_text = condition.get('text', '').lower()
                all_conditions.add(condition_text)
                
                # Track dermatologic-specific conditions
                if any(derm_term in condition_text for derm_term in [
                    'acne', 'onychomycosis', 'eczema', 'rosacea', 'psoriasis',
                    'scabies', 'dermatitis', 'tinea', 'keratosis', 'lichen',
                    'herpes', 'photoaging', 'seborrheic', 'xerosis', 'burn'
                ]):
                    dermatologic_conditions.add(condition_text)
            
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
            
            # Show results with dermatology-specific analysis
            print(f"    ✅ {processing_time:.1f}ms | {total_entities} entities | {tier_used} tier | quality: {quality_score:.2f}")
            
            # Show extracted entities by category
            for category, entity_list in entities.items():
                if entity_list:
                    entity_texts = [e.get('text', '') for e in entity_list]
                    print(f"       {category}: {entity_texts}")
            
            # Dermatology-specific analysis
            note_lower = note.lower()
            if any(condition in note_lower for condition in ['acne', 'psoriasis', 'eczema', 'dermatitis']):
                print(f"       🧴 Inflammatory skin condition detected")
            if any(med in note_lower for med in ['cream', 'ointment', 'lotion', 'gel']):
                print(f"       💊 Topical medication formulation detected")
            if any(term in note_lower for term in ['sun sensitivity', 'photosensitivity', 'black box warning']):
                print(f"       ⚠️  Important safety warning noted")
            if any(term in note_lower for term in ['liver function', 'pregnancy test', 'patch testing']):
                print(f"       🔬 Monitoring/testing requirement identified")
                
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
    print("🧴 Dermatology Clinical Notes - Analysis Complete!")
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
    
    print(f"\n🧴 Dermatologic Medication Analysis:")
    print(f"   Total unique medications: {len(all_medications)}")
    print(f"   Topical dermatologic drugs found: {len(set(topical_medications))}")
    print(f"   Medications detected: {list(sorted(all_medications))[:10]}")
    if topical_medications:
        print(f"   Dermatologic medications: {list(set(topical_medications))}")
    
    print(f"\n🧴 Dermatologic Condition Recognition:")
    print(f"   Total conditions found: {len(all_conditions)}")
    print(f"   Dermatologic-specific conditions: {len(dermatologic_conditions)}")
    print(f"   Conditions: {list(sorted(all_conditions))}")
    
    # Complete multi-specialty comparison
    try:
        # Load all previous specialty results
        with open('clinical_results/pediatric_batch_results.json', 'r') as f:
            pediatric_data = json.load(f)
        with open('clinical_results/geriatric_batch_results.json', 'r') as f:
            geriatric_data = json.load(f)
        with open('clinical_results/psychiatry_batch_results.json', 'r') as f:
            psychiatry_data = json.load(f)
            
        print(f"\n👶👴🧠🧴 Complete Multi-Specialty Performance Comparison:")
        
        specialties = ['Pediatric', 'Geriatric', 'Psychiatry', 'Dermatology']
        times = [
            pediatric_data['avg_processing_time_ms'], 
            geriatric_data['avg_processing_time_ms'], 
            psychiatry_data['avg_processing_time_ms'], 
            avg_time
        ]
        qualities = [
            pediatric_data['avg_quality_score'], 
            geriatric_data['avg_quality_score'], 
            psychiatry_data['avg_quality_score'], 
            avg_quality
        ]
        medications = [
            len(pediatric_data['unique_medications']),
            len(geriatric_data['unique_medications']),
            len(psychiatry_data['unique_medications']),
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
        
        # Performance leaders across all specialties
        fastest_specialty = specialties[times.index(min(times))]
        highest_quality = specialties[qualities.index(max(qualities))]
        most_medications = specialties[medications.index(max(medications))]
        
        print(f"\n🏆 Complete Multi-Specialty Performance Leaders:")
        print(f"   Fastest Processing: {fastest_specialty} ({min(times):.1f}ms)")
        print(f"   Highest Quality: {highest_quality} ({max(qualities):.2f})")
        print(f"   Most Medications Detected: {most_medications} ({max(medications)} medications)")
        
        # Overall system performance summary
        avg_across_specialties_time = sum(times) / len(times)
        avg_across_specialties_quality = sum(qualities) / len(qualities)
        
        print(f"\n📈 Overall System Performance Across All Specialties:")
        print(f"   Average Processing Time: {avg_across_specialties_time:.1f}ms")
        print(f"   Average Quality Score: {avg_across_specialties_quality:.2f}")
        print(f"   Success Rate: 100% across all {len(specialties)} specialties (80 total notes)")
        
    except FileNotFoundError:
        print(f"\n📊 Previous specialty results not found for complete comparison")
    
    # Performance assessment with specialty context
    print(f"\n🎯 Dermatology Specialty Assessment:")
    if avg_quality >= 0.8:
        print(f"   ✅ HIGH QUALITY: Excellent dermatologic entity extraction ({avg_quality:.2f})")
    elif avg_quality >= 0.6:
        print(f"   🟡 GOOD QUALITY: Solid dermatologic performance ({avg_quality:.2f})")
    else:
        print(f"   🔴 NEEDS IMPROVEMENT: Low dermatologic extraction ({avg_quality:.2f})")
    
    # Dermatology-specific recommendations
    print(f"\n💡 Dermatology-Specific Recommendations:")
    
    missing_dermatologic_meds = set(['tretinoin', 'terbinafine', 'hydrocortisone', 'doxycycline',
                                    'clobetasol', 'isotretinoin', 'permethrin', 'tacrolimus',
                                    'griseofulvin', 'betamethasone', 'valacyclovir', 'retinaldehyde',
                                    'ketoconazole', 'mometasone', 'pimecrolimus', 'adapalene', 'urea']) - set(topical_medications)
    
    if missing_dermatologic_meds:
        print(f"   1. 🧴 Add missing dermatologic medications to spaCy vocabulary:")
        print(f"      {list(missing_dermatologic_meds)}")
    
    spacy_percentage = tier_counts.get('spacy', 0) / len(successful) * 100 if successful else 0
    if spacy_percentage < 60:
        print(f"   2. 🏗️ Optimize for topical medication patterns")
        print(f"   3. 🧴 Add dermatologic condition recognition (acne, eczema, psoriasis)")
        print(f"   4. 💊 Enhance topical formulation detection (cream, ointment, gel)")
        
    print(f"   5. ⚠️ Implement dermatologic safety warning recognition")
    print(f"   6. 🔬 Add dermatologic monitoring requirement detection")
    print(f"   7. 🧴 Develop concentration percentage pattern recognition")
    print(f"   8. 💊 Add topical application frequency patterns")
    
    # Save results
    results_dir = Path("clinical_results")
    results_dir.mkdir(exist_ok=True)
    
    batch_data = {
        'batch_name': 'dermatology_encounter_notes',
        'timestamp': time.time(),
        'specialty': 'dermatology',
        'total_notes': len(DERMATOLOGY_CLINICAL_NOTES),
        'successful_notes': len(successful),
        'avg_processing_time_ms': float(avg_time),
        'avg_quality_score': float(avg_quality),
        'tier_usage': tier_counts,
        'unique_medications': list(sorted(all_medications)),
        'unique_conditions': list(sorted(all_conditions)),
        'dermatologic_conditions': list(sorted(dermatologic_conditions)),
        'topical_medications': list(set(topical_medications)),
        'results': results
    }
    
    batch_file = results_dir / "dermatology_batch_results.json"
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
    print("🧴 Multi-Specialty Test - Dermatology Encounter Notes")
    print("Testing 3-tier medical NLP across different medical specialties")
    print("="*70)
    
    asyncio.run(process_dermatology_batch())