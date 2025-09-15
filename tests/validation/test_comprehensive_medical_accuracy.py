#!/usr/bin/env python3
"""
Comprehensive Medical Accuracy Test: LLM vs Pipeline
20 test cases across all medical specialties for production-ready evaluation
"""

import asyncio
import time
import json
import sys
import os
import random
from typing import Dict, List, Any, Optional

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from nl_fhir.services.nlp.models import extract_medical_entities
from nl_fhir.services.nlp.llm_processor import LLMProcessor

class ComprehensiveMedicalAccuracyTest:
    def __init__(self):
        self.llm_processor = LLMProcessor()
        
        # 20 diverse test cases across all specialties from sample notes
        self.test_cases = [
            # General Medicine (3 cases)
            {
                "text": "Start patient John Doe on 50mg of Prozac once daily",
                "specialty": "General Medicine",
                "expected": {
                    "medications": ["Prozac"],
                    "dosages": ["50mg"], 
                    "frequencies": ["once daily"]
                }
            },
            {
                "text": "Initiate patient Mark Smith on 10mg of Lisinopril once daily for hypertension management",
                "specialty": "General Medicine",
                "expected": {
                    "medications": ["Lisinopril"],
                    "dosages": ["10mg"],
                    "frequencies": ["once daily"],
                    "conditions": ["hypertension"]
                }
            },
            {
                "text": "Prescribe patient Emily Johnson 75mg of Clopidogrel once daily following stent placement",
                "specialty": "General Medicine", 
                "expected": {
                    "medications": ["Clopidogrel"],
                    "dosages": ["75mg"],
                    "frequencies": ["once daily"],
                    "procedures": ["stent placement"]
                }
            },
            
            # Pediatrics (2 cases)
            {
                "text": "Started patient Noah Kim on 250mg Cefdinir once daily for otitis media; advised parents on red stool discoloration",
                "specialty": "Pediatrics",
                "expected": {
                    "medications": ["Cefdinir"],
                    "dosages": ["250mg"],
                    "frequencies": ["once daily"],
                    "conditions": ["otitis media"]
                }
            },
            {
                "text": "Administered patient Ava Patel 0.5mL of MMR vaccine subcutaneously in right arm; documented immunization record",
                "specialty": "Pediatrics",
                "expected": {
                    "medications": ["MMR vaccine"],
                    "dosages": ["0.5mL"],
                    "routes": ["subcutaneous"]
                }
            },
            
            # Geriatrics (2 cases)
            {
                "text": "Started patient Margaret Hill on 10mg Donepezil once daily for mild Alzheimer's disease; discussed GI side effects",
                "specialty": "Geriatrics",
                "expected": {
                    "medications": ["Donepezil"],
                    "dosages": ["10mg"],
                    "frequencies": ["once daily"],
                    "conditions": ["Alzheimer's disease"]
                }
            },
            {
                "text": "Prescribed patient George Allen 25mg Hydrochlorothiazide once daily for hypertension; monitored electrolytes",
                "specialty": "Geriatrics",
                "expected": {
                    "medications": ["Hydrochlorothiazide"],
                    "dosages": ["25mg"],
                    "frequencies": ["once daily"],
                    "conditions": ["hypertension"]
                }
            },
            
            # Psychiatry (2 cases)
            {
                "text": "Started patient Alex Morgan on 20mg Fluoxetine once daily for major depressive disorder; follow-up in 4 weeks",
                "specialty": "Psychiatry",
                "expected": {
                    "medications": ["Fluoxetine"],
                    "dosages": ["20mg"],
                    "frequencies": ["once daily"],
                    "conditions": ["major depressive disorder"]
                }
            },
            {
                "text": "Initiated patient Jordan Lee on 0.5mg Clonazepam twice daily for panic disorder; discussed dependency risks",
                "specialty": "Psychiatry",
                "expected": {
                    "medications": ["Clonazepam"],
                    "dosages": ["0.5mg"],
                    "frequencies": ["twice daily"],
                    "conditions": ["panic disorder"]
                }
            },
            
            # Emergency Medicine (2 cases)  
            {
                "text": "Administered patient Ava Thompson 4mg Ondansetron IV for acute nausea and vomiting; reassessed in 30 minutes",
                "specialty": "Emergency Medicine",
                "expected": {
                    "medications": ["Ondansetron"],
                    "dosages": ["4mg"],
                    "routes": ["IV"],
                    "conditions": ["nausea", "vomiting"]
                }
            },
            {
                "text": "Started patient Liam Brooks on 1g Ceftriaxone IV for suspected sepsis; blood cultures drawn",
                "specialty": "Emergency Medicine",
                "expected": {
                    "medications": ["Ceftriaxone"],
                    "dosages": ["1g"],
                    "routes": ["IV"],
                    "conditions": ["sepsis"],
                    "lab_tests": ["blood cultures"]
                }
            },
            
            # Cardiology (2 cases)
            {
                "text": "Started patient Daniel Moore on 10mg Atorvastatin nightly for LDL reduction; lipid panel in 6 weeks",
                "specialty": "Cardiology",
                "expected": {
                    "medications": ["Atorvastatin"],
                    "dosages": ["10mg"],
                    "frequencies": ["nightly"],
                    "lab_tests": ["lipid panel"]
                }
            },
            {
                "text": "Prescribed patient Ava Robinson 25mg Metoprolol twice daily for rate control in atrial fibrillation",
                "specialty": "Cardiology",
                "expected": {
                    "medications": ["Metoprolol"],
                    "dosages": ["25mg"],
                    "frequencies": ["twice daily"],
                    "conditions": ["atrial fibrillation"]
                }
            },
            
            # Dermatology (1 case)
            {
                "text": "Prescribed patient Ava Brooks 0.1% Tretinoin cream nightly for acne; advised on gradual titration and sun sensitivity",
                "specialty": "Dermatology",
                "expected": {
                    "medications": ["Tretinoin"],
                    "dosages": ["0.1%"],
                    "frequencies": ["nightly"],
                    "conditions": ["acne"],
                    "routes": ["topical"]
                }
            },
            
            # Endocrinology (1 case)
            {
                "text": "Started patient Ava Thompson on 10mg Methimazole twice daily for hyperthyroidism; TSH and free T4 to be rechecked in 4 weeks",
                "specialty": "Endocrinology",
                "expected": {
                    "medications": ["Methimazole"],
                    "dosages": ["10mg"],
                    "frequencies": ["twice daily"],
                    "conditions": ["hyperthyroidism"],
                    "lab_tests": ["TSH", "free T4"]
                }
            },
            
            # Infectious Disease (1 case)
            {
                "text": "Started patient Ava Thompson on 600mg Linezolid twice daily for MRSA pneumonia; CBC monitored",
                "specialty": "Infectious Disease",
                "expected": {
                    "medications": ["Linezolid"],
                    "dosages": ["600mg"],
                    "frequencies": ["twice daily"],
                    "conditions": ["MRSA pneumonia"],
                    "lab_tests": ["CBC"]
                }
            },
            
            # Oncology (1 case)
            {
                "text": "Started patient Ava Thompson on 500mg Capecitabine orally twice daily for metastatic breast cancer; hand-foot syndrome discussed",
                "specialty": "Oncology",
                "expected": {
                    "medications": ["Capecitabine"],
                    "dosages": ["500mg"],
                    "frequencies": ["twice daily"],
                    "routes": ["oral"],
                    "conditions": ["metastatic breast cancer"]
                }
            },
            
            # Pain Management (1 case)  
            {
                "text": "Started patient Ava Thompson on 25mcg Fentanyl patch every 72 hours for chronic cancer pain; breakthrough meds available",
                "specialty": "Pain Management",
                "expected": {
                    "medications": ["Fentanyl"],
                    "dosages": ["25mcg"],
                    "frequencies": ["every 72 hours"],
                    "routes": ["patch"],
                    "conditions": ["chronic cancer pain"]
                }
            },
            
            # Gastroenterology (1 case)
            {
                "text": "Started patient Ava Thompson on 40mg Pantoprazole daily for erosive esophagitis; endoscopy scheduled in 6 weeks",
                "specialty": "Gastroenterology",
                "expected": {
                    "medications": ["Pantoprazole"],
                    "dosages": ["40mg"],
                    "frequencies": ["daily"],
                    "conditions": ["erosive esophagitis"],
                    "procedures": ["endoscopy"]
                }
            },
            
            # Pulmonology (1 case)
            {
                "text": "Started patient Ava Thompson on 250mcg Fluticasone inhaler twice daily for persistent asthma; spacer technique reviewed",
                "specialty": "Pulmonology",
                "expected": {
                    "medications": ["Fluticasone"],
                    "dosages": ["250mcg"],
                    "frequencies": ["twice daily"],
                    "routes": ["inhaler"],
                    "conditions": ["persistent asthma"]
                }
            },
            
            # Hematology (1 case) - Using the one from our earlier test
            {
                "text": "Prescribed patient Liam Brooks 100mg Hydroxyurea daily for sickle cell disease; CBC tracked",
                "specialty": "Hematology", 
                "expected": {
                    "medications": ["Hydroxyurea"],
                    "dosages": ["100mg"],
                    "frequencies": ["daily"],
                    "conditions": ["sickle cell disease"],
                    "lab_tests": ["CBC"]
                }
            }
        ]
    
    async def run_comprehensive_test(self):
        """Run comprehensive 20-case medical accuracy comparison"""
        
        print("=" * 90)
        print("🏥 COMPREHENSIVE MEDICAL ACCURACY TEST: LLM vs PIPELINE")
        print("=" * 90)
        print(f"Testing {len(self.test_cases)} cases across {len(set(case['specialty'] for case in self.test_cases))} medical specialties")
        print("Using gpt-4o-mini with temperature=0.0 for maximum medical accuracy")
        print("-" * 90)
        
        # Initialize results tracking
        pipeline_results = []
        llm_results = []
        cost_tracking = {"llm_calls": 0, "total_tokens": 0}
        specialty_results = {}
        
        # Process each test case
        for i, test_case in enumerate(self.test_cases, 1):
            text = test_case["text"]
            specialty = test_case["specialty"]
            expected = test_case["expected"]
            
            print(f"\n🔬 Test {i:2d}/20 [{specialty}]: {text[:60]}...")
            print("-" * 80)
            
            # Test current pipeline
            pipeline_start = time.time()
            pipeline_result = await self._test_pipeline(text, expected, f"test-{i}")
            pipeline_time = time.time() - pipeline_start
            pipeline_result["processing_time"] = pipeline_time
            pipeline_result["specialty"] = specialty
            pipeline_results.append(pipeline_result)
            
            # Test LLM escalation  
            llm_start = time.time()
            llm_result = await self._test_llm(text, expected, f"test-{i}")
            llm_time = time.time() - llm_start
            llm_result["processing_time"] = llm_time
            llm_result["specialty"] = specialty
            llm_results.append(llm_result)
            
            # Track LLM usage for cost calculation
            if llm_result.get("method") == "escalated_to_llm":
                cost_tracking["llm_calls"] += 1
                cost_tracking["total_tokens"] += 1500  # Estimate
            
            # Track by specialty
            if specialty not in specialty_results:
                specialty_results[specialty] = {"pipeline": [], "llm": []}
            specialty_results[specialty]["pipeline"].append(pipeline_result)
            specialty_results[specialty]["llm"].append(llm_result)
            
            # Print case comparison
            self._print_case_results(i, pipeline_result, llm_result, expected)
        
        # Print comprehensive analysis
        print("\n" + "=" * 90)
        print("📊 COMPREHENSIVE ANALYSIS RESULTS")
        print("=" * 90)
        
        await self._print_overall_analysis(pipeline_results, llm_results, cost_tracking)
        await self._print_specialty_analysis(specialty_results)
        await self._print_medical_safety_assessment(pipeline_results, llm_results)
        await self._print_production_recommendations(pipeline_results, llm_results, cost_tracking)
        
        return {
            "pipeline_results": pipeline_results,
            "llm_results": llm_results,
            "cost_tracking": cost_tracking,
            "specialty_breakdown": specialty_results
        }
    
    async def _test_pipeline(self, text: str, expected: Dict, request_id: str) -> Dict[str, Any]:
        """Test current transformer pipeline"""
        try:
            results = extract_medical_entities(text)
            
            # Convert to standardized format
            entities = []
            confidence_scores = []
            
            for category, entity_list in results.items():
                for entity in entity_list:
                    entities.append({
                        "category": category,
                        "text": entity.get("text", ""),
                        "confidence": entity.get("confidence", 0.0)
                    })
                    confidence_scores.append(entity.get("confidence", 0.0))
            
            # Calculate accuracy
            accuracy_metrics = self._calculate_accuracy(entities, expected)
            
            return {
                "method": "transformer_pipeline",
                "entities": entities,
                "total_entities": len(entities),
                "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
                "min_confidence": min(confidence_scores) if confidence_scores else 0.0,
                "low_confidence_count": sum(1 for c in confidence_scores if c < 0.6),
                **accuracy_metrics,
                "error": None
            }
        except Exception as e:
            return {
                "method": "transformer_pipeline",
                "entities": [],
                "total_entities": 0,
                "avg_confidence": 0.0,
                "min_confidence": 0.0,
                "low_confidence_count": 0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "error": str(e)
            }
    
    async def _test_llm(self, text: str, expected: Dict, request_id: str) -> Dict[str, Any]:
        """Test LLM escalation approach"""
        try:
            # Initialize LLM processor if needed
            if not self.llm_processor.initialized:
                self.llm_processor.initialize()
            
            # Process with LLM
            llm_results = self.llm_processor.process_clinical_text(text, [], request_id)
            structured_output = llm_results.get("structured_output", {})
            method = llm_results.get("method", "unknown")
            
            # CORRECTED: Convert structured output to standardized format with embedded data extraction
            entities = []
            confidence_scores = []
            
            # Extract medications AND their embedded dosage/frequency data
            for med in structured_output.get("medications", []):
                if isinstance(med, dict):
                    # Add the medication name
                    med_name = med.get("name", "")
                    if med_name:
                        entities.append({
                            "category": "medications", 
                            "text": med_name,
                            "confidence": 0.9,
                            "source": "llm"
                        })
                        confidence_scores.append(0.9)
                    
                    # CORRECTED: Extract embedded dosage
                    dosage = med.get("dosage", "")
                    if dosage:
                        entities.append({
                            "category": "dosages",
                            "text": str(dosage),
                            "confidence": 0.9,
                            "source": "llm_embedded"
                        })
                        confidence_scores.append(0.9)
                    
                    # CORRECTED: Extract embedded frequency
                    frequency = med.get("frequency", "")
                    if frequency:
                        entities.append({
                            "category": "frequencies",
                            "text": str(frequency),
                            "confidence": 0.9,
                            "source": "llm_embedded"
                        })
                        confidence_scores.append(0.9)
            
            # Extract lab tests
            for lab in structured_output.get("lab_tests", []):
                if isinstance(lab, dict):
                    entities.append({
                        "category": "lab_tests",
                        "text": lab.get("name", ""),
                        "confidence": 0.9
                    })
                    confidence_scores.append(0.9)
            
            # Extract conditions
            for condition in structured_output.get("conditions", []):
                if isinstance(condition, dict):
                    entities.append({
                        "category": "conditions",
                        "text": condition.get("name", ""),
                        "confidence": 0.9
                    })
                    confidence_scores.append(0.9)
            
            # Extract procedures  
            for proc in structured_output.get("procedures", []):
                if isinstance(proc, dict):
                    entities.append({
                        "category": "procedures",
                        "text": proc.get("name", ""),
                        "confidence": 0.9
                    })
                    confidence_scores.append(0.9)
            
            # Calculate accuracy
            accuracy_metrics = self._calculate_accuracy(entities, expected)
            
            return {
                "method": method,
                "entities": entities,
                "total_entities": len(entities),
                "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
                "min_confidence": min(confidence_scores) if confidence_scores else 0.0,
                "low_confidence_count": sum(1 for c in confidence_scores if c < 0.6),
                **accuracy_metrics,
                "llm_raw_output": structured_output,
                "error": None
            }
        except Exception as e:
            return {
                "method": "llm_failed",
                "entities": [],
                "total_entities": 0,
                "avg_confidence": 0.0,
                "min_confidence": 0.0,
                "low_confidence_count": 0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "error": str(e)
            }
    
    def _calculate_accuracy(self, entities: List[Dict], expected: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate precision, recall, and F1 score"""
        
        # Group entities by category
        found_by_category = {}
        for entity in entities:
            category = entity["category"]
            text = entity["text"].lower().strip()
            
            if category not in found_by_category:
                found_by_category[category] = []
            found_by_category[category].append(text)
        
        # Calculate metrics per category
        all_precision = []
        all_recall = []
        total_expected = 0
        total_correct = 0
        
        for exp_category, exp_items in expected.items():
            total_expected += len(exp_items)
            
            # Handle category name variations (medications vs medication, etc.)
            possible_categories = [exp_category, exp_category.rstrip('s'), exp_category + 's']
            found_items = []
            
            for cat in possible_categories:
                if cat in found_by_category:
                    found_items.extend(found_by_category[cat])
            
            # Find matches
            correct_matches = 0
            for exp_item in exp_items:
                exp_lower = exp_item.lower().strip()
                for found_item in found_items:
                    if exp_lower in found_item or found_item in exp_lower:
                        correct_matches += 1
                        total_correct += 1
                        break
            
            # Calculate category metrics
            category_precision = correct_matches / len(found_items) if found_items else 0.0
            category_recall = correct_matches / len(exp_items) if exp_items else 0.0
            
            all_precision.append(category_precision)
            all_recall.append(category_recall)
        
        # Overall metrics
        overall_precision = sum(all_precision) / len(all_precision) if all_precision else 0.0
        overall_recall = sum(all_recall) / len(all_recall) if all_recall else 0.0
        f1_score = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0
        
        return {
            "precision": overall_precision,
            "recall": overall_recall, 
            "f1_score": f1_score,
            "correct_entities": total_correct,
            "expected_entities": total_expected
        }
    
    def _print_case_results(self, case_num: int, pipeline_result: Dict, llm_result: Dict, expected: Dict):
        """Print results for individual test case"""
        
        print(f"Pipeline: {pipeline_result['correct_entities']}/{pipeline_result['expected_entities']} correct "
              f"({pipeline_result['f1_score']:.1%} F1, {pipeline_result['avg_confidence']:.1%} conf, "
              f"{pipeline_result['processing_time']:.3f}s)")
        
        print(f"LLM:      {llm_result['correct_entities']}/{llm_result['expected_entities']} correct "
              f"({llm_result['f1_score']:.1%} F1, {llm_result['avg_confidence']:.1%} conf, "
              f"{llm_result['processing_time']:.3f}s)")
        
        # Show winner
        if llm_result['f1_score'] > pipeline_result['f1_score']:
            print(f"✅ LLM WINS (+{llm_result['f1_score'] - pipeline_result['f1_score']:.1%} F1)")
        elif pipeline_result['f1_score'] > llm_result['f1_score']:
            print(f"✅ PIPELINE WINS (+{pipeline_result['f1_score'] - llm_result['f1_score']:.1%} F1)")  
        else:
            print(f"🤝 TIE")
    
    async def _print_overall_analysis(self, pipeline_results: List[Dict], llm_results: List[Dict], cost_tracking: Dict):
        """Print overall comparison analysis"""
        
        # Calculate averages
        pipeline_avg_f1 = sum(r['f1_score'] for r in pipeline_results) / len(pipeline_results)
        pipeline_avg_conf = sum(r['avg_confidence'] for r in pipeline_results) / len(pipeline_results)
        pipeline_avg_time = sum(r['processing_time'] for r in pipeline_results) / len(pipeline_results)
        pipeline_low_conf = sum(r['low_confidence_count'] for r in pipeline_results)
        
        llm_avg_f1 = sum(r['f1_score'] for r in llm_results) / len(llm_results)
        llm_avg_conf = sum(r['avg_confidence'] for r in llm_results) / len(llm_results)
        llm_avg_time = sum(r['processing_time'] for r in llm_results) / len(llm_results)
        llm_low_conf = sum(r['low_confidence_count'] for r in llm_results)
        
        print(f"\n📈 OVERALL PERFORMANCE COMPARISON:")
        print("-" * 60)
        print(f"{'Metric':<25} {'Pipeline':<15} {'LLM':<15} {'Winner'}")
        print("-" * 60)
        pipeline_f1_str = f"{pipeline_avg_f1:.1%}"
        llm_f1_str = f"{llm_avg_f1:.1%}"
        pipeline_conf_str = f"{pipeline_avg_conf:.1%}"
        llm_conf_str = f"{llm_avg_conf:.1%}"
        print(f"{'Average F1 Score':<25} {pipeline_f1_str:<15} {llm_f1_str:<15} {'LLM' if llm_avg_f1 > pipeline_avg_f1 else 'Pipeline'}")
        print(f"{'Average Confidence':<25} {pipeline_conf_str:<15} {llm_conf_str:<15} {'LLM' if llm_avg_conf > pipeline_avg_conf else 'Pipeline'}")
        pipeline_time_str = f"{pipeline_avg_time:.3f}s"
        llm_time_str = f"{llm_avg_time:.3f}s"
        print(f"{'Average Speed':<25} {pipeline_time_str:<15} {llm_time_str:<15} {'Pipeline' if pipeline_avg_time < llm_avg_time else 'LLM'}")
        print(f"{'Low Confidence (<60%)':<25} {pipeline_low_conf:<15} {llm_low_conf:<15} {'LLM' if llm_low_conf < pipeline_low_conf else 'Pipeline'}")
        
        # Cost analysis
        estimated_cost = cost_tracking["llm_calls"] * 0.002  # Rough estimate
        print(f"\n💰 COST ANALYSIS:")
        print(f"LLM Calls Made: {cost_tracking['llm_calls']}/20")
        print(f"Estimated Cost: ${estimated_cost:.4f}")
        print(f"Cost per Accurate Entity: ${estimated_cost / sum(r['correct_entities'] for r in llm_results) if sum(r['correct_entities'] for r in llm_results) > 0 else 0:.4f}")
    
    async def _print_specialty_analysis(self, specialty_results: Dict):
        """Print analysis by medical specialty"""
        
        print(f"\n🏥 MEDICAL SPECIALTY BREAKDOWN:")
        print("-" * 80)
        
        for specialty, results in specialty_results.items():
            pipeline_avg_f1 = sum(r['f1_score'] for r in results["pipeline"]) / len(results["pipeline"])
            llm_avg_f1 = sum(r['f1_score'] for r in results["llm"]) / len(results["llm"])
            
            winner = "LLM" if llm_avg_f1 > pipeline_avg_f1 else "Pipeline"
            advantage = abs(llm_avg_f1 - pipeline_avg_f1)
            
            print(f"{specialty:<25} Pipeline: {pipeline_avg_f1:.1%}  LLM: {llm_avg_f1:.1%}  Winner: {winner} (+{advantage:.1%})")
    
    async def _print_medical_safety_assessment(self, pipeline_results: List[Dict], llm_results: List[Dict]):
        """Print medical safety assessment"""
        
        print(f"\n🚨 MEDICAL SAFETY ASSESSMENT:")
        print("-" * 50)
        
        # Count dangerous scenarios (low confidence in medical entities)
        pipeline_risky = sum(1 for r in pipeline_results if r['avg_confidence'] < 0.7 and r['total_entities'] > 0)
        llm_risky = sum(1 for r in llm_results if r['avg_confidence'] < 0.7 and r['total_entities'] > 0)
        
        # Count complete failures (no entities found)
        pipeline_failures = sum(1 for r in pipeline_results if r['total_entities'] == 0)
        llm_failures = sum(1 for r in llm_results if r['total_entities'] == 0)
        
        print(f"Low Confidence Cases (<70%): Pipeline {pipeline_risky}/20, LLM {llm_risky}/20")
        print(f"Complete Extraction Failures: Pipeline {pipeline_failures}/20, LLM {llm_failures}/20")
        
        # Overall safety rating
        pipeline_safety = "SAFE" if pipeline_risky <= 2 and pipeline_failures <= 1 else "RISKY" 
        llm_safety = "SAFE" if llm_risky <= 2 and llm_failures <= 1 else "RISKY"
        
        print(f"\nSAFETY RATING:")
        print(f"Pipeline: {pipeline_safety}")
        print(f"LLM: {llm_safety}")
    
    async def _print_production_recommendations(self, pipeline_results: List[Dict], llm_results: List[Dict], cost_tracking: Dict):
        """Print production deployment recommendations"""
        
        print(f"\n🎯 PRODUCTION RECOMMENDATIONS:")
        print("-" * 50)
        
        # Calculate key metrics for decision
        llm_avg_f1 = sum(r['f1_score'] for r in llm_results) / len(llm_results)
        pipeline_avg_f1 = sum(r['f1_score'] for r in pipeline_results) / len(pipeline_results)
        
        llm_better_cases = sum(1 for i, _ in enumerate(llm_results) if llm_results[i]['f1_score'] > pipeline_results[i]['f1_score'])
        
        cost_per_case = (cost_tracking["llm_calls"] * 0.002) / 20
        
        print(f"LLM Superior Performance: {llm_better_cases}/20 cases ({llm_better_cases/20:.1%})")
        print(f"Average Accuracy Improvement: +{llm_avg_f1 - pipeline_avg_f1:.1%} F1 Score")
        print(f"Cost per Case: ${cost_per_case:.4f}")
        
        # Make recommendation
        if llm_avg_f1 > pipeline_avg_f1 + 0.1 and llm_better_cases >= 12:
            print(f"\n✅ RECOMMENDATION: IMPLEMENT LLM ESCALATION")
            print(f"   - Significant accuracy improvement ({llm_avg_f1 - pipeline_avg_f1:.1%})")
            print(f"   - Cost-effective for medical accuracy gains")
            print(f"   - Use for cases where pipeline confidence < 70%")
        elif llm_avg_f1 > pipeline_avg_f1:
            print(f"\n⚠️  RECOMMENDATION: SELECTIVE LLM ESCALATION")
            print(f"   - Modest improvement, use for critical cases only")
            print(f"   - Trigger LLM for pipeline confidence < 60%")
        else:
            print(f"\n❌ RECOMMENDATION: KEEP CURRENT PIPELINE")
            print(f"   - LLM does not provide sufficient accuracy improvement")
            print(f"   - Focus on improving pipeline rather than LLM escalation")

async def main():
    """Run comprehensive medical accuracy test"""
    test = ComprehensiveMedicalAccuracyTest()
    results = await test.run_comprehensive_test()
    
    # Save results for further analysis
    with open("comprehensive_medical_accuracy_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Results saved to: comprehensive_medical_accuracy_results.json")

if __name__ == "__main__":
    asyncio.run(main())