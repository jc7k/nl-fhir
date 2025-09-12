#!/usr/bin/env python3
"""
Simple FHIR Compliance Test
Tests whether our NLP extraction actually produces valid FHIR bundles
"""

import sys
import json
import time
from pathlib import Path

# Add the project root to Python path  
sys.path.insert(0, 'src')

from nl_fhir.services.nlp.models import model_manager

# Sample clinical notes for testing
TEST_NOTES = [
    "Started patient John Doe on 500mg Metformin twice daily for type 2 diabetes",
    "Prescribed 10mg Lisinopril once daily for hypertension",
    "Administer 40mg Enoxaparin subcutaneously every 12 hours for DVT prophylaxis",
    "Started patient on 500mg Amoxicillin three times daily for infection",
    "Give 200mg Ibuprofen every 6 hours as needed for pain"
]

def create_basic_fhir_bundle(entities, patient_id="test-patient"):
    """Create a basic FHIR R4 bundle from extracted entities"""
    
    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": []
    }
    
    # Add medications as MedicationRequest resources
    for med in entities.get("medications", []):
        if isinstance(med, dict):
            med_text = med.get("text", "Unknown medication")
            dosage = med.get("dosage", "")
            frequency = med.get("frequency", "")
            route = med.get("route", "oral")
            
            medication_request = {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "text": f"{med_text} {dosage}".strip()
                    },
                    "subject": {
                        "reference": f"Patient/{patient_id}"
                    },
                    "dosageInstruction": [{
                        "text": f"{dosage} {frequency}".strip(),
                        "route": {
                            "text": route
                        }
                    }]
                },
                "request": {
                    "method": "POST",
                    "url": "MedicationRequest"
                }
            }
            bundle["entry"].append(medication_request)
    
    # Add conditions
    for condition in entities.get("conditions", []):
        condition_text = condition.get("text", condition) if isinstance(condition, dict) else condition
        
        condition_resource = {
            "resource": {
                "resourceType": "Condition",
                "clinicalStatus": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active"
                    }]
                },
                "code": {
                    "text": condition_text
                },
                "subject": {
                    "reference": f"Patient/{patient_id}"
                }
            },
            "request": {
                "method": "POST", 
                "url": "Condition"
            }
        }
        bundle["entry"].append(condition_resource)
    
    return bundle

def validate_fhir_structure(bundle):
    """Basic FHIR structure validation"""
    
    issues = []
    
    # Check required fields
    if not bundle.get("resourceType") == "Bundle":
        issues.append("Missing or incorrect resourceType")
    
    if not bundle.get("type"):
        issues.append("Missing bundle type")
        
    if not isinstance(bundle.get("entry"), list):
        issues.append("Entry must be a list")
    
    # Validate each entry
    for i, entry in enumerate(bundle.get("entry", [])):
        if not entry.get("resource"):
            issues.append(f"Entry {i}: Missing resource")
        else:
            resource = entry["resource"]
            if not resource.get("resourceType"):
                issues.append(f"Entry {i}: Missing resourceType")
            
            # Validate MedicationRequest
            if resource.get("resourceType") == "MedicationRequest":
                if not resource.get("status"):
                    issues.append(f"Entry {i}: MedicationRequest missing status")
                if not resource.get("intent"):
                    issues.append(f"Entry {i}: MedicationRequest missing intent")
                if not resource.get("subject"):
                    issues.append(f"Entry {i}: MedicationRequest missing subject")
                    
            # Validate Condition
            elif resource.get("resourceType") == "Condition":
                if not resource.get("clinicalStatus"):
                    issues.append(f"Entry {i}: Condition missing clinicalStatus")
                if not resource.get("subject"):
                    issues.append(f"Entry {i}: Condition missing subject")
    
    return len(issues) == 0, issues

def main():
    """Run FHIR compliance tests"""
    
    print("🏥 FHIR R4 Compliance Test")
    print("=" * 60)
    print("Testing NLP → FHIR conversion without external dependencies")
    print()
    
    results = []
    valid_count = 0
    
    for i, clinical_text in enumerate(TEST_NOTES, 1):
        print(f"{i}. Testing: {clinical_text[:60]}...")
        
        # Extract entities
        start_time = time.time()
        entities = model_manager.extract_medical_entities(clinical_text)
        extraction_time = (time.time() - start_time) * 1000
        
        # Create FHIR bundle
        bundle = create_basic_fhir_bundle(entities)
        
        # Validate structure
        is_valid, issues = validate_fhir_structure(bundle)
        
        if is_valid:
            print(f"   ✅ VALID FHIR Bundle - {len(bundle['entry'])} resources ({extraction_time:.1f}ms)")
            valid_count += 1
        else:
            print(f"   ❌ INVALID FHIR Bundle - Issues: {', '.join(issues[:2])}")
        
        # Store result
        results.append({
            "test_id": i,
            "clinical_text": clinical_text,
            "entities": entities,
            "bundle": bundle,
            "valid": is_valid,
            "issues": issues,
            "extraction_time_ms": extraction_time
        })
    
    # Summary
    print()
    print("=" * 60)
    print("📊 COMPLIANCE SUMMARY")
    print("=" * 60)
    
    success_rate = (valid_count / len(TEST_NOTES)) * 100
    
    print(f"Total Tests: {len(TEST_NOTES)}")
    print(f"Valid FHIR Bundles: {valid_count}")
    print(f"Invalid Bundles: {len(TEST_NOTES) - valid_count}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Average Extraction Time: {sum(r['extraction_time_ms'] for r in results) / len(results):.1f}ms")
    
    # Quality assessment
    print()
    if success_rate == 100:
        print("🟢 EXCELLENT - Basic FHIR structure is valid")
    elif success_rate >= 80:
        print("🟡 GOOD - Most bundles are structurally valid")
    else:
        print("🔴 NEEDS WORK - Significant FHIR compliance issues")
    
    # Save results
    output_dir = Path("clinical_results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "fhir_compliance_test.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": len(TEST_NOTES),
            "valid_bundles": valid_count,
            "success_rate": success_rate,
            "results": results
        }, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Show example bundle
    if results and results[0]["valid"]:
        print("\n📋 Example Valid FHIR Bundle:")
        print(json.dumps(results[0]["bundle"], indent=2)[:500] + "...")
    
    # IMPORTANT WARNING
    print()
    print("⚠️  IMPORTANT NOTE:")
    print("This test only validates basic FHIR structure, NOT full R4 compliance.")
    print("For production claims, you must validate against a real HAPI FHIR server:")
    print()
    print("1. Start HAPI server: docker run -p 8080:8080 hapiproject/hapi:latest")
    print("2. Run full validation suite against the server")
    print("3. Verify terminology bindings (SNOMED, RxNorm, LOINC)")
    print("4. Test with real EHR integration")
    
    return success_rate

if __name__ == "__main__":
    success_rate = main()
    print(f"\n{'='*60}")
    print(f"Final Score: {success_rate:.1f}% structural compliance")
    print(f"{'='*60}")