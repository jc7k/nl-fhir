"""
Tests for TaskResourceFactory - Epic TW-001: Task Workflow Integration
Regression: conversion.py calls create_task_resource, which was lost with the
legacy factory, so workflow Tasks were silently dropped from bundles.
"""

import pytest

from src.nl_fhir.services.fhir.factories import get_factory_registry
from src.nl_fhir.services.fhir.factories.task_factory import TaskResourceFactory
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


@pytest.fixture
def task_factory():
    """Get Task factory instance"""
    return get_factory_registry().get_factory("Task")


def test_registry_maps_task_to_real_factory(task_factory):
    """Task must not fall back to MockResourceFactory"""
    assert isinstance(task_factory, TaskResourceFactory)


def test_create_task_with_all_references(task_factory):
    task = task_factory.create(
        "Task",
        {
            "description": "Monitor for red man syndrome",
            "status": "requested",
            "priority": "routine",
            "patient_id": "Patient/patient-12345",
            "focus_ref": "MedicationRequest/med-1",
            "requester_ref": "Practitioner/ordering-provider",
            "owner_ref": "Practitioner/nurse",
            "code": {
                "system": "http://snomed.info/sct",
                "code": "182836005",
                "display": "Review of medication",
            },
        },
        "req-task-001",
    )

    assert task["resourceType"] == "Task"
    assert task["status"] == "requested"
    assert task["intent"] == "order"
    assert task["priority"] == "routine"
    assert task["for"] == {"reference": "Patient/patient-12345"}
    assert task["focus"] == {"reference": "MedicationRequest/med-1"}
    assert task["requester"] == {"reference": "Practitioner/ordering-provider"}
    assert task["owner"] == {"reference": "Practitioner/nurse"}
    assert task["code"]["coding"][0]["code"] == "182836005"
    assert task["code"]["text"] == "Review of medication"
    assert "authoredOn" in task and "lastModified" in task


def test_task_meta_is_fhir_compliant(task_factory):
    """Only standard meta elements (no base-class 'factory'/'created_at')"""
    task = task_factory.create("Task", {"patient_id": "patient-1"}, "req-task-002")

    assert set(task["meta"]) == {"tag"}
    assert {"system": "http://nl-fhir.io/request-id", "code": "req-task-002"} in task["meta"]["tag"]


def test_status_dependent_fields(task_factory):
    cancelled = task_factory.create(
        "Task",
        {
            "patient_id": "patient-1",
            "status": "cancelled",
            "status_reason": "Patient discharged",
            "output": "ignored",
        },
    )
    assert cancelled["statusReason"] == {"text": "Patient discharged"}
    assert "output" not in cancelled

    requested = task_factory.create(
        "Task", {"patient_id": "patient-1", "status": "requested", "status_reason": "ignored"}
    )
    assert "statusReason" not in requested


def test_missing_patient_raises(task_factory):
    with pytest.raises(ValueError, match="patient_id"):
        task_factory.create("Task", {"description": "No patient"})


def test_adapter_create_task_resource_matches_conversion_call():
    """Same keyword call shape as services/conversion.py"""
    task = get_factory_adapter().create_task_resource(
        task_data={"description": "Review lab results", "status": "requested"},
        patient_ref="patient-789",
        focus_ref="ServiceRequest/sr-1",
        requester_ref="Practitioner/ordering-provider",
        owner_ref="Practitioner/nurse",
        request_id="req-task-003",
    )

    assert task["resourceType"] == "Task"
    assert task["for"] == {"reference": "Patient/patient-789"}
    assert task["focus"] == {"reference": "ServiceRequest/sr-1"}
    assert task["owner"] == {"reference": "Practitioner/nurse"}
