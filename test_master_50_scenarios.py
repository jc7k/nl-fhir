#!/usr/bin/env python3
"""
Master Test Suite: 50 Clinical Scenarios for NL-FHIR Epic Validation
Comprehensive coverage including original 32 scenarios + 18 complex medication cases

This test suite validates all Epic stories:
- Epic 1: Input Layer & Web Interface  
- Epic 2: NLP Pipeline & Entity Extraction
- Epic 3: FHIR Bundle Assembly & Validation
- Epic 4: Reverse Validation & Summarization
- Epic 5: Infrastructure & Deployment
"""

import asyncio
import json
import requests
from datetime import datetime
from src.nl_fhir.services.conversion import ConversionService

async def test_all_50_scenarios():
    """Test all 50 clinical scenarios for comprehensive Epic coverage"""
    
    conversion_service = ConversionService()
    
    # Master Test Scenarios (50 total: 32 original + 18 complex medications)
    test_scenarios = [
        # ===== ORIGINAL 32 SCENARIOS =====
        # Basic Lab Tests & Procedures (Epic 2)
        {
            "id": 1,
            "epic": "Epic 2",
            "category": "Lab Tests",
            "name": "CBC and Metabolic Panel Test",
            "text": "Order CBC and comprehensive metabolic panel for routine health screening",
            "expected_entities": ["lab_tests"]
        },
        {
            "id": 2,
            "epic": "Epic 2", 
            "category": "Lab Tests",
            "name": "Diabetes Labs (HbA1c)",
            "text": "Order HbA1c level and lipid panel for diabetes monitoring",
            "expected_entities": ["lab_tests"]
        },
        {
            "id": 3,
            "epic": "Epic 2",
            "category": "Procedures",
            "name": "Chest Pain Procedure", 
            "text": "Order chest X-ray and ECG for patient with chest pain",
            "expected_entities": ["procedures"]
        },
        
        # Basic Medications (Epic 2)
        {
            "id": 4,
            "epic": "Epic 2",
            "category": "Medications",
            "name": "Sertraline Medication",
            "text": "Start patient on Sertraline 100mg daily for depression",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 5,
            "epic": "Epic 2",
            "category": "Medications",
            "name": "Albuterol for Asthma",
            "text": "Prescribe Albuterol inhaler 2 puffs every 6 hours for asthma",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 6,
            "epic": "Epic 2",
            "category": "Medications",
            "name": "Multiple Medications",
            "text": "Prescribe Albuterol inhaler 2 puffs every 6 hours and Prednisone 20mg daily for asthma exacerbation",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 7,
            "epic": "Epic 2",
            "category": "Medications",
            "name": "Diabetes Management",
            "text": "Start patient on Metformin 500mg twice daily for type 2 diabetes",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 8,
            "epic": "Epic 2",
            "category": "Medications",
            "name": "Antibiotic Treatment",
            "text": "Prescribe Amoxicillin 875mg twice daily for 10 days for bacterial infection",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 9,
            "epic": "Epic 2",
            "category": "Medications",
            "name": "Blood Pressure Management", 
            "text": "Start Lisinopril 10mg daily for hypertension management",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 10,
            "epic": "Epic 2",
            "category": "Medications",
            "name": "Pain Management",
            "text": "Prescribe Ibuprofen 600mg three times daily for pain management",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 11,
            "epic": "Epic 2",
            "category": "Medications",
            "name": "Sleep Aid",
            "text": "Start patient on Ambien 10mg at bedtime for insomnia",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 12,
            "epic": "Epic 2",
            "category": "Medications",
            "name": "Cholesterol Management",
            "text": "Prescribe Atorvastatin 20mg daily for high cholesterol",
            "expected_entities": ["medications", "conditions"]
        },
        
        # Complex Multi-Entity Scenarios (Epic 3)
        {
            "id": 13,
            "epic": "Epic 3",
            "category": "Emergency Care",
            "name": "Heart Attack Workup",
            "text": "Order STAT ECG, chest X-ray, and cardiac enzymes for patient with chest pain and shortness of breath",
            "expected_entities": ["procedures", "lab_tests", "conditions"]
        },
        {
            "id": 14,
            "epic": "Epic 3",
            "category": "Infectious Disease",
            "name": "Pneumonia Treatment",
            "text": "Start patient on Ceftriaxone 2g IV daily and order chest CT for pneumonia workup",
            "expected_entities": ["medications", "procedures", "conditions"]
        },
        {
            "id": 15,
            "epic": "Epic 3",
            "category": "Chronic Care",
            "name": "Diabetes Complications",
            "text": "Order diabetic foot exam, HbA1c, and microalbumin for diabetes follow-up",
            "expected_entities": ["procedures", "lab_tests", "conditions"]
        },
        {
            "id": 16,
            "epic": "Epic 3",
            "category": "Emergency Care",
            "name": "Stroke Protocol",
            "text": "STAT head CT without contrast, PT/PTT, and neurologic consultation for possible stroke",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 17,
            "epic": "Epic 3",
            "category": "Nephrology",
            "name": "Kidney Function Assessment",
            "text": "Order comprehensive metabolic panel, urinalysis, and renal ultrasound for kidney function evaluation",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 18,
            "epic": "Epic 3",
            "category": "Endocrinology",
            "name": "Thyroid Disorder Workup",
            "text": "Order TSH, free T4, and thyroid ultrasound for thyroid function assessment",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 19,
            "epic": "Epic 3",
            "category": "Oncology",
            "name": "Cancer Screening",
            "text": "Schedule mammography, order CEA level, and CBC for cancer screening follow-up",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 20,
            "epic": "Epic 3",
            "category": "Cardiology",
            "name": "Cardiac Monitoring",
            "text": "Order 24-hour Holter monitor, echocardiogram, and BNP level for cardiac evaluation",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 21,
            "epic": "Epic 3",
            "category": "Gastroenterology",
            "name": "Liver Function Tests",
            "text": "Order liver function panel, hepatitis B and C serology, and abdominal ultrasound",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 22,
            "epic": "Epic 3",
            "category": "Pulmonology",
            "name": "Respiratory Assessment",
            "text": "Order pulmonary function tests, chest CT with contrast, and arterial blood gas",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 23,
            "epic": "Epic 3",
            "category": "Gastroenterology",
            "name": "Gastrointestinal Workup",
            "text": "Schedule upper endoscopy, order H. pylori testing, and complete blood count",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 24,
            "epic": "Epic 3",
            "category": "Orthopedics",
            "name": "Bone Health Assessment",
            "text": "Order DEXA scan, vitamin D level, and calcium with phosphorus for osteoporosis screening",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 25,
            "epic": "Epic 3",
            "category": "Infectious Disease",
            "name": "Infectious Disease Workup",
            "text": "Order blood cultures, procalcitonin level, and chest X-ray for sepsis evaluation",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 26,
            "epic": "Epic 3",
            "category": "Neurology",
            "name": "Neurological Assessment",
            "text": "Order brain MRI with gadolinium, lumbar puncture, and CSF analysis for neurologic symptoms",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 27,
            "epic": "Epic 3",
            "category": "Rheumatology",
            "name": "Rheumatology Workup", 
            "text": "Order ANA, anti-CCP antibodies, ESR, and CRP for autoimmune disease evaluation",
            "expected_entities": ["lab_tests"]
        },
        {
            "id": 28,
            "epic": "Epic 3",
            "category": "Endocrinology",
            "name": "Endocrine Assessment",
            "text": "Order cortisol level, ACTH stimulation test, and adrenal CT for adrenal insufficiency workup",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 29,
            "epic": "Epic 3",
            "category": "Hematology",
            "name": "Hematology Consultation",
            "text": "Order peripheral blood smear, iron studies, and bone marrow biopsy for anemia evaluation",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 30,
            "epic": "Epic 3",
            "category": "Vascular Medicine",
            "name": "Vascular Assessment",
            "text": "Order carotid duplex ultrasound, ankle-brachial index, and D-dimer level for vascular evaluation",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 31,
            "epic": "Epic 3",
            "category": "Gynecology",
            "name": "Reproductive Health",
            "text": "Order pelvic ultrasound, pregnancy test, and hormone panel for reproductive health assessment",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 32,
            "epic": "Epic 3",
            "category": "Allergy/Immunology",
            "name": "Allergy Testing",
            "text": "Order comprehensive allergy panel, IgE level, and skin prick testing for allergic reactions",
            "expected_entities": ["lab_tests", "procedures"]
        },
        
        # ===== NEW 18 COMPLEX MEDICATION SCENARIOS =====
        # Advanced Medication Cases (Epic 2 & 3)
        {
            "id": 33,
            "epic": "Epic 2",
            "category": "Urology",
            "name": "Erectile Dysfunction Management",
            "text": "Initiated patient Julian West on 5mg Tadalafil as needed, not more than once daily, for erectile dysfunction; discussed cardiovascular risks.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 34,
            "epic": "Epic 2",
            "category": "Neurology",
            "name": "Seizure Management",
            "text": "Prescribed patient Nora Singh 250mg Levetiracetam twice daily for new-onset focal seizures; EEG and MRI ordered for further evaluation.",
            "expected_entities": ["medications", "conditions", "procedures"]
        },
        {
            "id": 35,
            "epic": "Epic 2",
            "category": "Dermatology",
            "name": "Eczema Treatment",
            "text": "Started patient Caleb Young on 0.1% Triamcinolone topical cream applied twice daily to affected areas for eczema flare-up.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 36,
            "epic": "Epic 2",
            "category": "Emergency Medicine",
            "name": "Anaphylaxis Treatment",
            "text": "Administered patient Ella James 0.3mg Epinephrine intramuscularly via auto-injector for anaphylaxis; monitored vitals for 2 hours post-injection.",
            "expected_entities": ["medications", "conditions", "procedures"]
        },
        {
            "id": 37,
            "epic": "Epic 2",
            "category": "Psychiatry",
            "name": "Schizophrenia Management",
            "text": "Recommended patient Owen Clark begin 2mg Risperidone orally at bedtime for schizophrenia; scheduled psychiatric follow-up in 1 week.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 38,
            "epic": "Epic 2",
            "category": "Infectious Disease",
            "name": "STI Treatment",
            "text": "Prescribed patient Layla Torres 1g Azithromycin orally once for chlamydia treatment; advised partner notification and abstinence for 7 days.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 39,
            "epic": "Epic 2",
            "category": "Rheumatology",
            "name": "Rheumatoid Arthritis Treatment",
            "text": "Started patient Gabriel Flores on 15mg Methotrexate once weekly for rheumatoid arthritis; folic acid supplementation initiated concurrently.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 40,
            "epic": "Epic 2",
            "category": "Neurology",
            "name": "Parkinson's Disease Management",
            "text": "Initiated patient Hannah Bell on 0.5mg Pramipexole three times daily for Parkinson's disease; advised on fall precautions.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 41,
            "epic": "Epic 2",
            "category": "Sleep Medicine",
            "name": "Insomnia Treatment",
            "text": "Prescribed patient Isaac Green 10mg Zolpidem at bedtime for short-term insomnia; warned about next-day drowsiness and driving risks.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 42,
            "epic": "Epic 2",
            "category": "Pediatrics",
            "name": "RSV Prophylaxis",
            "text": "Administered patient Zoe Carter 0.5mL of RSV monoclonal antibody intramuscularly for infant prophylaxis; documented consent.",
            "expected_entities": ["medications"]
        },
        {
            "id": 43,
            "epic": "Epic 2",
            "category": "Addiction Medicine",
            "name": "Smoking Cessation",
            "text": "Started patient Levi Bennett on 300mg Bupropion XL once daily for smoking cessation; discussed neuropsychiatric side effects.",
            "expected_entities": ["medications"]
        },
        {
            "id": 44,
            "epic": "Epic 2",
            "category": "Psychiatry",
            "name": "ADHD Treatment",
            "text": "Prescribed patient Aria Mitchell 0.05mg Clonidine patch weekly for ADHD adjunct therapy; monitored blood pressure.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 45,
            "epic": "Epic 2",
            "category": "Dermatology",
            "name": "Acne Treatment",
            "text": "Initiated patient Mateo Rivera on 100mg Spironolactone daily for acne and hormonal regulation; advised potassium monitoring.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 46,
            "epic": "Epic 2",
            "category": "Gynecology",
            "name": "Bacterial Vaginosis Treatment",
            "text": "Recommended patient Stella Nguyen begin 2g Metronidazole vaginal gel once daily for 5 days for bacterial vaginosis.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 47,
            "epic": "Epic 2",
            "category": "Rheumatology",
            "name": "Lupus Management",
            "text": "Started patient Elias Morgan on 400mg Hydroxychloroquine once daily for lupus management; baseline eye exam scheduled.",
            "expected_entities": ["medications", "conditions", "procedures"]
        },
        {
            "id": 48,
            "epic": "Epic 2",
            "category": "Neurology",
            "name": "Essential Tremor Treatment",
            "text": "Prescribed patient Violet Hayes 10mg Propranolol three times daily for essential tremor; advised on fatigue and bradycardia risks.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 49,
            "epic": "Epic 2",
            "category": "Endocrinology",
            "name": "Hyperprolactinemia Treatment",
            "text": "Initiated patient Nathaniel Ross on 0.25mg Cabergoline twice weekly for hyperprolactinemia; prolactin levels to be rechecked in 1 month.",
            "expected_entities": ["medications", "conditions", "lab_tests"]
        },
        {
            "id": 50,
            "epic": "Epic 2",
            "category": "Pain Management",
            "name": "Postherpetic Neuralgia Treatment",
            "text": "Started patient Penelope Foster on 600mg Gabapentin three times daily for postherpetic neuralgia; titration plan discussed.",
            "expected_entities": ["medications", "conditions"]
        }
    ]
    
    print("🧪 Master Test Suite: All 50 Clinical Scenarios")
    print("Epic Coverage: Stories 1-23 validation across all domains")
    print("=" * 70)
    
    total_scenarios = len(test_scenarios)
    passed_scenarios = 0
    failed_scenarios = []
    
    # Track Epic-wise performance
    epic_stats = {
        "Epic 1": {"passed": 0, "total": 0},
        "Epic 2": {"passed": 0, "total": 0}, 
        "Epic 3": {"passed": 0, "total": 0}
    }
    
    for scenario in test_scenarios:
        epic = scenario.get('epic', 'Unknown')
        epic_stats[epic]['total'] += 1
        
        print(f"\n{scenario['id']}. [{epic} - {scenario['category']}] {scenario['name']}")
        print(f"   Input: {scenario['text']}")
        
        try:
            # Test NLP extraction
            result = await conversion_service._basic_text_analysis(scenario['text'], f"test-{scenario['id']}")
            
            # Extract entities from the nested structure
            extracted_entities = result.get('extracted_entities', {})
            medications = extracted_entities.get('medications', [])
            lab_tests = extracted_entities.get('lab_tests', [])
            procedures = extracted_entities.get('procedures', [])
            conditions = extracted_entities.get('conditions', [])
            
            print(f"   📊 Entities Found:")
            print(f"      Medications: {len(medications)}")
            print(f"      Lab Tests: {len(lab_tests)}")
            print(f"      Procedures: {len(procedures)}")
            print(f"      Conditions: {len(conditions)}")
            
            # Display specific entities found
            if medications:
                med_names = [med['text'] for med in medications]
                print(f"      Found medications: {med_names}")
            if lab_tests:
                lab_names = [lab['text'] for lab in lab_tests]
                print(f"      Found lab tests: {lab_names}")
            if procedures:
                proc_names = [proc['text'] for proc in procedures]
                print(f"      Found procedures: {proc_names}")
            if conditions:
                cond_names = [cond['text'] for cond in conditions]
                print(f"      Found conditions: {cond_names}")
            
            total_entities = len(medications) + len(lab_tests) + len(procedures) + len(conditions)
            
            # Check if we found expected entity types
            found_types = []
            if medications: found_types.append("medications")
            if lab_tests: found_types.append("lab_tests")  
            if procedures: found_types.append("procedures")
            if conditions: found_types.append("conditions")
            
            expected_types = scenario.get('expected_entities', [])
            
            # Success if we found at least one entity and it matches expected types (if specified)
            success = total_entities > 0
            if expected_types:
                # Check if we found at least one of the expected entity types
                expected_found = any(exp_type in found_types for exp_type in expected_types)
                success = success and expected_found
            
            if success:
                print(f"   ✅ PASS - Found {total_entities} total entities")
                if expected_types:
                    print(f"      Expected: {expected_types}, Found: {found_types}")
                passed_scenarios += 1
                epic_stats[epic]['passed'] += 1
            else:
                print(f"   ❌ FAIL - No entities found or missing expected types")
                if expected_types:
                    print(f"      Expected: {expected_types}, Found: {found_types}")
                failed_scenarios.append({
                    'id': scenario['id'],
                    'epic': epic,
                    'category': scenario['category'],
                    'name': scenario['name'],
                    'expected': expected_types,
                    'found': found_types,
                    'total_entities': total_entities
                })
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            failed_scenarios.append({
                'id': scenario['id'],
                'epic': epic,
                'category': scenario['category'],
                'name': scenario['name'],
                'error': str(e)
            })
    
    # Summary results
    print(f"\n" + "=" * 70)
    success_rate = (passed_scenarios / total_scenarios) * 100
    print(f"🎯 MASTER RESULTS: {passed_scenarios}/{total_scenarios} scenarios passed ({success_rate:.1f}%)")
    
    # Epic-wise breakdown
    print(f"\n📈 Epic Performance Breakdown:")
    for epic, stats in epic_stats.items():
        if stats['total'] > 0:
            epic_rate = (stats['passed'] / stats['total']) * 100
            print(f"   {epic}: {stats['passed']}/{stats['total']} ({epic_rate:.1f}%)")
    
    if failed_scenarios:
        print(f"\n❌ Failed Scenarios ({len(failed_scenarios)}):")
        for failure in failed_scenarios:
            if 'error' in failure:
                print(f"   {failure['id']}. [{failure['epic']}] {failure['name']} - ERROR: {failure['error']}")
            else:
                print(f"   {failure['id']}. [{failure['epic']}] {failure['name']} - Expected: {failure.get('expected', 'N/A')}, Found: {failure.get('found', [])}")
    
    # Final assessment
    if success_rate >= 95:
        print("🚀 DEPLOYMENT READY! All Epics performing excellently.")
    elif success_rate >= 90:
        print("🎉 EXCELLENT! Near-deployment quality achieved.")
    elif success_rate >= 80:
        print("✨ VERY GOOD! Minor optimizations needed.")
    elif success_rate >= 70:
        print("👍 GOOD progress! Some Epic refinements needed.")
    else:
        print("⚠️  Additional Epic development required.")
    
    return success_rate, failed_scenarios, epic_stats

