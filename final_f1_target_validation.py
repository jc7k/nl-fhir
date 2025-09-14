#!/usr/bin/env python3
"""
Final F1 Target Validation - Option 1 Complete Implementation Test

This script validates that Option 1 enhancements achieve the 0.75 F1 target
through enhanced pediatric and emergency medicine patterns plus optimized threshold.
"""

import os
import json
import time
from datetime import datetime

# Apply final optimized configuration
os.environ['LLM_ESCALATION_THRESHOLD'] = '0.72'  # Fine-tuned optimal threshold
os.environ['LLM_ESCALATION_MIN_ENTITIES'] = '3'

from src.nl_fhir.services.nlp.models import extract_medical_entities

print("🎯 FINAL F1 TARGET VALIDATION: Testing Option 1 Complete Implementation")
print("=" * 70)
print("Target: ≥0.75 F1 Score with Enhanced Patterns + Optimized Threshold")
print("=" * 70)

# Expanded test cases targeting our enhanced patterns
test_cases = [
    # Enhanced Pediatrics Tests (targeting new liquid/suspension patterns)
    {
        "specialty": "Pediatrics",
        "text": "Amoxicillin suspension 250mg/5ml, administer 5ml PO TID for acute otitis media",
        "expected": {"medication": "amoxicillin", "dosage": "250mg/5ml", "frequency": "TID", "condition": "otitis media"}
    },
    {
        "specialty": "Pediatrics",
        "text": "Children's ibuprofen suspension 100mg/5ml, give 2.5ml q6h PRN fever",
        "expected": {"medication": "ibuprofen", "dosage": "100mg/5ml", "frequency": "q6h", "condition": "fever"}
    },
    {
        "specialty": "Pediatrics",
        "text": "Acetaminophen drops 80mg/0.8ml, weight-based dosing q4h for pain",
        "expected": {"medication": "acetaminophen", "dosage": "80mg/0.8ml", "frequency": "q4h", "condition": "pain"}
    },

    # Enhanced Emergency Medicine Tests (targeting new route patterns)
    {
        "specialty": "Emergency",
        "text": "STAT Epinephrine 1mg IV push for anaphylaxis shock",
        "expected": {"medication": "epinephrine", "dosage": "1mg", "route": "IV push", "condition": "anaphylaxis"}
    },
    {
        "specialty": "Emergency",
        "text": "Morphine 4mg IV bolus q2h PRN severe chest pain",
        "expected": {"medication": "morphine", "dosage": "4mg", "route": "IV bolus", "condition": "chest pain"}
    },
    {
        "specialty": "Emergency",
        "text": "Naloxone 0.4mg IM injection for opioid overdose",
        "expected": {"medication": "naloxone", "dosage": "0.4mg", "route": "IM", "condition": "overdose"}
    },
    {
        "specialty": "Emergency",
        "text": "Nitroglycerin 0.4mg sublingual PRN chest pain",
        "expected": {"medication": "nitroglycerin", "dosage": "0.4mg", "route": "sublingual", "condition": "chest pain"}
    },

    # General Medicine (should maintain high performance)
    {
        "specialty": "General",
        "text": "Metformin 500mg PO BID for type 2 diabetes management",
        "expected": {"medication": "metformin", "dosage": "500mg", "frequency": "BID", "condition": "diabetes"}
    },
    {
        "specialty": "General",
        "text": "Lisinopril 10mg daily by mouth for hypertension control",
        "expected": {"medication": "lisinopril", "dosage": "10mg", "frequency": "daily", "condition": "hypertension"}
    },
    {
        "specialty": "General",
        "text": "Atorvastatin 20mg once daily for hyperlipidemia",
        "expected": {"medication": "atorvastatin", "dosage": "20mg", "frequency": "daily", "condition": "hyperlipidemia"}
    }
]

