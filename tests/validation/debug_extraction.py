#!/usr/bin/env python3
"""
Debug exactly what's being extracted for failing test cases
"""

import sys
sys.path.append('../../src')

from nl_fhir.services.nlp.models import model_manager

def debug_extraction():
    """Debug extraction for failing cases"""

    failing_cases = [
        # Pediatrics failures
        ("cephalexin case", "Start neonate patient (weight: 12kg) on cephalexin 25mg/kg/day BID for infection."),
        ("azithromycin case", "Start child patient (weight: 18kg) on azithromycin 15mg/kg/day BID for infection."),

        # Cardiology failures
        ("captopril case", "Start patient on captopril 5mg daily for diastolic dysfunction."),
        ("enalapril case", "Start patient on enalapril 5mg daily for cardiomyopathy. Monitor INR."),
        ("ramipril case", "Start patient on ramipril 5mg daily for CHF. Monitor electrolytes."),

        # Working case for comparison
        ("lisinopril case", "Start patient on lisinopril 5mg daily for systolic dysfunction."),
        ("amoxicillin case", "Start neonate patient (weight: 8kg) on amoxicillin 25mg/kg/day BID for infection.")
    ]

    for case_name, text in failing_cases:
        print(f"\n🔬 DEBUGGING: {case_name}")
        print(f"Text: {text}")

        try:
            extracted = model_manager.extract_medical_entities(text)

            print(f"Extracted entities:")
            for category, entities in extracted.items():
                if entities:
                    print(f"  {category}: {len(entities)} entities")
                    for i, entity in enumerate(entities[:3]):  # Show first 3
                        print(f"    {i+1}. {entity.get('text', 'N/A')} (confidence: {entity.get('confidence', 'N/A')})")
                else:
                    print(f"  {category}: 0 entities")

        except Exception as e:
            print(f"  ❌ Error: {e}")

        print("-" * 50)

if __name__ == "__main__":
    debug_extraction()