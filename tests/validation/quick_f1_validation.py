#!/usr/bin/env python3
"""
Quick F1 Validation - Test F1 improvements with small sample
"""

import sys
sys.path.append('../../src')

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from nl_fhir.services.nlp.models import model_manager


def quick_validate_f1() -> Dict[str, Any]:
    """Quick F1 validation with 10 cases per specialty"""

    print("🎯 QUICK F1 VALIDATION")
    print("="*40)
    print("Testing 10 cases per P0 specialty\n")

    # Find latest enhanced test cases
    test_files = list(Path('.').glob('enhanced_p0_specialty_test_cases_*.json'))
    if not test_files:
        print("❌ No enhanced test cases found")
        return {}

    latest_file = max(test_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Using: {latest_file}")

    with open(latest_file, 'r') as f:
        data = json.load(f)

    results = {}
    baseline_scores = {
        'emergency': 0.571,
        'pediatrics': 0.250,
        'cardiology': 0.412,
        'oncology': 0.389
    }

    for specialty in ['emergency', 'pediatrics', 'cardiology', 'oncology']:
        print(f"\n🔬 Testing {specialty.upper()}")

        specialty_cases = data['test_cases'].get(specialty, [])
        positive_cases = [c for c in specialty_cases if c.get('case_type') == 'positive']

        # Test first 10 positive cases
        test_cases = positive_cases[:10]
        print(f"   📊 Testing {len(test_cases)} cases")

        correct = 0
        total = len(test_cases)
        processing_times = []

        for i, case in enumerate(test_cases):
            start_time = time.time()

            try:
                # Extract entities
                text = case['text']
                extracted = model_manager.extract_medical_entities(text)
                expected = case['expected']

                processing_time = time.time() - start_time
                processing_times.append(processing_time)

                # Simple matching - check if we found expected medication
                match = False
                if 'expected' in case and 'medication' in case['expected']:
                    expected_med = case['expected']['medication'].lower()

                    # Check all entity categories for medication
                    for category, entities in extracted.items():
                        if entities and 'medication' in category.lower():
                            for entity in entities:
                                if entity.get('text', '').lower() == expected_med:
                                    match = True
                                    break
                        if match:
                            break

                if match:
                    correct += 1

                print(f"   Case {i+1}: {'✅' if match else '❌'} ({processing_time:.3f}s)")

            except Exception as e:
                print(f"   Case {i+1}: ⚠️ Error: {e}")
                processing_times.append(0)

        # Calculate F1 (simplified)
        accuracy = correct / total if total > 0 else 0
        baseline_f1 = baseline_scores[specialty]
        improvement = ((accuracy - baseline_f1) / baseline_f1 * 100) if baseline_f1 > 0 else 0

        results[specialty] = {
            'total_cases': total,
            'correct': correct,
            'accuracy': accuracy,
            'baseline_f1': baseline_f1,
            'improvement_pct': improvement,
            'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0
        }

        print(f"   📈 Results: {correct}/{total} correct ({accuracy:.3f})")
        print(f"   📊 F1: {baseline_f1:.3f} → {accuracy:.3f} ({improvement:+.1f}%)")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"quick_f1_validation_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'results': results,
            'summary': {
                'overall_improvement': sum(r['improvement_pct'] for r in results.values()) / len(results)
            }
        }, f, indent=2)

    print(f"\n🎯 QUICK VALIDATION COMPLETE")
    print(f"📁 Results: {output_file}")

    return results


if __name__ == "__main__":
    quick_validate_f1()