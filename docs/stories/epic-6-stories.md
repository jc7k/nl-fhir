# Epic 6: Critical Foundation Resources - User Stories

**Epic Goal:** Complete the "Critical 20" FHIR resources that deliver 80% of clinical value
**Timeline:** Q4 2025
**Priority:** Highest (300% ROI)

---

## Story 6.1: CarePlan Resource Implementation

**As a** clinician managing patient care
**I want** to create and manage comprehensive care plans using FHIR CarePlan resources
**So that** I can coordinate treatment activities across care teams and track patient progress systematically

### **Acceptance Criteria**

#### AC1: CarePlan Resource Creation
**Given** I have patient treatment requirements
**When** I process clinical text containing care planning information
**Then** the system shall create a FHIR R4-compliant CarePlan resource with:
- Unique identifier and version tracking
- Patient reference (mandatory)
- Care plan status (draft, active, on-hold, revoked, completed, entered-in-error, unknown)
- Intent (proposal, plan, order, option)
- Category coding (assessment-and-plan, careteam, etc.)
- Title and description fields
- Subject (patient) reference
- Encounter reference (when available)
- Period (start and end dates)
- Created date and author references

#### AC2: CarePlan Activities Management
**Given** I have a CarePlan resource
**When** I add care activities and goals
**Then** the system shall support:
- Activity detail with kind, status, and description
- Goal references linking to Goal resources
- Activity timing and scheduling
- Activity performer assignments (care team members)
- Activity reason codes and references
- Progress notes and outcome tracking

#### AC3: Care Team Integration
**Given** I have multiple healthcare providers involved in patient care
**When** I create a CarePlan
**Then** the system shall:
- Reference Practitioner resources for care team members
- Support role assignments (primary care, specialist, nurse, etc.)
- Enable care team communication preferences
- Track care team member responsibilities per activity

#### AC4: FHIR Validation and Terminology
**Given** I create any CarePlan resource
**When** the resource is validated
**Then** it shall:
- Pass 100% HAPI FHIR R4 validation
- Use appropriate SNOMED CT codes for categories and activities
- Include proper coding systems (LOINC, CPT, SNOMED)
- Maintain referential integrity with linked resources

#### AC5: NLP Integration
**Given** clinical text mentioning care planning
**When** processed through the NLP pipeline
**Then** the system shall:
- Extract care plan activities, goals, and timelines
- Identify care team members and roles
- Parse treatment schedules and frequencies
- Create appropriate CarePlan resource automatically

### **Definition of Done**
- [ ] CarePlan resource factory method implemented
- [ ] Full FHIR R4 schema compliance verified
- [ ] HAPI FHIR validation passing (100%)
- [ ] Unit tests covering all acceptance criteria (>95% coverage)
- [ ] Integration tests with existing Patient, Practitioner resources
- [ ] NLP extraction rules for care planning text
- [ ] API endpoint for CarePlan CRUD operations
- [ ] Documentation updated (API docs, clinical use cases)

### **Technical Implementation Notes**
- Extend FHIRResourceFactory with create_care_plan method
- Implement CarePlan status workflow management
- Add terminology validation for care plan categories
- Create CarePlan-specific NLP extraction patterns
- Ensure proper resource linking and referential integrity

---

## Story 6.2: AllergyIntolerance Resource Implementation

**As a** clinician prescribing medications
**I want** to document and access patient allergy information using FHIR AllergyIntolerance resources
**So that** I can prevent adverse drug reactions and ensure patient safety during treatment

### **Acceptance Criteria**

#### AC1: AllergyIntolerance Resource Creation
**Given** I have patient allergy information
**When** I create an AllergyIntolerance resource
**Then** the system shall create a FHIR R4-compliant resource with:
- Patient reference (mandatory)
- Allergen substance coding (RxNorm, SNOMED CT, UNII)
- Clinical status (active, inactive, resolved)
- Verification status (unconfirmed, presumed, confirmed, refuted, entered-in-error)
- Type (allergy, intolerance)
- Category (food, medication, environment, biologic)
- Criticality (low, high, unable-to-assess)
- Code for the allergen
- Onset information (age, period, range, string)

#### AC2: Reaction Documentation
**Given** I document an allergic reaction
**When** I create the AllergyIntolerance
**Then** the system shall support:
- Reaction substance identification
- Manifestation coding (SNOMED CT for symptoms)
- Reaction description in clinical terms
- Severity (mild, moderate, severe)
- Exposure route (oral, parenteral, topical, etc.)
- Reaction onset timing
- Note field for additional clinical context

#### AC3: Clinical Decision Support Integration
**Given** I have documented AllergyIntolerance resources
**When** I prescribe medications or order procedures
**Then** the system shall:
- Cross-reference against known allergens
- Provide allergy alerts for potential interactions
- Support allergy checking workflows
- Enable allergy review and verification processes

