# Epic 4: FHIR Bundle Summarization - Technical Architecture

## Architecture Overview

Epic 4 implements a **simplified, LLM-first approach** to converting HAPI-validated FHIR bundles into structured, human-readable clinical summaries using **Pydantic + Instructor** for consistent output.

### Core Architectural Principle

Instead of complex template engines or extensive validation frameworks, Epic 4 leverages the fact that **HAPI-validated FHIR bundles are already structured and complete**, making LLM summarization straightforward and reliable.

```
Architecture Flow:
HAPI-Validated FHIR Bundle → Bundle Analysis → Schema Selection → LLM + Instructor → Structured Clinical Summary
```

## System Components

### 1. Bundle Analysis Engine

**Purpose:** Analyze FHIR bundle content to determine appropriate summarization approach

**Key Components:**
- `FHIRBundleAnalyzer`: Examines bundle composition and complexity
- `SchemaSelector`: Chooses appropriate Pydantic model based on analysis  
- `ClinicalElementExtractor`: Converts FHIR resources to human-readable elements

**Analysis Criteria:**
- Resource types (medications, labs, procedures)
- Bundle complexity (simple, comprehensive, emergency)
- Urgency indicators (stat, urgent, routine)
- High-risk medications or procedures

### 2. Dynamic Pydantic Schema System

**Purpose:** Ensure consistent, structured output while maintaining human readability

**Schema Types:**

**MedicationOnlySummary:**
```python
class MedicationOnlySummary(BaseModel):
    summary_type: Literal["medication_orders"]
    patient_context: str  # "Adult patient with hypertension"
    medications: List[MedicationSummary]
    clinical_assessment: ClinicalAssessment
```

**ComprehensiveOrderSummary:**
```python  
class ComprehensiveOrderSummary(BaseModel):
    summary_type: Literal["comprehensive_orders"]
    patient_context: str
    medications: List[MedicationSummary] = []
    laboratory_orders: List[LaboratoryOrderSummary] = []
    procedures: List[ProcedureSummary] = []
    clinical_assessment: ClinicalAssessment
    coordination_notes: Optional[str]
```

**EmergencyOrderSummary:**
```python
class EmergencyOrderSummary(BaseModel):
    summary_type: Literal["emergency_orders"]
    urgency_level: Literal["urgent", "stat", "emergent"]
    immediate_orders: List[Union[MedicationSummary, LaboratoryOrderSummary, ProcedureSummary]]
    critical_actions: List[str]
```

### 3. Structured LLM Service

**Purpose:** Generate consistent, validated clinical summaries using LLM with structural constraints

**Core Technology:**
- **Instructor + OpenAI:** Constrains LLM output to valid Pydantic models
- **Role-based Prompts:** Customizes language for physician, nurse, pharmacist
- **Low Temperature (0.1):** Ensures consistency across multiple calls

**Service Flow:**
```python
response = await client.chat.completions.create(
    model="gpt-4",
    response_model=selected_schema,  # Pydantic model constrains output
    messages=[{"role": "user", "content": role_based_prompt}],
    temperature=0.1  # Consistency over creativity
)
```

### 4. API Integration Layer

**Purpose:** Provide production-ready REST endpoints for clinical workflow integration

**Primary Endpoint:**
```
POST /fhir/summarize
Content-Type: application/json

{
  "fhir_bundle": { /* HAPI-validated FHIR R4 bundle */ },
  "clinical_role": "physician",
  "request_context": "post-procedure review"
}
```

**Response Format:**
```json
{
  "status": "success",
  "request_id": "req_123",
  "processing_time_ms": 245,
  "schema_used": "MedicationOnlySummary", 
  "clinical_summary": {
    "summary_type": "medication_orders",
    "patient_context": "Adult patient with hypertension",
    "medications": [...],
    "clinical_assessment": {...}
  }
}
```

## Data Flow Architecture

### Request Processing Pipeline

1. **Request Reception** (`FastAPI Endpoint`)
   - Validate FHIR bundle structure
   - Extract clinical role and context
   - Generate unique request ID

2. **Bundle Analysis** (`FHIRBundleAnalyzer`)
   - Parse FHIR resources (MedicationRequest, ServiceRequest, Observation)
   - Assess complexity and urgency
   - Extract clinical elements in natural language

3. **Schema Selection** (`SchemaSelector`)
   - Select appropriate Pydantic model based on analysis
   - Configure role-based prompt template
   - Prepare LLM request parameters

4. **Structured Summarization** (`StructuredClinicalSummarizer`)
   - Generate role-based prompt with clinical context
   - Call LLM with Instructor constraints
   - Validate response against Pydantic schema

5. **Response Assembly** (`ClinicalSummaryService`)
   - Package structured summary with metadata
   - Add performance metrics and request tracking
   - Return comprehensive response

## Technical Implementation Details

### File Organization
```
src/nl_fhir/
├── services/
│   ├── structured_clinical_summarizer.py  # Main LLM service
│   ├── bundle_analyzer.py                 # FHIR bundle analysis
│   ├── clinical_summary_models.py         # Pydantic schema definitions
│   └── clinical_element_extractor.py      # FHIR → natural language
├── api/
│   ├── endpoints/clinical_summary.py      # FastAPI endpoints
│   ├── models/request_models.py           # API request schemas
│   └── models/response_models.py          # API response schemas
└── core/
    ├── llm_client.py                      # Instructor + OpenAI integration
    └── performance_monitoring.py          # Metrics and tracking
```

