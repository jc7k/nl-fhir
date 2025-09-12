#!/usr/bin/env python3
"""
Batch Clinical Test Case Processor
Efficiently processes multiple clinical notes (20+ at a time) through our 3-tier NLP architecture
"""

import sys
sys.path.append('../../src')
sys.path.append('tests/framework')

import asyncio
import json
import time
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

from qa_framework import (
    ClinicalTestCase, 
    ClinicalTestRunner, 
    TestReportGenerator,
    ClinicalTestLoader
)

class BatchClinicalProcessor:
    """Process multiple clinical notes efficiently with comprehensive analysis"""
    
    def __init__(self):
        self.test_runner = ClinicalTestRunner()
        self.report_generator = TestReportGenerator()
        self.test_loader = ClinicalTestLoader()
        
    def create_test_cases_from_clinical_notes(
        self, 
        clinical_notes: List[str],
        batch_name: str = "batch",
        base_expectations: Dict[str, Any] = None
    ) -> List[ClinicalTestCase]:
        """Convert raw clinical notes into structured test cases"""
        
        if base_expectations is None:
            base_expectations = {
                "performance_limit_ms": 2000,  # <2s requirement
                "min_quality_score": 0.5,     # Reasonable baseline
                "expected_tier": "any"        # Let system decide
            }
        
        test_cases = []
        
        for i, note in enumerate(clinical_notes, 1):
            # Auto-detect likely medical scenario based on content
            scenario_type = self._detect_scenario_type(note)
            expected_entities = self._predict_expected_entities(note)
            
            test_case = ClinicalTestCase(
                name=f"{batch_name}_case_{i:03d}_{scenario_type}",
                clinical_text=note.strip(),
                expected_entities=expected_entities,
                expected_fhir_resources=self._predict_fhir_resources(expected_entities),
                performance_expectations=base_expectations.copy(),
                medical_scenario=scenario_type
            )
            
            test_cases.append(test_case)
            
        return test_cases
    
    def _detect_scenario_type(self, clinical_text: str) -> str:
        """Auto-detect medical scenario type from clinical text"""
        
        text_lower = clinical_text.lower()
        
        # Medication patterns
        if any(word in text_lower for word in ["prescribe", "medication", "mg", "daily", "tablet", "initiat"]):
            if any(word in text_lower for word in ["discontinue", "stop", "cease"]):
                return "medication_discontinuation"
            else:
                return "medication_order"
        
        # Lab/diagnostic patterns
        elif any(word in text_lower for word in ["order", "lab", "test", "cbc", "panel", "check"]):
            return "lab_order"
        
        # Procedure patterns
        elif any(word in text_lower for word in ["procedure", "surgery", "biopsy", "scan", "x-ray"]):
            return "procedure_order"
        
        # Follow-up patterns
        elif any(word in text_lower for word in ["follow", "appointment", "visit", "schedule"]):
            return "follow_up"
        
        # Complex clinical language
        elif any(word in text_lower for word in ["presents with", "complains", "reports", "history"]):
            return "clinical_assessment"
        
        # Default
        else:
            return "general_clinical"
    
    def _predict_expected_entities(self, clinical_text: str) -> Dict[str, List[str]]:
        """Predict what entities should be found in the clinical text"""
        
        text_lower = clinical_text.lower()
        entities = {
            "medications": [],
            "dosages": [],
            "frequencies": [],
            "conditions": [],
            "procedures": [],
            "lab_tests": []
        }
        
        # Common medication names (expand based on your data)
        med_terms = [
            "tadalafil", "lisinopril", "metformin", "aspirin", "warfarin",
            "atorvastatin", "amlodipine", "omeprazole", "losartan", "gabapentin",
            "levothyroxine", "simvastatin", "amlodipine", "hydrochlorothiazide"
        ]
        
        for med in med_terms:
            if med in text_lower:
                entities["medications"].append(med)
        
        # Dosage patterns
        import re
        dosage_pattern = re.compile(r'\d+\s*(?:mg|gram|tablet|capsule|ml|mcg|iu)', re.IGNORECASE)
        dosages = dosage_pattern.findall(clinical_text)
        entities["dosages"] = list(set(dosages))
        
        # Frequency patterns  
        freq_terms = ["daily", "twice daily", "three times", "as needed", "prn", "bid", "tid"]
        for freq in freq_terms:
            if freq in text_lower:
                entities["frequencies"].append(freq)
        
        # Common conditions
        condition_terms = [
            "hypertension", "diabetes", "dysfunction", "pain", "bleeding",
            "heart failure", "depression", "anxiety", "copd", "seizures"
        ]
        
        for condition in condition_terms:
            if condition in text_lower:
                entities["conditions"].append(condition)
        
        return entities
    
    def _predict_fhir_resources(self, expected_entities: Dict[str, List[str]]) -> List[str]:
        """Predict FHIR resources that should be generated"""
        
        resources = []
        
        if expected_entities.get("medications"):
            resources.append("MedicationRequest")
        
        if expected_entities.get("conditions"):
            resources.append("Condition")
            
        if expected_entities.get("procedures") or expected_entities.get("lab_tests"):
            resources.append("DiagnosticReport")
            resources.append("Observation")
        
        # Always expect a Patient resource if we're creating clinical records
        if any(expected_entities.values()):
            resources.append("Patient")
        
        return list(set(resources))
    
    async def process_batch(
        self, 
        clinical_notes: List[str],
        batch_name: str = None,
        save_results: bool = True
    ) -> Dict[str, Any]:
        """Process a batch of clinical notes and return comprehensive results"""
        
        if batch_name is None:
            batch_name = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"🏥 Processing Clinical Batch: {batch_name}")
        print(f"📝 Notes in batch: {len(clinical_notes)}")
        print("="*60)
        
        # Create test cases
        print("1. Creating structured test cases...")
        test_cases = self.create_test_cases_from_clinical_notes(clinical_notes, batch_name)
        
        # Run tests
        print("2. Running 3-tier NLP analysis...")
        batch_start_time = time.time()
        results = await self.test_runner.run_test_suite(test_cases)
        batch_processing_time = (time.time() - batch_start_time) * 1000
        
        # Analyze results
        print("3. Analyzing batch results...")
        analysis = self._analyze_batch_results(results, batch_processing_time)
        
        # Generate reports
        if save_results:
            print("4. Generating reports...")
            self._save_batch_results(batch_name, test_cases, results, analysis)
        
        return {
            'batch_name': batch_name,
            'test_cases': test_cases,
            'results': results,
            'analysis': analysis,
            'batch_processing_time_ms': batch_processing_time
        }
    
    def _analyze_batch_results(self, results: List[Dict], batch_time: float) -> Dict[str, Any]:
        """Comprehensive analysis of batch results"""
        
        total_tests = len(results)
        successful_tests = [r for r in results if r.get('success', False)]
        failed_tests = [r for r in results if not r.get('success', False)]
        
        # Performance analysis
        processing_times = [r['processing_time_ms'] for r in results if 'processing_time_ms' in r]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Quality analysis
        quality_scores = [r.get('quality_score', 0) for r in successful_tests]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Tier usage analysis
        tier_usage = {}
        for result in results:
            tier = result.get('tier_used', 'unknown')
            tier_usage[tier] = tier_usage.get(tier, 0) + 1
        
        # Performance compliance
        under_2s = sum(1 for t in processing_times if t <= 2000)
        performance_compliance = under_2s / len(processing_times) if processing_times else 0
        
        # Quality compliance  
        high_quality = sum(1 for q in quality_scores if q >= 0.8)
        quality_compliance = high_quality / len(quality_scores) if quality_scores else 0
        
        return {
            'total_tests': total_tests,
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'success_rate': len(successful_tests) / total_tests if total_tests > 0 else 0,
            'avg_processing_time_ms': avg_processing_time,
            'avg_quality_score': avg_quality,
            'tier_usage': tier_usage,
            'performance_compliance': performance_compliance,
            'quality_compliance': quality_compliance,
            'batch_processing_time_ms': batch_time,
            'throughput_notes_per_second': total_tests / (batch_time / 1000) if batch_time > 0 else 0
        }
    
    def _save_batch_results(
        self, 
        batch_name: str, 
        test_cases: List[ClinicalTestCase],
        results: List[Dict],
        analysis: Dict[str, Any]
    ):
        """Save batch results and generate reports"""
        
        # Create batch directory
        batch_dir = Path(f"tests/results/{batch_name}")
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        # Save test cases
        test_cases_data = [case.to_dict() for case in test_cases]
        with open(batch_dir / "test_cases.json", 'w') as f:
            json.dump(test_cases_data, f, indent=2)
        
        # Save results
        with open(batch_dir / "results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save analysis
        with open(batch_dir / "analysis.json", 'w') as f:
            json.dump(analysis, f, indent=2)
        
        # Generate HTML report
        html_file = batch_dir / "batch_report.html"
        self.report_generator.generate_batch_html_report(
            batch_name, test_cases, results, analysis, str(html_file)
        )
        
        print(f"📊 Batch results saved to: {batch_dir}")
        print(f"📈 HTML report: {html_file}")

def create_sample_batch():
    """Create a sample batch for demonstration"""
    sample_notes = [
        "Initiated patient Julian West on 5mg Tadalafil as needed for erectile dysfunction",
        "Prescribed Lisinopril 10mg daily for hypertension", 
        "Order CBC and comprehensive metabolic panel, check troponins",
        "Start patient on Metformin 500mg twice daily for diabetes",
        "Discontinue aspirin due to GI bleeding, continue warfarin",
        "Patient reports chest pain, order EKG and cardiac enzymes",
        "Schedule follow-up appointment in 2 weeks for blood pressure check",
        "Continue current medications, patient tolerated well",
        "Patient needs something for the chronic condition we discussed",
        "Increase Atorvastatin to 40mg daily, recheck lipids in 3 months"
    ]
    
    return sample_notes

async def main():
    """Demonstrate batch processing"""
    
    print("🏥 Batch Clinical Note Processor - Demonstration")
    print("="*60)
    
    # Create processor
    processor = BatchClinicalProcessor()
    
    # Use sample notes for demo
    sample_notes = create_sample_batch()
    
    print(f"Processing {len(sample_notes)} sample clinical notes...")
    
    # Process batch
    batch_results = await processor.process_batch(
        clinical_notes=sample_notes,
        batch_name="demo_batch",
        save_results=True
    )
    
    # Show summary
    analysis = batch_results['analysis']
    print(f"\n🎉 Batch Processing Complete!")
    print(f"✅ Success rate: {analysis['success_rate']:.2%}")
    print(f"⏱️  Average processing: {analysis['avg_processing_time_ms']:.1f}ms")
    print(f"📊 Average quality: {analysis['avg_quality_score']:.2f}")
    print(f"🚀 Throughput: {analysis['throughput_notes_per_second']:.1f} notes/second")
    print(f"🎯 Performance compliance: {analysis['performance_compliance']:.2%} under 2s")
    
    print(f"\n💡 Ready to process your clinical notes!")
    print(f"   - Send 20 notes at a time")
    print(f"   - Each batch will be analyzed and reported")
    print(f"   - Results saved for trend analysis")

if __name__ == "__main__":
    asyncio.run(main())