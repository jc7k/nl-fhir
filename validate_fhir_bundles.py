#!/usr/bin/env python3
"""
FHIR Bundle Validation Against HAPI Server
Validates NLP-extracted entities converted to FHIR bundles
Tests actual FHIR R4 compliance and HAPI validation
"""

import sys
import os
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add the project root to Python path
sys.path.insert(0, 'src')

from nl_fhir.services.nlp.models import model_manager
from nl_fhir.services.fhir.bundle_assembler import FHIRBundleAssembler
from nl_fhir.services.fhir.hapi_client import HAPIFHIRClient
from nl_fhir.services.fhir.validator import FHIRValidator
from nl_fhir.services.fhir.validation_service import ValidationService

# Test clinical notes from various specialties
TEST_CLINICAL_NOTES = [
    # Simple medication orders
    "Started patient John Doe on 500mg Metformin twice daily for type 2 diabetes",
    "Prescribed 10mg Lisinopril once daily for hypertension",
    
    # Complex medication with route
    "Administer 40mg Enoxaparin subcutaneously every 12 hours for DVT prophylaxis",
    "Started 100mg IV Vancomycin every 6 hours for MRSA infection",
    
    # Multiple medications
    "Started patient on 500mg Metformin twice daily and 10mg Lisinopril once daily for diabetes and hypertension management",
    
    # Pediatric dosing
    "Give 250mg Amoxicillin orally three times daily for 7 days for ear infection",
    
    # Oncology medication
    "Initiated 200mg Pembrolizumab IV every 3 weeks for melanoma",
    
    # Pain management
    "Prescribed 5mg Oxycodone every 4 hours as needed for breakthrough pain",
    
    # Psychiatric medication
    "Started 20mg Fluoxetine once daily for major depressive disorder",
    
    # Cardiology complex
    "Prescribed 75mg Clopidogrel daily, 81mg Aspirin daily, and 20mg Atorvastatin at bedtime for CAD"
]

class FHIRBundleValidator:
    """Validates FHIR bundles from NLP extraction against HAPI server"""
    
    def __init__(self):
        self.bundle_assembler = FHIRBundleAssembler()
        self.hapi_client = HAPIFHIRClient(base_url="http://localhost:8080/fhir")
        self.fhir_validator = FHIRValidator()
        self.validation_service = ValidationService()
        
    async def initialize(self):
        """Initialize all validation components"""
        print("🔧 Initializing FHIR validation components...")
        
        # Initialize components
        self.bundle_assembler.initialize()
        self.fhir_validator.initialize()
        
        # Check HAPI server connection
        hapi_available = self.hapi_client.initialize()
        if not hapi_available:
            print("⚠️  WARNING: HAPI FHIR server not available at http://localhost:8080/fhir")
            print("   Running in local validation mode only")
            print("   To enable HAPI validation, start the server with:")
            print("   docker run -p 8080:8080 hapiproject/hapi:latest")
        else:
            print("✅ HAPI FHIR server connected successfully")
            
        await self.validation_service.initialize()
        
        return hapi_available
        
    def extract_and_convert_to_fhir(self, clinical_text: str, patient_id: str = "test-patient") -> Tuple[Dict, Dict]:
        """Extract entities and convert to FHIR bundle"""
        
        # Extract medical entities using 3-tier NLP
        entities = model_manager.extract_medical_entities(clinical_text)
        
        # Convert to structured format for bundle assembly
        structured_data = {
            "medications": [],
            "conditions": [],
            "procedures": []
        }
        
        # Process medications
        for med in entities.get("medications", []):
            if isinstance(med, dict):
                med_data = {
                    "medication": med.get("text", ""),
                    "dosage": med.get("dosage", ""),
                    "route": med.get("route", "oral"),
                    "frequency": med.get("frequency", ""),
                    "indication": med.get("indication", "")
                }
                structured_data["medications"].append(med_data)
        
        # Process conditions
        for condition in entities.get("conditions", []):
            if isinstance(condition, dict):
                structured_data["conditions"].append(condition.get("text", condition))
            else:
                structured_data["conditions"].append(condition)
                
        # Process procedures
        for procedure in entities.get("procedures", []):
            if isinstance(procedure, dict):
                structured_data["procedures"].append(procedure.get("text", procedure))
            else:
                structured_data["procedures"].append(procedure)
        
        # Create FHIR bundle
        bundle = self.bundle_assembler.create_bundle(
            patient_id=patient_id,
            medications=structured_data["medications"],
            conditions=structured_data["conditions"],
            procedures=structured_data["procedures"]
        )
        
        return entities, bundle
        
    async def validate_bundle(self, bundle: Dict, source_text: str) -> Dict:
        """Validate FHIR bundle against HAPI server"""
        
        validation_result = {
            "source_text": source_text[:100] + "..." if len(source_text) > 100 else source_text,
            "local_validation": None,
            "hapi_validation": None,
            "is_valid": False,
            "errors": [],
            "warnings": []
        }
        
        # Local validation using pydantic FHIR models
        try:
            local_result = self.fhir_validator.validate_bundle(bundle)
            validation_result["local_validation"] = {
                "valid": local_result.get("valid", False),
                "issues": local_result.get("issues", [])
            }
        except Exception as e:
            validation_result["local_validation"] = {
                "valid": False,
                "error": str(e)
            }
        
        # HAPI server validation
        if self.hapi_client.initialized:
            try:
                hapi_result = await self.validation_service.validate_bundle(bundle, "test-validation")
                validation_result["hapi_validation"] = {
                    "valid": hapi_result.get("valid", False),
                    "issues": hapi_result.get("issues", [])
                }
                
                # Extract errors and warnings
                for issue in hapi_result.get("issues", []):
                    if issue.get("severity") in ["error", "fatal"]:
                        validation_result["errors"].append(issue.get("message", "Unknown error"))
                    elif issue.get("severity") == "warning":
                        validation_result["warnings"].append(issue.get("message", "Unknown warning"))
                        
            except Exception as e:
                validation_result["hapi_validation"] = {
                    "valid": False,
                    "error": str(e)
                }
        
        # Determine overall validity
        local_valid = validation_result["local_validation"] and validation_result["local_validation"].get("valid", False)
        hapi_valid = validation_result["hapi_validation"] and validation_result["hapi_validation"].get("valid", False)
        
        # If HAPI is available, use its result; otherwise use local
        if validation_result["hapi_validation"] is not None:
            validation_result["is_valid"] = hapi_valid
        else:
            validation_result["is_valid"] = local_valid
            
        return validation_result

