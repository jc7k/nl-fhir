# NL-FHIR Suggested Commands

## Current Project Status
**This project is in planning/documentation phase** - no source code or build system exists yet. Commands will be added as development progresses.

## Agent Commands (Available Now)
- `/pm` - Activate Product Manager agent for PRD/story work
- `/dev` - Activate Developer agent for implementation work  
- `/architect` - Activate Architect agent for system design
- `/bmad-orchestrator` - Multi-agent workflow coordination

## Future Development Commands (To Be Implemented)
Based on the PRD planning, these commands will be needed:

### Testing (When Implemented)
- `pytest` - Run unit and integration tests
- `pytest tests/` - Run specific test directory
- `pytest -v tests/test_nlp.py` - Run single test file with verbose output

### Quality Assurance (When Implemented)
- `ruff check` - Python linting
- `ruff format` - Code formatting
- `mypy` - Type checking
- `black` - Code formatting (if used instead of ruff)

### Development Server (When Implemented)
- `uvicorn main:app --reload` - Run FastAPI development server
- `docker-compose up hapi-fhir` - Start local HAPI FHIR server
- `docker-compose down` - Stop local services

### FHIR Testing (When Implemented)
- Custom validation commands against golden datasets
- HAPI FHIR endpoint health checks
- Bundle validation test suites

## BMAD-METHOD Commands
- `npx bmad-method list:agents` - List available agents
- `npx bmad-method validate` - Validate configuration
- `md-tree explode [file] [output-dir]` - Shard markdown documents

## Documentation Commands  
- View PRD sections: `cat docs/prd/[section].md`
- Access agent help: Activate agent and use `*help` command