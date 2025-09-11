# NL-FHIR Makefile (Epic 5 tooling)

.PHONY: help install run dev test smoke lint format docker-build

help:
	@echo "Targets:"
	@echo "  install      - Install package and deps"
	@echo "  run          - Run dev server (uvicorn)"
	@echo "  dev          - Run app with reload"
	@echo "  test         - Run full pytest suite"
	@echo "  smoke        - Run health/metrics smoke via TestClient"
	@echo "  docker-build - Build Docker image locally"

install:
	pip install --upgrade pip
	pip install .

run:
	uvicorn nl_fhir.main:app --host 0.0.0.0 --port 8000

dev:
	uvicorn nl_fhir.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest -q

smoke:
	python - <<'PY'
from fastapi.testclient import TestClient
from nl_fhir.main import app
client = TestClient(app)
for path in ('/health','/readiness','/liveness','/metrics'):
    r = client.get(path)
    assert r.status_code == 200, (path, r.text)
print('Smoke OK')
PY

docker-build:
	docker build -t nl-fhir:local .

