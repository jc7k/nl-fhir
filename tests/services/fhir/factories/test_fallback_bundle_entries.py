"""
Regression: when one resource fails R4B validation, _create_fhir_bundle falls
back to a dict bundle, but the entries that did validate were left as
BundleEntry model objects. optimize_bundle then failed with "'BundleEntry'
object has no attribute 'get'" and the HAPI client failed with "Object of type
BundleEntry is not JSON serializable".

The fallback bundle must contain only plain FHIR JSON dicts.
"""

import json

from src.nl_fhir.services.fhir.bundle_assembler import FHIRBundleAssembler

PATIENT = {
    "resourceType": "Patient",
    "id": "pat-1",
    "gender": "female",
    "birthDate": "1980-01-01",
}
# Practitioner has no 'status' element in R4, so R4B rejects this entry
INVALID_PRACTITIONER = {
    "resourceType": "Practitioner",
    "id": "prac-1",
    "status": "active",
    "name": [{"family": "Smith"}],
}


def _fallback_bundle():
    assembler = FHIRBundleAssembler()
    assembler.initialize()
    return assembler, assembler.create_transaction_bundle(
        [PATIENT, INVALID_PRACTITIONER], "req-fallback"
    )


def test_fallback_bundle_entries_are_plain_dicts():
    _, bundle = _fallback_bundle()

    assert bundle["resourceType"] == "Bundle"
    assert len(bundle["entry"]) == 2
    assert all(isinstance(entry, dict) for entry in bundle["entry"])
    resources = {e["resource"]["resourceType"]: e["resource"] for e in bundle["entry"]}
    assert resources["Patient"]["birthDate"] == "1980-01-01"
    assert resources["Practitioner"] == INVALID_PRACTITIONER


def test_fallback_bundle_is_json_serializable():
    _, bundle = _fallback_bundle()

    round_tripped = json.loads(json.dumps(bundle))

    assert round_tripped["entry"][0]["request"] == {"method": "POST", "url": "Patient"}


def test_fallback_bundle_can_be_optimized():
    assembler, bundle = _fallback_bundle()

    optimized = assembler.optimize_bundle(bundle, "req-fallback")

    assert optimized is not bundle
    assert [e["resource"]["resourceType"] for e in optimized["entry"]] == [
        "Patient",
        "Practitioner",
    ]
