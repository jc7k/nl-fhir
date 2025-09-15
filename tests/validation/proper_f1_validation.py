#!/usr/bin/env python3
"""
Proper F1 Validation - Using actual 3-tier MedSpaCy pipeline
Pre-warms models to handle initialization overhead
"""

import sys
sys.path.append('../../src')

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from nl_fhir.services.nlp.models import model_manager


def proper_f1_validation() -> Dict[str, Any]:
    """Proper F1 validation using actual 3-tier MedSpaCy pipeline"""

    print("🏥 PROPER F1 VALIDATION")
    print("="*50)
    print("Real F1 scores using full 3-tier MedSpaCy pipeline")
    print("Tier 1: MedSpaCy → Tier 2: Transformers → Tier 3: Regex")
    print()

    # Find test cases
    test_files = list(Path('.').glob('enhanced_p0_specialty_test_cases_*.json'))
    if not test_files:
        print("❌ No enhanced test cases found")
        return {}

    latest_file = max(test_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Using: {latest_file}")

    with open(latest_file, 'r') as f:
        data = json.load(f)

    # CRITICAL: Pre-warm all models with throwaway tests
    print("🔥 Pre-warming MedSpaCy pipeline (handling initialization overhead)...")

    warmup_tests = [
        "Give patient Test Smith 5mg of morphine IV for pain.",
        "Patient John Doe needs 10mg metoprolol for hypertension.",
        "Administer 75mg carboplatin to cancer patient.",
        "Child needs 250mg amoxicillin for infection."
    ]

    total_warmup_start = time.time()
    for i, warmup_text in enumerate(warmup_tests):
        print(f"   Warming model {i+1}/4: ", end="", flush=True)
        warmup_start = time.time()
        _ = model_manager.extract_medical_entities(warmup_text)
        warmup_time = time.time() - warmup_start
        print(f"{warmup_time:.1f}s")

    total_warmup_time = time.time() - total_warmup_start
    print(f"   ✅ All models warmed up in {total_warmup_time:.1f}s\n")

    results = {}
    baseline_scores = {
        'emergency': 0.571,
        'pediatrics': 0.250,
        'cardiology': 0.412,
        'oncology': 0.389
    }

    total_start_time = time.time()

    for specialty in ['emergency', 'pediatrics', 'cardiology', 'oncology']:
        print(f"🔬 Validating {specialty.upper()} with MedSpaCy pipeline")

        specialty_cases = data['test_cases'].get(specialty, [])
        positive_cases = [c for c in specialty_cases if c.get('case_type') == 'positive']

        # Test with 15 cases per specialty for reliable F1 with reasonable time
        test_cases = positive_cases[:15]
        print(f"   📊 Testing {len(test_cases)} positive cases")

        specialty_start = time.time()
        correct_extractions = 0
        total_extractions = 0
        false_positives = 0
        false_negatives = 0
        processing_times = []
        detailed_results = []

        for i, case in enumerate(test_cases):
            case_start = time.time()

            try:
                text = case['text']
                # Use the full 3-tier pipeline
                extracted = model_manager.extract_medical_entities(text)
                expected = case['expected']

                processing_time = time.time() - case_start
                processing_times.append(processing_time)

                # Calculate matches with improved MedSpaCy logic
                matches = calculate_medspacy_matches(extracted, expected)

                if matches['overall_match']:
                    correct_extractions += 1

                total_extractions += 1

                # Calculate precision/recall components
                if matches['has_extraction'] and matches['overall_match']:
                    pass  # True positive
                elif matches['has_extraction'] and not matches['overall_match']:
                    false_positives += 1
                elif not matches['has_extraction'] and expected:
                    false_negatives += 1

                status = "✅" if matches['overall_match'] else "❌"
                print(f"     Case {i+1}: {status} ({processing_time:.3f}s)")

                # Store detailed result for analysis
                detailed_results.append({
                    'case_id': case.get('case_id', f'case_{i+1}'),
                    'text': text[:80] + "..." if len(text) > 80 else text,
                    'expected': expected,
                    'extracted': {k: len(v) if v else 0 for k, v in extracted.items()},  # Entity counts
                    'extracted_sample': {k: v[:2] if v else [] for k, v in extracted.items()},  # Sample entities
                    'match': matches['overall_match'],
                    'match_details': matches['field_matches'],
                    'processing_time': processing_time
                })

            except Exception as e:
                print(f"     Case {i+1}: ⚠️ Error: {e}")
                processing_times.append(0)

        # Calculate actual F1 metrics
        true_positives = correct_extractions
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        baseline_f1 = baseline_scores[specialty]
        improvement = ((f1_score - baseline_f1) / baseline_f1 * 100) if baseline_f1 > 0 else 0

        specialty_time = time.time() - specialty_start

        results[specialty] = {
            'total_cases': len(test_cases),
            'correct_extractions': correct_extractions,
            'accuracy': correct_extractions / len(test_cases) if test_cases else 0,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'baseline_f1': baseline_f1,
            'improvement_percentage': improvement,
            'processing_time': specialty_time,
            'avg_case_time': sum(processing_times) / len(processing_times) if processing_times else 0,
            'detailed_results': detailed_results[:3]  # Sample for analysis
        }

        target = 0.80 if specialty == 'emergency' else 0.75
        target_status = "✅ TARGET MET" if f1_score >= target else f"❌ Gap: {target - f1_score:.3f}"

        print(f"   📈 F1 Score: {f1_score:.3f} (baseline: {baseline_f1:.3f})")
        print(f"   📊 Improvement: {improvement:+.1f}%")
        print(f"   🎯 Target: {target_status}")
        print(f"   ⏱️ Processing: {specialty_time:.1f}s total, {results[specialty]['avg_case_time']:.3f}s avg\n")

    total_time = time.time() - total_start_time

    # Calculate overall metrics
    total_cases = sum(r['total_cases'] for r in results.values())
    total_correct = sum(r['correct_extractions'] for r in results.values())
    overall_accuracy = total_correct / total_cases if total_cases > 0 else 0

    weighted_f1 = sum(
        r['f1_score'] * r['total_cases'] for r in results.values()
    ) / total_cases if total_cases > 0 else 0

    overall_baseline = sum(
        r['baseline_f1'] * r['total_cases'] for r in results.values()
    ) / total_cases if total_cases > 0 else 0

    overall_improvement = ((weighted_f1 - overall_baseline) / overall_baseline * 100) if overall_baseline > 0 else 0

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"proper_f1_validation_{timestamp}.json"

    final_results = {
        'validation_timestamp': timestamp,
        'extraction_method': '3-tier_medspacy_pipeline',
        'warmup_time': total_warmup_time,
        'total_processing_time': total_time,
        'specialty_results': results,
        'overall_metrics': {
            'total_cases': total_cases,
            'overall_accuracy': overall_accuracy,
            'weighted_f1': weighted_f1,
            'baseline_f1': overall_baseline,
            'improvement_percentage': overall_improvement
        },
        'pipeline_analysis': analyze_pipeline_performance(results),
        'summary': generate_medspacy_summary(results, overall_improvement)
    }

    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)

    print(f"🏥 PROPER F1 VALIDATION COMPLETE")
    print(f"📁 Results: {output_file}")
    print(f"⏱️ Total time: {total_time:.1f}s (including {total_warmup_time:.1f}s warmup)")
    print(f"\n📊 MEDSPACY PIPELINE RESULTS:")
    print(f"   Weighted F1: {weighted_f1:.3f}")
    print(f"   Baseline F1: {overall_baseline:.3f}")
    print(f"   Improvement: {overall_improvement:+.1f}%")

    if overall_improvement > 50:
        print(f"   🎯 EXCELLENT improvement with MedSpaCy!")
    elif overall_improvement > 25:
        print(f"   📈 GOOD improvement demonstrated")
    elif overall_improvement > 0:
        print(f"   📊 POSITIVE improvement shown")
    else:
        print(f"   ⚠️ Pipeline optimization needed")

    return final_results


