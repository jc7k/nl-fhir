# NL-FHIR Project Purpose

## Overview
This is a **Natural Language to FHIR Converter** project that enables clinicians to enter unstructured natural language doctor's orders and automatically generate valid FHIR R4 Bundles.

## Core Functionality
- Convert free-text clinical orders into structured FHIR resources
- Validate bundles against HAPI FHIR servers  
- Optional bundle execution
- Reverse validation (FHIR bundle back to plain English summary)

## Key Components
- **Input Layer**: Web form + RESTful API endpoints
- **NLP Pipeline**: spaCy/medspaCy entity extraction + PydanticAI structured outputs
- **FHIR Assembly**: Resource creation and transaction bundle assembly
- **Validation**: HAPI FHIR server integration with failover
- **Summarization**: Template-based + optional LLM enhancement

## Target Users
- Physicians (dictating orders)
- Nurses (entering lab/procedure requests) 
- Admins (reviewing generated bundles)
- System integrators (API consumers)

## Success Metrics
- ≥95% schema validation success rate
- <2s processing latency
- ≥4/5 clinician satisfaction
- Zero HIPAA compliance breaches