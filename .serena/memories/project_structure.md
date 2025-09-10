# NL-FHIR Project Structure

## Current State
This project is in **planning and documentation phase** - no source code exists yet. The project contains comprehensive product planning documentation and tooling setup.

## Directory Structure

### Documentation
- `docs/prd/` - 29 sharded PRD sections covering all aspects of the project
  - Core sections: 1-overview.md, 5-functional-requirements.md, 7-dependencies.md
  - Architecture: 13-deployment-strategy-railway.md, 22-cicd-regression-automation.md
  - Quality: 20-acceptance-criteria.md, 14-regression-testing-local.md

### Configuration & Tooling
- `.bmad-core/` - BMAD-METHOD agent definitions and templates
  - `core-config.yaml` - Project configuration (PRD sharding, dev settings)
  - `agents/` - Specialized agent definitions (pm, dev, architect, etc.)
  - `tasks/` - Executable workflow templates
  - `templates/` - Document templates (PRD, architecture, etc.)

- `.claude/` - Claude Code configuration
  - `statusline.sh` - Custom status line script
  - `settings.local.json` - Local Claude settings

### Agent System
- `AGENTS.md` - Auto-generated agent directory and instructions
- `CLAUDE.md` - Archon workflow integration and development patterns

## Key Files
- `CLAUDE.md` - Primary development workflow (Archon-first task management)
- `docs/NL_FHIR_PRD_v1.6_full_with_copyright.md` - Original comprehensive PRD
- `.bmad-core/core-config.yaml` - Project configuration settings

## Development Approach
- **Agent-driven development** with specialized roles (PM, Dev, Architect, QA)
- **Archon MCP server integration** for task management and knowledge base
- **Research-driven implementation** with RAG queries before coding
- **Epic-based planning** with 23 user stories across 5 major epics