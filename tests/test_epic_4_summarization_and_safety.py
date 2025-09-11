from fastapi.testclient import TestClient

from src.nl_fhir.main import app
from src.nl_fhir.config import settings


def make_sample_bundle():
    return {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "medicationCodeableConcept": {"text": "Warfarin 2mg tablet"},
                    "dosageInstruction": [
                        {
                            "text": "Take 1 tablet daily",
                            "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                        }
                    ],
                }
            },
            {
                "resource": {
                    "resourceType": "ServiceRequest",
                    "code": {"text": "Complete Blood Count"},
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"text": "Serum Potassium"},
                    "valueQuantity": {"value": 6.2, "unit": "mmol/L"},
                    "interpretation": {"coding": [{"code": "H", "display": "High"}]},
                }
            },
            {
                "resource": {
                    "resourceType": "DiagnosticReport",
                    "code": {"text": "CBC Panel"},
                    "conclusion": "Mild anemia",
                }
            },
            {
                "resource": {
                    "resourceType": "Procedure",
                    "code": {"text": "Chest X-ray"}
                }
            },
            {
                "resource": {
                    "resourceType": "ImagingStudy",
                    "series": [{"modality": {"code": "XR", "display": "X-ray"}}]
                }
            },
        ],
    }


def test_summarize_bundle_with_safety_checks():
    # Enable features
    settings.summarization_enabled = True
    settings.safety_validation_enabled = True

    client = TestClient(app)
    payload = {"bundle": make_sample_bundle(), "user_role": "clinician"}
    resp = client.post("/summarize-bundle", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "Warfarin" in data["human_readable_summary"]
    assert data["bundle_summary"]["resource_counts"]["MedicationRequest"] == 1
    # New resources present in summary text
    assert "Observation: Serum Potassium" in data["human_readable_summary"]
    assert "Diagnostic report: CBC Panel" in data["human_readable_summary"]
    assert "Procedure: Chest X-ray." in data["human_readable_summary"]
    assert "Imaging study:" in data["human_readable_summary"]

    safety = data.get("safety_checks")
    assert safety is not None
    issues = " ".join(safety.get("issues", []))
    assert "high-risk" in issues.lower()
    assert "warfarin" in issues.lower()
    # Observation high flag surfaces as warning
    warnings = " ".join(safety.get("warnings", []))
    assert "Observation flagged as" in warnings


def test_summarize_bundle_feature_disabled_returns_404():
    settings.summarization_enabled = False
    client = TestClient(app)
    payload = {"bundle": make_sample_bundle(), "user_role": "clinician"}
    resp = client.post("/summarize-bundle", json=payload)
    assert resp.status_code == 404
