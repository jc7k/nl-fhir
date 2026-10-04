"""
Tests for per-entity resource creation in UnifiedFHIRPipeline.
Regression: _create_fhir_resources wrapped every entity in one try, so a single
entity the factory rejected dropped all resources and the request failed with
"No FHIR resources could be created". Failures are now reported per entity, and
a bundle with failed entities is never executed.
"""

from unittest.mock import AsyncMock

from src.nl_fhir.services.fhir.unified_pipeline import UnifiedFHIRPipeline

GOOD_ENTITIES = {
    "patient_info": {"patient_ref": "PT-partial-1"},
    "conditions": [{"name": "sepsis"}],
    "procedures": [{"name": "blood culture"}],
}
# A medication without any accepted name key is rejected by the factory
BAD_MEDICATION = {"dosage": "1g", "route": "IV"}


async def _pipeline() -> UnifiedFHIRPipeline:
    pipeline = UnifiedFHIRPipeline()
    await pipeline.initialize()
    return pipeline


async def test_failed_entity_keeps_other_resources():
    pipeline = await _pipeline()
    entities = {**GOOD_ENTITIES, "medications": [{"name": "vancomycin"}, BAD_MEDICATION]}

    result = await pipeline.process_nlp_to_fhir(entities, validate_bundle=False)

    resource_types = sorted(r["resourceType"] for r in result.fhir_resources)
    assert resource_types == ["Condition", "MedicationRequest", "Patient", "ServiceRequest"]
    assert len(result.errors) == 1
    assert result.errors[0].startswith("Failed to create FHIR resource for medications[1]")
    assert result.fhir_bundle is not None
    assert result.success is False


async def test_all_entities_valid_has_no_errors():
    pipeline = await _pipeline()
    entities = {**GOOD_ENTITIES, "medications": [{"name": "vancomycin"}]}

    result = await pipeline.process_nlp_to_fhir(entities, validate_bundle=False)

    assert result.errors == []
    assert len(result.fhir_resources) == 4


async def test_partial_bundle_is_not_executed():
    pipeline = await _pipeline()
    pipeline._validate_fhir_bundle = AsyncMock(return_value={"is_valid": True})
    pipeline._execute_fhir_bundle = AsyncMock(return_value={"success": True})
    entities = {**GOOD_ENTITIES, "medications": [BAD_MEDICATION]}

    result = await pipeline.process_nlp_to_fhir(entities, validate_bundle=True, execute_bundle=True)

    pipeline._execute_fhir_bundle.assert_not_awaited()
    assert result.execution_results is None
    assert "Bundle not executed: some NLP entities failed to convert" in result.warnings
    assert result.success is False


async def test_complete_valid_bundle_is_executed():
    pipeline = await _pipeline()
    pipeline._validate_fhir_bundle = AsyncMock(return_value={"is_valid": True})
    pipeline._execute_fhir_bundle = AsyncMock(return_value={"success": True})
    entities = {**GOOD_ENTITIES, "medications": [{"name": "vancomycin"}]}

    result = await pipeline.process_nlp_to_fhir(entities, validate_bundle=True, execute_bundle=True)

    pipeline._execute_fhir_bundle.assert_awaited_once()
    assert result.execution_results == {"success": True}
