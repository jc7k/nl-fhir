"""Regression coverage for the repository safety review; no external services."""

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from src.nl_fhir.api.endpoints import fhir_pipeline
from src.nl_fhir.config import settings
from src.nl_fhir.models.request import ClinicalRequestAdvanced
from src.nl_fhir.services import conversion
from src.nl_fhir.services.fhir.hapi_client import HAPIFHIRClient
from src.nl_fhir.services.fhir.factory_adapter import get_fhir_resource_factory
from src.nl_fhir.services.medication_context import medication_context
from src.nl_fhir.services.nlp import entity_extractor
from src.nl_fhir.services.nlp.extractors.medical_entity_extractor import MedicalEntityExtractor


@pytest.mark.parametrize("medication,text,expected", [
    ("metformin", "Aspirin 81 mg daily and metformin 500 mg twice daily.", "500 mg"),
    ("lisinopril", "Give 5 mg lisinopril", "5 mg"),
    ("lorazepam", "Lorazepam 0.5 mg at bedtime", "0.5 mg"),
    ("vancomycin", "Vancomycin 1 g IV; aspirin 81 mg daily", "1 g"),
    ("metformin", "Aspirin 81 mg daily and metformin", "As directed"),
])
def test_dose_belongs_to_medication(medication, text, expected):
    assert conversion.ConversionService()._extract_dosage_from_context(medication, text, "test") == expected


def test_medication_context_stops_at_other_drug_without_punctuation():
    text = "Aspirin daily metformin 500 mg twice daily"
    context = medication_context(text, "aspirin", ["aspirin", "metformin"])
    assert conversion.ConversionService()._extract_dosage_from_context("aspirin", context, "test") == "As directed"


@pytest.mark.parametrize("medication,text,expected", [
    ("acetaminophen", "Acetaminophen 500 mg as needed", "as needed"),
    ("tramadol", "Tramadol 50 mg at bedtime", "at bedtime"),
    ("metformin", "Metformin 500 mg bid", "twice daily"),
    ("metformin", "Metformin 500 mg b.i.d.", "twice daily"),
    ("metformin", "Metformin 500 mg ac", "before meals"),
    ("aspirin", "Aspirin 81 mg daily", "once daily"),
    ("acetaminophen", "Acetaminophen 500 mg", "As needed"),
])
def test_frequency_uses_complete_tokens(medication, text, expected):
    assert conversion.ConversionService()._extract_frequency_from_context(medication, text, "test") == expected


@pytest.fixture
def conversion_run(monkeypatch):
    """Exercise the real orchestration, substituting NLP and FHIR boundaries."""
    factory = Mock()
    for method, resource_type in [
        ("create_patient_resource", "Patient"),
        ("create_practitioner_resource", "Practitioner"),
        ("create_encounter_resource", "Encounter"),
        ("create_medication_request", "MedicationRequest"),
        ("create_condition_resource", "Condition"),
        ("create_service_request", "ServiceRequest"),
    ]:
        getattr(factory, method).return_value = {"resourceType": resource_type, "id": resource_type.lower()}
    monkeypatch.setattr(conversion, "get_fhir_resource_factory", AsyncMock(return_value=factory))
    assembler = Mock()
    assembler.create_transaction_bundle.side_effect = lambda resources, _: {
        "resourceType": "Bundle", "type": "transaction",
        "entry": [{"resource": resource} for resource in resources],
    }
    assembler.optimize_bundle.side_effect = lambda bundle, _: bundle
    assembler.get_bundle_summary.return_value = {}
    monkeypatch.setattr(conversion, "FHIRBundleAssembler", Mock(return_value=assembler))
    monkeypatch.setattr(settings, "observations_enabled", False)
    workflow = Mock()
    workflow.detect_workflow_patterns.return_value = []
    monkeypatch.setattr(conversion, "get_task_workflow_service", AsyncMock(return_value=workflow))

    async def run(entities, text="Synthetic patient receives aspirin 81 mg daily", local_valid=True, remote_valid=True, source="hapi_fhir"):
        nlp = SimpleNamespace(process_clinical_text=AsyncMock(return_value={
            "extracted_entities": {"entities": entities}, "structured_output": {},
        }))
        monkeypatch.setattr(conversion, "get_nlp_pipeline", AsyncMock(return_value=nlp))
        local = Mock()
        local.validate_bundle.return_value = {
            "is_valid": local_valid, "errors": [] if local_valid else ["local-error"],
        }
        monkeypatch.setattr(conversion, "get_fhir_validator", AsyncMock(return_value=local))
        hapi = SimpleNamespace(validate_bundle=AsyncMock(return_value={
            "is_valid": remote_valid, "validation_source": source,
            "errors": [] if remote_valid else ["remote-error"],
        }))
        monkeypatch.setattr(conversion, "get_hapi_client", AsyncMock(return_value=hapi))
        request = ClinicalRequestAdvanced(clinical_text=text, patient_ref="synthetic-private-id")
        response = await conversion.ConversionService().convert_advanced(request, "safe-request-id")
        assert response.fhir_bundle is not None, response.fhir_validation_results
        return response, factory
    return run


