"""
Regression tests: Transformers NER tier must not leak numpy scalars into entity dicts.

Hugging Face token-classification pipelines return ``score`` as ``numpy.float32``
(and, depending on the transformers version, ``start``/``end`` as numpy ints).
Those values used to be copied verbatim into the entity dicts that end up in
``ConvertResponseAdvanced.extracted_entities``, so FastAPI failed with
``PydanticSerializationError: Unable to serialize unknown type: numpy.float32``
and /convert returned HTTP 500 even though conversion had succeeded.

The HF pipeline is mocked here; no model is loaded or downloaded.
"""

import json

import numpy as np
import pytest

from nl_fhir.services.nlp.extractors.medical_entity_extractor import MedicalEntityExtractor

TEXT = "Start patient on 500mg Metformin twice daily for type 2 diabetes. Order CBC."


def _fake_hf_output():
    """Mimic ``pipeline("ner", aggregation_strategy="simple")`` output types."""
    return [
        {
            "entity_group": "MEDICATION",
            "score": np.float32(0.9134),
            "word": "Metformin",
            "start": np.int64(23),
            "end": np.int64(32),
        },
        {
            "entity_group": "DOSAGE",
            "score": np.float32(0.8148),
            "word": "500mg",
            "start": 17,
            "end": 22,
        },
        {
            "entity_group": "DISEASE_DISORDER",
            "score": np.float32(0.7421),
            "word": "type 2 diabetes",
            "start": np.int32(49),
            "end": np.int32(64),
        },
        {
            "entity_group": "DIAGNOSTIC_PROCEDURE",
            "score": np.float32(0.6901),
            "word": "CBC",
            "start": 72,
            "end": 75,
        },
    ]


def _fake_pipeline(text):
    assert text == TEXT
    return _fake_hf_output()


@pytest.fixture
def extractor():
    # Model managers are lazy, so constructing the extractor does not load any model.
    return MedicalEntityExtractor()


def _all_entities(result):
    for category, entities in result.items():
        for entity in entities:
            yield category, entity


def test_transformer_entities_use_builtin_numeric_types(extractor):
    result = extractor._extract_with_transformers(TEXT, _fake_pipeline)

    entities = list(_all_entities(result))
    assert len(entities) == 4, result

    for category, entity in entities:
        assert type(entity["confidence"]) is float, (category, entity)
        assert type(entity["start"]) is int, (category, entity)
        assert type(entity["end"]) is int, (category, entity)
        assert entity["method"] == "transformers_ner"


def test_transformer_entities_preserve_values(extractor):
    result = extractor._extract_with_transformers(TEXT, _fake_pipeline)

    medication = result["medications"][0]
    assert medication["text"] == "Metformin"
    assert medication["confidence"] == pytest.approx(0.9134, abs=1e-6)
    assert (medication["start"], medication["end"]) == (23, 32)

    assert result["lab_tests"][0]["text"] == "CBC"
    assert result["conditions"][0]["text"] == "type 2 diabetes"


def test_transformer_entities_are_json_serializable(extractor):
    result = extractor._extract_with_transformers(TEXT, _fake_pipeline)

    # Default json encoder has no numpy support; this is what used to blow up.
    encoded = json.dumps(result)
    decoded = json.loads(encoded)
    assert decoded["medications"][0]["confidence"] == pytest.approx(0.9134, abs=1e-6)


def test_numpy_score_still_passes_quality_thresholds(extractor):
    """Casting must happen before the confidence threshold filter, not after."""
    low_confidence = [
        {
            "entity_group": "MEDICATION",
            "score": np.float32(0.55),  # below the 0.6 medication threshold
            "word": "Metformin",
            "start": 23,
            "end": 32,
        }
    ]
    result = extractor._extract_with_transformers(TEXT, lambda _text: low_confidence)
    assert result["medications"] == []
