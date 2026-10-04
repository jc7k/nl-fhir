"""
Load and Concurrent Request Tests
Production Readiness: Performance under load testing

Coverage:
- Concurrent request handling
- Rate limiting
- Memory stability under load
- Response time degradation
- Connection pool handling

Timing policy
-------------
These tests run in-process through TestClient, so wall-clock numbers measure
the test machine (shared CI runner, coverage tracing, other processes) more
than the service. A warm /convert costs ~0.1-0.3s, almost all of it CPU-bound
transformer NER inference (Tier 2 entity extraction) plus local FHIR model
validation, so the old ">= 5 req/s" check sat right at the machine's limit and
failed ~1 in 3 runs.

So correctness assertions (success counts, status codes, memory growth) are
strict, while timing assertions are either:
- derived from the product SLA (<2s per /convert, SLA_RESPONSE_TIME_SECONDS)
  rather than from how fast a given machine happens to be, or
- relative to the same run's own baseline, using medians so one GC pause or
  scheduler hiccup cannot fail the test.
Each bound still catches real regressions: a hang, a per-request model reload
(seconds per call), or latency that grows with request count.
"""

import pytest
from fastapi.testclient import TestClient
import time
import concurrent.futures
from statistics import mean, median

from src.nl_fhir.api.middleware.timing import SLA_RESPONSE_TIME_SECONDS
from src.nl_fhir.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def warm_up_convert_pipeline():
    """Load the NLP models once before any timed request.

    Otherwise whichever test runs first pays the cold-start cost inside its
    timed requests (e.g. 5.4s average vs the 5.0s limit on a CI runner).
    """
    client.post(
        "/convert",
        json={"clinical_text": "metformin 500mg", "patient_ref": "Patient/warmup"},
    )


class TestConcurrentConversion:
    """Test concurrent /convert requests"""

    def test_10_concurrent_convert_requests(self):
        """Test handling 10 concurrent conversion requests"""

        def make_convert_request(request_id):
            payload = {
                "clinical_text": f"metformin 500mg for patient {request_id}",
                "patient_ref": f"Patient/concurrent-{request_id}"
            }
            start = time.time()
            response = client.post("/convert", json=payload)
            duration = time.time() - start
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration": duration,
                "response": response
            }

        # Execute 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_convert_request, i) for i in range(10)]
            results = [f.result() for f in futures]

        # Rate limiting is disabled for tests (conftest), so every request must succeed
        success_count = sum(1 for r in results if r["status_code"] == 200)
        assert success_count == 10, f"Only {success_count}/10 requests succeeded"

        # CPU-bound work is serialized by the GIL, so with 10 in flight each
        # request waits for the others: average latency ~5x a single request
        # (~1s locally). 5s leaves room for slow runners while still failing
        # on deadlock-like contention or per-request model loading.
        durations = [r["duration"] for r in results]
        avg_duration = mean(durations)
        assert avg_duration < 5.0, f"Average response time {avg_duration:.2f}s too slow"

    def test_20_concurrent_validation_requests(self):
        """Test handling 20 concurrent validation requests"""

        bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [{
                "resource": {
                    "resourceType": "Patient",
                    "id": "concurrent-validation",
                    "name": [{"family": "Test"}]
                },
                "request": {"method": "POST", "url": "Patient"}
            }]
        }

        def make_validation_request():
            start = time.time()
            response = client.post("/validate", json={"bundle": bundle})
            duration = time.time() - start
            return {
                "status_code": response.status_code,
                "duration": duration
            }

        # Execute 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_validation_request) for _ in range(20)]
            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r["status_code"] == 200)
        assert success_count == 20, f"Only {success_count}/20 validations succeeded"

    def test_concurrent_health_checks_no_interference(self):
        """Test that health checks don't interfere with main requests"""

        def make_convert_request():
            payload = {
                "clinical_text": "metformin 500mg",
                "patient_ref": "Patient/test"
            }
            return client.post("/convert", json=payload)

        def make_health_request():
            return client.get("/health")

        # Mix of 10 convert + 10 health check requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            convert_futures = [executor.submit(make_convert_request) for _ in range(10)]
            health_futures = [executor.submit(make_health_request) for _ in range(10)]

            convert_results = [f.result() for f in convert_futures]
            health_results = [f.result() for f in health_futures]

        # Both types should succeed
        assert all(r.status_code == 200 for r in convert_results)
        assert all(r.status_code == 200 for r in health_results)


