#!/usr/bin/env python3
"""
Quick F1 Validation - Subset testing for rapid feedback
Tests key specialties to validate configuration optimization impact
"""

import os
import json
import asyncio
import time
from datetime import datetime

# Apply optimized configuration with fine-tuned threshold
os.environ['LLM_ESCALATION_THRESHOLD'] = '0.72'  # Fine-tuned from 0.75 for optimal balance
os.environ['LLM_ESCALATION_MIN_ENTITIES'] = '3'

from src.nl_fhir.services.nlp.models import extract_medical_entities

print("🚀 QUICK F1 VALIDATION: Testing Optimized Configuration")
print("=" * 60)

# Test cases from our critical specialties
test_cases = [
    # Pediatrics (was 0.250 F1 - lowest performer)
    {
        "specialty": "Pediatrics",
        "text": "Amoxicillin suspension 250mg/5ml, give 5ml PO TID for otitis media",
        "expected": {"medication": "amoxicillin", "dosage": "250mg/5ml", "frequency": "TID", "condition": "otitis media"}
    },
    {
        "specialty": "Pediatrics",
        "text": "Children's ibuprofen 100mg/5ml, 2.5ml q6h PRN fever",
        "expected": {"medication": "ibuprofen", "dosage": "100mg/5ml", "frequency": "q6h", "condition": "fever"}
    },

    # Emergency Medicine (was 0.571 F1)
    {
        "specialty": "Emergency",
        "text": "STAT Epinephrine 1mg IV push for anaphylaxis",
        "expected": {"medication": "epinephrine", "dosage": "1mg", "route": "IV", "condition": "anaphylaxis"}
    },
    {
        "specialty": "Emergency",
        "text": "Morphine 4mg IV q2h PRN severe chest pain",
        "expected": {"medication": "morphine", "dosage": "4mg", "frequency": "q2h", "condition": "chest pain"}
    },

    # General Medicine (baseline cases)
    {
        "specialty": "General",
        "text": "Metformin 500mg PO BID for type 2 diabetes",
        "expected": {"medication": "metformin", "dosage": "500mg", "frequency": "BID", "condition": "type 2 diabetes"}
    },
    {
        "specialty": "General",
        "text": "Lisinopril 10mg daily for hypertension",
        "expected": {"medication": "lisinopril", "dosage": "10mg", "frequency": "daily", "condition": "hypertension"}
    }
]

def calculate_quick_f1(expected, extracted):
    """Quick F1 calculation"""
    if not expected:
        return 0.0

    matches = 0
    for key, value in expected.items():
        # Check if entity type exists in extracted
        if key in ['medication', 'dosage', 'frequency', 'condition']:
            entity_list = extracted.get(f"{key}s", extracted.get(key, []))
            if not isinstance(entity_list, list):
                entity_list = [entity_list]

            # Check for match
            for entity in entity_list:
                entity_text = entity.get('text', '') if isinstance(entity, dict) else str(entity)
                if value.lower() in entity_text.lower() or entity_text.lower() in value.lower():
                    matches += 1
                    break

    precision = matches / max(len([e for entities in extracted.values() if isinstance(entities, list) for e in entities]), 1)
    recall = matches / len(expected)

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)

# Run validation
results_by_specialty = {}
all_f1_scores = []
total_time = 0

print("\n📊 TEST RESULTS:")
print("-" * 60)
print(f"{'Specialty':<15} {'Text':<30} {'F1 Score':>10} {'Time':>8}")
print("-" * 60)

for case in test_cases:
    start = time.time()

    # Extract entities using optimized configuration
    extracted = extract_medical_entities(case['text'])

    processing_time = time.time() - start
    total_time += processing_time

    # Calculate F1
    f1_score = calculate_quick_f1(case['expected'], extracted)
    all_f1_scores.append(f1_score)

    # Track by specialty
    specialty = case['specialty']
    if specialty not in results_by_specialty:
        results_by_specialty[specialty] = []
    results_by_specialty[specialty].append(f1_score)

    # Display result
    status = "✅" if f1_score >= 0.75 else "⚠️" if f1_score >= 0.5 else "❌"
    text_preview = case['text'][:30] + "..."
    print(f"{specialty:<15} {text_preview:<30} {f1_score:>10.3f} {processing_time:>7.2f}s {status}")

# Calculate averages
print("\n" + "=" * 60)
print("📈 SPECIALTY AVERAGES:")
print("=" * 60)

for specialty, scores in results_by_specialty.items():
    avg_f1 = sum(scores) / len(scores)
    improvement = ""

    if specialty == "Pediatrics":
        improvement = f" (was 0.250, +{((avg_f1 - 0.250) / 0.250 * 100):.0f}%)"
    elif specialty == "Emergency":
        improvement = f" (was 0.571, +{((avg_f1 - 0.571) / 0.571 * 100):.0f}%)"

    status = "✅ TARGET MET" if avg_f1 >= 0.75 else "⚠️ CLOSE" if avg_f1 >= 0.65 else "❌ NEEDS WORK"
    print(f"{specialty:<15} F1: {avg_f1:.3f}{improvement} {status}")

overall_f1 = sum(all_f1_scores) / len(all_f1_scores)
avg_time = total_time / len(test_cases)

print("\n" + "=" * 60)
print("🎯 OVERALL RESULTS:")
print("=" * 60)
print(f"Overall F1 Score:        {overall_f1:.3f}")
print(f"Baseline F1:             0.411")
print(f"Improvement:             {((overall_f1 - 0.411) / 0.411 * 100):+.1f}%")
print(f"Target (0.75):           {'✅ ACHIEVED' if overall_f1 >= 0.75 else f'{(overall_f1/0.75*100):.1f}% of target'}")
print(f"Avg Processing Time:     {avg_time:.2f}s")
print()

# Save quick results
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
quick_results = {
    "timestamp": datetime.now().isoformat(),
    "overall_f1": overall_f1,
    "baseline_f1": 0.411,
    "improvement_percent": ((overall_f1 - 0.411) / 0.411 * 100),
    "specialty_averages": {k: sum(v)/len(v) for k, v in results_by_specialty.items()},
    "avg_processing_time": avg_time,
    "test_cases": len(test_cases)
}

filename = f"quick_f1_validation_{timestamp}.json"
with open(filename, 'w') as f:
    json.dump(quick_results, f, indent=2)

print(f"💾 Results saved to: {filename}")

# Final verdict
if overall_f1 >= 0.75:
    print("\n🎉 SUCCESS: F1 TARGET ACHIEVED WITH CONFIGURATION OPTIMIZATION!")
elif overall_f1 >= 0.65:
    print("\n⚠️  CLOSE: Near target - minor tuning needed")
else:
    print("\n🔧 IN PROGRESS: Configuration showing improvement, further optimization possible")