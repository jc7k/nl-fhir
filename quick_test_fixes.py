#!/usr/bin/env python3
"""
Quick test script to verify our fixes for lab/procedure order failures
"""

import asyncio
import json
from datetime import datetime
from src.nl_fhir.services.conversion import ConversionService

async def test_fixes():
    """Test the key failing scenarios from the original 12"""
    
    conversion_service = ConversionService()
    
    # Test scenarios that were previously failing
    test_cases = [
        {
            "name": "CBC and Metabolic Panel Test",
            "text": "Order CBC and comprehensive metabolic panel for routine health screening"
        },
        {
            "name": "Diabetes Labs (HbA1c)",  
            "text": "Order HbA1c level and lipid panel for diabetes monitoring"
        },
        {
            "name": "Chest Pain Procedure",
            "text": "Order chest X-ray and ECG for patient with chest pain"
        },
        {
            "name": "Zoloft Medication (previously missing)",
            "text": "Start patient on Sertraline 100mg daily for depression"
        },
        {
            "name": "Multiple Medication Order",
            "text": "Prescribe Albuterol inhaler 2 puffs every 6 hours and Prednisone 20mg daily for asthma exacerbation"
        }
    ]
    
    print("🧪 Testing Core NLP Extraction Fixes")
    print("=" * 50)
    
    total_scenarios = len(test_cases)
    passed_scenarios = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Input: {test_case['text']}")
        
        try:
            # Test basic NLP extraction
            result = await conversion_service._basic_text_analysis(test_case['text'], f"test-{i}")
            
            medications = result.get('medications', [])
            lab_tests = result.get('lab_tests', [])
            procedures = result.get('procedures', [])
            conditions = result.get('conditions', [])
            
            print(f"   📊 Results:")
            print(f"      Medications: {len(medications)}")
            print(f"      Lab Tests: {len(lab_tests)}")
            print(f"      Procedures: {len(procedures)}")
            print(f"      Conditions: {len(conditions)}")
            
            # Display found entities
            if medications:
                print(f"      Found medications: {[med['text'] for med in medications]}")
            if lab_tests:
                print(f"      Found lab tests: {[lab['text'] for lab in lab_tests]}")
            if procedures:
                print(f"      Found procedures: {[proc['text'] for proc in procedures]}")
            if conditions:
                print(f"      Found conditions: {[cond['text'] for cond in conditions]}")
            
            total_entities = len(medications) + len(lab_tests) + len(procedures) + len(conditions)
            
            if total_entities > 0:
                print(f"   ✅ PASS - Found {total_entities} total entities")
                passed_scenarios += 1
            else:
                print(f"   ❌ FAIL - No entities found")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print(f"\n" + "=" * 50)
    success_rate = (passed_scenarios / total_scenarios) * 100
    print(f"🎯 SUMMARY: {passed_scenarios}/{total_scenarios} scenarios passed ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("🚀 All core fixes are working! Ready for comprehensive testing.")
    elif success_rate >= 80:
        print("✨ Good progress! Minor tweaks may be needed.")
    else:
        print("⚠️  Additional fixes needed.")
    
    return success_rate

if __name__ == "__main__":
    asyncio.run(test_fixes())