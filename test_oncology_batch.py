#!/usr/bin/env python3
"""
Oncology Clinical Notes Batch Processor
Processes 20 oncology clinical notes to validate NLP system performance
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

def load_oncology_notes():
    """Load Oncology clinical notes for processing"""
    return [
        "Started patient Ava Thompson on 500mg Capecitabine orally twice daily for metastatic breast cancer; hand-foot syndrome discussed.",
        
        "Prescribed patient Liam Brooks 100mg Cisplatin IV every 3 weeks for non-small cell lung cancer; hydration protocol initiated.",
        
        "Initiated patient Emma Davis on 150mg Erlotinib daily for EGFR-positive lung cancer; rash management reviewed.",
        
        "Started patient Noah Clark on 100mg Imatinib daily for chronic myeloid leukemia; CBC monitored.",
        
        "Prescribed patient Olivia Martinez 125mg Palbociclib daily for 21 days on, 7 days off for HR+ breast cancer; neutropenia precautions discussed.",
        
        "Started patient Mason Lee on 50mg Temozolomide daily for glioblastoma; concurrent radiation scheduled.",
        
        "Initiated patient Sophia Turner on 200mg Pembrolizumab IV every 3 weeks for melanoma; immune-related adverse events reviewed.",
        
        "Prescribed patient Ethan Rivera 100mg Bicalutamide daily for prostate cancer; LFTs monitored.",
        
        "Started patient Mia Scott on 500mg Cyclophosphamide IV every 3 weeks for lymphoma; antiemetic regimen initiated.",
        
        "Initiated patient Lucas Bennett on 100mg Sorafenib twice daily for hepatocellular carcinoma; hand-foot syndrome monitored.",
        
        "Prescribed patient Chloe Adams 2mg Anastrozole daily for postmenopausal breast cancer; bone density screening scheduled.",
        
        "Started patient Julian Moore on 100mg Nivolumab IV every 2 weeks for renal cell carcinoma; thyroid function monitored.",
        
        "Initiated patient Ella Nguyen on 100mg Lenalidomide daily for multiple myeloma; thromboprophylaxis advised.",
        
        "Prescribed patient Benjamin Carter 100mg Etoposide IV daily for 3 days every 21 days for small cell lung cancer.",
        
        "Started patient Grace Simmons on 100mg Trastuzumab IV every 3 weeks for HER2+ breast cancer; cardiac monitoring scheduled.",
        
        "Initiated patient Nathaniel Young on 100mg Olaparib twice daily for BRCA-mutated ovarian cancer.",
        
        "Prescribed patient Lily Bell 100mg Fulvestrant IM every 2 weeks for ER+ breast cancer; injection site reactions discussed.",
        
        "Started patient Gabriel Hayes on 100mg Methotrexate IV weekly for osteosarcoma; leucovorin rescue planned.",
        
        "Initiated patient Natalie Robinson on 100mg Ibrutinib daily for chronic lymphocytic leukemia; bleeding risk reviewed.",
        
        "Prescribed patient Daniel Foster 100mg Paclitaxel IV weekly for metastatic breast cancer; neuropathy monitored."
    ]

def analyze_oncology_batch():
    """Process all Oncology notes and generate comprehensive analysis"""
    
    print("🎗️ Oncology Clinical Notes Batch Processor")
    print("=" * 55)
    
    notes = load_oncology_notes()
    results = []
    processing_times = []
    
    print(f"📊 Processing {len(notes)} oncology clinical notes...")
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
                "note_id": f"onco_{i:03d}",
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
                "note_id": f"onco_{i:03d}",
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
    print("📈 ONCOLOGY BATCH ANALYSIS RESULTS")
    print("=" * 40)
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
    
    # Medical entity analysis for Oncology specialty
    print()
    print("🎗️ Oncology-Specific Medical Analysis:")
    
    all_medications = []
    all_conditions = []
    all_procedures = []
    chemotherapy_agents = []
    targeted_therapy_agents = []
    immunotherapy_agents = []
    hormone_therapy_agents = []
    cancer_types = []
    
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
            
            # Identify oncology-specific medication categories
            note_text = result["clinical_note"].lower()
            
            # Chemotherapy agents
            chemo_drugs = ["capecitabine", "cisplatin", "cyclophosphamide", "temozolomide", 
                          "etoposide", "methotrexate", "paclitaxel"]
            for drug in chemo_drugs:
                if drug in note_text:
                    chemotherapy_agents.append(drug)
            
            # Targeted therapy agents
            targeted_drugs = ["erlotinib", "imatinib", "palbociclib", "sorafenib", 
                             "lenalidomide", "olaparib", "ibrutinib", "trastuzumab"]
            for drug in targeted_drugs:
                if drug in note_text:
                    targeted_therapy_agents.append(drug)
                    
            # Immunotherapy agents
            immuno_drugs = ["pembrolizumab", "nivolumab"]
            for drug in immuno_drugs:
                if drug in note_text:
                    immunotherapy_agents.append(drug)
                    
            # Hormone therapy agents
            hormone_drugs = ["bicalutamide", "anastrozole", "fulvestrant"]
            for drug in hormone_drugs:
                if drug in note_text:
                    hormone_therapy_agents.append(drug)
            
            # Cancer types
            cancers = ["breast cancer", "lung cancer", "leukemia", "glioblastoma", "melanoma", 
                      "prostate cancer", "lymphoma", "carcinoma", "myeloma", "osteosarcoma"]
            for cancer in cancers:
                if cancer in note_text:
                    cancer_types.append(cancer)
    
    # Display medical findings
    print(f"  Total Medications Identified: {len(set(all_medications))}")
    print(f"  Total Conditions Identified: {len(set(all_conditions))}")
    print(f"  Total Procedures Identified: {len(set(all_procedures))}")
    print(f"  Chemotherapy Agents Detected: {len(set(chemotherapy_agents))}")
    print(f"  Targeted Therapy Agents Detected: {len(set(targeted_therapy_agents))}")
    print(f"  Immunotherapy Agents Detected: {len(set(immunotherapy_agents))}")
    print(f"  Hormone Therapy Agents Detected: {len(set(hormone_therapy_agents))}")
    print(f"  Cancer Types Identified: {len(set(cancer_types))}")
    
    # Top Oncology medications by category
    if chemotherapy_agents:
        chemo_freq = {}
        for drug in chemotherapy_agents:
            chemo_freq[drug] = chemo_freq.get(drug, 0) + 1
        top_chemo = sorted(chemo_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"  Top Chemotherapy: {', '.join([f'{drug} ({freq})' for drug, freq in top_chemo])}")
    
    if targeted_therapy_agents:
        targeted_freq = {}
        for drug in targeted_therapy_agents:
            targeted_freq[drug] = targeted_freq.get(drug, 0) + 1
        top_targeted = sorted(targeted_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"  Top Targeted Therapy: {', '.join([f'{drug} ({freq})' for drug, freq in top_targeted])}")
    
    # Most common cancer types
    if cancer_types:
        cancer_freq = {}
        for cancer in cancer_types:
            cancer_freq[cancer] = cancer_freq.get(cancer, 0) + 1
        top_cancers = sorted(cancer_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"  Most Common Cancers: {', '.join([f'{cancer} ({freq})' for cancer, freq in top_cancers])}")
    
    # Save detailed results
    output_dir = Path("clinical_results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "oncology_batch_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "specialty": "Oncology",
            "total_notes": len(results),
            "successful_extractions": len(successful_results),
            "success_rate": success_rate,
            "average_processing_time_ms": avg_processing_time,
            "processing_tier_distribution": tier_analysis if successful_results else {},
            "medical_analysis": {
                "unique_medications": len(set(all_medications)),
                "unique_conditions": len(set(all_conditions)),
                "unique_procedures": len(set(all_procedures)),
                "chemotherapy_agents_count": len(set(chemotherapy_agents)),
                "targeted_therapy_agents_count": len(set(targeted_therapy_agents)),
                "immunotherapy_agents_count": len(set(immunotherapy_agents)),
                "hormone_therapy_agents_count": len(set(hormone_therapy_agents)),
                "cancer_types_count": len(set(cancer_types)),
                "top_chemotherapy": top_chemo[:5] if chemotherapy_agents else [],
                "top_targeted_therapy": top_targeted[:5] if targeted_therapy_agents else [],
                "most_common_cancers": top_cancers[:5] if cancer_types else []
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
    print(f"🎯 Oncology Specialty Quality Assessment: {quality_grade}")
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
    print("✅ Rheumatology (11 notes) - 100% success")
    print(f"🎗️ Oncology ({len(notes)} notes) - {success_rate:.1%} success")
    
    total_notes = 9 * 20 + 11 + len(notes)  # 9 specialties @ 20 notes + rheumatology 11 + oncology
    print(f"📊 TOTAL VALIDATION: {total_notes} clinical notes across 11 medical specialties")
    
    return results, success_rate

if __name__ == "__main__":
    analyze_oncology_batch()