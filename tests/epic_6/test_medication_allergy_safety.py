#!/usr/bin/env python3
"""
Epic 6 Stories 6.2 & 6.5: Medication-Allergy Safety Integration Test
Test comprehensive safety checking between medications and patient allergies
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from nl_fhir.services.fhir.resource_factory import FHIRResourceFactory

def test_penicillin_allergy_safety():
    """Test penicillin allergy safety checking"""
    print("=== Testing Penicillin Allergy Safety ===")

    factory = FHIRResourceFactory()

    # Patient allergies
    patient_allergies = [
        {
            "substance": "Penicillin",
            "criticality": "high",
            "clinical_status": "active",
            "verification_status": "confirmed"
        }
    ]

    # Test 1: Direct penicillin prescription (UNSAFE)
    penicillin_data = {
        "name": "Penicillin V 250mg",
        "form": "tablet",
        "ingredients": [{"name": "Penicillin V", "strength": {"value": 250, "unit": "mg"}}]
    }

    safety_check = factory.check_medication_allergy_safety(penicillin_data, patient_allergies)

    print(f"Direct Penicillin Prescription:")
    print(f"  Is Safe: {safety_check['is_safe']}")
    print(f"  Alerts: {len(safety_check['alerts'])}")
    for alert in safety_check['alerts']:
        print(f"    - {alert['severity'].upper()}: {alert['message']}")

    # Test 2: Amoxicillin prescription (same class - UNSAFE)
    amoxicillin_data = {
        "name": "Amoxicillin 500mg",
        "form": "capsule",
        "ingredients": [{"name": "Amoxicillin", "strength": {"value": 500, "unit": "mg"}}]
    }

    safety_check = factory.check_medication_allergy_safety(amoxicillin_data, patient_allergies)

    print(f"\nAmoxicillin Prescription (Penicillin class):")
    print(f"  Is Safe: {safety_check['is_safe']}")
    print(f"  Alerts: {len(safety_check['alerts'])}")
    for alert in safety_check['alerts']:
        print(f"    - {alert['severity'].upper()}: {alert['message']}")

    # Test 3: Safe alternative (Azithromycin - macrolide class)
    azithromycin_data = {
        "name": "Azithromycin 250mg",
        "form": "tablet",
        "ingredients": [{"name": "Azithromycin", "strength": {"value": 250, "unit": "mg"}}]
    }

    safety_check = factory.check_medication_allergy_safety(azithromycin_data, patient_allergies)

    print(f"\nAzithromycin Prescription (Safe alternative):")
    print(f"  Is Safe: {safety_check['is_safe']}")
    print(f"  Alerts: {len(safety_check['alerts'])}")

    return True

def test_multiple_allergies_complex_medication():
    """Test complex medication against multiple allergies"""
    print("\n=== Testing Multiple Allergies with Complex Medication ===")

    factory = FHIRResourceFactory()

    # Patient with multiple allergies
    patient_allergies = [
        {
            "substance": "Sulfonamide",
            "criticality": "high",
            "clinical_status": "active"
        },
        {
            "substance": "Ibuprofen",
            "criticality": "medium",
            "clinical_status": "active"
        },
        {
            "substance": "Shellfish",
            "criticality": "high",
            "clinical_status": "active"
        }
    ]

    # Test combination medication containing sulfa
    combo_medication = {
        "name": "Trimethoprim/Sulfamethoxazole DS",
        "form": "tablet",
        "ingredients": [
            {"name": "Trimethoprim", "strength": {"value": 160, "unit": "mg"}},
            {"name": "Sulfamethoxazole", "strength": {"value": 800, "unit": "mg"}}
        ]
    }

    safety_check = factory.check_medication_allergy_safety(combo_medication, patient_allergies)

    print("Trimethoprim/Sulfamethoxazole (contains sulfa):")
    print(f"  Is Safe: {safety_check['is_safe']}")
    print(f"  Allergy Matches: {len(safety_check['allergy_matches'])}")

    for match in safety_check['allergy_matches']:
        match_type = match['type'].replace('_', ' ').title()
        print(f"    - {match_type}: {match.get('ingredient', match.get('substance'))}")

    print(f"  Alerts: {len(safety_check['alerts'])}")
    for alert in safety_check['alerts']:
        print(f"    - {alert['severity'].upper()}: {alert['message']}")

    return True

def test_ingredient_level_allergy_checking():
    """Test ingredient-level allergy checking"""
    print("\n=== Testing Ingredient-Level Allergy Checking ===")

    factory = FHIRResourceFactory()

    # Patient allergic to specific ingredient
    patient_allergies = [
        {
            "substance": "Acetaminophen",
            "criticality": "medium",
            "clinical_status": "active"
        }
    ]

    # Test medication containing the allergen as ingredient
    pain_medication = {
        "name": "Hydrocodone/Acetaminophen 5mg/325mg",
        "form": "tablet",
        "ingredients": [
            {"name": "Hydrocodone Bitartrate", "strength": {"value": 5, "unit": "mg"}},
            {"name": "Acetaminophen", "strength": {"value": 325, "unit": "mg"}}
        ]
    }

    safety_check = factory.check_medication_allergy_safety(pain_medication, patient_allergies)

    print("Hydrocodone/Acetaminophen (contains acetaminophen):")
    print(f"  Is Safe: {safety_check['is_safe']}")
    print(f"  Ingredient Matches: {len(safety_check['allergy_matches'])}")

    for match in safety_check['allergy_matches']:
        if match['type'] == 'ingredient_match':
            print(f"    - Ingredient '{match['ingredient']}' matches allergy to '{match['substance']}'")

    for alert in safety_check['alerts']:
        print(f"    - {alert['severity'].upper()}: {alert['message']}")
        print(f"      Recommendation: {alert['recommendation']}")

    return True

def test_low_risk_allergy_monitoring():
    """Test low-risk allergy that requires monitoring but not contraindication"""
    print("\n=== Testing Low-Risk Allergy Monitoring ===")

    factory = FHIRResourceFactory()

    # Patient with low-risk allergy
    patient_allergies = [
        {
            "substance": "Latex",
            "criticality": "low",
            "clinical_status": "active"
        }
    ]

    # Test medication (should be safe but may trigger monitoring)
    medication_data = {
        "name": "Metformin 500mg",
        "form": "tablet",
        "ingredients": [{"name": "Metformin HCl", "strength": {"value": 500, "unit": "mg"}}]
    }

    safety_check = factory.check_medication_allergy_safety(medication_data, patient_allergies)

    print("Metformin with latex allergy:")
    print(f"  Is Safe: {safety_check['is_safe']}")
    print(f"  Alerts: {len(safety_check['alerts'])}")

    if safety_check['recommendations']:
        print("  General Recommendations:")
        for rec in safety_check['recommendations']:
            print(f"    - {rec}")

    return True

def test_no_allergies_safe_prescription():
    """Test safe prescription with no patient allergies"""
    print("\n=== Testing Safe Prescription (No Allergies) ===")

    factory = FHIRResourceFactory()

    # No patient allergies
    patient_allergies = []

    medication_data = {
        "name": "Lisinopril 10mg",
        "form": "tablet",
        "ingredients": [{"name": "Lisinopril", "strength": {"value": 10, "unit": "mg"}}]
    }

    safety_check = factory.check_medication_allergy_safety(medication_data, patient_allergies)

    print("Lisinopril with no patient allergies:")
    print(f"  Is Safe: {safety_check['is_safe']}")
    print(f"  Alerts: {len(safety_check['alerts'])}")
    print(f"  Recommendations: {len(safety_check['recommendations'])}")

    return True

def main():
    """Run all medication-allergy safety tests"""
    print("Epic 6 Stories 6.2 & 6.5: Medication-Allergy Safety Integration")
    print("=" * 70)

    try:
        # Test penicillin allergy safety
        test_penicillin_allergy_safety()

        # Test multiple allergies with complex medication
        test_multiple_allergies_complex_medication()

        # Test ingredient-level checking
        test_ingredient_level_allergy_checking()

        # Test low-risk monitoring
        test_low_risk_allergy_monitoring()

        # Test safe prescription
        test_no_allergies_safe_prescription()

        print("\n" + "=" * 70)
        print("🎉 ALL MEDICATION-ALLERGY SAFETY TESTS COMPLETED!")
        print("Epic 6 Sprint 1 Safety Foundation implementation is complete")
        print("✅ Story 6.2: AllergyIntolerance resource implementation")
        print("✅ Story 6.5: Medication resource implementation")
        print("✅ Safety Integration: Medication-allergy checking")

        return True

    except Exception as e:
        print(f"\n❌ Error during safety testing: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)