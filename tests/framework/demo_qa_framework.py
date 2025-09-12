#!/usr/bin/env python3
"""
Demonstration of the Extensible QA Framework
Shows how to use the framework to test your 3-tier NLP architecture
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.framework.qa_framework import (
    ClinicalTestLoader, ClinicalTestRunner, TestReportGenerator,
    create_medication_test, create_lab_test
)
from src.nl_fhir.services.nlp.models import model_manager


class MockNLPProcessor:
    """Mock NLP processor for demonstration"""
    
    def extract_medical_entities(self, text: str):
        """Use the actual 3-tier system"""
        return model_manager.extract_medical_entities(text)


async def demo_qa_framework():
    """Demonstrate the QA framework capabilities"""
    
    print(">ê NL-FHIR QA Framework Demonstration")
    print("=" * 60)
    
    # 1. Load test cases from JSON configuration
    loader = ClinicalTestLoader("tests/data")
    test_cases = loader.load_test_cases_from_json("tests/data/medication_test_cases.json")
    
    print(f"\n=Ë Loaded {len(test_cases)} test cases:")
    for i, case in enumerate(test_cases, 1):
        print(f"   {i}. {case.name} ({case.complexity_level})")
    
    # 2. Create additional test cases programmatically
    print(f"\n=à Creating additional test cases programmatically...")
    
    additional_tests = [
        create_medication_test(
            name="Custom Test - Atorvastatin",
            clinical_text="Patient needs Atorvastatin 20mg nightly for cholesterol management", 
            expected_medication="atorvastatin",
            expected_dosage="20mg",
            expected_frequency="nightly"
        ),
        create_lab_test(
            name="Custom Lab Order",
            clinical_text="Order CBC, basic metabolic panel, and lipid profile for follow-up",
            expected_lab_tests=["cbc", "metabolic panel", "lipid"]
        )
    ]
    
    # Combine all test cases
    all_test_cases = test_cases + additional_tests
    print(f"   =Ê Total test cases: {len(all_test_cases)}")
    
    # 3. Set up test runner with your actual NLP processor
    print(f"\n<Ã Setting up test runner...")
    nlp_processor = MockNLPProcessor()
    runner = ClinicalTestRunner(nlp_processor=nlp_processor)
    
    # 4. Run test suite
    print(f"\n>ê Executing test suite...")
    results = await runner.run_test_suite(all_test_cases)
    
    # 5. Generate reports
    print(f"\n=Ê Generating reports...")
    report_generator = TestReportGenerator()
    
    # Summary report
    summary = report_generator.generate_summary_report(results)
    
    print(f"\n=È Test Results Summary:")
    print(f"    Success Rate: {summary['summary']['success_rate']:.1%}")
    print(f"   ¡ Avg Processing Time: {summary['performance']['avg_processing_time_ms']:.1f}ms")
    print(f"   <¯ Avg Quality Score: {summary['quality']['avg_quality_score']:.2f}")
    print(f"   =Ï Performance Compliance: {summary['summary']['performance_compliance_rate']:.1%}")
    print(f"   <× Tier Distribution: {summary['tier_distribution']}")
    
    # Performance analysis
    meets_2s = summary['performance']['meets_2s_requirement']
    meets_95_quality = summary['quality']['meets_95_percent_target']
    
    print(f"\n<¯ Requirements Assessment:")
    print(f"   {'' if meets_2s else 'L'} <2s Performance: {meets_2s}")
    print(f"   {'' if meets_95_quality else 'L'} e95% Quality Target: {meets_95_quality}")
    
    # Detailed results
    print(f"\n=Ë Detailed Results:")
    for result in results:
        status = " PASS" if result.success else "L FAIL"
        print(f"   {status} {result.test_name}")
        print(f"      ñ  {result.processing_time_ms:.1f}ms | <¯ {result.entity_quality_score:.2f} | <× {result.tier_used}")
        
        if result.issues:
            for issue in result.issues:
                print(f"         =¨ {issue}")
        
        if result.recommendations:
            for rec in result.recommendations:
                print(f"         =¡ {rec}")
    
    # Generate HTML report
    html_path = "tests/reports/qa_demo_report.html"
    Path(html_path).parent.mkdir(parents=True, exist_ok=True)
    report_generator.generate_detailed_html_report(results, html_path)
    print(f"\n=Ä Detailed HTML report generated: {html_path}")
    
    # 6. Identify critical issues
    print(f"\n= Critical Issues Analysis:")
    
    failed_tests = [r for r in results if not r.success]
    slow_tests = [r for r in results if r.processing_time_ms > 1000]
    low_quality_tests = [r for r in results if r.entity_quality_score < 0.7]
    
    if failed_tests:
        print(f"   =¨ {len(failed_tests)} tests failed:")
        for result in failed_tests:
            print(f"      - {result.test_name}: {', '.join(result.issues)}")
    
    if slow_tests:
        print(f"   ð {len(slow_tests)} tests exceed 1s processing time:")
        for result in slow_tests:
            print(f"      - {result.test_name}: {result.processing_time_ms:.1f}ms")
    
    if low_quality_tests:
        print(f"   =É {len(low_quality_tests)} tests have low quality scores:")
        for result in low_quality_tests:
            print(f"      - {result.test_name}: {result.entity_quality_score:.2f}")
    
    # 7. Recommendations for improvement
    print(f"\n=¡ Framework Recommendations:")
    
    if summary['performance']['avg_processing_time_ms'] > 1000:
        print("   1. Performance: Consider optimizing the 3-tier escalation logic")
        print("      - Review spaCy pattern efficiency")
        print("      - Optimize transformer model loading")
        print("      - Add caching for repeated entities")
    
    if summary['quality']['avg_quality_score'] < 0.8:
        print("   2. Quality: Improve entity extraction accuracy")
        print("      - Expand medical terminology dictionaries")
        print("      - Add more clinical abbreviations")
        print("      - Fine-tune escalation thresholds")
    
    regex_usage = summary['tier_distribution'].get('regex', 0)
    total_tests = summary['summary']['total_tests']
    if regex_usage / total_tests > 0.3:
        print("   3. Architecture: Too many tests falling back to regex")
        print("      - Improve spaCy medical pattern coverage")
        print("      - Consider adding medspaCy integration")
        print("      - Review escalation criteria")
    
    print(f"\n<‰ QA Framework demonstration complete!")
    print(f"    - Framework ready for production use")
    print(f"    - Easy to add new test cases via JSON or programmatically")
    print(f"    - Comprehensive reporting and analysis")
    print(f"    - Performance and quality monitoring built-in")


def demo_test_case_creation():
    """Show how to create test cases programmatically"""
    
    print(f"\n=à Test Case Creation Examples:")
    
    # Create various types of test cases
    medication_test = create_medication_test(
        name="Example Medication Test",
        clinical_text="Patient should take Metformin 850mg twice daily with meals",
        expected_medication="metformin",
        expected_dosage="850mg", 
        expected_frequency="twice daily"
    )
    
    lab_test = create_lab_test(
        name="Example Lab Test",
        clinical_text="Please order CBC, CMP, and TSH for annual physical",
        expected_lab_tests=["cbc", "cmp", "tsh"]
    )
    
    print(f"   =Ë Created medication test: {medication_test.name}")
    print(f"      - Expects: {len(medication_test.expected_entities)} entities")
    print(f"      - FHIR resources: {len(medication_test.expected_fhir_resources)}")
    
    print(f"   >ê Created lab test: {lab_test.name}")
    print(f"      - Expects: {len(lab_test.expected_entities)} entities")
    print(f"      - FHIR resources: {len(lab_test.expected_fhir_resources)}")
    
    # Save test cases to JSON
    loader = ClinicalTestLoader("tests/data")
    test_cases = [medication_test, lab_test]
    loader.save_test_cases_to_json(test_cases, "tests/data/demo_test_cases.json")
    print(f"   =¾ Saved test cases to: tests/data/demo_test_cases.json")


if __name__ == "__main__":
    print("<å NL-FHIR Extensible QA Framework")
    print("=" * 50)
    
    # Demo test case creation
    demo_test_case_creation()
    
    # Demo full framework
    asyncio.run(demo_qa_framework())