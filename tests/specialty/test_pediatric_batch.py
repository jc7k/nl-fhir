#!/usr/bin/env python3
"""
Test Pediatric Clinical Notes - Real Data Validation
Process the 20 pediatric encounter notes through our 3-tier NLP system
"""

import sys
sys.path.append('../../src')

import asyncio
import json
import time
from pathlib import Path
from nl_fhir.services.nlp.models import model_manager

# The 20 pediatric clinical notes you provided
PEDIATRIC_CLINICAL_NOTES = [
    "Prescribed patient Lily Thompson 5mL of Acetaminophen oral suspension every 6 hours as needed for fever.",
    "Started patient Noah Kim on 250mg Cefdinir once daily for otitis media; advised parents on red stool discoloration.",
    "Administered patient Ava Patel 0.5mL of MMR vaccine subcutaneously in right arm; documented immunization record.",
    "Initiated patient Ethan Garcia on 4mg Ondansetron orally every 8 hours for nausea and vomiting.",
    "Prescribed patient Mia Johnson 1 puff of Fluticasone nasal spray daily for allergic rhinitis.",
    "Started patient Lucas Brown on 10mg Montelukast nightly for asthma control; discussed behavioral side effects.",
    "Recommended patient Emma Davis begin 5mL Amoxicillin oral suspension three times daily for streptococcal pharyngitis.",
    "Administered patient Sophia Lee 0.25mL of rotavirus vaccine orally; no adverse reaction noted.",
    "Prescribed patient Jackson Nguyen 1 drop of Ofloxacin ophthalmic solution in affected eye four times daily for conjunctivitis.",
    "Started patient Olivia Martinez on 0.1% Hydrocortisone cream twice daily for diaper rash.",
    "Initiated patient Benjamin Clark on 2.5mg Prednisolone oral solution twice daily for asthma exacerbation.",
    "Prescribed patient Grace Wilson 5mL Diphenhydramine at bedtime for allergic reaction; advised on sedation risk.",
    "Started patient Henry Adams on 0.5mg Loratadine chewable tablet once daily for seasonal allergies.",
    "Administered patient Zoe Robinson 0.5mL of DTaP vaccine intramuscularly in left thigh; monitored for 15 minutes post-injection.",
    "Prescribed patient Ella Hernandez 1 drop of Polymyxin B/Trimethoprim ophthalmic solution every 3 hours for bacterial conjunctivitis.",
    "Started patient Liam Scott on 5mL Ibuprofen oral suspension every 6 hours as needed for pain.",
    "Initiated patient Natalie Young on 0.5mg Melatonin nightly for sleep onset delay; discussed behavioral sleep hygiene.",
    "Prescribed patient Carter Evans 1 puff of Budesonide inhaler twice daily for persistent asthma.",
    "Started patient Chloe Ramirez on 5mL Azithromycin oral suspension once daily for 3 days for pneumonia.",
    "Administered patient Mason Bell 0.5mL of Hepatitis A vaccine intramuscularly; updated immunization chart."
]

