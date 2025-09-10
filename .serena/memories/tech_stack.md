# NL-FHIR Technology Stack

## Current Status
**This is a planning/documentation phase project** - no actual code implementation exists yet. The project is fully documented with comprehensive PRD and epic/story planning.

## Planned Technology Stack

### Backend
- **FastAPI** - Python web framework for API endpoints
- **fhir.resources (Pydantic)** - FHIR R4 schema validation
- **spaCy/medspaCy/scispaCy** - Medical NLP and entity recognition
- **PydanticAI or Instructor** - Structured LLM outputs with schema constraints
- **HAPI FHIR server** - FHIR validation and execution (Docker local + cloud endpoints)

### Optional Components  
- **ChromaDB** - Vector database for RAG/terminology lookup
- **Arize Phoenix** - Observability and monitoring
- **OpenAI API** - LLM services (GPT-4o mini recommended)

### Infrastructure
- **Railway** - Cloud hosting platform
- **Docker** - Local development and HAPI FHIR testing
- **GitHub Actions** - CI/CD pipeline

### Development Tools
- **BMAD-METHOD** - Project management and agent-based development
- **Archon MCP Server** - Task management and knowledge base
- Multiple specialized agents (pm, dev, architect, etc.)

## Architecture Pattern
- **Microservices-style** single FastAPI application
- **Pipeline architecture** for NLP processing
- **Transaction-based** FHIR bundle processing
- **Failover-enabled** external service integration