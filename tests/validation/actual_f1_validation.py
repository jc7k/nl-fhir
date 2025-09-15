#!/usr/bin/env python3
"""
Actual F1 Validation - Real data with optimized processing
"""

import sys
sys.path.append('../../src')

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from nl_fhir.services.nlp.models import model_manager


def actual_f1_validation() -> Dict[str, Any]:
    """Run actual F1 validation with optimized processing"""

    print("🎯 ACTUAL F1 VALIDATION")
    print("="*50)
    print("Real F1 scores with optimized NLP processing")
    print("Handling model initialization overhead\n")

    # Find test cases
    test_files = list(Path('.').glob('enhanced_p0_specialty_test_cases_*.json'))
    if not test_files:
        print("❌ No enhanced test cases found")
        return {}

    latest_file = max(test_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Using: {latest_file}")

    with open(latest_file, 'r') as f:
        data = json.load(f)

    # Pre-warm models with a dummy case
    print("🔥 Pre-warming NLP models...")
    warmup_start = time.time()
    _ = model_manager.extract_medical_entities("Give patient test 1mg of medication.")
    warmup_time = time.time() - warmup_start
    print(f"   ✅ Models loaded in {warmup_time:.1f}s\n")

    results = {}
    baseline_scores = {
        'emergency': 0.571,
        'pediatrics': 0.250,
        'cardiology': 0.412,
        'oncology': 0.389
    }

    total_start_time = time.time()

    for specialty in ['emergency', 'pediatrics', 'cardiology', 'oncology']:
        print(f"🔬 Validating {specialty.upper()}")

        specialty_cases = data['test_cases'].get(specialty, [])
        positive_cases = [c for c in specialty_cases if c.get('case_type') == 'positive']

        # Test with 20 cases per specialty for reliable F1
        test_cases = positive_cases[:20]
        print(f"   📊 Testing {len(test_cases)} positive cases")

        specialty_start = time.time()
        correct_extractions = 0
        total_extractions = 0
        false_positives = 0
        false_negatives = 0
        processing_times = []

        for i, case in enumerate(test_cases):
            case_start = time.time()

            try:
                text = case['text']
                extracted = model_manager.extract_medical_entities(text)
                expected = case['expected']

                processing_time = time.time() - case_start
                processing_times.append(processing_time)

                # Calculate matches using improved logic
                matches = calculate_entity_matches(extracted, expected)

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
            'avg_case_time': sum(processing_times) / len(processing_times) if processing_times else 0
        }

        print(f"   📈 F1 Score: {f1_score:.3f} (baseline: {baseline_f1:.3f})")
        print(f"   📊 Improvement: {improvement:+.1f}%")
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
    output_file = f"actual_f1_validation_{timestamp}.json"

    final_results = {
        'validation_timestamp': timestamp,
        'warmup_time': warmup_time,
        'total_processing_time': total_time,
        'specialty_results': results,
        'overall_metrics': {
            'total_cases': total_cases,
            'overall_accuracy': overall_accuracy,
            'weighted_f1': weighted_f1,
            'baseline_f1': overall_baseline,
            'improvement_percentage': overall_improvement
        },
        'summary': generate_validation_summary(results, overall_improvement)
    }

    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)

    print(f"🎯 ACTUAL F1 VALIDATION COMPLETE")
    print(f"📁 Results: {output_file}")
    print(f"⏱️ Total time: {total_time:.1f}s (including {warmup_time:.1f}s warmup)")
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Weighted F1: {weighted_f1:.3f}")
    print(f"   Baseline F1: {overall_baseline:.3f}")
    print(f"   Improvement: {overall_improvement:+.1f}%")

    return final_results


def calculate_entity_matches(extracted: Dict, expected: Dict) -> Dict[str, Any]:
    """Calculate entity matches with improved logic"""

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
            # Check all extraction categories for this field
            for category, entities in extracted.items():
                if entities and field in category.lower():
                    for entity in entities:
                        extracted_val = str(entity.get('text', '')).lower().strip()

                        # Different matching strategies per field
                        if field == 'medication':
                            # Medication matching
                            if expected_val in extracted_val or extracted_val in expected_val:
                                field_found = True
                                break
                        elif field == 'patient':
                            # Patient name matching
                            expected_parts = expected_val.split()
                            extracted_parts = extracted_val.split()
                            if set(expected_parts) & set(extracted_parts):
                                field_found = True
                                break
                        else:
                            # Exact match for dosage/frequency
                            if expected_val == extracted_val:
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

    # Overall match if at least 60% of fields match
    matches['overall_match'] = (matched_fields / total_fields) >= 0.6 if total_fields > 0 else False
    matches['match_percentage'] = (matched_fields / total_fields) if total_fields > 0 else 0

    return matches


def generate_validation_summary(results: Dict, overall_improvement: float) -> List[str]:
    """Generate validation summary"""

    summary = []

    for specialty, result in results.items():
        f1_score = result['f1_score']
        target = 0.80 if specialty == 'emergency' else 0.75

        if f1_score >= target:
            summary.append(f"✅ {specialty.title()}: Target achieved (F1: {f1_score:.3f})")
        elif f1_score > result['baseline_f1']:
            summary.append(f"📈 {specialty.title()}: Improvement shown (F1: {f1_score:.3f})")
        else:
            summary.append(f"⚠️ {specialty.title()}: Limited improvement (F1: {f1_score:.3f})")

    if overall_improvement > 50:
        summary.append(f"🎯 Excellent overall improvement: {overall_improvement:+.1f}%")
    elif overall_improvement > 25:
        summary.append(f"📈 Good overall improvement: {overall_improvement:+.1f}%")
    elif overall_improvement > 0:
        summary.append(f"📊 Positive improvement shown: {overall_improvement:+.1f}%")
    else:
        summary.append(f"⚠️ Improvement needed: {overall_improvement:+.1f}%")

    return summary


if __name__ == "__main__":
    actual_f1_validation()