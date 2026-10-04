"""
Regression: bundle_assembler and validator imported fhir.resources' default
models, which are FHIR R5 in fhir.resources >= 7. Valid R4 resources were
rejected (Encounter.class must be a list, MedicationRequest.medication[x] and
CodeableConcept.text not permitted), so every bundle silently fell back to an
unvalidated dict and the validator reported false structural errors.

They must use the R4B models, and model-based bundles must serialize to FHIR
JSON (dates as strings, 'class' alias) so they can be sent to HAPI.
"""

import json
import logging

import pytest

from src.nl_fhir.services.fhir.bundle_assembler import FHIRBundleAssembler
from src.nl_fhir.services.fhir.validator import FHIRValidator

ENCOUNTER = {
    "resourceType": "Encounter",
    "id": "enc-1",
    "status": "in-progress",
    "class": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
    },
    "subject": {"reference": "Patient/pat-1"},
}
MEDICATION_REQUEST = {
    "resourceType": "MedicationRequest",
    "id": "mr-1",
    "status": "active",
    "intent": "order",
    "medicationCodeableConcept": {"text": "amoxicillin 500 mg"},
    "subject": {"reference": "Patient/pat-1"},
}
SERVICE_REQUEST = {
    "resourceType": "ServiceRequest",
    "id": "sr-1",
    "status": "active",
    "intent": "order",
    "code": {"text": "CBC"},
    "subject": {"reference": "Patient/pat-1"},
}
PATIENT = {
    "resourceType": "Patient",
    "id": "pat-1",
    "gender": "female",
    "birthDate": "1980-01-01",
}
R4_RESOURCES = [PATIENT, ENCOUNTER, MEDICATION_REQUEST, SERVICE_REQUEST]


@pytest.mark.parametrize("resource", R4_RESOURCES, ids=lambda r: r["resourceType"])
def test_validator_accepts_valid_r4_resource(resource):
    validator = FHIRValidator()
    validator.initialize()

    result = validator.validate_resource(resource, "req-r4")

    structure_errors = [
        issue
        for issue in result["issues"]
        if issue.get("type") == "structure" and issue.get("severity") == "error"
    ]
    assert structure_errors == []


def test_transaction_bundle_uses_r4_models_without_fallback(caplog):
    assembler = FHIRBundleAssembler()
    assembler.initialize()

    with caplog.at_level(logging.WARNING):
        bundle = assembler.create_transaction_bundle(R4_RESOURCES, "req-r4")

    assert "creation failed" not in caplog.text
    # Must be plain FHIR JSON, ready to send to HAPI
    round_tripped = json.loads(json.dumps(bundle))
    resources = {e["resource"]["resourceType"]: e["resource"] for e in round_tripped["entry"]}
    assert resources["Encounter"]["class"] == ENCOUNTER["class"]
    assert resources["Patient"]["birthDate"] == "1980-01-01"
    assert resources["MedicationRequest"]["medicationCodeableConcept"] == {
        "text": "amoxicillin 500 mg"
    }
