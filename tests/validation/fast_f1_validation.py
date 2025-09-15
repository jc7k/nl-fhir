#!/usr/bin/env python3
"""
Fast F1 Validation - Using regex-only extraction for speed
"""

import sys
sys.path.append('../../src')

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from nl_fhir.services.nlp.extractors.regex_extractor import RegexExtractor


def fast_f1_validation() -> Dict[str, Any]:
    """Fast F1 validation using regex-only extraction"""

    print("⚡ FAST F1 VALIDATION")
    print("="*40)
    print("Real F1 scores using regex patterns only")
    print("Bypassing heavy transformer models\n")

    # Find test cases
    test_files = list(Path('.').glob('enhanced_p0_specialty_test_cases_*.json'))
    if not test_files:
        print("❌ No enhanced test cases found")
        return {}

    latest_file = max(test_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Using: {latest_file}")

    with open(latest_file, 'r') as f:
        data = json.load(f)

    # Initialize regex extractor only
    regex_extractor = RegexExtractor()

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

        # Test with 25 cases per specialty for good F1 estimate
        test_cases = positive_cases[:25]
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
                extracted = regex_extractor.extract_entities(text)
                expected = case['expected']

                processing_time = time.time() - case_start
                processing_times.append(processing_time)

                # Calculate matches
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
                print(f"     Case {i+1}: {status} ({processing_time:.4f}s)")

                # Store detailed result for analysis
                detailed_results.append({
                    'case_id': case.get('case_id', f'case_{i+1}'),
                    'text': text[:80] + "..." if len(text) > 80 else text,
                    'expected': expected,
                    'extracted': {k: v for k, v in extracted.items() if v},  # Only non-empty
                    'match': matches['overall_match'],
                    'match_percentage': matches['match_percentage'],
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
            'detailed_results': detailed_results[:5]  # Sample for analysis
        }

        target = 0.80 if specialty == 'emergency' else 0.75
        target_status = "✅ TARGET MET" if f1_score >= target else f"❌ Gap: {target - f1_score:.3f}"

        print(f"   📈 F1 Score: {f1_score:.3f} (baseline: {baseline_f1:.3f})")
        print(f"   📊 Improvement: {improvement:+.1f}%")
        print(f"   🎯 Target: {target_status}")
        print(f"   ⏱️ Processing: {specialty_time:.2f}s total, {results[specialty]['avg_case_time']:.4f}s avg\n")

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
    output_file = f"fast_f1_validation_{timestamp}.json"

    final_results = {
        'validation_timestamp': timestamp,
        'extraction_method': 'regex_only',
        'total_processing_time': total_time,
        'specialty_results': results,
        'overall_metrics': {
            'total_cases': total_cases,
            'overall_accuracy': overall_accuracy,
            'weighted_f1': weighted_f1,
            'baseline_f1': overall_baseline,
            'improvement_percentage': overall_improvement
        },
        'performance_analysis': generate_performance_analysis(results),
        'summary': generate_validation_summary(results, overall_improvement)
    }

    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)

    print(f"⚡ FAST F1 VALIDATION COMPLETE")
    print(f"📁 Results: {output_file}")
    print(f"⏱️ Total time: {total_time:.2f}s")
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Weighted F1: {weighted_f1:.3f}")
    print(f"   Baseline F1: {overall_baseline:.3f}")
    print(f"   Improvement: {overall_improvement:+.1f}%")

    if overall_improvement > 50:
        print(f"   🎯 EXCELLENT improvement achieved!")
    elif overall_improvement > 25:
        print(f"   📈 GOOD improvement shown")
    elif overall_improvement > 0:
        print(f"   📊 POSITIVE improvement demonstrated")
    else:
        print(f"   ⚠️ Further optimization needed")

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
                            # Medication matching - flexible
                            if expected_val in extracted_val or extracted_val in expected_val:
                                field_found = True
                                break
                        elif field == 'patient':
                            # Patient name matching - check name parts
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


def generate_performance_analysis(results: Dict) -> Dict[str, Any]:
    """Generate performance analysis"""

    analysis = {}

    for specialty, result in results.items():
        target = 0.80 if specialty == 'emergency' else 0.75
        f1_score = result['f1_score']

        analysis[specialty] = {
            'target_met': f1_score >= target,
            'target_gap': max(0, target - f1_score),
            'improvement_from_baseline': result['improvement_percentage'],
            'processing_efficiency': f"Avg {result['avg_case_time']:.4f}s per case"
        }

    return analysis


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
    fast_f1_validation()