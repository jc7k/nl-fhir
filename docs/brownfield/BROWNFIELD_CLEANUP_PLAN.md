# Brownfield Test Cleanup Plan

**Created**: November 2, 2025
**Status**: Ready for Implementation
**Target**: v1.2.2 (Factory Tests) and v1.3.0 (Security Fixes)

## 📊 Overview

After successfully releasing v1.2.1 with critical CI/CD fixes, we have 5 brownfield issues representing **50 failing tests** that need systematic cleanup.

**Release v1.2.1 Status**: ✅ GREEN - Main branch stable
**Brownfield Issues**: 5 issues, 50 tests, ~15-20 hours effort

---

## 🎯 Execution Strategy

### Phase 1: Factory Test Cleanup (v1.2.2)

**Target**: Issues #51, #52, #53, #54
**Tests**: 39 total
**Effort**: ~6-8 hours
**Priority**: MEDIUM
**Risk**: LOW

### Phase 2: Security Fixes (v1.3.0)

**Target**: Issue #43
**Tests**: 11 total
**Effort**: ~8-12 hours
**Priority**: CRITICAL
**Risk**: HIGH - Requires proper security review

---

## 📋 Phase 1: Factory Test Cleanup

### Issue #51 - Medication Factory Tests (16 tests)

**Root Cause**: Tests accessing private methods that no longer exist after factory refactoring

**Example Failure**:

```python
# Test expects private method
code = factory._lookup_rxnorm_code('Metformin')
# Error: AttributeError: 'MedicationResourceFactory' object has no attribute '_lookup_rxnorm_code'
```

**Failed Tests**:

```
tests/services/fhir/factories/test_medication_factory.py::TestMedicationResourceFactory::test_rxnorm_medication_lookup
tests/services/fhir/factories/test_medication_factory.py::TestMedicationResourceFactory::test_pharmacy_workflow_support
tests/services/fhir/factories/test_medication_factory.py::TestMedicationResourceFactory::test_performance_monitoring
tests/services/fhir/factories/test_medication_factory.py::TestMedicationResourceFactory::test_health_check
tests/services/fhir/factories/test_medication_factory.py::TestMedicationResourceFactory::test_error_handling_invalid_resource_type
tests/services/fhir/factories/test_medication_factory.py::TestMedicationResourceFactory::test_error_handling_missing_required_data
tests/services/fhir/factories/test_medication_factory.py::TestMedicationResourceFactory::test_ndc_code_validation
tests/services/fhir/factories/test_medication_factory.py::TestMedicationResourceFactory::test_medication_strength_parsing
tests/services/fhir/factories/test_medication_factory.py::TestMedicationResourceFactory::test_concurrent_medication_checking
tests/services/fhir/factories/test_medication_factory.py::TestMedicationResourceFactory::test_performance_requirements
tests/services/fhir/factories/test_medication_factory.py::TestMedicationFactoryIntegration::test_factory_registry_integration
tests/services/fhir/factories/test_medication_factory_basic.py::TestMedicationFactoryIntegration::test_factory_registry_integration
```

**Fix Strategy**:

1. Read test file to understand what's being tested
2. Identify if functionality still exists (public API vs removed feature)
3. Update tests to use public API or remove obsolete tests
4. Verify no functional regressions

**Acceptance Criteria**:

- [ ] All 16 tests passing or properly removed if obsolete
- [ ] Factory functionality verified through public API
- [ ] No new test failures introduced

---

### Issue #54 - Factory Integration Tests (16 tests)

**Root Cause**: Factory registry and architecture changes after FactoryAdapter introduction

**Failed Test Categories**:

- Factory Registry Tests (6 failures)
- Base Factory Tests (3 failures)
- CarePlan Factory Tests (2 failures)
- Clinical Factory Tests (2 failures)
- Encounter Factory Tests (2 failures)
- Patient Factory Test (1 failure)

**Key Areas**:

1. Feature flag integration behavior
2. Legacy factory fallback mechanism
3. Factory statistics API
4. Cross-factory references
5. Unknown resource type handling

**Fix Strategy**:

1. Review FactoryAdapter implementation
2. Update tests for new registry behavior
3. Verify feature flags work correctly
4. Test legacy fallback paths
5. Validate cross-factory integration

**Acceptance Criteria**:

- [ ] All 16 integration tests passing
- [ ] Feature flags verified functional
- [ ] Legacy compatibility maintained
- [ ] Registry delegation working

---

### Issue #52 - Validator Tests (5 tests)

**Status**: Not yet analyzed in detail

**Fix Strategy**:

1. Run tests to identify failure patterns
2. Review validator implementation changes
3. Update tests to match current validator API
4. Verify validation logic correctness

**Acceptance Criteria**:

- [ ] All 5 validator tests passing
- [ ] Validation functionality verified
- [ ] No validation regressions

---

### Issue #53 - Reference Manager Tests (2 tests)

**Status**: Not yet analyzed in detail

**Fix Strategy**:

1. Run tests to see error messages
2. Check ReferenceManager API changes
3. Update test expectations
4. Verify reference handling works

**Acceptance Criteria**:

- [ ] Both reference manager tests passing
- [ ] Reference resolution functional

---

## 🔒 Phase 2: Security Fixes (CRITICAL)

### Issue #43 - Security Vulnerabilities (11 tests)

**⚠️ WARNING**: These are REAL SECURITY ISSUES, not just test failures

**HIPAA Compliance Violations (5 tests)**:

