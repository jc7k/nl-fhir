#!/usr/bin/env bash
set -euo pipefail

# NL-FHIR Health Check Script
# Usage: ./deployment/scripts/health-check.sh <base-url>

BASE_URL="${1:-}"
if [[ -z "${BASE_URL}" ]]; then
  echo "Usage: $0 <base-url> (e.g., https://your-service.up.railway.app)" >&2
  exit 2
fi

echo "Checking endpoints on ${BASE_URL} ..."

do_request() {
  local path="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "${BASE_URL}${path}" | sed -e 's/.*/OK: '&/dev/null
    echo "${path} OK"
  else
    python - <<PY
import sys, json
import requests
base = sys.argv[1]
path = sys.argv[2]
r = requests.get(base+path, timeout=10)
assert r.status_code == 200, (path, r.status_code, r.text)
print(path, 'OK')
PY
    \
    "${BASE_URL}" "${path}" >/dev/null
  fi
}

do_request "/health"
do_request "/readiness"
do_request "/liveness"
do_request "/metrics"

echo "All checks passed."

