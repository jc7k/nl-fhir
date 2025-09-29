"""
Story 3.3: HAPI FHIR Integration Tests
Simplified test suite for HAPI validation and execution services
"""

import pytest
import asyncio
import time
from datetime import datetime

from src.nl_fhir.services.fhir.validation_service import get_validation_service
from src.nl_fhir.services.fhir.execution_service import get_execution_service
from src.nl_fhir.services.fhir.failover_manager import get_failover_manager


@pytest.mark.asyncio
async def test_validation_service_initialization():
    """Test validation service initialization and health"""
    validation_service = await get_validation_service()
    assert validation_service.initialized == True
    
    # Test metrics initialization
    metrics = validation_service.get_validation_metrics()
    assert "total_validations" in metrics
    assert "success_rate_percentage" in metrics
    assert "meets_target" in metrics


@pytest.mark.asyncio
async def test_execution_service_initialization():
    """Test execution service initialization and health"""
    execution_service = await get_execution_service()
    assert execution_service.initialized == True
    
    # Test metrics initialization
    metrics = execution_service.get_execution_metrics()
    assert "total_executions" in metrics
    assert "successful_executions" in metrics
    assert "success_rate_percentage" in metrics
    assert "meets_target" in metrics


@pytest.mark.asyncio
async def test_failover_manager_initialization():
    """Test failover manager initialization and endpoints"""
    failover_manager = await get_failover_manager()
    assert failover_manager.initialized == True
    
    # Check default endpoints are configured
    endpoint_status = failover_manager.get_endpoint_status()
    assert "endpoints" in endpoint_status
    assert len(endpoint_status["endpoints"]) >= 3  # local_docker, cloud_primary, cloud_fallback
    
    # Check failover metrics
    metrics = failover_manager.get_failover_metrics()
    assert "total_endpoints" in metrics
    assert "healthy_endpoints" in metrics
    assert "availability_percentage" in metrics
    assert "meets_availability_target" in metrics


@pytest.mark.asyncio
async def test_bundle_validation():
    """Test FHIR bundle validation functionality"""
    validation_service = await get_validation_service()
    
    # Sample FHIR transaction bundle
    sample_bundle = {
        "resourceType": "Bundle",
        "id": "test-bundle-123",
        "type": "transaction",
        "timestamp": datetime.now().isoformat() + "Z",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-123",
                    "name": [{"family": "TestPatient", "given": ["John"]}],
                    "gender": "male",
                    "birthDate": "1980-01-01"
                },
                "request": {
                    "method": "PUT",
                    "url": "Patient/patient-123"
                }
            }
        ]
    }
    
    # Test validation
    request_id = "test-validation-001"
    result = await validation_service.validate_bundle(sample_bundle, request_id)
    
    # Verify validation structure
    assert "validation_result" in result
    assert "is_valid" in result
    assert "issues" in result
    assert "user_messages" in result
    assert "recommendations" in result
    assert "bundle_quality_score" in result
    assert "validation_source" in result
    assert "validation_time" in result
    
    # Should have reasonable quality score
    assert result["bundle_quality_score"] >= 0.0
    assert result["bundle_quality_score"] <= 1.0


@pytest.mark.asyncio
async def test_bundle_execution():
    """Test FHIR bundle execution functionality"""
    execution_service = await get_execution_service()
    
    # Sample FHIR transaction bundle
    sample_bundle = {
        "resourceType": "Bundle",
        "id": "test-bundle-456",
        "type": "transaction",
        "timestamp": datetime.now().isoformat() + "Z",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-456",
                    "name": [{"family": "TestPatient", "given": ["Jane"]}],
                    "gender": "female",
                    "birthDate": "1985-01-01"
                },
                "request": {
                    "method": "PUT",
                    "url": "Patient/patient-456"
                }
            }
        ]
    }
    
    # Test execution
    request_id = "test-execution-001"
    result = await execution_service.execute_bundle(
        sample_bundle,
        request_id=request_id,
        validate_first=True,
        force_execution=True  # Force execution despite any warnings
    )
    
    # Verify execution structure
    assert "execution_result" in result
    assert "success" in result
    assert "total_resources" in result
    assert "successful_resources" in result
    assert "created_resources" in result
    assert "execution_summary" in result
    assert "execution_source" in result
    assert "execution_time" in result
    
    # Should complete execution (success or simulation)
    assert result["execution_result"] in ["success", "partial", "failure"]
    assert result["total_resources"] >= 0


@pytest.mark.asyncio
async def test_performance_requirements():
    """Test that services meet <2s performance requirements"""
    validation_service = await get_validation_service()
    
    # Simple test bundle
    test_bundle = {
        "resourceType": "Bundle",
        "id": "perf-test",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-perf",
                    "gender": "unknown"
                },
                "request": {
                    "method": "PUT",
                    "url": "Patient/patient-perf"
                }
            }
        ]
    }
    
    # Test validation performance
    start_time = time.time()
    result = await validation_service.validate_bundle(test_bundle, "perf-test")
    validation_time = time.time() - start_time
    
    # Should complete within 2 seconds
    assert validation_time < 2.0, f"Validation took {validation_time:.3f}s, exceeds 2s requirement"
    
    # Verify performance is recorded
    assert "validation_time" in result
    assert result["validation_time"].endswith("s")


@pytest.mark.asyncio
async def test_complete_epic_3_pipeline():
    """Test complete Epic 3 pipeline integration"""
    from src.nl_fhir.services.fhir.factory_adapter import get_fhir_resource_factory
    from src.nl_fhir.services.fhir.bundle_assembler import get_bundle_assembler
    
    # Initialize services
    resource_factory = await get_fhir_resource_factory()
    bundle_assembler = await get_bundle_assembler()
    validation_service = await get_validation_service()
    execution_service = await get_execution_service()
    
    request_id = "test-pipeline-001"
    
    # Step 1: Create FHIR resources (Story 3.1)
    patient_data = {
        "age": "45", "gender": "male", "patient_ref": "patient-pipeline-test"
    }
    provider_data = {
        "name": "Dr. Pipeline", "npi": "1234567890"
    }
    
    patient_resource = resource_factory.create_patient_resource(patient_data, request_id)
    practitioner_resource = resource_factory.create_practitioner_resource(provider_data, request_id)
    
    # Step 2: Assemble transaction bundle (Story 3.2)
    resources = [patient_resource, practitioner_resource]
    bundle = bundle_assembler.create_transaction_bundle(resources, request_id)
    
    # Verify bundle structure
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "transaction"
    assert len(bundle["entry"]) >= 2
    
    # Step 3: Validate bundle (Story 3.3)
    validation_result = await validation_service.validate_bundle(bundle, request_id)
    assert "validation_result" in validation_result
    assert "bundle_quality_score" in validation_result
    
    # Step 4: Execute bundle (Story 3.3)
    execution_result = await execution_service.execute_bundle(
        bundle,
        request_id=request_id,
        validate_first=False,  # Already validated
        force_execution=True
    )
    
    # Should complete execution
    assert execution_result["execution_result"] in ["success", "partial"]
    assert execution_result["total_resources"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])