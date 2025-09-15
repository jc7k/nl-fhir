# Comprehensive Specialty Test Design: 100 Cases Per Specialty

**Date**: September 14, 2025
**Designer**: Quinn (Test Architect)
**Scope**: Scale from 66 clinical test cases (22 specialties × 3 each) to 2,200 comprehensive test cases (22 specialties × 100 each)

## Executive Summary

Current state: **66 realistic clinical test cases** covering 22 medical specialties
Target state: **2,200 comprehensive test cases** with positive/negative coverage
Research sources: ClinicalTrials.gov API, Medical literature patterns, Clinical documentation standards, FHIR implementation guides

## Test Strategy Overview

### Total Test Architecture
- **Total test scenarios**: 2,200 (22 specialties × 100 cases each)
- **Positive test cases**: 1,540 (70% - valid clinical scenarios)
- **Negative test cases**: 660 (30% - edge cases, errors, boundary conditions)
- **Priority distribution**: P0: 440, P1: 880, P2: 660, P3: 220
- **Complexity levels**: Simple (30%), Realistic (50%), Complex (20%)

### Test Level Distribution
- **Unit tests**: 660 (30% - entity extraction validation)
- **Integration tests**: 1,100 (50% - NLP pipeline processing)
- **E2E tests**: 440 (20% - full FHIR bundle generation)

## Research-Driven Test Case Generation

### Primary Research Sources

#### 1. ClinicalTrials.gov API Mining
- **Purpose**: Extract authentic clinical language patterns
- **Coverage**: Real medication dosing, frequency patterns, clinical contexts
- **Implementation**: `tests/data/mine_clinicaltrials_text.py`
- **Yield**: 30+ realistic patterns per medication

#### 2. Medical Literature Patterns
- **Purpose**: Evidence-based clinical terminology
- **Sources**: Medical journals, clinical guidelines, evidence-based protocols
- **Focus**: Specialty-specific terminology, diagnostic criteria, treatment protocols

#### 3. Clinical Documentation Standards
- **Purpose**: Real-world EHR documentation patterns
- **Sources**: HL7 FHIR guides, medical coding standards, clinical workflow documentation
- **Coverage**: Structured data formats, clinical narrative styles

#### 4. Existing Realistic Generator
- **Base**: `tests/data/generate_realistic_clinical_text.py`
- **Strengths**: Complex variations, real-world messiness, clinical complications
- **Enhancement**: Scale patterns to specialty-specific requirements

## Specialty-Specific Test Design Matrix

### High-Priority Specialties (P0 - 100 cases each)

#### 1. **Emergency Medicine** (Current F1: 0.571 → Target: >0.80)
**Positive Cases (70):**
- Acute presentations: chest pain, shortness of breath, severe trauma
- Time-critical scenarios: STEMI, stroke, sepsis
- Medication urgency: stat orders, emergency dosing
- Complex multi-system cases

**Negative Cases (30):**
- Missing critical timing indicators
- Ambiguous severity markers
- Incomplete dosing information
- Non-emergency presentations misclassified

**Test Case Examples:**
```python
# Positive: Clear emergency indication
"STAT: Give patient John Smith 325mg Aspirin chewable now for acute MI presentation. ECG shows STEMI."

# Negative: Missing urgency context
"Patient reports occasional chest discomfort. Consider aspirin therapy sometime."

# Complex: Multi-system emergency
"Trauma alert: Patient Jane Doe, hypotensive, give 1L NS bolus, morphine 2-4mg IV q5min PRN severe pain, blood transfusion type and cross."
```

#### 2. **Pediatrics** (Current F1: 0.250 → Target: >0.75)
**Critical Focus**: Age-specific terminology, weight-based dosing, developmental considerations

**Positive Cases (70):**
- Weight-based dosing: mg/kg calculations
- Age-appropriate medications: pediatric formulations
- Developmental considerations: infant vs. child vs. adolescent
- Pediatric-specific conditions: failure to thrive, developmental delays

**Negative Cases (30):**
- Adult dosing applied to children
- Age-inappropriate medications
- Missing weight/age context
- Contraindicated pediatric medications

