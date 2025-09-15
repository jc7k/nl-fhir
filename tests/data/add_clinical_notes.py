#!/usr/bin/env python3
"""
Simple Clinical Notes Processor - Ready for Your Batch
Easy interface for adding your clinical notes in batches of 20
"""

import sys
sys.path.append('src')

import asyncio
import json
import time
from pathlib import Path
from nl_fhir.services.nlp.models import model_manager

class SimpleClinicalProcessor:
    """Simple processor for your clinical notes"""
    
    def __init__(self):
        self.results_dir = Path("clinical_results")
        self.results_dir.mkdir(exist_ok=True)
        
    async def process_clinical_batch(self, clinical_notes, batch_name=None):
        """Process a batch of clinical notes through our 3-tier NLP"""
        
        if batch_name is None:
            batch_name = f"batch_{int(time.time())}"
        
        print(f"🏥 Processing Clinical Batch: {batch_name}")
        print(f"📝 Processing {len(clinical_notes)} clinical notes...")
        print("="*60)
        
        results = []
        start_time = time.time()
        
        for i, note in enumerate(clinical_notes, 1):
            print(f"\n{i:2d}. Processing: {note[:60]}{'...' if len(note) > 60 else ''}")
            
            # Time each note processing
            note_start = time.time()
            
            try:
                # Extract medical entities using our 3-tier system
                entities = model_manager.extract_medical_entities(note)
                
                processing_time = (time.time() - note_start) * 1000
                
                # Count total entities found
                total_entities = sum(len(entity_list) for entity_list in entities.values())
                
                # Determine which tier was used (based on method in entities)
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
                
                # Calculate quality score (simple heuristic)
                words = len(note.split())
                quality_score = min(1.0, total_entities / max(1, words * 0.1))
                
                result = {
                    'note_number': i,
                    'clinical_text': note,
                    'processing_time_ms': processing_time,
                    'entities_found': total_entities,
                    'tier_used': tier_used,
                    'quality_score': quality_score,
                    'entities': entities,
                    'success': True
                }
                
                # Show results
                print(f"    ✅ {processing_time:.1f}ms | {total_entities} entities | {tier_used} tier | quality: {quality_score:.2f}")
                
                # Show key entities found
                for category, entity_list in entities.items():
                    if entity_list:
                        entity_texts = [e.get('text', '') for e in entity_list]
                        print(f"       {category}: {entity_texts}")
                
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
        
        # Calculate batch statistics
        total_time = (time.time() - start_time) * 1000
        successful = [r for r in results if r.get('success', False)]
        
        if successful:
            avg_time = sum(r['processing_time_ms'] for r in successful) / len(successful)
            avg_entities = sum(r['entities_found'] for r in successful) / len(successful)
            avg_quality = sum(r['quality_score'] for r in successful) / len(successful)
            
            # Tier usage
            tier_counts = {}
            for r in successful:
                tier = r.get('tier_used', 'unknown')
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
        else:
            avg_time = avg_entities = avg_quality = 0
            tier_counts = {}
        
        # Print summary
        print(f"\n🎉 Batch Processing Complete!")
        print("="*50)
        print(f"📊 Results Summary:")
        print(f"   ✅ Success rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"   ⏱️  Average processing time: {avg_time:.1f}ms")
        print(f"   📈 Average entities found: {avg_entities:.1f}")
        print(f"   🎯 Average quality score: {avg_quality:.2f}")
        print(f"   🚀 Total batch time: {total_time:.1f}ms")
        print(f"   📊 Throughput: {len(results)/(total_time/1000):.1f} notes/second")
        
        print(f"\n🏗️  3-Tier Architecture Usage:")
        for tier, count in tier_counts.items():
            percentage = count / len(successful) * 100 if successful else 0
            print(f"   {tier}: {count} ({percentage:.1f}%)")
        
        # Save results
        batch_file = self.results_dir / f"{batch_name}.json"
        batch_data = {
            'batch_name': batch_name,
            'timestamp': time.time(),
            'total_notes': len(clinical_notes),
            'successful_notes': len(successful),
            'avg_processing_time_ms': avg_time,
            'avg_quality_score': avg_quality,
            'tier_usage': tier_counts,
            'results': results
        }
        
        with open(batch_file, 'w') as f:
            json.dump(batch_data, f, indent=2)
        
        print(f"\n💾 Results saved to: {batch_file}")
        
        return batch_data

# Sample clinical notes for demonstration
SAMPLE_CLINICAL_NOTES = [
    "Start patient on Lisinopril 10mg daily for hypertension",
    "Initiate Metformin 500mg twice daily with meals for diabetes",
    "Prescribe Atorvastatin 20mg at bedtime for hyperlipidemia",
    "Begin Levothyroxine 50mcg daily on empty stomach for hypothyroidism",
    "Order CBC with differential and comprehensive metabolic panel",
    "Check fasting glucose and HbA1c in 3 months",
    "Obtain lipid panel and liver function tests before next visit",
    "Patient reports chest discomfort with exertion, order cardiac enzymes and EKG",
    "Continue current heart failure medications, patient stable",
    "Increase dosage of antidepressant, patient tolerating well",
    "Discontinue aspirin due to GI bleeding risk",
    "Switch from immediate-release to extended-release formulation",
    "Reduce warfarin dose to 2.5mg daily, check INR weekly",
    "Schedule follow-up in 2 weeks to reassess symptoms",
    "Return to clinic in 3 months for medication review",
    "Patient education on diabetes management provided",
    "Schedule colonoscopy for cancer screening",
    "Refer to cardiology for stress test evaluation",
    "Order chest X-ray to evaluate persistent cough",
    "Arrange sleep study for suspected sleep apnea"
]

async def process_your_notes(your_clinical_notes):
    """
    Process YOUR clinical notes through our 3-tier medical NLP system
    
    Args:
        your_clinical_notes: List of strings, each containing a clinical note
        
    Returns:
        Dictionary with results and statistics
    """
    
    processor = SimpleClinicalProcessor()
    results = await processor.process_clinical_batch(your_clinical_notes)
    return results

async def demo():
    """Run demonstration with sample notes"""
    
    print("🏥 Clinical Notes Processor - Ready for Your Data!")
    print("="*60)
    print("📝 Running demo with 20 sample clinical notes...")
    
    results = await process_your_notes(SAMPLE_CLINICAL_NOTES)
    
    print(f"\n💡 To process your own clinical notes:")
    print(f"   1. Replace SAMPLE_CLINICAL_NOTES with your list of notes")
    print(f"   2. Each note should be a string")
    print(f"   3. Process 20 notes at a time for best results")
    print(f"   4. Results are automatically saved to clinical_results/")
    
    return results

# Instructions for adding your clinical notes
"""
TO PROCESS YOUR CLINICAL NOTES:

1. Replace the SAMPLE_CLINICAL_NOTES list with your notes:

   YOUR_NOTES = [
       "Patient needs blood pressure medication",
       "Order comprehensive metabolic panel",
       "Continue current diabetes medications",
       # Add up to 20 more notes here...
   ]

2. Run the processor:

   results = await process_your_notes(YOUR_NOTES)

3. View the results in clinical_results/ folder
"""

if __name__ == "__main__":
    asyncio.run(demo())