### Key Dependencies

**Core Libraries:**
- **Instructor:** Pydantic-constrained LLM output
- **OpenAI:** Primary LLM service (GPT-4)
- **Pydantic v2:** Structured data validation
- **FastAPI:** Async REST API framework

**Integration Requirements:**
- Epic 3: HAPI-validated FHIR bundles as input
- OpenAI API: Access and rate limits
- Production Infrastructure: Monitoring and logging

### Configuration Management

**Environment Variables:**
```bash
# LLM Configuration
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000
LLM_TIMEOUT_MS=15000

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT_MS=30000

# Monitoring
METRICS_ENABLED=true
STRUCTURED_LOGGING=true
LOG_LEVEL=INFO
```

## Performance Characteristics

### Response Time Targets

| Component | Target | Rationale |
|-----------|--------|-----------|
| Bundle Analysis | <50ms | Simple FHIR parsing and element extraction |
| Schema Selection | <10ms | Logic-based decision making |
| LLM Summarization | <400ms | Single OpenAI API call with structured output |
| **Total Pipeline** | **<500ms** | Clinical workflow compatibility |

### Scalability Considerations

**Horizontal Scaling:**
- Stateless service design enables multiple instances
- Async FastAPI supports high concurrent request volume
- LLM API calls are independent and parallelizable

**Resource Usage:**
- Memory: <100MB per request (FHIR bundle + LLM response)
- CPU: Minimal (I/O bound to LLM API)
- Network: OpenAI API bandwidth primary constraint

**Rate Limiting:**
- OpenAI API limits determine maximum throughput
- Request queuing for high-volume scenarios
- Caching for repeated identical requests

## Error Handling Strategy

### Error Categories and Responses

**1. Input Validation Errors**
- Invalid FHIR bundle structure
- Missing required fields
- Response: 400 Bad Request with specific validation errors

**2. LLM API Errors**
- OpenAI service unavailable
- Rate limit exceeded
- Response: 503 Service Unavailable with retry guidance

**3. Schema Validation Errors**  
- LLM output doesn't match Pydantic schema
- Instructor validation failures
- Response: 500 Internal Server Error with fallback summary

**4. System Errors**
- Unexpected exceptions
- Infrastructure failures  
- Response: 500 Internal Server Error with support information

### Graceful Degradation

**Fallback Mechanisms:**
1. **Primary:** Structured LLM summary with full Pydantic validation
2. **Fallback 1:** Basic LLM summary without strict schema constraints  
3. **Fallback 2:** Simple FHIR resource listing with human-readable extraction
4. **Final:** Clear error message with manual review guidance

## Security and Compliance

### Data Handling
- **No PHI Storage:** All clinical data processed in memory only
- **API Transmission:** HTTPS/TLS encryption for all communications
- **Logging:** Structured logging without sensitive clinical information
- **Request Tracking:** Use anonymized request IDs, not patient identifiers

### LLM API Security
- **Environment Variables:** API keys stored as secure environment variables
- **Request Filtering:** Validate and sanitize all FHIR bundle inputs
- **Response Validation:** Pydantic schema validation prevents injection attacks
- **Audit Logging:** Track all LLM API calls for security monitoring

## Monitoring and Observability

### Key Metrics

**Performance Metrics:**
- Request processing time (p50, p95, p99)
- LLM API response time and token usage
- Error rates by category
- Concurrent request capacity

**Clinical Metrics:**
- Schema selection accuracy
- Role-based usage patterns  
- Bundle complexity distribution
- Clinical review feedback scores

**System Metrics:**
- Memory usage and garbage collection
- CPU utilization patterns
- Network throughput to LLM APIs
- Service availability and uptime

### Monitoring Implementation

**Structured Logging:**
```python
logger.info("clinical_summary_request", extra={
    "request_id": request_id,
    "clinical_role": clinical_role,
    "bundle_complexity": analysis.complexity_level,
    "processing_time_ms": processing_time,
    "schema_used": selected_schema.__name__
})
```

**Metrics Collection:**
- Prometheus metrics for operational monitoring
- Custom dashboards for clinical usage patterns
- Alerting for error rates and performance degradation

## Deployment Architecture

### Production Infrastructure

**Container Deployment:**
- Docker containers with FastAPI application
- Kubernetes orchestration for scaling and reliability
- Load balancer with health check integration

**API Gateway Integration:**
- Rate limiting and request throttling
- Authentication and authorization (future enhancement)
- Request/response logging and monitoring

**Monitoring Stack:**
- Prometheus + Grafana for metrics and dashboards
- ELK stack for log aggregation and analysis  
- PagerDuty or similar for alerting

### Development vs Production

**Development Environment:**
- Single container with mock LLM responses for rapid testing
- Simplified logging and monitoring
- Direct database connections

**Production Environment:**  
- Multi-instance deployment with load balancing
- Full monitoring and alerting infrastructure
- Secure secrets management for API keys
- Production-grade logging and audit trails

This architecture provides a **simple, reliable, and maintainable** approach to FHIR bundle summarization that leverages the strengths of modern LLMs while ensuring consistent, structured output suitable for clinical review and verification.