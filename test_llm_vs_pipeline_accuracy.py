#!/usr/bin/env python3
"""
LLM vs Current Pipeline Medical Accuracy Comparison
Evaluates which approach provides better medical entity extraction safety
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nl_fhir.services.nlp.models import extract_medical_entities
from nl_fhir.services.nlp.llm_processor import LLMProcessor

class AccuracyComparison:
    def __init__(self):
        self.llm_processor = LLMProcessor()
        self.test_cases = [
            {
                "text": "Started patient Mia Scott on 500mg Ciprofloxacin twice daily for traveler's diarrhea; advised on hydration and rest.",
                "expected_entities": {
                    "medications": ["Ciprofloxacin"],
                    "dosages": ["500mg"],
                    "frequencies": ["twice daily"],
                    "conditions": ["traveler's diarrhea"]
                }
            },
            {
                "text": "Prescribed patient Ethan Rivera 2L oxygen via nasal cannula continuously for hypoxemia; home oxygen setup arranged.",
                "expected_entities": {
                    "medications": ["oxygen"],
                    "dosages": ["2L"],
                    "routes": ["nasal cannula"],
                    "frequencies": ["continuously"],
                    "conditions": ["hypoxemia"]
                }
            },
            {
                "text": "Prescribed patient Liam Brooks 100mg Hydroxyurea daily for sickle cell disease; CBC tracked.",
                "expected_entities": {
                    "medications": ["Hydroxyurea"],
                    "dosages": ["100mg"],
                    "frequencies": ["daily"],
                    "conditions": ["sickle cell disease"],
                    "lab_tests": ["CBC"]
                }
            },
            {
                "text": "Order CBC, BMP, and lipid panel for patient John Smith tomorrow morning.",
                "expected_entities": {
                    "lab_tests": ["CBC", "BMP", "lipid panel"],
                    "temporal": ["tomorrow morning"]
                }
            },
            {
                "text": "Start metformin 850mg twice daily with meals for diabetes management.",
                "expected_entities": {
                    "medications": ["metformin"],
                    "dosages": ["850mg"],
                    "frequencies": ["twice daily"],
                    "conditions": ["diabetes"]
                }
            }
        ]
    
    async def test_current_pipeline(self, text: str) -> Dict[str, Any]:
        """Test current transformer-based pipeline"""
        start_time = time.time()
        
        try:
            results = extract_medical_entities(text)
            processing_time = time.time() - start_time
            
            # Analyze confidence levels and entity coverage
            all_entities = []
            confidence_levels = []
            
            for category, entities in results.items():
                for entity in entities:
                    all_entities.append({
                        "text": entity["text"],
                        "type": category,
                        "confidence": entity.get("confidence", 0.0),
                        "source": "transformer"
                    })
                    confidence_levels.append(entity.get("confidence", 0.0))
            
            avg_confidence = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0.0
            min_confidence = min(confidence_levels) if confidence_levels else 0.0
            
            return {
                "entities": all_entities,
                "total_entities": len(all_entities),
                "avg_confidence": avg_confidence,
                "min_confidence": min_confidence,
                "processing_time": processing_time,
                "low_confidence_count": sum(1 for c in confidence_levels if c < 0.6),
                "method": "current_pipeline"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "method": "current_pipeline",
                "processing_time": time.time() - start_time
            }
    
    async def test_llm_escalation(self, text: str) -> Dict[str, Any]:
        """Test LLM escalation approach"""
        start_time = time.time()
        
        try:
            # Initialize LLM processor if needed
            if not self.llm_processor.initialized:
                self.llm_processor.initialize()
            
            # Process with LLM for structured output
            llm_results = self.llm_processor.process_clinical_text(text, [], "test-llm")
            processing_time = time.time() - start_time
            
            # Extract entities from LLM structured output
            structured_data = llm_results.get("structured_output", {})
            
            all_entities = []
            
            # Map LLM output to entities (assuming high confidence for LLM)
            entity_mappings = {
                "medications": "medications",
                "dosages": "dosages", 
                "frequencies": "frequencies",
                "conditions": "conditions",
                "lab_tests": "lab_tests",
                "routes": "routes",
                "temporal": "temporal"
            }
            
            for llm_key, entity_type in entity_mappings.items():
                if llm_key in structured_data:
                    items = structured_data[llm_key]
                    if isinstance(items, str):
                        items = [items]
                    elif isinstance(items, list):
                        pass
                    elif isinstance(items, dict):
                        # Handle dict case - convert to string or extract relevant field
                        items = [str(items)]
                    else:
                        continue
                    
                    for item in items:
                        if isinstance(item, dict):
                            # If item is a dict, try to get text representation
                            item_text = item.get('text', str(item))
                        else:
                            item_text = str(item)
                        
                        if item_text and item_text.strip():
                            all_entities.append({
                                "text": item_text.strip(),
                                "type": entity_type,
                                "confidence": 0.9,  # LLM assumed high confidence
                                "source": "llm"
                            })
            
            # Calculate metrics
            confidence_levels = [e["confidence"] for e in all_entities]
            avg_confidence = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0.0
            min_confidence = min(confidence_levels) if confidence_levels else 0.0
            
            return {
                "entities": all_entities,
                "total_entities": len(all_entities),
                "avg_confidence": avg_confidence,
                "min_confidence": min_confidence,
                "processing_time": processing_time,
                "low_confidence_count": sum(1 for c in confidence_levels if c < 0.6),
                "method": "llm_escalation",
                "llm_raw_output": structured_data
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "method": "llm_escalation",
                "processing_time": time.time() - start_time
            }
    
    def evaluate_accuracy(self, results: Dict[str, Any], expected: Dict[str, List[str]]) -> Dict[str, Any]:
        """Evaluate accuracy against expected entities"""
        
        entities_by_type = {}
        for entity in results.get("entities", []):
            entity_type = entity["type"]
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity["text"].lower())
        
        accuracy_metrics = {
            "precision": {},
            "recall": {},
            "f1": {},
            "total_precision": 0.0,
            "total_recall": 0.0,
            "total_f1": 0.0
        }
        
        all_precision = []
        all_recall = []
        
        for expected_type, expected_items in expected.items():
            expected_set = set(item.lower() for item in expected_items)
            found_set = set(entities_by_type.get(expected_type, []))
            
            tp = len(expected_set.intersection(found_set))
            fp = len(found_set - expected_set)
            fn = len(expected_set - found_set)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            
            accuracy_metrics["precision"][expected_type] = precision
            accuracy_metrics["recall"][expected_type] = recall
            accuracy_metrics["f1"][expected_type] = f1
            
            all_precision.append(precision)
            all_recall.append(recall)
        
        # Calculate overall metrics
        accuracy_metrics["total_precision"] = sum(all_precision) / len(all_precision) if all_precision else 0.0
        accuracy_metrics["total_recall"] = sum(all_recall) / len(all_recall) if all_recall else 0.0
        accuracy_metrics["total_f1"] = 2 * (accuracy_metrics["total_precision"] * accuracy_metrics["total_recall"]) / (accuracy_metrics["total_precision"] + accuracy_metrics["total_recall"]) if (accuracy_metrics["total_precision"] + accuracy_metrics["total_recall"]) > 0 else 0.0
        
        return accuracy_metrics

    async def run_comparison(self):
        """Run comprehensive comparison"""
        
        print("=" * 80)
        print("LLM vs Current Pipeline Medical Accuracy Comparison")
        print("=" * 80)
        
        pipeline_results = []
        llm_results = []
        
        for i, test_case in enumerate(self.test_cases, 1):
            text = test_case["text"]
            expected = test_case["expected_entities"]
            
            print(f"\n🔬 Test Case {i}: {text[:60]}...")
            print("-" * 60)
            
            # Test current pipeline
            print("Testing current transformer pipeline...")
            pipeline_result = await self.test_current_pipeline(text)
            pipeline_accuracy = self.evaluate_accuracy(pipeline_result, expected)
            pipeline_result["accuracy"] = pipeline_accuracy
            pipeline_results.append(pipeline_result)
            
            # Test LLM escalation
            print("Testing LLM escalation...")
            llm_result = await self.test_llm_escalation(text)
            llm_accuracy = self.evaluate_accuracy(llm_result, expected)
            llm_result["accuracy"] = llm_accuracy
            llm_results.append(llm_result)
            
            # Compare results for this case
            self.print_case_comparison(pipeline_result, llm_result, expected)
        
        # Print overall comparison
        print("\n" + "=" * 80)
        print("OVERALL COMPARISON RESULTS")
        print("=" * 80)
        
        self.print_overall_comparison(pipeline_results, llm_results)
        
        return {
            "pipeline_results": pipeline_results,
            "llm_results": llm_results
        }
    
    def print_case_comparison(self, pipeline_result: Dict, llm_result: Dict, expected: Dict):
        """Print comparison for individual test case"""
        
        print(f"\n📊 Current Pipeline Results:")
        if "error" in pipeline_result:
            print(f"   ❌ Error: {pipeline_result['error']}")
        else:
            print(f"   Entities Found: {pipeline_result['total_entities']}")
            print(f"   Avg Confidence: {pipeline_result['avg_confidence']:.1%}")
            print(f"   Min Confidence: {pipeline_result['min_confidence']:.1%}")
            print(f"   Low Confidence (<60%): {pipeline_result['low_confidence_count']}")
            print(f"   Processing Time: {pipeline_result['processing_time']:.3f}s")
            print(f"   Precision: {pipeline_result['accuracy']['total_precision']:.1%}")
            print(f"   Recall: {pipeline_result['accuracy']['total_recall']:.1%}")
            print(f"   F1 Score: {pipeline_result['accuracy']['total_f1']:.1%}")
        
        print(f"\n🤖 LLM Escalation Results:")
        if "error" in llm_result:
            print(f"   ❌ Error: {llm_result['error']}")
        else:
            print(f"   Entities Found: {llm_result['total_entities']}")
            print(f"   Avg Confidence: {llm_result['avg_confidence']:.1%}")
            print(f"   Min Confidence: {llm_result['min_confidence']:.1%}")
            print(f"   Low Confidence (<60%): {llm_result['low_confidence_count']}")
            print(f"   Processing Time: {llm_result['processing_time']:.3f}s")
            print(f"   Precision: {llm_result['accuracy']['total_precision']:.1%}")
            print(f"   Recall: {llm_result['accuracy']['total_recall']:.1%}")
            print(f"   F1 Score: {llm_result['accuracy']['total_f1']:.1%}")
    
    def print_overall_comparison(self, pipeline_results: List[Dict], llm_results: List[Dict]):
        """Print overall comparison metrics"""
        
        # Calculate averages for pipeline
        pipeline_valid = [r for r in pipeline_results if "error" not in r]
        pipeline_avg_confidence = sum(r["avg_confidence"] for r in pipeline_valid) / len(pipeline_valid) if pipeline_valid else 0
        pipeline_avg_f1 = sum(r["accuracy"]["total_f1"] for r in pipeline_valid) / len(pipeline_valid) if pipeline_valid else 0
        pipeline_avg_time = sum(r["processing_time"] for r in pipeline_valid) / len(pipeline_valid) if pipeline_valid else 0
        pipeline_total_low_conf = sum(r["low_confidence_count"] for r in pipeline_valid)
        
        # Calculate averages for LLM
        llm_valid = [r for r in llm_results if "error" not in r]
        llm_avg_confidence = sum(r["avg_confidence"] for r in llm_valid) / len(llm_valid) if llm_valid else 0
        llm_avg_f1 = sum(r["accuracy"]["total_f1"] for r in llm_valid) / len(llm_valid) if llm_valid else 0
        llm_avg_time = sum(r["processing_time"] for r in llm_valid) / len(llm_valid) if llm_valid else 0
        llm_total_low_conf = sum(r["low_confidence_count"] for r in llm_valid)
        
        print(f"\n📈 PERFORMANCE METRICS COMPARISON:")
        print("-" * 50)
        print(f"{'Metric':<25} {'Pipeline':<15} {'LLM':<15} {'Winner'}")
        print("-" * 50)
        pipeline_conf_str = f"{pipeline_avg_confidence:.1%}"
        llm_conf_str = f"{llm_avg_confidence:.1%}"
        pipeline_f1_str = f"{pipeline_avg_f1:.1%}"
        llm_f1_str = f"{llm_avg_f1:.1%}"
        print(f"{'Average Confidence':<25} {pipeline_conf_str:<15} {llm_conf_str:<15} {'LLM' if llm_avg_confidence > pipeline_avg_confidence else 'Pipeline'}")
        print(f"{'Average F1 Score':<25} {pipeline_f1_str:<15} {llm_f1_str:<15} {'LLM' if llm_avg_f1 > pipeline_avg_f1 else 'Pipeline'}")
        pipeline_time_str = f"{pipeline_avg_time:.3f}s"
        llm_time_str = f"{llm_avg_time:.3f}s"
        print(f"{'Average Speed':<25} {pipeline_time_str:<15} {llm_time_str:<15} {'Pipeline' if pipeline_avg_time < llm_avg_time else 'LLM'}")
        print(f"{'Low Confidence Count':<25} {pipeline_total_low_conf:<15} {llm_total_low_conf:<15} {'LLM' if llm_total_low_conf < pipeline_total_low_conf else 'Pipeline'}")
        
        print(f"\n🏥 MEDICAL SAFETY ASSESSMENT:")
        print("-" * 40)
        
        # Safety recommendations
        if pipeline_avg_confidence >= 0.7 and pipeline_total_low_conf <= 2:
            pipeline_safety = "SAFE"
        elif pipeline_avg_confidence >= 0.6 and pipeline_total_low_conf <= 5:
            pipeline_safety = "MODERATE"
        else:
            pipeline_safety = "RISKY"
        
        if llm_avg_confidence >= 0.7 and llm_total_low_conf <= 2:
            llm_safety = "SAFE"
        elif llm_avg_confidence >= 0.6 and llm_total_low_conf <= 5:
            llm_safety = "MODERATE"
        else:
            llm_safety = "RISKY"
        
        print(f"Current Pipeline Safety: {pipeline_safety}")
        print(f"LLM Escalation Safety: {llm_safety}")
        
        # Final recommendation
        print(f"\n🎯 RECOMMENDATION:")
        if llm_avg_f1 > pipeline_avg_f1 and llm_safety in ["SAFE", "MODERATE"]:
            print("✅ RECOMMEND LLM ESCALATION for better medical accuracy and safety")
        elif pipeline_safety == "SAFE" and llm_safety == "RISKY":
            print("✅ KEEP CURRENT PIPELINE - safer confidence levels")
        elif llm_total_low_conf < pipeline_total_low_conf:
            print("⚠️  CONSIDER LLM ESCALATION - fewer low confidence extractions")
        else:
            print("🔄 HYBRID APPROACH - Use LLM escalation for low-confidence cases")
        
        print(f"\nConfidence Threshold Analysis:")
        print(f"- Medications should require ≥60% confidence (high risk)")
        print(f"- Diagnostic procedures can accept ≥40% confidence (moderate risk)")
        print(f"- Current pipeline low confidence count: {pipeline_total_low_conf}")
        print(f"- LLM escalation low confidence count: {llm_total_low_conf}")
        
        if pipeline_total_low_conf > 5:
            print(f"⚠️  WARNING: Current pipeline has {pipeline_total_low_conf} low confidence extractions")
            print("   Consider implementing LLM escalation for entities below confidence thresholds")

async def main():
    comparison = AccuracyComparison()
    await comparison.run_comparison()

if __name__ == "__main__":
    asyncio.run(main())