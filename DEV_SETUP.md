# Development Setup Guide

## Development Tools (Local-Only)

This project uses several AI-powered development tools that are **intentionally excluded from git tracking**. These tools exist in your local working directory but are not checked into the repository to keep the production codebase clean.

### Local-Only Development Tools

The following directories exist locally but are **not tracked by git**:

- **`.bmad-core/`** - BMAD AI Development Framework

  - Agent team configurations
  - Task automation templates
  - Workflow orchestration
  - Knowledge base and documentation tools

- **`.claude/`** - Claude AI Development Configurations

  - Custom slash commands for BMAD agents
  - Claude-specific project settings
  - Development workflow integrations

- **`.gemini/`** - Gemini AI Development Configurations

  - BMAD agent configurations for Gemini
  - Task templates in TOML format
  - Alternative AI workflow support

- **`.serena/`** - Serena Code Analysis Tool

  - Project memories and analysis
  - Codebase structure documentation
  - Development workflow insights

- **`.specify/`** - GitHub Spec Kit Planning Tools
  - Feature specification templates
  - Planning and task management scripts
  - Project constitution and guidelines

### Why These Tools Are Local-Only

1. **Clean Production Deployments** - Production containers and deployments don't need development tooling
2. **Personal Workflow** - These tools are configured for individual developer preferences
3. **Reduced Repository Size** - Keeps the git repository focused on production code
4. **Security** - Development tools may contain local configurations or paths

### Backup and Recovery

A backup of all development tools is available at:

```bash
~/nl-fhir-dev-tools-backup/
```

This backup was created on 2025-10-18 and contains:

- `.bmad-core/` (75 files)
- `.claude/` (43 files)
- `.gemini/` (33 files)
- `.serena/` (9 files)
- `.specify/` (11 files)

**To restore from backup:**

```bash
# Copy all dev tools back to project directory
cp -r ~/nl-fhir-dev-tools-backup/.bmad-core ~/projects/nl-fhir/
cp -r ~/nl-fhir-dev-tools-backup/.claude ~/projects/nl-fhir/
cp -r ~/nl-fhir-dev-tools-backup/.gemini ~/projects/nl-fhir/
cp -r ~/nl-fhir-dev-tools-backup/.serena ~/projects/nl-fhir/
cp -r ~/nl-fhir-dev-tools-backup/.specify ~/projects/nl-fhir/

# Verify restoration
ls -d ~/projects/nl-fhir/.bmad-core ~/projects/nl-fhir/.claude ~/projects/nl-fhir/.gemini ~/projects/nl-fhir/.serena ~/projects/nl-fhir/.specify
```

### Git Behavior

When you run `git status`, these directories will appear as "Untracked files":

```
Untracked files:
  .bmad-core/
  .claude/
  .gemini/
  .serena/
  .specify/
```

**This is expected behavior.** These directories are excluded in `.gitignore` and will never be committed to the repository, even if you run `git add .`

### Setting Up a New Development Machine

If you're setting up the project on a new machine and need these development tools:

1. **Obtain the dev tools backup** from your previous machine or backup location
2. **Copy to project directory** as shown in the restoration commands above
3. **Verify tools are working** by running BMAD or Spec Kit commands
4. **Confirm git ignores them** with `git status` - they should appear as untracked

### Production Deployment

When deploying to production (Docker, Railway, etc.):

- These dev tool directories won't be included in version control
- Production builds remain clean and focused
- No manual cleanup required - `.gitignore` handles everything automatically

### Questions?

If you need to share development tool configurations with team members:

- Use a separate private repository
- Share backup archives via secure channels
- Document any required setup in team knowledge base

---

**Last Updated:** 2025-10-18
**Backup Location:** `~/nl-fhir-dev-tools-backup/`
**Total Dev Tool Files:** 171 files safely preserved locally