#### AC4: Safety Validation and Alerts
**Given** critical allergy information exists
**When** any clinical order is processed
**Then** the system shall:
- Generate safety alerts for high-criticality allergies
- Validate medication orders against documented allergies
- Provide clear allergy warnings in clinical summaries
- Support allergy override documentation with reasons

#### AC5: NLP Allergy Extraction
**Given** clinical text mentioning allergies or adverse reactions
**When** processed through NLP pipeline
**Then** the system shall:
- Identify allergen substances and drug names
- Extract reaction descriptions and severity
- Parse allergy history and temporal information
- Create AllergyIntolerance resources automatically

### **Definition of Done**
- [ ] AllergyIntolerance resource factory method implemented
- [ ] Full FHIR R4 schema compliance verified
- [ ] HAPI FHIR validation passing (100%)
- [ ] Unit tests covering all acceptance criteria (>95% coverage)
- [ ] Integration with medication safety checking
- [ ] NLP extraction for allergy information
- [ ] Clinical decision support alerts implemented
- [ ] API endpoints for allergy management
- [ ] Safety validation workflows tested

### **Technical Implementation Notes**
- Implement comprehensive allergen terminology mapping
- Add allergy checking logic for medication orders
- Create allergy-specific NLP patterns and entity extraction
- Integrate with existing MedicationRequest validation
- Implement allergy alert generation and management

---

## Story 6.3: Immunization Resource Implementation

**As a** public health nurse tracking immunizations
**I want** to document patient immunization records using FHIR Immunization resources
**So that** I can maintain accurate vaccination records and support public health reporting requirements

### **Acceptance Criteria**

#### AC1: Immunization Resource Creation
**Given** I administer or document a vaccination
**When** I create an Immunization resource
**Then** the system shall create a FHIR R4-compliant resource with:
- Patient reference (mandatory)
- Vaccine code (CVX - CDC vaccine codes)
- Status (completed, entered-in-error, not-done)
- Status reason (when not completed)
- Vaccine code and manufacturer (MVX codes)
- Lot number and expiration date
- Administration date and time
- Primary source indicator (directly administered vs. reported)
- Location reference where administered

#### AC2: Vaccine Administration Details
**Given** I document vaccine administration
**When** I create the Immunization record
**Then** the system shall support:
- Dose quantity and units
- Route of administration (intramuscular, oral, nasal, etc.)
- Site of administration (deltoid, thigh, etc.)
- Performing practitioner reference
- Encounter reference (when applicable)
- Funding source information
- Program eligibility tracking

#### AC3: Vaccine Series and Dose Tracking
**Given** multi-dose vaccine series
**When** I record immunizations
**Then** the system shall:
- Track dose sequence numbers (1st, 2nd, booster, etc.)
- Support vaccine series identification
- Calculate due dates for subsequent doses
- Track completion status of vaccine series
- Support catch-up scheduling recommendations

#### AC4: Adverse Event and Contraindication Tracking
**Given** vaccine administration with adverse events
**When** I document the immunization
**Then** the system shall:
- Link to adverse event documentation
- Support contraindication documentation
- Track vaccine refusal reasons
- Enable exemption documentation (medical, religious, philosophical)
- Support reaction severity and follow-up tracking

#### AC5: Public Health Reporting Integration
**Given** completed immunization records
**When** generating public health reports
**Then** the system shall:
- Support immunization registry data format
- Enable age-appropriate vaccine recommendations
- Track population-level vaccination coverage
- Support outbreak investigation data needs
- Generate vaccination summary reports

### **Definition of Done**
- [ ] Immunization resource factory method implemented
- [ ] CVX/MVX vaccine code integration
- [ ] Dose series tracking functionality
- [ ] Adverse event linkage capability
- [ ] Public health reporting support
- [ ] NLP extraction for immunization data
- [ ] Integration with scheduling systems
- [ ] Regulatory compliance validation

---

## Story 6.4: Location Resource Implementation

**As a** healthcare system administrator
**I want** to manage healthcare locations using FHIR Location resources
**So that** I can track where care is delivered and optimize resource allocation across facilities

### **Acceptance Criteria**

#### AC1: Location Resource Creation
**Given** I need to define a healthcare location
**When** I create a Location resource
**Then** the system shall create a FHIR R4-compliant resource with:
- Unique identifier and status (active, suspended, inactive)
- Name and description of the location
- Location type (building, wing, room, bed, area, etc.)
- Physical type (site, building, wing, corridor, room, bed)
- Telecom contact information
- Address with full geographic details
- Position (latitude/longitude) when applicable
- Managing organization reference

#### AC2: Location Hierarchy Management
**Given** complex healthcare facilities with multiple levels
**When** I organize locations
**Then** the system shall support:
- Parent-child location relationships
- Location hierarchy browsing and navigation
- Location inheritance of properties (address, organization)
- Location containment validation
- Multi-level location reporting and analysis

