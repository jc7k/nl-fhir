# Product Requirements Document (PRD)

**Project:** Natural Language to FHIR Converter\
**Owner:** Product Manager (Healthcare AI Applications)\
**Version:** v1.6\
**Date:** 2025-09-09

------------------------------------------------------------------------

## 1. Overview

This product enables clinicians to enter **unstructured natural language
doctor's orders** and automatically generate a valid **FHIR R4 Bundle**.
The bundle can be validated against a **HAPI FHIR server** and
optionally executed.

The system bridges the gap between free-text encounter notes and
structured EHR integration by combining **lightweight NLP, retrieval
grounding, structured extraction, and schema validation**.

------------------------------------------------------------------------

## 2. Problem Statement

Clinicians often express instructions in free text or dictation, while
EHRs require **FHIR-compliant structured data**. Manual translation is
error-prone and time-consuming. An automated pipeline reduces clinical
burden and minimizes errors.

------------------------------------------------------------------------

## 3. Objectives & Goals

-   Accept unstructured clinical orders in natural language.\
-   Parse intent, entities, and required clinical attributes.\
-   Generate FHIR resources (MedicationRequest, ServiceRequest,
    Observation, Encounter).\
-   Assemble resources into a valid **FHIR R4 Bundle**.\
-   Validate with a **local or cloud HAPI FHIR server**.\
-   Provide **reverse validation** by summarizing FHIR Bundles into
    plain English.\
-   Ensure security, compliance, and extensibility.

**Success Metrics:**\
- ≥ 95% schema validation success rate.\
- Processing latency \< 2 seconds per request.\
- Clinician satisfaction ≥ 4/5.\
- Zero HIPAA compliance breaches in pilot phase.

------------------------------------------------------------------------

## 4. User Stories

-   *As a physician*, I want to dictate "Start patient John Doe on 500
    mg amoxicillin twice daily" and receive a **MedicationRequest**
    resource.\
-   *As a nurse*, I want to type "Order CBC for patient Jane Smith
    tomorrow morning" and receive a **ServiceRequest**.\
-   *As an admin*, I want to view a plain-English summary of generated
    bundles to confirm intent.\
-   *As a system integrator*, I want API endpoints for ingestion into an
    EHR.

------------------------------------------------------------------------

## 5. Functional Requirements

### 5.1 Input Layer

-   Web form with single text field (textarea) + submit button.\
-   RESTful `POST /convert` endpoint accepts `{text, patientRef}`.

### 5.2 NLP & Extraction

-   spaCy/medspaCy for initial entity/rule extraction.\
-   Optional RAG (ChromaDB) for terminology lookup.\
-   PydanticAI (or Instructor + OpenAI Structured Outputs) for
    schema-constrained slot filling.

### 5.3 FHIR Bundle Assembly

-   Support FHIR R4 resources: Patient, Practitioner, MedicationRequest,
    ServiceRequest, Observation, Encounter.\
-   Assemble into **transaction Bundle**.

### 5.4 Validation & Execution

-   RESTful `POST /validate` endpoint → calls HAPI `$validate`.\
-   Block execution if validation errors present.\
-   Optional `POST /execute` endpoint to post bundle to HAPI server.

### 5.5 Reverse Validation (Summarization)

-   RESTful `POST /summarize-bundle` endpoint.\
-   Deterministic template-based English output (primary).\
-   Optional LLM polishing (guarded, diff-checked).\
-   Findings block: missing fields, conflicts, assumptions, provenance.

------------------------------------------------------------------------

## 6. Non-Functional Requirements

-   **Security:** HIPAA-compliant, TLS 1.2+, surrogate IDs in POC.\
-   **Performance:** \<2s response time.\
-   **Reliability:** ≥ 99.9% uptime target in production.\
-   **Scalability:** MVP handles 1,000 orders/day; scalable via
    containerization.\
-   **Auditability:** Store provenance (codes, retrieval sources,
    assumptions).

------------------------------------------------------------------------

## 7. Dependencies

-   **HAPI FHIR server** (local Docker or public cloud endpoints).\
-   **fhir.resources (Pydantic)** for schema.\
-   **spaCy/medspaCy/scispaCy** for entity recognition.\
-   **PydanticAI / Instructor** for structured LLM outputs.\
-   **ChromaDB** (optional) for retrieval.\
-   **Arize Phoenix** (optional) for observability.

------------------------------------------------------------------------

## 8. Risks & Open Questions

-   Ambiguity in natural language (e.g., "order labs" with no test
    specified).\
-   Safety risks if incorrect mapping occurs.\
-   Privacy concerns if external APIs used with PHI.\
-   Dependency on terminology completeness (RxNorm/LOINC coverage).

------------------------------------------------------------------------

## 9. Milestones

-   **MVP (3 months):** /convert + /validate, text input, FHIR bundle
    assembly, HAPI validation.\
-   **Pilot (6 months):** Reverse validation (/summarize-bundle), seed
    dataset (\~200 pairs).\
-   **Production (12 months):** Full RAG support, CRAG/Self-RAG gates,
    SPA frontend, compliance audit.

