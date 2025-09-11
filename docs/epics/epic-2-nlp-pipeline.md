# Epic 2: NLP Pipeline & Entity Extraction

## Epic Goal

Transform natural language clinical orders into structured medical entities using advanced NLP processing, medical terminology mapping, and AI-powered extraction to enable accurate FHIR resource creation.

## Epic Description

**Business Value:**
This epic is the core intelligence of the NL-FHIR system, converting unstructured clinical text into precise medical entities that can be mapped to FHIR resources. This enables clinicians to use natural language while ensuring clinical accuracy and standardization.

**Technical Foundation:**
- spaCy/medspaCy for medical entity recognition and extraction
- ChromaDB vector database for medical terminology lookup and mapping
- PydanticAI/Instructor for structured LLM outputs with schema validation
- Integration with medical coding standards (RxNorm, LOINC, ICD-10)

**Clinical Intelligence:**
The pipeline extracts medications, dosages, frequencies, lab orders, procedures, and patient instructions while mapping them to standardized medical codes for interoperability.

## Epic Stories

### 2.1 NLP Pipeline Foundation
**Status:** Draft  
**Goal:** Implement core spaCy/medspaCy pipeline for medical entity extraction  
**Key Features:** Medical entity recognition, dosage extraction, frequency parsing, clinical text preprocessing

### 2.2 RAG Medical Terminology  
**Status:** Draft  
**Goal:** Integrate ChromaDB for medical terminology lookup and code mapping  
**Key Features:** Vector embeddings, RxNorm/LOINC/ICD-10 mapping, similarity search, terminology validation

### 2.3 Structured LLM Output
**Status:** Draft  
**Goal:** Implement PydanticAI for structured medical data extraction  
**Key Features:** Schema-constrained outputs, slot filling, clinical reasoning, validation rules

### 2.4 NLP Production Ready
**Status:** Draft  
**Goal:** Production optimization and integration of complete NLP pipeline  
**Key Features:** Performance optimization, error handling, monitoring, pipeline orchestration

## Success Criteria

- [ ] Extract medical entities from natural language with >95% accuracy
- [ ] Map medications to RxNorm codes with >90% accuracy
- [ ] Map lab orders to LOINC codes with >90% accuracy
- [ ] Process clinical text in <1s for typical orders (50-200 characters)
- [ ] Handle edge cases and ambiguous inputs gracefully
- [ ] Maintain medical accuracy through validation and fallback mechanisms
- [ ] Support multiple clinical order types (medications, labs, procedures)

## Technical Architecture

**NLP Pipeline Components:**
- **Text Preprocessing:** Clinical text normalization and cleaning
- **Entity Extraction:** spaCy/medspaCy for medical NER
- **Terminology Mapping:** ChromaDB vector search for code lookup
- **Structured Output:** PydanticAI for schema-validated extraction
- **Validation:** Medical logic validation and consistency checking

**Data Flow:**
```
Clinical Text → Preprocessing → Entity Extraction → Terminology Mapping → Structured Output → Validation → Medical Entities
```

**Medical Terminologies:**
- **RxNorm:** Medication names and codes
- **LOINC:** Laboratory and clinical observations
- **ICD-10:** Conditions and diagnoses
- **SNOMED CT:** Clinical concepts (future enhancement)

## Dependencies

**Prerequisites:**
- Epic 1: Input Layer (provides clinical text input)

**Provides Foundation For:**
- Epic 3: FHIR Assembly (consumes structured medical entities)
- Epic 4: Reverse Validation (validates extracted entities)

**External Dependencies:**
- OpenAI API for LLM processing
- Medical terminology databases (RxNorm, LOINC, ICD-10)
- spaCy/medspaCy models and pipelines

## Risk Mitigation

**Primary Risks:**
1. **Medical Accuracy Risk:** Incorrect entity extraction leading to clinical errors
   - **Mitigation:** Multiple validation layers, confidence scoring, fallback to manual review
2. **Performance Risk:** Slow NLP processing affecting user experience
   - **Mitigation:** Async processing, model optimization, caching strategies  
3. **Terminology Coverage Risk:** Missing or outdated medical codes
   - **Mitigation:** Regular terminology updates, manual code entry fallback
4. **API Dependency Risk:** OpenAI API failures or rate limits
   - **Mitigation:** Local model fallback, API key rotation, rate limiting

**Rollback Plan:**
- Fallback to simpler rule-based extraction
- Cache previous successful extractions
- Manual override capabilities for critical cases
- Graceful degradation with user notifications

## Epic Timeline

**Sprint 2 (Epic 2 Complete)**
- Week 1: Story 2.1 - Core NLP pipeline foundation
- Week 2: Story 2.2 - Medical terminology integration
- Week 3: Story 2.3 - Structured LLM outputs
- Week 4: Story 2.4 - Production optimization and integration

**Critical Path Dependencies:**
- Medical terminology data must be loaded before 2.2
- LLM integration requires API keys and rate limit setup
- Performance testing requires realistic clinical text dataset

## Definition of Done

- [ ] All 4 stories completed with acceptance criteria met
- [ ] NLP pipeline extracts medical entities with validated accuracy
- [ ] Medical terminology mapping works for RxNorm, LOINC, ICD-10
- [ ] Structured outputs conform to validated medical schemas
- [ ] Performance meets <1s processing time for typical orders
- [ ] Error handling covers edge cases and invalid inputs
- [ ] Integration tests validate end-to-end pipeline functionality
- [ ] Medical accuracy validation using golden dataset
- [ ] Production monitoring and alerting configured
- [ ] Documentation complete for medical entity schemas
- [ ] Code review with medical and technical validation
- [ ] Security review for PHI handling in processing

## Success Metrics

**Medical Accuracy Metrics:**
- >95% entity extraction accuracy on validation dataset
- >90% medication mapping accuracy (RxNorm)
- >90% lab order mapping accuracy (LOINC)
- <1% critical medical errors in extraction

**Performance Metrics:**
- <1s processing time for 95th percentile of orders
- >99% pipeline availability
- <100MB memory usage per extraction
- Cache hit rate >80% for terminology lookups

**Quality Metrics:**
- >90% confidence score for extracted entities
- <5% manual review rate for uncertain extractions
- 0 PHI exposure incidents during processing
- >95% structured output schema validation success

**Integration Metrics:**
- 100% integration with Epic 1 input layer
- 100% compatibility with Epic 3 FHIR assembly
- <0.1s handoff time between pipeline components
- >99.9% data consistency between pipeline stages