async def process_pediatric_batch():
    """Process the pediatric clinical notes and analyze results"""
    
    print("🧒 Processing Pediatric Clinical Notes - Real Data Test")
    print("="*65)
    print(f"📝 Processing {len(PEDIATRIC_CLINICAL_NOTES)} real pediatric encounter notes...")
    print("Testing our 3-tier medical NLP architecture with clinical data\n")
    
    results = []
    start_time = time.time()
    
    # Track unique medications found for vocabulary analysis
    all_medications = set()
    all_conditions = set()
    pediatric_specific_terms = set()
    
    for i, note in enumerate(PEDIATRIC_CLINICAL_NOTES, 1):
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
                all_medications.add(med.get('text', '').lower())
            
            for condition in entities.get('conditions', []):
                all_conditions.add(condition.get('text', '').lower())
            
            # Identify pediatric-specific terms
            note_lower = note.lower()
            pediatric_terms = ['vaccine', 'immunization', 'oral suspension', 'chewable', 'pediatric', 'child']
            for term in pediatric_terms:
                if term in note_lower:
                    pediatric_specific_terms.add(term)
            
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
            
            # Show results with detailed analysis
            print(f"    ✅ {processing_time:.1f}ms | {total_entities} entities | {tier_used} tier | quality: {quality_score:.2f}")
            
            # Show extracted entities by category
            for category, entity_list in entities.items():
                if entity_list:
                    entity_texts = [e.get('text', '') for e in entity_list]
                    print(f"       {category}: {entity_texts}")
            
            # Pediatric-specific analysis
            if 'vaccine' in note_lower or 'immunization' in note_lower:
                print(f"       🩹 Immunization record detected")
            if 'mg' in note and any(age_term in note_lower for age_term in ['child', 'pediatric', 'infant']):
                print(f"       👶 Pediatric dosing detected")
                
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
    
    # Print comprehensive results
    print("🧒 Pediatric Clinical Notes - Analysis Complete!")
    print("="*55)
    
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
    
    print(f"\n💊 Medication Vocabulary Analysis:")
    print(f"   Unique medications found: {len(all_medications)}")
    print(f"   Top medications: {list(sorted(all_medications))[:10]}")
    
    print(f"\n🏥 Condition Recognition:")
    print(f"   Unique conditions found: {len(all_conditions)}")
    print(f"   Conditions detected: {list(sorted(all_conditions))}")
    
    print(f"\n👶 Pediatric-Specific Features:")
    print(f"   Pediatric terms identified: {list(sorted(pediatric_specific_terms))}")
    
    # Performance assessment
    print(f"\n🎯 Performance Assessment:")
    if avg_quality >= 0.8:
        print(f"   ✅ HIGH QUALITY: Excellent entity extraction ({avg_quality:.2f})")
    elif avg_quality >= 0.6:
        print(f"   🟡 GOOD QUALITY: Solid performance, room for improvement ({avg_quality:.2f})")
    else:
        print(f"   🔴 NEEDS IMPROVEMENT: Low entity extraction ({avg_quality:.2f})")
    
    if avg_time <= 500:
        print(f"   ✅ FAST PERFORMANCE: Well within <2s requirement ({avg_time:.1f}ms)")
    elif avg_time <= 1000:
        print(f"   🟡 ACCEPTABLE: Good performance ({avg_time:.1f}ms)")
    else:
        print(f"   🔴 SLOW: Above optimal range ({avg_time:.1f}ms)")
    
    # Recommendations based on real data
    print(f"\n💡 Recommendations for Improvement:")
    
    spacy_percentage = tier_counts.get('spacy', 0) / len(successful) * 100 if successful else 0
    if spacy_percentage < 50:
        print(f"   1. 🔧 Expand spaCy medical vocabulary with pediatric medications")
        print(f"      Missing: Acetaminophen, Cefdinir, Ondansetron, Fluticasone, etc.")
    
    if avg_quality < 0.8:
        print(f"   2. 📚 Add pediatric-specific medical terminology")
        print(f"      Focus: Vaccines, oral suspensions, pediatric dosing patterns")
        
    print(f"   3. 🩹 Implement immunization record recognition")
    print(f"   4. 👶 Add pediatric dosing pattern detection")
    print(f"   5. 🏥 Enhance condition recognition for pediatric conditions")
    
    # Save results
    results_dir = Path("clinical_results")
    results_dir.mkdir(exist_ok=True)
    
    batch_data = {
        'batch_name': 'pediatric_encounter_notes',
        'timestamp': time.time(),
        'total_notes': len(PEDIATRIC_CLINICAL_NOTES),
        'successful_notes': len(successful),
        'avg_processing_time_ms': float(avg_time),
        'avg_quality_score': float(avg_quality),
        'tier_usage': tier_counts,
        'unique_medications': list(sorted(all_medications)),
        'unique_conditions': list(sorted(all_conditions)),
        'pediatric_terms': list(sorted(pediatric_specific_terms)),
        'results': results
    }
    
    batch_file = results_dir / "pediatric_batch_results.json"
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
    print("🧒 Real Clinical Data Test - Pediatric Encounter Notes")
    print("Testing 3-tier medical NLP with actual clinical documentation")
    print("="*70)
    
    asyncio.run(process_pediatric_batch())