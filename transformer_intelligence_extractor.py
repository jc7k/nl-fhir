#!/usr/bin/env python3
"""
Transformer Intelligence Extractor - Phase 0 of 3-Tier Architecture Migration

This tool extracts valuable patterns from the current Transformer NER model
before we eliminate it, preserving the intelligence for Smart Regex Consolidation.

CRITICAL: Run this BEFORE removing Tier 2 Transformers to capture learned patterns.
"""

import os
import json
import time
import re
import statistics
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, Counter

# Set configuration for current system
os.environ['LLM_ESCALATION_THRESHOLD'] = '0.72'
os.environ['LLM_ESCALATION_MIN_ENTITIES'] = '3'

from src.nl_fhir.services.nlp.models import NLPModelManager

class TransformerIntelligenceExtractor:
    """Extract valuable patterns from Transformer NER before elimination"""

    def __init__(self):
        self.model_manager = NLPModelManager()
        self.extracted_patterns = {
            "medication_variations": {},
            "dosage_patterns": {},
            "frequency_patterns": {},
            "condition_patterns": {},
            "confidence_thresholds": {},
            "entity_type_mappings": {},
            "gap_analysis": {}
        }

    def extract_transformer_intelligence(self, test_cases: List[Dict]) -> Dict:
        """
        Main intelligence extraction process

        Args:
            test_cases: List of test cases with text and expected entities

        Returns:
            Comprehensive intelligence report for Smart Regex building
        """

        print("🔬 PHASE 0: TRANSFORMER INTELLIGENCE EXTRACTION")
        print("=" * 60)

        intelligence_report = {
            "extraction_timestamp": datetime.now().isoformat(),
            "test_cases_analyzed": len(test_cases),
            "tier_comparison": {},
            "pattern_intelligence": {},
            "consolidation_recommendations": {}
        }

        # Step 1: Comparative Analysis (MedSpaCy vs Transformer vs Combined)
        print("\n📊 Step 1: Comparative Tier Analysis...")
        tier_comparison = self.analyze_tier_performance(test_cases)
        intelligence_report["tier_comparison"] = tier_comparison

        # Step 2: Pattern Intelligence Extraction
        print("\n🧠 Step 2: Pattern Intelligence Mining...")
        pattern_intelligence = self.mine_pattern_intelligence(test_cases)
        intelligence_report["pattern_intelligence"] = pattern_intelligence

        # Step 3: Gap Analysis (What does Transformer catch that MedSpaCy misses?)
        print("\n🎯 Step 3: Gap Analysis for Smart Regex...")
        gap_analysis = self.analyze_extraction_gaps(test_cases)
        intelligence_report["gap_analysis"] = gap_analysis

        # Step 4: Smart Regex Consolidation Recommendations
        print("\n⚡ Step 4: Consolidation Strategy...")
        consolidation_recommendations = self.generate_consolidation_recommendations(
            tier_comparison, pattern_intelligence, gap_analysis
        )
        intelligence_report["consolidation_recommendations"] = consolidation_recommendations

        return intelligence_report

    def analyze_tier_performance(self, test_cases: List[Dict]) -> Dict:
        """Analyze performance of each tier individually and combined"""

        tier_results = {
            "medspacy_only": [],
            "transformer_only": [],
            "regex_only": [],
            "medspacy_transformer_combined": []
        }

        processing_times = {
            "medspacy": [],
            "transformer": [],
            "regex": [],
            "combined": []
        }

        for i, case in enumerate(test_cases):
            print(f"   Analyzing case {i+1}/{len(test_cases)}: {case['text'][:50]}...")

            # Test each tier individually
            medspacy_result, medspacy_time = self.test_medspacy_only(case['text'])
            transformer_result, transformer_time = self.test_transformer_only(case['text'])
            regex_result, regex_time = self.test_regex_only(case['text'])

            # Test smart combination
            combined_result, combined_time = self.test_smart_combination(
                case['text'], medspacy_result, transformer_result
            )

            # Calculate F1 scores
            medspacy_f1 = self.calculate_f1(medspacy_result, case.get('expected', {}))
            transformer_f1 = self.calculate_f1(transformer_result, case.get('expected', {}))
            regex_f1 = self.calculate_f1(regex_result, case.get('expected', {}))
            combined_f1 = self.calculate_f1(combined_result, case.get('expected', {}))

            # Store results
            tier_results["medspacy_only"].append(medspacy_f1)
            tier_results["transformer_only"].append(transformer_f1)
            tier_results["regex_only"].append(regex_f1)
            tier_results["medspacy_transformer_combined"].append(combined_f1)

            # Store timing
            processing_times["medspacy"].append(medspacy_time)
            processing_times["transformer"].append(transformer_time)
            processing_times["regex"].append(regex_time)
            processing_times["combined"].append(combined_time)

        # Calculate averages and improvements
        comparison_results = {
            "f1_scores": {
                "medspacy_avg": statistics.mean(tier_results["medspacy_only"]),
                "transformer_avg": statistics.mean(tier_results["transformer_only"]),
                "regex_avg": statistics.mean(tier_results["regex_only"]),
                "combined_avg": statistics.mean(tier_results["medspacy_transformer_combined"])
            },
            "processing_times": {
                "medspacy_avg": statistics.mean(processing_times["medspacy"]),
                "transformer_avg": statistics.mean(processing_times["transformer"]),
                "regex_avg": statistics.mean(processing_times["regex"]),
                "combined_avg": statistics.mean(processing_times["combined"])
            },
            "transformer_value_analysis": {
                "f1_improvement": statistics.mean(tier_results["medspacy_transformer_combined"]) - statistics.mean(tier_results["medspacy_only"]),
                "time_cost": statistics.mean(processing_times["transformer"]),
                "roi_analysis": "Calculate if transformer improvement justifies time cost"
            }
        }

        return comparison_results

    def mine_pattern_intelligence(self, test_cases: List[Dict]) -> Dict:
        """Mine intelligent patterns from successful transformer extractions"""

        pattern_intelligence = {
            "successful_medication_patterns": Counter(),
            "successful_dosage_patterns": Counter(),
            "successful_frequency_patterns": Counter(),
            "transformer_unique_extractions": [],
            "confidence_analysis": defaultdict(list)
        }

        for case in test_cases:
            # Get transformer extractions
            transformer_result, _ = self.test_transformer_only(case['text'])

            # Analyze successful patterns
            for category, entities in transformer_result.items():
                for entity in entities:
                    if entity.get('confidence', 0) > 0.7:  # High confidence extractions

                        # Extract pattern around successful entity
                        pattern = self.extract_pattern_context(case['text'], entity)

                        if category == "medications":
                            pattern_intelligence["successful_medication_patterns"][pattern] += 1
                        elif category == "dosages":
                            pattern_intelligence["successful_dosage_patterns"][pattern] += 1
                        elif category == "frequencies":
                            pattern_intelligence["successful_frequency_patterns"][pattern] += 1

                        # Confidence analysis
                        pattern_intelligence["confidence_analysis"][category].append(entity.get('confidence', 0))

        # Convert counters to regular dicts for JSON serialization
        pattern_intelligence["successful_medication_patterns"] = dict(pattern_intelligence["successful_medication_patterns"])
        pattern_intelligence["successful_dosage_patterns"] = dict(pattern_intelligence["successful_dosage_patterns"])
        pattern_intelligence["successful_frequency_patterns"] = dict(pattern_intelligence["successful_frequency_patterns"])

        return pattern_intelligence

    def analyze_extraction_gaps(self, test_cases: List[Dict]) -> Dict:
        """Analyze what Transformer catches that MedSpaCy misses"""

        gap_analysis = {
            "medspacy_gaps": [],
            "transformer_unique_value": [],
            "recommended_regex_additions": [],
            "gap_frequency": Counter()
        }

        for case in test_cases:
            medspacy_result, _ = self.test_medspacy_only(case['text'])
            transformer_result, _ = self.test_transformer_only(case['text'])

            # Find unique transformer extractions
            transformer_unique = self.find_unique_extractions(transformer_result, medspacy_result)

            if transformer_unique:
                gap_analysis["transformer_unique_value"].append({
                    "text": case['text'],
                    "transformer_unique": transformer_unique,
                    "medspacy_missed": self.identify_medspacy_gaps(medspacy_result, case.get('expected', {}))
                })

                # Count gap types
                for category, entities in transformer_unique.items():
                    for entity in entities:
                        gap_type = f"{category}:{entity.get('text', '')}"
                        gap_analysis["gap_frequency"][gap_type] += 1

        # Generate regex recommendations based on gaps
        gap_analysis["recommended_regex_additions"] = self.generate_regex_from_gaps(
            gap_analysis["gap_frequency"]
        )

        return gap_analysis

    def test_medspacy_only(self, text: str) -> Tuple[Dict, float]:
        """Test MedSpaCy extraction only"""
        start_time = time.time()

        medspacy_nlp = self.model_manager.load_medspacy_clinical_engine()
        if medspacy_nlp:
            result = self.model_manager._extract_with_medspacy_clinical(text, medspacy_nlp)
        else:
            result = {"medications": [], "dosages": [], "frequencies": [], "patients": [], "conditions": [], "procedures": [], "lab_tests": []}

        processing_time = time.time() - start_time
        return result, processing_time

    def test_transformer_only(self, text: str) -> Tuple[Dict, float]:
        """Test Transformer NER extraction only"""
        start_time = time.time()

        ner_model = self.model_manager.load_medical_ner_model()
        if ner_model and not isinstance(ner_model, dict):
            result = self.model_manager._extract_with_transformers(text, ner_model)
        else:
            result = {"medications": [], "dosages": [], "frequencies": [], "patients": [], "conditions": [], "procedures": [], "lab_tests": []}

        processing_time = time.time() - start_time
        return result, processing_time

    def test_regex_only(self, text: str) -> Tuple[Dict, float]:
        """Test Regex extraction only"""
        start_time = time.time()

        fallback_nlp = self.model_manager.load_fallback_nlp()
        result = self.model_manager._extract_with_regex(text, fallback_nlp)

        processing_time = time.time() - start_time
        return result, processing_time

    def test_smart_combination(self, text: str, medspacy_result: Dict, transformer_result: Dict) -> Tuple[Dict, float]:
        """Test smart combination of MedSpaCy + Transformer"""
        start_time = time.time()

        # Intelligent merge: MedSpaCy base + Transformer gap filling
        combined_result = medspacy_result.copy()

        for category, transformer_entities in transformer_result.items():
            for t_entity in transformer_entities:
                # Check if this entity adds value (not already covered by MedSpaCy)
                if not self.is_entity_covered(t_entity, combined_result.get(category, [])):
                    combined_result[category].append({
                        **t_entity,
                        "source": "transformer_gap_fill"
                    })

        processing_time = time.time() - start_time
        return combined_result, processing_time

    def calculate_f1(self, extracted: Dict, expected: Dict) -> float:
        """Calculate F1 score for extraction results"""
        if not expected:
            return 0.0

        matches = 0
        total_expected = len(expected)
        total_extracted = sum(len(entities) for entities in extracted.values() if isinstance(entities, list))

        for key, value in expected.items():
            entity_list = extracted.get(f"{key}s", extracted.get(key, []))
            if not isinstance(entity_list, list):
                entity_list = [entity_list]

            for entity in entity_list:
                entity_text = entity.get('text', '') if isinstance(entity, dict) else str(entity)
                if value.lower() in entity_text.lower() or entity_text.lower() in value.lower():
                    matches += 1
                    break

        precision = matches / max(total_extracted, 1)
        recall = matches / max(total_expected, 1)

        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)

    def extract_pattern_context(self, text: str, entity: Dict) -> str:
        """Extract regex pattern from successful entity extraction"""
        entity_text = entity.get('text', '')

        # Simple pattern extraction - look for context around entity
        text_lower = text.lower()
        entity_lower = entity_text.lower()

        entity_pos = text_lower.find(entity_lower)
        if entity_pos == -1:
            return entity_lower  # Fallback to entity itself

        # Extract 10 characters before and after for context
        start = max(0, entity_pos - 10)
        end = min(len(text), entity_pos + len(entity_text) + 10)
        context = text[start:end]

        # Convert to basic regex pattern
        pattern = re.escape(entity_text)
        return pattern

    def find_unique_extractions(self, transformer_result: Dict, medspacy_result: Dict) -> Dict:
        """Find entities extracted by transformer but missed by MedSpaCy"""
        unique_extractions = {}

        for category, transformer_entities in transformer_result.items():
            medspacy_entities = medspacy_result.get(category, [])

            unique_in_category = []
            for t_entity in transformer_entities:
                if not self.is_entity_covered(t_entity, medspacy_entities):
                    unique_in_category.append(t_entity)

            if unique_in_category:
                unique_extractions[category] = unique_in_category

        return unique_extractions

    def is_entity_covered(self, entity: Dict, existing_entities: List[Dict]) -> bool:
        """Check if entity is already covered by existing extractions"""
        entity_text = entity.get('text', '').lower()

        for existing in existing_entities:
            existing_text = existing.get('text', '').lower()
            if entity_text in existing_text or existing_text in entity_text:
                return True

        return False

    def identify_medspacy_gaps(self, medspacy_result: Dict, expected: Dict) -> List[str]:
        """Identify what MedSpaCy missed from expected results"""
        gaps = []

        for key, value in expected.items():
            entity_list = medspacy_result.get(f"{key}s", medspacy_result.get(key, []))

            found = False
            for entity in entity_list:
                entity_text = entity.get('text', '') if isinstance(entity, dict) else str(entity)
                if value.lower() in entity_text.lower() or entity_text.lower() in value.lower():
                    found = True
                    break

            if not found:
                gaps.append(f"{key}:{value}")

        return gaps

    def generate_regex_from_gaps(self, gap_frequency: Counter) -> List[Dict]:
        """Generate regex patterns from frequent gaps"""
        recommendations = []

        # Focus on gaps that appear multiple times
        for gap, frequency in gap_frequency.most_common(10):
            if frequency >= 2:  # Appears in multiple test cases
                category, text = gap.split(':', 1)

                regex_pattern = {
                    "category": category,
                    "text": text,
                    "frequency": frequency,
                    "suggested_pattern": re.escape(text),
                    "priority": "HIGH" if frequency >= 3 else "MEDIUM"
                }
                recommendations.append(regex_pattern)

        return recommendations

    def generate_consolidation_recommendations(self, tier_comparison: Dict, pattern_intelligence: Dict, gap_analysis: Dict) -> Dict:
        """Generate specific recommendations for Smart Regex Consolidation"""

        recommendations = {
            "consolidation_strategy": {},
            "pattern_priorities": {},
            "implementation_plan": {},
            "expected_performance": {}
        }

        # Analyze transformer value
        f1_improvement = tier_comparison["transformer_value_analysis"]["f1_improvement"]
        time_cost = tier_comparison["transformer_value_analysis"]["time_cost"]

        if f1_improvement < 0.05 and time_cost > 100:  # Less than 5% improvement, >100ms cost
            strategy = "ELIMINATE_TRANSFORMER"
            confidence = "HIGH"
        elif f1_improvement < 0.02:
            strategy = "MERGE_PATTERNS_ONLY"
            confidence = "MEDIUM"
        else:
            strategy = "SELECTIVE_PATTERN_PRESERVATION"
            confidence = "LOW"

        recommendations["consolidation_strategy"] = {
            "strategy": strategy,
            "confidence": confidence,
            "reasoning": f"F1 improvement: {f1_improvement:.3f}, Time cost: {time_cost:.1f}ms"
        }

        # Pattern priorities
        medication_patterns = pattern_intelligence.get("successful_medication_patterns", {})
        top_medication_patterns = sorted(medication_patterns.items(), key=lambda x: x[1], reverse=True)[:5]

        recommendations["pattern_priorities"] = {
            "high_priority_medications": [p[0] for p in top_medication_patterns],
            "gap_fill_patterns": [r["suggested_pattern"] for r in gap_analysis.get("recommended_regex_additions", [])[:5]],
            "confidence_thresholds": pattern_intelligence.get("confidence_analysis", {})
        }

        # Implementation plan
        recommendations["implementation_plan"] = {
            "phase_1": "Extract high-value transformer patterns to regex",
            "phase_2": "Build Smart Regex Consolidation system",
            "phase_3": "Remove transformer tier and validate performance",
            "estimated_time": "2-3 days implementation"
        }

        # Expected performance
        current_combined_f1 = tier_comparison["f1_scores"]["combined_avg"]
        medspacy_f1 = tier_comparison["f1_scores"]["medspacy_avg"]

        recommendations["expected_performance"] = {
            "current_4tier_f1": current_combined_f1,
            "predicted_3tier_f1": medspacy_f1 + (f1_improvement * 0.7),  # Assume 70% of transformer value preserved
            "speed_improvement": f"Remove {time_cost:.1f}ms transformer processing time",
            "complexity_reduction": "25% fewer architectural components"
        }

        return recommendations

