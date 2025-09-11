# Epic Integration Architecture

## Overview

This document details how the 5 NL-FHIR epics integrate technically, showing data flow, API contracts, database schema evolution, and deployment dependencies across the complete system.

## System Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Epic 1       │    │    Epic 2       │    │    Epic 3       │    │    Epic 4       │
│  Input Layer    │───▶│  NLP Pipeline   │───▶│ FHIR Assembly   │───▶│ Reverse Valid.  │
│                 │    │                 │    │                 │    │                 │
│ Web Form + API  │    │ Entity Extract. │    │ Bundle Creation │    │ Summarization   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         └───────────────────────┼───────────────────────┼───────────────────────┘
                                 │                       │
                    ┌─────────────────────────────────────────────────────────┐
                    │                Epic 5                                   │
                    │          Infrastructure & Deployment                    │
                    │                                                         │
                    │  Railway • CI/CD • Monitoring • Operations             │
                    └─────────────────────────────────────────────────────────┘
```

## Epic-to-Epic Integration Details

### Epic 1 → Epic 2: Clinical Text Processing
**Interface:** Internal Python function calls
**Data Contract:**
```python
# Epic 1 Output (Input to Epic 2)
class ClinicalRequest:
    request_id: str
    clinical_text: str
    patient_ref: Optional[str] = None
    timestamp: datetime
    
# Epic 2 Input Processing
def process_clinical_text(request: ClinicalRequest) -> MedicalEntities
```

**Integration Points:**
- Epic 1 validates and sanitizes clinical text input
- Epic 2 receives structured request with surrogate patient ID
- Error propagation: Epic 1 handles user-facing errors, Epic 2 handles processing errors

### Epic 2 → Epic 3: Medical Entity Transformation
**Interface:** Structured Python objects
**Data Contract:**
```python
# Epic 2 Output (Input to Epic 3)
class MedicalEntities:
    medications: List[MedicationEntity]
    lab_orders: List[LabOrderEntity]
    procedures: List[ProcedureEntity]
    patient_context: PatientContext
    confidence_scores: Dict[str, float]
    
# Epic 3 Input Processing
def create_fhir_bundle(entities: MedicalEntities) -> FHIRBundle
```

**Integration Points:**
- Epic 2 provides structured medical entities with confidence scores
- Epic 3 maps entities to FHIR resources with validation
- Fallback: Low confidence entities trigger manual review workflow

### Epic 3 → Epic 4: FHIR Bundle Validation
**Interface:** FHIR R4 Bundle objects
**Data Contract:**
```python
# Epic 3 Output (Input to Epic 4)
class FHIRBundleResult:
    bundle: Bundle  # FHIR R4 Bundle
    validation_status: ValidationStatus
    original_request: ClinicalRequest
    processing_metadata: Dict[str, Any]
    
# Epic 4 Input Processing
def validate_and_summarize(result: FHIRBundleResult) -> ClinicalSummary
```

**Integration Points:**
- Epic 3 provides validated FHIR bundles with metadata
- Epic 4 performs reverse validation and generates summaries
- Cross-validation: Epic 4 compares original text with generated FHIR

### Epic 5: Infrastructure Integration
**Deployment Orchestration:**
- **Epic 1:** FastAPI application service (2GB memory, 2 vCPU)
- **Epic 2:** NLP processing service with ML models (4GB memory, GPU optional)
- **Epic 3:** FHIR service with HAPI integration (2GB memory)
- **Epic 4:** Validation service (1GB memory)
- **Shared Infrastructure:** PostgreSQL, ChromaDB, Redis cache

## Data Flow Architecture

### Complete Request Processing Flow
```
1. Web Form Input (Epic 1)
   ↓ HTTP POST /convert
2. Request Validation & Logging (Epic 1)
   ↓ Internal function call
3. NLP Entity Extraction (Epic 2)
   ↓ Structured entities
4. FHIR Resource Creation (Epic 3)
   ↓ FHIR Bundle
5. Bundle Validation (Epic 3)
   ↓ Validated bundle
6. Reverse Validation & Summary (Epic 4)
   ↓ Clinical summary
7. Response Assembly (Epic 1)
   ↓ HTTP JSON response
