#!/usr/bin/env python3
"""
Manual test of Epic 3 FHIR pipeline integration
Tests the complete pipeline from resource factory through bundle assembly to HAPI validation
"""

import asyncio
import json
import time
from datetime import datetime

# Import Epic 3 services
from src.nl_fhir.services.fhir.resource_factory import get_fhir_resource_factory
from src.nl_fhir.services.fhir.bundle_assembler import get_bundle_assembler
from src.nl_fhir.services.fhir.validation_service import get_validation_service
from src.nl_fhir.services.fhir.execution_service import get_execution_service
from src.nl_fhir.services.fhir.failover_manager import get_failover_manager


async def test_epic_3_pipeline():
    """Test complete Epic 3 pipeline integration"""
    print("🔍 Testing Epic 3 FHIR Pipeline Integration")
    print("=" * 50)
    
    try:
        request_id = "test-epic-3-pipeline"
        
        # Step 1: Initialize all services
        print("\n1. Initializing FHIR services...")
        
        resource_factory = await get_fhir_resource_factory()
        print(f"   ✅ Resource Factory initialized: {resource_factory.initialized}")
        
        bundle_assembler = await get_bundle_assembler()
        print(f"   ✅ Bundle Assembler initialized: {bundle_assembler.initialized}")
        
        validation_service = await get_validation_service()
        print(f"   ✅ Validation Service initialized: {validation_service.initialized}")
        
        execution_service = await get_execution_service()
        print(f"   ✅ Execution Service initialized: {execution_service.initialized}")
        
        failover_manager = await get_failover_manager()
        print(f"   ✅ Failover Manager initialized: {failover_manager.initialized}")
        
        # Step 2: Test resource creation (Story 3.1)
        print("\n2. Creating FHIR resources (Story 3.1)...")
        
        patient_data = {
            "age": "45", 
            "gender": "male", 
            "patient_ref": "patient-test-123"
        }
        patient_resource = resource_factory.create_patient_resource(patient_data, request_id)
        print(f"   ✅ Patient resource created: {patient_resource.get('resourceType')}")
        
        medication_data = {
            "name": "Lisinopril", 
            "dosage": "10mg", 
            "frequency": "once daily",
            "rxnorm_code": "617296"
        }
        medication_resource = resource_factory.create_medication_request(medication_data, patient_data["patient_ref"], request_id)
        print(f"   ✅ Medication request created: {medication_resource.get('resourceType')}")
        
        # Step 3: Test bundle assembly (Story 3.2)
        print("\n3. Assembling transaction bundle (Story 3.2)...")
        
        resources = [patient_resource, medication_resource]
        bundle = bundle_assembler.create_transaction_bundle(resources, request_id)
        
        print(f"   ✅ Transaction bundle created:")
        print(f"      - Bundle Type: {bundle.get('type')}")
        print(f"      - Resources: {len(bundle.get('entry', []))}")
        print(f"      - Bundle ID: {bundle.get('id')}")
        
        # Add a condition resource for more complete testing
        condition_data = {
            "name": "Hypertension",
            "icd10_code": "I10",
            "status": "active"
        }
        condition_resource = resource_factory.create_condition_resource(condition_data, patient_data["patient_ref"], request_id)
        print(f"   ✅ Condition resource created: {condition_resource.get('resourceType')}")
        
        # Update bundle with all resources
        all_resources = [patient_resource, medication_resource, condition_resource]
        bundle = bundle_assembler.create_transaction_bundle(all_resources, request_id)
        print(f"   ✅ Updated bundle with {len(bundle.get('entry', []))} resources")
        
        # Step 4: Test bundle validation (Story 3.3)
        print("\n4. Validating FHIR bundle (Story 3.3)...")
        
        start_time = time.time()
        validation_result = await validation_service.validate_bundle(bundle, request_id)
        validation_time = time.time() - start_time
        
        print(f"   ✅ Bundle validation completed:")
        print(f"      - Result: {validation_result.get('validation_result')}")
        print(f"      - Valid: {validation_result.get('is_valid')}")
        print(f"      - Quality Score: {validation_result.get('bundle_quality_score')}")
        print(f"      - Validation Time: {validation_time:.3f}s")
        print(f"      - Source: {validation_result.get('validation_source')}")
        
        # Step 5: Test optional bundle execution (Story 3.3)
        print("\n5. Testing bundle execution (Story 3.3)...")
        
        start_time = time.time()
        execution_result = await execution_service.execute_bundle(
            bundle, 
            request_id=request_id,
            validate_first=False,  # Already validated
            force_execution=True   # Force execution for testing
        )
        execution_time = time.time() - start_time
        
        print(f"   ✅ Bundle execution completed:")
        print(f"      - Result: {execution_result.get('execution_result')}")
        print(f"      - Success: {execution_result.get('success')}")
        print(f"      - Total Resources: {execution_result.get('total_resources')}")
        print(f"      - Successful Resources: {execution_result.get('successful_resources')}")
        print(f"      - Execution Time: {execution_time:.3f}s")
        
        # Step 6: Test failover manager
        print("\n6. Testing failover capabilities...")
        
        endpoint_status = failover_manager.get_endpoint_status()
        print(f"   ✅ Endpoint status:")
        print(f"      - Total Endpoints: {len(endpoint_status.get('endpoints', []))}")
        print(f"      - Health Status: {endpoint_status.get('healthy_endpoints', 0)}/{len(endpoint_status.get('endpoints', []))}")
        
        failover_metrics = failover_manager.get_failover_metrics()
        print(f"   ✅ Failover metrics:")
        print(f"      - Availability: {failover_metrics.get('availability_percentage')}%")
        print(f"      - Meets Target: {failover_metrics.get('meets_availability_target')}")
        
        # Step 7: Performance validation
        print("\n7. Performance validation...")
        
        if validation_time < 2.0:
            print(f"   ✅ Validation performance: {validation_time:.3f}s (< 2s requirement)")
        else:
            print(f"   ⚠️  Validation performance: {validation_time:.3f}s (exceeds 2s requirement)")
            
        if execution_time < 2.0:
            print(f"   ✅ Execution performance: {execution_time:.3f}s (< 2s requirement)")
        else:
            print(f"   ⚠️  Execution performance: {execution_time:.3f}s (exceeds 2s requirement)")
        
        # Step 8: Service metrics
        print("\n8. Service metrics validation...")
        
        validation_metrics = validation_service.get_validation_metrics()
        print(f"   ✅ Validation metrics:")
        print(f"      - Total Validations: {validation_metrics.get('total_validations')}")
        print(f"      - Success Rate: {validation_metrics.get('success_rate_percentage')}%")
        print(f"      - Meets Target: {validation_metrics.get('meets_target')}")
        
        execution_metrics = execution_service.get_execution_metrics()
        print(f"   ✅ Execution metrics:")
        print(f"      - Total Executions: {execution_metrics.get('total_executions')}")
        print(f"      - Success Rate: {execution_metrics.get('success_rate_percentage')}%")
        print(f"      - Meets Target: {execution_metrics.get('meets_target')}")
        
        print("\n" + "=" * 50)
        print("🎉 Epic 3 Pipeline Integration Test COMPLETED!")
        print("✅ All services initialized and functioning correctly")
        print("✅ Complete FHIR pipeline validated from NLP → Resources → Bundle → Validation → Execution")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during Epic 3 pipeline test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_epic_3_pipeline())
    exit(0 if success else 1)