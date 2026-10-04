"""
Regression: EncounterResourceFactory required an input 'class' key, so callers
passing e.g. {"status": "finished"} failed with
"Required field 'class' is missing for Encounter". FHIR R4 Encounter.class is
required on the *output* resource; the factory must default it (AMB) and
accept common input keys/synonyms.
"""

import pytest

from src.nl_fhir.services.fhir.factories import get_factory_registry
from src.nl_fhir.services.fhir.factories.encounter_factory import (
    EncounterResourceFactory,
)
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter

ACT_CODE = "http://terminology.hl7.org/CodeSystem/v3-ActCode"


@pytest.fixture
def encounter_factory():
    factory = get_factory_registry().get_factory("Encounter")
    assert isinstance(factory, EncounterResourceFactory)
    return factory


def test_encounter_without_class_defaults_to_ambulatory(encounter_factory):
    encounter = encounter_factory.create(
        "Encounter", {"status": "finished", "patient_id": "patient-1"}
    )

    assert encounter["class"] == {
        "system": ACT_CODE,
        "code": "AMB",
        "display": "ambulatory",
    }
    assert encounter["status"] == "finished"
    assert encounter["subject"]["reference"] == "Patient/patient-1"


def test_adapter_encounter_without_class():
    """The legacy adapter path used by many callers/tests."""
    encounter = get_factory_adapter().create_encounter_resource(
        {"status": "finished"}, "Patient/patient-1"
    )

    assert encounter["resourceType"] == "Encounter"
    assert encounter["class"]["system"] == ACT_CODE
    assert encounter["class"]["code"] == "AMB"


@pytest.mark.parametrize(
    "data, expected_code, expected_display",
    [
        ({"class": "IMP"}, "IMP", "inpatient encounter"),
        ({"class": "emer"}, "EMER", "emergency"),
        ({"encounter_class": "inpatient"}, "IMP", "inpatient encounter"),
        ({"class_code": "VR"}, "VR", "virtual"),
        ({"class": "telehealth"}, "VR", "virtual"),
        ({"class": "unknown-kind"}, "AMB", "ambulatory"),
        ({"class": {"code": "HH"}}, "HH", "home health"),
    ],
)
def test_encounter_class_input_mapping(encounter_factory, data, expected_code, expected_display):
    encounter = encounter_factory.create(
        "Encounter", {"status": "planned", "patient_id": "p1", **data}
    )

    assert encounter["class"]["system"] == ACT_CODE
    assert encounter["class"]["code"] == expected_code
    assert encounter["class"]["display"] == expected_display
