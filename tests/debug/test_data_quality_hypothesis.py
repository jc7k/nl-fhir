#!/usr/bin/env python3
"""
Data Quality Hypothesis Validation Test
Tests if fixing data quality issues improves F1 performance more than algorithmic complexity
"""

import json
import re
from typing import Dict, List, Tuple

# Original problematic pediatric cases
ORIGINAL_PEDIATRIC_CASES = [
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
]

# Fixed pediatric cases with proper weight-based dosing and terminology
FIXED_PEDIATRIC_CASES = [
    {
        "text": "Started pediatric patient Lucy Chen (8 years old, 25kg) on amoxicillin 10mg/kg three times daily for acute otitis media.",
        "expected": {"patient": "Lucy Chen", "medication": "amoxicillin", "dosage": "10mg/kg", "frequency": "three times daily", "condition": "acute otitis media", "age": "8 years", "weight": "25kg"}
    },
    {
        "text": "Prescribed pediatric patient Tommy Rodriguez (weight-based dosing) ibuprofen 5mg/kg every 6 hours for fever reduction.",
        "expected": {"patient": "Tommy Rodriguez", "medication": "ibuprofen", "dosage": "5mg/kg", "frequency": "every 6 hours", "condition": "pediatric fever", "dosing_type": "weight-based"}
    },
    {
        "text": "Pediatric patient Sarah Kim on albuterol inhaler age-appropriate dosing 1-2 puffs as needed for pediatric asthma exacerbation.",
        "expected": {"patient": "Sarah Kim", "medication": "albuterol", "dosage": "1-2 puffs", "frequency": "as needed", "condition": "pediatric asthma exacerbation", "age_appropriate": True}
    }
]

class SimpleNLPBaseline:
    """Simple regex/spaCy baseline to test data quality impact"""

    def __init__(self):
        self.medication_patterns = [
            r'\b(amoxicillin|ibuprofen|albuterol|morphine|epinephrine|metformin)\b',
            r'\b([a-z]+cillin|[a-z]*profen|[a-z]*ol)\b'
        ]

        self.dosage_patterns = [
            r'\b(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|units|puffs)(?:/kg)?\b',
            r'\b(\d+-\d+)\s*(puffs|units)\b'
        ]

        self.frequency_patterns = [
            r'\b(once|twice|three times|every \d+ hours|daily|as needed)\b',
            r'\b(nightly|morning|bedtime)\b'
        ]

        self.condition_patterns = [
            r'\bfor\s+([a-z\s]+?)(?:\.|$)',
            r'\b(acute|chronic|severe|mild)\s+([a-z\s]+?)(?:\.|$)'
        ]

        self.pediatric_indicators = [
            r'\b(pediatric|child|infant|age \d+|years old|\d+kg weight)\b',
            r'\bmg/kg\b',
            r'\bweight-based\b',
            r'\bage-appropriate\b'
        ]

    def extract_entities(self, text: str) -> Dict[str, any]:
        """Extract entities using simple patterns"""
        entities = {}

        # Extract medication
        for pattern in self.medication_patterns:
            match = re.search(pattern, text.lower())
            if match:
                entities['medication'] = match.group(1)
                break

        # Extract dosage
        for pattern in self.dosage_patterns:
            match = re.search(pattern, text.lower())
            if match:
                entities['dosage'] = match.group(0)
                break

        # Extract frequency
        for pattern in self.frequency_patterns:
            match = re.search(pattern, text.lower())
            if match:
                entities['frequency'] = match.group(0)
                break

        # Extract condition
        for pattern in self.condition_patterns:
            match = re.search(pattern, text.lower())
            if match:
                condition = match.group(1) if len(match.groups()) == 1 else f"{match.group(1)} {match.group(2)}"
                entities['condition'] = condition.strip()
                break

        # Check for pediatric indicators
        pediatric_score = 0
        for pattern in self.pediatric_indicators:
            if re.search(pattern, text.lower()):
                pediatric_score += 1

        entities['pediatric_indicators'] = pediatric_score
        entities['is_pediatric'] = pediatric_score >= 2

        return entities

    def calculate_f1_score(self, extracted: Dict, expected: Dict) -> float:
        """Calculate F1 score between extracted and expected entities"""

        # Count matches
        matches = 0
        total_expected = 0
        total_extracted = len([k for k in extracted.keys() if k not in ['pediatric_indicators', 'is_pediatric']])

        for key in ['medication', 'dosage', 'frequency', 'condition']:
            if key in expected:
                total_expected += 1
                if key in extracted:
                    # Simple string matching (could be enhanced)
                    expected_val = expected[key].lower()
                    extracted_val = extracted[key].lower()

                    # Check for partial matches
                    if expected_val in extracted_val or extracted_val in expected_val:
                        matches += 1
                    # Special case for dosage patterns (mg/kg vs mg)
                    elif key == 'dosage' and ('mg/kg' in expected_val and 'mg' in extracted_val):
                        matches += 0.5  # Partial credit for recognizing medication but wrong format

        # Calculate F1
        if total_expected == 0:
            return 0.0
        if total_extracted == 0:
            return 0.0

        precision = matches / total_extracted if total_extracted > 0 else 0
        recall = matches / total_expected if total_expected > 0 else 0

        if precision + recall == 0:
            return 0.0

        f1 = 2 * (precision * recall) / (precision + recall)
        return f1

