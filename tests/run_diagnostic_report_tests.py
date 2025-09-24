#!/usr/bin/env python3
"""
Test Runner for DiagnosticReport Implementation
Story ID: NL-FHIR-DR-001
Validates NLP extraction and FHIR resource creation using sample clinical texts
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add src path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nl_fhir.services.fhir.diagnostic_report_implementation import DiagnosticReportFactory
from nl_fhir.services.nlp.diagnostic_report_patterns import DiagnosticReportExtractor


class DiagnosticReportTestRunner:
    """Test runner for DiagnosticReport implementation with sample data"""

    def __init__(self):
        self.factory = DiagnosticReportFactory()
        self.extractor = DiagnosticReportExtractor()
        self.load_sample_data()

    def load_sample_data(self):
        """Load sample clinical texts from JSON file"""
        samples_file = Path(__file__).parent / "data" / "diagnostic_report_samples.json"

        with open(samples_file, 'r') as f:
            self.samples = json.load(f)

    def run_all_tests(self):
        """Run all test categories"""
        print("🧪 DiagnosticReport Implementation Test Suite")
        print("=" * 60)

        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "categories": {}
        }

        # Test each category
        categories = [
            "laboratory_reports",
            "radiology_reports",
            "pathology_reports",
            "cardiology_reports",
            "complex_scenarios",
            "edge_cases"
        ]

        for category in categories:
            print(f"\n📋 Testing {category.replace('_', ' ').title()}")
            print("-" * 40)

            category_results = self.test_category(category)
            results["categories"][category] = category_results
            results["total_tests"] += category_results["total"]
            results["passed"] += category_results["passed"]
            results["failed"] += category_results["failed"]

        self.print_summary(results)
        return results

    def test_category(self, category: str) -> Dict[str, int]:
        """Test a specific category of samples"""

        if category not in self.samples["test_scenarios"]:
            print(f"⚠️  Category {category} not found in samples")
            return {"total": 0, "passed": 0, "failed": 0}

        samples = self.samples["test_scenarios"][category]
        results = {"total": len(samples), "passed": 0, "failed": 0}

        for sample in samples:
            try:
                success = self.test_single_sample(sample, category)
                if success:
                    results["passed"] += 1
                    print(f"✅ {sample['id']}: PASSED")
                else:
                    results["failed"] += 1
                    print(f"❌ {sample['id']}: FAILED")

            except Exception as e:
                results["failed"] += 1
                print(f"💥 {sample['id']}: ERROR - {str(e)}")

        return results

    def test_single_sample(self, sample: Dict[str, Any], category: str) -> bool:
        """Test a single clinical text sample"""

        clinical_text = sample["clinical_text"]
        expected = sample.get("expected_extraction", {})

        # Step 1: Test NLP extraction
        extracted_reports = self.extractor.extract_diagnostic_reports(clinical_text)

        if not extracted_reports:
            print(f"  🔍 No reports extracted from text")
            return False

        # For complex scenarios with multiple expected reports
        if category == "complex_scenarios" and "expected_reports" in sample:
            return self.validate_multiple_reports(extracted_reports, sample["expected_reports"])

        # For single report scenarios
        report = extracted_reports[0]  # Take first/primary report

        # Step 2: Validate extraction against expected values
        validation_passed = True

        if "category" in expected:
            if report.get("category") != expected["category"]:
                print(f"  📂 Category mismatch: got {report.get('category')}, expected {expected['category']}")
                validation_passed = False

        if "procedure" in expected:
            extracted_procedure = report.get("procedure", report.get("text", "")).lower()
            expected_procedure = expected["procedure"].lower()
            if expected_procedure not in extracted_procedure:
                print(f"  🔬 Procedure mismatch: got {extracted_procedure}, expected {expected_procedure}")
                validation_passed = False

        if "status" in expected:
            if report.get("status") != expected["status"]:
                print(f"  📊 Status mismatch: got {report.get('status')}, expected {expected['status']}")
                validation_passed = False

        if "interpretation" in expected:
            if report.get("interpretation") != expected["interpretation"]:
                print(f"  🎯 Interpretation mismatch: got {report.get('interpretation')}, expected {expected['interpretation']}")
                validation_passed = False

        # Step 3: Test FHIR resource creation
        try:
            fhir_resource = self.factory.create_diagnostic_report(
                report,
                "patient-test-001",
                f"test-{sample['id']}"
            )

            # Validate basic FHIR structure
            required_fields = ["resourceType", "id", "status", "category", "code", "subject"]
            for field in required_fields:
                if field not in fhir_resource:
                    print(f"  🏗️ Missing required FHIR field: {field}")
                    validation_passed = False

            # Check resource type
            if fhir_resource.get("resourceType") != "DiagnosticReport":
                print(f"  🏷️ Wrong resource type: {fhir_resource.get('resourceType')}")
                validation_passed = False

        except Exception as e:
            print(f"  ⚠️ FHIR creation failed: {str(e)}")
            validation_passed = False

        return validation_passed

    def validate_multiple_reports(self, extracted: List[Dict], expected: List[Dict]) -> bool:
        """Validate multiple reports from complex scenarios"""

        if len(extracted) < len(expected):
            print(f"  📊 Expected {len(expected)} reports, got {len(extracted)}")
            return False

        # Check if all expected categories are present
        extracted_categories = [r.get("category") for r in extracted]
        expected_categories = [r.get("category") for r in expected]

        for expected_cat in expected_categories:
            if expected_cat not in extracted_categories:
                print(f"  📂 Missing expected category: {expected_cat}")
                return False

        return True

    def print_summary(self, results: Dict[str, Any]):
        """Print test results summary"""

        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        total = results["total_tests"]
        passed = results["passed"]
        failed = results["failed"]
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass Rate: {pass_rate:.1f}%")

        print("\nResults by Category:")
        for category, cat_results in results["categories"].items():
            cat_pass_rate = (cat_results["passed"] / cat_results["total"] * 100) if cat_results["total"] > 0 else 0
            print(f"  {category}: {cat_results['passed']}/{cat_results['total']} ({cat_pass_rate:.1f}%)")

        print("\n" + "=" * 60)

        if pass_rate >= 80:
            print("🎉 IMPLEMENTATION READY FOR PRODUCTION!")
        elif pass_rate >= 60:
            print("⚠️  Implementation needs refinement")
        else:
            print("❌ Implementation needs significant work")

    def test_specific_samples(self, sample_ids: List[str]):
        """Test only specific sample IDs"""

        print(f"🧪 Testing Specific Samples: {', '.join(sample_ids)}")
        print("=" * 60)

        found_samples = []

        # Find samples by ID across all categories
        for category_name, samples in self.samples["test_scenarios"].items():
            for sample in samples:
                if sample["id"] in sample_ids:
                    found_samples.append((sample, category_name))

        if not found_samples:
            print("❌ No matching sample IDs found")
            return

        results = {"total": len(found_samples), "passed": 0, "failed": 0}

        for sample, category in found_samples:
            print(f"\n📋 Testing {sample['id']} ({category})")
            print("-" * 40)

            try:
                success = self.test_single_sample(sample, category)
                if success:
                    results["passed"] += 1
                    print(f"✅ {sample['id']}: PASSED")
                else:
                    results["failed"] += 1
                    print(f"❌ {sample['id']}: FAILED")

            except Exception as e:
                results["failed"] += 1
                print(f"💥 {sample['id']}: ERROR - {str(e)}")

        print(f"\nResults: {results['passed']}/{results['total']} passed")

    def demonstrate_workflow(self, sample_id: str):
        """Demonstrate complete workflow for a specific sample"""

        # Find the sample
        sample = None
        category = None

        for cat_name, samples in self.samples["test_scenarios"].items():
            for s in samples:
                if s["id"] == sample_id:
                    sample = s
                    category = cat_name
                    break

        if not sample:
            print(f"❌ Sample {sample_id} not found")
            return

        print(f"🔬 WORKFLOW DEMONSTRATION: {sample_id}")
        print("=" * 60)

        print(f"📝 Original Clinical Text:")
        print(f"   {sample['clinical_text'][:200]}{'...' if len(sample['clinical_text']) > 200 else ''}")

        print(f"\n🤖 Step 1: NLP Extraction")
        extracted_reports = self.extractor.extract_diagnostic_reports(sample['clinical_text'])

        if extracted_reports:
            report = extracted_reports[0]
            print(f"   ✅ Extracted {len(extracted_reports)} report(s)")
            print(f"   📂 Category: {report.get('category')}")
            print(f"   🔬 Procedure: {report.get('procedure', report.get('text', 'N/A'))}")
            print(f"   📊 Status: {report.get('status', 'final')}")
            print(f"   🎯 Interpretation: {report.get('interpretation', 'N/A')}")
            if "conclusion" in report:
                print(f"   💡 Conclusion: {report['conclusion'][:100]}{'...' if len(report.get('conclusion', '')) > 100 else ''}")
        else:
            print("   ❌ No reports extracted")
            return

        print(f"\n🏗️ Step 2: FHIR Resource Creation")
        try:
            fhir_resource = self.factory.create_diagnostic_report(
                report,
                "patient-demo-001",
                f"demo-{sample_id}",
                service_request_refs=["service-req-demo"] if category in ["laboratory_reports", "radiology_reports"] else None
            )

            print(f"   ✅ FHIR DiagnosticReport created")
            print(f"   🏷️ Resource Type: {fhir_resource['resourceType']}")
            print(f"   🆔 Resource ID: {fhir_resource['id']}")
            print(f"   📊 Status: {fhir_resource['status']}")
            print(f"   📂 Category: {fhir_resource['category'][0]['coding'][0]['display']}")
            print(f"   👤 Subject: {fhir_resource['subject']['reference']}")

            if "basedOn" in fhir_resource:
                print(f"   🔗 Linked to: {fhir_resource['basedOn'][0]['reference']}")

            if "conclusion" in fhir_resource:
                print(f"   💡 Conclusion: {fhir_resource['conclusion'][:100]}{'...' if len(fhir_resource['conclusion']) > 100 else ''}")

            print(f"\n📋 Complete FHIR Resource:")
            print(json.dumps(fhir_resource, indent=2)[:500] + "..." if len(json.dumps(fhir_resource)) > 500 else json.dumps(fhir_resource, indent=2))

        except Exception as e:
            print(f"   ❌ FHIR creation failed: {str(e)}")


def main():
    """Main function for command-line usage"""

    runner = DiagnosticReportTestRunner()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "all":
            runner.run_all_tests()
        elif command == "demo" and len(sys.argv) > 2:
            runner.demonstrate_workflow(sys.argv[2])
        elif command == "test" and len(sys.argv) > 2:
            sample_ids = sys.argv[2].split(',')
            runner.test_specific_samples(sample_ids)
        else:
            print("Usage:")
            print("  python run_diagnostic_report_tests.py all")
            print("  python run_diagnostic_report_tests.py demo <sample_id>")
            print("  python run_diagnostic_report_tests.py test <sample_id1,sample_id2,...>")
    else:
        print("🧪 DiagnosticReport Test Runner")
        print("Available commands:")
        print("  all     - Run all test scenarios")
        print("  demo    - Demonstrate workflow for specific sample")
        print("  test    - Test specific sample IDs")
        print("\nExample:")
        print("  python run_diagnostic_report_tests.py all")
        print("  python run_diagnostic_report_tests.py demo lab-001-cbc")
        print("  python run_diagnostic_report_tests.py test lab-001-cbc,rad-001-cxr-normal")


if __name__ == "__main__":
    main()