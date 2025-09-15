# Pull Request

## 📋 Description

<!-- Provide a clear and concise description of your changes -->

### What does this PR do?
<!-- Describe the main functionality or fix this PR introduces -->

### Related Issues
<!-- Link to any related issues. Use "Fixes #123" or "Addresses #123" -->
- Fixes #
- Addresses #

## 🏥 Medical/Clinical Impact

<!-- Describe the medical or clinical significance of these changes -->

### Clinical Benefits
<!-- How does this improve patient care or clinical workflows? -->
-

### Medical Safety Considerations
<!-- Any safety implications, drug interactions, dosing considerations, etc. -->
-

### FHIR Compliance
<!-- How do these changes maintain or improve FHIR R4 compliance? -->
-

## 🔧 Type of Change

<!-- Check all that apply -->
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🧪 Test improvements
- [ ] 🔒 Security fix
- [ ] ⚡ Performance improvement
- [ ] 🔧 Code refactoring

## 🧪 Testing

<!-- Describe the testing you have performed -->

### Test Coverage
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Epic-level tests added/updated
- [ ] Manual testing performed

### FHIR Validation
- [ ] All generated bundles validate against HAPI FHIR R4
- [ ] Bundle structure follows FHIR specification
- [ ] Resource relationships are correct

### Medical Accuracy Testing
- [ ] Tested with diverse medical specialties
- [ ] Validated medical terminology usage
- [ ] Checked dosage and frequency accuracy
- [ ] Verified clinical context preservation

### Performance Testing
- [ ] Response time within acceptable limits (<2s)
- [ ] Memory usage is reasonable
- [ ] No performance regressions identified

## ✅ Checklist

### Code Quality
- [ ] My code follows the project's coding standards
- [ ] I have performed a self-review of my code
- [ ] I have commented complex code sections
- [ ] My changes generate no new warnings
- [ ] I have added type hints where applicable

### Testing Requirements
- [ ] I have added tests that prove my fix is effective or feature works
- [ ] New and existing unit tests pass locally
- [ ] Integration tests pass
- [ ] FHIR validation tests pass

### Documentation
- [ ] I have updated relevant documentation
- [ ] I have added docstrings to new functions/classes
- [ ] API documentation is updated (if applicable)
- [ ] Medical terminology is properly documented

### Security & Compliance
- [ ] No real PHI (Patient Health Information) is included
- [ ] All test data is synthetic
- [ ] Security implications have been considered
- [ ] HIPAA compliance is maintained

### Medical Ethics & Safety
- [ ] Changes prioritize patient safety
- [ ] Medical accuracy has been verified
- [ ] Clinical workflows are considered
- [ ] No potential for harmful medical misinformation

## 🔬 Test Results

<!-- Include relevant test results -->

### Automated Test Results
```
# Paste test output here
```

### FHIR Validation Results
<!-- Include HAPI FHIR validation results if applicable -->
- Bundles tested:
- Validation success rate:
- Resource types validated:

### Performance Metrics
<!-- Include performance measurements if applicable -->
- Average response time:
- Memory usage:
- Throughput:

## 📸 Screenshots/Examples

<!-- If applicable, add screenshots or example inputs/outputs -->

### Before
<!-- Screenshots or examples of behavior before your changes -->

### After
<!-- Screenshots or examples of behavior after your changes -->

### Sample Usage
<!-- Provide examples of how to use the new feature -->

```python
# Example code or API usage
```

## 🔗 Additional Context

<!-- Add any other context about the pull request here -->

### Dependencies
<!-- List any new dependencies added -->
-

### Breaking Changes
<!-- Describe any breaking changes and migration path -->
-

### Future Considerations
<!-- Any follow-up work or considerations for future development -->
-

## 👥 Reviewers

<!-- Tag specific reviewers if needed -->
<!-- @username for medical accuracy review -->
<!-- @username for security review -->
<!-- @username for FHIR compliance review -->

---

**By submitting this pull request, I confirm that:**
- [ ] I have read and followed the project's contributing guidelines
- [ ] I understand the medical responsibility of this healthcare software
- [ ] I have used only synthetic data for testing
- [ ] I have considered patient safety in all changes
- [ ] I agree to the project's Code of Conduct