async def main():
    """Main validation test runner"""
    
    print("🏥 FHIR Bundle Validation Test Suite")
    print("=" * 60)
    print("Validating NLP → FHIR conversion against HAPI FHIR R4 standards")
    print()
    
    validator = FHIRBundleValidator()
    hapi_available = await validator.initialize()
    
    print()
    print("📋 Testing {} clinical notes".format(len(TEST_CLINICAL_NOTES)))
    print("-" * 60)
    
    results = []
    valid_count = 0
    
    for i, clinical_text in enumerate(TEST_CLINICAL_NOTES, 1):
        print(f"\n{i}. Testing: {clinical_text[:80]}...")
        
        try:
            # Extract and convert
            start_time = time.time()
            entities, bundle = validator.extract_and_convert_to_fhir(clinical_text)
            conversion_time = (time.time() - start_time) * 1000
            
            # Validate
            validation_start = time.time()
            validation_result = await validator.validate_bundle(bundle, clinical_text)
            validation_time = (time.time() - validation_start) * 1000
            
            # Display results
            if validation_result["is_valid"]:
                print(f"   ✅ VALID - Conversion: {conversion_time:.1f}ms, Validation: {validation_time:.1f}ms")
                valid_count += 1
            else:
                print(f"   ❌ INVALID - Conversion: {conversion_time:.1f}ms, Validation: {validation_time:.1f}ms")
                if validation_result["errors"]:
                    print(f"   Errors: {'; '.join(validation_result['errors'][:2])}")
            
            if validation_result["warnings"]:
                print(f"   ⚠️  Warnings: {'; '.join(validation_result['warnings'][:2])}")
            
            # Store result
            results.append({
                "test_id": i,
                "clinical_text": clinical_text,
                "entities_extracted": entities,
                "bundle_created": bundle is not None,
                "validation_result": validation_result,
                "conversion_time_ms": conversion_time,
                "validation_time_ms": validation_time
            })
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append({
                "test_id": i,
                "clinical_text": clinical_text,
                "error": str(e)
            })
    
    # Summary
    print()
    print("=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    success_rate = (valid_count / len(TEST_CLINICAL_NOTES)) * 100 if TEST_CLINICAL_NOTES else 0
    
    print(f"Total Tests: {len(TEST_CLINICAL_NOTES)}")
    print(f"Valid Bundles: {valid_count}")
    print(f"Invalid Bundles: {len(TEST_CLINICAL_NOTES) - valid_count}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if hapi_available:
        print(f"Validation Mode: HAPI FHIR Server (Full R4 Compliance)")
    else:
        print(f"Validation Mode: Local Only (Pydantic Models)")
    
    # Quality assessment
    print()
    if success_rate >= 95:
        print("🟢 EXCELLENT - Production Ready")
    elif success_rate >= 80:
        print("🟡 GOOD - Minor improvements needed")
    elif success_rate >= 60:
        print("🟠 FAIR - Significant improvements required")
    else:
        print("🔴 NEEDS WORK - Major issues with FHIR compliance")
    
    # Save detailed results
    output_file = Path("clinical_results/fhir_validation_results.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "hapi_available": hapi_available,
            "total_tests": len(TEST_CLINICAL_NOTES),
            "valid_bundles": valid_count,
            "success_rate": success_rate,
            "detailed_results": results
        }, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    # Architectural recommendation
    print()
    print("🏗️ ARCHITECTURAL RECOMMENDATIONS:")
    if not hapi_available:
        print("1. ⚠️  Start HAPI FHIR server for complete validation:")
        print("   docker run -p 8080:8080 hapiproject/hapi:latest")
    
    if success_rate < 100:
        print("2. Review failed validations for:")
        print("   - Missing required FHIR fields")
        print("   - Invalid code system references")
        print("   - Malformed resource structures")
        print("3. Update bundle assembler to ensure R4 compliance")
    
    return success_rate

if __name__ == "__main__":
    success_rate = asyncio.run(main())
    
    # Exit with appropriate code
    if success_rate >= 95:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Needs improvement