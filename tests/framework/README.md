# NL-FHIR Extensible QA Framework

A comprehensive quality assurance framework for testing clinical NLP and FHIR integration pipelines.

## Features
- **Extensible Test Cases**: JSON configuration and programmatic creation
- **3-Tier Architecture Testing**: spaCy ’ Transformers ’ LLM escalation
- **Comprehensive Reporting**: HTML reports with performance and quality metrics
- **HIPAA Compliance**: No PHI, secure logging, audit trails

## Quick Start

```python
from tests.framework.qa_framework import ClinicalTestLoader, ClinicalTestRunner

# Load test cases
loader = ClinicalTestLoader("tests/data")
test_cases = loader.load_test_cases_from_json("tests/data/medication_test_cases.json")

# Run tests
runner = ClinicalTestRunner(nlp_processor=your_nlp_processor)
results = await runner.run_test_suite(test_cases)

# Generate report
from tests.framework.qa_framework import TestReportGenerator
generator = TestReportGenerator()
generator.generate_detailed_html_report(results, "test_report.html")
```

## Test Case Structure

```json
{
  "id": "med-001",
  "name": "Simple Medication Order",
  "clinical_text": "Patient needs Lisinopril 10mg daily",
  "scenario": "medication_order",
  "expected_entities": [
    {"category": "medications", "value": "lisinopril", "required": true}
  ],
  "minimum_quality_score": 0.8,
  "performance": {"max_processing_time_ms": 1000, "expected_tier": "spacy"}
}
```

## Performance Requirements
- **<2s Processing Time**: End-to-end response requirement
- **e95% Quality Score**: Entity extraction accuracy target
- **e99.9% Uptime**: Production reliability target

## Demo
```bash
uv run python tests/framework/demo_qa_framework.py
```