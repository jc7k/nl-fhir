# Pre-Pull Request Checklist

**IMPORTANT**: Complete this checklist BEFORE creating a pull request to avoid common code review issues.

## 🤖 Automated Checks (Run These First)

### 1. Code Review Agent
```bash
# Use Claude's code-reviewer agent to review your changes
# This catches most issues before human review
```

### 2. Test Suite
```bash
# Run all tests
uv run pytest

# Run specific test files related to your changes
uv run pytest tests/path/to/test.py -v

# Run with coverage
uv run pytest --cov=src/nl_fhir --cov-report=term-missing
```

### 3. Linting & Formatting
```bash
# Check code style
uv run ruff check src/ tests/

# Auto-format code
uv run ruff format src/ tests/

# Type checking
uv run mypy src/
```

## ✅ Manual Review Checklist

### Code Quality
- [ ] **No duplicate code** - Check for patterns that should be consolidated
- [ ] **Proper imports** - Import from the correct modules (e.g., ValidationSeverity from validation_common)
- [ ] **Type hints** - All functions have proper type annotations
- [ ] **Error handling** - Graceful handling of edge cases and errors
- [ ] **No commented code** - Remove or explain any commented code blocks

### Common Issues (Based on PR History)

#### 1. Regex Patterns
- [ ] Use `re.escape()` for special characters in dynamic patterns
- [ ] Use word boundaries (`\b`) to prevent false positive substring matches
- [ ] Test regex patterns with edge cases

#### 2. Validation & Safety
- [ ] High-risk medication detection uses word boundary matching
- [ ] No false positives (e.g., "counseling" triggering "insulin")
- [ ] Validation patterns are consolidated in `validation_common.py`

#### 3. Backward Compatibility
- [ ] Existing APIs maintained (add aliases if needed)
- [ ] Legacy methods provided for deprecated functionality
- [ ] Migration path documented for breaking changes

#### 4. Import Organization
- [ ] Enums imported from `validation_common` not individual services
- [ ] Lazy loading for performance-critical imports
- [ ] No circular import dependencies

#### 5. Testing
- [ ] New functionality has test coverage
- [ ] Edge cases are tested
- [ ] Backward compatibility is tested
- [ ] Integration tests pass

### Security & Compliance
- [ ] **No PHI in logs** - Use request IDs and surrogate identifiers only
- [ ] **No secrets** - No hardcoded credentials or API keys
- [ ] **Input sanitization** - User input is properly validated
- [ ] **HIPAA compliance** - Medical data handling follows guidelines

### Documentation
- [ ] **Docstrings** - All new functions/classes have docstrings
- [ ] **Type hints** - Complex types are properly annotated
- [ ] **Migration notes** - Document any migration requirements
- [ ] **REFACTOR tags** - Add story IDs for refactoring work

## 📊 Performance Considerations
- [ ] **No N+1 queries** - Batch database operations where possible
- [ ] **Lazy loading** - Don't compute expensive operations at import time
- [ ] **Caching** - Use caching for expensive repeated operations
- [ ] **Memory usage** - Avoid loading large datasets into memory

## 🔍 Final Checks Before PR

### 1. Commit Quality
```bash
# Ensure commits are atomic and well-described
git log --oneline -5

# Squash if needed
git rebase -i HEAD~N
```

### 2. Branch Cleanliness
```bash
# Ensure branch is up to date with main
git fetch origin main
git rebase origin/main

# Check for conflicts
git status
```

### 3. PR Description Template
Ensure your PR description includes:
- **Summary** - What changed and why
- **Testing** - How it was tested
- **Breaking changes** - Any backward compatibility issues
- **Story/Issue ID** - Reference to tracking system

## 🚀 Common Commands Reference

```bash
# Run comprehensive pre-PR check
uv run pytest && uv run ruff check && uv run ruff format

# Check what files changed
git diff --name-only origin/main

# Run tests for changed files only
git diff --name-only origin/main | grep "\.py$" | xargs uv run pytest

# Check for common issues
grep -r "ValidationSeverity.INFO" src/  # Should use INFORMATION
grep -r "HIGH_RISK_MEDS.*in.*medication_lower" src/  # Should use word boundaries
```

## 📝 PR Title Conventions

Use these prefixes for clear PR categorization:
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring (REFACTOR-XXX stories)
- `test:` - Test additions/changes
- `docs:` - Documentation only
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

Example: `refactor: REFACTOR-009C Migrate clinical_validator to unified models`

## 🎯 Success Metrics

A good PR should have:
- ✅ All automated checks passing
- ✅ Zero code review comments about preventable issues
- ✅ Clear, atomic commits
- ✅ Comprehensive test coverage
- ✅ No regression in existing functionality

---

**Remember**: It's better to spend 10 minutes on pre-PR review than 2 hours fixing issues after code review!