import requests
import json

test_text = "Started patient John Smith on metformin 500mg twice daily for type 2 diabetes mellitus."

response = requests.post(
    "http://localhost:8001/convert",
    json={"clinical_text": test_text},
    timeout=15
)

data = response.json()

print("=" * 60)
print("EXTRACTION TEST RESULTS")
print("=" * 60)
print("\nInput Text:")
print(test_text)
print("\nLLM Structured Output:")
if "llm_structured" in data:
    print(json.dumps(data["llm_structured"], indent=2))
else:
    print("No LLM structured output found")

print("\nExtracted Entities:")
if "entities" in data:
    entities = data["entities"]
    print(f"Conditions: {entities.get('conditions', [])}")
    print(f"Medications: {entities.get('medications', [])}")
    print(f"Patients: {entities.get('patients', [])}")

print("\nFHIR Bundle Conditions:")
if "fhir_bundle" in data and "entry" in data["fhir_bundle"]:
    for entry in data["fhir_bundle"]["entry"]:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Condition":
            code = resource.get("code", {})
            print(f"Condition Resource: {code.get('text', 'Unknown')}")