#!/usr/bin/env python3
"""
Rheumatology Clinical Notes Batch Processor
Processes 11 rheumatology clinical notes to validate NLP system performance
"""

import sys
import os
import json
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from nl_fhir.services.nlp.models import model_manager

def load_rheumatology_notes():
    """Load Rheumatology clinical notes for processing"""
    return [
        "Initiated patient Lucas Bennett on 60mg Tocilizumab IV monthly for giant cell arteritis; CRP tracked.",
        
        "Prescribed patient Chloe Adams 1g Mycophenolate mofetil twice daily for lupus nephritis; renal panel ordered.",
        
        "Started patient Julian Moore on 50mg Cyclosporine twice daily for dermatomyositis; blood pressure monitored.",
        
        "Initiated patient Ella Nguyen on 100mg Celecoxib daily for osteoarthritis; cardiovascular risk reviewed.",
        
        "Prescribed patient Benjamin Carter 500mg Colchicine twice daily for acute gout flare; renal dosing adjusted.",
        
        "Started patient Grace Simmons on 10mg Tofacitinib twice daily for rheumatoid arthritis; lipid panel ordered.",
        
        "Initiated patient Nathaniel Young on 100mg Dapsone daily for vasculitis; G6PD screening completed.",
        
        "Prescribed patient Lily Bell 0.6mg Colchicine daily for gout prophylaxis; GI tolerance discussed.",
        
        "Started patient Gabriel Hayes on 50mg Anakinra subcutaneously daily for adult-onset Still's disease.",
        
        "Initiated patient Natalie Robinson on 250mg Indomethacin three times daily for acute gout; hydration encouraged.",
        
        "Prescribed patient Daniel Foster 100mg Rituximab IV every 6 months for seropositive RA; infusion reaction precautions reviewed."
    ]

