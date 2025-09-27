# Story: Clean Up Deprecated/Backup Files

**Story ID:** REFACTOR-008
**Epic:** Code Cleanup (Epic 2)
**Status:** READY FOR DEVELOPMENT
**Estimated Effort:** 2 hours
**Priority:** P2 - Medium

## User Story

**As a** developer
**I want** deprecated and backup files removed from the codebase
**So that** the project structure is clean and maintainable without confusion

## Background & Context

After successful completion of REFACTOR-006 (unified security middleware) and REFACTOR-007 (middleware cleanup), several old backup files remain in the codebase that are no longer needed:

**Files Identified for Removal:**
- `src/nl_fhir/services/summarization_old.py` (178 lines) - Old template-based summarizer
- `src/nl_fhir/services/nlp/models_backup.py` (1,431 lines) - Old NLP model manager
- `src/nl_fhir/main_backup.py` (1,193 lines) - Old main application file

**Current References:**
- `summarization_old.py` is imported by:
  - `src/nl_fhir/services/hybrid_summarizer.py` (line 10)
  - `src/nl_fhir/api/dependencies.py` (line 12)

**Newer Alternatives Available:**
- New summarization framework: `src/nl_fhir/services/summarization/`
- Current main application: `src/nl_fhir/main.py` (uses modern summarization_router)
- Modern NLP models in production use

## Analysis

### Impact Assessment

**Low Risk Removal:**
- `main_backup.py` - No references found, clearly a backup
- `models_backup.py` - No references found, contains old NLP patterns

**Requires Migration:**
- `summarization_old.py` - Has active imports that need to be updated

### Migration Plan

1. **Update hybrid_summarizer.py**: Replace `SummarizationService` import with modern equivalent
2. **Update dependencies.py**: Replace legacy summarization service
3. **Remove backup files**: Delete unused backup files safely

## Acceptance Criteria

### Must Have
- [ ] Update imports in `hybrid_summarizer.py` to use modern summarization
- [ ] Update imports in `api/dependencies.py` to use modern summarization
- [ ] Remove `src/nl_fhir/services/summarization_old.py`
- [ ] Remove `src/nl_fhir/services/nlp/models_backup.py`
- [ ] Remove `src/nl_fhir/main_backup.py`
- [ ] All tests continue to pass
- [ ] Application starts successfully
- [ ] No broken imports or references

### Should Have
- [ ] Verify no functionality regression
- [ ] Clean up any related __pycache__ files
- [ ] Update any documentation references if needed

## Technical Implementation

### 1. Migration Steps

```python
# Update src/nl_fhir/services/hybrid_summarizer.py
# Replace:
from .summarization_old import SummarizationService

# With:
from .summarization.fhir_bundle_summarizer import FHIRBundleSummarizer

# Update class initialization:
# Replace:
self.template_summarizer = SummarizationService()

# With:
self.template_summarizer = FHIRBundleSummarizer()
```

```python
# Update src/nl_fhir/api/dependencies.py
# Replace:
from ..services.summarization_old import SummarizationService

# With:
from ..services.summarization.fhir_bundle_summarizer import FHIRBundleSummarizer
```

### 2. Safe Removal Commands

```bash
# After migration, remove deprecated files
rm src/nl_fhir/services/summarization_old.py
rm src/nl_fhir/services/nlp/models_backup.py
rm src/nl_fhir/main_backup.py

# Clean up compiled cache
find src/nl_fhir -name "__pycache__" -exec rm -rf {} \; 2>/dev/null || true
```

### 3. Verification Steps

```bash
# Test imports
uv run python -c "from src.nl_fhir.services.hybrid_summarizer import HybridSummarizer; print('OK')"

# Test application startup
uv run uvicorn src.nl_fhir.main:app --host 0.0.0.0 --port 8001 --reload --timeout-keep-alive 5 &
sleep 5
curl http://localhost:8001/health
pkill -f uvicorn

# Run tests
uv run pytest tests/ -v --tb=short
```

## Risk Assessment

**Risk Level:** Low
- Backup files have no critical functionality
- Modern alternatives are already implemented and in use
- Changes are isolated to import statements

**Mitigation:**
- Test thoroughly before removing files
- Verify all imports work correctly
- Keep git history for potential rollback

## Success Metrics

- **Lines of code removed**: ~2,800 lines
- **Files removed**: 3 deprecated files
- **Zero breaking changes**: All tests pass
- **Clean imports**: No import errors

## Definition of Done

- [ ] All deprecated files successfully removed
- [ ] Import statements updated to use modern services
- [ ] Application starts without errors
- [ ] All existing tests pass
- [ ] No broken imports or missing references
- [ ] Code reduction achieved (2,800+ lines removed)

---
**Story Status:** READY FOR DEVELOPMENT
**Dependencies:** None
**Next Story:** Continue with validation services consolidation