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
    assert "Diagnostic report" in data["human_readable_summary"] and "CBC Panel" in data["human_readable_summary"]
    assert "Procedure" in data["human_readable_summary"] and "Chest X-ray" in data["human_readable_summary"]
    assert "ImagingStudy resource" in data["human_readable_summary"]

    safety = data.get("safety_checks")
    assert safety is not None

    # Check that safety analysis is comprehensive
    enhanced = safety.get("enhanced_analysis", {})
    assert "drug_interactions" in enhanced
    assert "contraindications" in enhanced
    assert "clinical_recommendations" in enhanced

    # Warfarin should generate monitoring recommendations
    clinical_recs = enhanced.get("clinical_recommendations", {})
    assert clinical_recs.get("has_recommendations") == True
    recommendations_text = str(clinical_recs.get("recommendations", []))
    assert "warfarin" in recommendations_text.lower() or "vitamin k" in recommendations_text.lower()

    # Risk assessment should be present in enhanced_analysis
    risk_assessment = enhanced.get("risk_assessment", {})
    assert risk_assessment.get("overall_score") is not None
    assert risk_assessment.get("risk_level") is not None


def test_summarize_bundle_feature_disabled_returns_404():
    settings.summarization_enabled = False
    client = TestClient(app)
    payload = {"bundle": make_sample_bundle(), "user_role": "clinician"}
    resp = client.post("/summarize-bundle", json=payload)
    assert resp.status_code == 404
