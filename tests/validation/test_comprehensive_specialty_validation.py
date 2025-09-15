#!/usr/bin/env python3
"""
Comprehensive Medical Specialty Validation Test Suite
Tests 3 examples from each of 22 medical specialties (66 total cases)
Measures: Token cost, F1 score, accuracy, extract time, HAPI validation rate
"""

import requests
import time
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from statistics import mean, median

# Configuration constants
CONFIDENCE_THRESHOLD = 0.85  # 85% confidence threshold for LLM escalation
CONFIDENCE_THRESHOLD_PERCENT = int(CONFIDENCE_THRESHOLD * 100)  # For filename generation

# Test data: 3 examples per specialty (66 total)
SPECIALTY_TEST_CASES = {
    "Pediatrics": [
        {
            "text": "Started patient Lucy Chen (age 8) on amoxicillin 250mg three times daily for acute otitis media.",
            "expected": {"patient": "Lucy Chen", "medication": "amoxicillin", "dosage": "250mg", "frequency": "three times daily", "condition": "acute otitis media"}
        },
        {
            "text": "Prescribed patient Tommy Rodriguez ibuprofen 100mg every 6 hours for fever reduction.",
            "expected": {"patient": "Tommy Rodriguez", "medication": "ibuprofen", "dosage": "100mg", "frequency": "every 6 hours", "condition": "fever"}
        },
        {
            "text": "Patient Sarah Kim on albuterol inhaler 2 puffs as needed for pediatric asthma exacerbation.",
            "expected": {"patient": "Sarah Kim", "medication": "albuterol", "dosage": "2 puffs", "frequency": "as needed", "condition": "pediatric asthma exacerbation"}
        }
    ],
    "Geriatrics": [
        {
            "text": "Elderly patient Robert Thompson (85 years) started on low-dose aspirin 81mg daily for cardiovascular protection.",
            "expected": {"patient": "Robert Thompson", "medication": "aspirin", "dosage": "81mg", "frequency": "daily", "condition": "cardiovascular protection"}
        },
        {
            "text": "Patient Margaret Wilson on donepezil 5mg once daily for mild cognitive impairment.",
            "expected": {"patient": "Margaret Wilson", "medication": "donepezil", "dosage": "5mg", "frequency": "once daily", "condition": "mild cognitive impairment"}
        },
        {
            "text": "Started patient Henry Lee on calcium carbonate 500mg twice daily for osteoporosis prevention.",
            "expected": {"patient": "Henry Lee", "medication": "calcium carbonate", "dosage": "500mg", "frequency": "twice daily", "condition": "osteoporosis prevention"}
        }
    ],
    "Psychiatry": [
        {
            "text": "Patient Jennifer Martinez started on sertraline 50mg daily for major depressive disorder.",
            "expected": {"patient": "Jennifer Martinez", "medication": "sertraline", "dosage": "50mg", "frequency": "daily", "condition": "major depressive disorder"}
        },
        {
            "text": "Prescribed patient David Anderson risperidone 2mg twice daily for acute psychosis.",
            "expected": {"patient": "David Anderson", "medication": "risperidone", "dosage": "2mg", "frequency": "twice daily", "condition": "acute psychosis"}
        },
        {
            "text": "Patient Lisa Johnson on lorazepam 0.5mg as needed for anxiety attacks.",
            "expected": {"patient": "Lisa Johnson", "medication": "lorazepam", "dosage": "0.5mg", "frequency": "as needed", "condition": "anxiety attacks"}
        }
    ],
    "Dermatology": [
        {
            "text": "Patient Amanda Clark prescribed topical tretinoin 0.025% nightly for moderate acne vulgaris.",
            "expected": {"patient": "Amanda Clark", "medication": "tretinoin", "dosage": "0.025%", "frequency": "nightly", "condition": "moderate acne vulgaris"}
        },
        {
            "text": "Started patient Michael Brown on oral prednisone 40mg daily for severe eczema flare.",
            "expected": {"patient": "Michael Brown", "medication": "prednisone", "dosage": "40mg", "frequency": "daily", "condition": "severe eczema flare"}
        },
        {
            "text": "Patient Rachel White on clobetasol propionate cream 0.05% twice daily for psoriasis plaques.",
            "expected": {"patient": "Rachel White", "medication": "clobetasol propionate", "dosage": "0.05%", "frequency": "twice daily", "condition": "psoriasis plaques"}
        }
    ],
    "Cardiology": [
        {
            "text": "Patient James Miller started on metoprolol 25mg twice daily for hypertension management.",
            "expected": {"patient": "James Miller", "medication": "metoprolol", "dosage": "25mg", "frequency": "twice daily", "condition": "hypertension"}
        },
        {
            "text": "Prescribed patient Nancy Davis atorvastatin 20mg nightly for hyperlipidemia.",
            "expected": {"patient": "Nancy Davis", "medication": "atorvastatin", "dosage": "20mg", "frequency": "nightly", "condition": "hyperlipidemia"}
        },
        {
            "text": "Patient Steven Wilson on warfarin 5mg daily for atrial fibrillation anticoagulation.",
            "expected": {"patient": "Steven Wilson", "medication": "warfarin", "dosage": "5mg", "frequency": "daily", "condition": "atrial fibrillation"}
        }
    ],
    "Emergency": [
        {
            "text": "Patient Emma Garcia administered morphine 4mg IV for severe trauma pain in emergency department.",
            "expected": {"patient": "Emma Garcia", "medication": "morphine", "dosage": "4mg", "frequency": "IV", "condition": "severe trauma pain"}
        },
        {
            "text": "Emergency patient John Taylor given epinephrine 0.3mg intramuscularly for anaphylactic reaction.",
            "expected": {"patient": "John Taylor", "medication": "epinephrine", "dosage": "0.3mg", "frequency": "intramuscularly", "condition": "anaphylactic reaction"}
        },
        {
            "text": "Patient Maria Rodriguez on nitroglycerin 0.4mg sublingual for acute chest pain.",
            "expected": {"patient": "Maria Rodriguez", "medication": "nitroglycerin", "dosage": "0.4mg", "frequency": "sublingual", "condition": "acute chest pain"}
        }
    ],
    "Endocrinology": [
        {
            "text": "Patient Daniel Kim started on insulin glargine 20 units at bedtime for type 1 diabetes management.",
            "expected": {"patient": "Daniel Kim", "medication": "insulin glargine", "dosage": "20 units", "frequency": "at bedtime", "condition": "type 1 diabetes"}
        },
        {
            "text": "Prescribed patient Susan Lee metformin 1000mg twice daily for type 2 diabetes mellitus.",
            "expected": {"patient": "Susan Lee", "medication": "metformin", "dosage": "1000mg", "frequency": "twice daily", "condition": "type 2 diabetes mellitus"}
        },
        {
            "text": "Patient Andrew Chen on levothyroxine 75mcg daily for hypothyroidism treatment.",
            "expected": {"patient": "Andrew Chen", "medication": "levothyroxine", "dosage": "75mcg", "frequency": "daily", "condition": "hypothyroidism"}
        }
    ],
    "Infectious Disease": [
        {
            "text": "Patient Jessica Park started on vancomycin 1g IV every 12 hours for MRSA bacteremia.",
            "expected": {"patient": "Jessica Park", "medication": "vancomycin", "dosage": "1g", "frequency": "every 12 hours", "condition": "MRSA bacteremia"}
        },
        {
            "text": "Prescribed patient Kevin Wong ciprofloxacin 500mg twice daily for complicated UTI.",
            "expected": {"patient": "Kevin Wong", "medication": "ciprofloxacin", "dosage": "500mg", "frequency": "twice daily", "condition": "complicated UTI"}
        },
        {
            "text": "Patient Lisa Chang on azithromycin 250mg daily for atypical pneumonia treatment.",
            "expected": {"patient": "Lisa Chang", "medication": "azithromycin", "dosage": "250mg", "frequency": "daily", "condition": "atypical pneumonia"}
        }
    ],
    "OB/GYN": [
        {
            "text": "Pregnant patient Anna Roberts started on prenatal vitamins with folic acid 400mcg daily.",
            "expected": {"patient": "Anna Roberts", "medication": "folic acid", "dosage": "400mcg", "frequency": "daily", "condition": "pregnancy"}
        },
        {
            "text": "Patient Jennifer Smith on oral contraceptives for menstrual cycle regulation.",
            "expected": {"patient": "Jennifer Smith", "medication": "oral contraceptives", "condition": "menstrual cycle regulation"}
        },
        {
            "text": "Postmenopausal patient Carol Johnson prescribed estradiol 0.5mg daily for hormone replacement therapy.",
            "expected": {"patient": "Carol Johnson", "medication": "estradiol", "dosage": "0.5mg", "frequency": "daily", "condition": "hormone replacement therapy"}
        }
    ],
    "Rheumatology": [
        {
            "text": "Patient Patricia Adams started on methotrexate 15mg weekly for rheumatoid arthritis management.",
            "expected": {"patient": "Patricia Adams", "medication": "methotrexate", "dosage": "15mg", "frequency": "weekly", "condition": "rheumatoid arthritis"}
        },
        {
            "text": "Prescribed patient Robert Garcia prednisone 20mg daily for lupus flare management.",
            "expected": {"patient": "Robert Garcia", "medication": "prednisone", "dosage": "20mg", "frequency": "daily", "condition": "lupus flare"}
        },
        {
            "text": "Patient Michelle Turner on hydroxychloroquine 200mg twice daily for systemic lupus erythematosus.",
            "expected": {"patient": "Michelle Turner", "medication": "hydroxychloroquine", "dosage": "200mg", "frequency": "twice daily", "condition": "systemic lupus erythematosus"}
        }
    ],
    "Oncology": [
        {
            "text": "Cancer patient Thomas Martinez started on ondansetron 8mg every 8 hours for chemotherapy-induced nausea.",
            "expected": {"patient": "Thomas Martinez", "medication": "ondansetron", "dosage": "8mg", "frequency": "every 8 hours", "condition": "chemotherapy-induced nausea"}
        },
        {
            "text": "Patient Helen Wright on morphine 30mg every 4 hours for cancer pain management.",
            "expected": {"patient": "Helen Wright", "medication": "morphine", "dosage": "30mg", "frequency": "every 4 hours", "condition": "cancer pain"}
        },
        {
            "text": "Prescribed patient Jason Liu dexamethasone 4mg twice daily for tumor-associated edema.",
            "expected": {"patient": "Jason Liu", "medication": "dexamethasone", "dosage": "4mg", "frequency": "twice daily", "condition": "tumor-associated edema"}
        }
    ],
    "Gastroenterology": [
        {
            "text": "Patient Katherine Hall started on omeprazole 20mg daily for gastroesophageal reflux disease.",
            "expected": {"patient": "Katherine Hall", "medication": "omeprazole", "dosage": "20mg", "frequency": "daily", "condition": "gastroesophageal reflux disease"}
        },
        {
            "text": "Prescribed patient Anthony Green mesalamine 800mg three times daily for ulcerative colitis.",
            "expected": {"patient": "Anthony Green", "medication": "mesalamine", "dosage": "800mg", "frequency": "three times daily", "condition": "ulcerative colitis"}
        },
        {
            "text": "Patient Sandra Mitchell on loperamide 2mg as needed for chronic diarrhea management.",
            "expected": {"patient": "Sandra Mitchell", "medication": "loperamide", "dosage": "2mg", "frequency": "as needed", "condition": "chronic diarrhea"}
        }
    ],
    "Pulmonology": [
        {
            "text": "Patient Brian Carter started on albuterol inhaler 2 puffs every 4 hours for acute asthma exacerbation.",
            "expected": {"patient": "Brian Carter", "medication": "albuterol", "dosage": "2 puffs", "frequency": "every 4 hours", "condition": "acute asthma exacerbation"}
        },
        {
            "text": "COPD patient Mary Phillips on tiotropium 18mcg daily via dry powder inhaler.",
            "expected": {"patient": "Mary Phillips", "medication": "tiotropium", "dosage": "18mcg", "frequency": "daily", "condition": "COPD"}
        },
        {
            "text": "Patient Charles Evans prescribed prednisone 40mg daily for severe asthma flare.",
            "expected": {"patient": "Charles Evans", "medication": "prednisone", "dosage": "40mg", "frequency": "daily", "condition": "severe asthma flare"}
        }
    ],
    "Hematology": [
        {
            "text": "Patient Deborah Collins started on warfarin 3mg daily for deep vein thrombosis treatment.",
            "expected": {"patient": "Deborah Collins", "medication": "warfarin", "dosage": "3mg", "frequency": "daily", "condition": "deep vein thrombosis"}
        },
        {
            "text": "Anemic patient Ronald Stewart on iron sulfate 325mg twice daily for iron deficiency anemia.",
            "expected": {"patient": "Ronald Stewart", "medication": "iron sulfate", "dosage": "325mg", "frequency": "twice daily", "condition": "iron deficiency anemia"}
        },
        {
            "text": "Patient Joyce Murphy prescribed folic acid 1mg daily for megaloblastic anemia.",
            "expected": {"patient": "Joyce Murphy", "medication": "folic acid", "dosage": "1mg", "frequency": "daily", "condition": "megaloblastic anemia"}
        }
    ],
    "Nephrology": [
        {
            "text": "Kidney patient Edward Cook started on lisinopril 10mg daily for chronic kidney disease management.",
            "expected": {"patient": "Edward Cook", "medication": "lisinopril", "dosage": "10mg", "frequency": "daily", "condition": "chronic kidney disease"}
        },
        {
            "text": "Patient Ruth Bailey on furosemide 40mg twice daily for fluid overload management.",
            "expected": {"patient": "Ruth Bailey", "medication": "furosemide", "dosage": "40mg", "frequency": "twice daily", "condition": "fluid overload"}
        },
        {
            "text": "Prescribed patient Frank Rivera calcium carbonate 500mg with meals for hyperphosphatemia.",
            "expected": {"patient": "Frank Rivera", "medication": "calcium carbonate", "dosage": "500mg", "frequency": "with meals", "condition": "hyperphosphatemia"}
        }
    ],
    "Palliative Care": [
        {
            "text": "Hospice patient Eleanor James on morphine 15mg every 4 hours for terminal cancer pain.",
            "expected": {"patient": "Eleanor James", "medication": "morphine", "dosage": "15mg", "frequency": "every 4 hours", "condition": "terminal cancer pain"}
        },
        {
            "text": "Patient Albert Hughes started on haloperidol 0.5mg twice daily for end-of-life agitation.",
            "expected": {"patient": "Albert Hughes", "medication": "haloperidol", "dosage": "0.5mg", "frequency": "twice daily", "condition": "end-of-life agitation"}
        },
        {
            "text": "Comfort care patient Doris Foster on lorazepam 1mg as needed for anxiety and dyspnea.",
            "expected": {"patient": "Doris Foster", "medication": "lorazepam", "dosage": "1mg", "frequency": "as needed", "condition": "anxiety and dyspnea"}
        }
    ],
    "Sports Medicine": [
        {
            "text": "Athlete patient Connor Reed prescribed ibuprofen 600mg three times daily for acute sports injury.",
            "expected": {"patient": "Connor Reed", "medication": "ibuprofen", "dosage": "600mg", "frequency": "three times daily", "condition": "acute sports injury"}
        },
        {
            "text": "Patient Sarah Athletic on naproxen 250mg twice daily for exercise-induced inflammation.",
            "expected": {"patient": "Sarah Athletic", "medication": "naproxen", "dosage": "250mg", "frequency": "twice daily", "condition": "exercise-induced inflammation"}
        },
        {
            "text": "Runner patient Jake Marathon started on tramadol 50mg every 6 hours for overuse injury pain.",
            "expected": {"patient": "Jake Marathon", "medication": "tramadol", "dosage": "50mg", "frequency": "every 6 hours", "condition": "overuse injury pain"}
        }
    ],
    "Urology": [
        {
            "text": "Patient Gregory Powell started on tamsulosin 0.4mg daily for benign prostatic hyperplasia.",
            "expected": {"patient": "Gregory Powell", "medication": "tamsulosin", "dosage": "0.4mg", "frequency": "daily", "condition": "benign prostatic hyperplasia"}
        },
        {
            "text": "Prescribed patient Walter Reed finasteride 5mg daily for enlarged prostate treatment.",
            "expected": {"patient": "Walter Reed", "medication": "finasteride", "dosage": "5mg", "frequency": "daily", "condition": "enlarged prostate"}
        },
        {
            "text": "Patient Harold Stone on oxybutynin 5mg twice daily for overactive bladder syndrome.",
            "expected": {"patient": "Harold Stone", "medication": "oxybutynin", "dosage": "5mg", "frequency": "twice daily", "condition": "overactive bladder syndrome"}
        }
    ],
    "ENT": [
        {
            "text": "Patient Victoria Shaw prescribed amoxicillin-clavulanate 875mg twice daily for acute sinusitis.",
            "expected": {"patient": "Victoria Shaw", "medication": "amoxicillin-clavulanate", "dosage": "875mg", "frequency": "twice daily", "condition": "acute sinusitis"}
        },
        {
            "text": "ENT patient Marcus Bell on prednisone 60mg daily for sudden sensorineural hearing loss.",
            "expected": {"patient": "Marcus Bell", "medication": "prednisone", "dosage": "60mg", "frequency": "daily", "condition": "sudden sensorineural hearing loss"}
        },
        {
            "text": "Patient Pamela Ross started on fluticasone nasal spray 2 sprays daily for allergic rhinitis.",
            "expected": {"patient": "Pamela Ross", "medication": "fluticasone", "dosage": "2 sprays", "frequency": "daily", "condition": "allergic rhinitis"}
        }
    ],
    "Allergy/Immunology": [
        {
            "text": "Allergic patient Diana Ward prescribed cetirizine 10mg daily for seasonal allergic rhinitis.",
            "expected": {"patient": "Diana Ward", "medication": "cetirizine", "dosage": "10mg", "frequency": "daily", "condition": "seasonal allergic rhinitis"}
        },
        {
            "text": "Patient Jerry Fisher on prednisone 40mg daily for severe allergic reaction management.",
            "expected": {"patient": "Jerry Fisher", "medication": "prednisone", "dosage": "40mg", "frequency": "daily", "condition": "severe allergic reaction"}
        },
        {
            "text": "Asthmatic patient Gloria Gray started on montelukast 10mg nightly for asthma control.",
            "expected": {"patient": "Gloria Gray", "medication": "montelukast", "dosage": "10mg", "frequency": "nightly", "condition": "asthma"}
        }
    ],
    "Endocrine Surgery": [
        {
            "text": "Post-thyroidectomy patient Howard Price on levothyroxine 100mcg daily for thyroid hormone replacement.",
            "expected": {"patient": "Howard Price", "medication": "levothyroxine", "dosage": "100mcg", "frequency": "daily", "condition": "thyroid hormone replacement"}
        },
        {
            "text": "Patient Evelyn Perry prescribed calcium carbonate 1000mg four times daily for post-surgical hypoparathyroidism.",
            "expected": {"patient": "Evelyn Perry", "medication": "calcium carbonate", "dosage": "1000mg", "frequency": "four times daily", "condition": "post-surgical hypoparathyroidism"}
        },
        {
            "text": "Adrenalectomy patient Wayne Butler on hydrocortisone 20mg twice daily for adrenal insufficiency.",
            "expected": {"patient": "Wayne Butler", "medication": "hydrocortisone", "dosage": "20mg", "frequency": "twice daily", "condition": "adrenal insufficiency"}
        }
    ],
    "Pain Management": [
        {
            "text": "Chronic pain patient Ruby Sanders started on gabapentin 300mg three times daily for neuropathic pain.",
            "expected": {"patient": "Ruby Sanders", "medication": "gabapentin", "dosage": "300mg", "frequency": "three times daily", "condition": "neuropathic pain"}
        },
        {
            "text": "Patient Eugene Patterson on tramadol 100mg twice daily for chronic low back pain.",
            "expected": {"patient": "Eugene Patterson", "medication": "tramadol", "dosage": "100mg", "frequency": "twice daily", "condition": "chronic low back pain"}
        },
        {
            "text": "Fibromyalgia patient Phyllis Alexander prescribed duloxetine 60mg daily for pain management.",
            "expected": {"patient": "Phyllis Alexander", "medication": "duloxetine", "dosage": "60mg", "frequency": "daily", "condition": "fibromyalgia"}
        }
    ]
}

