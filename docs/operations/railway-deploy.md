# Railway Deployment Runbook (Epic 5.1)

This guide describes how to deploy NL‑FHIR to Railway safely, without impacting Epic 4 development.

## Prerequisites

- Railway account with project access
- Docker enabled locally (optional for local validation)
- Secrets for production (set in Railway dashboard):
  - `SECRET_KEY`
  - `DATABASE_URL` (PostgreSQL, if used)
  - `SENTRY_DSN` (optional)
  - `ALLOWED_HOSTS` (e.g., `*.up.railway.app`)
  - Epic 4 flags should remain disabled unless explicitly required:
    - `SUMMARIZATION_ENABLED=false`
    - `SAFETY_VALIDATION_ENABLED=false`

## Environments

Create separate environments in Railway:

- `development` — safe sandbox; can enable experimental flags
- `staging` — mirrors production; feature flags off by default
- `production` — flags for Epic 4 remain off unless approved

Recommended core env vars by environment:

- Common:
  - `ENVIRONMENT=production|staging|development`
  - `LOG_LEVEL=INFO` (use `DEBUG` for development only)
  - `CORS_ORIGINS` (prod: your frontend origin)
  - `ALLOWED_HOSTS=*.up.railway.app`
  - `WORKERS=4` (Gunicorn worker count; documented default)

## Build & Deploy

The repository contains `Dockerfile` (multi‑stage, non‑root) and `railway.toml`:

- Build: Railway uses the provided Dockerfile via `builder = "DOCKERFILE"`
- Start: `gunicorn nl_fhir.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT ...`

Notes:
- `$PORT` is injected by Railway; no change needed
- Worker count is 4 by default; you can override start command in Railway UI if needed
- Health endpoint `/health` is used for readiness checks

Helper scripts (scaffolds):
- `./deployment/scripts/deploy.sh <environment>` — reminds required steps and triggers CLI deploy (adapt as needed)
- `./deployment/scripts/rollback.sh <deployment-id>` — reminder scaffold for rollback
- `./deployment/scripts/health-check.sh <service-url>` — probes `/health`, `/readiness`, `/liveness`, `/metrics`

## Health, Readiness, Liveness & Metrics

- Health: `GET /health` returns JSON system health
- Readiness: `GET /readiness` indicates if service can receive traffic
- Liveness: `GET /liveness` indicates if service should be restarted
- Metrics: `GET /metrics` returns app metrics (no PHI)
- All are enabled by default (`ENABLE_HEALTH_CHECK=true`, `ENABLE_METRICS=true`)

## Secrets Management

- Use Railway’s Variables UI for all secrets (never commit secrets)
- Suggested variables:
  - `SECRET_KEY` — application secret
  - `DATABASE_URL` — if enabling DB
  - `SENTRY_DSN` — optional error monitoring
  - Epic 4 (keep disabled unless explicitly approved):
    - `SUMMARIZATION_ENABLED=false`
    - `SAFETY_VALIDATION_ENABLED=false`

## Scaling & Performance

- Start with `2 vCPU / 2GB RAM`; increase if NLP (Epic 2) is enabled
- Keep Epic 4 disabled in production until ownership transfer is complete
- Use staging to test new flags before enabling in production

## Rollback

- Railway keeps prior deploys; roll back via Railway UI → Deployments
- Because containers are immutable, rollbacks are instant and safe
- Ensure database migrations (if introduced) are backward‑compatible or reversible

## Safety Guardrails for Parallel Development

- Do not modify Epic 4 services while deploying infra
- Keep `SUMMARIZATION_ENABLED` and `SAFETY_VALIDATION_ENABLED` false in production
- Group infra changes in separate PRs labeled `epic-5`

## Local Validation (Optional)

Run locally using Docker Compose (dev mode):

```bash
docker compose up --build
# Then: curl http://localhost:8000/health
```

## Checklist (Go‑Live)

- [ ] Separate Railway environments created (dev/staging/prod)
- [ ] Required secrets set in each environment
- [ ] Health and metrics endpoints verified in staging
- [ ] Epic 4 flags remain disabled in production
- [ ] Rollback procedure confirmed in Railway UI
