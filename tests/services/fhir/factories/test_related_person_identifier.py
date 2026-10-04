"""Regression: RelatedPerson creation must not fail identifier_format validation.

PatientResourceFactory._create_related_person wraps a plain-string identifier
as ``{"system": "urn:ietf:rfc:3986", "value": ...}``. ValidatorRegistry's URI
check only accepted http(s) URLs, so every URN system (valid FHIR R4 ``uri``)
failed ``identifier_format`` / ``coding_format`` validation and creation raised.
"""

import pytest

from nl_fhir.services.fhir.factories.coders import CoderRegistry
from nl_fhir.services.fhir.factories.patient_factory import PatientResourceFactory
from nl_fhir.services.fhir.factories.references import ReferenceManager
from nl_fhir.services.fhir.factories.validators import ValidatorRegistry


@pytest.fixture
def factory():
    return PatientResourceFactory(
        validators=ValidatorRegistry(),
        coders=CoderRegistry(),
        reference_manager=ReferenceManager(),
    )


def test_related_person_with_string_identifier_is_created(factory):
    result = factory.create(
        "RelatedPerson",
        {"identifier": "RP-2024-001", "patient": "patient-123", "relationship": "spouse"},
    )

    assert result["resourceType"] == "RelatedPerson"
    assert result["identifier"] == [{"system": "urn:ietf:rfc:3986", "value": "RP-2024-001"}]
    assert result["patient"] == {"reference": "Patient/patient-123"}


def test_related_person_with_communication_language_is_created(factory):
    result = factory.create(
        "RelatedPerson",
        {"patient": "patient-123", "communication": {"language": "es-ES", "preferred": True}},
    )

    coding = result["communication"][0]["language"]["coding"][0]
    assert coding["system"] == "urn:ietf:bcp:47"
    assert coding["code"] == "es-ES"


@pytest.mark.parametrize(
    "system",
    [
        "urn:ietf:rfc:3986",
        "urn:oid:2.16.840.1.113883.4.1",
        "urn:uuid:53fefa32-fcbb-4ff8-8a92-55ee120877b7",
        "urn:ietf:bcp:47",
        "http://hl7.org/fhir/sid/us-ssn",
    ],
)
def test_identifier_format_accepts_fhir_uri_systems(system):
    validators = ValidatorRegistry()
    resource = {"resourceType": "RelatedPerson", "identifier": [{"system": system, "value": "x1"}]}

    assert validators.validate_fhir_r4(resource), validators.get_validation_errors()


@pytest.mark.parametrize("system", ["not a uri", "urn:", "urn:ietf", "urn:has space:x"])
def test_identifier_format_still_rejects_malformed_systems(system):
    validators = ValidatorRegistry()
    resource = {"resourceType": "RelatedPerson", "identifier": [{"system": system, "value": "x1"}]}

    assert not validators.validate_fhir_r4(resource)
