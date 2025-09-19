# User Story IW-002: Device Resource for Infusion Equipment

## Story Overview
**Story ID:** IW-002
**Epic:** Epic-IW-001 (Infusion Workflow FHIR Resource Support)
**Priority:** P0 - Critical
**Story Points:** 5
**Sprint:** Sprint 1

## User Story
**As a** nurse managing infusion therapy with medical devices
**I want** the system to create FHIR Device resources for infusion equipment from natural language input
**So that** I can track which devices are used for patient care and maintain equipment accountability

## Acceptance Criteria

### AC1: Device Resource Creation
**Given** clinical text mentioning infusion equipment
**When** the NLP pipeline processes the text
**Then** a valid FHIR Device resource is created with:
- [ ] Device identifier (serial number, asset tag)
- [ ] Device type (IV pump, PCA pump, infusion stand)
- [ ] Manufacturer information (when available)
- [ ] Device status (active, inactive, entered-in-error)
- [ ] Device names and model information

### AC2: Device Type Recognition
**Given** text describing various infusion equipment
**When** creating Device resources
**Then** the system recognizes:
- [ ] IV pumps and infusion pumps
- [ ] PCA (Patient Controlled Analgesia) pumps
- [ ] Syringe pumps
- [ ] Infusion stands and poles
- [ ] Central line access devices
- [ ] Generic "infusion equipment" references

### AC3: Device Coding Standards
**Given** any Device resource creation
**When** assigning device types
**Then** the system uses:
- [ ] SNOMED CT codes for device types where available
- [ ] Consistent device categorization
- [ ] Proper medical device terminology
- [ ] Fallback to text description when codes unavailable

### AC4: HAPI FHIR Validation
**Given** any generated Device resource
**When** validated against HAPI FHIR server
**Then** validation passes 100% of the time with no errors

### AC5: Bundle Integration
**Given** a clinical scenario involving devices
**When** generating FHIR bundle
**Then** Device resources are:
- [ ] Included in bundle entries
- [ ] Assigned unique identifiers
- [ ] Available for reference by other resources
- [ ] Follow transaction bundle patterns

## Technical Requirements

### NLP Enhancement
- **Extract device mentions:** "IV pump", "PCA pump", "infusion equipment"
- **Recognize device actions:** "connected to", "using", "via pump"
- **Parse device details:** model numbers, serial numbers, settings

### Resource Factory Extension
```python
def create_device_resource(
    self,
    device_data: Dict[str, Any],
    request_id: Optional[str] = None
) -> Dict[str, Any]:
```

### Data Model Support
- **Device types:** IV pump, PCA pump, infusion stand, central line
- **Status values:** active, inactive, entered-in-error, unknown
- **Identifier systems:** hospital asset management, manufacturer serial numbers

## Test Scenarios

### Scenario 1: IV Pump Usage
**Input:** "Patient receiving morphine infusion via IV pump for post-operative pain management."
**Expected Output:**
```json
{
  "resourceType": "Device",
  "identifier": [{
    "system": "http://hospital.local/device-id",
    "value": "IV-PUMP-001"
  }],
  "type": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "182722004",
      "display": "Infusion pump"
    }]
  },
  "status": "active",
  "deviceName": [{
    "name": "IV Pump",
    "type": "user-friendly-name"
  }]
}
```

### Scenario 2: PCA Pump Reference
**Input:** "Patient using PCA pump for self-administered pain control with fentanyl."
**Expected Output:**
- Device resource for PCA pump
- Patient Controlled Analgesia device type
- Connection to fentanyl administration

### Scenario 3: Generic Infusion Equipment
**Input:** "Administer vancomycin through infusion equipment over 60 minutes."
**Expected Output:**
- Generic infusion device resource
- Duration information captured
- Available for DeviceUseStatement linking

## Definition of Done
- [ ] Resource factory method implemented and tested
- [ ] NLP pipeline extracts device mentions
- [ ] All test scenarios pass with 100% HAPI validation
- [ ] Integration tests with bundle assembly complete
- [ ] Device coding standards documentation complete
- [ ] Code review and documentation complete

## Dependencies
- **Prerequisite:** Basic resource factory patterns
- **Integration:** NLP entity extraction capabilities
- **Standards:** SNOMED CT device codes research

## Risk Mitigation
- **Device Identification:** Start with generic device types, expand specificity over time
- **Coding Standards:** Research medical device terminologies for proper codes
- **NLP Complexity:** Begin with obvious device mentions, improve detection iteratively

## Future Considerations
- **Real Device Integration:** APIs for actual device data import
- **Device Maintenance:** Tracking device service and calibration
- **Device Analytics:** Usage patterns and performance metrics

---
**Story Owner:** Development Team
**Reviewer:** Clinical SME + Technical Lead
**Estimated Completion:** Sprint 1, Week 1