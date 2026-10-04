"""
Regression: EncounterResourceFactory required an input 'class' key, so callers
passing e.g. {"status": "finished"} failed with
"Required field 'class' is missing for Encounter". FHIR R4 Encounter.class is
required on the *output* resource; the factory must default it (AMB) and
accept common input keys/synonyms.
"""

import logging

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


UNRECOGNIZED_CLASS_INPUTS = [
    {"class": "urgent care"},
    {"encounter_class": "made-up-kind"},
    {"class": {"system": ACT_CODE, "display": "no code here"}},
]


@pytest.mark.parametrize("data", UNRECOGNIZED_CLASS_INPUTS)
def test_unrecognized_class_logs_warning_without_raw_value(encounter_factory, caplog, data):
    with caplog.at_level(logging.WARNING, logger="EncounterResourceFactory"):
        encounter = encounter_factory.create(
            "Encounter", {"status": "planned", "patient_id": "p1", **data}, "req-123"
        )

    assert encounter["class"]["code"] == "AMB"
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and "encounter class" in r.getMessage().lower()
    ]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert "AMB" in message
    assert "req-123" in message
    # HIPAA: never echo the supplied clinical text into logs
    for forbidden in ("urgent care", "made-up-kind", "no code here"):
        assert forbidden not in message


@pytest.mark.parametrize(
    "data", [{}, {"class": "IMP"}, {"class": "inpatient"}, {"class": {"code": "HH"}}]
)
def test_recognized_or_missing_class_does_not_warn(encounter_factory, caplog, data):
    with caplog.at_level(logging.WARNING, logger="EncounterResourceFactory"):
        encounter_factory.create(
            "Encounter", {"status": "planned", "patient_id": "p1", **data}, "req-1"
        )

    assert not [r for r in caplog.records if "encounter class" in r.getMessage().lower()]


@pytest.mark.parametrize(
    "data",
    [
        {"class": "urgent care", "class_display": "urgent care"},
        {"class_display": "urgent care"},
    ],
)
def test_defaulted_class_ignores_class_display(encounter_factory, data):
    """A defaulted AMB code must not carry a contradictory caller display."""
    encounter = encounter_factory.create(
        "Encounter", {"status": "planned", "patient_id": "p1", **data}
    )

    assert encounter["class"]["code"] == "AMB"
    assert encounter["class"]["display"] == "ambulatory"


def test_recognized_class_keeps_class_display(encounter_factory):
    encounter = encounter_factory.create(
        "Encounter",
        {
            "status": "planned",
            "patient_id": "p1",
            "class": "IMP",
            "class_display": "inpatient admission",
        },
    )

    assert encounter["class"]["code"] == "IMP"
    assert encounter["class"]["display"] == "inpatient admission"