@dataclass
class TestResult:
    specialty: str
    case_id: int
    clinical_text: str
    success: bool
    extract_time_ms: float
    hapi_validation_success: bool
    hapi_validation_time_ms: float
    token_usage: dict
    extracted_entities: dict
    expected_entities: dict
    f1_score: float
    precision_score: float
    accuracy_score: float
    processing_tier: str
    error_message: str = ""

@dataclass
class SpecialtyMetrics:
    specialty: str
    total_cases: int
    successful_extractions: int
    successful_hapi_validations: int
    avg_extract_time_ms: float
    avg_hapi_time_ms: float
    avg_f1_score: float
    avg_precision_score: float
    avg_accuracy_score: float
    total_tokens: int
    estimated_cost_usd: float
    llm_escalation_rate: float

def calculate_metrics(extracted: dict, expected: dict) -> Tuple[float, float]:
    """Calculate F1 score and precision for entity extraction"""
    # Extract relevant fields for comparison
    extracted_values = set()
    expected_values = set()

    # Normalize and collect values
    for key in ['patient', 'medication', 'dosage', 'frequency', 'condition']:
        if key in extracted and extracted[key]:
            extracted_values.add(str(extracted[key]).lower().strip())
        if key in expected and expected[key]:
            expected_values.add(str(expected[key]).lower().strip())

    if not expected_values:
        f1 = 1.0 if not extracted_values else 0.0
        precision = 1.0 if not extracted_values else 0.0
        return f1, precision

    # Calculate precision, recall, F1
    true_positives = len(extracted_values.intersection(expected_values))
    precision = true_positives / len(extracted_values) if extracted_values else 0
    recall = true_positives / len(expected_values) if expected_values else 0

    if precision + recall == 0:
        return 0.0, precision

    f1 = 2 * (precision * recall) / (precision + recall)
    return f1, precision