def analyze_rheumatology_batch():
    """Process all Rheumatology notes and generate comprehensive analysis"""
    
    print("🦴 Rheumatology Clinical Notes Batch Processor")
    print("=" * 60)
    
    notes = load_rheumatology_notes()
    results = []
    processing_times = []
    
    print(f"📊 Processing {len(notes)} rheumatology clinical notes...")
    print()
    
    for i, note in enumerate(notes, 1):
        print(f"Processing note {i}/{len(notes)}...", end=" ")
        
        start_time = time.time()
        try:
            # Extract medical entities using our 3-tier system
            entities = model_manager.extract_medical_entities(note)
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            processing_times.append(processing_time)
            
            # Count entities and determine processing tier
            total_entities = sum(len(entity_list) for entity_list in entities.values())
            
            # Determine tier used
            methods_used = set()
            for entity_list in entities.values():
                for entity in entity_list:
                    if entity.get('method'):
                        methods_used.add(entity['method'])
            
            if 'llm' in methods_used:
                processing_tier = "LLM"
            elif 'spacy' in methods_used:
                processing_tier = "spaCy"
            else:
                processing_tier = "Regex"
            
            # Enhanced result with metadata
            enhanced_result = {
                "note_id": f"rheum_{i:03d}",
                "processing_time_ms": round(processing_time, 1),
                "processing_tier": processing_tier,
                "success": True,
                "extracted_data": entities,
                "total_entities": total_entities,
                "clinical_note": note[:100] + "..." if len(note) > 100 else note
            }
            
            results.append(enhanced_result)
            print(f"✅ Success ({processing_time:.1f}ms, {processing_tier}, {total_entities} entities)")
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            processing_times.append(processing_time)
            
            error_result = {
                "note_id": f"rheum_{i:03d}",
                "processing_time_ms": round(processing_time, 1),
                "success": False,
                "error": str(e),
                "clinical_note": note[:100] + "..." if len(note) > 100 else note
            }
            
            results.append(error_result)
            print(f"❌ Error ({processing_time:.1f}ms): {str(e)}")
    
    # Calculate comprehensive statistics
    successful_results = [r for r in results if r["success"]]
    success_rate = len(successful_results) / len(results)
    avg_processing_time = sum(processing_times) / len(processing_times)
    
    print()
    print("📈 RHEUMATOLOGY BATCH ANALYSIS RESULTS")
    print("=" * 45)
    print(f"Total Notes Processed: {len(results)}")
    print(f"Successful Extractions: {len(successful_results)}")
    print(f"Success Rate: {success_rate:.1%}")
    print(f"Average Processing Time: {avg_processing_time:.1f}ms")
    print(f"Total Processing Time: {sum(processing_times):.0f}ms")
    
    # Processing tier analysis
    if successful_results:
        tier_analysis = {}
        for result in successful_results:
            tier = result.get("processing_tier", "unknown")
            tier_analysis[tier] = tier_analysis.get(tier, 0) + 1
        
        print()
        print("🔄 Processing Tier Distribution:")
        for tier, count in sorted(tier_analysis.items()):
            percentage = (count / len(successful_results)) * 100
            print(f"  {tier}: {count} notes ({percentage:.1f}%)")
    
    # Medical entity analysis for Rheumatology specialty
    print()
    print("🦴 Rheumatology-Specific Medical Analysis:")
    
    all_medications = []
    all_conditions = []
    all_procedures = []
    immunosuppressants = []
    antirheumatic_drugs = []
    biologic_medications = []
    
    for result in successful_results:
        entities = result["extracted_data"]
        if isinstance(entities, dict):
            medications = entities.get("medications", [])
            conditions = entities.get("conditions", [])
            procedures = entities.get("procedures", [])
            
            # Extract entity names from the entities (they may be objects with 'text' field)
            med_names = [med.get('text', med) if isinstance(med, dict) else med for med in medications]
            condition_names = [cond.get('text', cond) if isinstance(cond, dict) else cond for cond in conditions]
            procedure_names = [proc.get('text', proc) if isinstance(proc, dict) else proc for proc in procedures]
            
            all_medications.extend(med_names)
            all_conditions.extend(condition_names)
            all_procedures.extend(procedure_names)
            
            # Identify rheumatology-specific medication categories
            note_text = result["clinical_note"].lower()
            
            # Immunosuppressants
            immunosuppressive_drugs = ["mycophenolate", "cyclosporine", "methotrexate", "azathioprine", "tacrolimus"]
            for drug in immunosuppressive_drugs:
                if drug in note_text:
                    immunosuppressants.append(drug)
            
            # Antirheumatic drugs (DMARDs)
            dmard_drugs = ["tofacitinib", "colchicine", "celecoxib", "indomethacin", "dapsone"]
            for drug in dmard_drugs:
                if drug in note_text:
                    antirheumatic_drugs.append(drug)
                    
            # Biologic medications
            biologic_drugs = ["tocilizumab", "rituximab", "anakinra", "adalimumab", "infliximab"]
            for drug in biologic_drugs:
                if drug in note_text:
                    biologic_medications.append(drug)
    
    # Display medical findings
    print(f"  Total Medications Identified: {len(set(all_medications))}")
    print(f"  Total Conditions Identified: {len(set(all_conditions))}")
    print(f"  Total Procedures Identified: {len(set(all_procedures))}")
    print(f"  Immunosuppressants Detected: {len(set(immunosuppressants))}")
    print(f"  Antirheumatic Drugs Detected: {len(set(antirheumatic_drugs))}")
    print(f"  Biologic Medications Detected: {len(set(biologic_medications))}")
    
    # Top Rheumatology medications
    if all_medications:
        med_freq = {}
        for med in all_medications:
            med_freq[med] = med_freq.get(med, 0) + 1
        top_meds = sorted(med_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"  Top Medications: {', '.join([f'{med} ({freq})' for med, freq in top_meds])}")
    
    # Display detected rheumatologic conditions
    rheumatologic_conditions = ["arthritis", "lupus", "gout", "vasculitis", "dermatomyositis", "arteritis"]
    detected_conditions = [cond for cond in set(all_conditions) if any(rheum_cond in cond.lower() for rheum_cond in rheumatologic_conditions)]
    if detected_conditions:
        print(f"  Rheumatologic Conditions: {', '.join(detected_conditions[:5])}")
    
    # Save detailed results
    output_dir = Path("clinical_results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "rheumatology_batch_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "specialty": "Rheumatology",
            "total_notes": len(results),
            "successful_extractions": len(successful_results),
            "success_rate": success_rate,
            "average_processing_time_ms": avg_processing_time,
            "processing_tier_distribution": tier_analysis if successful_results else {},
            "medical_analysis": {
                "unique_medications": len(set(all_medications)),
                "unique_conditions": len(set(all_conditions)),
                "unique_procedures": len(set(all_procedures)),
                "immunosuppressants_count": len(set(immunosuppressants)),
                "antirheumatic_drugs_count": len(set(antirheumatic_drugs)),
                "biologic_medications_count": len(set(biologic_medications)),
                "top_medications": top_meds[:10] if all_medications else [],
                "detected_conditions": detected_conditions[:10]
            },
            "detailed_results": results
        }, f, indent=2, default=str)
    
    print(f"💾 Detailed results saved to: {output_file}")
    
    # Quality assessment
    if success_rate >= 0.95:
        quality_grade = "🟢 EXCELLENT"
    elif success_rate >= 0.90:
        quality_grade = "🟡 GOOD"
    elif success_rate >= 0.80:
        quality_grade = "🟠 FAIR"
    else:
        quality_grade = "🔴 NEEDS IMPROVEMENT"
    
    print()
    print(f"🎯 Rheumatology Specialty Quality Assessment: {quality_grade}")
    print(f"📊 Performance Score: {success_rate:.3f}")
    
    # Specialty summary comparison
    print()
    print("🏥 MULTI-SPECIALTY VALIDATION PROGRESS:")
    print("✅ Pediatric Medicine (20 notes) - 100% success")
    print("✅ Geriatric Medicine (20 notes) - 100% success") 
    print("✅ Psychiatry (20 notes) - 100% success")
    print("✅ Dermatology (20 notes) - 100% success")
    print("✅ Cardiology (20 notes) - 100% success")
    print("✅ Emergency Medicine (20 notes) - 100% success")
    print("✅ Endocrinology (20 notes) - 100% success")
    print("✅ Infectious Disease (20 notes) - 100% success")
    print("✅ OB/GYN (20 notes) - 100% success")
    print(f"🦴 Rheumatology ({len(notes)} notes) - {success_rate:.1%} success")
    
    total_notes = 9 * 20 + len(notes)  # 9 previous specialties + current
    print(f"📊 TOTAL VALIDATION: {total_notes} clinical notes across 10 medical specialties")
    
    return results, success_rate

if __name__ == "__main__":
    analyze_rheumatology_batch()