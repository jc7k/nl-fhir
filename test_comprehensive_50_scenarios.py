#!/usr/bin/env python3
"""
Comprehensive test of all 50 clinical scenarios for NL-FHIR conversion
Tests the original 32 scenarios plus 18 additional patient encounter notes to achieve 100% success rate.
"""

import asyncio
import json
import requests
from datetime import datetime
from src.nl_fhir.services.conversion import ConversionService

async def test_all_50_scenarios():
    """Test all 50 clinical scenarios for comprehensive coverage"""
    
    conversion_service = ConversionService()
    
    # All 50 test scenarios (32 original + 18 additional patient encounter notes)
    test_scenarios = [
        # Original 32 scenarios
        {
            "id": 1,
            "name": "CBC and Metabolic Panel Test",
            "text": "Order CBC and comprehensive metabolic panel for routine health screening",
            "expected_entities": ["lab_tests"]
        },
        {
            "id": 2, 
            "name": "Diabetes Labs (HbA1c)",
            "text": "Order HbA1c level and lipid panel for diabetes monitoring",
            "expected_entities": ["lab_tests"]
        },
        {
            "id": 3,
            "name": "Chest Pain Procedure", 
            "text": "Order chest X-ray and ECG for patient with chest pain",
            "expected_entities": ["procedures"]
        },
        {
            "id": 4,
            "name": "Sertraline Medication",
            "text": "Start patient on Sertraline 100mg daily for depression",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 5,
            "name": "Albuterol for Asthma",
            "text": "Prescribe Albuterol inhaler 2 puffs every 6 hours for asthma",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 6,
            "name": "Multiple Medications",
            "text": "Prescribe Albuterol inhaler 2 puffs every 6 hours and Prednisone 20mg daily for asthma exacerbation",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 7,
            "name": "Diabetes Management",
            "text": "Start patient on Metformin 500mg twice daily for type 2 diabetes",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 8,
            "name": "Antibiotic Treatment",
            "text": "Prescribe Amoxicillin 875mg twice daily for 10 days for bacterial infection",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 9,
            "name": "Blood Pressure Management", 
            "text": "Start Lisinopril 10mg daily for hypertension management",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 10,
            "name": "Pain Management",
            "text": "Prescribe Ibuprofen 600mg three times daily for pain management",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 11,
            "name": "Sleep Aid",
            "text": "Start patient on Ambien 10mg at bedtime for insomnia",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 12,
            "name": "Cholesterol Management",
            "text": "Prescribe Atorvastatin 20mg daily for high cholesterol",
            "expected_entities": ["medications", "conditions"]
        },
        
        # Additional 20 scenarios (13-32)
        {
            "id": 13,
            "name": "Heart Attack Workup",
            "text": "Order STAT ECG, chest X-ray, and cardiac enzymes for patient with chest pain and shortness of breath",
            "expected_entities": ["procedures", "lab_tests", "conditions"]
        },
        {
            "id": 14,
            "name": "Pneumonia Treatment",
            "text": "Start patient on Ceftriaxone 2g IV daily and order chest CT for pneumonia workup",
            "expected_entities": ["medications", "procedures", "conditions"]
        },
        {
            "id": 15,
            "name": "Diabetes Complications",
            "text": "Order diabetic foot exam, HbA1c, and microalbumin for diabetes follow-up",
            "expected_entities": ["procedures", "lab_tests", "conditions"]
        },
        {
            "id": 16,
            "name": "Stroke Protocol",
            "text": "STAT head CT without contrast, PT/PTT, and neurologic consultation for possible stroke",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 17,
            "name": "Kidney Function Assessment",
            "text": "Order comprehensive metabolic panel, urinalysis, and renal ultrasound for kidney function evaluation",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 18,
            "name": "Thyroid Disorder Workup",
            "text": "Order TSH, free T4, and thyroid ultrasound for thyroid function assessment",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 19,
            "name": "Cancer Screening",
            "text": "Schedule mammography, order CEA level, and CBC for cancer screening follow-up",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 20,
            "name": "Cardiac Monitoring",
            "text": "Order 24-hour Holter monitor, echocardiogram, and BNP level for cardiac evaluation",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 21,
            "name": "Liver Function Tests",
            "text": "Order liver function panel, hepatitis B and C serology, and abdominal ultrasound",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 22,
            "name": "Respiratory Assessment",
            "text": "Order pulmonary function tests, chest CT with contrast, and arterial blood gas",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 23,
            "name": "Gastrointestinal Workup",
            "text": "Schedule upper endoscopy, order H. pylori testing, and complete blood count",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 24,
            "name": "Bone Health Assessment",
            "text": "Order DEXA scan, vitamin D level, and calcium with phosphorus for osteoporosis screening",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 25,
            "name": "Infectious Disease Workup",
            "text": "Order blood cultures, procalcitonin level, and chest X-ray for sepsis evaluation",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 26,
            "name": "Neurological Assessment",
            "text": "Order brain MRI with gadolinium, lumbar puncture, and CSF analysis for neurologic symptoms",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 27,
            "name": "Rheumatology Workup", 
            "text": "Order ANA, anti-CCP antibodies, ESR, and CRP for autoimmune disease evaluation",
            "expected_entities": ["lab_tests"]
        },
        {
            "id": 28,
            "name": "Endocrine Assessment",
            "text": "Order cortisol level, ACTH stimulation test, and adrenal CT for adrenal insufficiency workup",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 29,
            "name": "Hematology Consultation",
            "text": "Order peripheral blood smear, iron studies, and bone marrow biopsy for anemia evaluation",
            "expected_entities": ["lab_tests", "procedures"]
        },
        {
            "id": 30,
            "name": "Vascular Assessment",
            "text": "Order carotid duplex ultrasound, ankle-brachial index, and D-dimer level for vascular evaluation",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 31,
            "name": "Reproductive Health",
            "text": "Order pelvic ultrasound, pregnancy test, and hormone panel for reproductive health assessment",
            "expected_entities": ["procedures", "lab_tests"]
        },
        {
            "id": 32,
            "name": "Allergy Testing",
            "text": "Order comprehensive allergy panel, IgE level, and skin prick testing for allergic reactions",
            "expected_entities": ["lab_tests", "procedures"]
        },
        
        # New 18 patient encounter notes (33-50)
        {
            "id": 33,
            "name": "Tadalafil for Erectile Dysfunction",
            "text": "Initiated patient Julian West on 5mg Tadalafil as needed, not more than once daily, for erectile dysfunction; discussed cardiovascular risks.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 34,
            "name": "Levetiracetam for Seizures",
            "text": "Prescribed patient Nora Singh 250mg Levetiracetam twice daily for new-onset focal seizures; EEG and MRI ordered for further evaluation.",
            "expected_entities": ["medications", "conditions", "procedures"]
        },
        {
            "id": 35,
            "name": "Triamcinolone for Eczema",
            "text": "Started patient Caleb Young on 0.1% Triamcinolone topical cream applied twice daily to affected areas for eczema flare-up.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 36,
            "name": "Epinephrine for Anaphylaxis",
            "text": "Administered patient Ella James 0.3mg Epinephrine intramuscularly via auto-injector for anaphylaxis; monitored vitals for 2 hours post-injection.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 37,
            "name": "Risperidone for Schizophrenia",
            "text": "Recommended patient Owen Clark begin 2mg Risperidone orally at bedtime for schizophrenia; scheduled psychiatric follow-up in 1 week.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 38,
            "name": "Azithromycin for Chlamydia",
            "text": "Prescribed patient Layla Torres 1g Azithromycin orally once for chlamydia treatment; advised partner notification and abstinence for 7 days.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 39,
            "name": "Methotrexate for Rheumatoid Arthritis",
            "text": "Started patient Gabriel Flores on 15mg Methotrexate once weekly for rheumatoid arthritis; folic acid supplementation initiated concurrently.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 40,
            "name": "Pramipexole for Parkinson's Disease",
            "text": "Initiated patient Hannah Bell on 0.5mg Pramipexole three times daily for Parkinson's disease; advised on fall precautions.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 41,
            "name": "Zolpidem for Insomnia",
            "text": "Prescribed patient Isaac Green 10mg Zolpidem at bedtime for short-term insomnia; warned about next-day drowsiness and driving risks.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 42,
            "name": "RSV Monoclonal Antibody",
            "text": "Administered patient Zoe Carter 0.5mL of RSV monoclonal antibody intramuscularly for infant prophylaxis; documented consent.",
            "expected_entities": ["medications"]
        },
        {
            "id": 43,
            "name": "Bupropion for Smoking Cessation",
            "text": "Started patient Levi Bennett on 300mg Bupropion XL once daily for smoking cessation; discussed neuropsychiatric side effects.",
            "expected_entities": ["medications"]
        },
        {
            "id": 44,
            "name": "Clonidine for ADHD",
            "text": "Prescribed patient Aria Mitchell 0.05mg Clonidine patch weekly for ADHD adjunct therapy; monitored blood pressure.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 45,
            "name": "Spironolactone for Acne",
            "text": "Initiated patient Mateo Rivera on 100mg Spironolactone daily for acne and hormonal regulation; advised potassium monitoring.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 46,
            "name": "Metronidazole for Bacterial Vaginosis",
            "text": "Recommended patient Stella Nguyen begin 2g Metronidazole vaginal gel once daily for 5 days for bacterial vaginosis.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 47,
            "name": "Hydroxychloroquine for Lupus",
            "text": "Started patient Elias Morgan on 400mg Hydroxychloroquine once daily for lupus management; baseline eye exam scheduled.",
            "expected_entities": ["medications", "conditions", "procedures"]
        },
        {
            "id": 48,
            "name": "Propranolol for Essential Tremor",
            "text": "Prescribed patient Violet Hayes 10mg Propranolol three times daily for essential tremor; advised on fatigue and bradycardia risks.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 49,
            "name": "Cabergoline for Hyperprolactinemia",
            "text": "Initiated patient Nathaniel Ross on 0.25mg Cabergoline twice weekly for hyperprolactinemia; prolactin levels to be rechecked in 1 month.",
            "expected_entities": ["medications", "conditions"]
        },
        {
            "id": 50,
            "name": "Gabapentin for Postherpetic Neuralgia",
            "text": "Started patient Penelope Foster on 600mg Gabapentin three times daily for postherpetic neuralgia; titration plan discussed.",
            "expected_entities": ["medications", "conditions"]
        }
    ]
    
    print("🧪 Comprehensive Testing: All 50 Clinical Scenarios")
    print("=" * 60)
    
    total_scenarios = len(test_scenarios)
    passed_scenarios = 0
    failed_scenarios = []
    
    for scenario in test_scenarios:
        print(f"\n{scenario['id']}. Testing: {scenario['name']}")
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
            else:
                print(f"   ❌ FAIL - No entities found or missing expected types")
                if expected_types:
                    print(f"      Expected: {expected_types}, Found: {found_types}")
                failed_scenarios.append({
                    'id': scenario['id'],
                    'name': scenario['name'],
                    'expected': expected_types,
                    'found': found_types,
                    'total_entities': total_entities
                })
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            failed_scenarios.append({
                'id': scenario['id'],
                'name': scenario['name'],
                'error': str(e)
            })
    
    # Summary results
    print(f"\n" + "=" * 60)
    success_rate = (passed_scenarios / total_scenarios) * 100
    print(f"🎯 FINAL RESULTS: {passed_scenarios}/{total_scenarios} scenarios passed ({success_rate:.1f}%)")
    
    if failed_scenarios:
        print(f"\n❌ Failed Scenarios ({len(failed_scenarios)}):")
        for failure in failed_scenarios:
            if 'error' in failure:
                print(f"   {failure['id']}. {failure['name']} - ERROR: {failure['error']}")
            else:
                print(f"   {failure['id']}. {failure['name']} - Expected: {failure.get('expected', 'N/A')}, Found: {failure.get('found', [])}")
    
    if success_rate == 100:
        print("🚀 PERFECT! All 50 scenarios passed! Ready for deployment.")
    elif success_rate >= 95:
        print("🎉 EXCELLENT! Near-perfect success rate achieved.")
    elif success_rate >= 90:
        print("✨ VERY GOOD! Minor improvements may be needed.")
    elif success_rate >= 80:
        print("👍 GOOD progress! Some fixes still needed.")
    else:
        print("⚠️  Additional work required to reach target success rate.")
    
    return success_rate, failed_scenarios