**Test Case Examples:**
```python
# Positive: Clear pediatric dosing
"Start 6-month-old Baby Johnson on amoxicillin 40mg/kg/day divided BID for acute otitis media. Weight: 8kg."

# Negative: Adult dosing pattern
"Give child 500mg amoxicillin twice daily for ear infection."

# Complex: Developmental context
"3-year-old with failure to thrive, start high-calorie formula 120cal/oz, monitor weight gain, consider GI evaluation."
```

#### 3. **Cardiology** (Current: ~0.41 → Target: >0.75)
**Positive Cases (70):**
- Cardiac medications: ACE inhibitors, beta-blockers, statins
- Dosing considerations: heart failure titration, renal function
- Cardiac conditions: MI, CHF, arrhythmias, hypertension
- Monitoring requirements: INR, electrolytes, ECG

**Negative Cases (30):**
- Contraindicated combinations
- Missing monitoring parameters
- Inappropriate dosing for cardiac conditions
- Drug interactions in cardiac patients

#### 4. **Oncology** (Current: ~0.39 → Target: >0.75)
**Positive Cases (70):**
- Chemotherapy protocols: cycle timing, pre-medications
- Supportive care: anti-emetics, growth factors
- Cancer stage considerations: adjuvant vs. metastatic
- Palliative care integration

**Negative Cases (30):**
- Inappropriate chemotherapy scheduling
- Missing supportive care medications
- Dose-limiting toxicity scenarios
- End-of-life medication conflicts

### Medium-Priority Specialties (P1 - 100 cases each)

#### Examples: Internal Medicine, Surgery, Psychiatry, Endocrinology
- Follow similar positive/negative distribution
- Focus on specialty-specific terminology
- Include common comorbidities
- Test boundary conditions

### Lower-Priority Specialties (P2/P3 - 100 cases each)

#### Examples: Dermatology, Ophthalmology, ENT, Radiology
- Simpler test scenarios
- Focus on basic medication extraction
- Limited negative case complexity

## Test Case Generation Framework

### Phase 1: Research-Based Pattern Extraction

```python
class ComprehensiveTestGenerator:
    def __init__(self):
        self.clinical_trials_miner = ClinicalTrialsMiner()
        self.realistic_generator = RealisticClinicalTextGenerator()
        self.specialty_patterns = self.load_specialty_patterns()

    def generate_specialty_cases(self, specialty: str, count: int = 100) -> List[TestCase]:
        """Generate 100 test cases for a medical specialty"""

        # Distribution: 70 positive, 30 negative
        positive_cases = self.generate_positive_cases(specialty, 70)
        negative_cases = self.generate_negative_cases(specialty, 30)

        return positive_cases + negative_cases

    def generate_positive_cases(self, specialty: str, count: int) -> List[TestCase]:
        """Generate valid clinical scenarios"""

        # 30% simple, 50% realistic, 20% complex
        simple_cases = self.generate_simple_cases(specialty, int(count * 0.3))
        realistic_cases = self.generate_realistic_cases(specialty, int(count * 0.5))
        complex_cases = self.generate_complex_cases(specialty, int(count * 0.2))

        return simple_cases + realistic_cases + complex_cases

    def generate_negative_cases(self, specialty: str, count: int) -> List[TestCase]:
        """Generate edge cases and error conditions"""

        return [
            self.generate_missing_information_cases(specialty, count // 5),
            self.generate_contraindication_cases(specialty, count // 5),
            self.generate_dosing_error_cases(specialty, count // 5),
            self.generate_terminology_ambiguity_cases(specialty, count // 5),
            self.generate_boundary_condition_cases(specialty, count // 5)
        ]
```

### Phase 2: Specialty-Specific Pattern Libraries

```python
SPECIALTY_PATTERNS = {
    "emergency": {
        "medications": ["morphine", "fentanyl", "midazolam", "epinephrine", "atropine"],
        "dosing_contexts": ["STAT", "emergent", "critical", "life-threatening"],
        "conditions": ["STEMI", "stroke", "sepsis", "trauma", "cardiac arrest"],
        "negative_patterns": ["routine", "scheduled", "elective", "non-urgent"]
    },
    "pediatrics": {
        "medications": ["amoxicillin", "acetaminophen", "ibuprofen", "albuterol"],
        "dosing_contexts": ["mg/kg", "weight-based", "age-appropriate"],
        "conditions": ["otitis media", "asthma", "fever", "failure to thrive"],
        "negative_patterns": ["adult dose", "not pediatric", "contraindicated in children"]
    },
    "cardiology": {
        "medications": ["lisinopril", "metoprolol", "atorvastatin", "warfarin"],
        "dosing_contexts": ["titrate", "monitor INR", "renal function", "heart rate"],
        "conditions": ["CHF", "MI", "atrial fibrillation", "hypertension"],
        "negative_patterns": ["bradycardia", "hypotension", "renal failure"]
    }
}
```

