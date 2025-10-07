<!--
Sync Impact Report:
Version: 1.0.0 → 1.0.0 (Initial Constitution Creation)
Modified Principles: N/A (initial creation)
Added Sections: All sections (initial constitution)
Removed Sections: None
Templates Status:
  ✅ plan-template.md - Aligned with medical safety and HIPAA principles
  ✅ spec-template.md - Aligned with test-first and user story requirements
  ✅ tasks-template.md - Aligned with modular architecture and testing principles
Follow-up TODOs: None - all placeholders filled
-->

# NL-FHIR Project Constitution

## Core Principles

### I. Medical Safety First (NON-NEGOTIABLE)

**Fail-safe design is mandatory.** All clinical data processing MUST validate inputs before processing. Return errors rather than incorrect medical data. No clinical decision-making functionality without proper validation and regulatory compliance.

**Rationale:** Errors in medical AI systems can directly impact patient safety. Medical accuracy is critical and non-negotiable. This project serves research and development purposes and must maintain the highest standards of data integrity.

### II. HIPAA Compliance by Design (NON-NEGOTIABLE)

**Zero PHI in logs, code, or tests.** Use surrogate identifiers and request IDs only. All communications MUST use TLS 1.2+ encryption. Input sanitization prevents injection attacks. Complete audit logging tracks all processing without exposing protected health information.

**Rationale:** Healthcare software must comply with HIPAA regulations. Privacy violations can result in severe legal and ethical consequences. Compliance must be built into the architecture from the start, not added later.

### III. Test-First Development

**Tests written → User approved → Tests fail → Then implement.** Comprehensive test coverage across unit, integration, and epic levels mandatory. Golden dataset regression testing ensures clinical accuracy. 456+ test cases validate functionality across 22 medical specialties.

**Rationale:** Medical software requires higher reliability standards than typical applications. Test-first development prevents regressions and ensures clinical accuracy. The comprehensive test suite provides confidence in system behavior.

### IV. FHIR R4 Compliance

**100% FHIR R4 specification adherence required.** All bundles MUST validate against HAPI FHIR server. Use standardized medical terminologies (RxNorm, LOINC, ICD-10, SNOMED CT, CVX). Transaction bundles ensure atomic processing of clinical orders.

**Rationale:** Healthcare interoperability depends on strict FHIR compliance. Deviations from standards break integration with EHR systems and violate healthcare data exchange requirements.

### V. Performance Excellence

**Sub-2-second API response time target.** Real-time SLA monitoring with automatic violation detection. Model warmup eliminates cold start delays. Performance targets must be exceeded by measurable margins (current: 12-71x faster than targets).

**Rationale:** Clinical workflows require immediate response. Delays impact physician productivity and patient care quality. Performance must be monitored continuously in production environments.

### VI. Modular Factory Architecture

**Factory Registry pattern for FHIR resource creation.** Specialized factories with shared components (MedicationResourceFactory, PatientResourceFactory, ClinicalResourceFactory, DeviceResourceFactory). FactoryAdapter provides legacy compatibility during transitions. Each factory independently testable.

**Rationale:** Modular design enables independent development and testing of resource types. Factory pattern centralizes resource creation logic, ensuring consistency and facilitating maintenance across 74 FHIR resource types.

### VII. Documentation as Code

**Comprehensive documentation required for all features.** Epic and story structure with clear acceptance criteria. Architecture decisions recorded in markdown. API documentation auto-generated from code. Medical terminology and FHIR mappings must be explained.

**Rationale:** Medical software complexity requires thorough documentation. Future maintainers need clear context for clinical logic. Documentation enables clinical validation and regulatory review.

## Medical Domain Requirements

### Clinical Accuracy Standards

- **Terminology Validation:** All medical codes must use standard vocabularies (RxNorm for medications, LOINC for observations, ICD-10 for conditions, SNOMED CT for clinical concepts, CVX for vaccines)
- **Medical Specialty Support:** System MUST support 22+ medical specialties with specialty-specific terminology patterns
- **Safety Checks:** Drug interaction checking, dosage validation, high-risk medication flagging, contraindication detection
- **Audit Trail:** Complete processing trail with request IDs for compliance and debugging (without exposing PHI)

### FHIR Resource Coverage