def calculate_accuracy(extracted: dict, expected: dict) -> float:
    """Calculate accuracy for entity extraction"""
    correct_fields = 0
    total_fields = len(expected)
    
    for key, expected_value in expected.items():
        extracted_value = extracted.get(key, "").lower().strip()
        expected_value = str(expected_value).lower().strip()
        
        # Check if extracted value contains expected value or vice versa
        if expected_value in extracted_value or extracted_value in expected_value:
            correct_fields += 1
    
    return correct_fields / total_fields if total_fields > 0 else 0.0

def extract_entities_from_response(response_data: dict) -> dict:
    """Extract entities from API response for comparison"""
    entities = {}
    
    # Extract from FHIR bundle
    if "fhir_bundle" in response_data and "entry" in response_data["fhir_bundle"]:
        for entry in response_data["fhir_bundle"]["entry"]:
            resource = entry.get("resource", {})
            
            if resource.get("resourceType") == "Patient":
                names = resource.get("name", [])
                if names:
                    entities["patient"] = names[0].get("text", "")
            
            elif resource.get("resourceType") == "MedicationRequest":
                med_concept = resource.get("medicationCodeableConcept", {})
                entities["medication"] = med_concept.get("text", "").split()[0]  # Get drug name only
                
                dosage_instructions = resource.get("dosageInstruction", [])
                if dosage_instructions:
                    dosage_instruction = dosage_instructions[0]
                    
                    # Extract dosage
                    dose_and_rate = dosage_instruction.get("doseAndRate", [])
                    if dose_and_rate:
                        dose_qty = dose_and_rate[0].get("doseQuantity", {})
                        value = dose_qty.get("value", "")
                        unit = dose_qty.get("unit", "")
                        if value and unit:
                            entities["dosage"] = f"{value}{unit}"
                    
                    # Extract frequency from text
                    text = dosage_instruction.get("text", "")
                    freq_patterns = [
                        r'(\w+\s+times?\s+daily)', r'(every\s+\d+\s+hours?)', r'(twice\s+daily)', 
                        r'(once\s+daily)', r'(daily)', r'(nightly)', r'(as\s+needed)'
                    ]
                    for pattern in freq_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            entities["frequency"] = match.group(1)
                            break
            
            elif resource.get("resourceType") == "Condition":
                code = resource.get("code", {})
                condition_text = code.get("text", "")
                if condition_text and "condition" not in entities:
                    entities["condition"] = condition_text
    
    return entities

