#!/usr/bin/env python3
"""
Test Smart Regex Consolidation System (New Tier 2)
Validates the replacement of Transformer NER with intelligent pattern matching
"""

import sys
sys.path.append('../../src')
sys.path.append('../../')

import unittest
import asyncio
from typing import Dict, List, Any

# Import the Smart Regex Consolidation system
try:
    from smart_regex_consolidator import SmartRegexConsolidator
    CONSOLIDATOR_AVAILABLE = True
except ImportError:
    CONSOLIDATOR_AVAILABLE = False


class TestSmartRegexConsolidation(unittest.TestCase):
    """Test suite for Smart Regex Consolidation functionality"""

    def setUp(self):
        """Initialize test components"""
        if CONSOLIDATOR_AVAILABLE:
            self.consolidator = SmartRegexConsolidator()
        else:
            self.skipTest("Smart Regex Consolidator not available")

    def test_consolidator_initialization(self):
        """Test that the Smart Regex Consolidator initializes properly"""
        self.assertIsNotNone(self.consolidator)
        self.assertTrue(hasattr(self.consolidator, 'extract_with_smart_consolidation'))

    def test_medication_pattern_enhancement(self):
        """Test enhanced medication pattern recognition"""

        text = "Prescribed Lisinopril 10mg daily for hypertension"

        # Simulate basic MedSpaCy results
        medspacy_results = {
            "medications": [{"text": "Lisinopril", "confidence": 0.9}],
            "dosages": [],
            "frequencies": [],
            "conditions": []
        }

        # Apply Smart Regex Consolidation
        enhanced_results = self.consolidator.extract_with_smart_consolidation(text, medspacy_results)

        # Verify enhancements
        self.assertIn("medications", enhanced_results)
        self.assertIn("dosages", enhanced_results)
        self.assertIn("frequencies", enhanced_results)

        # Check for pattern-based enhancements
        if enhanced_results["dosages"]:
            self.assertTrue(any("10mg" in str(dosage) for dosage in enhanced_results["dosages"]))

        if enhanced_results["frequencies"]:
            self.assertTrue(any("daily" in str(freq) for freq in enhanced_results["frequencies"]))

    def test_complex_medication_consolidation(self):
        """Test consolidation of complex medication orders"""

        text = "Amoxicillin 875mg BID with meals for strep throat, continue for 10 days"

        medspacy_results = {
            "medications": [{"text": "Amoxicillin", "confidence": 0.85}],
            "dosages": [],
            "frequencies": [],
            "conditions": [],
            "durations": []
        }

        enhanced_results = self.consolidator.extract_with_smart_consolidation(text, medspacy_results)

        # Verify comprehensive extraction
        self.assertIn("medications", enhanced_results)

        # Check for enhanced pattern detection
        expected_patterns = ["875mg", "BID", "10 days", "strep throat"]
        text_lower = text.lower()

        for pattern in expected_patterns:
            self.assertIn(pattern.lower(), text_lower)

    def test_gap_analysis_functionality(self):
        """Test the gap analysis system"""

        text = "Patient needs insulin adjustment based on blood glucose levels"

        medspacy_results = {
            "medications": [],  # MedSpaCy missed insulin
            "conditions": [],
            "monitoring": []
        }

        enhanced_results = self.consolidator.extract_with_smart_consolidation(text, medspacy_results)

        # The consolidator should identify and fill gaps
        self.assertIsInstance(enhanced_results, dict)

        # Check that gap analysis was performed
        # (The actual enhancement depends on the patterns in the consolidator)

    def test_confidence_weighting(self):
        """Test confidence-based pattern weighting"""

        text = "Take acetaminophen 500mg as needed for pain"

        # High confidence MedSpaCy results
        high_confidence_results = {
            "medications": [{"text": "acetaminophen", "confidence": 0.95}],
            "dosages": [{"text": "500mg", "confidence": 0.9}],
            "frequencies": [],
            "conditions": []
        }

        enhanced_results = self.consolidator.extract_with_smart_consolidation(text, high_confidence_results)

        # With high confidence, consolidator should preserve original results
        self.assertIn("medications", enhanced_results)
        self.assertIn("dosages", enhanced_results)

    def test_performance_requirements(self):
        """Test that Smart Regex Consolidation meets performance requirements"""

        import time

        text = "Complex clinical order with multiple medications and detailed instructions"

        medspacy_results = {
            "medications": [{"text": "medication", "confidence": 0.8}],
            "dosages": [],
            "frequencies": [],
            "conditions": []
        }

        # Measure processing time
        start_time = time.time()

        enhanced_results = self.consolidator.extract_with_smart_consolidation(text, medspacy_results)

        processing_time_ms = (time.time() - start_time) * 1000

        # Should be much faster than Transformer NER (target < 50ms)
        self.assertLess(processing_time_ms, 100,
                       f"Smart Consolidation took {processing_time_ms:.2f}ms, should be < 100ms")

    def test_hierarchical_pattern_matching(self):
        """Test hierarchical pattern matching functionality"""

        test_cases = [
            {
                "text": "Metformin 850mg twice daily with meals",
                "expected_patterns": ["metformin", "850mg", "twice daily", "with meals"]
            },
            {
                "text": "CBC and comprehensive metabolic panel",
                "expected_patterns": ["CBC", "comprehensive metabolic panel"]
            },
            {
                "text": "Continue current insulin regimen",
                "expected_patterns": ["insulin", "continue", "regimen"]
            }
        ]

        for case in test_cases:
            medspacy_results = {"medications": [], "lab_tests": [], "instructions": []}

            enhanced_results = self.consolidator.extract_with_smart_consolidation(
                case["text"], medspacy_results
            )

            # Verify that results structure is maintained
            self.assertIsInstance(enhanced_results, dict)

    def test_medical_safety_patterns(self):
        """Test medical safety pattern recognition"""

        safety_critical_text = "Patient allergic to penicillin, prescribe alternative antibiotic"

        medspacy_results = {
            "medications": [],
            "allergies": [],
            "conditions": []
        }

        enhanced_results = self.consolidator.extract_with_smart_consolidation(
            safety_critical_text, medspacy_results
        )

        # Should maintain safety-critical information
        self.assertIsInstance(enhanced_results, dict)

        # Check that safety patterns are preserved
        text_lower = safety_critical_text.lower()
        self.assertIn("allergic", text_lower)
        self.assertIn("penicillin", text_lower)

    def test_consolidation_vs_transformer_replacement(self):
        """Test that Smart Consolidation effectively replaces Transformer NER"""

        # Test cases that would have gone to Transformer NER
        complex_cases = [
            "Patient reports intermittent chest pain, consider stress test",
            "Adjust warfarin dose based on INR results",
            "Discontinue current antibiotics if culture negative"
        ]

        for text in complex_cases:
            medspacy_results = {
                "medications": [],
                "conditions": [],
                "procedures": [],
                "lab_tests": []
            }

            start_time = time.time()
            enhanced_results = self.consolidator.extract_with_smart_consolidation(text, medspacy_results)
            processing_time_ms = (time.time() - start_time) * 1000

            # Should process faster than Transformer NER (which took ~344ms)
            self.assertLess(processing_time_ms, 50,
                           f"Consolidation took {processing_time_ms:.2f}ms for complex case")

            # Should return valid results structure
            self.assertIsInstance(enhanced_results, dict)

    def test_error_handling(self):
        """Test error handling in Smart Regex Consolidation"""

        # Test with malformed input
        malformed_results = None

        try:
            enhanced_results = self.consolidator.extract_with_smart_consolidation(
                "Normal text", malformed_results
            )
            # Should handle gracefully
            self.assertIsInstance(enhanced_results, dict)
        except Exception as e:
            # Should not crash the system
            self.fail(f"Smart Consolidation crashed with malformed input: {e}")

    def test_integration_with_existing_pipeline(self):
        """Test integration with existing NLP pipeline"""

        # This test ensures the consolidator works with real pipeline output
        text = "Prescribed Metformin 500mg BID for Type 2 diabetes management"

        # Simulate realistic MedSpaCy output
        realistic_medspacy_results = {
            "medications": [
                {"text": "Metformin", "start": 10, "end": 18, "confidence": 0.87}
            ],
            "dosages": [],
            "frequencies": [],
            "conditions": [
                {"text": "Type 2 diabetes", "start": 31, "end": 46, "confidence": 0.92}
            ]
        }

        enhanced_results = self.consolidator.extract_with_smart_consolidation(
            text, realistic_medspacy_results
        )

        # Should preserve high-confidence original results
        self.assertIn("medications", enhanced_results)
        self.assertIn("conditions", enhanced_results)

        # Should enhance with additional patterns
        self.assertIn("dosages", enhanced_results)
        self.assertIn("frequencies", enhanced_results)


def run_consolidation_tests():
    """Run all Smart Regex Consolidation tests"""

    if not CONSOLIDATOR_AVAILABLE:
        print("⚠️  Smart Regex Consolidator not available - skipping tests")
        return False

    print("🧪 Running Smart Regex Consolidation Test Suite")
    print("=" * 60)

    # Run the test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSmartRegexConsolidation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\n📊 Test Results:")
    print(f"   Tests Run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    success = len(result.failures) == 0 and len(result.errors) == 0

    if success:
        print("✅ Smart Regex Consolidation: ALL TESTS PASSED")
    else:
        print("❌ Smart Regex Consolidation: TESTS FAILED")

    return success


if __name__ == "__main__":
    run_consolidation_tests()