"""
Regression: every factory must emit a FHIR R4-compliant ``meta``.

BaseResourceFactory._add_metadata used to write non-FHIR keys ('factory',
'created_at' without timezone, 'version', 'request_id') into meta, and
subclasses added more ('creation_time_ms'). FHIR R4 Meta allows only
versionId, lastUpdated, source, profile, security and tag.
"""

import re

import pytest

from src.nl_fhir.services.fhir.factories.careplan_factory import CarePlanResourceFactory
from src.nl_fhir.services.fhir.factories.clinical_factory import ClinicalResourceFactory
from src.nl_fhir.services.fhir.factories.coders import CoderRegistry
from src.nl_fhir.services.fhir.factories.device_factory import DeviceResourceFactory
from src.nl_fhir.services.fhir.factories.encounter_factory import EncounterResourceFactory
from src.nl_fhir.services.fhir.factories.medication_factory import MedicationResourceFactory
from src.nl_fhir.services.fhir.factories.patient_factory import PatientResourceFactory
from src.nl_fhir.services.fhir.factories.references import ReferenceManager
from src.nl_fhir.services.fhir.factories.validators import ValidatorRegistry

FHIR_META_KEYS = {
    "id",
    "extension",
    "versionId",
    "lastUpdated",
    "source",
    "profile",
    "security",
    "tag",
}
# FHIR R4 instant: full date-time with seconds and a mandatory timezone
INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")

CASES = [
    (ClinicalResourceFactory, "Observation", {"name": "Heart rate", "patient_id": "patient-123"}),
    (
        CarePlanResourceFactory,
        "CarePlan",
        {"patient_id": "patient-123", "title": "Plan", "status": "active", "intent": "plan"},
    ),
    (
        EncounterResourceFactory,
        "Encounter",
        {"patient_id": "patient-123", "status": "finished", "class": "AMB"},
    ),
    (PatientResourceFactory, "Patient", {"name": "John Doe", "gender": "male"}),
    (DeviceResourceFactory, "Device", {"name": "IV pump"}),
    (
        MedicationResourceFactory,
        "MedicationRequest",
        {"medication": "aspirin", "patient_id": "patient-123"},
    ),
]


@pytest.mark.parametrize(
    "factory_cls,resource_type,data", CASES, ids=[c[0].__name__ for c in CASES]
)
def test_factory_meta_is_fhir_r4_compliant(factory_cls, resource_type, data):
    factory = factory_cls(
        validators=ValidatorRegistry(),
        coders=CoderRegistry(),
        reference_manager=ReferenceManager(),
    )
    resource = factory.create(resource_type, data, "req-42")
    meta = resource["meta"]

    assert set(meta) <= FHIR_META_KEYS, f"non-FHIR meta keys: {set(meta) - FHIR_META_KEYS}"
    assert INSTANT_RE.match(meta["lastUpdated"]), meta["lastUpdated"]

    for coding in meta.get("tag", []) + meta.get("security", []):
        assert set(coding) <= {"system", "version", "code", "display", "userSelected"}
        assert coding["system"].startswith("http")

    # Provenance previously stored in non-FHIR keys is kept as tags
    tags = {(t["system"], t["code"]) for t in meta["tag"]}
    assert ("http://nl-fhir.io/factory", factory_cls.__name__) in tags
    assert ("http://nl-fhir.io/request-id", "req-42") in tags
