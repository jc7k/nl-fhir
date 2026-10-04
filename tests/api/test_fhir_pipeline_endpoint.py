"""
Tests for the unified FHIR pipeline (POST /fhir/pipeline).
Regression: UnifiedFHIRPipeline.initialize() read `resource_factory.initialized`,
which FactoryAdapter did not expose (it only had `_initialized`). Initialization
always failed, the pipeline never became ready, and every request re-ran it.
"""

from fastapi.testclient import TestClient

from src.nl_fhir.main import app
from src.nl_fhir.services.fhir import unified_pipeline
from src.nl_fhir.services.fhir.factory_adapter import FactoryAdapter
from src.nl_fhir.services.fhir.unified_pipeline import UnifiedFHIRPipeline

NLP_ENTITIES = {
    "patient_info": {"patient_ref": "PT-pipeline-1"},
    "medications": [{"name": "vancomycin", "dosage": "1g", "route": "IV", "frequency": "q12h"}],
    "conditions": [{"name": "sepsis"}],
    "procedures": [{"name": "blood culture"}],
}


def test_factory_adapter_exposes_initialized_flag():
    adapter = FactoryAdapter()
    assert adapter.initialized is False

    adapter.initialize()

    assert adapter.initialized is True


async def test_unified_pipeline_initializes():
    pipeline = UnifiedFHIRPipeline()

    assert await pipeline.initialize() is True
    assert pipeline.initialized is True
    assert pipeline.get_pipeline_status()["service_status"]["resource_factory"] is True


def test_pipeline_endpoint_creates_resources():
    response = TestClient(app).post(
        "/fhir/pipeline", json={"nlp_entities": NLP_ENTITIES, "validate_bundle": False}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True, body["errors"]
    assert body["errors"] == []
    resource_types = sorted(r["resourceType"] for r in body["fhir_resources"])
    assert resource_types == ["Condition", "MedicationRequest", "Patient", "ServiceRequest"]
    assert body["fhir_bundle"]["type"] == "transaction"
    # The shared pipeline the endpoint used must have finished initializing
    assert unified_pipeline._unified_pipeline.initialized is True
