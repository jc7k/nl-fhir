import requests
import json

# Test multiple conditions extraction
test_text = "Administered patient Michael Wilson morphine 5mg IV for severe chest pain secondary to myocardial infarction."

response = requests.post(
    "http://localhost:8001/convert",
    json={"clinical_text": test_text},
    timeout=15
)

data = response.json()

print("=" * 70)
print("MULTIPLE CONDITIONS EXTRACTION TEST")
print("=" * 70)
print("\nInput Text:")
print(test_text)

print("\nExtracted Conditions from Entities:")
if "entities" in data:
    conditions = data["entities"].get("conditions", [])
    print(f"Found {len(conditions)} conditions:")
    for i, cond in enumerate(conditions, 1):
        print(f"  {i}. {cond.get('text', 'Unknown')}")
else:
    print("No entities found")

print("\nFHIR Bundle Condition Resources:")
condition_count = 0
if "fhir_bundle" in data and "entry" in data["fhir_bundle"]:
    for entry in data["fhir_bundle"]["entry"]:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Condition":
            condition_count += 1
            code = resource.get("code", {})
            condition_text = code.get("text", "Unknown")
            print(f"  Condition {condition_count}: {condition_text}")

print(f"\nExpected: Both 'severe chest pain' and 'myocardial infarction'")
print(f"Total Condition Resources: {condition_count}")

# Check if both expected conditions are present
expected_conditions = ["severe chest pain", "myocardial infarction"]
extracted_texts = []
if "fhir_bundle" in data and "entry" in data["fhir_bundle"]:
    for entry in data["fhir_bundle"]["entry"]:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Condition":
            code = resource.get("code", {})
            extracted_texts.append(code.get("text", "").lower())

print(f"\nAnalysis:")
for expected in expected_conditions:
    found = any(expected.lower() in text for text in extracted_texts)
    print(f"  '{expected}': {'✅ Found' if found else '❌ Missing'}")