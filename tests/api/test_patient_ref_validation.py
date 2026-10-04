"""
Tests for ClinicalRequest.patient_ref validation.
Regression: the request pattern accepted '_' and arbitrary '/' segments, which
are not valid in FHIR ids, so such refs passed the API and then failed reference
validation downstream. patient_ref must now be a FHIR id or Patient/<id>.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.nl_fhir.main import app
from src.nl_fhir.models.request import ClinicalRequest

CLINICAL_TEXT = "Order CBC with differential"


@pytest.mark.parametrize(
    "patient_ref",
    ["PT-123", "patient.123", "Patient/test-123", "Patient/a.b-1", "A" * 64],
)
def test_fhir_id_patient_ref_is_accepted(patient_ref):
    request = ClinicalRequest(clinical_text=CLINICAL_TEXT, patient_ref=patient_ref)

    assert request.patient_ref == patient_ref


@pytest.mark.parametrize(
    "patient_ref",
    [
        "PT_123",
        "Patient/PT_123",
        "Practitioner/123",
        "Patient/a/b",
        "Patient/",
        "A" * 65,
        "PT-123<>",
    ],
)
def test_non_fhir_id_patient_ref_is_rejected(patient_ref):
    with pytest.raises(ValidationError):
        ClinicalRequest(clinical_text=CLINICAL_TEXT, patient_ref=patient_ref)


def test_empty_patient_ref_becomes_none():
    request = ClinicalRequest(clinical_text=CLINICAL_TEXT, patient_ref="")

    assert request.patient_ref is None


def test_convert_rejects_underscore_patient_ref_with_422():
    response = TestClient(app).post(
        "/convert", json={"clinical_text": CLINICAL_TEXT, "patient_ref": "PT_123"}
    )

    assert response.status_code == 422