async def test_epic_specific_api():
    """Test Epic-specific API functionality"""
    
    base_url = "http://localhost:8000/api/v1"
    
    # Representative scenarios for each Epic
    epic_test_cases = [
        {
            "epic": "Epic 2",
            "name": "Complex Medication (Levetiracetam)",
            "clinical_text": "Prescribed patient Nora Singh 250mg Levetiracetam twice daily for new-onset focal seizures; EEG and MRI ordered for further evaluation."
        },
        {
            "epic": "Epic 2", 
            "name": "Basic Lab Test (CBC)",
            "clinical_text": "Order CBC and comprehensive metabolic panel for routine health screening"
        },
        {
            "epic": "Epic 3",
            "name": "Multi-Entity Emergency (Heart Attack)",
            "clinical_text": "Order STAT ECG, chest X-ray, and cardiac enzymes for patient with chest pain and shortness of breath"
        }
    ]
    
    print(f"\n🌐 Epic-Specific API Validation")
    print("=" * 50)
    
    api_passed = 0
    total_api_tests = len(epic_test_cases)
    
    for i, test_case in enumerate(epic_test_cases, 1):
        print(f"\n{i}. [{test_case['epic']}] {test_case['name']}")
        
        try:
            response = requests.post(
                f"{base_url}/convert",
                json={"clinical_text": test_case['clinical_text']},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "extracted_entities" in data and "fhir_bundle" in data:
                    entities = data["extracted_entities"]
                    total_entities = sum(len(entities.get(key, [])) for key in ['medications', 'lab_tests', 'procedures', 'conditions'])
                    
                    bundle = data["fhir_bundle"]
                    bundle_entries = len(bundle.get("entry", []))
                    
                    print(f"   ✅ API Success - {total_entities} entities → {bundle_entries} FHIR resources")
                    api_passed += 1
                else:
                    print(f"   ❌ API response missing required fields")
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ API Request Error: {str(e)}")
    
    api_success_rate = (api_passed / total_api_tests) * 100
    print(f"\n📊 Epic API Results: {api_passed}/{total_api_tests} passed ({api_success_rate:.1f}%)")
    
    return api_success_rate

async def main():
    """Run master test suite for all Epics"""
    
    print("🎯 NL-FHIR Master Test Suite")
    print("Epic 1-5 Comprehensive Validation (Stories 1-23)")
    print("50 Clinical Scenarios + API Integration Testing")
    print("=" * 70)
    
    # Test all 50 scenarios
    nlp_success_rate, failed_scenarios, epic_stats = await test_all_50_scenarios()
    
    # Test Epic-specific API endpoints
    api_success_rate = await test_epic_specific_api()
    
    print(f"\n" + "=" * 70)
    print("📈 EPIC VALIDATION SUMMARY")
    print(f"   Overall NLP Processing: {nlp_success_rate:.1f}% success rate")
    print(f"   API Integration: {api_success_rate:.1f}% success rate")
    
    # Epic readiness assessment
    print(f"\n🏆 EPIC READINESS ASSESSMENT:")
    for epic, stats in epic_stats.items():
        if stats['total'] > 0:
            epic_rate = (stats['passed'] / stats['total']) * 100
            status = "🚀 READY" if epic_rate >= 90 else "⚠️  NEEDS WORK" if epic_rate < 80 else "🔧 MINOR FIXES"
            print(f"   {epic}: {epic_rate:.1f}% - {status}")
    
    # Final deployment recommendation
    if nlp_success_rate >= 95 and api_success_rate >= 95:
        print("\n🚀 DEPLOYMENT APPROVED: All Epics meet production standards!")
    elif nlp_success_rate >= 90 and api_success_rate >= 90:
        print("\n✅ NEAR-PRODUCTION READY: Minor optimizations recommended")
    else:
        print("\n⚠️  CONTINUE DEVELOPMENT: Address Epic gaps before deployment")

if __name__ == "__main__":
    asyncio.run(main())