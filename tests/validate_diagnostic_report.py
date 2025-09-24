#!/usr/bin/env python3
"""
Quick Validation Script for DiagnosticReport Implementation
Tests basic functionality with simple examples
"""

import sys
from pathlib import Path

# Add src path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from nl_fhir.services.fhir.diagnostic_report_implementation import DiagnosticReportFactory
    from nl_fhir.services.nlp.diagnostic_report_patterns import DiagnosticReportExtractor
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

def test_basic_functionality():
    """Test basic DiagnosticReport functionality"""

    print("\n🧪 BASIC FUNCTIONALITY TEST")
    print("=" * 40)

    # Initialize components
    factory = DiagnosticReportFactory()
    extractor = DiagnosticReportExtractor()

    # Test cases
    test_cases = [
        {
            "name": "Simple Lab Report",
            "text": "CBC shows WBC 7.5, Hemoglobin 14.2 g/dL, all normal",
            "expected_category": "laboratory"
        },
        {
            "name": "Chest X-ray",
            "text": "Chest X-ray shows clear lung fields, no acute findings",
            "expected_category": "radiology"
        },
        {
            "name": "ECG Report",
            "text": "ECG shows normal sinus rhythm at 72 bpm",
            "expected_category": "cardiology"
        },
        {
            "name": "Skin Biopsy",
            "text": "Skin biopsy reveals benign nevus, no malignancy",
            "expected_category": "pathology"
        }
    ]

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"   Text: {test_case['text']}")

        try:
            # Test NLP extraction
            reports = extractor.extract_diagnostic_reports(test_case['text'])

            if not reports:
                print("   ❌ No reports extracted")
                continue

            report = reports[0]
            print(f"   🔍 Extracted category: {report.get('category')}")

            # Check category
            if report.get('category') == test_case['expected_category']:
                print("   ✅ Category correct")
            else:
                print(f"   ⚠️ Category mismatch: expected {test_case['expected_category']}")

            # Test FHIR creation
            fhir_resource = factory.create_diagnostic_report(
                report,
                "patient-test-001",
                f"test-{i}"
            )

            # Validate basic FHIR structure
            if (fhir_resource.get('resourceType') == 'DiagnosticReport' and
                'id' in fhir_resource and
                'status' in fhir_resource and
                'subject' in fhir_resource):
                print("   ✅ FHIR resource created successfully")
                print(f"   📋 Resource ID: {fhir_resource['id']}")
                print(f"   📊 Status: {fhir_resource['status']}")
                passed += 1
            else:
                print("   ❌ FHIR resource structure invalid")

        except Exception as e:
            print(f"   💥 Error: {str(e)}")

    print(f"\n📊 RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 All tests passed! Implementation is working correctly.")
    elif passed >= total * 0.75:
        print("⚠️ Most tests passed. Minor issues to resolve.")
    else:
        print("❌ Multiple failures. Implementation needs work.")

    return passed == total

def test_category_detection():
    """Test category detection patterns"""

    print("\n🔍 CATEGORY DETECTION TEST")
    print("=" * 40)

    extractor = DiagnosticReportExtractor()

    category_tests = [
        # Laboratory
        ("lab results show glucose 95", "laboratory"),
        ("blood work completed", "laboratory"),
        ("urinalysis pending", "laboratory"),
        ("CBC with differential", "laboratory"),

        # Radiology
        ("chest x-ray clear", "radiology"),
        ("CT scan normal", "radiology"),
        ("MRI brain shows", "radiology"),
        ("ultrasound abdomen", "radiology"),

        # Pathology
        ("biopsy results available", "pathology"),
        ("histology confirms", "pathology"),
        ("cytology negative", "pathology"),

        # Cardiology
        ("ECG normal sinus rhythm", "cardiology"),
        ("echo shows EF 55%", "cardiology"),
        ("stress test negative", "cardiology")
    ]

    correct = 0
    total = len(category_tests)

    for text, expected_category in category_tests:
        reports = extractor.extract_diagnostic_reports(text)

        if reports and reports[0].get('category') == expected_category:
            correct += 1
            print(f"✅ '{text}' → {expected_category}")
        else:
            actual = reports[0].get('category') if reports else 'None'
            print(f"❌ '{text}' → expected {expected_category}, got {actual}")

    print(f"\n📊 Category Detection: {correct}/{total} correct ({correct/total*100:.1f}%)")
    return correct >= total * 0.8

def test_fhir_compliance():
    """Test FHIR compliance basics"""

    print("\n🏗️ FHIR COMPLIANCE TEST")
    print("=" * 40)

    factory = DiagnosticReportFactory()

    # Test data
    test_data = {
        "text": "Laboratory results show normal CBC",
        "category": "laboratory",
        "procedure": "CBC",
        "conclusion": "All values within normal limits"
    }

    try:
        resource = factory.create_diagnostic_report(
            test_data,
            "patient-123",
            "test-compliance"
        )

        # Check required fields
        required_fields = [
            "resourceType",
            "id",
            "status",
            "category",
            "code",
            "subject",
            "effectiveDateTime"
        ]

        missing_fields = []
        for field in required_fields:
            if field not in resource:
                missing_fields.append(field)

        if not missing_fields:
            print("✅ All required FHIR fields present")
        else:
            print(f"❌ Missing required fields: {missing_fields}")
            return False

        # Check field formats
        if resource["resourceType"] != "DiagnosticReport":
            print(f"❌ Wrong resourceType: {resource['resourceType']}")
            return False

        if not resource["subject"]["reference"].startswith("Patient/"):
            print(f"❌ Invalid subject reference: {resource['subject']['reference']}")
            return False

        if not isinstance(resource["category"], list) or len(resource["category"]) == 0:
            print("❌ Category should be non-empty list")
            return False

        print("✅ Basic FHIR structure is valid")
        print(f"   Resource Type: {resource['resourceType']}")
        print(f"   ID: {resource['id']}")
        print(f"   Status: {resource['status']}")
        print(f"   Category: {resource['category'][0]['coding'][0]['display']}")

        return True

    except Exception as e:
        print(f"❌ FHIR creation failed: {str(e)}")
        return False

def main():
    """Run all validation tests"""

    print("🧪 DiagnosticReport Implementation Validation")
    print("=" * 50)

    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Category Detection", test_category_detection),
        ("FHIR Compliance", test_fhir_compliance)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🔬 Running {test_name} Test...")
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"💥 {test_name} test failed with error: {str(e)}")
            results.append((test_name, False))

    print(f"\n{'='*50}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*50}")

    passed_tests = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")

    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Implementation is ready for integration.")
    elif passed_tests >= total_tests * 0.66:
        print("⚠️ Most tests passed. Minor fixes needed.")
    else:
        print("❌ Implementation needs significant work.")

    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)