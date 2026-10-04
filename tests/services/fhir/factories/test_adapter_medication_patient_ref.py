"""
Tests for FactoryAdapter.create_medication_request patient references.
Regression: legacy callers pass a bare patient id ("patient-123"), which the
adapter forwarded verbatim, so MedicationRequest.subject failed
reference_format validation and the resource was not created.
"""

import pytest

from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


@pytest.mark.parametrize("patient_ref", ["patient-123", "Patient/patient-123"])
def test_create_medication_request_normalizes_patient_ref(patient_ref):
    med_request = get_factory_adapter().create_medication_request(
        {"medication_name": "vancomycin", "dosage": "1g", "route": "IV"},
        patient_ref,
    )

    assert med_request["subject"]["reference"] == "Patient/patient-123"
