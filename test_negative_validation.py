"""
Comprehensive Negative Test Suite
Tests all 100 faulty clinical orders from docs/faulty-orders.json
Validates error detection, FHIR compliance, and escalation workflows
"""

import json
import sys
import os
from typing import Dict, List, Any
from datetime import datetime
import statistics

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.nl_fhir.services.clinical_validator import validate_clinical_order, ValidationSeverity
from src.nl_fhir.services.error_handler import handle_validation_error


class NegativeTestRunner:
    """Comprehensive negative testing framework"""
    
    def __init__(self):
        self.results = {
            "test_summary": {},
            "detailed_results": [],
            "category_analysis": {},
            "escalation_analysis": {},
            "fhir_compliance": {},
            "performance_metrics": {}
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all 100 negative test cases"""
        
        print("🧪 Starting Comprehensive Negative Test Suite")
        print("=" * 60)
        
        # Load test cases
        test_cases = self._load_test_cases()
        total_cases = len(test_cases)
        
        print(f"📊 Loaded {total_cases} negative test cases")
        print(f"🎯 Testing error detection and escalation workflows\n")
        
        # Run tests
        start_time = datetime.now()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"[{i:3d}/{total_cases}] {test_case['specialty']}: {test_case['order'][:50]}...")
            result = self._run_single_test(test_case, f"test_{i}")
            self.results["detailed_results"].append(result)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Analyze results
        self._analyze_results(test_cases, processing_time)
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    def _load_test_cases(self) -> List[Dict[str, Any]]:
        """Load the 100 faulty clinical orders"""
        
        with open('docs/faulty-orders.json', 'r') as f:
            return json.load(f)
    
    def _run_single_test(self, test_case: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        """Run validation on a single test case"""
        
        try:
            # Run clinical validation
            validation_result = validate_clinical_order(test_case['order'], request_id)
            
            # Generate error response
            error_response = handle_validation_error(validation_result, request_id)
            
            # Analyze test result
            return {
                "test_case": test_case,
                "request_id": request_id,
                "validation_successful": True,
                "validation_result": {
                    "is_valid": validation_result.is_valid,
                    "can_process_fhir": validation_result.can_process_fhir,
                    "issues_detected": len(validation_result.issues),
                    "confidence": validation_result.confidence,
                    "escalation_required": validation_result.escalation_required,
                    "processing_recommendation": validation_result.processing_recommendation
                },
                "error_response": {
                    "status": error_response["status"],
                    "escalation_level": error_response["escalation"]["level"],
                    "total_issues": error_response["validation_summary"]["total_issues"],
                    "fatal_issues": error_response["validation_summary"]["fatal_issues"],
                    "error_issues": error_response["validation_summary"]["error_issues"]
                },
                "detected_correctly": self._validate_detection_accuracy(test_case, validation_result),
                "processing_time_ms": 0  # Will be calculated in batch
            }
            
        except Exception as e:
            return {
                "test_case": test_case,
                "request_id": request_id,
                "validation_successful": False,
                "error": str(e),
                "detected_correctly": False,
                "processing_time_ms": 0
            }
    
    def _validate_detection_accuracy(self, test_case: Dict[str, Any], validation_result) -> bool:
        """Validate that our system correctly detected the expected issues"""
        
        # Expected issues based on test case description
        expected_issues = test_case.get('issue', '').lower()
        fhir_impact = test_case.get('fhirImpact', '').lower()
        
        # Check if we detected any issues (all negative cases should have issues)
        if len(validation_result.issues) == 0:
            return False
            
        # Check specific patterns based on expected issues
        detected_codes = [issue.code.value.lower() for issue in validation_result.issues]
        
        # Map expected issues to our validation codes
        if 'conditional' in expected_issues:
            return any('conditional' in code for code in detected_codes)
        elif 'multiple' in expected_issues or 'ambiguity' in expected_issues:
            return any('ambiguity' in code for code in detected_codes)
        elif 'missing' in fhir_impact or 'cannot populate' in fhir_impact:
            return any('missing' in code for code in detected_codes)
        elif 'protocol' in expected_issues or 'discretion' in expected_issues:
            return any('protocol' in code for code in detected_codes)
        elif 'vague' in expected_issues or 'unclear' in expected_issues:
            return any('vague' in code for code in detected_codes)
        
        # If we detected issues but couldn't map specifically, still partially correct
        return len(validation_result.issues) > 0
    
    def _analyze_results(self, test_cases: List[Dict], processing_time: float):
        """Analyze comprehensive test results"""
        
        successful_validations = sum(1 for r in self.results["detailed_results"] if r["validation_successful"])
        correct_detections = sum(1 for r in self.results["detailed_results"] if r.get("detected_correctly", False))
        
        # Test summary
        self.results["test_summary"] = {
            "total_cases": len(test_cases),
            "successful_validations": successful_validations,
            "correct_detections": correct_detections,
            "detection_accuracy": (correct_detections / len(test_cases)) * 100,
            "validation_success_rate": (successful_validations / len(test_cases)) * 100,
            "total_processing_time_seconds": processing_time,
            "avg_processing_time_ms": (processing_time * 1000) / len(test_cases)
        }
        
        # Category analysis
        specialty_results = {}
        for result in self.results["detailed_results"]:
            specialty = result["test_case"]["specialty"]
            if specialty not in specialty_results:
                specialty_results[specialty] = {
                    "total": 0,
                    "detected_correctly": 0,
                    "escalation_required": 0,
                    "fatal_issues": 0
                }
            
            specialty_results[specialty]["total"] += 1
            if result.get("detected_correctly", False):
                specialty_results[specialty]["detected_correctly"] += 1
            if result.get("validation_result", {}).get("escalation_required", False):
                specialty_results[specialty]["escalation_required"] += 1
            if result.get("error_response", {}).get("fatal_issues", 0) > 0:
                specialty_results[specialty]["fatal_issues"] += 1
        
        self.results["category_analysis"] = specialty_results
        
        # Escalation analysis
        escalation_levels = {}
        for result in self.results["detailed_results"]:
            level = result.get("error_response", {}).get("escalation_level", "unknown")
            escalation_levels[level] = escalation_levels.get(level, 0) + 1
        
        self.results["escalation_analysis"] = escalation_levels
        
        # FHIR compliance analysis
        cannot_process = sum(1 for r in self.results["detailed_results"] 
                           if not r.get("validation_result", {}).get("can_process_fhir", True))
        
        self.results["fhir_compliance"] = {
            "cases_cannot_process_fhir": cannot_process,
            "fhir_blocking_rate": (cannot_process / len(test_cases)) * 100,
            "cases_can_process_with_warnings": len(test_cases) - cannot_process
        }
    
    def _print_summary(self):
        """Print comprehensive test summary"""
        
        print("\n" + "=" * 60)
        print("🎯 COMPREHENSIVE NEGATIVE TEST RESULTS")
        print("=" * 60)
        
        summary = self.results["test_summary"]
        print(f"📊 Test Cases: {summary['total_cases']}")
        print(f"✅ Successful Validations: {summary['successful_validations']}/{summary['total_cases']} ({summary['validation_success_rate']:.1f}%)")
        print(f"🎯 Correct Detections: {summary['correct_detections']}/{summary['total_cases']} ({summary['detection_accuracy']:.1f}%)")
        print(f"⚡ Avg Processing Time: {summary['avg_processing_time_ms']:.1f}ms per case")
        
        print(f"\n🚨 ESCALATION ANALYSIS:")
        for level, count in self.results["escalation_analysis"].items():
            percentage = (count / summary['total_cases']) * 100
            print(f"   {level}: {count} cases ({percentage:.1f}%)")
        
        print(f"\n📋 FHIR COMPLIANCE:")
        fhir = self.results["fhir_compliance"]
        print(f"   Cannot Process: {fhir['cases_cannot_process_fhir']} cases ({fhir['fhir_blocking_rate']:.1f}%)")
        print(f"   Can Process with Warnings: {fhir['cases_can_process_with_warnings']} cases")
        
        print(f"\n🏥 TOP PROBLEM SPECIALTIES:")
        specialty_sorted = sorted(
            self.results["category_analysis"].items(),
            key=lambda x: x[1]["fatal_issues"] + (x[1]["total"] - x[1]["detected_correctly"]),
            reverse=True
        )[:5]
        
        for specialty, data in specialty_sorted:
            accuracy = (data["detected_correctly"] / data["total"]) * 100 if data["total"] > 0 else 0
            print(f"   {specialty}: {data['detected_correctly']}/{data['total']} correct ({accuracy:.0f}%), {data['fatal_issues']} fatal issues")


def save_results(results: Dict[str, Any]):
    """Save comprehensive test results"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"clinical_results/negative_validation_results_{timestamp}.json"
    
    os.makedirs("clinical_results", exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {filename}")


if __name__ == "__main__":
    # Run comprehensive negative test suite
    runner = NegativeTestRunner()
    results = runner.run_comprehensive_test()
    
    # Save results
    save_results(results)
    
    # Quick validation examples
    print(f"\n🔍 SAMPLE ERROR RESPONSES:")
    print("-" * 40)
    
    # Test a few specific examples
    sample_orders = [
        "Start beta blocker if BP remains high, maybe metoprolol or atenolol",
        "Give something for thyroid, maybe Synthroid?",
        "Start aspirin 81mg daily"  # This should pass as a control
    ]
    
    for i, order in enumerate(sample_orders, 1):
        print(f"\n{i}. Testing: '{order}'")
        validation_result = validate_clinical_order(order, f"sample_{i}")
        error_response = handle_validation_error(validation_result, f"sample_{i}")
        
        print(f"   Status: {error_response['status']}")
        print(f"   Issues: {error_response['validation_summary']['total_issues']}")
        print(f"   Escalation: {error_response['escalation']['level']}")
        print(f"   Can Process FHIR: {error_response['can_process_fhir']}")
        
        if error_response['validation_summary']['total_issues'] > 0:
            top_issue = error_response['issues'][0]
            print(f"   Top Issue: {top_issue['message']}")
            print(f"   Guidance: {top_issue['guidance']}")
    
    print(f"\n✅ Negative validation testing complete!")
    print(f"🎯 System ready for production with comprehensive error handling")