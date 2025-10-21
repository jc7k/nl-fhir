# NLP Service Refactoring Guide

**Status**: Compatibility shim completed
**Date**: 2025-10-19
**Migration**: Backward compatible via `services/nlp/models.py`

---

## Architecture Change: Monolithic → Modular

### Old Structure (Pre-Refactoring)
```
services/nlp/
  └── models.py  # Monolithic NLPModelManager with all logic (~800 lines)
```

### New Structure (Current)
```
services/nlp/
  ├── models.py                    # Compatibility shim (maintains backward compatibility)
  ├── model_managers/              # Model loading and caching
  │   ├── transformer_manager.py   # Transformer models (Medical-NER, embeddings)
  │   ├── spacy_manager.py         # spaCy model management
  │   └── medspacy_manager.py      # MedSpaCy clinical intelligence
  ├── extractors/                  # Entity extraction logic
  │   ├── medical_entity_extractor.py  # Main 4-tier extraction
  │   ├── regex_extractor.py       # Regex-based fallback
  │   └── llm_extractor.py         # LLM escalation
  ├── quality/                     # Quality scoring and escalation
  │   ├── quality_scorer.py        # Confidence metrics
  │   └── escalation_manager.py    # LLM escalation decisions
  └── llm/                         # LLM integration
      ├── models/response_models.py # Pydantic response models
      └── processors/              # LLM processors
```

---

## Breaking Changes

### ❌ Field Rename: `instructions` → `clinical_instructions`

**Affected**: LLM response models, structured output

**Location**: `services/nlp/llm/models/response_models.py:44`

```python
# OLD (deprecated)
assert "instructions" in structured_output

# NEW (correct)
assert "clinical_instructions" in structured_output
```

**Migration**: Update all test assertions and API consumers to use `clinical_instructions`

---

## Compatibility Shim API

### Purpose
The compatibility shim (`services/nlp/models.py`) maintains backward compatibility for existing tests and code that depend on the original monolithic API.

### Available Methods

#### ✅ Model Loading
```python
from src.nl_fhir.services.nlp.models import model_manager

# All original model loading methods preserved
model_manager.load_medical_ner_model()
model_manager.load_spacy_medical_nlp()
model_manager.load_medspacy_clinical_engine()
model_manager.load_sentence_transformer()
model_manager.load_fallback_nlp()
```

#### ✅ Entity Extraction
```python
# Main extraction method (delegates to MedicalEntityExtractor)
entities = model_manager.extract_medical_entities(text)
```

#### ✅ Quality & Escalation
```python
# Quality scoring (delegates to QualityScorer)
score = model_manager._calculate_quality_score(entities, text)

# Weighted confidence (delegates to QualityScorer)
weighted_conf = model_manager._calculate_weighted_confidence(entities)

# Escalation decision (delegates to EscalationManager)
should_escalate = model_manager._should_escalate_to_llm(entities, text)
```

#### ✅ Legacy Methods
All internal methods prefixed with `_` are preserved for backward compatibility:
- `_extract_with_medspacy_clinical()`
- `_extract_with_transformers()`
- `_extract_with_spacy_medical()`
- `_extract_with_regex()`
- `_is_extraction_sufficient()`
- `_extract_with_llm_escalation()`
- `_get_clinical_context()`
- `_adjust_confidence_for_clinical_context()`

---

## Test Writing Guidelines

### 1. Import from Compatibility Shim
```python
# CORRECT - Use compatibility shim
from src.nl_fhir.services.nlp.models import model_manager

# AVOID - Direct import from new modules (unless you need new functionality)
from src.nl_fhir.services.nlp.extractors.medical_entity_extractor import MedicalEntityExtractor
```

### 2. Use Backward-Compatible APIs
```python
# CORRECT - Compatibility method
confidence = model_manager._calculate_weighted_confidence(entities)

# AVOID - Direct access to new modules
from src.nl_fhir.services.nlp.quality.quality_scorer import QualityScorer
scorer = QualityScorer()
metrics = scorer.calculate_confidence_metrics(entities)
weighted_conf = metrics["weighted_confidence"]
```

### 3. Check for Breaking Changes
Before writing tests, review this guide for:
- Renamed fields (`instructions` → `clinical_instructions`)
- Changed method signatures
- New return types

---

## Development Best Practices

### When to Use New Modules Directly
Use new modular components when:
- Building new features that don't need backward compatibility
- Need access to new functionality not in compatibility shim
- Writing new unit tests for specific modules

### When to Use Compatibility Shim
Use compatibility shim when:
- Maintaining existing tests
- Refactoring code that depends on original API
- Ensuring backward compatibility

---

## Refactoring Checklist

When refactoring NLP code:

- [ ] **Document breaking changes** in this file
- [ ] **Update compatibility shim** to delegate new functionality
- [ ] **Update existing tests** to use new field names/APIs
- [ ] **Run full test suite** to catch regressions
- [ ] **Update CHANGELOG.md** with breaking changes
- [ ] **Create migration guide** for major API changes

---

## Medical Safety Weighting

The NLP pipeline uses weighted confidence scoring for medical safety:

### Entity Type Weights
- **medications, conditions**: 3x weight (critical for medical safety)
- **dosages, frequencies**: 2x weight (important for medication safety)
- **others** (patients, labs, etc.): 1x weight (standard)

### Calculation Example
```python
entities = {
    "medications": [{"confidence": 0.9}],  # 3x weight
    "conditions": [{"confidence": 0.8}],   # 3x weight
    "dosages": [{"confidence": 0.7}],      # 2x weight
    "patients": [{"confidence": 0.5}]      # 1x weight
}

# Weighted confidence = (0.9*3 + 0.8*3 + 0.7*2 + 0.5*1) / (3+3+2+1)
#                     = 6.9 / 9 = 0.7666...
```

### LLM Escalation Threshold
- **Default**: 85% weighted confidence (medical safety requirement)
- **Configurable**: via `LLM_ESCALATION_THRESHOLD` environment variable
- **Purpose**: Ensure high accuracy for clinical decision support

---

## Troubleshooting

### Issue: `AttributeError: 'NLPModelManager' object has no attribute '_calculate_weighted_confidence'`

**Cause**: Using old compatibility shim before method was added

**Fix**: Ensure you're using the latest version of `services/nlp/models.py` (includes method added 2025-10-19)

### Issue: `KeyError: 'instructions'`

**Cause**: Using deprecated field name

**Fix**: Replace `instructions` with `clinical_instructions` in all code

### Issue: Tests fail with "method does not exist"

**Cause**: Incomplete compatibility shim

**Fix**: Check this guide for available methods. If method is missing, either:
1. Add it to compatibility shim (for backward compatibility)
2. Update code to use new modular API directly

---

## References

- **Original Monolithic Code**: Removed during refactoring (pre-2025-10-19)
- **New Modular Architecture**: `src/nl_fhir/services/nlp/` (current)
- **Compatibility Layer**: `src/nl_fhir/services/nlp/models.py`
- **Breaking Changes**: Documented in this guide

---

**Questions or Issues?** Check GitHub issues or create new issue with label `nlp-refactoring`
