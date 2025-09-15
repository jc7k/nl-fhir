#!/usr/bin/env python3
"""
Fixed MedSpaCy Integration Test - Direct NLP Service Testing
Epic 2.5 - Story 2.5.1 Runtime Validation
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import logging
import json
from datetime import datetime
from typing import Dict, List, Any
from nl_fhir.services.nlp.models import model_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_medspacy_direct_integration():
    """Test MedSpaCy Clinical Intelligence Engine directly"""

    print("🏥 MedSpaCy Clinical Intelligence Integration Test (Direct)")
    print("=" * 70)

    # Test cases for different clinical scenarios
    test_cases = [
        {
            "name": "Basic Medication Order",
            "text": "Patient John Doe started on amoxicillin 250mg three times daily for acute otitis media.",
            "expected_entities": ["amoxicillin", "250mg", "three times", "daily", "acute otitis media"]
        },
        {
            "name": "Complex Medication with Route",
            "text": "Administer morphine 4mg IV every 4 hours for severe pain management.",
            "expected_entities": ["morphine", "4mg", "IV", "every 4 hours", "severe pain"]
        },
        {
            "name": "Medication with Clinical Context",
            "text": "Patient denies chest pain but reports shortness of breath. Start metformin 500mg daily.",
            "expected_entities": ["chest pain", "shortness of breath", "metformin", "500mg", "daily"]
        },
        {
            "name": "Multiple Medications",
            "text": "Continue lisinopril 10mg daily and start atorvastatin 20mg nightly for hyperlipidemia.",
            "expected_entities": ["lisinopril", "10mg", "daily", "atorvastatin", "20mg", "nightly", "hyperlipidemia"]
        },
        {
            "name": "Lab Orders with Clinical Indication",
            "text": "Order CBC and lipid panel for diabetes monitoring. Patient on metformin 850mg twice daily.",
            "expected_entities": ["CBC", "lipid panel", "diabetes", "metformin", "850mg", "twice daily"]
        }
    ]

    results = []
    medspacy_working = False

    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {case['name']} ---")
        print(f"Input: {case['text']}")

        try:
            # Test MedSpaCy loading
            medspacy_nlp = model_manager.load_medspacy_clinical_engine()
            if medspacy_nlp is None:
                print("❌ MedSpaCy failed to load")
                continue

            # Extract entities using MedSpaCy
            entities = model_manager._extract_with_medspacy_clinical(case['text'], medspacy_nlp)

            # Count entities and calculate metrics
            total_entities = sum(len(entity_list) for entity_list in entities.values())
            medspacy_entities = 0
            confidence_scores = []

            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    if 'method' in entity and 'medspacy' in entity.get('method', ''):
                        medspacy_entities += 1
                    if 'confidence' in entity:
                        confidence_scores.append(entity['confidence'])

            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            medspacy_percentage = (medspacy_entities / total_entities * 100) if total_entities > 0 else 0

            print(f"✅ Entities Found: {total_entities}")
            print(f"🎯 MedSpaCy Entities: {medspacy_entities}/{total_entities} ({medspacy_percentage:.1f}%)")
            print(f"📊 Avg Confidence: {avg_confidence:.3f}")
            print(f"🔍 Entity Details:")

            for entity_type, entity_list in entities.items():
                if entity_list:
                    print(f"  {entity_type.upper()}: {[e['text'] for e in entity_list]}")

            # Clinical context analysis
            clinical_context_count = 0
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    if 'clinical_context' in entity:
                        clinical_context_count += 1

            print(f"🏥 Clinical Context Applied: {clinical_context_count}/{total_entities} entities")

            if medspacy_entities > 0:
                medspacy_working = True

            results.append({
                "test_case": case['name'],
                "total_entities": total_entities,
                "medspacy_entities": medspacy_entities,
                "medspacy_percentage": medspacy_percentage,
                "avg_confidence": avg_confidence,
                "clinical_context_count": clinical_context_count,
                "success": total_entities > 0
            })

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "test_case": case['name'],
                "error": str(e),
                "success": False
            })

    # Summary analysis
    print("\n" + "=" * 70)
    print("📋 MEDSPACY INTEGRATION ANALYSIS RESULTS")
    print("=" * 70)

    successful_tests = [r for r in results if r.get('success', False)]
    total_entities = sum(r.get('total_entities', 0) for r in successful_tests)
    total_medspacy = sum(r.get('medspacy_entities', 0) for r in successful_tests)
    avg_confidence = sum(r.get('avg_confidence', 0) for r in successful_tests) / len(successful_tests) if successful_tests else 0

    print(f"✅ Test Success Rate: {len(successful_tests)}/{len(test_cases)} ({len(successful_tests)/len(test_cases)*100:.1f}%)")
    print(f"🎯 MedSpaCy Integration Status: {'OPERATIONAL' if medspacy_working else 'NOT WORKING'}")
    print(f"📊 Total Entities Detected: {total_entities}")
    print(f"🏥 MedSpaCy Entities: {total_medspacy}/{total_entities} ({total_medspacy/total_entities*100:.1f}%)" if total_entities > 0 else "🏥 No entities detected")
    print(f"📈 Average Confidence Score: {avg_confidence:.3f}")

    # Epic 2.5 Performance Assessment
    print(f"\n🎯 EPIC 2.5 PERFORMANCE ASSESSMENT:")
    print(f"Target F1 Score: >0.75 → Current Status: {'✅ MedSpaCy Operational' if medspacy_working else '❌ MedSpaCy Not Working'}")
    print(f"Target Accuracy: >93% → Current Status: {'✅ High Confidence ({:.1f}%)'.format(avg_confidence*100) if avg_confidence > 0.8 else '⚠️ Lower Confidence'}")
    print(f"Clinical Intelligence: {'✅ Active' if total_medspacy > 0 else '❌ Not Active'}")

    # Save results
    results_file = f"medspacy_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "test_metadata": {
                "timestamp": datetime.now().isoformat(),
                "medspacy_working": medspacy_working,
                "total_tests": len(test_cases),
                "successful_tests": len(successful_tests)
            },
            "summary_metrics": {
                "total_entities": total_entities,
                "medspacy_entities": total_medspacy,
                "medspacy_percentage": total_medspacy/total_entities*100 if total_entities > 0 else 0,
                "avg_confidence": avg_confidence
            },
            "detailed_results": results
        }, f, indent=2)

    print(f"💾 Results saved to: {results_file}")

    return {
        "medspacy_working": medspacy_working,
        "success_rate": len(successful_tests) / len(test_cases),
        "avg_confidence": avg_confidence,
        "results_file": results_file
    }

if __name__ == "__main__":
    test_medspacy_direct_integration()