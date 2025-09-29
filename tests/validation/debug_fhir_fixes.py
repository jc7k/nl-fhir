#!/usr/bin/env python3
"""
Debug script to validate FHIR bundle fixes
Tests all the identified issues and confirms fixes
"""

import sys
import json
import asyncio
from typing import Dict, Any

# Add the project source to Python path
sys.path.insert(0, '/home/user/projects/nl-fhir/src')

from nl_fhir.services.nlp.extractors.regex_extractor import RegexExtractor
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter
from nl_fhir.services.fhir.bundle_assembler import FHIRBundleAssembler
from nl_fhir.services.fhir.validator import FHIRValidator


def test_patient_name_extraction():
    """Test patient name extraction fixes"""
    print("=== Testing Patient Name Extraction ===")
    
    extractor = RegexExtractor()
    
    test_cases = [
        "Patient: Jane Doe",
        "patient: jane doe", 
        "Patient: John Smith",
        "patient: Sarah Williams",
        "Start patient Jane Doe on medication"
    ]
    
    for test_case in test_cases:
        result = extractor.extract_entities(test_case)
        patients = result.get("patients", [])
        patient_names = [p["text"] for p in patients]
        print(f"'{test_case}' -> Patients: {patient_names}")
    
    print()


def test_medication_codes():
    """Test medication code fixes - no more unknown codes"""
    print("=== Testing Medication Code Fixes ===")
    
    factory = get_factory_adapter()
    factory.initialize()
    
    test_medications = [
        {"name": "cisplatin", "dosage": "80mg/m²"},
        {"name": "carboplatin", "dosage": "AUC 6"},
        {"name": "metformin", "dosage": "500mg"},
        {"name": "unknown-drug", "dosage": "100mg"}
    ]
    
    for med_data in test_medications:
        concept = factory._create_medication_concept(med_data)
        print(f"\nMedication: {med_data['name']}")
        for coding in concept.coding:
            print(f"  System: {coding.system}")
            print(f"  Code: {coding.code}")
            print(f"  Display: {coding.display}")
            
            # Check for unwanted "unknown" codes
            if "unknown" in coding.code and med_data['name'] in ["cisplatin", "carboplatin", "metformin"]:
                print(f"  ❌ ISSUE: Found unknown code for known medication!")
            elif "unknown" not in coding.code and med_data['name'] in ["cisplatin", "carboplatin", "metformin"]:
                print(f"  ✅ GOOD: Proper code for known medication")
    
    print()


def test_lab_test_extraction():
    """Test enhanced lab test extraction"""
    print("=== Testing Lab Test Extraction ===")
    
    extractor = RegexExtractor()
    
    test_cases = [
        "Order CBC and CMP",
        "Check troponin levels",
        "Send blood cultures",
        "cisplatin 80mg/m² IV over 1 hour, followed by carboplatin AUC 6, order CBC and CMP",
    ]
    
    for test_case in test_cases:
        result = extractor.extract_entities(test_case)
        lab_tests = result.get("lab_tests", [])
        lab_names = [lab["text"] for lab in lab_tests]
        print(f"'{test_case}' -> Lab tests: {lab_names}")
    
    print()


def test_multiple_medication_extraction():
    """Test multiple medication extraction in complex text"""
    print("=== Testing Multiple Medication Extraction ===")
    
    extractor = RegexExtractor()
    
    complex_text = "cisplatin 80mg/m² IV over 1 hour, followed by carboplatin AUC 6"
    
    result = extractor.extract_entities(complex_text)
    medications = result.get("medications", [])
    med_names = [med["text"] for med in medications]
    
    print(f"Complex text: '{complex_text}'")
    print(f"Extracted medications: {med_names}")
    print(f"Expected: ['cisplatin', 'carboplatin']")
    
    if 'cisplatin' in med_names and 'carboplatin' in med_names:
        print("✅ SUCCESS: Both medications extracted!")
    else:
        print("❌ ISSUE: Missing medications")
    
    print()


async def test_bundle_creation():
    """Test FHIR bundle creation fixes"""
    print("=== Testing FHIR Bundle Creation ===")
    
    factory = get_factory_adapter()
    factory.initialize()
    
    assembler = FHIRBundleAssembler()
    assembler.initialize()
    
    validator = FHIRValidator()
    validator.initialize()
    
    # Create test resources
    patient_resource = factory.create_patient_resource(
        {"patient_ref": "PT-123", "name": "Jane Doe"}
    )
    
    med_resource = factory.create_medication_request(
        {"name": "cisplatin", "dosage": "80mg/m²", "frequency": "daily"},
        patient_resource["id"]
    )
    
    resources = [patient_resource, med_resource]
    
    # Test bundle creation
    bundle = assembler.create_transaction_bundle(resources, "test-123")
    
    print(f"Bundle created: {bundle.get('resourceType')} with {len(bundle.get('entry', []))} entries")
    
    # Test bundle validation
    validation_result = validator.validate_bundle(bundle, "test-123")
    
    print(f"Bundle validation:")
    print(f"  Valid: {validation_result['is_valid']}")
    print(f"  Total issues: {validation_result['total_issues']}")
    
    for issue in validation_result.get('errors', []):
        print(f"  ERROR: {issue['message']}")
    
    for issue in validation_result.get('warnings', [])[:3]:  # Show first 3 warnings
        print(f"  WARNING: {issue['message']}")
    
    # Test individual resource validation
    print(f"\nIndividual resource validation:")
    for resource in resources:
        resource_result = validator.validate_resource(resource, "test-123")
        print(f"  {resource['resourceType']}: Valid = {resource_result['is_valid']}")
    
    print()


async def main():
    """Run all debug tests"""
    print("FHIR Bundle Fixes Debug Test")
    print("="*50)
    
    test_patient_name_extraction()
    test_medication_codes() 
    test_lab_test_extraction()
    test_multiple_medication_extraction()
    await test_bundle_creation()
    
    print("="*50)
    print("Debug testing completed!")


if __name__ == "__main__":
    asyncio.run(main())
