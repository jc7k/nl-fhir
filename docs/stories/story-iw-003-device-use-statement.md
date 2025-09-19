# User Story IW-003: DeviceUseStatement Patient-Device Linking

## Story Overview
**Story ID:** IW-003
**Epic:** Epic-IW-001 (Infusion Workflow FHIR Resource Support)
**Priority:** P1 - High
**Story Points:** 5
**Sprint:** Sprint 2

## User Story
**As a** nurse tracking device usage for patients
**I want** the system to create FHIR DeviceUseStatement resources linking patients to infusion devices
**So that** I can maintain records of which devices were used for each patient and when

## Acceptance Criteria

### AC1: DeviceUseStatement Resource Creation
**Given** clinical text describing patient device usage
**When** the NLP pipeline processes the text
**Then** a valid FHIR DeviceUseStatement resource is created with:
- [ ] Patient reference (who used the device)
- [ ] Device reference (which device was used)
- [ ] Usage period (when device was used)
- [ ] Status (active, completed, entered-in-error)
- [ ] Reason for use (clinical indication)

### AC2: Patient-Device Relationship Recognition
**Given** text describing device usage scenarios
**When** creating DeviceUseStatement resources
**Then** the system correctly identifies:
- [ ] Patient-device relationships ("patient using IV pump")
- [ ] Temporal aspects ("started on", "connected to", "using")
- [ ] Clinical context (medication delivery, monitoring)
- [ ] Multiple devices per patient scenarios

### AC3: Integration with Related Resources
**Given** existing Patient and Device resources
**When** creating DeviceUseStatement
**Then** the resource correctly references:
- [ ] Patient resource via subject field
- [ ] Device resource via device field
- [ ] Related MedicationAdministration (if applicable)
- [ ] Encounter context

### AC4: HAPI FHIR Validation
**Given** any generated DeviceUseStatement resource
**When** validated against HAPI FHIR server
**Then** validation passes 100% of the time with no errors

### AC5: Bundle Integration and Linking
**Given** a complete infusion scenario
**When** generating FHIR bundle
**Then** DeviceUseStatement resources:
- [ ] Link Patient and Device resources correctly
- [ ] Include proper resource references
- [ ] Maintain referential integrity in bundle
- [ ] Support transaction bundle patterns

## Technical Requirements

### NLP Enhancement
- **Extract usage relationships:** "patient using", "connected to", "via device"
- **Recognize temporal indicators:** "started", "continuing", "disconnected"
- **Parse clinical context:** reason for device usage

### Resource Factory Extension
```python
def create_device_use_statement(
    self,
    usage_data: Dict[str, Any],
    patient_ref: str,
    device_ref: str,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
```

### Data Model Support
- **Status values:** active, completed, entered-in-error, intended, stopped, on-hold
- **Timing periods:** effectiveDateTime, effectivePeriod
- **Reason codes:** Clinical indication for device usage

## Test Scenarios

### Scenario 1: IV Pump Usage for Morphine
**Input:** "Patient Emma Garcia receiving morphine infusion via IV pump for post-operative pain."
**Expected Output:**
```json
{
  "resourceType": "DeviceUseStatement",
  "status": "active",
  "subject": {"reference": "Patient/emma-garcia"},
  "device": {"reference": "Device/iv-pump-001"},
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "182836005",
      "display": "Review of medication"
    }],
    "text": "morphine infusion for post-operative pain"
  }],
  "effectiveDateTime": "2024-01-15T10:30:00Z"
}
```

### Scenario 2: PCA Pump for Pain Control
**Input:** "Patient John Smith using PCA pump for self-administered fentanyl pain control."
**Expected Output:**
- DeviceUseStatement linking patient to PCA pump
- Reason indicating pain control
- Self-administration context

### Scenario 3: Multiple Device Usage
**Input:** "Patient on vancomycin infusion through IV pump and cardiac monitoring via telemetry device."
**Expected Output:**
- Two separate DeviceUseStatement resources
- One for IV pump (medication delivery)
- One for telemetry (monitoring) - if Device resource created

## Definition of Done
- [ ] Resource factory method implemented and tested
- [ ] NLP pipeline extracts patient-device relationships
- [ ] All test scenarios pass with 100% HAPI validation
- [ ] Integration tests with existing Patient and Device resources
- [ ] Bundle assembly correctly links all references
- [ ] Code review and documentation complete

## Dependencies
- **Prerequisite:** IW-001 (MedicationAdministration) and IW-002 (Device) completion
- **Integration:** Patient and Device resource availability
- **Validation:** Bundle reference integrity testing

## Risk Mitigation
- **Reference Integrity:** Comprehensive testing of resource linking
- **Complex Scenarios:** Start with single device usage, expand to multiple devices
- **NLP Accuracy:** Validate patient-device relationship extraction thoroughly

## Future Considerations
- **Device Lifecycle:** Track device assignment, transfer, and return
- **Usage Analytics:** Aggregate device utilization patterns
- **Real-time Updates:** Live device status updates

---
**Story Owner:** Development Team
**Reviewer:** Clinical SME + Technical Lead
**Estimated Completion:** Sprint 2, Week 1