def main():
    """Run Transformer Intelligence Extraction"""

    # Load test cases from our validation suite
    test_cases = [
        {
            "text": "Amoxicillin suspension 250mg/5ml, administer 5ml PO TID for acute otitis media",
            "expected": {"medication": "amoxicillin", "dosage": "250mg/5ml", "frequency": "TID", "condition": "otitis media"}
        },
        {
            "text": "Children's ibuprofen suspension 100mg/5ml, give 2.5ml q6h PRN fever",
            "expected": {"medication": "ibuprofen", "dosage": "100mg/5ml", "frequency": "q6h", "condition": "fever"}
        },
        {
            "text": "STAT Epinephrine 1mg IV push for anaphylaxis shock",
            "expected": {"medication": "epinephrine", "dosage": "1mg", "route": "IV push", "condition": "anaphylaxis"}
        },
        {
            "text": "Morphine 4mg IV bolus q2h PRN severe chest pain",
            "expected": {"medication": "morphine", "dosage": "4mg", "route": "IV bolus", "condition": "chest pain"}
        },
        {
            "text": "Metformin 500mg PO BID for type 2 diabetes management",
            "expected": {"medication": "metformin", "dosage": "500mg", "frequency": "BID", "condition": "diabetes"}
        },
        {
            "text": "Lisinopril 10mg daily by mouth for hypertension control",
            "expected": {"medication": "lisinopril", "dosage": "10mg", "frequency": "daily", "condition": "hypertension"}
        }
    ]

    # Initialize extractor
    extractor = TransformerIntelligenceExtractor()

    # Extract intelligence
    intelligence_report = extractor.extract_transformer_intelligence(test_cases)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"transformer_intelligence_extraction_{timestamp}.json"

    # Convert numpy float32 to regular floats for JSON serialization
    def convert_floats(obj):
        if isinstance(obj, dict):
            return {key: convert_floats(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_floats(item) for item in obj]
        elif hasattr(obj, 'item'):  # numpy scalars
            return obj.item()
        else:
            return obj

    intelligence_report = convert_floats(intelligence_report)

    with open(filename, 'w') as f:
        json.dump(intelligence_report, f, indent=2)

    print(f"\n💾 Intelligence extraction complete! Results saved to: {filename}")

    # Print summary
    print("\n🎯 EXTRACTION SUMMARY:")
    print("=" * 60)

    tier_comparison = intelligence_report["tier_comparison"]
    consolidation = intelligence_report["consolidation_recommendations"]

    print(f"📊 F1 Score Analysis:")
    print(f"   MedSpaCy Only:     {tier_comparison['f1_scores']['medspacy_avg']:.3f}")
    print(f"   Transformer Only:  {tier_comparison['f1_scores']['transformer_avg']:.3f}")
    print(f"   Combined:          {tier_comparison['f1_scores']['combined_avg']:.3f}")
    print(f"   Transformer Value: {tier_comparison['transformer_value_analysis']['f1_improvement']:+.3f}")

    print(f"\n⚡ Performance Analysis:")
    print(f"   MedSpaCy Time:     {tier_comparison['processing_times']['medspacy_avg']:.1f}ms")
    print(f"   Transformer Time:  {tier_comparison['processing_times']['transformer_avg']:.1f}ms")
    print(f"   Combined Time:     {tier_comparison['processing_times']['combined_avg']:.1f}ms")

    print(f"\n🏗️ Consolidation Recommendation:")
    print(f"   Strategy:          {consolidation['consolidation_strategy']['strategy']}")
    print(f"   Confidence:        {consolidation['consolidation_strategy']['confidence']}")
    print(f"   Reasoning:         {consolidation['consolidation_strategy']['reasoning']}")

    print(f"\n🎯 Next Steps:")
    print(f"   1. {consolidation['implementation_plan']['phase_1']}")
    print(f"   2. {consolidation['implementation_plan']['phase_2']}")
    print(f"   3. {consolidation['implementation_plan']['phase_3']}")
    print(f"   Estimated Time:    {consolidation['implementation_plan']['estimated_time']}")

    return intelligence_report

if __name__ == "__main__":
    main()