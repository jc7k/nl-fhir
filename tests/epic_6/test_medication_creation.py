#!/usr/bin/env python3
"""
Epic 6 Story 6.5: Test Medication Resource Creation
Test script for validating medication FHIR resource implementation
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter

def test_basic_medication():
    """Test basic medication resource creation"""
    print("=== Testing Basic Medication Resource Creation ===")

    factory = get_factory_adapter()

    medication_data = {
        "name": "Amoxicillin 500mg Capsules",
        "strength": "500mg",
        "form": "capsule",
        "manufacturer": "Generic Pharma"
    }

    try:
        medication_resource = factory.create_medication_resource(medication_data)

        print("✅ Medication resource created successfully")
        print(f"Resource ID: {medication_resource['id']}")
        print(f"Resource Type: {medication_resource['resourceType']}")
        print(f"Status: {medication_resource['status']}")

        # Check RxNorm coding
        if 'code' in medication_resource and 'coding' in medication_resource['code']:
            for coding in medication_resource['code']['coding']:
                if coding.get('system') == 'http://www.nlm.nih.gov/research/umls/rxnorm':
                    print(f"✅ RxNorm code: {coding.get('code')} - {coding.get('display')}")

        # Check form
        if 'form' in medication_resource:
            print(f"✅ Form: {medication_resource['form'].get('text', 'Not specified')}")

        return medication_resource

    except Exception as e:
        print(f"❌ Error creating medication resource: {str(e)}")
        return None

def test_complex_medication():
    """Test complex medication with ingredients and batch info"""
    print("\n=== Testing Complex Medication with Ingredients ===")

    factory = get_factory_adapter()

    medication_data = {
        "name": "Hydrocodone/Acetaminophen 5mg/325mg",
        "form": "tablet",
        "manufacturer": "Watson Pharmaceuticals",
        "ingredients": [
            {
                "name": "Hydrocodone Bitartrate",
                "strength": {
                    "value": 5,
                    "unit": "mg"
                },
                "active": True
            },
            {
                "name": "Acetaminophen",
                "strength": {
                    "value": 325,
                    "unit": "mg"
                },
                "active": True
            }
        ],
        "batch": {
            "lotNumber": "LOT123456",
            "expirationDate": "2025-12-31"
        }
    }

    try:
        medication_resource = factory.create_medication_resource(medication_data)

        print("✅ Complex medication resource created successfully")
        print(f"Resource ID: {medication_resource['id']}")

        # Check ingredients
        if 'ingredient' in medication_resource:
            print(f"✅ Ingredients count: {len(medication_resource['ingredient'])}")
            for idx, ingredient in enumerate(medication_resource['ingredient']):
                ingredient_name = ingredient['itemCodeableConcept'].get('text', 'Unknown')
                strength = "Unknown strength"
                if 'strength' in ingredient:
                    strength_num = ingredient['strength']['numerator']
                    strength = f"{strength_num['value']}{strength_num['unit']}"
                print(f"  - Ingredient {idx+1}: {ingredient_name} ({strength})")

        # Check batch info
        if 'batch' in medication_resource:
            batch = medication_resource['batch']
            print(f"✅ Batch info: Lot {batch.get('lotNumber', 'N/A')}, Expires {batch.get('expirationDate', 'N/A')}")

        return medication_resource

    except Exception as e:
        print(f"❌ Error creating complex medication resource: {str(e)}")
        return None

def test_fallback_medication():
    """Test fallback medication creation"""
    print("\n=== Testing Fallback Medication ===")

    factory = get_factory_adapter()

    medication_data = {
        "name": "Unknown Brand Medication",
        "form": "injection",
        "ingredients": ["Active Ingredient A", "Inactive Ingredient B"]
    }

    try:
        # Test the fallback method directly
        medication_resource = factory._create_fallback_medication(medication_data)

        print("✅ Fallback medication resource created successfully")
        print(f"Resource ID: {medication_resource['id']}")
        print(f"Name: {medication_resource['code']['text']}")
        print(f"Form: {medication_resource.get('form', {}).get('text', 'Not specified')}")

        if 'ingredient' in medication_resource:
            print(f"✅ Fallback ingredients count: {len(medication_resource['ingredient'])}")
            for ingredient in medication_resource['ingredient']:
                print(f"  - {ingredient['itemCodeableConcept']['text']}")

        return medication_resource

    except Exception as e:
        print(f"❌ Error creating fallback medication resource: {str(e)}")
        return None

def validate_medication_structure(medication_resource):
    """Validate FHIR medication resource structure"""
    print("\n=== Validating FHIR R4 Medication Structure ===")

    required_fields = ['resourceType', 'id', 'status']

    for field in required_fields:
        if field not in medication_resource:
            print(f"❌ Missing required field: {field}")
            return False
        else:
            print(f"✅ Required field present: {field}")

    # Check resource type
    if medication_resource['resourceType'] != 'Medication':
        print(f"❌ Invalid resourceType: {medication_resource['resourceType']}")
        return False

    # Check status values
    valid_statuses = ['active', 'inactive', 'entered-in-error']
    if medication_resource['status'] not in valid_statuses:
        print(f"❌ Invalid status: {medication_resource['status']}")
        return False

    print("✅ Medication resource structure is valid")
    return True

def main():
    """Run all medication tests"""
    print("Epic 6 Story 6.5: Medication Resource Implementation Test")
    print("=" * 60)

    # Test basic medication
    basic_med = test_basic_medication()
    if basic_med and validate_medication_structure(basic_med):
        print("✅ Basic medication test PASSED")
    else:
        print("❌ Basic medication test FAILED")
        return False

    # Test complex medication
    complex_med = test_complex_medication()
    if complex_med and validate_medication_structure(complex_med):
        print("✅ Complex medication test PASSED")
    else:
        print("❌ Complex medication test FAILED")
        return False

    # Test fallback medication
    fallback_med = test_fallback_medication()
    if fallback_med and validate_medication_structure(fallback_med):
        print("✅ Fallback medication test PASSED")
    else:
        print("❌ Fallback medication test FAILED")
        return False

    print("\n" + "=" * 60)
    print("🎉 ALL MEDICATION TESTS PASSED!")
    print("Story 6.5 Medication resource implementation is working correctly")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)