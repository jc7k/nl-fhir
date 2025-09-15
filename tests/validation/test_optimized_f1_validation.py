#!/usr/bin/env python3
"""
F1 Validation Test with Optimized Configuration
Tests the optimized threshold and enhanced MedSpaCy rules
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime
import time

# Apply AGGRESSIVE optimization - further reduced thresholds
os.environ['LLM_ESCALATION_THRESHOLD'] = '0.70'  # More aggressive reduction
os.environ['LLM_ESCALATION_CONFIDENCE_CHECK'] = 'weighted_average'
os.environ['LLM_ESCALATION_MIN_ENTITIES'] = '2'  # Reduce minimum entities required

from src.nl_fhir.services.nlp.pipeline import nlp_pipeline

logger = logging.getLogger(__name__)

class OptimizedF1Validator:
    """Validates F1 performance with optimized configuration"""

    def __init__(self):
        self.baseline_config = {
            "threshold": 0.85,
            "rules": 25,
            "avg_time": 15.0
        }

        self.optimized_config = {
            "threshold": 0.70,
            "rules": 70,  # From enhanced MedSpaCy rules
            "target_time": 5.0
        }

    def load_realistic_test_cases(self) -> List[Dict]:
        """Load our generated realistic clinical text cases"""

        test_cases = []

        # Load synthetic test cases
        try:
            with open('realistic_clinical_test_cases_20250914_093841.json', 'r') as f:
                data = json.load(f)
                # Take smaller sample for faster testing
                test_cases.extend(data.get('clean', [])[:5])
                test_cases.extend(data.get('realistic', [])[:8])
                test_cases.extend(data.get('complex', [])[:5])
        except FileNotFoundError:
            logger.warning("Synthetic test cases not found")

        # Load clinical trial cases
        try:
            with open('clinical_trials_test_cases_20250914_094227.json', 'r') as f:
                trial_data = json.load(f)
                test_cases.extend(trial_data[:7])  # Sample of clinical trials
        except FileNotFoundError:
            logger.warning("Clinical trial test cases not found")

        return test_cases

    async def calculate_f1_score(self, expected: Dict, extracted_entities: List[Dict]) -> float:
        """Calculate F1 score for entity extraction"""

        if not expected:
            return 0.0

        # Extract entity texts and types for comparison
        extracted_by_type = {}
        for entity in extracted_entities:
            etype = entity.get('type', '').lower()
            text = entity.get('text', '').lower().strip()
            if etype not in extracted_by_type:
                extracted_by_type[etype] = []
            extracted_by_type[etype].append(text)

        # Calculate matches
        matches = 0
        total_expected = len(expected)

        for expected_type, expected_value in expected.items():
            if not expected_value:
                continue

            expected_value_norm = str(expected_value).lower().strip()

            # Map expected types to extracted types
            type_mappings = {
                'medication': ['medication'],
                'patient': ['person', 'patient'],
                'dosage': ['dosage'],
                'frequency': ['frequency'],
                'condition': ['condition']
            }

            found_match = False
            search_types = type_mappings.get(expected_type, [expected_type])

            for search_type in search_types:
                if search_type in extracted_by_type:
                    for extracted_text in extracted_by_type[search_type]:
                        # Check for exact match or substring match
                        if (expected_value_norm == extracted_text or
                            expected_value_norm in extracted_text or
                            extracted_text in expected_value_norm):
                            found_match = True
                            break
                if found_match:
                    break

            if found_match:
                matches += 1

        # Calculate F1 score
        precision = matches / max(len([e for entities in extracted_by_type.values() for e in entities]), 1)
        recall = matches / total_expected if total_expected > 0 else 0

        if precision + recall == 0:
            return 0.0

        f1 = 2 * (precision * recall) / (precision + recall)
        return f1

    async def run_optimized_validation(self):
        """Run comprehensive validation with optimized configuration"""

        print("🚀 F1 VALIDATION: Optimized Configuration vs Baseline")
        print("=" * 60)
        print(f"Baseline: {self.baseline_config['threshold']} threshold, {self.baseline_config['rules']} rules, {self.baseline_config['avg_time']}s")
        print(f"Optimized: {self.optimized_config['threshold']} threshold, {self.optimized_config['rules']} rules, target <{self.optimized_config['target_time']}s")
        print()

        # Initialize pipeline with optimized settings
        if not nlp_pipeline.initialized:
            print("🔧 Initializing optimized NLP pipeline...")
            nlp_pipeline.initialize()

        # Load test cases
        test_cases = self.load_realistic_test_cases()
        print(f"📋 Testing on {len(test_cases)} realistic clinical text cases")

        results = {
            "test_timestamp": datetime.now().isoformat(),
            "configuration": {
                "threshold": float(os.environ['LLM_ESCALATION_THRESHOLD']),
                "min_entities": int(os.environ['LLM_ESCALATION_MIN_ENTITIES']),
                "enhanced_rules": self.optimized_config['rules']
            },
            "case_results": [],
            "performance_metrics": {}
        }

        # Performance tracking
        total_processing_time = 0
        total_f1_scores = []
        llm_escalation_count = 0
        successful_cases = 0

        print("\n🧪 TESTING RESULTS:")
        print("-" * 60)

        for i, case in enumerate(test_cases[:20]):  # Test first 20 cases
            try:
                text = case.get('text', '')
                expected = case.get('expected', {})
                complexity = case.get('complexity', 'unknown')

                print(f"Case {i+1:2d} ({complexity:8s}): {text[:50]}...")

                start_time = time.time()

                # Process with optimized configuration
                result = await nlp_pipeline.process_clinical_text(
                    text,
                    request_id=f"opt_val_{i+1}"
                )

                processing_time = time.time() - start_time
                total_processing_time += processing_time

                # Extract entities
                entities = result.get('extracted_entities', {}).get('entities', [])

                # Calculate F1 score
                f1_score = await self.calculate_f1_score(expected, entities)
                total_f1_scores.append(f1_score)

                # Check LLM escalation
                llm_escalated = 'escalated_to_llm' in result.get('structured_output', {}).get('method', '')
                if llm_escalated:
                    llm_escalation_count += 1

                # Track case result
                case_result = {
                    "case_id": i + 1,
                    "complexity": complexity,
                    "f1_score": f1_score,
                    "processing_time": processing_time,
                    "entities_found": len(entities),
                    "llm_escalated": llm_escalated
                }
                results["case_results"].append(case_result)
                successful_cases += 1

                # Display results
                status = "✅" if f1_score >= 0.75 else "⚠️" if f1_score >= 0.5 else "❌"
                print(f"         F1: {f1_score:.3f} | Time: {processing_time:.1f}s | Entities: {len(entities)} | LLM: {'Y' if llm_escalated else 'N'} {status}")

            except Exception as e:
                logger.error(f"Case {i+1} failed: {e}")
                print(f"         ERROR: {str(e)[:50]}")

        # Calculate final metrics
        avg_f1 = sum(total_f1_scores) / len(total_f1_scores) if total_f1_scores else 0
        avg_processing_time = total_processing_time / successful_cases if successful_cases > 0 else 0
        escalation_rate = (llm_escalation_count / successful_cases) * 100 if successful_cases > 0 else 0

        results["performance_metrics"] = {
            "average_f1_score": avg_f1,
            "average_processing_time": avg_processing_time,
            "llm_escalation_rate": escalation_rate,
            "successful_cases": successful_cases,
            "total_cases_tested": len(test_cases[:20]),
            "cases_above_target": sum(1 for f1 in total_f1_scores if f1 >= 0.75),
            "performance_improvement": max(0, (self.baseline_config['avg_time'] - avg_processing_time) / self.baseline_config['avg_time']) * 100
        }

        print("\n" + "=" * 60)
        print("📊 OPTIMIZED CONFIGURATION RESULTS:")
        print("=" * 60)
        print(f"Average F1 Score:        {avg_f1:.3f}")
        print(f"Target Achievement:      {results['performance_metrics']['cases_above_target']}/{successful_cases} cases ≥ 0.75 F1")
        print(f"Average Processing Time: {avg_processing_time:.1f}s")
        print(f"Performance Improvement: {results['performance_metrics']['performance_improvement']:.1f}% faster")
        print(f"LLM Escalation Rate:     {escalation_rate:.1f}%")
        print()

        # Determine success
        success_criteria = {
            "f1_target_met": avg_f1 >= 0.75,
            "processing_improved": avg_processing_time < self.baseline_config['avg_time'],
            "escalation_reduced": escalation_rate < 90  # Target: reduce from 100%
        }

        if success_criteria["f1_target_met"] and success_criteria["processing_improved"]:
            print("🎉 CONFIGURATION OPTIMIZATION: SUCCESS!")
            print("   ✅ F1 target achieved (≥ 0.75)")
            print("   ✅ Processing time improved")
            if success_criteria["escalation_reduced"]:
                print("   ✅ LLM escalation rate reduced")
            else:
                print("   ⚠️  LLM escalation still high (may need further tuning)")
        else:
            print("⚠️  CONFIGURATION OPTIMIZATION: Partial Success")
            if not success_criteria["f1_target_met"]:
                print("   ❌ F1 target not met - needs further rule enhancement")
            if not success_criteria["processing_improved"]:
                print("   ❌ Processing time not improved - needs threshold adjustment")

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"optimized_f1_validation_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Detailed results saved to: {filename}")

        return results

async def main():
    """Execute optimized F1 validation"""
    validator = OptimizedF1Validator()
    results = await validator.run_optimized_validation()

    return results

if __name__ == "__main__":
    asyncio.run(main())