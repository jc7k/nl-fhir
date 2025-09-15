#!/usr/bin/env python3
"""
Simple Clinical Batch Processor
Quick interface for processing 20+ clinical notes at a time
"""

import sys
sys.path.append('src')
sys.path.append('tests/framework')

import asyncio
import json
import time
from pathlib import Path
from batch_clinical_processor import BatchClinicalProcessor

async def process_your_clinical_notes(clinical_notes_list):
    """Process your clinical notes through the 3-tier NLP system"""
    
    print(f"🏥 Processing {len(clinical_notes_list)} Clinical Notes")
    print("="*60)
    
    # Initialize processor
    processor = BatchClinicalProcessor()
    
    # Process the batch
    batch_name = f"user_batch_{int(time.time())}"
    results = await processor.process_batch(
        clinical_notes=clinical_notes_list,
        batch_name=batch_name,
        save_results=True
    )
    
    # Print summary
    analysis = results['analysis']
    print(f"\n🎉 Batch Processing Complete!")
    print(f"📊 Results:")
    print(f"   ✅ Success rate: {analysis['success_rate']:.1%} ({analysis['successful_tests']}/{analysis['total_tests']})")
    print(f"   ⏱️  Average time: {analysis['avg_processing_time_ms']:.1f}ms")
    print(f"   🎯 Quality score: {analysis['avg_quality_score']:.2f}")
    print(f"   🚀 Throughput: {analysis['throughput_notes_per_second']:.1f} notes/sec")
    
    print(f"\n🏗️  3-Tier Usage:")
    for tier, count in analysis['tier_usage'].items():
        percentage = count / analysis['total_tests'] * 100
        print(f"   {tier}: {count} ({percentage:.1f}%)")
    
    print(f"\n📁 Results saved in: tests/results/{batch_name}/")
    
    return results

def demo_with_sample_notes():
    """Demo with sample clinical notes"""
    
    sample_notes = [
        # Medication orders
        "Start patient on Lisinopril 10mg daily for hypertension",
        "Initiate Metformin 500mg twice daily with meals for diabetes",
        "Prescribe Atorvastatin 20mg at bedtime for hyperlipidemia",
        "Begin Levothyroxine 50mcg daily on empty stomach for hypothyroidism",
        
        # Lab orders
        "Order CBC with differential and comprehensive metabolic panel",
        "Check fasting glucose and HbA1c in 3 months",
        "Obtain lipid panel and liver function tests before next visit",
        
        # Complex clinical scenarios
        "Patient reports chest discomfort with exertion, order cardiac enzymes and EKG",
        "Continue current heart failure medications, patient stable",
        "Increase dosage of antidepressant, patient tolerating well",
        
        # Medication changes
        "Discontinue aspirin due to GI bleeding risk",
        "Switch from immediate-release to extended-release formulation",
        "Reduce warfarin dose to 2.5mg daily, check INR weekly",
        
        # Follow-up orders
        "Schedule follow-up in 2 weeks to reassess symptoms",
        "Return to clinic in 3 months for medication review",
        "Patient education on diabetes management provided",
        
        # Procedure orders
        "Schedule colonoscopy for cancer screening",
        "Refer to cardiology for stress test evaluation",
        "Order chest X-ray to evaluate persistent cough",
        "Arrange sleep study for suspected sleep apnea"
    ]
    
    return sample_notes

async def main():
    """Main entry point"""
    
    print("🏥 Clinical Batch Processor - Ready for Your Notes!")
    print("="*60)
    
    # For demo purposes, use sample notes
    print("📝 Running demo with 20 sample clinical notes...")
    sample_notes = demo_with_sample_notes()
    
    results = await process_your_clinical_notes(sample_notes)
    
    print(f"\n💡 Ready to process your real clinical notes!")
    print(f"   - Replace the sample_notes list with your clinical notes")
    print(f"   - Each note should be a string with the clinical text")
    print(f"   - Process 20 notes at a time for optimal performance")
    
    print(f"\n📖 Example usage:")
    print(f"""
    # Your clinical notes
    your_notes = [
        "Patient needs medication for blood pressure control",
        "Order lab work including CBC and chemistry panel",
        # ... add up to 20 more notes
    ]
    
    # Process them
    results = await process_your_clinical_notes(your_notes)
    """)

if __name__ == "__main__":
    asyncio.run(main())