8. Client Display (Epic 1)
```

### Database Schema Evolution

#### Epic 1: Foundation Schema
```sql
-- Request tracking and audit
CREATE TABLE clinical_requests (
    id UUID PRIMARY KEY,
    request_text TEXT NOT NULL,
    patient_ref VARCHAR(255),
    created_at TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

CREATE TABLE processing_logs (
    id UUID PRIMARY KEY,
    request_id UUID REFERENCES clinical_requests(id),
    stage VARCHAR(50),  -- 'input', 'nlp', 'fhir', 'validation'
    status VARCHAR(20), -- 'started', 'completed', 'failed'
    processing_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP
);
```

#### Epic 2: NLP Enhancement
```sql
-- Add NLP processing results
ALTER TABLE processing_logs ADD COLUMN nlp_confidence DECIMAL(3,2);
ALTER TABLE processing_logs ADD COLUMN entities_extracted JSONB;

CREATE TABLE medical_entities (
    id UUID PRIMARY KEY,
    request_id UUID REFERENCES clinical_requests(id),
    entity_type VARCHAR(50), -- 'medication', 'lab_order', 'procedure'
    entity_text TEXT,
    confidence_score DECIMAL(3,2),
    medical_codes JSONB, -- RxNorm, LOINC, ICD-10 codes
    extracted_at TIMESTAMP
);
```

#### Epic 3: FHIR Storage
```sql
-- Add FHIR bundle storage
CREATE TABLE fhir_bundles (
    id UUID PRIMARY KEY,
    request_id UUID REFERENCES clinical_requests(id),
    bundle_json JSONB NOT NULL,
    validation_status VARCHAR(20), -- 'valid', 'invalid', 'warning'
    validation_issues JSONB,
    hapi_response JSONB,
    created_at TIMESTAMP
);

-- Index for FHIR bundle queries
CREATE INDEX idx_fhir_bundles_request_id ON fhir_bundles(request_id);
CREATE INDEX idx_fhir_bundles_validation_status ON fhir_bundles(validation_status);
```

#### Epic 4: Validation Enhancement
```sql
-- Add reverse validation and summaries
CREATE TABLE clinical_summaries (
    id UUID PRIMARY KEY,
    bundle_id UUID REFERENCES fhir_bundles(id),
    summary_text TEXT NOT NULL,
    accuracy_score DECIMAL(3,2),
    safety_alerts JSONB,
    generated_at TIMESTAMP
);

-- Add safety validation tracking
CREATE TABLE safety_validations (
    id UUID PRIMARY KEY,
    bundle_id UUID REFERENCES fhir_bundles(id),
    validation_type VARCHAR(50), -- 'drug_interaction', 'contraindication'
    severity VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    finding TEXT,
    recommendation TEXT,
    created_at TIMESTAMP
);
```

#### Epic 5: Production Monitoring
```sql
-- Add production monitoring and metrics
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY,
    metric_name VARCHAR(100),
    metric_value DECIMAL(10,2),
    metric_unit VARCHAR(20),
    recorded_at TIMESTAMP
);

CREATE TABLE error_tracking (
    id UUID PRIMARY KEY,
    request_id UUID REFERENCES clinical_requests(id),
    error_type VARCHAR(50),
    error_details JSONB,
    stack_trace TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    occurred_at TIMESTAMP
);
```

## API Contract Evolution

### Epic 1: Foundation API
```python
# Basic conversion endpoint
POST /convert
{
    "clinical_text": "Start patient on lisinopril 10mg daily",
    "patient_ref": "12345"
}

Response: {
    "request_id": "uuid",
    "status": "processing"
}
```

### Epic 2-3: Enhanced with NLP & FHIR
```python
# Enhanced response with FHIR bundle
POST /convert
Response: {
    "request_id": "uuid",
    "status": "completed",
    "bundle": { /* FHIR R4 Bundle */ },
    "validation": {
        "is_valid": true,
        "issues": []
    },
    "entities": [
        {
            "type": "medication",
            "text": "lisinopril 10mg daily",
            "confidence": 0.95,
            "codes": {"rxnorm": "12345"}
        }
    ]
}
```

### Epic 4: Added Validation Endpoints
```python
# New validation endpoints
POST /validate
{
    "bundle": { /* FHIR Bundle */ }
}

