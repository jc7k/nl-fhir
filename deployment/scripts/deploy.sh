#!/usr/bin/env bash
set -euo pipefail

# NL-FHIR Railway Deploy Script (scaffold)
# Usage: ./deployment/scripts/deploy.sh <environment>
# Environments: development | staging | production

ENVIRONMENT="${1:-}"
if [[ -z "${ENVIRONMENT}" ]]; then
  echo "Usage: $0 <environment>" >&2
  exit 2
fi

if ! command -v railway >/dev/null 2>&1; then
  echo "Error: Railway CLI not found. Install from https://docs.railway.app/develop/cli" >&2
  exit 1
fi

echo "Preparing deployment for environment: ${ENVIRONMENT}"
echo "Reminder: Set variables per docs/operations/railway-variables-setup.md before deploying."
echo "Safety: Keep Epic 4 flags disabled in prod unless approved (SUMMARIZATION_ENABLED=false, SAFETY_VALIDATION_ENABLED=false)."

# Example commands (uncomment and adapt to your project setup):
# Select project and environment
# railway use --project <your-project-id-or-name>
# railway env set ENVIRONMENT=${ENVIRONMENT}

# Trigger deploy using Dockerfile (default behavior with railway.toml)
# railway up --service <service-name>

echo "This is a scaffold. Use Railway UI or CLI to deploy."
echo "After deploy, run: ./deployment/scripts/health-check.sh <service-url>"

exit 0

