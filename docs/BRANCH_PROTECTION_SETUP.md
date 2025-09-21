# 🛡️ GitHub Branch Protection Setup Guide

## Overview

This guide provides instructions for setting up community-friendly branch protection rules that encourage contributions while maintaining code quality for the open source NL-FHIR medical AI project.

## 🎯 Branch Strategy

### Main Branches
- **`main`**: Production-ready code for open source community
- **`internal-dev`**: Private development tools and proprietary elements
- **`develop`**: Integration branch for community contributions (optional)

### Feature Branches
- **`feature/*`**: Community feature development
- **`hotfix/*`**: Production fixes
- **`docs/*`**: Documentation improvements (lower barriers)

## 🔧 Branch Protection Rules Configuration

### Main Branch Protection

Navigate to: **Settings** → **Branches** → **Add rule** → **Branch name pattern**: `main`

#### ✅ Recommended Settings for Community Projects

**Protect matching branches:**
```yaml
☑️ Require a pull request before merging
  ☑️ Require approvals: 1-2 reviewers (not excessive for community)
  ☑️ Dismiss stale PR approvals when new commits are pushed
  ☑️ Require review from code owners (if CODEOWNERS file exists)
  ☐ Restrict pushes that create files larger than 100MB
  ☐ Require approval of the most recent reviewable push

☑️ Require status checks to pass before merging
  ☑️ Require branches to be up to date before merging
  Status checks (add when CI/CD is configured):
  - ✅ continuous-integration/github-actions
  - ✅ test-suite
  - ✅ medical-accuracy-validation
  - ✅ fhir-compliance-check
  - ✅ security-scan

☑️ Require conversation resolution before merging

☐ Require signed commits (optional - may reduce contributions)

☐ Require linear history (optional - may complicate community PRs)

☐ Require deployments to succeed before merging

☑️ Lock branch (prevents force pushes and deletions)

☑️ Do not allow bypassing the above settings
  ☐ Restrict pushes that create files larger than 100MB
```

### Additional Branch Protections

**Internal Development Branch:**
```yaml
Branch name pattern: internal-dev
☑️ Restrict pushes that create files larger than 100MB
☑️ Lock branch
☑️ Require administrators to follow these rules
```

**Documentation Branches (Lower Barrier):**
```yaml
Branch name pattern: docs/*
☑️ Require a pull request before merging
  ☑️ Require approvals: 1 reviewer
☑️ Allow force pushes (for documentation iteration)
☐ Require status checks (documentation may not need CI)
```

## 🏥 Medical AI-Specific Considerations

### Required Status Checks

**Medical Accuracy Validation:**
- Clinical terminology validation
- Medical entity extraction accuracy tests
- FHIR compliance verification
- Drug interaction safety checks (when applicable)

**Security and Privacy:**
- HIPAA compliance validation
- PHI detection scans (should find none)
- Security vulnerability scans
- Dependency security checks

**Code Quality:**
- Python linting (ruff)
- Type checking (mypy)
- Test coverage requirements
- Medical safety code review

### Code Owners File (Optional)

Create `.github/CODEOWNERS` for automatic review assignments:

```
# Global owners for medical AI safety
* @medical-team-lead @ai-safety-expert

# Medical NLP and entity extraction
/src/nl_fhir/services/nlp/ @medical-nlp-expert @clinical-reviewer

# FHIR resource generation
/src/nl_fhir/services/fhir/ @fhir-expert @healthcare-interop-lead

# Medical terminology and safety
/src/nl_fhir/models/ @clinical-terminology-expert

# Security and privacy
/src/nl_fhir/api/middleware/ @security-expert
/SECURITY.md @security-expert

# Documentation requiring medical review
/docs/MEDICAL_SAFETY.md @medical-team-lead @regulatory-expert
```

## 🤝 Community-Friendly Practices

### Encouraging Contributions

**Low-Barrier Areas:**
- Documentation improvements
- Test case additions
- Medical terminology enhancements
- Performance optimizations

**Medium-Barrier Areas:**
- New medical specialty support
- FHIR resource additions
- API endpoint enhancements

**High-Barrier Areas:**
- Core medical NLP logic
- Safety-critical components
- Security implementations

### Auto-Labeling and Triage