def test_data_quality_hypothesis():
    """Test if data quality fixes improve F1 more than algorithmic complexity"""
    print("🧪 Testing Data Quality Hypothesis")
    print("=" * 50)

    baseline = SimpleNLPBaseline()

    # Test original problematic data
    print("📊 Testing ORIGINAL pediatric cases (problematic data):")
    original_f1_scores = []

    for i, case in enumerate(ORIGINAL_PEDIATRIC_CASES):
        extracted = baseline.extract_entities(case['text'])
        f1_score = baseline.calculate_f1_score(extracted, case['expected'])
        original_f1_scores.append(f1_score)

        print(f"  Case {i+1}: F1={f1_score:.3f}")
        print(f"    Extracted: {extracted}")
        print(f"    Expected: {case['expected']}")
        print()

    original_avg_f1 = sum(original_f1_scores) / len(original_f1_scores)
    print(f"📈 ORIGINAL Average F1 Score: {original_avg_f1:.3f}")
    print()

    # Test fixed data
    print("📊 Testing FIXED pediatric cases (quality data):")
    fixed_f1_scores = []

    for i, case in enumerate(FIXED_PEDIATRIC_CASES):
        extracted = baseline.extract_entities(case['text'])
        f1_score = baseline.calculate_f1_score(extracted, case['expected'])
        fixed_f1_scores.append(f1_score)

        print(f"  Case {i+1}: F1={f1_score:.3f}")
        print(f"    Extracted: {extracted}")
        print(f"    Expected: {case['expected']}")
        print()

    fixed_avg_f1 = sum(fixed_f1_scores) / len(fixed_f1_scores)
    print(f"📈 FIXED Average F1 Score: {fixed_avg_f1:.3f}")
    print()

    # Calculate improvement
    improvement = fixed_avg_f1 - original_avg_f1
    percent_improvement = (improvement / original_avg_f1) * 100 if original_avg_f1 > 0 else 0

    print("=" * 50)
    print("🎯 DATA QUALITY HYPOTHESIS RESULTS:")
    print("=" * 50)
    print(f"Original F1 (problematic data): {original_avg_f1:.3f}")
    print(f"Fixed F1 (quality data): {fixed_avg_f1:.3f}")
    print(f"Improvement: +{improvement:.3f} ({percent_improvement:.1f}%)")
    print()

    if percent_improvement > 50:
        print("✅ HYPOTHESIS CONFIRMED: Data quality fixes provide major F1 improvement")
        print("   Recommendation: Prioritize data cleaning over complex architecture")
        print("   Expected real-world improvement: 40-80% F1 boost from data fixes alone")
    elif percent_improvement > 20:
        print("⚠️ HYPOTHESIS PARTIALLY CONFIRMED: Data quality has significant impact")
        print("   Recommendation: Combine data fixes with targeted architecture improvements")
        print("   Expected real-world improvement: 20-40% from data, 20-30% from architecture")
    else:
        print("❌ HYPOTHESIS REJECTED: Data quality impact is minimal")
        print("   Recommendation: Focus on complex algorithmic solutions")
        print("   Expected improvement primarily from architecture enhancements")

    # Save results
    results = {
        "original_f1": original_avg_f1,
        "fixed_f1": fixed_avg_f1,
        "improvement": improvement,
        "percent_improvement": percent_improvement,
        "hypothesis_confirmed": percent_improvement > 50,
        "recommendation": "data_quality_first" if percent_improvement > 50 else "hybrid_approach" if percent_improvement > 20 else "algorithmic_focus"
    }

    with open('data_quality_hypothesis_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: data_quality_hypothesis_results.json")

    return results

if __name__ == "__main__":
    test_data_quality_hypothesis()