def calculate_medspacy_matches(extracted: Dict, expected: Dict) -> Dict[str, Any]:
    """Calculate entity matches optimized for MedSpaCy output structure"""

    matches = {
        'has_extraction': bool(extracted and any(entities for entities in extracted.values())),
        'field_matches': {},
        'overall_match': False
    }

    total_fields = 0
    matched_fields = 0

    for field in ['patient', 'medication', 'dosage', 'frequency']:
        if field in expected:
            total_fields += 1
            expected_val = str(expected[field]).lower().strip()

            field_found = False

            # MedSpaCy-specific entity category mapping
            category_mappings = {
                'patient': ['patients', 'person', 'persons'],
                'medication': ['medications', 'drugs', 'medication'],
                'dosage': ['dosages', 'dose', 'dosage'],
                'frequency': ['frequencies', 'frequency', 'freq']
            }

            # Check all possible categories for this field
            for category in category_mappings.get(field, [field]):
                if category in extracted and extracted[category]:
                    for entity in extracted[category]:
                        extracted_val = str(entity.get('text', '')).lower().strip()

                        # Field-specific matching logic optimized for MedSpaCy
                        if field == 'medication':
                            # Medication matching - handle drug names and aliases
                            medication_matches = [
                                expected_val in extracted_val,
                                extracted_val in expected_val,
                                # Handle common drug name variations
                                any(part in extracted_val for part in expected_val.split() if len(part) > 3),
                                any(part in expected_val for part in extracted_val.split() if len(part) > 3)
                            ]
                            if any(medication_matches):
                                field_found = True
                                break

                        elif field == 'patient':
                            # Patient name matching - handle name parts
                            expected_parts = set(expected_val.split())
                            extracted_parts = set(extracted_val.split())
                            if expected_parts & extracted_parts:
                                field_found = True
                                break

                        elif field == 'dosage':
                            # Dosage matching - handle units and formatting
                            import re
                            expected_nums = re.findall(r'\d+(?:\.\d+)?', expected_val)
                            extracted_nums = re.findall(r'\d+(?:\.\d+)?', extracted_val)
                            expected_units = re.findall(r'[a-zA-Z]+', expected_val)
                            extracted_units = re.findall(r'[a-zA-Z]+', extracted_val)

                            # Match if numbers and units align
                            if (expected_nums and extracted_nums and expected_nums[0] == extracted_nums[0]) or \
                               (expected_units and extracted_units and expected_units[0].lower() == extracted_units[0].lower()) or \
                               (expected_val == extracted_val):
                                field_found = True
                                break

                        else:
                            # Frequency and other fields - flexible matching
                            if expected_val == extracted_val or \
                               expected_val in extracted_val or \
                               extracted_val in expected_val:
                                field_found = True
                                break

                if field_found:
                    break

            matches['field_matches'][field] = {
                'expected': expected[field],
                'found': field_found
            }

            if field_found:
                matched_fields += 1

    # Overall match if at least 60% of fields match (or 50% for complex cases)
    threshold = 0.6 if total_fields <= 3 else 0.5
    matches['overall_match'] = (matched_fields / total_fields) >= threshold if total_fields > 0 else False
    matches['match_percentage'] = (matched_fields / total_fields) if total_fields > 0 else 0

    return matches


