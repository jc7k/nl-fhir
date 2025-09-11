#!/usr/bin/env bash
set -euo pipefail

# NL-FHIR Railway Rollback Script (scaffold)
# Usage:
#   List deployments:  railway deployments
#   Roll back:         ./deployment/scripts/rollback.sh <deployment-id>

DEPLOY_ID="${1:-}"
if [[ -z "${DEPLOY_ID}" ]]; then
  echo "Usage: $0 <deployment-id>" >&2
  echo "Tip: Use 'railway deployments' to get the deployment id." >&2
  exit 2
fi

if ! command -v railway >/dev/null 2>&1; then
  echo "Error: Railway CLI not found. Install from https://docs.railway.app/develop/cli" >&2
  exit 1
fi

echo "Rolling back to deployment: ${DEPLOY_ID}"

# Example command (uncomment when ready):
# railway rollback ${DEPLOY_ID}

echo "This is a scaffold. You can also roll back via Railway UI → Deployments."
echo "After rollback, run: ./deployment/scripts/health-check.sh <service-url>"

exit 0

