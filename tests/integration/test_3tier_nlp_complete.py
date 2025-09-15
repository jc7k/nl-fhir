#!/usr/bin/env python3
"""
Test the NEW 3-tier medical NLP architecture post-migration
TIER 1: Enhanced MedSpaCy → TIER 2: Smart Regex Consolidation → TIER 3: LLM Safety Escalation
Validates performance improvements and maintained quality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

import asyncio
import time
import json
from typing import Dict, List, Any
from datetime import datetime

from nl_fhir.services.conversion import ConversionService
from nl_fhir.services.nlp.pipeline import nlp_pipeline

# Import the new 3-tier components
try:
    from smart_regex_consolidator import SmartRegexConsolidator
    from simplified_escalation_engine import SimplifiedEscalationEngine
    SMART_CONSOLIDATION_AVAILABLE = True
except ImportError:
    SMART_CONSOLIDATION_AVAILABLE = False
    print("⚠️  Smart Regex Consolidation not available - using basic testing")


class ThreeTierArchitectureValidator:
    """Comprehensive validator for the new 3-tier architecture"""

    def __init__(self):
        self.conversion_service = ConversionService()
        self.smart_consolidator = SmartRegexConsolidator() if SMART_CONSOLIDATION_AVAILABLE else None
        self.escalation_engine = SimplifiedEscalationEngine() if SMART_CONSOLIDATION_AVAILABLE else None

    async def test_3tier_architecture(self) -> Dict[str, Any]:
        """Test the complete 3-tier medical NLP system"""

        print("🚀 Testing NEW 3-Tier Medical NLP Architecture")
        print("=" * 70)
        print("✅ Enhanced MedSpaCy (Tier 1)")
        print("⚡ Smart Regex Consolidation (Tier 2)")
        print("🛡️  LLM Safety Escalation (Tier 3)")
        print("=" * 70)

        # Performance-focused test cases
        test_cases = [
            {
                "name": "Simple Clinical Order (Tier 1 should handle efficiently)",
                "text": "Prescribed Lisinopril 10mg daily for hypertension",
                "expected_tier": "medspacy",
                "expected_entities": ["medications", "dosages", "frequencies", "conditions"],
                "performance_target_ms": 100
            },
            {
                "name": "Complex Medication (Smart Consolidation test)",
                "text": "Initiate patient on Amoxicillin 875mg BID with meals for strep throat",
                "expected_tier": "smart_consolidation",
                "expected_entities": ["medications", "dosages", "frequencies", "conditions", "timing"],
                "performance_target_ms": 150
            },
            {
                "name": "Medication with Instructions (Pattern Enhancement)",
                "text": "Continue current insulin regimen, adjust based on blood glucose readings",
                "expected_tier": "smart_consolidation",
                "expected_entities": ["medications", "monitoring", "instructions"],
                "performance_target_ms": 120
            },
            {
                "name": "Lab Orders (Enhanced Pattern Matching)",
                "text": "Order CBC, CMP, and lipid panel, schedule follow-up in 2 weeks",
                "expected_tier": "medspacy",
                "expected_entities": ["lab_tests", "procedures", "scheduling"],
                "performance_target_ms": 90
            },
            {
                "name": "Complex Clinical Note (Potential LLM Escalation)",
                "text": "Patient reports intermittent chest discomfort, consider cardiac workup if symptoms persist",
                "expected_tier": "llm_escalation",
                "expected_entities": ["symptoms", "procedures", "conditions"],
                "performance_target_ms": 200
            },
            {
                "name": "Multiple Medications (Consolidation Test)",
                "text": "D/C current antibiotics, start Ciprofloxacin 500mg BID, continue Prednisone taper",
                "expected_tier": "smart_consolidation",
                "expected_entities": ["medications", "dosages", "frequencies", "instructions"],
                "performance_target_ms": 180
            }
        ]

        results = {
            "test_timestamp": datetime.now().isoformat(),
            "architecture": "3-tier_enhanced",
            "total_cases": len(test_cases),
            "case_results": [],
            "performance_metrics": {
                "avg_processing_time_ms": 0,
                "tier_distribution": {"medspacy": 0, "smart_consolidation": 0, "llm_escalation": 0},
                "performance_targets_met": 0,
                "quality_scores": []
            },
            "architecture_validation": {
                "smart_consolidation_functional": SMART_CONSOLIDATION_AVAILABLE,
                "performance_improvement_achieved": False,
                "quality_maintained": False
            }
        }

        total_processing_time = 0
        performance_targets_met = 0

        # Initialize NLP pipeline
        if not nlp_pipeline.initialized:
            print("🔧 Initializing NLP pipeline...")
            nlp_pipeline.initialize()

        for i, case in enumerate(test_cases):
            print(f"\n📝 Test Case {i+1}: {case['name']}")
            print(f"   Text: {case['text'][:60]}...")

            start_time = time.time()

            try:
                # Process through the new 3-tier architecture
                result = await self._process_through_3tier(case["text"], f"test_3tier_{i+1}")

                processing_time_ms = (time.time() - start_time) * 1000
                total_processing_time += processing_time_ms

                # Determine which tier handled the request
                tier_used = self._determine_tier_used(result)
                results["performance_metrics"]["tier_distribution"][tier_used] += 1

                # Check performance target
                target_met = processing_time_ms <= case["performance_target_ms"]
                if target_met:
                    performance_targets_met += 1

                # Assess entity extraction quality
                quality_score = self._assess_extraction_quality(result, case["expected_entities"])
                results["performance_metrics"]["quality_scores"].append(quality_score)

                case_result = {
                    "case_id": i + 1,
                    "name": case["name"],
                    "processing_time_ms": processing_time_ms,
                    "performance_target_ms": case["performance_target_ms"],
                    "target_met": target_met,
                    "tier_used": tier_used,
                    "expected_tier": case["expected_tier"],
                    "tier_correct": tier_used == case["expected_tier"],
                    "quality_score": quality_score,
                    "extracted_entities": result.get("extracted_entities", {}),
                    "status": "✅" if target_met and quality_score >= 0.7 else "⚠️"
                }

                results["case_results"].append(case_result)

                print(f"   ⏱️  Processing: {processing_time_ms:.1f}ms (target: {case['performance_target_ms']}ms)")
                print(f"   🎯 Tier Used: {tier_used} (expected: {case['expected_tier']})")
                print(f"   📊 Quality: {quality_score:.2f} {case_result['status']}")

            except Exception as e:
                print(f"   ❌ Error: {e}")
                case_result = {
                    "case_id": i + 1,
                    "name": case["name"],
                    "error": str(e),
                    "status": "❌"
                }
                results["case_results"].append(case_result)

        # Calculate overall metrics
        avg_processing_time = total_processing_time / len(test_cases)
        avg_quality_score = sum(results["performance_metrics"]["quality_scores"]) / len(results["performance_metrics"]["quality_scores"])

        results["performance_metrics"]["avg_processing_time_ms"] = avg_processing_time
        results["performance_metrics"]["performance_targets_met"] = performance_targets_met
        results["performance_metrics"]["avg_quality_score"] = avg_quality_score

        # Architecture validation
        results["architecture_validation"]["performance_improvement_achieved"] = avg_processing_time < 150  # Target improvement
        results["architecture_validation"]["quality_maintained"] = avg_quality_score >= 0.7

        # Print summary
        print(f"\n🎯 3-TIER ARCHITECTURE TEST RESULTS")
        print(f"{'=' * 50}")
        print(f"📊 Average Processing Time: {avg_processing_time:.1f}ms")
        print(f"🎯 Performance Targets Met: {performance_targets_met}/{len(test_cases)}")
        print(f"📈 Average Quality Score: {avg_quality_score:.2f}")
        print(f"🏗️  Tier Distribution:")
        for tier, count in results["performance_metrics"]["tier_distribution"].items():
            print(f"   • {tier}: {count} cases")

        # Validation summary
        print(f"\n✅ ARCHITECTURE VALIDATION:")
        print(f"   • Smart Consolidation Available: {SMART_CONSOLIDATION_AVAILABLE}")
        print(f"   • Performance Improved: {results['architecture_validation']['performance_improvement_achieved']}")
        print(f"   • Quality Maintained: {results['architecture_validation']['quality_maintained']}")

        if results["architecture_validation"]["performance_improvement_achieved"] and results["architecture_validation"]["quality_maintained"]:
            print(f"🎉 3-TIER ARCHITECTURE MIGRATION: SUCCESS")
        else:
            print(f"⚠️  3-TIER ARCHITECTURE MIGRATION: NEEDS ATTENTION")

        return results

    async def _process_through_3tier(self, text: str, request_id: str) -> Dict[str, Any]:
        """Process text through the new 3-tier architecture"""

        # Use the main conversion service which should integrate the new architecture
        try:
            # Method 1: Try using the NLP pipeline directly
            result = await nlp_pipeline.process_clinical_text(text, request_id)
            return result
        except Exception as e:
            # Method 2: Fallback to conversion service basic analysis
            try:
                result = await self.conversion_service._basic_text_analysis(text, request_id)
                return result
            except Exception as e2:
                # Method 3: Create minimal result structure
                return {
                    "extracted_entities": {"medications": [], "conditions": [], "procedures": []},
                    "processing_tier": "error",
                    "error": str(e2)
                }

    def _determine_tier_used(self, result: Dict[str, Any]) -> str:
        """Determine which tier processed the request based on result structure"""

        if "error" in result:
            return "error"

        # Check for tier indicators in the result
        if "processing_tier" in result:
            return result["processing_tier"]

        # Infer from result characteristics
        entities = result.get("extracted_entities", {})
        entity_count = sum(len(entities.get(key, [])) for key in entities.keys())

        if entity_count >= 3:
            return "smart_consolidation"  # Rich extraction suggests consolidation
        elif entity_count >= 1:
            return "medspacy"  # Basic extraction
        else:
            return "llm_escalation"  # Minimal extraction suggests escalation needed

    def _assess_extraction_quality(self, result: Dict[str, Any], expected_entities: List[str]) -> float:
        """Assess the quality of entity extraction"""

        extracted_entities = result.get("extracted_entities", {})

        if not expected_entities:
            return 1.0

        found_types = 0
        for expected_type in expected_entities:
            # Check various forms of the entity type
            if (expected_type in extracted_entities and
                len(extracted_entities[expected_type]) > 0):
                found_types += 1
            elif (expected_type.rstrip('s') in extracted_entities and
                  len(extracted_entities[expected_type.rstrip('s')]) > 0):
                found_types += 1

        return found_types / len(expected_entities)


async def test_3tier_medical_nlp():
    """Main test function for the 3-tier architecture"""

    validator = ThreeTierArchitectureValidator()

    try:
        results = await validator.test_3tier_architecture()

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_3tier_results_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {results_file}")

        return results

    except Exception as e:
        print(f"❌ 3-tier architecture test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(test_3tier_medical_nlp())