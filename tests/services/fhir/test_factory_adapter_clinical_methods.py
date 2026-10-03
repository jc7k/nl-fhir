"""
FactoryAdapter legacy methods used by ConversionService.

conversion.py calls create_service_request / create_condition_resource /
create_diagnostic_report with bare resource ids (not "Type/id"); these tests
pin that calling convention and the resulting FHIR references.
"""

import pytest

from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


@pytest.fixture
def adapter():
    return get_factory_adapter()


def test_create_service_request_from_conversion_args(adapter):
    service_data = {
        "code": "CBC",
        "category": "laboratory",
        "status": "active",
        "intent": "order",
    }

    resource = adapter.create_service_request(
        service_data,
        "patient-1",
        "req-1",
        practitioner_ref="practitioner-1",
        encounter_ref="encounter-1",
    )

    assert resource["resourceType"] == "ServiceRequest"
    assert resource["subject"] == {"reference": "Patient/patient-1"}
    assert resource["requester"] == {"reference": "Practitioner/practitioner-1"}
    assert resource["encounter"] == {"reference": "Encounter/encounter-1"}
    assert resource["code"]["text"].lower() == "cbc"


def test_create_condition_resource_from_conversion_args(adapter):
    condition_data = {
        "name": "hypertension",
        "clinical_status": "active",
        "verification_status": "provisional",
    }

    resource = adapter.create_condition_resource(
        condition_data, "patient-1", "req-1", encounter_ref="encounter-1"
    )

    assert resource["resourceType"] == "Condition"
    assert resource["subject"] == {"reference": "Patient/patient-1"}
    assert resource["encounter"] == {"reference": "Encounter/encounter-1"}


def test_create_diagnostic_report_links_orders_and_results(adapter):
    resource = adapter.create_diagnostic_report(
        {"name": "complete blood count"},
        "patient-1",
        "req-1",
        service_request_refs=["service-1"],
        observation_refs=["obs-1", "obs-2"],
    )

    assert resource["resourceType"] == "DiagnosticReport"
    assert resource["subject"] == {"reference": "Patient/patient-1"}
    assert resource["basedOn"] == [{"reference": "ServiceRequest/service-1"}]
    assert resource["result"] == [
        {"reference": "Observation/obs-1"},
        {"reference": "Observation/obs-2"},
    ]
