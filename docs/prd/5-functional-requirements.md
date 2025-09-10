# 5. Functional Requirements

## 5.1 Input Layer

-   Web form with single text field (textarea) + submit button.\
-   RESTful `POST /convert` endpoint accepts `{text, patientRef}`.

## 5.2 NLP & Extraction

-   spaCy/medspaCy for initial entity/rule extraction.\
-   Optional RAG (ChromaDB) for terminology lookup.\
-   PydanticAI (or Instructor + OpenAI Structured Outputs) for
    schema-constrained slot filling.

## 5.3 FHIR Bundle Assembly

-   Support FHIR R4 resources: Patient, Practitioner, MedicationRequest,
    ServiceRequest, Observation, Encounter.\
-   Assemble into **transaction Bundle**.

## 5.4 Validation & Execution

-   RESTful `POST /validate` endpoint → calls HAPI `$validate`.\
-   Block execution if validation errors present.\
-   Optional `POST /execute` endpoint to post bundle to HAPI server.

## 5.5 Reverse Validation (Summarization)

-   RESTful `POST /summarize-bundle` endpoint.\
-   Deterministic template-based English output (primary).\
-   Optional LLM polishing (guarded, diff-checked).\
-   Findings block: missing fields, conflicts, assumptions, provenance.

------------------------------------------------------------------------