def calculate_enhanced_f1(expected, extracted):
    """Enhanced F1 calculation with partial match scoring"""
    if not expected:
        return 0.0

    matches = 0
    partial_matches = 0

    for key, value in expected.items():
        # Check if entity type exists in extracted
        if key in ['medication', 'dosage', 'frequency', 'condition', 'route']:
            entity_list = extracted.get(f"{key}s", extracted.get(key, []))
            if not isinstance(entity_list, list):
                entity_list = [entity_list]

            # Check for exact and partial matches
            found_exact = False
            found_partial = False

            for entity in entity_list:
                entity_text = entity.get('text', '') if isinstance(entity, dict) else str(entity)
                entity_lower = entity_text.lower()
                value_lower = value.lower()

                # Exact match (full credit)
                if value_lower in entity_lower or entity_lower in value_lower:
                    if not found_exact:
                        matches += 1
                        found_exact = True
                        break
                # Partial match (partial credit) - for complex terms
                elif len(value_lower) > 5 and any(word in entity_lower for word in value_lower.split() if len(word) > 3):
                    if not found_partial and not found_exact:
                        partial_matches += 0.5
                        found_partial = True

    # Calculate precision with partial match bonus
    total_extracted = sum(len(entities) for entities in extracted.values() if isinstance(entities, list))
    precision = (matches + partial_matches) / max(total_extracted, 1)
    recall = (matches + partial_matches) / len(expected)

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)

# Run comprehensive validation
results_by_specialty = {}
all_f1_scores = []
total_time = 0
detailed_results = []

print("\n📊 DETAILED TEST RESULTS:")
print("-" * 70)
print(f"{'Specialty':<12} {'Test Case':<25} {'F1 Score':>10} {'Time':>8} {'Status'}")
print("-" * 70)

for i, case in enumerate(test_cases, 1):
    start = time.time()

    # Extract entities using enhanced configuration
    extracted = extract_medical_entities(case['text'])

    processing_time = time.time() - start
    total_time += processing_time

    # Calculate enhanced F1
    f1_score = calculate_enhanced_f1(case['expected'], extracted)
    all_f1_scores.append(f1_score)

    # Track by specialty
    specialty = case['specialty']
    if specialty not in results_by_specialty:
        results_by_specialty[specialty] = []
    results_by_specialty[specialty].append(f1_score)

    # Determine status
    if f1_score >= 0.75:
        status = "✅ TARGET"
    elif f1_score >= 0.65:
        status = "⚠️ CLOSE"
    else:
        status = "❌ BELOW"

    # Create test case label
    test_label = f"Test {i}"
    text_preview = case['text'][:25] + "..."

    print(f"{specialty:<12} {test_label:<25} {f1_score:>10.3f} {processing_time:>7.2f}s {status}")

    # Store detailed results
    detailed_results.append({
        "test_id": i,
        "specialty": specialty,
        "text": case['text'],
        "expected": case['expected'],
        "extracted": extracted,
        "f1_score": f1_score,
        "processing_time": processing_time
    })

# Calculate final metrics
print("\n" + "=" * 70)
print("📈 SPECIALTY PERFORMANCE ANALYSIS:")
print("=" * 70)

specialty_improvements = {
    "Pediatrics": {"baseline": 0.250, "previous": 0.472},
    "Emergency": {"baseline": 0.571, "previous": 0.667},
    "General": {"baseline": 0.411, "previous": 0.750}
}

for specialty, scores in results_by_specialty.items():
    avg_f1 = sum(scores) / len(scores)
    baseline = specialty_improvements[specialty]["baseline"]
    previous = specialty_improvements[specialty]["previous"]

    improvement_from_baseline = ((avg_f1 - baseline) / baseline * 100)
    improvement_from_previous = ((avg_f1 - previous) / previous * 100) if previous > 0 else 0

    # Status determination
    if avg_f1 >= 0.75:
        status = "✅ TARGET ACHIEVED"
    elif avg_f1 >= 0.65:
        status = "⚠️ NEAR TARGET"
    else:
        status = "❌ NEEDS MORE WORK"

    print(f"{specialty:<12} F1: {avg_f1:.3f}")
    print(f"             Baseline improvement: +{improvement_from_baseline:.0f}% (from {baseline:.3f})")
    print(f"             Recent improvement:   +{improvement_from_previous:+.0f}% (from {previous:.3f})")
    print(f"             Status: {status}")
    print()

