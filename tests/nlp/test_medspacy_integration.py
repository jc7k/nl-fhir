#!/usr/bin/env python3
"""
Test MedSpaCy Clinical Intelligence Integration
Epic 2.5 - Story 2.5.1 Testing
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import logging
import json
from nl_fhir.services.nlp.models import NLPModelManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_medspacy_clinical_intelligence():
    """Test MedSpaCy Clinical Intelligence Engine with clinical scenarios"""
    
    logger.info("🏥 Testing MedSpaCy Clinical Intelligence Integration (Epic 2.5)")
    
    # Initialize NLP Model Manager
    nlp_manager = NLPModelManager()
    
    # Test cases covering Epic 2.5 requirements
    clinical_test_cases = [
        # Negation detection test
        "Patient John Doe denies chest pain but reports shortness of breath",
        
        # Medication order with dosage and frequency
        "Start patient on 500mg amoxicillin twice daily for pneumonia",
        
        # Complex clinical scenario with multiple entities
        "Patient Mary Smith has diabetes. Prescribe metformin 850mg daily. Order HbA1c and lipid panel.",
        
        # Clinical context with temporal information
        "History of hypertension, currently on lisinopril 10mg daily",
        
        # Lab order with clinical indication
        "Order CBC and chest X-ray for evaluation of chronic cough"
    ]
    
    results = []
    
    for i, test_case in enumerate(clinical_test_cases, 1):
        logger.info(f"\n--- Test Case {i} ---")
        logger.info(f"Input: {test_case}")
        
        try:
            # Test MedSpaCy clinical extraction
            entities = nlp_manager.extract_medical_entities(test_case)
            
            # Count total entities
            total_entities = sum(len(entity_list) for entity_list in entities.values())
            
            logger.info(f"🎯 Extracted {total_entities} entities:")
            for entity_type, entity_list in entities.items():
                if entity_list:
                    logger.info(f"  {entity_type}: {len(entity_list)} entities")
                    for entity in entity_list:
                        clinical_context = entity.get('clinical_context', {})
                        negated = clinical_context.get('is_negated', False)
                        historical = clinical_context.get('is_historical', False)
                        context_str = ""
                        if negated:
                            context_str += " [NEGATED]"
                        if historical:
                            context_str += " [HISTORICAL]"
                        logger.info(f"    • {entity['text']} (conf: {entity['confidence']:.2f}, method: {entity['method']}){context_str}")
            
            # Calculate quality score
            quality_score = nlp_manager._calculate_quality_score(entities, test_case)
            logger.info(f"📊 Quality Score: {quality_score:.2f}")
            
            results.append({
                "test_case": test_case,
                "entities": entities,
                "total_entities": total_entities,
                "quality_score": quality_score
            })
            
        except Exception as e:
            logger.error(f"❌ Test case {i} failed: {e}")
            results.append({
                "test_case": test_case,
                "error": str(e)
            })
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("🏥 MEDSPACY CLINICAL INTELLIGENCE TEST SUMMARY")
    logger.info("="*60)
    
    successful_tests = [r for r in results if 'error' not in r]
    failed_tests = [r for r in results if 'error' in r]
    
    logger.info(f"✅ Successful Tests: {len(successful_tests)}/{len(clinical_test_cases)}")
    logger.info(f"❌ Failed Tests: {len(failed_tests)}")
    
    if successful_tests:
        avg_entities = sum(r['total_entities'] for r in successful_tests) / len(successful_tests)
        avg_quality = sum(r['quality_score'] for r in successful_tests) / len(successful_tests)
        
        logger.info(f"📊 Average Entities Extracted: {avg_entities:.1f}")
        logger.info(f"📊 Average Quality Score: {avg_quality:.2f}")
        
        # Check if we're meeting Epic 2.5 targets
        if avg_quality >= 0.6:  # Target improvement over current 0.5
            logger.info("🎯 QUALITY TARGET: APPROACHING (Epic 2.5 improvement detected)")
        else:
            logger.info("⚠️  QUALITY TARGET: NEEDS IMPROVEMENT")
    
    # Test MedSpaCy model loading specifically
    logger.info("\n--- MedSpaCy Model Loading Test ---")
    try:
        medspacy_engine = nlp_manager.load_medspacy_clinical_engine()
        if medspacy_engine:
            logger.info("✅ MedSpaCy Clinical Engine loaded successfully")
            
            # Test direct MedSpaCy processing
            test_doc = medspacy_engine("Patient denies chest pain. Start amoxicillin 500mg twice daily.")
            logger.info(f"✅ Direct MedSpaCy processing successful: {len(test_doc.ents)} entities detected")
            
            for ent in test_doc.ents:
                logger.info(f"    • {ent.text} ({ent.label_})")
                
        else:
            logger.warning("⚠️  MedSpaCy Clinical Engine not available - using fallback")
            
    except Exception as e:
        logger.error(f"❌ MedSpaCy model loading failed: {e}")
    
    return results

if __name__ == "__main__":
    results = test_medspacy_clinical_intelligence()
    
    # Save results for analysis
    with open("medspacy_test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n✅ Test results saved to medspacy_test_results.json")