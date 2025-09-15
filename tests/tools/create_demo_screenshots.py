#!/usr/bin/env python3
"""
Create demo screenshots/visualizations for LinkedIn post
"""

import json
from datetime import datetime

def create_input_demo():
    """Create demo showing clinical input"""

    clinical_note = """Patient Emma Rodriguez, 67-year-old female, presents to ED with acute chest pain and shortness of breath.
Started on dual antiplatelet therapy: aspirin 81mg daily and clopidogrel 75mg twice daily for acute coronary syndrome.
Also initiating atorvastatin 40mg once daily at bedtime for hyperlipidemia.
Patient has history of type 2 diabetes - continue metformin 500mg twice daily with meals.
For hypertension, start lisinopril 10mg once daily, monitor BP closely.
Order CBC, comprehensive metabolic panel, lipid panel, and troponin levels STAT."""

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NL-FHIR: Clinical Input Demo</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .title {{ color: #2c3e50; font-size: 32px; font-weight: 700; margin-bottom: 10px; }}
        .subtitle {{ color: #7f8c8d; font-size: 18px; }}
        .input-section {{ background: #f8f9fa; padding: 25px; border-radius: 8px; border-left: 4px solid #3498db; }}
        .label {{ color: #2c3e50; font-weight: 600; margin-bottom: 15px; font-size: 16px; }}
        .clinical-text {{ background: white; padding: 20px; border-radius: 6px; font-size: 16px; line-height: 1.6; color: #34495e; border: 1px solid #dee2e6; }}
        .stats {{ display: flex; justify-content: space-around; margin-top: 25px; }}
        .stat {{ text-align: center; }}
        .stat-number {{ font-size: 24px; font-weight: 700; color: #3498db; }}
        .stat-label {{ color: #7f8c8d; font-size: 14px; }}
        .highlight {{ background: #fff3cd; padding: 2px 4px; border-radius: 3px; }}
        .footer {{ text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🏥 NL-FHIR Converter</div>
            <div class="subtitle">Transform Clinical Notes → FHIR R4 Bundles</div>
        </div>

        <div class="input-section">
            <div class="label">📝 Clinical Note Input:</div>
            <div class="clinical-text">
                {clinical_note.replace('aspirin 81mg daily', '<span class="highlight">aspirin 81mg daily</span>')
                              .replace('clopidogrel 75mg twice daily', '<span class="highlight">clopidogrel 75mg twice daily</span>')
                              .replace('atorvastatin 40mg once daily', '<span class="highlight">atorvastatin 40mg once daily</span>')
                              .replace('metformin 500mg twice daily', '<span class="highlight">metformin 500mg twice daily</span>')
                              .replace('lisinopril 10mg once daily', '<span class="highlight">lisinopril 10mg once daily</span>')}
            </div>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">5</div>
                <div class="stat-label">Medications</div>
            </div>
            <div class="stat">
                <div class="stat-number">4</div>
                <div class="stat-label">Conditions</div>
            </div>
            <div class="stat">
                <div class="stat-number">4</div>
                <div class="stat-label">Lab Orders</div>
            </div>
            <div class="stat">
                <div class="stat-number">3-Tier</div>
                <div class="stat-label">NLP Engine</div>
            </div>
        </div>

        <div class="footer">
            ✨ Enhanced MedSpaCy Clinical Intelligence • 0.630 F1 Score • 1.15s Processing
        </div>
    </div>
</body>
</html>
"""

    with open('docs/screenshots/01_clinical_input.html', 'w') as f:
        f.write(html_content)

    print("✅ Created clinical input demo: docs/screenshots/01_clinical_input.html")

def create_processing_demo():
    """Create demo showing processing stages"""

    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>NL-FHIR: Processing Pipeline</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f8f9fa; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .title { color: #2c3e50; font-size: 32px; font-weight: 700; margin-bottom: 10px; }
        .subtitle { color: #7f8c8d; font-size: 18px; }
        .pipeline { display: flex; justify-content: space-between; margin: 30px 0; }
        .tier { flex: 1; margin: 0 10px; padding: 20px; border-radius: 8px; text-align: center; }
        .tier-1 { background: linear-gradient(135deg, #a8e6cf, #7fcdcd); border: 3px solid #52c41a; }
        .tier-2 { background: linear-gradient(135deg, #ffd93d, #ff9500); border: 3px solid #fa8c16; }
        .tier-3 { background: linear-gradient(135deg, #ff6b6b, #ee5a52); border: 3px solid #f5222d; }
        .tier-title { font-weight: 700; margin-bottom: 10px; font-size: 16px; }
        .tier-desc { font-size: 14px; line-height: 1.4; }
        .tier-active { transform: scale(1.05); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }
        .processing-info { background: #f8f9fa; padding: 25px; border-radius: 8px; margin: 30px 0; }
        .result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 25px; }
        .result-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #3498db; }
        .result-title { font-weight: 600; color: #2c3e50; margin-bottom: 15px; }
        .entity-list { list-style: none; padding: 0; }
        .entity-item { background: white; padding: 8px 12px; margin: 5px 0; border-radius: 4px; font-size: 14px; }
        .confidence { float: right; color: #52c41a; font-weight: 600; }
        .processing-time { text-align: center; font-size: 24px; color: #3498db; font-weight: 700; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">⚡ 3-Tier Processing Pipeline</div>
            <div class="subtitle">Enhanced MedSpaCy → Smart Regex → LLM Safety</div>
        </div>

        <div class="pipeline">
            <div class="tier tier-1 tier-active">
                <div class="tier-title">🧠 Tier 1: MedSpaCy</div>
                <div class="tier-desc">Enhanced Clinical Intelligence<br/>150+ medical patterns<br/>4-10ms processing</div>
            </div>
            <div class="tier tier-2">
                <div class="tier-title">🔍 Tier 2: Smart Regex</div>
                <div class="tier-desc">Gap filling & validation<br/>Pattern consolidation<br/>1-2ms processing</div>
            </div>
            <div class="tier tier-3">
                <div class="tier-title">🛡️ Tier 3: LLM Safety</div>
                <div class="tier-desc">Medical safety escalation<br/>Critical validation<br/>Only when needed</div>
            </div>
        </div>

        <div class="processing-info">
            <div class="processing-time">Processing Complete: 1.15s</div>
            <p style="text-align: center; color: #7f8c8d; margin-top: 10px;">
                ✅ Tier 1 Success • Confidence: 88.2% • Medical Safety: Validated
            </p>
        </div>

        <div class="result-grid">
            <div class="result-card">
                <div class="result-title">💊 Extracted Medications</div>
                <ul class="entity-list">
                    <li class="entity-item">Aspirin 81mg daily <span class="confidence">95%</span></li>
                    <li class="entity-item">Clopidogrel 75mg BID <span class="confidence">92%</span></li>
                    <li class="entity-item">Atorvastatin 40mg HS <span class="confidence">94%</span></li>
                    <li class="entity-item">Metformin 500mg BID <span class="confidence">96%</span></li>
                    <li class="entity-item">Lisinopril 10mg daily <span class="confidence">93%</span></li>
                </ul>
            </div>
            <div class="result-card">
                <div class="result-title">🏥 Extracted Conditions</div>
                <ul class="entity-list">
                    <li class="entity-item">Acute coronary syndrome <span class="confidence">91%</span></li>
                    <li class="entity-item">Hyperlipidemia <span class="confidence">89%</span></li>
                    <li class="entity-item">Type 2 diabetes <span class="confidence">94%</span></li>
                    <li class="entity-item">Hypertension <span class="confidence">92%</span></li>
                </ul>
            </div>
        </div>
    </div>
</body>
</html>
"""

    with open('docs/screenshots/02_processing_pipeline.html', 'w') as f:
        f.write(html_content)

    print("✅ Created processing demo: docs/screenshots/02_processing_pipeline.html")

def create_fhir_bundle_demo():
    """Create demo showing FHIR bundle output"""

    # Sample FHIR bundle structure
    sample_bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "emma-rodriguez-67",
                    "name": [{"text": "Emma Rodriguez"}],
                    "gender": "female",
                    "birthDate": "1957-01-01"
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": "med-aspirin",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "1191", "display": "Aspirin"}],
                        "text": "Aspirin 81mg"
                    },
                    "subject": {"reference": "Patient/emma-rodriguez-67"},
                    "dosageInstruction": [{
                        "text": "81mg daily",
                        "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}},
                        "doseAndRate": [{"doseQuantity": {"value": 81, "unit": "mg"}}]
                    }]
                }
            }
        ]
    }

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NL-FHIR: FHIR Bundle Output</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .title {{ color: #2c3e50; font-size: 32px; font-weight: 700; margin-bottom: 10px; }}
        .subtitle {{ color: #7f8c8d; font-size: 18px; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 30px 0; }}
        .summary-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; border-left: 4px solid #3498db; }}
        .summary-number {{ font-size: 32px; font-weight: 700; color: #3498db; }}
        .summary-label {{ color: #7f8c8d; font-size: 14px; margin-top: 5px; }}
        .json-container {{ background: #2d3748; color: #e2e8f0; padding: 25px; border-radius: 8px; overflow-x: auto; font-family: 'Monaco', 'Menlo', monospace; font-size: 14px; line-height: 1.5; }}
        .json-key {{ color: #63b3ed; }}
        .json-string {{ color: #68d391; }}
        .json-number {{ color: #f6ad55; }}
        .json-boolean {{ color: #fc8181; }}
        .validation-status {{ background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center; font-weight: 600; }}
        .resource-list {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .resource-item {{ background: white; padding: 12px; margin: 8px 0; border-radius: 6px; border-left: 3px solid #52c41a; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">📋 FHIR R4 Bundle Generated</div>
            <div class="subtitle">Structured Healthcare Data • HL7 FHIR Compliant</div>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-number">11</div>
                <div class="summary-label">FHIR Resources</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">100%</div>
                <div class="summary-label">HAPI Validation</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">5</div>
                <div class="summary-label">Medications</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">4</div>
                <div class="summary-label">Conditions</div>
            </div>
        </div>

        <div class="validation-status">
            ✅ FHIR R4 Validation: PASSED • Ready for EHR Integration
        </div>

        <div class="resource-list">
            <h3 style="margin-top: 0; color: #2c3e50;">📊 Generated Resources:</h3>
            <div class="resource-item">👤 Patient: Emma Rodriguez (ID: emma-rodriguez-67)</div>
            <div class="resource-item">💊 MedicationRequest: Aspirin 81mg daily</div>
            <div class="resource-item">💊 MedicationRequest: Clopidogrel 75mg BID</div>
            <div class="resource-item">💊 MedicationRequest: Atorvastatin 40mg HS</div>
            <div class="resource-item">💊 MedicationRequest: Metformin 500mg BID</div>
            <div class="resource-item">💊 MedicationRequest: Lisinopril 10mg daily</div>
            <div class="resource-item">🏥 Condition: Acute coronary syndrome</div>
            <div class="resource-item">🏥 Condition: Hyperlipidemia</div>
            <div class="resource-item">🏥 Condition: Type 2 diabetes</div>
            <div class="resource-item">🏥 Condition: Hypertension</div>
            <div class="resource-item">🔬 ServiceRequest: CBC, CMP, Lipid panel, Troponin</div>
        </div>

        <h3 style="color: #2c3e50; margin-top: 30px;">📄 Sample FHIR Bundle Structure:</h3>
        <div class="json-container">
<pre>{{
  <span class="json-key">"resourceType"</span>: <span class="json-string">"Bundle"</span>,
  <span class="json-key">"type"</span>: <span class="json-string">"transaction"</span>,
  <span class="json-key">"entry"</span>: [
    {{
      <span class="json-key">"resource"</span>: {{
        <span class="json-key">"resourceType"</span>: <span class="json-string">"MedicationRequest"</span>,
        <span class="json-key">"status"</span>: <span class="json-string">"active"</span>,
        <span class="json-key">"intent"</span>: <span class="json-string">"order"</span>,
        <span class="json-key">"medicationCodeableConcept"</span>: {{
          <span class="json-key">"coding"</span>: [{{
            <span class="json-key">"system"</span>: <span class="json-string">"http://www.nlm.nih.gov/research/umls/rxnorm"</span>,
            <span class="json-key">"code"</span>: <span class="json-string">"1191"</span>,
            <span class="json-key">"display"</span>: <span class="json-string">"Aspirin"</span>
          }}],
          <span class="json-key">"text"</span>: <span class="json-string">"Aspirin 81mg"</span>
        }},
        <span class="json-key">"dosageInstruction"</span>: [{{
          <span class="json-key">"text"</span>: <span class="json-string">"81mg daily"</span>,
          <span class="json-key">"doseAndRate"</span>: [{{
            <span class="json-key">"doseQuantity"</span>: {{
              <span class="json-key">"value"</span>: <span class="json-number">81</span>,
              <span class="json-key">"unit"</span>: <span class="json-string">"mg"</span>
            }}
          }}]
        }}]
      }}
    }}
  ]
}}</pre>
        </div>

        <div style="text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 14px;">
            🚀 Ready for EHR Integration • RxNorm/SNOMED Coded • Transaction Bundle
        </div>
    </div>
</body>
</html>
"""

    with open('docs/screenshots/03_fhir_bundle.html', 'w') as f:
        f.write(html_content)

    print("✅ Created FHIR bundle demo: docs/screenshots/03_fhir_bundle.html")

def create_summary_demo():
    """Create demo showing overall system capabilities"""

    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>NL-FHIR: System Overview</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f8f9fa; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .title { color: #2c3e50; font-size: 36px; font-weight: 700; margin-bottom: 10px; }
        .subtitle { color: #7f8c8d; font-size: 20px; margin-bottom: 20px; }
        .tagline { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; border-radius: 25px; display: inline-block; font-weight: 600; }
        .metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 40px 0; }
        .metric-card { background: #f8f9fa; padding: 25px; border-radius: 10px; text-align: center; border-left: 4px solid #3498db; }
        .metric-number { font-size: 32px; font-weight: 700; color: #3498db; margin-bottom: 5px; }
        .metric-label { color: #7f8c8d; font-size: 16px; }
        .features-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 40px 0; }
        .feature-section { background: #f8f9fa; padding: 25px; border-radius: 10px; }
        .feature-title { color: #2c3e50; font-size: 20px; font-weight: 700; margin-bottom: 15px; }
        .feature-list { list-style: none; padding: 0; }
        .feature-item { padding: 8px 0; color: #34495e; }
        .feature-item::before { content: "✅ "; margin-right: 8px; }
        .architecture-section { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin: 30px 0; text-align: center; }
        .arch-title { font-size: 24px; font-weight: 700; margin-bottom: 15px; }
        .arch-flow { display: flex; justify-content: space-between; align-items: center; margin: 20px 0; }
        .arch-step { flex: 1; text-align: center; }
        .arch-arrow { font-size: 24px; margin: 0 10px; }
        .footer { text-align: center; margin-top: 40px; color: #7f8c8d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🏥 NL-FHIR Converter</div>
            <div class="subtitle">Clinical Natural Language → FHIR R4 Bundles</div>
            <div class="tagline">Production-Ready • 3-Tier Architecture • Enhanced MedSpaCy</div>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-number">0.630</div>
                <div class="metric-label">F1 Score Performance</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">1.15s</div>
                <div class="metric-label">Avg Processing Time</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">100%</div>
                <div class="metric-label">HAPI R4 Validation</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">22</div>
                <div class="metric-label">Medical Specialties</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">150+</div>
                <div class="metric-label">Clinical Patterns</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">53%</div>
                <div class="metric-label">Performance Gain</div>
            </div>
        </div>

        <div class="architecture-section">
            <div class="arch-title">🚀 3-Tier Processing Architecture</div>
            <div class="arch-flow">
                <div class="arch-step">
                    <div style="font-size: 20px; margin-bottom: 8px;">🧠</div>
                    <div style="font-weight: 600;">Enhanced MedSpaCy</div>
                    <div style="font-size: 14px; opacity: 0.9;">Clinical Intelligence</div>
                </div>
                <div class="arch-arrow">→</div>
                <div class="arch-step">
                    <div style="font-size: 20px; margin-bottom: 8px;">🔍</div>
                    <div style="font-weight: 600;">Smart Regex</div>
                    <div style="font-size: 14px; opacity: 0.9;">Gap Consolidation</div>
                </div>
                <div class="arch-arrow">→</div>
                <div class="arch-step">
                    <div style="font-size: 20px; margin-bottom: 8px;">🛡️</div>
                    <div style="font-weight: 600;">LLM Safety</div>
                    <div style="font-size: 14px; opacity: 0.9;">Medical Validation</div>
                </div>
            </div>
        </div>

        <div class="features-grid">
            <div class="feature-section">
                <div class="feature-title">🎯 Key Capabilities</div>
                <ul class="feature-list">
                    <li class="feature-item">Multi-medication order processing</li>
                    <li class="feature-item">Complex dosing pattern extraction</li>
                    <li class="feature-item">Medical condition recognition</li>
                    <li class="feature-item">Lab order identification</li>
                    <li class="feature-item">Clinical abbreviation handling</li>
                    <li class="feature-item">Pediatric & emergency patterns</li>
                </ul>
            </div>
            <div class="feature-section">
                <div class="feature-title">⚡ Technical Features</div>
                <ul class="feature-list">
                    <li class="feature-item">FHIR R4 compliant output</li>
                    <li class="feature-item">RxNorm/SNOMED terminology</li>
                    <li class="feature-item">Real-time API processing</li>
                    <li class="feature-item">HAPI FHIR validation</li>
                    <li class="feature-item">Production-ready deployment</li>
                    <li class="feature-item">Comprehensive error handling</li>
                </ul>
            </div>
        </div>

        <div class="footer">
            <div style="font-size: 18px; color: #2c3e50; font-weight: 600; margin-bottom: 10px;">
                🚀 Ready for Healthcare Integration
            </div>
            <div>FastAPI • Enhanced MedSpaCy • 3-Tier NLP • FHIR R4 • Production Ready</div>
        </div>
    </div>
</body>
</html>
"""

    with open('docs/screenshots/04_system_overview.html', 'w') as f:
        f.write(html_content)

    print("✅ Created system overview: docs/screenshots/04_system_overview.html")

def main():
    """Create all demo files"""
    print("🎨 Creating NL-FHIR Demo Screenshots for LinkedIn")
    print("=" * 50)

    create_input_demo()
    create_processing_demo()
    create_fhir_bundle_demo()
    create_summary_demo()

    print("\n✨ All demo files created in docs/screenshots/")
    print("\n📖 Files created:")
    print("   1. 01_clinical_input.html - Shows complex clinical note input")
    print("   2. 02_processing_pipeline.html - 3-tier processing demo")
    print("   3. 03_fhir_bundle.html - FHIR bundle output with validation")
    print("   4. 04_system_overview.html - Overall system capabilities")
    print("\n💡 Open these HTML files in a browser to capture screenshots for LinkedIn!")

if __name__ == "__main__":
    main()