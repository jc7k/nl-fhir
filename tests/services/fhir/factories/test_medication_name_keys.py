"""
Tests for MedicationResourceFactory medication name keys.
Regression: the required-field check only accepted 'medication_name', while the
builders (and legacy FactoryAdapter callers) also use 'name' and 'medication',
so those MedicationRequests were rejected and dropped from bundles.
"""

import pytest

from src.nl_fhir.services.fhir.factories import get_factory_registry
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


@pytest.fixture
def medication_factory():
    """Get MedicationRequest factory instance"""
    return get_factory_registry().get_factory("MedicationRequest")


@pytest.mark.parametrize("key", ["medication_name", "name", "medication"])
def test_medication_request_accepts_name_key(medication_factory, key):
    med_request = medication_factory.create(
        "MedicationRequest",
        {key: "vancomycin", "patient_ref": "Patient/patient-12345"},
    )

    assert med_request["resourceType"] == "MedicationRequest"
    assert med_request["medicationCodeableConcept"]["text"] == "vancomycin"


def test_medication_request_without_name_is_rejected(medication_factory):
    with pytest.raises(ValueError, match="medication_name"):
        medication_factory.create(
            "MedicationRequest", {"dosage": "1g", "patient_ref": "Patient/patient-12345"}
        )


def test_medication_administration_still_requires_patient_id(medication_factory):
    with pytest.raises(ValueError, match="patient_id"):
        medication_factory.create("MedicationAdministration", {"name": "vancomycin"})


def test_adapter_create_medication_request_with_legacy_name_key():
    """Legacy callers pass {'name': ...} through FactoryAdapter"""
    med_request = get_factory_adapter().create_medication_request(
        {"name": "vancomycin", "dosage": "1g", "route": "IV"},
        "Patient/patient-12345",
    )

    assert med_request["medicationCodeableConcept"]["text"] == "vancomycin"
    assert med_request["subject"]["reference"] == "Patient/patient-12345"