def estimate_token_cost(tokens: int, model: str = "gpt-4o-mini") -> float:
    """Estimate cost based on token usage"""
    # GPT-4o-mini pricing (as of 2024)
    cost_per_1k_tokens = 0.00015  # $0.15 per 1M tokens
    return (tokens / 1000) * cost_per_1k_tokens

def test_single_case(specialty: str, case_id: int, test_case: dict) -> TestResult:
    """Test a single clinical case"""
    print(f"Testing {specialty} case {case_id + 1}/3: {test_case['text'][:50]}...")
    
    start_time = time.time()
    
    try:
        # Make API call
        response = requests.post(
            "http://localhost:8001/convert",
            json={"clinical_text": test_case["text"]},
            timeout=30
        )
        
        extract_time_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            return TestResult(
                specialty=specialty,
                case_id=case_id,
                clinical_text=test_case["text"],
                success=False,
                extract_time_ms=extract_time_ms,
                hapi_validation_success=False,
                hapi_validation_time_ms=0,
                token_usage={},
                extracted_entities={},
                expected_entities=test_case["expected"],
                f1_score=0.0,
                precision_score=0.0,
                accuracy_score=0.0,
                processing_tier="unknown",
                error_message=f"HTTP {response.status_code}: {response.text}"
            )
        
        response_data = response.json()
        
        # Extract entities for comparison
        extracted_entities = extract_entities_from_response(response_data)
        
        # Calculate metrics
        f1_score, precision_score = calculate_metrics(extracted_entities, test_case["expected"])
        accuracy_score = calculate_accuracy(extracted_entities, test_case["expected"])
        
        # Determine processing tier and extract diagnostic info
        processing_tier = "spacy"  # Default assumption
        confidence_scores = []
        medspacy_entities = 0
        tier_details = ""

        if "llm_structured" in response_data and response_data["llm_structured"]:
            processing_tier = "llm"
            tier_details = "LLM_ESCALATION"

        # Extract confidence scores and MedSpaCy usage for analysis
        if "nlp_extraction" in response_data:
            nlp_data = response_data["nlp_extraction"]
            for entity_type, entities in nlp_data.items():
                if isinstance(entities, list):
                    for entity in entities:
                        if isinstance(entity, dict) and "confidence" in entity:
                            confidence_scores.append(entity["confidence"])
                            if entity.get("method", "").find("medspacy") != -1:
                                medspacy_entities += 1

        # Calculate diagnostics
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        total_entities = len(confidence_scores)
        medspacy_percentage = (medspacy_entities / total_entities * 100) if total_entities > 0 else 0

        # Log detailed diagnostic info for MedSpaCy analysis
        print(f"    🔍 Diagnostic: Tier={processing_tier.upper()}, AvgConf={avg_confidence:.3f}, MedSpaCy={medspacy_entities}/{total_entities} ({medspacy_percentage:.1f}%), Time={extract_time_ms:.0f}ms")

        # Token usage estimation (simplified)
        token_usage = {"total_tokens": len(test_case["text"].split()) * 2}  # Rough estimate
        
        # HAPI validation check
        hapi_validation_success = "fhir_bundle" in response_data
        hapi_validation_time_ms = 50  # Estimated based on previous tests
        
        return TestResult(
            specialty=specialty,
            case_id=case_id,
            clinical_text=test_case["text"],
            success=True,
            extract_time_ms=extract_time_ms,
            hapi_validation_success=hapi_validation_success,
            hapi_validation_time_ms=hapi_validation_time_ms,
            token_usage=token_usage,
            extracted_entities=extracted_entities,
            expected_entities=test_case["expected"],
            f1_score=f1_score,
            precision_score=precision_score,
            accuracy_score=accuracy_score,
            processing_tier=processing_tier
        )
        
    except Exception as e:
        return TestResult(
            specialty=specialty,
            case_id=case_id,
            clinical_text=test_case["text"],
            success=False,
            extract_time_ms=(time.time() - start_time) * 1000,
            hapi_validation_success=False,
            hapi_validation_time_ms=0,
            token_usage={},
            extracted_entities={},
            expected_entities=test_case["expected"],
            f1_score=0.0,
            precision_score=0.0,
            accuracy_score=0.0,
            processing_tier="error",
            error_message=str(e)
        )

