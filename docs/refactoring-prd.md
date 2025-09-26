# NL-FHIR Codebase Refactoring PRD
**Version:** 1.0.0
**Date:** September 25, 2025
**Status:** Draft
**Product Manager:** John

## Executive Summary

This PRD defines a comprehensive refactoring initiative for the NL-FHIR v1.1.0 production codebase to address critical technical debt and improve maintainability. The primary driver is a 10,600-line God class (FHIRResourceFactory) that poses significant risks to system stability and development velocity.

## Problem Statement

### Current Pain Points
1. **God Class Architecture**: Single FHIRResourceFactory class with 219 methods spanning 10,600 lines
2. **Duplicate Infrastructure**: Complete middleware duplication between directories
3. **Legacy Code Accumulation**: Multiple backup files indicating incomplete refactoring attempts
4. **Deep Nesting Complexity**: 5-level directory structures causing import complexity
5. **Maintainability Crisis**: Any change to resource generation risks entire FHIR pipeline

### Business Impact
- **Development Velocity**: 3-5x longer to implement new FHIR resources
- **Bug Risk**: High probability of regression with any resource factory change
- **Onboarding Time**: New developers require 2-3 weeks to understand factory patterns
- **Testing Overhead**: Unable to unit test individual resource generators effectively

## Goals & Success Metrics

### Primary Goals
1. Decompose FHIRResourceFactory into domain-specific factories
2. Eliminate code duplication across middleware layers
3. Reduce maximum file size to <500 lines
4. Simplify directory structure to maximum 3 levels

### Success Metrics
- **Code Quality**: Reduce cyclomatic complexity by 60%
- **Test Coverage**: Increase unit test coverage from 45% to 80%
- **Development Speed**: Reduce new resource implementation time by 50%
- **Bug Rate**: Decrease production incidents by 40%
- **Performance**: Maintain current <2s response time

## User Stories & Requirements

### Epic 1: FHIRResourceFactory Decomposition (P0 - Critical)

**Story 1.1: Extract Patient Resource Factory**
- **As a** developer
- **I want** Patient-related resources in a dedicated factory
- **So that** I can modify patient logic without affecting other resources
- **Acceptance Criteria:**
  - PatientResourceFactory handles Patient, RelatedPerson, Person
  - Maintains backward compatibility
  - 100% test coverage for patient resources

**Story 1.2: Extract Medication Resource Factory**
- **As a** developer
- **I want** Medication resources in a dedicated factory
- **So that** medication logic is isolated and maintainable
- **Acceptance Criteria:**
  - MedicationResourceFactory handles all medication-related resources
  - Includes MedicationRequest, MedicationAdministration, MedicationStatement
  - Preserves existing validation logic

**Story 1.3: Extract Clinical Resource Factory**
- **As a** developer
- **I want** Clinical observations in a dedicated factory
- **So that** clinical data processing is modular
- **Acceptance Criteria:**
  - ClinicalResourceFactory handles Observation, DiagnosticReport, Condition
  - Maintains LOINC/SNOMED coding logic
  - Performance remains <100ms per resource

**Story 1.4: Create Factory Registry Pattern**
- **As a** system architect
- **I want** a factory registry to manage all resource factories
- **So that** resource creation is centralized but modular
- **Acceptance Criteria:**
  - FactoryRegistry dynamically loads appropriate factory
  - Supports factory extension without core changes
  - Maintains singleton pattern for efficiency

### Epic 2: Middleware Consolidation (P1 - High)

**Story 2.1: Unify Security Middleware**
- **As a** security engineer
- **I want** single security middleware implementation
- **So that** security policies are consistently applied
- **Acceptance Criteria:**
  - Consolidate `/middleware/` and `/api/middleware/`
  - Single source of truth for CORS, headers, auth
  - Maintain all existing security features

**Story 2.2: Consolidate Rate Limiting**
- **As a** platform engineer
- **I want** unified rate limiting implementation
- **So that** rate limits are consistently enforced
- **Acceptance Criteria:**
  - Single rate limiter configuration
  - Support for endpoint-specific limits
  - Redis-backed for distributed deployment

### Epic 3: Code Organization (P2 - Medium)

