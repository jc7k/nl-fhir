# Production Readiness Roadmap: 9.5/10 → 10/10

**Current Score:** 9.5/10 (after test cleanup + 120 new tests)
**Target Score:** 10/10 (enterprise production-ready)
**Estimated Timeline:** 2-4 weeks for critical items, 2-3 months for complete hardening

---

## Current Status ✅

**Completed (9.5/10 achieved):**
- ✅ Comprehensive API endpoint testing (78 tests)
- ✅ Docker deployment validation (21 tests)
- ✅ Load and concurrent request testing (12 tests)
- ✅ HAPI FHIR failover resilience (9 tests)
- ✅ Test suite cleanup (removed 18 redundant files)
- ✅ Security testing (50+ tests for HIPAA, auth, input validation)
- ✅ Factory architecture testing (246 tests)
- ✅ Production Docker configurations (full + minimal modes)

**Remaining for 10/10:**
Below is the prioritized roadmap organized by impact and effort.

---

## Phase 1: Critical Production Infrastructure (1-2 weeks)
**Impact:** High | **Effort:** Medium | **Priority:** CRITICAL

These are essential for enterprise production deployments.

### 1.1 CI/CD Pipeline with Test Stages ⚠️ CRITICAL
**Why:** Automated quality gates prevent broken code from reaching production

**Implementation:**
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on: [push, pull_request]

jobs:
  # Stage 1: Fast unit tests (< 2 min)
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: uv run pytest tests/services/ tests/nlp/ -v --tb=short
        timeout-minutes: 3

  # Stage 2: Security tests (< 1 min)
  security-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run security tests
        run: uv run pytest tests/security/ -v
        timeout-minutes: 2

  # Stage 3: API tests (< 5 min)
  api-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run API endpoint tests
        run: uv run pytest tests/api/ -v
        timeout-minutes: 5

  # Stage 4: Integration tests (< 5 min)
  integration-tests:
    needs: [security-tests, api-tests]
    runs-on: ubuntu-latest
    steps:
      - name: Run integration tests
        run: uv run pytest tests/integration/ tests/epic/ -v
        timeout-minutes: 7

  # Stage 5: Load tests (< 5 min)
  load-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run load tests
        run: uv run pytest tests/load/ -v --tb=short
        timeout-minutes: 7

  # Stage 6: Docker deployment tests
  docker-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t nl-fhir:ci .
      - name: Run deployment tests
        run: uv run pytest tests/deployment/ -v -k "not slow"
        timeout-minutes: 10
```

**Deliverables:**
- [ ] GitHub Actions workflow file (`.github/workflows/ci.yml`)
- [ ] Test stage markers in pytest (`@pytest.mark.unit`, `@pytest.mark.integration`)
- [ ] Fast/slow test separation
- [ ] Automated PR checks
- [ ] Branch protection rules

**Time:** 2-3 days

---

### 1.2 Test Coverage Reporting ⚠️ CRITICAL
**Why:** Know exactly what code is tested vs. untested

**Implementation:**
```toml
# pyproject.toml (add to [tool.pytest.ini_options])
addopts = [
    "--cov=src/nl_fhir",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80"
]

[tool.coverage.run]
source = ["src/nl_fhir"]
omit = [
    "*/tests/*",
    "*/conftest.py",
    "*/__pycache__/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

**Commands:**
```bash
# Generate coverage report
uv run pytest --cov=src/nl_fhir --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Fail if coverage < 80%
uv run pytest --cov=src/nl_fhir --cov-fail-under=80
```

**Deliverables:**
- [ ] pytest-cov configuration in pyproject.toml
- [ ] Coverage reports in CI/CD
- [ ] Coverage badge in README
- [ ] Minimum 80% coverage requirement
- [ ] Coverage enforcement in CI

**Time:** 1 day

---

### 1.3 Security Scanning (SAST/Dependency Scanning) ⚠️ CRITICAL
**Why:** Detect vulnerabilities before production deployment

**Implementation:**
```yaml
# .github/workflows/security.yml
name: Security Scanning

on: [push, pull_request]

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # Scan for vulnerable dependencies
      - name: Safety check
        run: |
          uv pip install safety
          uv run safety check --json

      # Alternative: Use Snyk
      - name: Snyk scan
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  sast-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # Static analysis with bandit
      - name: Bandit security scan
        run: |
          uv pip install bandit
          uv run bandit -r src/ -f json -o bandit-report.json

      # Upload results
      - name: Upload security results
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: bandit-report.json
```

**Tools to integrate:**
- **Bandit:** Python security linter (SAST)
- **Safety:** Dependency vulnerability scanner
- **Snyk:** Comprehensive security platform
- **Trivy:** Container vulnerability scanner

**Deliverables:**
- [ ] Bandit SAST scanning in CI
- [ ] Dependency vulnerability scanning (Safety/Snyk)
- [ ] Docker image scanning (Trivy)
- [ ] Security policy documentation
- [ ] Automated security alerts

**Time:** 2-3 days

---

### 1.4 Observability & Monitoring ⚠️ CRITICAL
**Why:** Can't operate what you can't observe

**Implementation:**

**Structured Logging:**
```python
# src/nl_fhir/observability/logging.py
import structlog
from pythonjsonlogger import jsonlogger

def configure_logging():
    """Configure structured JSON logging for production"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

**Metrics/Telemetry:**
```python
# src/nl_fhir/observability/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# FHIR-specific metrics
fhir_conversion_count = Counter(
    'fhir_conversions_total',
    'Total FHIR conversions',
    ['status']
)

validation_success_rate = Gauge(
    'fhir_validation_success_rate',
    'FHIR validation success rate'
)
```

**Health Check Enhancement:**
```python
# src/nl_fhir/api/endpoints/health.py (enhanced)
@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependency status"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "hapi_fhir": check_hapi_status(),
            "database": check_db_status(),
            "nlp_models": check_nlp_models(),
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
        }
    }