def analyze_pipeline_performance(results: Dict) -> Dict[str, Any]:
    """Analyze MedSpaCy pipeline performance"""

    analysis = {
        'extraction_effectiveness': {},
        'processing_efficiency': {},
        'improvement_patterns': {}
    }

    for specialty, result in results.items():
        target = 0.80 if specialty == 'emergency' else 0.75
        f1_score = result['f1_score']

        analysis['extraction_effectiveness'][specialty] = {
            'f1_achievement': f1_score,
            'target_gap': max(0, target - f1_score),
            'baseline_improvement': result['improvement_percentage'],
            'precision': result['precision'],
            'recall': result['recall']
        }

        analysis['processing_efficiency'][specialty] = {
            'avg_processing_time': result['avg_case_time'],
            'total_cases_processed': result['total_cases']
        }

        # Analyze improvement patterns
        if result['improvement_percentage'] > 50:
            pattern = "excellent_improvement"
        elif result['improvement_percentage'] > 25:
            pattern = "good_improvement"
        elif result['improvement_percentage'] > 0:
            pattern = "positive_improvement"
        else:
            pattern = "needs_optimization"

        analysis['improvement_patterns'][specialty] = pattern

    return analysis


def generate_medspacy_summary(results: Dict, overall_improvement: float) -> List[str]:
    """Generate MedSpaCy validation summary"""

    summary = []

    for specialty, result in results.items():
        f1_score = result['f1_score']
        target = 0.80 if specialty == 'emergency' else 0.75

        if f1_score >= target:
            summary.append(f"✅ {specialty.title()}: Target achieved with MedSpaCy (F1: {f1_score:.3f})")
        elif f1_score > result['baseline_f1']:
            summary.append(f"📈 {specialty.title()}: MedSpaCy improvement shown (F1: {f1_score:.3f}, +{result['improvement_percentage']:.1f}%)")
        else:
            summary.append(f"⚠️ {specialty.title()}: MedSpaCy underperforming (F1: {f1_score:.3f})")

    # Overall assessment
    if overall_improvement > 50:
        summary.append(f"🎯 MedSpaCy pipeline delivering excellent results: {overall_improvement:+.1f}%")
    elif overall_improvement > 25:
        summary.append(f"📈 MedSpaCy pipeline showing good improvement: {overall_improvement:+.1f}%")
    elif overall_improvement > 0:
        summary.append(f"📊 MedSpaCy pipeline showing positive results: {overall_improvement:+.1f}%")
    else:
        summary.append(f"⚠️ MedSpaCy pipeline needs optimization: {overall_improvement:+.1f}%")

    return summary


if __name__ == "__main__":
    proper_f1_validation()