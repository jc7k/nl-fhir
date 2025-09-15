#!/usr/bin/env python3
"""
Test to verify organized test structure works correctly
"""

import subprocess
import sys


def test_nlp_tests_discoverable():
    """Verify NLP tests can be discovered and run"""
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/nlp/", "--collect-only", "-q"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"NLP test discovery failed: {result.stderr}"
    assert "tests/nlp/" in result.stdout, "NLP tests not discovered"


def test_validation_tests_discoverable():
    """Verify validation tests can be discovered and run"""
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/validation/", "--collect-only", "-q"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Validation test discovery failed: {result.stderr}"
    assert "tests/validation/" in result.stdout, "Validation tests not discovered"


def test_core_tests_runnable():
    """Verify core FHIR tests run successfully"""
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/test_fhir_core.py", "-v"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Core FHIR tests failed: {result.stderr}"
    assert "PASSED" in result.stdout, "No passing tests found"


def test_main_tests_runnable():
    """Verify main application tests run successfully"""
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/test_main.py", "-v"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Main tests failed: {result.stderr}"
    assert "PASSED" in result.stdout, "No passing tests found"


if __name__ == "__main__":
    print("🧪 Testing Organized Test Structure...")

    try:
        test_nlp_tests_discoverable()
        print("✅ NLP tests discoverable")

        test_validation_tests_discoverable()
        print("✅ Validation tests discoverable")

        test_core_tests_runnable()
        print("✅ Core FHIR tests runnable")

        test_main_tests_runnable()
        print("✅ Main application tests runnable")

        print("🎉 All organized test structure checks PASSED!")
        sys.exit(0)

    except AssertionError as e:
        print(f"❌ Test structure check failed: {e}")
        sys.exit(1)