@pytest.mark.asyncio
@pytest.mark.parametrize("local,remote,source,expected", [
    (False, True, "fallback", False),
    (False, True, "hapi_fhir", False),
    (True, False, "hapi_fhir", False),
    (True, True, "hapi_fhir", True),
    (True, True, "fallback", True),
])
async def test_remote_validation_cannot_erase_local_failure(conversion_run, local, remote, source, expected):
    response, _ = await conversion_run([], local_valid=local, remote_valid=remote, source=source)
    assert response.fhir_validation_results["is_valid"] is expected
    if not local:
        assert "local-error" in response.fhir_validation_results["errors"]


def test_hapi_fallback_rejects_incomplete_resource():
    result = HAPIFHIRClient()._fallback_validation({
        "resourceType": "Bundle", "type": "transaction",
        "entry": [{"resource": {"resourceType": "MedicationRequest"}}],
    }, "synthetic")
    assert result["is_valid"] is False
    assert result["remote_validation_performed"] is False


@pytest.mark.asyncio
async def test_conversion_logs_do_not_contain_clinical_values(conversion_run, caplog):
    caplog.set_level(logging.INFO, logger=conversion.__name__)
    entities = [
        {"type": "person", "text": "Synthetic Private Person"},
        {"type": "medication", "text": "metformin"},
        {"type": "condition", "text": "diabetes"},
    ]
    await conversion_run(entities, "Synthetic Private Person receives metformin 500 mg twice daily for diabetes")
    messages = "\n".join(r.getMessage() for r in caplog.records if r.name == conversion.__name__)
    for sensitive in ["Synthetic Private Person", "metformin", "diabetes", "synthetic-private-id", "500 mg"]:
        assert sensitive not in messages
    assert "safe-request-id" in messages


@pytest.mark.asyncio
async def test_conversion_keeps_independent_medication_instructions(conversion_run):
    _, factory = await conversion_run(
        [{"type": "medication", "text": "aspirin"}, {"type": "medication", "text": "metformin"}],
        "Aspirin 81 mg qd and metformin 500 mg twice daily.",
    )
    orders = [call.args[0] for call in factory.create_medication_request.call_args_list]
    assert [(o["dosage"], o["frequency"]) for o in orders] == [("81 mg", "once daily"), ("500 mg", "twice daily")]


@pytest.mark.asyncio
async def test_current_mention_does_not_reuse_historical_dose(conversion_run):
    text = "Previously aspirin 81 mg daily. Start aspirin 325 mg daily."
    _, factory = await conversion_run([
        {"type": "medication", "text": "aspirin", "start_char": text.index("aspirin"),
         "attributes": {"clinical_context": {"is_historical": True}}},
        {"type": "medication", "text": "aspirin", "start_char": text.rindex("aspirin")},
    ], text)
    factory.create_medication_request.assert_called_once()
    assert factory.create_medication_request.call_args.args[0]["dosage"] == "325 mg"


@pytest.mark.asyncio
async def test_corrected_doses_reach_real_fhir_resources(conversion_run, monkeypatch):
    monkeypatch.setattr(conversion, "get_fhir_resource_factory", get_fhir_resource_factory)
    response, _ = await conversion_run(
        [{"type": "medication", "text": "aspirin"}, {"type": "medication", "text": "metformin"}],
        "Aspirin 81 mg daily and metformin 500 mg twice daily.",
    )
    medications = [entry["resource"] for entry in response.fhir_bundle["entry"]
                   if entry["resource"]["resourceType"] == "MedicationRequest"]
    assert len(medications) == 2
    assert [m["dosageInstruction"][0]["text"] for m in medications] == ["81 mg", "500 mg"]
    assert [m["dosageInstruction"][0]["timing"]["repeat"]["frequency"] for m in medications] == [1, 2]


@pytest.mark.asyncio
async def test_as_needed_reaches_real_fhir_resource(conversion_run, monkeypatch):
    monkeypatch.setattr(conversion, "get_fhir_resource_factory", get_fhir_resource_factory)
    response, _ = await conversion_run(
        [{"type": "medication", "text": "acetaminophen"}],
        "Acetaminophen 500 mg as needed",
    )
    order = next(entry["resource"] for entry in response.fhir_bundle["entry"]
                 if entry["resource"]["resourceType"] == "MedicationRequest")
    instruction = order["dosageInstruction"][0]
    assert instruction["asNeededBoolean"] is True
    assert instruction["timing"]["code"]["text"] == "as needed"
    assert "before meals" not in str(instruction)