**Story 3.1: Flatten NLP Directory Structure**
- **As a** developer
- **I want** simpler NLP module organization
- **So that** imports are cleaner and navigation easier
- **Acceptance Criteria:**
  - Maximum 3-level nesting
  - Clear module boundaries
  - Preserve all functionality

**Story 3.2: Remove Legacy Code**
- **As a** maintainer
- **I want** legacy backup files removed
- **So that** codebase is clean and unambiguous
- **Acceptance Criteria:**
  - Remove all *_backup.py files
  - Archive any useful code snippets
  - Update documentation

## Technical Architecture

### Proposed Factory Structure
```
services/fhir/factories/
├── __init__.py (FactoryRegistry)
├── base.py (BaseResourceFactory)
├── patient_factory.py (Patient, RelatedPerson, Person)
├── medication_factory.py (Medication*, Immunization)
├── clinical_factory.py (Observation, DiagnosticReport, Condition)
├── procedure_factory.py (Procedure, ServiceRequest)
├── encounter_factory.py (Encounter, EpisodeOfCare)
├── device_factory.py (Device, DeviceUseStatement)
└── administrative_factory.py (Organization, Practitioner, Location)
```

### Dependency Injection Pattern
```python
class FactoryRegistry:
    """Central registry for all FHIR resource factories"""

    def __init__(self):
        self._factories = {}
        self._register_factories()

    def get_factory(self, resource_type: str) -> BaseResourceFactory:
        """Get appropriate factory for resource type"""
        return self._factories.get(resource_type)
```

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
1. Create BaseResourceFactory abstract class
2. Implement FactoryRegistry pattern
3. Set up comprehensive test framework
4. Create migration utilities

### Phase 2: Core Refactoring (Week 3-5)
1. Extract Patient resources (highest usage)
2. Extract Medication resources (complex logic)
3. Extract Clinical resources (performance critical)
4. Implement factory integration tests

### Phase 3: Complete Migration (Week 6-7)
1. Extract remaining resource types
2. Middleware consolidation
3. Directory structure optimization
4. Legacy code cleanup

### Phase 4: Validation & Optimization (Week 8)
1. Performance benchmarking
2. Load testing
3. Documentation updates
4. Team training

## Risk Assessment & Mitigation

### High Risks
1. **Production Breakage**
   - Mitigation: Feature flags for gradual rollout
   - Rollback: Maintain old factory alongside new

2. **Performance Degradation**
   - Mitigation: Benchmark each phase
   - Rollback: Revert to monolithic factory if needed

3. **API Contract Changes**
   - Mitigation: Extensive integration testing
   - Rollback: Adapter pattern for compatibility

### Medium Risks
1. **Incomplete Test Coverage**
   - Mitigation: Require 100% coverage for new code

2. **Team Resistance**
   - Mitigation: Involve team in design decisions

## Dependencies

### Technical Dependencies
- Python 3.10+ (current version)
- FastAPI framework
- FHIR R4 specification
- pytest for testing framework

### Team Dependencies
- 2 Senior Engineers for core refactoring
- 1 QA Engineer for test coverage
- 1 DevOps for deployment strategy

## Success Criteria

### Definition of Done
- [ ] All resource factories extracted and tested
- [ ] Middleware consolidated to single implementation
- [ ] No files exceed 500 lines
- [ ] Test coverage >80%
- [ ] Performance metrics maintained or improved
- [ ] Zero production incidents during migration
- [ ] Documentation updated
- [ ] Team trained on new architecture

## Timeline

**Total Duration:** 8 weeks

- Week 1-2: Foundation and planning
- Week 3-5: Core factory refactoring
- Week 6-7: Complete migration
- Week 8: Validation and optimization

## Appendices

### A. Current vs Proposed Metrics
| Metric | Current | Target |
|--------|---------|--------|
| Largest file | 10,600 lines | <500 lines |
| Cyclomatic complexity | 487 | <50 |
| Test coverage | 45% | 80% |
| Resource implementation time | 3 days | 1.5 days |

### B. Factory Method Mapping
[Detailed mapping of 219 methods to new factories - available in technical appendix]

---
**END OF PRD**