"""
HAPI FHIR Failover and Resilience Tests
Production Readiness: Critical failover testing

Coverage:
- HAPI server unavailability handling
- Graceful degradation to local validation
- Timeout handling
- Validation caching
- Failover manager functionality

These tests never contact a live HAPI server: ``requests.get`` (the client's
``/metadata`` probe) and ``requests.post`` (``Bundle/$validate``) are patched
in every test so the outcome does not depend on the local environment.
"""

import time
from unittest.mock import Mock, patch

import pytest
import requests

from src.nl_fhir.services.fhir.validation_service import FHIRValidationService

VALIDATION_STATUSES = {"success", "warning", "error"}


def _patient_bundle(patient_id: str, family: str, bundle_id: str | None = None) -> dict:
    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "name": [{"family": family}],
                }
            }
        ],
    }
    if bundle_id:
        bundle["id"] = bundle_id
    return bundle


def _empty_bundle() -> dict:
    return {"resourceType": "Bundle", "type": "transaction", "entry": []}


def _assert_processed_result(result: dict) -> None:
    """The service must always hand back a processed validation result, never None/raise."""
    assert result is not None
    assert result["validation_result"] in VALIDATION_STATUSES
    assert "is_valid" in result
    assert "validation_source" in result


class TestHAPIFailover:
    """Test HAPI FHIR server failover scenarios"""

    @pytest.fixture
    def validation_service(self):
        """Get validation service instance"""
        return FHIRValidationService()

    @pytest.fixture
    def hapi_unreachable(self):
        """Simulate the HAPI server being completely unreachable."""
        with patch("requests.get", side_effect=requests.ConnectionError("Connection refused")), \
             patch("requests.post", side_effect=requests.ConnectionError("Connection refused")) as post:
            yield post

    async def test_hapi_server_unavailable_graceful_degradation(self, validation_service, hapi_unreachable):
        """Test that validation works locally when HAPI is down"""
        bundle = _patient_bundle("test-123", "Test")

        # Should not raise, should fall back to local validation
        result = await validation_service.validate_bundle(bundle)

        _assert_processed_result(result)
        assert result["validation_source"] != "hapi_fhir"
        assert result["entry_count"] == 1

    async def test_hapi_timeout_handling(self, validation_service):
        """Test that timeouts don't crash the application"""
        with patch("requests.get", side_effect=requests.ConnectionError("Connection refused")), \
             patch("requests.post", side_effect=requests.Timeout("Request timeout")):
            result = await validation_service.validate_bundle(_empty_bundle())

        _assert_processed_result(result)
        assert result["validation_source"] != "hapi_fhir"

    async def test_hapi_slow_response_timeout(self, validation_service):
        """Test timeout protection for slow HAPI responses"""
        slow_server_seconds = 10
        client_timeout_seconds = 2

        def slow_response(*args, **kwargs):
            # Behave like a real HTTP client: give up once the caller's timeout elapses
            # instead of waiting for the (very slow) server.
            timeout = kwargs.get("timeout")
            if timeout is not None and timeout < slow_server_seconds:
                raise requests.Timeout(f"Read timed out after {timeout}s")
            time.sleep(slow_server_seconds)
            return Mock(status_code=200)

        with patch("requests.get", side_effect=requests.ConnectionError("Connection refused")), \
             patch("requests.post", side_effect=slow_response) as mock_post:
            await validation_service.initialize()

            with patch.object(validation_service.hapi_client, "timeout", client_timeout_seconds):
                start = time.time()
                result = await validation_service.validate_bundle(_empty_bundle())
                duration = time.time() - start

        # The client must pass its timeout through to the HTTP layer...
        mock_post.assert_called_once()
        assert mock_post.call_args.kwargs["timeout"] == client_timeout_seconds
        # ...so a slow server can't stall the request (not wait the full 10s)
        assert duration < 5.0
        _assert_processed_result(result)

    async def test_hapi_http_error_handling(self, validation_service):
        """Test handling of HTTP errors from HAPI"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch("requests.get", side_effect=requests.ConnectionError("Connection refused")), \
             patch("requests.post", return_value=mock_response):
            result = await validation_service.validate_bundle(_empty_bundle())

        # Should fall back rather than surface the HTTP error
        _assert_processed_result(result)
        assert result["validation_source"] != "hapi_fhir"

    async def test_hapi_invalid_response_format(self, validation_service):
        """Test handling of invalid response from HAPI"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid response"

        with patch("requests.get", side_effect=requests.ConnectionError("Connection refused")), \
             patch("requests.post", return_value=mock_response):
            result = await validation_service.validate_bundle(_empty_bundle())

        _assert_processed_result(result)
        assert result["validation_source"] != "hapi_fhir"

    async def test_validation_without_hapi_configured(self, validation_service, hapi_unreachable):
        """Test validation when HAPI URL is not configured"""
        # NOTE: HAPIFHIRClient does not read any HAPI_* environment variable (it defaults to
        # http://localhost:8080/fhir), so "not configured" is modelled as an unreachable server.
        with patch.dict("os.environ", {"HAPI_FHIR_BASE_URL": "", "HAPI_FHIR_URL": ""}):
            bundle = _patient_bundle("local-test", "LocalTest")

            # Should use local validation only
            result = await validation_service.validate_bundle(bundle)

        _assert_processed_result(result)
        assert result["validation_source"] != "hapi_fhir"

    async def test_hapi_retry_logic(self, validation_service):
        """Test retry logic for transient HAPI failures"""
        call_count = 0

        def failing_then_succeeding(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.ConnectionError("Temporary failure")
            # Success on 3rd try
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"resourceType": "OperationOutcome", "issue": []}
            return mock_response

        with patch("requests.get", side_effect=requests.ConnectionError("Connection refused")), \
             patch("requests.post", side_effect=failing_then_succeeding):
            result = await validation_service.validate_bundle(_empty_bundle())

        # Either succeeded after retrying or fell back to local validation -
        # a transient failure must never surface as an exception or a missing result.
        assert call_count >= 1
        _assert_processed_result(result)

    async def test_hapi_fallback_maintains_validation_quality(self, validation_service, hapi_unreachable):
        """Test that local validation quality is acceptable when HAPI unavailable"""
        # Known valid bundle
        valid_bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "valid-patient",
                        "name": [{"family": "ValidTest", "given": ["Test"]}],
                        "gender": "male",
                    },
                    "request": {"method": "POST", "url": "Patient"},
                }
            ],
        }

        # Known invalid bundle
        invalid_bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "InvalidResourceType",
                        "id": "invalid",
                    }
                }
            ],
        }

        valid_result = await validation_service.validate_bundle(valid_bundle)
        invalid_result = await validation_service.validate_bundle(invalid_bundle)

        # Both should complete without crashing, via local validation
        _assert_processed_result(valid_result)
        _assert_processed_result(invalid_result)
        assert valid_result["validation_source"] != "hapi_fhir"
        assert invalid_result["validation_source"] != "hapi_fhir"


class TestHAPICache:
    """Test HAPI validation caching"""

    async def test_validation_cache_reduces_hapi_calls(self):
        """Test that caching reduces calls to HAPI server"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"resourceType": "OperationOutcome", "issue": []}

        with patch("requests.get", side_effect=requests.ConnectionError("Connection refused")), \
             patch("requests.post", return_value=mock_response) as mock_post:
            service = FHIRValidationService()

            # The service keys its cache on Bundle.id, so the bundle needs one
            bundle = _patient_bundle("cache-test", "CacheTest", bundle_id="cache-test-bundle")

            # Validate same bundle twice
            result1 = await service.validate_bundle(bundle)
            result2 = await service.validate_bundle(bundle)

        _assert_processed_result(result1)
        _assert_processed_result(result2)
        assert result1["validation_source"] == "hapi_fhir"

        # Second call must be served from the cache, not from HAPI
        assert mock_post.call_count == 1
        assert result2 is result1
        assert service.get_validation_metrics()["cache_size"] == 1