Configure GitHub Actions for automatic issue/PR labeling:

```yaml
# .github/labeler.yml
medical-safety:
  - docs/MEDICAL_SAFETY.md
  - src/nl_fhir/services/medical_safety/

fhir-compliance:
  - src/nl_fhir/services/fhir/
  - tests/validation/

security:
  - SECURITY.md
  - src/nl_fhir/api/middleware/security*

documentation:
  - docs/**
  - README.md
  - CONTRIBUTING.md

community:
  - .github/**
  - CONTRIBUTING.md
  - CODE_OF_CONDUCT.md
```

## 🚀 CI/CD Integration

### Required Automated Checks

**Medical AI Validation Pipeline:**
```yaml
name: Medical AI Validation
on: [pull_request]
jobs:
  medical-accuracy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run medical accuracy tests
        run: uv run pytest tests/validation/ --medical-accuracy

  fhir-compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: FHIR R4 validation
        run: |
          docker-compose up -d hapi-fhir
          uv run pytest tests/fhir/ --fhir-validation

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Security vulnerability scan
        run: |
          pip install safety bandit
          safety check
          bandit -r src/

  hipaa-compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: PHI detection scan
        run: |
          # Scan for potential PHI patterns
          uv run python scripts/phi_detection_scan.py
```

### Status Check Configuration

Enable these status checks in branch protection:
- ✅ `ci/medical-accuracy`
- ✅ `ci/fhir-compliance`
- ✅ `ci/security-scan`
- ✅ `ci/hipaa-compliance`
- ✅ `ci/test-suite`
- ✅ `ci/code-quality`

## 📋 Implementation Checklist

### Initial Setup
- [ ] Configure main branch protection rules
- [ ] Set up internal-dev branch protection
- [ ] Create CODEOWNERS file (optional)
- [ ] Configure auto-labeling for issues/PRs
- [ ] Set up CI/CD pipeline with medical AI validation

### Community Onboarding
- [ ] Add "good first issue" labels for newcomers
- [ ] Create issue templates for different contribution types
- [ ] Document review process in CONTRIBUTING.md
- [ ] Set up discussion forums for community questions

### Medical AI Specific
- [ ] Implement medical accuracy validation in CI
- [ ] Set up FHIR compliance checking
- [ ] Configure PHI detection scans
- [ ] Add medical safety review requirements

### Monitoring and Maintenance
- [ ] Monitor contribution patterns and adjust barriers
- [ ] Regular review of protection rules effectiveness
- [ ] Community feedback collection and incorporation
- [ ] Quarterly security and compliance audits

## 🔍 Testing Branch Protection

### Validation Steps

1. **Create test PR** with medical changes
2. **Verify all status checks** run and pass
3. **Test review requirement** enforcement
4. **Confirm protection against** force pushes
5. **Validate medical accuracy** review process

### Common Issues and Solutions

**Problem:** Contributors struggle with complex review process
**Solution:** Provide clear contribution guidelines and mentorship

**Problem:** CI checks fail frequently on community PRs
**Solution:** Improve test reliability and provide better error messages

**Problem:** Medical accuracy reviews create bottlenecks
**Solution:** Train additional community members in medical review

## 📞 Support and Documentation

### Community Resources
- **Contributing Guide**: Detailed medical AI contribution process
- **Discord/Slack**: Real-time community support
- **Office Hours**: Regular video calls for complex contributions
- **Mentorship Program**: Pair new contributors with experienced members

### Maintainer Resources
- **Review Guidelines**: Consistent criteria for medical AI code review
- **Security Playbooks**: Response procedures for security issues
- **Medical Safety Protocols**: Handling clinical accuracy concerns
- **Community Management**: Building inclusive healthcare AI community

---

## 🎯 Success Metrics

Track these metrics to evaluate branch protection effectiveness:

- **Contribution Rate**: Number of community PRs per month
- **Review Time**: Average time from PR creation to merge
- **Quality Metrics**: Post-merge bug rate and medical accuracy
- **Community Growth**: Active contributors and issue engagement
- **Security Posture**: Vulnerability detection and resolution time

**Remember:** The goal is to balance community accessibility with medical AI safety and code quality. Adjust rules based on community feedback and project needs.