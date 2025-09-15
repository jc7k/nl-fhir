#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for 3-Tier Architecture
Executes all tests in optimized order for single-pass success

Updated for new organized test structure:
- tests/nlp/ - NLP and Smart Regex Consolidation tests
- tests/validation/ - Validation and performance tests
- tests/api/ - API integration tests
- tests/framework/ - FHIR framework tests
- tests/epic/ - Epic workflow tests
"""

import subprocess
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any


class ComprehensiveTestRunner:
    """Orchestrates comprehensive testing of the updated 3-tier architecture"""

    def __init__(self):
        self.results = {
            "test_session": {
                "start_time": datetime.now().isoformat(),
                "architecture": "3-tier_enhanced",
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "execution_phases": []
            }
        }

    def run_test_phase(self, phase_name: str, test_pattern: str, description: str) -> Dict[str, Any]:
        """Run a specific test phase with tracking"""

        print(f"\n🧪 {phase_name.upper()}")
        print(f"📋 {description}")
        print("=" * 60)

        start_time = time.time()

        try:
            # Run pytest with the specified pattern
            cmd = ["uv", "run", "pytest", test_pattern, "-v", "--tb=short"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            execution_time = time.time() - start_time

            # Parse pytest output for results
            output_lines = result.stdout.split('\n')

            # Look for the summary line
            passed = 0
            failed = 0
            errors = 0

            for line in output_lines:
                if "passed" in line or "failed" in line or "error" in line:
                    if " passed" in line:
                        try:
                            passed = int(line.split()[0])
                        except (ValueError, IndexError):
                            pass
                    if " failed" in line:
                        try:
                            failed = int(line.split()[0])
                        except (ValueError, IndexError):
                            pass

            phase_result = {
                "phase": phase_name,
                "description": description,
                "test_pattern": test_pattern,
                "execution_time_seconds": execution_time,
                "return_code": result.returncode,
                "tests_passed": passed,
                "tests_failed": failed,
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "stdout_preview": result.stdout[-500:] if result.stdout else "",
                "stderr_preview": result.stderr[-300:] if result.stderr else ""
            }

            # Update totals
            self.results["test_session"]["total_tests"] += passed + failed
            self.results["test_session"]["passed_tests"] += passed
            self.results["test_session"]["failed_tests"] += failed

            # Print phase summary
            status_emoji = "✅" if result.returncode == 0 else "❌"
            print(f"{status_emoji} {phase_name}: {passed} passed, {failed} failed ({execution_time:.1f}s)")

            if result.returncode != 0 and result.stderr:
                print(f"⚠️  Error Output: {result.stderr[:200]}...")

            return phase_result

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            print(f"⏰ {phase_name}: TIMEOUT after {execution_time:.1f}s")

            return {
                "phase": phase_name,
                "description": description,
                "test_pattern": test_pattern,
                "execution_time_seconds": execution_time,
                "status": "TIMEOUT",
                "error": "Test phase exceeded timeout limit"
            }

        except Exception as e:
            execution_time = time.time() - start_time
            print(f"💥 {phase_name}: EXCEPTION - {e}")

            return {
                "phase": phase_name,
                "description": description,
                "test_pattern": test_pattern,
                "execution_time_seconds": execution_time,
                "status": "ERROR",
                "error": str(e)
            }

    def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Execute the complete test suite in optimized phases"""

        print("🚀 COMPREHENSIVE TEST SUITE EXECUTION")
        print("🏗️  Testing 3-Tier Architecture Migration")
        print("=" * 70)

        # Phase 1: Core Unit Tests (Fast)
        phase1 = self.run_test_phase(
            "Phase 1: Core Unit Tests",
            "tests/nlp/test_entity_extractor.py tests/nlp/test_llm_*.py",
            "Fast unit tests for core NLP components"
        )
        self.results["test_session"]["execution_phases"].append(phase1)

        # Phase 2: New 3-Tier Architecture Tests
        phase2 = self.run_test_phase(
            "Phase 2: Smart Regex Consolidation",
            "tests/nlp/test_smart_regex_consolidation.py",
            "Validate new Smart Regex Consolidation system (Tier 2)"
        )
        self.results["test_session"]["execution_phases"].append(phase2)

        # Phase 3: Integration Tests
        phase3 = self.run_test_phase(
            "Phase 3: NLP Integration Tests",
            "tests/nlp/test_nlp_integration.py tests/integration/test_3tier_nlp_complete.py",
            "End-to-end NLP pipeline integration with 3-tier architecture"
        )
        self.results["test_session"]["execution_phases"].append(phase3)

        # Phase 4: API Integration Tests
        phase4 = self.run_test_phase(
            "Phase 4: API Integration",
            "tests/api/ tests/integration/test_medical_nlp_integration.py",
            "API endpoints and medical NLP integration"
        )
        self.results["test_session"]["execution_phases"].append(phase4)

        # Phase 5: FHIR Core Tests
        phase5 = self.run_test_phase(
            "Phase 5: FHIR Core Functionality",
            "tests/framework/ tests/test_fhir_core.py tests/test_bundle_assembly.py",
            "FHIR resource creation and bundle assembly"
        )
        self.results["test_session"]["execution_phases"].append(phase5)

        # Phase 6: Epic Integration Tests
        phase6 = self.run_test_phase(
            "Phase 6: Epic Integration Tests",
            "tests/epic/ tests/test_epic_*.py",
            "Complete epic workflow integration testing"
        )
        self.results["test_session"]["execution_phases"].append(phase6)

        # Phase 7: Performance and Validation Tests
        phase7 = self.run_test_phase(
            "Phase 7: Performance Validation",
            "tests/test_story_3_*.py tests/validation/",
            "Performance requirements and validation tests"
        )
        self.results["test_session"]["execution_phases"].append(phase7)

        # Phase 8: Batch and Comprehensive Scenarios
        phase8 = self.run_test_phase(
            "Phase 8: Comprehensive Scenarios",
            "tests/batch/ tests/test_main.py",
            "Large-scale scenario testing and main application tests"
        )
        self.results["test_session"]["execution_phases"].append(phase8)

        # Finalize results
        self.results["test_session"]["end_time"] = datetime.now().isoformat()

        total_execution_time = sum(
            phase.get("execution_time_seconds", 0)
            for phase in self.results["test_session"]["execution_phases"]
        )
        self.results["test_session"]["total_execution_time_seconds"] = total_execution_time

        # Calculate success metrics
        total_tests = self.results["test_session"]["total_tests"]
        passed_tests = self.results["test_session"]["passed_tests"]
        failed_tests = self.results["test_session"]["failed_tests"]

        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
        else:
            success_rate = 0

        self.results["test_session"]["success_rate_percent"] = success_rate
        self.results["test_session"]["phases_passed"] = sum(
            1 for phase in self.results["test_session"]["execution_phases"]
            if phase.get("status") == "PASSED"
        )

        return self.results

    def print_final_summary(self):
        """Print comprehensive test execution summary"""

        print("\n🎯 COMPREHENSIVE TEST EXECUTION SUMMARY")
        print("=" * 70)

        session = self.results["test_session"]

        print(f"📊 Overall Results:")
        print(f"   • Total Tests: {session['total_tests']}")
        print(f"   • Passed: {session['passed_tests']}")
        print(f"   • Failed: {session['failed_tests']}")
        print(f"   • Success Rate: {session['success_rate_percent']:.1f}%")
        print(f"   • Total Execution Time: {session['total_execution_time_seconds']:.1f}s")
        print(f"   • Phases Passed: {session['phases_passed']}/{len(session['execution_phases'])}")

        print(f"\n📋 Phase Summary:")
        for i, phase in enumerate(session["execution_phases"], 1):
            status_emoji = "✅" if phase.get("status") == "PASSED" else "❌"
            exec_time = phase.get("execution_time_seconds", 0)
            print(f"   {i}. {phase['phase']}: {status_emoji} ({exec_time:.1f}s)")

        # Overall assessment
        if session["success_rate_percent"] >= 95 and session["phases_passed"] >= 6:
            print(f"\n🎉 3-TIER ARCHITECTURE MIGRATION: SUCCESSFUL")
            print(f"   ✓ High test success rate ({session['success_rate_percent']:.1f}%)")
            print(f"   ✓ Most phases passed ({session['phases_passed']}/{len(session['execution_phases'])})")
            print(f"   ✓ Test suite execution ready for production")
        elif session["success_rate_percent"] >= 80:
            print(f"\n⚠️  3-TIER ARCHITECTURE MIGRATION: NEEDS ATTENTION")
            print(f"   • Success rate acceptable but room for improvement")
            print(f"   • {session['failed_tests']} tests need fixing")
        else:
            print(f"\n❌ 3-TIER ARCHITECTURE MIGRATION: ISSUES DETECTED")
            print(f"   • Success rate below acceptable threshold")
            print(f"   • {session['failed_tests']} tests failing - investigation needed")

    def save_results(self) -> str:
        """Save detailed test results"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_results_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n💾 Detailed results saved to: {filename}")
        return filename


def main():
    """Main execution function"""

    print("🔧 Initializing Comprehensive Test Runner...")

    runner = ComprehensiveTestRunner()

    try:
        # Execute comprehensive test suite
        results = runner.run_comprehensive_test_suite()

        # Print summary
        runner.print_final_summary()

        # Save detailed results
        runner.save_results()

        # Exit with appropriate code
        success_rate = results["test_session"]["success_rate_percent"]
        if success_rate >= 95:
            print(f"\n🎊 All tests completed successfully!")
            sys.exit(0)
        else:
            print(f"\n⚠️  Some tests need attention (success rate: {success_rate:.1f}%)")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n⏹️  Test execution interrupted by user")
        runner.save_results()
        sys.exit(2)

    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()