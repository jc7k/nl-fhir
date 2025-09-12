# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-09-11
### Added
- Epic 5 (Infrastructure & Deployment) completed and prepared for QA.
  - CI/CD: GitHub Actions with PR smoke (health/readiness/liveness/metrics), core tests, Docker build validation, JSON logging verification, and nightly full test run.
  - Monitoring: New `/readiness` and `/liveness` endpoints; existing `/health` and `/metrics` validated in CI.
  - Logging: Structured JSON logs in production via `python-json-logger` and `dictConfig`.
  - Deployment Ops: Railway deployment runbook, variables setup guide, and helper scripts (`deploy.sh`, `rollback.sh`, `health-check.sh`).
  - Developer Tooling: Makefile tasks for install/dev/test/smoke/docker build.
- Documentation updates:
  - QA readiness and gate decision for Epic 5.
  - README with CI badge, Railway instructions, and quick start.

### Changed
- `.env.example` hardened with explicit Epic 4 flags off by default in prod (`SUMMARIZATION_ENABLED=false`, `SAFETY_VALIDATION_ENABLED=false`) and `WORKERS` note.
- `railway.toml` annotated with production flag guidance.

### Notes
- Epic 4 remains feature-flagged and off by default in production.
- Deployment automation to Railway intentionally scaffolded (manual via UI/CLI) to avoid accidental deploys during QA.

