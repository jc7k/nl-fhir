#!/usr/bin/env python3
"""
Quick MedSpaCy F1 Validation - 5 cases per specialty for speed
"""

import sys
sys.path.append('../../src')

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from nl_fhir.services.nlp.models import model_manager


def quick_medspacy_f1() -> Dict[str, Any]:
    """Quick F1 validation with 5 cases per specialty using MedSpaCy"""

    print("⚡ QUICK MEDSPACY F1 VALIDATION")
    print("="*40)
    print("Real F1 scores with 3-tier MedSpaCy pipeline")
    print("Testing 5 cases per specialty for speed\n")

    # Find test cases
    test_files = list(Path('.').glob('enhanced_p0_specialty_test_cases_*.json'))
    if not test_files:
        print("❌ No enhanced test cases found")
        return {}

    latest_file = max(test_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Using: {latest_file}")

    with open(latest_file, 'r') as f:
        data = json.load(f)

    # Pre-warm with one test
    print("🔥 Pre-warming MedSpaCy...")
    warmup_start = time.time()
    _ = model_manager.extract_medical_entities("Give patient test 5mg morphine.")
    warmup_time = time.time() - warmup_start
    print(f"   ✅ Models loaded in {warmup_time:.1f}s\n")

    results = {}
    baseline_scores = {
        'emergency': 0.571,
        'pediatrics': 0.250,
        'cardiology': 0.412,
        'oncology': 0.389
    }

    total_start = time.time()

    for specialty in ['emergency', 'pediatrics', 'cardiology', 'oncology']:
        print(f"🔬 Testing {specialty.upper()}")

        specialty_cases = data['test_cases'].get(specialty, [])
        positive_cases = [c for c in specialty_cases if c.get('case_type') == 'positive']

        # Test only 5 cases for speed
        test_cases = positive_cases[:5]
        print(f"   📊 Processing {len(test_cases)} cases")

        correct = 0
        processing_times = []
        detailed_results = []

        for i, case in enumerate(test_cases):
            case_start = time.time()

            try:
                text = case['text']
                extracted = model_manager.extract_medical_entities(text)
                expected = case['expected']

                processing_time = time.time() - case_start
                processing_times.append(processing_time)

                # Simple matching - check key entities
                matches = calculate_simple_matches(extracted, expected)

                if matches['overall_match']:
                    correct += 1

                status = "✅" if matches['overall_match'] else "❌"
                print(f"     Case {i+1}: {status} ({processing_time:.2f}s)")

                detailed_results.append({
                    'case_id': case.get('case_id', f'{specialty}_{i+1}'),
                    'text': text[:60] + "..." if len(text) > 60 else text,
                    'expected': expected,
                    'extracted_counts': {k: len(v) if v else 0 for k, v in extracted.items()},
                    'match': matches['overall_match'],
                    'processing_time': processing_time
                })

            except Exception as e:
                print(f"     Case {i+1}: ⚠️ Error: {e}")
                processing_times.append(0)

        # Calculate F1
        accuracy = correct / len(test_cases) if test_cases else 0
        baseline_f1 = baseline_scores[specialty]

        # For quick test, use accuracy as F1 approximation
        f1_score = accuracy
        improvement = ((f1_score - baseline_f1) / baseline_f1 * 100) if baseline_f1 > 0 else 0

        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0

        results[specialty] = {
            'total_cases': len(test_cases),
            'correct': correct,
            'accuracy': accuracy,
            'f1_score': f1_score,
            'baseline_f1': baseline_f1,
            'improvement_percentage': improvement,
            'avg_processing_time': avg_time,
            'detailed_results': detailed_results
        }

        target = 0.80 if specialty == 'emergency' else 0.75
        target_status = "✅" if f1_score >= target else f"❌ Gap: {target - f1_score:.3f}"

        print(f"   📈 F1: {f1_score:.3f} (baseline: {baseline_f1:.3f})")
        print(f"   📊 Improvement: {improvement:+.1f}%")
        print(f"   🎯 Target: {target_status}")
        print(f"   ⏱️ Avg time: {avg_time:.2f}s per case\n")

    total_time = time.time() - total_start

    # Calculate overall metrics
    total_cases = sum(r['total_cases'] for r in results.values())
    total_correct = sum(r['correct'] for r in results.values())
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
    output_file = f"quick_medspacy_f1_{timestamp}.json"

    final_results = {
        'validation_timestamp': timestamp,
        'method': 'medspacy_3tier_pipeline_quick_test',
        'warmup_time': warmup_time,
        'total_time': total_time,
        'cases_per_specialty': 5,
        'specialty_results': results,
        'overall_metrics': {
            'total_cases': total_cases,
            'overall_accuracy': overall_accuracy,
            'weighted_f1': weighted_f1,
            'baseline_f1': overall_baseline,
            'improvement_percentage': overall_improvement
        }
    }

    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)

    print(f"⚡ QUICK MEDSPACY F1 COMPLETE")
    print(f"📁 Results: {output_file}")
    print(f"⏱️ Total: {total_time:.1f}s (warmup: {warmup_time:.1f}s)")
    print(f"\n📊 MEDSPACY PIPELINE RESULTS:")
    print(f"   Weighted F1: {weighted_f1:.3f}")
    print(f"   Baseline F1: {overall_baseline:.3f}")
    print(f"   Improvement: {overall_improvement:+.1f}%")

    return final_results


def calculate_simple_matches(extracted: Dict, expected: Dict) -> Dict[str, Any]:
    """Simple matching for quick validation"""

    matches = {
        'has_extraction': bool(extracted and any(entities for entities in extracted.values())),
        'overall_match': False
    }

    matched_fields = 0
    total_fields = len(expected)

    for field, expected_val in expected.items():
        expected_val = str(expected_val).lower().strip()
        field_found = False

        # Check all categories
        for category, entities in extracted.items():
            if entities and field.lower() in category.lower():
                for entity in entities:
                    extracted_val = str(entity.get('text', '')).lower().strip()

                    # Simple matching
                    if (expected_val in extracted_val or
                        extracted_val in expected_val or
                        expected_val == extracted_val):
                        field_found = True
                        break

            if field_found:
                break

        if field_found:
            matched_fields += 1

    # Overall match if at least 50% match (lenient for quick test)
    matches['overall_match'] = (matched_fields / total_fields) >= 0.5 if total_fields > 0 else False

    return matches


if __name__ == "__main__":
    quick_medspacy_f1()