@pytest.mark.asyncio
@pytest.mark.parametrize("flag", ["is_negated", "is_historical", "is_hypothetical", "is_family"])
async def test_non_current_mentions_do_not_create_active_resources(conversion_run, flag):
    entities = [
        {"type": kind, "text": text, "attributes": {"clinical_context": {flag: True}}}
        for kind, text in [("medication", "aspirin"), ("condition", "diabetes"), ("lab_test", "CBC")]
    ]
    entities.append({"type": "medication", "text": "metformin"})
    response, factory = await conversion_run(entities, "Historical aspirin and diabetes. Start metformin 500 mg bid")
    assert factory.create_medication_request.call_count == 1
    assert factory.create_medication_request.call_args.args[0]["medication"] == "metformin"
    factory.create_condition_resource.assert_not_called()
    factory.create_service_request.assert_not_called()
    assert response.extracted_entities["entities"] == entities


def test_medspacy_extension_flags_are_read():
    entity = SimpleNamespace(_=SimpleNamespace(is_negated=True, is_historical=True, is_family=True))
    context = MedicalEntityExtractor()._get_clinical_context(entity)
    assert context["is_negated"] and context["is_historical"] and context["is_family"]


def test_context_survives_entity_adapter(monkeypatch):
    monkeypatch.setattr(entity_extractor, "extract_medical_entities", lambda text: {
        "conditions": [{"text": "diabetes", "start": 3, "end": 11, "clinical_context": {"is_negated": True}}],
    })
    entities = entity_extractor.MedicalEntityExtractor().extract_entities("No diabetes")
    assert entities[0].attributes["clinical_context"]["is_negated"] is True


def test_context_survives_escalation_without_affecting_another_mention():
    result = {"conditions": [{"text": "diabetes", "start": 3}, {"text": "diabetes", "start": 25}]}
    clinical = {"conditions": [{"text": "diabetes", "start": 3, "clinical_context": {"is_family": True}}]}
    result = MedicalEntityExtractor._preserve_clinical_context(result, clinical)
    assert result["conditions"][0]["clinical_context"]["is_family"] is True
    assert "clinical_context" not in result["conditions"][1]


def test_context_survives_llm_without_offsets():
    result = {"conditions": [{"text": "diabetes", "start": 0, "end": 0}]}
    clinical = {"conditions": [{"text": "diabetes", "start": 3, "clinical_context": {"is_negated": True}}]}
    assert MedicalEntityExtractor._preserve_clinical_context(result, clinical)["conditions"][0]["clinical_context"]["is_negated"]


@pytest.mark.parametrize("token,authorization,execute,validate,expected", [
    (None, None, True, True, 503),
    ("", None, True, True, 503),
    ("execution-secret", None, True, True, 401),
    ("execution-secret", "Bearer wrong", True, True, 403),
    ("execution-secret", "Basic wrong", True, True, 401),
    ("execution-secret", "Bearer execution-secret", True, False, 422),
    ("execution-secret", "Bearer execution-secret", True, True, 200),
    (None, None, False, True, 200),
])
def test_http_execution_authorization(monkeypatch, token, authorization, execute, validate, expected):
    monkeypatch.setattr(settings, "fhir_execution_token", SecretStr(token) if token else None)
    result = {
        "request_id": "test", "success": True, "processing_metadata": {},
        "fhir_resources": [], "fhir_bundle": None, "validation_results": None,
        "execution_results": None, "quality_metrics": {}, "bundle_summary_data": {},
        "errors": [], "warnings": [],
    }
    pipeline = SimpleNamespace(process_nlp_to_fhir=AsyncMock(return_value=SimpleNamespace(
        request_id="test", success=True, to_dict=lambda: result,
    )))
    getter = AsyncMock(return_value=pipeline)
    monkeypatch.setattr(fhir_pipeline, "get_unified_fhir_pipeline", getter)
    app = FastAPI()
    app.include_router(fhir_pipeline.router)
    response = TestClient(app).post("/fhir/pipeline", json={
        "nlp_entities": {}, "execute_bundle": execute, "validate_bundle": validate,
    }, headers={"Authorization": authorization} if authorization else {})
    assert response.status_code == expected, response.text
    if expected != 200:
        getter.assert_not_awaited()
    else:
        pipeline.process_nlp_to_fhir.assert_awaited_once()