- **74 FHIR R4 Resources Implemented:** Complete coverage across 9 clinical domains (Primary Care, Hospital/Acute Care, Laboratory Medicine, Pharmacy, Financial/Billing, Scheduling, Documentation, Research, Infrastructure)
- **Resource Dependencies:** Proper ordering in transaction bundles (6-phase optimization)
- **Reference Resolution:** Bundle-internal UUID management for resource relationships
- **Validation:** 100% HAPI FHIR validation success rate mandatory

## Technical Standards

### Development Environment

- **Language/Runtime:** Python 3.10+ (avoid 3.11+ due to dependency compatibility)
- **Package Management:** uv exclusively - NEVER run pip directly, NEVER run python without `uv run`
- **Framework:** FastAPI for REST API with automatic OpenAPI documentation
- **NLP Engine:** MedSpaCy clinical intelligence with pre-warmed models
- **Testing:** pytest with 456+ test cases, performance monitoring via `./scripts/test_performance_monitor.sh`

### Code Quality Gates

- **Formatting:** Ruff format with 88-character line length
- **Linting:** Ruff check for fast comprehensive linting
- **Type Checking:** mypy with strict mode enabled
- **Test Coverage:** Maintain >80% code coverage, 100% for critical clinical paths
- **Performance:** Factory tests <2s, infusion tests <1s, integration tests <5s

### Security Architecture

- **Authentication:** JWT-based authentication with RBAC
- **Rate Limiting:** API throttling to prevent DoS attacks
- **Input Validation:** SQL injection, XSS, command injection prevention tested
- **Security Headers:** X-Content-Type-Options, X-Frame-Options, X-XSS-Protection
- **Security Testing:** 29 security tests across 5 critical domains (HIPAA, authentication, input validation, API security, FHIR security)

## Development Workflow

### Branch Strategy

- **Feature Branches:** `feature/descriptive-name` for new features
- **Epic Branches:** `epic/epic-name` for epic-level work
- **Hotfix Branches:** `hotfix/issue-description` for production fixes
- **Main Branch:** Protected, requires PR approval and passing CI/CD

### Commit Standards

**Conventional Commits format required:**
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation updates
- `test:` Test additions/improvements
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `security:` Security enhancements

### Testing Protocol

1. **Write tests first** following test-first principle
2. **Verify tests fail** before implementation
3. **Implement feature** to pass tests
4. **Run full test suite** with `uv run pytest`
5. **Performance validation** with `./scripts/test_performance_monitor.sh`
6. **Code quality checks** with `uv run ruff check && uv run ruff format && uv run mypy src/`

### Integration Requirements

- **HAPI FHIR Integration:** All bundles validated against local HAPI FHIR server before deployment
- **Epic Structure:** Features organized into epics with clear dependencies
- **Story-Based Development:** User stories with acceptance criteria guide implementation
- **Golden Dataset Testing:** Regression testing against known-good clinical orders

## Governance

### Amendment Process

1. **Propose Change:** Create GitHub issue describing constitutional change with rationale
2. **Discussion Period:** Minimum 7 days for community review and feedback
3. **Version Increment:** Follow semantic versioning (MAJOR for breaking changes, MINOR for additions, PATCH for clarifications)
4. **Documentation Update:** Update this constitution and propagate changes to dependent templates
5. **Migration Plan:** For breaking changes, provide migration path for existing code

### Compliance Verification

- **All PRs MUST verify compliance** with constitutional principles before merge
- **CI/CD Pipeline:** Automated checks enforce code quality, testing, and security standards
- **Epic Completion Gates:** Each epic requires 100% story completion and validation
- **Security Audits:** Regular security testing with comprehensive test suite
- **Performance Monitoring:** Continuous SLA tracking in production

### Exception Process

**Complexity must be justified.** Any violation of core principles requires:
1. **Documented Justification:** Explain why the principle cannot be followed
2. **Simpler Alternative Analysis:** Document why simpler alternatives were rejected
3. **Technical Review:** Architecture approval for deviations
4. **Migration Plan:** Path to eventually conform to principles if temporarily violating

### Runtime Development Guidance

For day-to-day development guidance and tool usage, refer to:
- **CLAUDE.md** - Project-specific instructions for Claude Code agent
- **README.md** - Quick start guide and development commands
- **CONTRIBUTING.md** - Contribution guidelines and workflows
- **docs/architecture/coding-standards.md** - Detailed code style requirements

**Version**: 1.0.0 | **Ratified**: 2025-10-06 | **Last Amended**: 2025-10-06