#### AC3: Location Operational Status
**Given** locations with varying operational states
**When** managing location resources
**Then** the system shall track:
- Operational status (open, closed, housekeeping, etc.)
- Availability schedules and hours of operation
- Capacity information (bed count, room occupancy)
- Service restrictions and capabilities
- Maintenance and downtime periods

#### AC4: Care Delivery Integration
**Given** clinical activities happening at locations
**When** documenting care delivery
**Then** the system shall:
- Link encounters to specific locations
- Support location-based service provision
- Enable location-specific resource scheduling
- Track location utilization metrics
- Support location-based reporting and analytics

#### AC5: Geographic and Navigation Support
**Given** location resources with geographic information
**When** providing location services
**Then** the system shall:
- Support address validation and standardization
- Provide geographic coordinate tracking
- Enable location-based searches and filtering
- Support distance calculations between locations
- Integrate with mapping and navigation systems

### **Definition of Done**
- [ ] Location resource factory method implemented
- [ ] Location hierarchy management capability
- [ ] Geographic information integration
- [ ] Operational status tracking
- [ ] Integration with encounter and scheduling systems
- [ ] Address validation and standardization
- [ ] Location-based reporting functionality

---

## Story 6.5: Medication Resource Implementation

**As a** pharmacist managing medication information
**I want** to maintain comprehensive medication data using FHIR Medication resources
**So that** I can provide accurate drug information for prescribing and dispensing workflows

### **Acceptance Criteria**

#### AC1: Medication Resource Creation
**Given** I need to define a medication
**When** I create a Medication resource
**Then** the system shall create a FHIR R4-compliant resource with:
- Medication code (RxNorm, NDC, or other standard codes)
- Status (active, inactive, entered-in-error)
- Manufacturer reference or identifier
- Form (tablet, capsule, liquid, etc.) with SNOMED CT coding
- Amount and strength information
- Ingredient composition with strength ratios
- Batch information (lot number, expiration date)

#### AC2: Medication Composition and Ingredients
**Given** medications with multiple active ingredients
**When** documenting medication details
**Then** the system shall support:
- Multiple ingredient specification with strengths
- Ingredient coding using RxNorm or UNII codes
- Concentration and ratio calculations
- Inactive ingredient documentation
- Allergen and excipient identification
- Bioequivalence and generic substitution information

#### AC3: Formulary and Classification Integration
**Given** healthcare system formulary requirements
**When** managing medications
**Then** the system shall:
- Support formulary status tracking (preferred, restricted, non-formulary)
- Enable therapeutic class categorization
- Track medication tier levels for insurance coverage
- Support prior authorization requirements documentation
- Enable cost and coverage information integration

#### AC4: Medication Safety Information
**Given** medication safety requirements
**When** providing medication information
**Then** the system shall:
- Include contraindication and precaution information
- Support drug interaction checking capabilities
- Provide pregnancy category and safety ratings
- Include black box warnings and special alerts
- Support age-specific dosing and safety information

#### AC5: Pharmacy Operations Integration
**Given** pharmacy workflow requirements
**When** using medication resources
**Then** the system shall:
- Support dispensing unit and packaging information
- Enable inventory management integration
- Track medication availability and substitution options
- Support compounding and preparation instructions
- Integrate with prescription and medication request workflows

### **Definition of Done**
- [ ] Medication resource factory method implemented
- [ ] RxNorm/NDC code integration
- [ ] Ingredient composition tracking
- [ ] Formulary status management
- [ ] Safety information integration
- [ ] Drug interaction checking foundation
- [ ] Pharmacy workflow integration points
- [ ] Comprehensive medication data validation

---

## **Epic 6 Implementation Summary**

### **Story Priority Order:**
1. **Story 6.2: AllergyIntolerance** (Highest safety impact)
2. **Story 6.5: Medication** (Foundation for safety checking)
3. **Story 6.1: CarePlan** (Care coordination enabler)
4. **Story 6.4: Location** (Infrastructure support)
5. **Story 6.3: Immunization** (Public health compliance)

### **Sprint Planning Recommendations:**
- **Sprint 1:** AllergyIntolerance + Medication (safety foundation)
- **Sprint 2:** CarePlan + Location (care coordination)
- **Sprint 3:** Immunization + integration testing

### **Risk Mitigation:**
- Start with AllergyIntolerance due to patient safety criticality
- Ensure Medication resource supports allergy checking
- Test CarePlan workflow integration extensively
- Validate Location hierarchy complexity early

### **Success Metrics:**
- 100% HAPI FHIR validation for all resources
- Zero medication safety incidents during implementation
- <100ms response time for all resource queries
- >95% test coverage for all stories