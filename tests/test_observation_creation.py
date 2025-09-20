import pytest
import asyncio
import sys
sys.path.append('src')

from nl_fhir.services.fhir.resource_factory import FHIRResourceFactory


@pytest.mark.asyncio
async def test_create_basic_observation_quantity():
    factory = FHIRResourceFactory()
    assert factory.initialize() is True

    obs = factory.create_observation_resource(
        observation_data={
            "status": "final",
            "category": "vital-signs",
            "code": {"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"},
            "value": 140,
            "unit": "mmHg",
            "interpretation": "high",
        },
        patient_ref="patient-123",
        request_id="test-obs-1",
    )

    assert obs["resourceType"] == "Observation"
    assert obs["status"] == "final"
    assert obs["subject"]["reference"] == "Patient/patient-123"
    assert obs["code"]["coding"][0]["code"] == "8480-6"
    assert obs.get("valueQuantity", {}).get("value") == 140
    assert obs.get("valueQuantity", {}).get("unit") == "mmHg"
    assert obs.get("valueQuantity", {}).get("system") == "http://unitsofmeasure.org"
    assert obs.get("valueQuantity", {}).get("code") == "mm[Hg]"
    assert obs.get("interpretation", [{}])[0]["coding"][0]["code"] == "H"


@pytest.mark.asyncio
async def test_create_observation_text_value():
    factory = FHIRResourceFactory()
    factory.initialize()

    obs = factory.create_observation_resource(
        observation_data={
            "status": "preliminary",
            "category": "laboratory",
            "code": "718-7",  # Hemoglobin
            "text": "Hemoglobin",
            "value": "normal",
        },
        patient_ref="patient-abc",
        request_id="test-obs-2",
    )

    assert obs["status"] == "preliminary"
    assert obs["code"]["coding"][0]["system"] in ["http://loinc.org", "http://snomed.info/sct"]
    assert obs.get("valueString") == "normal"
