# User Story IW-001: MedicationAdministration Resource Implementation

## Story Overview
**Story ID:** IW-001
**Epic:** Epic-IW-001 (Infusion Workflow FHIR Resource Support)
**Priority:** P0 - Critical
**Story Points:** 8
**Sprint:** Sprint 1

## User Story
**As a** ICU nurse documenting IV medication administration
**I want** the system to create FHIR MedicationAdministration resources from natural language input
**So that** I can maintain complete audit trails of when and how medications were actually given to patients

## Acceptance Criteria

### AC1: MedicationAdministration Resource Creation
**Given** clinical text describing IV medication administration
**When** the NLP pipeline processes the text
**Then** a valid FHIR MedicationAdministration resource is created with:
- [ ] Patient reference
- [ ] Medication reference or inline medication details
- [ ] Administration timestamp
- [ ] Dosage information (amount, rate, route)
- [ ] Performer (practitioner who administered)
- [ ] Status (completed, in-progress, stopped)

### AC2: Route and Method Support
**Given** text describing various administration routes
**When** creating MedicationAdministration resources
**Then** the system supports:
- [ ] IV (intravenous) administration
- [ ] IM (intramuscular) administration
- [ ] Sublingual administration
- [ ] Other common routes from existing test cases

### AC3: Integration with Existing Resources
**Given** a clinical scenario with patient, practitioner, and medication request
**When** creating MedicationAdministration
**Then** the resource correctly references:
- [ ] Existing Patient resource
- [ ] Existing Practitioner resource
- [ ] Related MedicationRequest (if available)
- [ ] Encounter context

### AC4: HAPI FHIR Validation
**Given** any generated MedicationAdministration resource
**When** validated against HAPI FHIR server
**Then** validation passes 100% of the time with no errors

### AC5: Bundle Integration
**Given** a complete clinical scenario
**When** generating FHIR bundle
**Then** MedicationAdministration resources are:
- [ ] Included in bundle entries
- [ ] Properly linked to related resources
- [ ] Include correct fullUrl references
- [ ] Follow transaction bundle patterns

## Technical Requirements

### NLP Enhancement
- **Extract administration details:** dosage, route, timing, performer
- **Recognize administration verbs:** "administered", "given", "received"
- **Parse timing expressions:** "4mg IV", "every 12 hours", "at 14:30"

### Resource Factory Extension
```python
def create_medication_administration(
    self,
    admin_data: Dict[str, Any],
    patient_ref: str,
    request_id: Optional[str] = None,
    practitioner_ref: Optional[str] = None,
    medication_request_ref: Optional[str] = None
) -> Dict[str, Any]:
```

### Data Model Support
- **Status values:** completed, in-progress, not-done, on-hold, stopped, unknown
- **Route codes:** IV, IM, sublingual, oral, topical, etc.
- **Dosage structures:** SimpleQuantity, Rate, Ratio support

## Test Scenarios

### Scenario 1: IV Morphine Administration (Existing Test Case)
**Input:** "Patient Emma Garcia administered morphine 4mg IV for severe trauma pain in emergency department."
**Expected Output:**
```json
{
  "resourceType": "MedicationAdministration",
  "status": "completed",
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "7052",
      "display": "morphine"
    }]
  },
  "subject": {"reference": "Patient/emma-garcia"},
  "dosage": {
    "route": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "47625008",
        "display": "intravenous route"
      }]
    },
    "dose": {
      "value": 4,
      "unit": "mg"
    }
  }
}
```

### Scenario 2: IV Vancomycin Administration (Existing Test Case)
**Input:** "Patient Jessica Park started on vancomycin 1g IV every 12 hours for MRSA bacteremia."
**Expected Output:**
- MedicationAdministration with vancomycin details
- Recurring administration pattern recognition
- MRSA indication reference

### Scenario 3: Emergency Epinephrine Administration
**Input:** "Emergency patient John Taylor given epinephrine 0.3mg intramuscularly for anaphylactic reaction."
**Expected Output:**
- IM route recognition
- Emergency context
- Epinephrine medication coding

## Definition of Done
- [ ] Resource factory method implemented and tested
- [ ] NLP pipeline extracts administration details
- [ ] All test scenarios pass with 100% HAPI validation
- [ ] Integration tests with bundle assembly complete
- [ ] Performance meets <2s response time requirement
- [ ] Code review and documentation complete

## Dependencies
- **Prerequisite:** Current MedicationRequest implementation
- **Integration:** Existing resource factory patterns
- **Validation:** HAPI FHIR validation pipeline

## Risk Mitigation
- **Clinical Safety:** Extensive validation with real clinical scenarios
- **Performance:** Incremental testing with bundle assembly
- **Complexity:** Start with common routes, expand based on test coverage

---
**Story Owner:** Development Team
**Reviewer:** Clinical SME + Technical Lead
**Estimated Completion:** Sprint 1, Week 2