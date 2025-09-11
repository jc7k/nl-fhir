"""
Comprehensive Epic 3 FHIR Integration Tests
Tests for Stories 3.1, 3.2, and 3.3 complete FHIR pipeline
HIPAA Compliant: No PHI in test data
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Test FHIR pipeline integration
from src.nl_fhir.services.fhir.resource_factory import get_fhir_resource_factory
from src.nl_fhir.services.fhir.bundle_assembler import get_bundle_assembler
from src.nl_fhir.services.fhir.validation_service import get_validation_service
from src.nl_fhir.services.fhir.execution_service import get_execution_service
from src.nl_fhir.services.fhir.failover_manager import get_failover_manager


class TestHAPIFHIRIntegration:
    """Story 3.3: HAPI FHIR Integration & Validation Tests"""
    
    @pytest.mark.asyncio
    async def test_validation_service_initialization(self):
        """Test validation service initialization and health"""
        validation_service = await get_validation_service()
        assert validation_service.initialized == True
        
        # Test metrics initialization
        metrics = validation_service.get_validation_metrics()
        assert "total_validations" in metrics
        assert "success_rate_percentage" in metrics
        assert "meets_target" in metrics
    
    @pytest.mark.asyncio
    async def test_execution_service_initialization(self):
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
    async def test_failover_manager_initialization(self):
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
    
    @pytest.fixture
    def sample_fhir_bundle(self):
        """Sample FHIR transaction bundle for testing"""
        return {
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
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "med-req-123",
                        "status": "active",
                        "intent": "order",
                        "subject": {"reference": "Patient/patient-123"},
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "617296",
                                "display": "Lisinopril 10mg"
                            }]
                        },
                        "dosageInstruction": [{
                            "text": "Take one tablet daily",
                            "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}}
                        }]
                    },
                    "request": {
                        "method": "POST",
                        "url": "MedicationRequest"
                    }
                }
            ]
        }
    
    @pytest.fixture
    def invalid_fhir_bundle(self):
        """Invalid FHIR bundle for testing error handling"""
        return {
            "resourceType": "Bundle",
            "id": "invalid-bundle",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        # Missing required fields: status, intent, subject
                        "medicationCodeableConcept": {
                            "coding": [{
                                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": "invalid-code"
                            }]
                        }
                    },
                    "request": {
                        "method": "POST",
                        "url": "MedicationRequest"
                    }
                }
            ]
        }
    
    async def test_validation_service_initialization(self, validation_service):
        """Test validation service initialization and health"""
        assert validation_service.initialized == True
        
        # Test metrics initialization
        metrics = validation_service.get_validation_metrics()
        assert "total_validations" in metrics
        assert "success_rate_percentage" in metrics
        assert "meets_target" in metrics
    
    async def test_bundle_validation_success(self, validation_service, sample_fhir_bundle):
        """Test successful FHIR bundle validation"""
        request_id = "test-validation-001"
        
        # Validate bundle
        result = await validation_service.validate_bundle(sample_fhir_bundle, request_id)
        
        # Verify validation structure
        assert "validation_result" in result
        assert "is_valid" in result
        assert "issues" in result
        assert "user_messages" in result
        assert "recommendations" in result
        assert "bundle_quality_score" in result
        assert "validation_source" in result
        assert "validation_time" in result
        
        # Verify validation success for well-formed bundle
        # Note: May be warnings due to fallback validation, but should not be errors
        assert result["validation_result"] in ["success", "warning"]
        assert result["bundle_quality_score"] >= 0.5  # Reasonable quality score
        
        # Verify user-friendly messages
        assert isinstance(result["user_messages"], dict)
        assert "errors" in result["user_messages"]
        assert "warnings" in result["user_messages"]
        assert "information" in result["user_messages"]
    
    async def test_bundle_validation_failure(self, validation_service, invalid_fhir_bundle):
        """Test FHIR bundle validation with errors"""
        request_id = "test-validation-002"
        
        # Validate invalid bundle
        result = await validation_service.validate_bundle(invalid_fhir_bundle, request_id)
        
        # Should have validation errors
        assert result["validation_result"] == "error"
        assert result["is_valid"] == False
        assert result["bundle_quality_score"] < 0.5  # Low quality score
        
        # Should have error messages
        assert len(result["issues"]["errors"]) > 0
        assert len(result["user_messages"]["errors"]) > 0
        assert len(result["recommendations"]) > 0
    
    async def test_execution_service_initialization(self, execution_service):
        """Test execution service initialization and health"""
        assert execution_service.initialized == True
        
        # Test metrics initialization
        metrics = execution_service.get_execution_metrics()
        assert "total_executions" in metrics
        assert "successful_executions" in metrics
        assert "success_rate_percentage" in metrics
        assert "meets_target" in metrics
    
    async def test_bundle_execution_success(self, execution_service, sample_fhir_bundle):
        """Test successful FHIR bundle execution"""
        request_id = "test-execution-001"
        
        # Execute bundle
        result = await execution_service.execute_bundle(
            sample_fhir_bundle, 
            request_id=request_id,
            validate_first=True,
            force_execution=False
        )
        
        # Verify execution structure
        assert "execution_result" in result
        assert "success" in result
        assert "total_resources" in result
        assert "successful_resources" in result
        assert "created_resources" in result
        assert "execution_summary" in result
        
        # Verify execution completed (success or simulation)
        assert result["execution_result"] in ["success", "partial"]
        assert result["total_resources"] == 2  # Patient + MedicationRequest
        assert len(result["created_resources"]) > 0
    
    async def test_failover_manager_initialization(self, failover_manager):
        """Test failover manager initialization and endpoints"""
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
    
    async def test_validation_performance_requirement(self, validation_service, sample_fhir_bundle):
        """Test validation meets <2s performance requirement"""
        request_id = "test-performance-001"
        
        # Measure validation time
        start_time = time.time()
        result = await validation_service.validate_bundle(sample_fhir_bundle, request_id)
        validation_time = time.time() - start_time
        
        # Should complete within 2 seconds
        assert validation_time < 2.0, f"Validation took {validation_time:.3f}s, exceeds 2s requirement"
        
        # Verify performance is recorded
        assert "validation_time" in result
        assert result["validation_time"].endswith("s")
    
    async def test_execution_performance_requirement(self, execution_service, sample_fhir_bundle):
        """Test execution meets <2s performance requirement"""
        request_id = "test-performance-002"
        
        # Measure execution time
        start_time = time.time()
        result = await execution_service.execute_bundle(sample_fhir_bundle, request_id)
        execution_time = time.time() - start_time
        
        # Should complete within 2 seconds
        assert execution_time < 2.0, f"Execution took {execution_time:.3f}s, exceeds 2s requirement"
        
        # Verify performance is recorded
        assert "execution_time" in result
        assert result["execution_time"].endswith("s")


class TestCompleteEpic3Pipeline:
    """Integration tests for complete Epic 3 FHIR pipeline (Stories 3.1 + 3.2 + 3.3)"""
    
    @pytest.fixture
    async def resource_factory(self):
        """Get initialized resource factory"""
        return await get_fhir_resource_factory()
    
    @pytest.fixture
    async def bundle_assembler(self):
        """Get initialized bundle assembler"""
        return await get_bundle_assembler()
    
    @pytest.fixture
    async def validation_service(self):
        """Get initialized validation service"""
        return await get_validation_service()
    
    @pytest.fixture
    async def execution_service(self):
        """Get initialized execution service"""
        return await get_execution_service()
    
    @pytest.fixture
    def nlp_entities(self):
        """Sample NLP entities for FHIR resource creation"""
        return {
            "medications": [
                {"name": "Lisinopril", "dosage": "10mg", "frequency": "once daily", "rxnorm_code": "617296"}
            ],
            "conditions": [
                {"name": "Hypertension", "icd10_code": "I10", "status": "active"}
            ],
            "patient_info": {
                "age": "45", "gender": "male", "patient_ref": "patient-test-123"
            },
            "provider_info": {
                "name": "Dr. Smith", "npi": "1234567890"
            }
        }
    
    async def test_complete_pipeline_success(self, resource_factory, bundle_assembler, 
                                          validation_service, execution_service, nlp_entities):
        """Test complete Epic 3 pipeline: NLP → FHIR → Bundle → Validation → Execution"""
        request_id = "test-pipeline-001"
        
        # Step 1: Create FHIR resources from NLP entities (Story 3.1)
        resources = {}
        
        # Create Patient resource
        patient_resource = resource_factory.create_patient_resource(
            nlp_entities["patient_info"], request_id
        )
        resources["patient"] = patient_resource
        
        # Create Practitioner resource
        practitioner_resource = resource_factory.create_practitioner_resource(
            nlp_entities["provider_info"], request_id
        )
        resources["practitioner"] = practitioner_resource
        
        # Create MedicationRequest resource
        med_resource = resource_factory.create_medication_request_resource(
            nlp_entities["medications"][0], 
            nlp_entities["patient_info"]["patient_ref"],
            request_id
        )
        resources["medication_request"] = med_resource
        
        # Step 2: Assemble transaction bundle (Story 3.2)
        resource_list = list(resources.values())
        bundle = bundle_assembler.create_transaction_bundle(resource_list, request_id)
        
        # Verify bundle structure
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "transaction"
        assert len(bundle["entry"]) >= 3  # Patient, Practitioner, MedicationRequest
        
        # Step 3: Validate bundle (Story 3.3)
        validation_result = await validation_service.validate_bundle(bundle, request_id)
        
        # Should have reasonable validation result
        assert validation_result["validation_result"] in ["success", "warning", "error"]
        assert "bundle_quality_score" in validation_result
        
        # Step 4: Execute bundle (Story 3.3)
        execution_result = await execution_service.execute_bundle(
            bundle, 
            request_id=request_id,
            validate_first=False,  # Already validated
            force_execution=True   # Execute despite any warnings
        )
        
        # Should complete execution
        assert execution_result["execution_result"] in ["success", "partial"]
        assert execution_result["total_resources"] >= 3


if __name__ == "__main__":
    """Run tests manually for development"""
    pytest.main([__file__, "-v", "-s"])