```

**Deliverables:**
- [ ] Structured JSON logging (structlog/pythonjsonlogger)
- [ ] Prometheus metrics endpoint
- [ ] Distributed tracing (OpenTelemetry) - Optional
- [ ] Enhanced health checks with dependency status
- [ ] Error tracking integration (Sentry) - Optional
- [ ] Monitoring dashboard (Grafana) - Optional

**Time:** 3-5 days

---

## Phase 2: Code Quality & Testing Excellence (1-2 weeks)
**Impact:** High | **Effort:** Medium | **Priority:** HIGH

### 2.1 Test Markers & Organization
**Why:** Enable fast feedback loops and targeted test execution

**Implementation:**
```python
# conftest.py (add to existing)
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Fast unit tests (<1s each)")
    config.addinivalue_line("markers", "integration: Integration tests (requires services)")
    config.addinivalue_line("markers", "slow: Slow tests (>5s)")
    config.addinivalue_line("markers", "security: Security validation tests")
    config.addinivalue_line("markers", "performance: Performance benchmark tests")
    config.addinivalue_line("markers", "load: Load and stress tests")
    config.addinivalue_line("markers", "requires_hapi: Tests requiring HAPI FHIR server")
    config.addinivalue_line("markers", "requires_docker: Tests requiring Docker")

# Usage in tests:
@pytest.mark.unit
def test_fast_factory_creation():
    """Fast unit test"""
    pass

@pytest.mark.integration
@pytest.mark.requires_hapi
def test_hapi_validation():
    """Integration test requiring HAPI"""
    pass
```

**Commands:**
```bash
# Run only fast unit tests
uv run pytest -m unit

# Run integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"

# Run security tests only
uv run pytest -m security
```

**Deliverables:**
- [ ] Test markers configured
- [ ] All tests marked appropriately
- [ ] Fast test subset identified (<2 min)
- [ ] Documentation of test categories

**Time:** 2 days

---

### 2.2 Pre-commit Hooks & Code Quality
**Why:** Catch issues before they reach CI/CD

**Implementation:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-r, src/]
```

**Setup:**
```bash
# Install pre-commit
uv pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

**Deliverables:**
- [ ] .pre-commit-config.yaml
- [ ] Pre-commit hooks installed
- [ ] Documentation for developers
- [ ] CI enforcement of code quality

**Time:** 1 day

---

### 2.3 Property-Based Testing (Hypothesis)
**Why:** Discover edge cases automatically

**Implementation:**
```python
# tests/property/test_fhir_property_based.py
from hypothesis import given, strategies as st
import pytest

@given(
    medication_name=st.text(min_size=1, max_size=100),
    dosage=st.integers(min_value=1, max_value=1000),
    frequency=st.sampled_from(["daily", "BID", "TID", "QID"])
)
def test_medication_creation_properties(medication_name, dosage, frequency):
    """Property: Any valid inputs should create valid FHIR resource"""
    from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter

    factory = get_factory_adapter()
    factory.initialize()

    med_data = {
        "medication": medication_name,
        "dosage": f"{dosage}mg",
        "frequency": frequency
    }

    # Property: Should always create valid resource
    result = factory.create_medication_request(med_data, "Patient/test")

    assert result is not None
    assert result["resourceType"] == "MedicationRequest"
    assert "id" in result

@given(st.text())
def test_clinical_text_never_crashes(clinical_text):
    """Property: Any text input should never crash the API"""
    from fastapi.testclient import TestClient
    from src.nl_fhir.main import app

    client = TestClient(app)
    response = client.post("/convert", json={
        "clinical_text": clinical_text,
        "patient_ref": "Patient/test"
    })

    # Property: Should always return valid HTTP response (never crash)
    assert response.status_code in [200, 400, 422, 500]
