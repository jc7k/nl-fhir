## Summary

Describe the purpose of this PR. Reference Epic/Story (e.g., Epic 5: 5.1–5.4) and link to relevant docs.

## Changes

- Infra/CI: (list)  
- Monitoring/Probes: (list)  
- Docs/Runbooks: (list)

## Deployment Notes (Railway)

- Follow `docs/operations/railway-variables-setup.md` to configure variables in Railway per environment.
- See `docs/operations/railway-deploy.md` for deploy/rollback and health checks.
- Helper scripts (scaffolds): `deployment/scripts/deploy.sh`, `rollback.sh`, `health-check.sh`.

## Feature Flags

- Epic 4 flags remain OFF by default in production:
  - `SUMMARIZATION_ENABLED=false`
  - `SAFETY_VALIDATION_ENABLED=false`

## How to Test

Local:
```bash
make install
make dev
make smoke  # /health, /readiness, /liveness, /metrics
```

CI:
- PR checks include core tests, Docker build validation, and smoke probes. See GitHub Actions tab.

## QA Checklist

- [ ] CI jobs (build-test, tests-core, docker-build) are green
- [ ] Nightly/dispatch `tests-full` passes (non-blocking)
- [ ] Probes return 200 locally and in staging (`health-check.sh`)
- [ ] Production logs are JSON when `ENVIRONMENT=production`
- [ ] Railway variables set per environment docs

## Risks

- Deployment automation to Railway is scaffolded; manual deploys used during QA to avoid accidental releases.

## Rollback Plan

- Use Railway UI → Deployments to roll back, or `deployment/scripts/rollback.sh <deployment-id>`.

