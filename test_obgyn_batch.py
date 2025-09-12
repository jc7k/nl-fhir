#!/usr/bin/env python3
"""
OB/GYN Clinical Notes Batch Processor
Processes 20 obstetrics and gynecology clinical notes to validate NLP system performance
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

def load_obgyn_notes():
    """Load OB/GYN clinical notes for processing"""
    return [
        "Patient presents for routine prenatal visit at 32 weeks gestation. Fundal height appropriate for gestational age. Fetal heart rate 140 bpm. Blood pressure 120/80. Urine dipstick negative for protein and glucose. Continue prenatal vitamins and schedule next visit in 2 weeks.",
        
        "28-year-old G2P1 at 39 weeks gestation presents in active labor. Cervix 6 cm dilated, 100% effaced, station 0. Membranes intact. Fetal heart rate tracing reassuring. Pain managed with epidural anesthesia. Plan for vaginal delivery.",
        
        "Postpartum day 2 following uncomplicated vaginal delivery. Lochia rubra, moderate amount. Uterus firm, fundal height at umbilicus. Perineal laceration healing well. Breastfeeding established. Patient ambulating without difficulty. Discharge home with newborn.",
        
        "46-year-old woman presents with irregular menstrual cycles and hot flashes. Last menstrual period 3 months ago. FSH 42 IU/L, estradiol 15 pg/mL consistent with menopause. Discussed hormone replacement therapy options. Prescribed calcium and vitamin D supplementation.",
        
        "Annual gynecologic exam for 35-year-old woman. Pap smear normal, HPV negative. Breast exam unremarkable. Discussed contraception options. Patient desires IUD placement. Scheduled for Mirena IUD insertion next week.",
        
        "24-year-old nulligravid woman presents with severe dysmenorrhea and heavy menstrual bleeding. Pelvic exam reveals enlarged, tender uterus. Transvaginal ultrasound shows multiple uterine fibroids. Started on hormonal therapy. Surgery consult arranged.",
        
        "First prenatal visit for 26-year-old G1P0 at 8 weeks gestation by LMP. Vital signs stable. Pelvic exam normal. Labs ordered: CBC, blood type, Rh, rubella, hepatitis B, HIV, syphilis. Prescribed prenatal vitamins with folic acid. Discussed lifestyle modifications.",
        
        "Routine gynecologic visit for 52-year-old woman. Chief complaint of vaginal dryness and painful intercourse since menopause. Pelvic exam reveals vaginal atrophy. Prescribed vaginal estrogen cream. Discussed benefits and risks of local hormone therapy.",
        
        "20-week anatomy ultrasound for 30-year-old G3P2 shows normal fetal growth and development. All anatomical structures appear normal. Placenta anterior, not previa. Amniotic fluid volume normal. Gender revealed as requested. Next visit in 4 weeks.",
        
        "34-year-old woman at 36 weeks gestation presents with contractions every 5 minutes for 2 hours. Cervix 3 cm dilated, 75% effaced. Fetal heart rate reactive. Group B strep positive - antibiotics initiated. Admitted for labor management.",
        
        "Postmenopausal bleeding evaluation for 58-year-old woman. Endometrial biopsy shows complex hyperplasia without atypia. Transvaginal ultrasound reveals thickened endometrium 12 mm. Started on progestin therapy. Follow-up biopsy in 6 months.",
        
        "Annual well-woman exam for 29-year-old. Normal Pap smear, breast exam unremarkable. Patient reports regular 28-day cycles. Currently using barrier contraception. Discussed reproductive health and preconception counseling for future pregnancy planning.",
        
        "Emergency department consultation for 22-year-old woman with severe pelvic pain and positive pregnancy test. Transvaginal ultrasound shows empty uterus, free fluid in pelvis. Beta-hCG 1200. Diagnosis: ruptured ectopic pregnancy. Emergency laparoscopy performed.",
        
        "6-week postpartum visit following cesarean delivery. Incision healing well, no signs of infection. Lochia alba, minimal amount. Breastfeeding going well. Cleared for normal activities and driving. Contraception counseled, patient chose depot medroxyprogesterone.",
        
        "41-year-old G4P3 at 18 weeks gestation for genetic counseling visit. Advanced maternal age discussed. Amniocentesis offered but declined. Cell-free DNA screening normal. Detailed ultrasound scheduled at 20 weeks. Continue routine prenatal care.",
        
        "Adolescent gynecology visit for 16-year-old with primary amenorrhea. Physical exam shows normal secondary sexual characteristics. Pelvic ultrasound normal uterus and ovaries. Labs: FSH, LH, prolactin, thyroid function normal. Reassurance provided, follow-up in 6 months.",
        
        "High-risk pregnancy consultation for 33-year-old with gestational diabetes. Glucose tolerance test: fasting 95, 1-hour 185, 2-hour 165. Started on diabetic diet and glucose monitoring. Nutrition consultation scheduled. Weekly biophysical profiles to begin at 32 weeks.",
        
        "Preoperative visit for 38-year-old woman scheduled for laparoscopic hysterectomy for symptomatic uterine fibroids. Medical clearance obtained. Discussed surgical risks and benefits. Alternative treatments reviewed. Patient counseled on postoperative recovery expectations.",
        
        "Fertility consultation for 31-year-old couple trying to conceive for 18 months. Semen analysis normal. HSG shows patent fallopian tubes. Ovulation confirmed with progesterone levels. Started clomiphene citrate 50mg days 5-9. Monitor follicle development with ultrasound.",
        
        "Emergency gynecology consult for 25-year-old woman with severe pelvic inflammatory disease. Cervical motion tenderness, bilateral adnexal tenderness. Elevated WBC, CRP. Started IV antibiotics ceftriaxone and doxycycline. Partner treatment arranged. STI counseling provided."
    ]

def analyze_obgyn_batch():
    """Process all OB/GYN notes and generate comprehensive analysis"""
    
    print("🏥 OB/GYN Clinical Notes Batch Processor")
    print("=" * 60)
    
    notes = load_obgyn_notes()
    results = []
    processing_times = []
    
    print(f"📊 Processing {len(notes)} obstetrics and gynecology clinical notes...")
    print()
    
    for i, note in enumerate(notes, 1):
        print(f"Processing note {i}/20...", end=" ")
        
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
                "note_id": f"obgyn_{i:03d}",
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
                "note_id": f"obgyn_{i:03d}",
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
    print("📈 OB/GYN BATCH ANALYSIS RESULTS")
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
    
    # Medical entity analysis for OB/GYN specialty
    print()
    print("🏥 OB/GYN-Specific Medical Analysis:")
    
    all_medications = []
    all_conditions = []
    all_procedures = []
    obstetric_terms = []
    gynecologic_terms = []
    
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
            
            # Identify OB/GYN-specific terms
            note_text = result["clinical_note"].lower()
            
            # Obstetric terms
            ob_terms = ["prenatal", "gestation", "pregnancy", "labor", "delivery", "postpartum", 
                       "fetal", "cervix", "contractions", "epidural", "cesarean", "vaginal delivery"]
            for term in ob_terms:
                if term in note_text:
                    obstetric_terms.append(term)
            
            # Gynecologic terms  
            gyn_terms = ["menstrual", "pap smear", "hpv", "menopause", "fibroids", "ovarian",
                        "hysterectomy", "iud", "contraception", "pelvic exam", "endometrial"]
            for term in gyn_terms:
                if term in note_text:
                    gynecologic_terms.append(term)
    
    # Display medical findings
    print(f"  Total Medications Identified: {len(set(all_medications))}")
    print(f"  Total Conditions Identified: {len(set(all_conditions))}")
    print(f"  Total Procedures Identified: {len(set(all_procedures))}")
    print(f"  Obstetric Terms Detected: {len(set(obstetric_terms))}")
    print(f"  Gynecologic Terms Detected: {len(set(gynecologic_terms))}")
    
    # Top OB/GYN medications
    if all_medications:
        med_freq = {}
        for med in all_medications:
            med_freq[med] = med_freq.get(med, 0) + 1
        top_meds = sorted(med_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"  Top Medications: {', '.join([f'{med} ({freq})' for med, freq in top_meds])}")
    
    # Save detailed results
    output_dir = Path("clinical_results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "obgyn_batch_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "specialty": "Obstetrics & Gynecology",
            "total_notes": len(results),
            "successful_extractions": len(successful_results),
            "success_rate": success_rate,
            "average_processing_time_ms": avg_processing_time,
            "processing_tier_distribution": tier_analysis if successful_results else {},
            "medical_analysis": {
                "unique_medications": len(set(all_medications)),
                "unique_conditions": len(set(all_conditions)),
                "unique_procedures": len(set(all_procedures)),
                "obstetric_terms_count": len(set(obstetric_terms)),
                "gynecologic_terms_count": len(set(gynecologic_terms)),
                "top_medications": top_meds[:10] if all_medications else []
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
    print(f"🎯 OB/GYN Specialty Quality Assessment: {quality_grade}")
    print(f"📊 Performance Score: {success_rate:.3f}")
    
    return results, success_rate

if __name__ == "__main__":
    analyze_obgyn_batch()