```

**Deliverables:**
- [ ] Hypothesis installed and configured
- [ ] 10-15 property-based tests
- [ ] Documentation of property testing approach

**Time:** 3-4 days

---

### 2.4 Mutation Testing
**Why:** Verify tests actually catch bugs

**Implementation:**
```bash
# Install mutmut
uv pip install mutmut

# Run mutation testing
mutmut run --paths-to-mutate=src/nl_fhir

# See results
mutmut results

# Show specific mutation
mutmut show <id>
```

```toml
# pyproject.toml
[tool.mutmut]
paths_to_mutate = "src/nl_fhir/"
backup = false
runner = "pytest -x"
tests_dir = "tests/"
```

**Target:** 80%+ mutation score (80% of mutations caught by tests)

**Deliverables:**
- [ ] Mutation testing configured
- [ ] Baseline mutation score established
- [ ] High-value mutations identified and killed
- [ ] CI integration (optional - can be slow)

**Time:** 3-4 days

---

## Phase 3: Advanced Testing & Resilience (2-3 weeks)
**Impact:** Medium-High | **Effort:** High | **Priority:** MEDIUM

### 3.1 Chaos Engineering Tests
**Why:** Validate resilience under failure conditions

**Implementation:**
```python
# tests/chaos/test_resilience.py
import pytest
from unittest.mock import patch
import random
import time

class TestChaosEngineering:
    """Chaos engineering tests for resilience validation"""

    def test_random_hapi_failures(self):
        """Test resilience with random HAPI failures"""
        import requests

        original_post = requests.post

        def chaotic_post(*args, **kwargs):
            # 30% chance of failure
            if random.random() < 0.3:
                raise requests.ConnectionError("Chaos: Random failure")
            return original_post(*args, **kwargs)

        with patch('requests.post', side_effect=chaotic_post):
            # System should handle random failures gracefully
            from fastapi.testclient import TestClient
            from src.nl_fhir.main import app

            client = TestClient(app)

            successes = 0
            for _ in range(20):
                response = client.post("/convert", json={
                    "clinical_text": "metformin 500mg",
                    "patient_ref": "Patient/chaos"
                })
                if response.status_code == 200:
                    successes += 1

            # At least 70% should succeed despite chaos
            assert successes >= 14

    def test_slow_dependencies(self):
        """Test resilience with slow dependencies"""
        import requests

        original_post = requests.post

        def slow_post(*args, **kwargs):
            time.sleep(random.uniform(0.1, 2.0))  # Random delay
            return original_post(*args, **kwargs)

        with patch('requests.post', side_effect=slow_post):
            # Should handle slow dependencies without cascading failures
            pass  # Implementation

    def test_memory_pressure(self):
        """Test behavior under memory pressure"""
        # Simulate memory pressure and verify graceful degradation
        pass

    def test_cpu_spike(self):
        """Test behavior during CPU spikes"""
        # Simulate CPU-intensive operations
        pass
```

**Deliverables:**
- [ ] Chaos engineering test suite (10-15 tests)
- [ ] Random failure injection
- [ ] Latency injection
- [ ] Resource exhaustion tests
- [ ] Documentation of chaos scenarios

**Time:** 4-5 days

---

### 3.2 Performance Regression Testing
**Why:** Prevent performance degradation over time

**Implementation:**
```python
# tests/performance/test_regression.py
import pytest
import time
import json
from pathlib import Path

# Store baseline performance metrics
BASELINE_FILE = Path("tests/performance/baseline_metrics.json")

def load_baseline():
    if BASELINE_FILE.exists():
        return json.loads(BASELINE_FILE.read_text())
    return {}

def save_baseline(metrics):
    BASELINE_FILE.write_text(json.dumps(metrics, indent=2))

class TestPerformanceRegression:
    """Detect performance regressions"""

    def test_conversion_performance_baseline(self):
        """Ensure conversion performance doesn't regress"""
        from fastapi.testclient import TestClient
        from src.nl_fhir.main import app

        client = TestClient(app)

        # Measure current performance
        durations = []
        for _ in range(50):
            start = time.time()
            response = client.post("/convert", json={
                "clinical_text": "metformin 500mg",
                "patient_ref": "Patient/perf-test"
            })
            duration = time.time() - start
            if response.status_code == 200:
                durations.append(duration)

        avg_duration = sum(durations) / len(durations)
        p95_duration = sorted(durations)[int(len(durations) * 0.95)]

        # Compare to baseline
        baseline = load_baseline()

        if "conversion_avg" in baseline:
            # Allow 10% regression
            assert avg_duration < baseline["conversion_avg"] * 1.1, \
                f"Performance regression: {avg_duration:.3f}s vs baseline {baseline['conversion_avg']:.3f}s"
        else:
            # Establish baseline
            baseline["conversion_avg"] = avg_duration
            baseline["conversion_p95"] = p95_duration
            save_baseline(baseline)