------------------------------------------------------------------------

## 10. Test Data Generation & Validation

-   Use **Synthea** synthetic FHIR bundles as ground truth.\
-   Generate natural-language encounter text with ChatGPT based on those
    bundles (20--30 seed examples).\
-   Scale with templates, paraphrasing, abbreviations, negations (\~200
    examples).\
-   Round-trip validation: text → bundle → summary → compare with
    original.

------------------------------------------------------------------------

## 11. Glossary

-   **FHIR (Fast Healthcare Interoperability Resources):** HL7 standard
    for exchanging healthcare data electronically.\
-   **FHIR R4:** Release 4 of the FHIR specification.\
-   **Bundle:** A container resource grouping multiple FHIR resources.\
-   **HAPI FHIR:** Open-source Java implementation of FHIR.\
-   **MedicationRequest, ServiceRequest, Observation, Encounter:** FHIR
    resource types.\
-   **spaCy/medspaCy:** NLP libraries for entity extraction.\
-   **PydanticAI/Instructor:** Python libraries enforcing LLM outputs to
    strict schemas.\
-   **ChromaDB:** Lightweight vector database for retrieval-augmented
    generation (RAG).\
-   **Synthea:** Synthetic patient data generator.

------------------------------------------------------------------------

## 12. Validation Environments & Fallback

-   **DEMO (Railway-hosted):** Validate bundles against multiple
    **public cloud HAPI endpoints** with automatic failover.\
-   **REGRESSION (Local):** Validate bundles against local Docker HAPI
    (pinned version).\
-   **Data policy:** No PHI; synthetic only; surrogate IDs.

------------------------------------------------------------------------

## 13. Deployment Strategy --- Railway

-   Railway hosts **single FastAPI service** (UI + API).\
-   Env vars: `MODE`, `HAPI_BASE_URLS`, `OPENAI_API_KEY`,
    `REQUEST_TIMEOUT_S`, `RETRY_MAX`, `BACKOFF_BASE_MS`.\
-   Failover logic implemented for `/validate`.\
-   DEMO mode points to public HAPI endpoints.\
-   Regression mode points to local HAPI in Docker.

------------------------------------------------------------------------

## 14. Regression Testing (Local)

-   Dockerized HAPI FHIR (pinned version, in-memory DB).\
-   Run golden bundles through `/convert`, `/validate`,
    `/summarize-bundle`.\
-   Assert ≥90% validation pass, ≥95% semantic fidelity.

------------------------------------------------------------------------

## 15. Demo/UX Notes

-   UI shows: raw FHIR Bundle, validation badge (with endpoint name),
    English summary.\
-   Badge states: Validated (Demo via hapi.fhir.org) \| Validated (Demo
    via smarthealthit.org) \| Validation unavailable.\
-   Runbook ensures demo fallback input if live order fails.

------------------------------------------------------------------------

## 16. Reverse Summary Safety Policy

(as in v1.5 --- deterministic first, schema-constrained LLM optional,
strict gates).

------------------------------------------------------------------------

## 17. Model Recommendation & Cost

(as in v1.5 --- GPT-4o mini recommended, cheapest viable, cost
negligible).

------------------------------------------------------------------------

## 18. Test & Demo Guidance

(as in v1.5 --- deterministic default, LLM shadow only).

------------------------------------------------------------------------

## 19. Logging & Observability

(as in v1.5 --- structured logs, no PHI, metrics, alerts).

------------------------------------------------------------------------

## 20. Acceptance Criteria

(Enumerated list of explicit demo/regression pass conditions).

------------------------------------------------------------------------

## 21. Roles & RACI

(as in v1.5).

------------------------------------------------------------------------

## 22. CI/CD & Regression Automation

-   GitHub Actions pipeline spins up local HAPI Docker, runs seed
    regression, fails build on error.

------------------------------------------------------------------------

## 23. Demo Runbook

-   Pre-demo checklist, live demo script, recovery fallback inputs.

------------------------------------------------------------------------

## 24. Security & Secrets

-   Secrets in Railway only. No PHI. Monthly rotation.

------------------------------------------------------------------------

## 25. Data Governance (Future RAG)

-   Versioned indices; provenance includes index_version.

------------------------------------------------------------------------

## 26. Monitoring & SLOs

-   p95 latency targets, demo availability, alert thresholds.

------------------------------------------------------------------------

## 27. Budget Estimate (POC)

-   Railway hobby tier: \~\$10--20/month.\
-   OpenAI mini usage negligible (\<\$1/10k summaries).\
-   Total infra: \<\$30/month.

------------------------------------------------------------------------

## 28. Timeline & Sprint Backlog

-   Sprint 1--6 breakdown as per PM recommendations.

------------------------------------------------------------------------

## 29. Appendix: Known Limitations

-   No PHI/EHR integration in MVP.\
-   No persistence of patient history.\
-   No advanced workflows.\
-   No enterprise auth/integration until Pilot.

------------------------------------------------------------------------

------------------------------------------------------------------------

© All rights reserved Jeff Chen 2025
