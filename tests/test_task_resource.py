#!/usr/bin/env python3
"""
Basic test for FHIR Task resource implementation
Story TW-001: Core Task Resource Implementation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


@pytest.fixture
def factory():
    """Create FHIR resource factory"""
    factory = get_factory_adapter()
    factory.initialize()
    return factory


class TestTaskResourceCreation:
    """Test FHIR Task resource creation functionality"""

    def test_create_basic_task_resource(self, factory):
        """Test creating a basic Task resource"""
        task_data = {
            "description": "Assign medication reconciliation task to pharmacy team",
            "status": "requested",
            "intent": "order",
            "priority": "routine"
        }
        patient_ref = "patient-123"

        result = factory.create_task_resource(
            task_data=task_data,
            patient_ref=patient_ref,
            request_id="test-request-001"
        )

        assert result is not None
        assert result["resourceType"] == "Task"
        assert result["status"] == "requested"
        assert result["intent"] == "order"
        assert result["priority"] == "routine"
        assert result["description"] == "Assign medication reconciliation task to pharmacy team"
        assert result["for"]["reference"] == "Patient/patient-123"
        assert "authoredOn" in result
        assert "lastModified" in result

    def test_create_task_with_focus_reference(self, factory):
        """Test creating Task with focus reference to MedicationRequest"""
        task_data = {
            "description": "Monitor vancomycin therapy for red man syndrome",
            "status": "requested",
            "intent": "order"
        }

        result = factory.create_task_resource(
            task_data=task_data,
            patient_ref="patient-456",
            focus_ref="MedicationRequest/med-req-789",
            request_id="test-request-002"
        )

        assert result is not None
        assert result["focus"]["reference"] == "MedicationRequest/med-req-789"

    def test_create_task_with_requester_and_owner(self, factory):
        """Test creating Task with requester and owner references"""
        task_data = {
            "description": "Schedule follow-up appointment with cardiology",
            "status": "requested",
            "intent": "order"
        }

        result = factory.create_task_resource(
            task_data=task_data,
            patient_ref="patient-789",
            requester_ref="Practitioner/dr-smith-123",
            owner_ref="Practitioner/nurse-jones-456",
            request_id="test-request-003"
        )

        assert result is not None
        assert result["requester"]["reference"] == "Practitioner/dr-smith-123"
        assert result["owner"]["reference"] == "Practitioner/nurse-jones-456"

    def test_create_task_with_business_status(self, factory):
        """Test creating Task with business status"""
        task_data = {
            "description": "Review lab results and contact patient",
            "status": "in-progress",
            "business_status": "waiting-for-lab-results"
        }

        result = factory.create_task_resource(
            task_data=task_data,
            patient_ref="patient-101",
            request_id="test-request-004"
        )

        assert result is not None
        assert result["businessStatus"]["text"] == "waiting-for-lab-results"

    def test_create_task_with_status_reason(self, factory):
        """Test creating Task with status reason for cancelled task"""
        task_data = {
            "description": "Patient education session",
            "status": "cancelled",
            "status_reason": "Patient discharged early"
        }

        result = factory.create_task_resource(
            task_data=task_data,
            patient_ref="patient-202",
            request_id="test-request-005"
        )

        assert result is not None
        assert result["statusReason"]["text"] == "Patient discharged early"

    def test_create_completed_task_with_output(self, factory):
        """Test creating completed Task with output"""
        task_data = {
            "description": "Medication review completed",
            "status": "completed",
            "output": "No drug interactions found, therapy continued"
        }

        result = factory.create_task_resource(
            task_data=task_data,
            patient_ref="patient-303",
            request_id="test-request-006"
        )

        assert result is not None
        assert result["status"] == "completed"
        assert len(result["output"]) == 1
        assert result["output"][0]["type"]["text"] == "result"
        assert result["output"][0]["valueString"] == "No drug interactions found, therapy continued"

    def test_create_task_with_code(self, factory):
        """Test creating Task with task code"""
        task_data = {
            "description": "Fulfill medication request",
            "status": "requested",
            "code": {
                "system": "http://hl7.org/fhir/CodeSystem/task-code",
                "code": "fulfill",
                "display": "Fulfill the focal request"
            }
        }

        result = factory.create_task_resource(
            task_data=task_data,
            patient_ref="patient-404",
            request_id="test-request-007"
        )

        assert result is not None
        assert "code" in result
        assert result["code"]["coding"][0]["code"] == "fulfill"

    def test_task_status_values(self, factory):
        """Test all valid FHIR Task status values"""
        valid_statuses = ["requested", "accepted", "in-progress", "on-hold", "completed", "cancelled"]

        for status in valid_statuses:
            task_data = {
                "description": f"Task with {status} status",
                "status": status
            }

            result = factory.create_task_resource(
                task_data=task_data,
                patient_ref="patient-500",
                request_id=f"test-status-{status}"
            )

            assert result is not None
            assert result["status"] == status

    def test_fallback_task_creation(self, factory):
        """Test fallback Task creation when FHIR library unavailable"""
        task_data = {
            "description": "Fallback task test",
            "status": "requested"
        }

        # Test fallback method directly
        result = factory._create_fallback_task_resource(
            task_data=task_data,
            patient_ref="patient-fallback",
            request_id="test-fallback"
        )

        assert result is not None
        assert result["resourceType"] == "Task"
        assert result["status"] == "requested"
        assert result["for"]["reference"] == "Patient/patient-fallback"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])