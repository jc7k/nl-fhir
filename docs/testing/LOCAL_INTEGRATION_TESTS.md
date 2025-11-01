# Local Integration Testing Guide

## Overview

Integration tests are **NOT run in CI/CD** due to GitHub Actions service container health check limitations. These tests require a fully operational HAPI FHIR server, which takes 35-40 seconds to initialize - longer than GitHub Actions will wait.

**Run integration tests locally only.**

## Why Integration Tests Are Skipped in CI/CD

### GitHub Actions Health Check Limitations

GitHub Actions service containers have hardcoded health check behavior:
- **Hardcoded retry limit**: 5-6 attempts only (ignores `--health-retries` configuration)
- **Exponential backoff**: 2s, 3s, 7s, 32s, 32s intervals
- **Maximum wait time**: ~2.5 minutes total
- **HAPI FHIR startup time**: 29s application start + 5-10s first `/fhir/metadata` request = **35-40 seconds**

Result: GitHub Actions abandons the health check before HAPI FHIR becomes healthy.

### Decision: Local Testing Only (Option B)

After attempting configuration changes, we determined that integration tests should run locally only:
- ✅ **Local development**: Full integration test coverage with docker-compose
- ❌ **CI/CD pipeline**: Unit, security, API, load, and Docker tests only

See Issue #44 for full analysis and decision rationale.

## Running Integration Tests Locally

### Prerequisites

1. **Docker and Docker Compose installed**
2. **Project dependencies installed**: `uv sync`
3. **Available ports**: 8080 (HAPI FHIR), 8001 (NL-FHIR API)

### Quick Start

```bash
# 1. Start HAPI FHIR server (background)
docker-compose up -d hapi-fhir

# 2. Wait for HAPI to become healthy (~35-40 seconds)
docker-compose ps  # Check status - should show "healthy"

# 3. Run integration tests
uv run pytest tests/epic/ tests/integration/ -v

# 4. Stop HAPI FHIR when done
docker-compose down
```

### Detailed Instructions

#### Step 1: Start HAPI FHIR Server

```bash
# Start in detached mode (background)
docker-compose up -d hapi-fhir

# OR: Start with logs visible (foreground)
docker-compose up hapi-fhir
```

**Expected startup time**: 35-40 seconds

#### Step 2: Verify HAPI FHIR Health

```bash
# Check container status
docker-compose ps

# Expected output:
# NAME                    STATUS
# nl-fhir-hapi-fhir-1    Up 45 seconds (healthy)

# Manual health check
curl http://localhost:8080/fhir/metadata

# Expected: JSON response with FHIR CapabilityStatement
```

#### Step 3: Run Integration Tests

```bash
# Run all integration tests
uv run pytest tests/epic/ tests/integration/ -v

# Run specific integration test files
uv run pytest tests/test_story_3_3_hapi.py -v
uv run pytest tests/epic/test_story_1_1_basic_input.py -v

# Run with detailed output
uv run pytest tests/epic/ -vv --tb=short

# Run specific test scenario
uv run pytest tests/epic/ -k "medication_request" -v
```

#### Step 4: Clean Up

```bash
# Stop HAPI FHIR server
docker-compose down

# Stop and remove volumes (fresh start next time)
docker-compose down -v
```

## Integration Test Coverage

### Test Suites

1. **Epic Tests** (`tests/epic/`)
   - Story 1.1: Basic input validation
   - Story 3.3: HAPI FHIR integration
   - End-to-end workflow validation

2. **Integration Tests** (`tests/integration/`)
   - FHIR bundle validation
   - HAPI FHIR transaction processing
   - Multi-resource workflows

### Expected Results

```bash
# Successful run output:
tests/epic/test_story_1_1_basic_input.py::test_basic_input PASSED
tests/test_story_3_3_hapi.py::test_hapi_connection PASSED
tests/test_story_3_3_hapi.py::test_bundle_validation PASSED
...

====== 8 passed in 3.47s ======
```

## Troubleshooting

### HAPI FHIR Won't Start

**Problem**: Container stays in "starting" status for 2+ minutes

**Solution**:
```bash
# Check logs for errors
docker-compose logs hapi-fhir

# Common issues:
# - Port 8080 already in use: Stop other services or change port
# - Insufficient memory: Allocate more memory to Docker (4GB+ recommended)
# - Corrupted volume: Remove volumes and restart
docker-compose down -v
docker-compose up -d hapi-fhir
```

### Connection Refused Errors

**Problem**: Tests fail with "Connection refused" to http://localhost:8080

**Cause**: HAPI FHIR not fully initialized yet

**Solution**:
```bash
# Wait longer for HAPI to become healthy
docker-compose ps  # Verify status is "healthy"

# Manual health check
curl http://localhost:8080/fhir/metadata

# If metadata endpoint works, re-run tests
uv run pytest tests/epic/ -v
```

### Tests Fail with Validation Errors

**Problem**: FHIR bundles fail HAPI validation

**Cause**: This is expected behavior - integration tests verify validation logic

**Solution**: Check test output for specific validation failures. These should be handled gracefully by the application.

## CI/CD Pipeline (Without Integration Tests)

The CI/CD pipeline runs 5 stages instead of 6:

1. **Stage 1**: Unit Tests (factory + NLP)
2. **Stage 2**: Security Scanning
3. **Stage 3**: API Endpoint Tests
4. **~~Stage 4: Integration Tests~~** ❌ **SKIPPED** (run locally only)
5. **Stage 5**: Load & Performance Tests
6. **Stage 6**: Docker Deployment Tests

Integration tests must pass locally before merging PRs.

## Local Development Workflow

```bash
# Daily development routine:
1. Start HAPI FHIR: docker-compose up -d hapi-fhir
2. Develop features
3. Run unit tests frequently: uv run pytest tests/services/ tests/nlp/ -v
4. Run integration tests before committing: uv run pytest tests/epic/ -v
5. Stop HAPI when done: docker-compose down
```

## Performance Benchmarks

- **HAPI FHIR startup**: 29 seconds (application ready)
- **First `/fhir/metadata` request**: 5-10 seconds
- **Total initialization**: 35-40 seconds
- **Integration test suite**: ~3-4 seconds (after HAPI ready)

## Related Documentation

- **Issue #44**: GitHub Actions health check limitations analysis
- **PR #47**: Integration test removal from CI/CD
- **docker-compose.yml**: HAPI FHIR service configuration
- **docs/prd/story-3-3-hapi-fhir-integration.md**: HAPI integration requirements

## FAQ

**Q: Why not use a lighter FHIR server for CI/CD?**
A: HAPI FHIR is our production validation backend. Testing against a different server would reduce test validity.

**Q: Can we cache the HAPI container to speed up startup?**
A: HAPI initialization time is application startup (Java Spring Boot), not Docker image pull. Caching won't help.

**Q: Should integration tests run before every commit?**
A: Yes, locally. They should pass before pushing to remote, but CI/CD will skip them.

**Q: What if integration tests fail locally but CI/CD passes?**
A: Do not merge. Integration tests validate critical FHIR functionality. Local failures indicate real issues.