class TestSustainedLoad:
    """Test sustained load handling"""

    def test_100_sequential_requests_no_memory_leak(self):
        """Test memory stability over 100 requests"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/load-test"
        }

        # Make 100 requests
        for i in range(100):
            response = client.post("/convert", json=payload)
            assert response.status_code == 200, f"Request {i} failed: {response.status_code}"
            if i % 20 == 0:  # Check every 20 requests
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = current_memory - initial_memory

                # Memory shouldn't grow unreasonably (allow 100MB growth)
                assert memory_growth < 100, f"Memory grew by {memory_growth}MB"

    def test_50_requests_response_time_stability(self):
        """Test that response times remain stable under moderate load"""

        def make_request():
            payload = {
                "clinical_text": "metformin 500mg",
                "patient_ref": "Patient/stability-test"
            }
            start = time.perf_counter()
            response = client.post("/convert", json=payload)
            duration = time.perf_counter() - start
            assert response.status_code == 200, f"Request failed: {response.status_code}"
            return duration

        # Execute 50 requests sequentially
        durations = [make_request() for _ in range(50)]

        # Compare medians of the first and last 15 requests: a mean of 10
        # ~0.15s samples doubles from a single GC pause or scheduler stall.
        median_first = median(durations[:15])
        median_last = median(durations[-15:])

        # Response time shouldn't degrade: allow up to 2x, plus 0.1s absolute
        # slack so millisecond-scale jitter on a fast baseline can't fail it.
        # Latency that grows with request count (leaky caches, unbounded lists)
        # still trips this.
        assert median_last < median_first * 2 + 0.1, \
            f"Response time degraded: median {median_first:.3f}s -> {median_last:.3f}s"


class TestRateLimiting:
    """Test rate limiting behavior"""

    def test_rapid_requests_within_rate_limit(self):
        """Test 100 requests per minute within rate limit"""
        start = time.time()

        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/rate-test"
        }

        # Send 50 requests as fast as possible
        responses = []
        for _ in range(50):
            response = client.post("/convert", json=payload)
            responses.append(response)

        duration = time.time() - start

        # Count successful responses
        success_count = sum(1 for r in responses if r.status_code == 200)

        # Most should succeed if under rate limit
        # Allow some failures for rate limiting
        assert success_count >= 40, f"Only {success_count}/50 succeeded"

        # 60s = 1.2s per request, inside the 2s SLA; ~8x local timing.
        assert duration < 60, f"50 requests took {duration:.1f}s"

    def test_excessive_requests_rate_limited(self):
        """Test that excessive requests are rate limited"""
        payload = {
            "clinical_text": "spam",
            "patient_ref": "Patient/spam"
        }

        # Try to send 200 requests rapidly
        responses = []
        for _ in range(200):
            response = client.post("/convert", json=payload)
            responses.append(response.status_code)
            if response.status_code == 429:  # Too Many Requests
                # Rate limiting is working
                return

        # If no 429 responses, either rate limiting not implemented
        # or limit is very high (both acceptable)
        pytest.skip("Rate limiting may not be implemented or has high threshold")


class TestConcurrentDifferentEndpoints:
    """Test concurrent requests across different endpoints"""

    def test_mixed_endpoint_concurrent_requests(self):
        """Test concurrent requests to different endpoints"""

        def convert_request():
            return client.post("/convert", json={
                "clinical_text": "metformin 500mg",
                "patient_ref": "Patient/mixed-test"
            })

        def validate_request():
            return client.post("/validate", json={
                "bundle": {
                    "resourceType": "Bundle",
                    "type": "transaction",
                    "entry": []
                }
            })

        def health_request():
            return client.get("/health")

        # Mix of different endpoints
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = []
            futures.extend([executor.submit(convert_request) for _ in range(10)])
            futures.extend([executor.submit(validate_request) for _ in range(10)])
            futures.extend([executor.submit(health_request) for _ in range(10)])

            results = [f.result() for f in futures]

        # All should succeed
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 25, f"Only {success_count}/30 requests succeeded"


class TestPerformanceRequirements:
    """Test production performance requirements"""

    def test_p95_response_time_under_load(self):
        """Test that 95th percentile response time is acceptable"""

        def make_request():
            payload = {
                "clinical_text": "metformin 500mg",
                "patient_ref": "Patient/p95-test"
            }
            start = time.time()
            response = client.post("/convert", json=payload)
            duration = time.time() - start
            return duration, response.status_code

        # Make 100 requests
        results = [make_request() for _ in range(100)]
        failed = [status for _, status in results if status != 200]
        assert not failed, f"{len(failed)}/100 requests failed: {sorted(set(failed))}"
        durations = [d for d, _ in results]

        # Calculate p95
        durations.sort()
        p95_index = int(len(durations) * 0.95)
        p95_time = durations[p95_index]

        # P95 under 3s: the 2s SLA plus headroom for a shared runner (~10x
        # local p95). A per-request model reload or network timeout fails it.
        assert p95_time < 3.0, f"P95 response time {p95_time:.2f}s exceeds 3s"

    def test_throughput_baseline(self):
        """Sequential throughput must meet the <2s-per-request SLA.

        This used to assert >= 5 req/s, i.e. < 0.2s per request. That measured
        the machine, not the service: a warm /convert takes 0.1-0.3s of CPU
        (mostly transformer NER inference), so it failed ~1 in 3 runs. The
        floor is now the product SLA (SLA_RESPONSE_TIME_SECONDS per request,
        i.e. >= 0.5 req/s): still a real gate, well clear of normal timing.
        """
        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/throughput-test"
        }

        start = time.perf_counter()
        responses = [client.post("/convert", json=payload) for _ in range(50)]
        duration = time.perf_counter() - start

        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count == 50, f"Only {success_count}/50 requests succeeded"

        throughput = success_count / duration
        min_throughput = 1.0 / SLA_RESPONSE_TIME_SECONDS
        assert throughput >= min_throughput, (
            f"Throughput {throughput:.2f} req/s below SLA floor {min_throughput:.2f} req/s "
            f"({duration / success_count:.2f}s per request)"
        )