async def test_api_endpoints():
    """Test a subset via API to ensure end-to-end functionality"""
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test key scenarios via API including new patient encounters
    api_test_cases = [
        {
            "name": "CBC and Metabolic Panel (Lab Test)",
            "clinical_text": "Order CBC and comprehensive metabolic panel for routine health screening"
        },
        {
            "name": "Sertraline Medication",  
            "clinical_text": "Start patient on Sertraline 100mg daily for depression"
        },
        {
            "name": "Heart Attack Workup (Complex)",
            "clinical_text": "Order STAT ECG, chest X-ray, and cardiac enzymes for patient with chest pain and shortness of breath"
        },
        {
            "name": "Tadalafil Patient Encounter",
            "clinical_text": "Initiated patient Julian West on 5mg Tadalafil as needed, not more than once daily, for erectile dysfunction; discussed cardiovascular risks."
        },
        {
            "name": "Seizure Medication with Workup",
            "clinical_text": "Prescribed patient Nora Singh 250mg Levetiracetam twice daily for new-onset focal seizures; EEG and MRI ordered for further evaluation."
        }
    ]
    
    print(f"\n🌐 API Endpoint Testing")
    print("=" * 40)
    
    api_passed = 0
    total_api_tests = len(api_test_cases)
    
    for i, test_case in enumerate(api_test_cases, 1):
        print(f"\n{i}. API Test: {test_case['name']}")
        
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
                    
                    print(f"   ✅ API Success - {total_entities} entities, {bundle_entries} FHIR resources")
                    api_passed += 1
                else:
                    print(f"   ❌ API response missing required fields")
            else:
                print(f"   ❌ API Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ API Request Error: {str(e)}")
    
    api_success_rate = (api_passed / total_api_tests) * 100
    print(f"\n📊 API Test Results: {api_passed}/{total_api_tests} passed ({api_success_rate:.1f}%)")
    
    return api_success_rate

async def main():
    """Run comprehensive testing"""
    
    print("🎯 NL-FHIR Comprehensive Testing Suite - 50 Scenarios")
    print("Testing enhanced Instructor-based LLM implementation")
    print("=" * 60)
    
    # Test all 50 scenarios
    nlp_success_rate, failed_scenarios = await test_all_50_scenarios()
    
    # Test API endpoints for end-to-end validation
    api_success_rate = await test_api_endpoints()
    
    print(f"\n" + "=" * 60)
    print("📈 OVERALL SUMMARY")
    print(f"   NLP Processing: {nlp_success_rate:.1f}% success rate")
    print(f"   API Integration: {api_success_rate:.1f}% success rate")
    
    # Final recommendation
    if nlp_success_rate >= 95 and api_success_rate >= 95:
        print("🚀 DEPLOYMENT READY: All systems performing excellently!")
    elif nlp_success_rate >= 90 and api_success_rate >= 90:
        print("✅ NEARLY READY: Minor optimizations recommended before deployment")
    else:
        print("⚠️  ADDITIONAL WORK NEEDED: Address remaining issues before deployment")

if __name__ == "__main__":
    asyncio.run(main())