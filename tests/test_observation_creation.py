import pytest
import asyncio
import sys
sys.path.append('src')

from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


@pytest.mark.asyncio
async def test_create_basic_observation_quantity():
    factory = get_factory_adapter()
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
    factory = get_factory_adapter()
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


@pytest.mark.asyncio
async def test_ucum_temperature_and_heart_rate_codes():
    factory = get_factory_adapter()
    factory.initialize()

    # Temperature in Fahrenheit → [degF]
    obs_temp = factory.create_observation_resource(
        observation_data={
            "status": "final",
            "category": "vital-signs",
            "code": {"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"},
            "value": 100.2,
            "unit": "F",
        },
        patient_ref="patient-xyz",
        request_id="test-obs-temp",
    )
    vq_t = obs_temp.get("valueQuantity", {})
    assert vq_t.get("system") == "http://unitsofmeasure.org"
    assert vq_t.get("code") == "[degF]"

    # Heart rate → /min
    obs_hr = factory.create_observation_resource(
        observation_data={
            "status": "final",
            "category": "vital-signs",
            "code": {"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"},
            "value": 72,
            "unit": "beats/min",
        },
        patient_ref="patient-xyz",
        request_id="test-obs-hr",
    )
    vq_hr = obs_hr.get("valueQuantity", {})
    assert vq_hr.get("system") == "http://unitsofmeasure.org"
    assert vq_hr.get("code") == "/min"


@pytest.mark.asyncio
async def test_ucum_weight_codes_kg_and_lb():
    factory = get_factory_adapter()
    factory.initialize()

    # Weight in kg → kg
    obs_wt_kg = factory.create_observation_resource(
        observation_data={
            "status": "final",
            "category": "vital-signs",
            "code": {"system": "http://loinc.org", "code": "29463-7", "display": "Body weight"},
            "value": 70,
            "unit": "kg",
        },
        patient_ref="patient-xyz",
        request_id="test-obs-weight-kg",
    )
    vq_kg = obs_wt_kg.get("valueQuantity", {})
    assert vq_kg.get("system") == "http://unitsofmeasure.org"
    assert vq_kg.get("code") == "kg"
    assert vq_kg.get("unit") == "kg"

    # Weight in lb → [lb_av]
    obs_wt_lb = factory.create_observation_resource(
        observation_data={
            "status": "final",
            "category": "vital-signs",
            "code": {"system": "http://loinc.org", "code": "29463-7", "display": "Body weight"},
            "value": 150,
            "unit": "lb",
        },
        patient_ref="patient-xyz",
        request_id="test-obs-weight-lb",
    )
    vq_lb = obs_wt_lb.get("valueQuantity", {})
    assert vq_lb.get("system") == "http://unitsofmeasure.org"
    assert vq_lb.get("code") == "[lb_av]"
    assert vq_lb.get("unit") == "lb"