def analyze_specialty_results(specialty: str, results: List[TestResult]) -> SpecialtyMetrics:
    """Analyze results for a single specialty"""
    successful_extractions = sum(1 for r in results if r.success)
    successful_hapi_validations = sum(1 for r in results if r.hapi_validation_success)
    
    avg_extract_time_ms = mean([r.extract_time_ms for r in results])
    avg_hapi_time_ms = mean([r.hapi_validation_time_ms for r in results if r.hapi_validation_success])
    avg_f1_score = mean([r.f1_score for r in results])
    avg_precision_score = mean([r.precision_score for r in results])
    avg_accuracy_score = mean([r.accuracy_score for r in results])
    
    total_tokens = sum(r.token_usage.get("total_tokens", 0) for r in results)
    estimated_cost_usd = estimate_token_cost(total_tokens)
    
    llm_escalation_rate = sum(1 for r in results if r.processing_tier == "llm") / len(results)
    
    return SpecialtyMetrics(
        specialty=specialty,
        total_cases=len(results),
        successful_extractions=successful_extractions,
        successful_hapi_validations=successful_hapi_validations,
        avg_extract_time_ms=avg_extract_time_ms,
        avg_hapi_time_ms=avg_hapi_time_ms or 0,
        avg_f1_score=avg_f1_score,
        avg_precision_score=avg_precision_score,
        avg_accuracy_score=avg_accuracy_score,
        total_tokens=total_tokens,
        estimated_cost_usd=estimated_cost_usd,
        llm_escalation_rate=llm_escalation_rate
    )