POST /summarize-bundle
{
    "bundle": { /* FHIR Bundle */ }
}

Response: {
    "summary": "Patient prescribed lisinopril 10mg once daily for hypertension",
    "safety_alerts": [],
    "accuracy_score": 0.98
}
```

## Error Handling Strategy

### Error Propagation Between Epics
```python
class ProcessingError:
    epic: str              # Which epic failed
    stage: str             # Specific processing stage
    error_type: str        # Classification of error
    user_message: str      # User-friendly message
    technical_details: str # Technical debugging info
    recoverable: bool      # Can user retry?
    
# Error handling chain
Epic 1 → User-facing HTTP errors (400, 422, 500)
Epic 2 → NLP processing errors → fallback to manual review
Epic 3 → FHIR validation errors → return specific validation issues  
Epic 4 → Validation errors → return with confidence warnings
Epic 5 → Infrastructure errors → automatic retry with fallback
```

### Fallback Strategies
1. **Epic 2 NLP Failure:** Fallback to simpler rule-based extraction
2. **Epic 3 FHIR Validation Failure:** Return validation errors with suggestions
3. **Epic 4 Summarization Failure:** Use template-based summary only
4. **Epic 5 Infrastructure Failure:** Graceful degradation with user notification

## Performance Integration

### Response Time Budget (Total: <2s)
- **Epic 1 (Input/Output):** <200ms - Form processing, response assembly
- **Epic 2 (NLP):** <800ms - Entity extraction, terminology lookup
- **Epic 3 (FHIR):** <500ms - Resource creation, bundle assembly, validation
- **Epic 4 (Validation):** <300ms - Summary generation, safety checks
- **Epic 5 (Infrastructure):** <200ms - Network, database, monitoring overhead

### Caching Strategy
- **Epic 2:** Cache medical terminology lookups (ChromaDB)
- **Epic 3:** Cache FHIR validation results for similar bundles
- **Epic 4:** Cache drug interaction and contraindication rules
- **Cross-Epic:** Redis cache for frequently processed clinical phrases

## Security Integration

### HIPAA Compliance Across Epics
- **Epic 1:** Input sanitization, audit logging with surrogate IDs
- **Epic 2:** No PHI in NLP processing logs, entity anonymization
- **Epic 3:** FHIR resource anonymization, secure HAPI communication
- **Epic 4:** Summary generation without PHI exposure
- **Epic 5:** End-to-end encryption, audit trail aggregation

### Authentication & Authorization
```python
# Security flow across epics
1. Epic 1: API key validation, rate limiting
2. Epic 2-4: Internal service authentication via JWT
3. Epic 5: Infrastructure secrets management, TLS encryption
```

## Deployment Dependencies

### Sequential Deployment Requirements
1. **Epic 5 Infrastructure:** Deploy first - Railway, PostgreSQL, monitoring
2. **Epic 1 Foundation:** Deploy core API and database schema
3. **Epic 2 NLP:** Deploy after Epic 1, requires ML models and ChromaDB
4. **Epic 3 FHIR:** Deploy after Epic 2, requires HAPI FHIR server setup
5. **Epic 4 Validation:** Deploy after Epic 3, requires full pipeline integration

### Rollback Strategy
- **Database:** Schema migrations are reversible within each epic
- **Services:** Blue-green deployment enables immediate rollback
- **Dependencies:** Epic rollback may require dependent epic rollback
- **Data:** Cross-epic data consistency maintained through transaction boundaries

## Monitoring Integration

### Cross-Epic Metrics
- **Business Metrics:** End-to-end conversion success rate, user satisfaction
- **Performance Metrics:** Epic-to-epic handoff times, total processing time
- **Quality Metrics:** FHIR validation success, medical accuracy scores
- **Reliability Metrics:** Error rates by epic, service availability

### Observability Stack
- **Tracing:** Distributed tracing across all 5 epics
- **Logging:** Centralized logging with epic-specific tags
- **Metrics:** Business and technical metrics aggregation
- **Alerting:** Epic-specific alerts with escalation procedures

This integration architecture ensures seamless operation across all 5 epics while maintaining clear boundaries, error handling, and production reliability.