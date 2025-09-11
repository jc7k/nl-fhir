# Railway Variables Setup Guide

This guide shows how to set environment variables in Railway for each environment (development, staging, production).

## 1) Open Your Railway Project

1. Go to https://railway.app and open your project.
2. Select the service that runs the FastAPI app (Dockerfile-based).

## 2) Configure Environments

If your project uses multiple environments (recommended):

1. In the project, create environments: `development`, `staging`, and `production`.
2. For each environment, you can set variables that apply only to that environment.

## 3) Set Variables (Per Environment)

Set the variables below in the Variables (or Settings → Variables) section for each environment.

### Development
- ENVIRONMENT=development
- LOG_LEVEL=DEBUG
- ALLOWED_HOSTS=localhost,127.0.0.1,*.up.railway.app,testserver
- CORS_ORIGINS=http://localhost:3000,http://localhost:8080
- SECRET_KEY=<dev-secret>
- WORKERS=1
- ENABLE_HEALTH_CHECK=true
- ENABLE_METRICS=true
- SUMMARIZATION_ENABLED=false
- SAFETY_VALIDATION_ENABLED=false

### Staging
- ENVIRONMENT=staging
- LOG_LEVEL=INFO
- ALLOWED_HOSTS=*.up.railway.app
- CORS_ORIGINS=<staging-frontend-origin>
- SECRET_KEY=<staging-secret>
- WORKERS=2
- ENABLE_HEALTH_CHECK=true
- ENABLE_METRICS=true
- SUMMARIZATION_ENABLED=false
- SAFETY_VALIDATION_ENABLED=false

### Production
- ENVIRONMENT=production
- LOG_LEVEL=INFO
- ALLOWED_HOSTS=*.up.railway.app
- CORS_ORIGINS=<production-frontend-origin>
- SECRET_KEY=<strong-unique-secret>
- WORKERS=4
- ENABLE_HEALTH_CHECK=true
- ENABLE_METRICS=true
- SUMMARIZATION_ENABLED=false
- SAFETY_VALIDATION_ENABLED=false

Optional (when needed):
- DATABASE_URL=<postgres-connection>
- REDIS_URL=<redis-connection>
- HAPI_FHIR_URL=<hapi-fhir-endpoint>
- FHIR_VALIDATION_ENABLED=true
- SENTRY_DSN=<sentry-dsn>

## 4) Deploy and Verify

1. Trigger a deploy in Railway.
2. After deploy, open the service URL and check `/health` — it should return HTTP 200.
3. Optionally check `/metrics` for application metrics.

If `/health` fails, check logs for missing or misconfigured variables.

## Notes

- Do not enable Epic 4 flags (`SUMMARIZATION_ENABLED`, `SAFETY_VALIDATION_ENABLED`) in production until approved.
- You can override the worker count by editing the start command in Railway; default is 4 as set in `railway.toml`.