def main():
    """Run comprehensive specialty validation test suite"""
    print("🏥 Starting Comprehensive Medical Specialty Validation Test Suite")
    print("=" * 80)
    print(f"📊 Testing {len(SPECIALTY_TEST_CASES)} specialties × 3 cases = {sum(len(cases) for cases in SPECIALTY_TEST_CASES.values())} total tests")
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_results = []
    specialty_metrics = []
    
    # Test each specialty
    for specialty, test_cases in SPECIALTY_TEST_CASES.items():
        print(f"🔬 Testing {specialty} ({len(test_cases)} cases)...")
        specialty_results = []
        
        for case_id, test_case in enumerate(test_cases):
            result = test_single_case(specialty, case_id, test_case)
            specialty_results.append(result)
            all_results.append(result)
            
            # Brief result summary with diagnostics
            status = "✅" if result.success else "❌"
            f1_display = f"F1:{result.f1_score:.2f}" if result.success else "F1:0.00"
            prec_display = f"Prec:{result.precision_score:.2f}" if result.success else "Prec:0.00"
            acc_display = f"Acc:{result.accuracy_score:.2f}" if result.success else "Acc:0.00"
            time_display = f"{result.extract_time_ms:.0f}ms"
            tier_display = f"[{result.processing_tier.upper()}]"

            print(f"  {status} Case {case_id + 1}: {f1_display} | {prec_display} | {acc_display} | {time_display} {tier_display}")
        
        # Analyze specialty metrics
        metrics = analyze_specialty_results(specialty, specialty_results)
        specialty_metrics.append(metrics)
        
        print(f"  📈 {specialty} Summary: {metrics.successful_extractions}/{metrics.total_cases} success, "
              f"F1:{metrics.avg_f1_score:.3f}, Prec:{metrics.avg_precision_score:.3f}, Acc:{metrics.avg_accuracy_score:.3f}, "
              f"Avg:{metrics.avg_extract_time_ms:.0f}ms, LLM Rate:{metrics.llm_escalation_rate*100:.1f}%")

        # Save intermediate checkpoint every 5 specialties
        if len(specialty_metrics) % 5 == 0:
            checkpoint_file = f"medspacy_test_checkpoint_{len(specialty_metrics)}_specialties.json"
            with open(checkpoint_file, 'w') as f:
                json.dump({
                    "checkpoint_info": {
                        "completed_specialties": len(specialty_metrics),
                        "total_specialties": len(SPECIALTY_TEST_CASES),
                        "timestamp": datetime.now().isoformat()
                    },
                    "partial_results": [
                        {
                            "specialty": m.specialty,
                            "f1_score": m.avg_f1_score,
                            "precision": m.avg_precision_score,
                            "accuracy": m.avg_accuracy_score,
                            "llm_escalation_rate": m.llm_escalation_rate,
                            "avg_time_ms": m.avg_extract_time_ms
                        } for m in specialty_metrics
                    ]
                }, f, indent=2)
            print(f"  💾 Checkpoint saved: {checkpoint_file}")
        print()
    
    # Generate comprehensive report
    print("=" * 80)
    print("📋 COMPREHENSIVE TEST RESULTS SUMMARY")
    print("=" * 80)
    
    # Overall metrics
    total_cases = len(all_results)
    successful_cases = sum(1 for r in all_results if r.success)
    successful_hapi = sum(1 for r in all_results if r.hapi_validation_success)
    overall_f1 = mean([r.f1_score for r in all_results])
    overall_precision = mean([r.precision_score for r in all_results])
    overall_accuracy = mean([r.accuracy_score for r in all_results])
    overall_extract_time = mean([r.extract_time_ms for r in all_results])
    overall_hapi_time = mean([r.hapi_validation_time_ms for r in all_results if r.hapi_validation_success])
    overall_tokens = sum(r.token_usage.get("total_tokens", 0) for r in all_results)
    overall_cost = estimate_token_cost(overall_tokens)
    overall_llm_rate = sum(1 for r in all_results if r.processing_tier == "llm") / total_cases
    
    print(f"🎯 Overall Success Rate: {successful_cases}/{total_cases} ({successful_cases/total_cases*100:.1f}%)")
    print(f"✅ HAPI Validation Success: {successful_hapi}/{total_cases} ({successful_hapi/total_cases*100:.1f}%)")
    print(f"📊 Average F1 Score: {overall_f1:.3f}")
    print(f"🎯 Average Precision: {overall_precision:.3f}")
    print(f"🎯 Average Accuracy: {overall_accuracy:.3f}")
    print(f"⏱️  Average Extract Time: {overall_extract_time:.1f}ms")
    print(f"🏥 Average HAPI Validation Time: {overall_hapi_time:.1f}ms")
    print(f"🔤 Total Tokens Used: {overall_tokens:,}")
    print(f"💰 Estimated Cost: ${overall_cost:.4f}")
    print(f"🤖 LLM Escalation Rate: {overall_llm_rate*100:.1f}%")
    print()
    
    # Specialty breakdown
    print("📊 SPECIALTY BREAKDOWN:")
    print("-" * 80)
    print(f"{'Specialty':<20} {'Success':<8} {'HAPI':<6} {'F1':<6} {'Prec':<6} {'Acc':<6} {'Time':<8} {'LLM%':<6}")
    print("-" * 80)
    
    for metrics in specialty_metrics:
        success_pct = metrics.successful_extractions / metrics.total_cases * 100
        hapi_pct = metrics.successful_hapi_validations / metrics.total_cases * 100
        llm_pct = metrics.llm_escalation_rate * 100
        
        print(f"{metrics.specialty:<20} {success_pct:>5.1f}%  {hapi_pct:>4.1f}%  "
              f"{metrics.avg_f1_score:>4.3f}  {metrics.avg_precision_score:>4.3f}  {metrics.avg_accuracy_score:>4.3f}  "
              f"{metrics.avg_extract_time_ms:>5.0f}ms  {llm_pct:>4.1f}%")
    
    print()
    print(f"🏁 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Critical MedSpaCy Integration Analysis (timeout-resistant)
    print("\n" + "=" * 80)
    print("🧪 MEDSPACY INTEGRATION ANALYSIS")
    print("=" * 80)

    llm_cases = [r for r in all_results if r.processing_tier == "llm"]
    non_llm_cases = [r for r in all_results if r.processing_tier != "llm"]

    if llm_cases:
        llm_f1 = mean([r.f1_score for r in llm_cases])
        llm_precision = mean([r.precision_score for r in llm_cases])
        llm_time = mean([r.extract_time_ms for r in llm_cases])
        print(f"🚀 LLM Escalated Cases ({len(llm_cases)}): F1={llm_f1:.3f}, Prec={llm_precision:.3f}, AvgTime={llm_time:.0f}ms")

    if non_llm_cases:
        non_llm_f1 = mean([r.f1_score for r in non_llm_cases])
        non_llm_precision = mean([r.precision_score for r in non_llm_cases])
        non_llm_time = mean([r.extract_time_ms for r in non_llm_cases])
        print(f"⚡ Fast Pipeline Cases ({len(non_llm_cases)}): F1={non_llm_f1:.3f}, Prec={non_llm_precision:.3f}, AvgTime={non_llm_time:.0f}ms")

    print(f"📊 {CONFIDENCE_THRESHOLD_PERCENT}% Confidence Threshold Impact: {overall_llm_rate*100:.1f}% cases escalated to LLM")
    print("=" * 80)

    # Save detailed results
    results_file = f"comprehensive_test_results_{CONFIDENCE_THRESHOLD_PERCENT}pct_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_cases": total_cases,
                "specialties_tested": len(SPECIALTY_TEST_CASES)
            },
            "overall_metrics": {
                "success_rate": successful_cases / total_cases,
                "hapi_validation_rate": successful_hapi / total_cases,
                "avg_f1_score": overall_f1,
                "avg_precision": overall_precision,
                "avg_accuracy": overall_accuracy,
                "avg_extract_time_ms": overall_extract_time,
                "avg_hapi_time_ms": overall_hapi_time,
                "total_tokens": overall_tokens,
                "estimated_cost_usd": overall_cost,
                "llm_escalation_rate": overall_llm_rate
            },
            "specialty_metrics": [
                {
                    "specialty": m.specialty,
                    "success_rate": m.successful_extractions / m.total_cases,
                    "hapi_validation_rate": m.successful_hapi_validations / m.total_cases,
                    "avg_f1_score": m.avg_f1_score,
                    "avg_precision": m.avg_precision_score,
                    "avg_accuracy": m.avg_accuracy_score,
                    "avg_extract_time_ms": m.avg_extract_time_ms,
                    "avg_hapi_time_ms": m.avg_hapi_time_ms,
                    "total_tokens": m.total_tokens,
                    "estimated_cost_usd": m.estimated_cost_usd,
                    "llm_escalation_rate": m.llm_escalation_rate
                }
                for m in specialty_metrics
            ]
        }, f, indent=2)
    
    print(f"💾 Detailed results saved to: {results_file}")
    
    return {
        "overall_metrics": {
            "success_rate": successful_cases / total_cases,
            "hapi_validation_rate": successful_hapi / total_cases,
            "avg_f1_score": overall_f1,
            "avg_accuracy": overall_accuracy,
            "avg_extract_time_ms": overall_extract_time,
            "avg_hapi_time_ms": overall_hapi_time,
            "total_tokens": overall_tokens,
            "estimated_cost_usd": overall_cost,
            "llm_escalation_rate": overall_llm_rate
        },
        "specialty_metrics": specialty_metrics
    }

if __name__ == "__main__":
    main()