### Phase 3: Automated Validation Framework

```python
class SpecialtyTestValidator:
    def validate_test_case(self, test_case: TestCase) -> ValidationResult:
        """Validate generated test case for medical accuracy"""

        checks = [
            self.validate_medication_dosing(test_case),
            self.validate_clinical_context(test_case),
            self.validate_specialty_appropriateness(test_case),
            self.validate_fhir_compatibility(test_case)
        ]

        return ValidationResult(
            passed=all(checks),
            errors=[check.error for check in checks if not check.passed],
            confidence=sum(check.confidence for check in checks) / len(checks)
        )
```

## Implementation Roadmap

### Week 1: Foundation Setup
- [ ] Enhance `mine_clinicaltrials_text.py` with specialty-specific queries
- [ ] Expand `generate_realistic_clinical_text.py` with 22 specialty patterns
- [ ] Create specialty-specific pattern libraries
- [ ] Implement automated test case validation

### Week 2: High-Priority Specialties (P0)
- [ ] Generate 400 test cases for Emergency Medicine, Pediatrics, Cardiology, Oncology
- [ ] Validate medical accuracy with domain experts
- [ ] Implement negative test case patterns
- [ ] Create automated F1 validation pipeline

### Week 3: Medium-Priority Specialties (P1)
- [ ] Generate 800 test cases for 8 medium-priority specialties
- [ ] Implement specialty-specific validation rules
- [ ] Create performance comparison framework
- [ ] Validate against existing 66 realistic cases

### Week 4: Lower-Priority Specialties (P2/P3)
- [ ] Generate 1,000 test cases for remaining 10 specialties
- [ ] Implement comprehensive test suite execution
- [ ] Create performance monitoring dashboard
- [ ] Document test case sources and validation methodology

## Quality Assurance Framework

### Test Case Validation Criteria
- [ ] **Medical Accuracy**: Clinically appropriate scenarios
- [ ] **Terminology Precision**: Correct medical language usage
- [ ] **Dosing Validation**: Appropriate medication dosing patterns
- [ ] **Specialty Relevance**: Cases appropriate for medical specialty
- [ ] **FHIR Compatibility**: Extractable to valid FHIR resources
- [ ] **Complexity Distribution**: Appropriate mix of simple/complex cases

### Performance Monitoring
- [ ] **F1 Score Tracking**: Per specialty and overall performance
- [ ] **Processing Speed**: Maintain <2s response time target
- [ ] **False Positive Rate**: Monitor for over-extraction
- [ ] **False Negative Rate**: Ensure critical information capture
- [ ] **Confidence Calibration**: Validate extraction confidence scores

## Expected Outcomes

### Target Performance Metrics
- **Overall F1 Score**: >0.75 (current: 0.411)
- **Emergency Medicine F1**: >0.80 (current: 0.571)
- **Pediatrics F1**: >0.75 (current: 0.250)
- **All Specialties F1**: >0.70 minimum
- **Processing Speed**: <2s average (maintained)

### Test Coverage Improvements
- **Positive Case Coverage**: 1,540 valid clinical scenarios
- **Negative Case Coverage**: 660 edge cases and error conditions
- **Specialty Depth**: 100 cases per specialty (vs. current 3)
- **Clinical Realism**: Research-based authentic patterns
- **Validation Rigor**: Automated medical accuracy checking

## Risk Mitigation

### Clinical Risk
- **False Negative Prevention**: Comprehensive negative test case coverage
- **Medical Accuracy**: Domain expert validation of generated cases
- **Safety Validation**: Critical medication and dosing error detection

### Technical Risk
- **Performance Degradation**: Incremental rollout with performance monitoring
- **Test Maintenance**: Automated validation and update procedures
- **Scalability**: Efficient test execution and reporting framework

---

**Document Status**: Architecture Complete - Ready for Implementation
**Next Steps**: Begin Week 1 foundation setup and research source enhancement
**Validation Required**: Medical domain expert review of specialty patterns