overall_f1 = sum(all_f1_scores) / len(all_f1_scores)
avg_time = total_time / len(test_cases)
baseline_f1 = 0.411

print("=" * 70)
print("🎯 FINAL TARGET VALIDATION RESULTS:")
print("=" * 70)
print(f"Overall F1 Score:        {overall_f1:.3f}")
print(f"Baseline F1 (original):  {baseline_f1:.3f}")
print(f"F1 Improvement:          {((overall_f1 - baseline_f1) / baseline_f1 * 100):+.1f}%")
print(f"Target Achievement:      {(overall_f1/0.75*100):.1f}% of 0.75 target")
print(f"Avg Processing Time:     {avg_time:.2f}s")
print(f"Test Cases Processed:    {len(test_cases)}")
print()

# Target assessment
if overall_f1 >= 0.75:
    verdict = "🎉 SUCCESS: F1 TARGET ACHIEVED!"
    verdict_detail = f"Achieved {overall_f1:.3f} F1 Score (>{75:.0f}% target)"
elif overall_f1 >= 0.70:
    verdict = "⚠️ VERY CLOSE: Minor optimization needed"
    verdict_detail = f"At {overall_f1:.3f} F1 Score ({overall_f1/0.75*100:.1f}% of target)"
elif overall_f1 >= 0.65:
    verdict = "🔧 GOOD PROGRESS: Additional patterns needed"
    verdict_detail = f"At {overall_f1:.3f} F1 Score, solid improvement trajectory"
else:
    verdict = "❌ MORE WORK NEEDED: Significant optimization required"
    verdict_detail = f"At {overall_f1:.3f} F1 Score, below expectations"

print(f"Final Verdict: {verdict}")
print(f"Assessment:    {verdict_detail}")

# Save comprehensive results
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results = {
    "timestamp": datetime.now().isoformat(),
    "test_type": "final_f1_target_validation_option_1",
    "configuration": {
        "llm_escalation_threshold": 0.72,
        "llm_escalation_min_entities": 3,
        "enhancements": ["pediatric_liquid_patterns", "emergency_route_patterns", "optimized_threshold"]
    },
    "overall_metrics": {
        "overall_f1": overall_f1,
        "baseline_f1": baseline_f1,
        "improvement_percent": ((overall_f1 - baseline_f1) / baseline_f1 * 100),
        "target_achievement_percent": (overall_f1/0.75*100),
        "avg_processing_time": avg_time,
        "test_cases_count": len(test_cases)
    },
    "specialty_performance": {
        specialty: {
            "avg_f1": sum(scores)/len(scores),
            "test_count": len(scores),
            "baseline": specialty_improvements[specialty]["baseline"],
            "previous": specialty_improvements[specialty]["previous"]
        } for specialty, scores in results_by_specialty.items()
    },
    "detailed_results": detailed_results,
    "verdict": verdict,
    "verdict_detail": verdict_detail
}

filename = f"final_f1_target_validation_{timestamp}.json"
with open(filename, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Comprehensive results saved to: {filename}")
print()

if overall_f1 >= 0.75:
    print("🏆 OPTION 1 IMPLEMENTATION COMPLETE!")
    print("✅ Enhanced patterns + optimized threshold achieved F1 target")
    print("✅ Configuration optimization approach validated")
    print("✅ No architectural redesign needed")
else:
    gap_to_target = 0.75 - overall_f1
    print(f"📊 OPTION 1 STATUS: {gap_to_target:.3f} F1 points from target")
    print("🔄 Ready for additional pattern refinement if needed")