- ❌ `test_phi_not_in_logs` - PHI data appearing in application logs
- ❌ `test_audit_logging_without_phi` - Audit logs contain PHI
- ❌ `test_resource_access_control_simulation` - Access control not enforced
- ❌ `test_sensitive_data_handling` - Sensitive data handling gaps
- ❌ `test_hipaa_compliance_summary` - Overall compliance issues

**Input Validation Gaps (3 tests)**:

- ❌ `test_sql_injection_prevention` - SQL injection vulnerabilities
- ❌ `test_xss_prevention` - XSS prevention missing
- ❌ `test_command_injection_prevention` - Command injection risks

**Access Control Issues (3 tests)**:

- ❌ `test_role_based_access_control` - RBAC not implemented
- ❌ `test_fhir_resource_access_control` - Resource-level permissions missing
- ❌ `test_fhir_bundle_security` - Bundle security validation gaps

**Fix Priority Order**:

1. **P0 - HIPAA PHI Logging** (Compliance-critical)

   - Remove PHI from application logs
   - Sanitize audit logs
   - Implement proper logging redaction

2. **P0 - Input Validation** (Security-critical)

   - SQL injection prevention
   - XSS prevention
   - Command injection prevention

3. **P1 - Access Control** (Data protection)
   - Implement RBAC
   - Resource-level permissions
   - Bundle security validation

**Security Review Requirements**:

- [ ] Code review by security-conscious developer
- [ ] Verify fixes don't introduce new vulnerabilities
- [ ] Test all security controls thoroughly
- [ ] Document security architecture
- [ ] Consider penetration testing

**Acceptance Criteria**:

- [ ] All 11 security tests passing
- [ ] No PHI in logs verified
- [ ] Input validation comprehensive
- [ ] Access controls functional
- [ ] Security documentation complete

---

## 🚀 Implementation Guide

### Session 1: Factory Tests (Issues #51-54)

**Pre-work** (5 minutes):

```bash
git checkout main
git pull origin main
git checkout -b fix/brownfield-factory-tests
```

**Execution Order**:

1. Issue #53 (2 tests) - Warmup, smallest scope
2. Issue #52 (5 tests) - Small scope
3. Issue #51 (16 tests) - Medication factory
4. Issue #54 (16 tests) - Integration tests

**Testing Strategy**:

```bash
# Run individual test to see error
uv run pytest path/to/test::TestClass::test_name -xvs --no-cov

# Fix and verify
uv run pytest path/to/test::TestClass::test_name -xvs --no-cov

# Run full suite at end
uv run pytest tests/services/fhir/factories/ -v --no-cov
```

**Commit Strategy**:

- One commit per issue fixed
- Include test results in commit message
- Reference issue number

**Expected Outcome**:

- PR for v1.2.2 with 39 factory tests fixed
- All factory test suites green
- No functional regressions

---

### Session 2: Security Fixes (Issue #43)

**⚠️ IMPORTANT**: Dedicated session with proper security focus

**Pre-work** (10 minutes):

```bash
git checkout main
git pull origin main
git checkout -b security/fix-hipaa-and-validation-issues
```

**Execution Order**:

1. **Audit current logging** - Understand where PHI appears
2. **Design logging redaction** - Plan PHI removal strategy
3. **Implement PHI redaction** - Fix logging issues
4. **Input validation review** - Analyze current validation
5. **Implement validation** - Add SQL/XSS/Command injection prevention
6. **Access control design** - Plan RBAC architecture
7. **Implement RBAC** - Add access controls
8. **Security testing** - Verify all fixes

**Security Checklist**:

- [ ] No PHI in ANY logs (app logs, audit logs, error logs)
- [ ] All user inputs validated and sanitized
- [ ] SQL parameterization used everywhere
- [ ] XSS prevention via output encoding
- [ ] Command execution properly sandboxed
- [ ] RBAC roles defined and enforced
- [ ] Resource-level permissions working
- [ ] Security documentation updated

**Expected Outcome**:

- PR for v1.3.0 with security fixes
- All security tests green
- Security audit documentation
- No new vulnerabilities introduced

---

## 📊 Success Metrics

### Phase 1 Success Criteria

- ✅ 39/39 factory tests passing
- ✅ No functional regressions
- ✅ CI/CD green with factory tests
- ✅ v1.2.2 released

### Phase 2 Success Criteria

- ✅ 11/11 security tests passing
- ✅ HIPAA compliance verified
- ✅ Security audit complete
- ✅ v1.3.0 released

### Overall Success

- ✅ 50/50 brownfield tests resolved
- ✅ All `continue-on-error` flags removed from CI/CD
- ✅ Full green pipeline
- ✅ Production-ready security posture

---

## 🔗 References

**Issues**:

- #51 - Medication factory tests
- #52 - Validator tests
- #53 - Reference manager tests
- #54 - Factory integration tests
- #43 - Security vulnerabilities

**Current Status**:

- v1.2.1 - Released (CI/CD fixes)
- Main branch - GREEN
- Factory tests - 207/246 passing (84%)
- Security tests - 0/11 passing (bypassed with continue-on-error)

**Documentation**:

- Issue tracker: https://github.com/jc7k/nl-fhir/issues
- Release: https://github.com/jc7k/nl-fhir/releases/tag/v1.2.1

---

## ⏭️ Next Steps

1. **Review this plan** before starting Session 1
2. **Schedule dedicated time** for each phase
3. **Start with Phase 1** (factory tests)
4. **Security session** should be when fresh and focused
5. **Celebrate progress** - v1.2.1 was a major win!

**Estimated Timeline**:

- Session 1 (Factory): 6-8 hours
- Session 2 (Security): 8-12 hours
- Total: 14-20 hours over 2-3 sessions

---

_Created as part of v1.2.1 release session - November 2, 2025_