```

**Deliverables:**
- [ ] Performance baseline metrics
- [ ] Regression detection tests
- [ ] Automated performance tracking
- [ ] Performance budget enforcement

**Time:** 2-3 days

---

### 3.3 Contract Testing (API Versioning)
**Why:** Ensure API backwards compatibility

**Implementation:**
```python
# tests/contract/test_api_contracts.py
import pytest
from pact import Consumer, Provider
from fastapi.testclient import TestClient
from src.nl_fhir.main import app

# Define API contract
class TestAPIContract:
    """Verify API contracts don't break"""

    def test_convert_endpoint_contract_v1(self):
        """Verify /convert endpoint maintains contract"""
        client = TestClient(app)

        # Required request fields (contract)
        required_request = {
            "clinical_text": "metformin 500mg"
        }

        response = client.post("/convert", json=required_request)

        assert response.status_code == 200
        data = response.json()

        # Required response fields (contract)
        assert "fhir_bundle" in data
        assert "request_id" in data
        assert "processing_time" in data

        # Type contracts
        assert isinstance(data["fhir_bundle"], (dict, type(None)))
        assert isinstance(data["request_id"], str)
        assert isinstance(data["processing_time"], (int, float))
```

**Deliverables:**
- [ ] API contract definitions
- [ ] Contract validation tests
- [ ] Breaking change detection
- [ ] API versioning strategy

**Time:** 3-4 days

---

## Phase 4: Documentation & Operations (1 week)
**Impact:** Medium | **Effort:** Medium | **Priority:** MEDIUM

### 4.1 Operations Runbook
**Why:** Enable operational excellence

**Deliverables:**
- [ ] Deployment procedures
- [ ] Rollback procedures
- [ ] Incident response playbook
- [ ] Troubleshooting guide
- [ ] Common issues & solutions
- [ ] Escalation procedures

**Time:** 2-3 days

---

### 4.2 Architecture Decision Records (ADRs)
**Why:** Document why architectural choices were made

**Example:**
```markdown
# ADR-001: Use HAPI FHIR for Validation

## Status
Accepted

## Context
Need reliable FHIR R4 validation for production bundles.

## Decision
Use HAPI FHIR as primary validation, fall back to local fhir.resources library.

## Consequences
- Positive: Industry-standard validation
- Positive: Comprehensive error messages
- Negative: External dependency
- Mitigation: Graceful fallback to local validation
```

**Deliverables:**
- [ ] ADR template
- [ ] 5-10 key ADRs documented
- [ ] ADR review process

**Time:** 2 days

---

### 4.3 Disaster Recovery Plan
**Why:** Ensure business continuity

**Deliverables:**
- [ ] Backup procedures
- [ ] Recovery time objectives (RTO)
- [ ] Recovery point objectives (RPO)
- [ ] Data restoration procedures
- [ ] Failover testing

**Time:** 2-3 days

---

## Summary: Path to 10/10

### Must-Have (Critical - 2 weeks)
1. ✅ CI/CD Pipeline with test stages (3 days)
2. ✅ Test coverage reporting >80% (1 day)
3. ✅ Security scanning (SAST + dependencies) (3 days)
4. ✅ Observability & monitoring (4 days)
5. ✅ Test markers & organization (2 days)

**Result after critical items: 9.8/10**

### Should-Have (High Priority - +1 week)
6. ✅ Pre-commit hooks (1 day)
7. ✅ Property-based testing (3 days)
8. ✅ Mutation testing (3 days)

**Result after high priority: 9.9/10**

### Nice-to-Have (Medium Priority - +2 weeks)
9. ✅ Chaos engineering (5 days)
10. ✅ Performance regression tests (3 days)
11. ✅ Contract testing (3 days)
12. ✅ Operations documentation (4 days)

**Result after all items: 10/10** 🎯

---

## Quick Start: Critical Path (1 Week)

**Week 1 Focus - Get to 9.8/10:**
- Day 1: CI/CD pipeline setup
- Day 2: Test coverage configuration
- Day 3-4: Security scanning integration
- Day 5-7: Observability & monitoring

**This gets you production-ready enough to deploy with confidence.**

---

## Estimated Total Timeline

- **Phase 1 (Critical):** 2 weeks → **9.8/10**
- **Phase 2 (High Priority):** +1 week → **9.9/10**
- **Phase 3 (Advanced):** +2 weeks → **9.95/10**
- **Phase 4 (Documentation):** +1 week → **10/10**

**Total:** 6 weeks to perfect 10/10 production readiness

**Minimum viable production deployment:** 2 weeks (9.8/10 with Phase 1 complete)
