# NL-FHIR: Natural Language → FHIR R4 Converter

![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg)

Production‑ready FastAPI service that converts clinical natural language into FHIR R4 bundles, with safety validation and reverse validation features.

## Quick Start

```bash
make install
make dev
# Open http://localhost:8000/docs
```

Smoke check (health/readiness/liveness/metrics):

```bash
make smoke
```

## Deploy to Railway (Epic 5)

- Set environment variables per `docs/operations/railway-variables-setup.md`.
- Review the deployment runbook in `docs/operations/railway-deploy.md`.
- Optional scripts (scaffolds):
  - `./deployment/scripts/deploy.sh <environment>`
  - `./deployment/scripts/rollback.sh <deployment-id>`
  - `./deployment/scripts/health-check.sh <service-url>`

Notes:
- Keep Epic 4 flags disabled in production unless explicitly approved:
  - `SUMMARIZATION_ENABLED=false`
  - `SAFETY_VALIDATION_ENABLED=false`

## CI

GitHub Actions pipeline runs core tests and smoke checks on PRs. A nightly full test suite runs as a non‑blocking job. See `.github/workflows/ci.yml`.

