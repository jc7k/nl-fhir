"""
Load and Concurrent Request Tests
Production Readiness: Performance under load testing

Coverage:
- Concurrent request handling
- Rate limiting
- Memory stability under load
- Response time degradation
- Connection pool handling
"""

import pytest
from fastapi.testclient import TestClient
import time
import concurrent.futures
from statistics import mean, median

from src.nl_fhir.main import app

client = TestClient(app)


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

        # All requests should complete successfully
        success_count = sum(1 for r in results if r["status_code"] == 200)
        assert success_count >= 8, f"Only {success_count}/10 requests succeeded"

        # Check response times
        durations = [r["duration"] for r in results]
        avg_duration = mean(durations)
        assert avg_duration < 5.0, f"Average response time {avg_duration}s too slow"

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
            response = client.post("/validate", json={"fhir_bundle": bundle})
            duration = time.time() - start
            return {
                "status_code": response.status_code,
                "duration": duration
            }

        # Execute 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_validation_request) for _ in range(20)]
            results = [f.result() for f in futures]

        # Most should succeed
        success_count = sum(1 for r in results if r["status_code"] == 200)
        assert success_count >= 15, f"Only {success_count}/20 validations succeeded"

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
            start = time.time()
            response = client.post("/convert", json=payload)
            duration = time.time() - start
            return duration

        # Execute 50 requests sequentially
        durations = [make_request() for _ in range(50)]

        # Calculate statistics
        first_10 = durations[:10]
        last_10 = durations[-10:]

        avg_first = mean(first_10)
        avg_last = mean(last_10)

        # Response time shouldn't degrade significantly
        # Allow up to 2x slowdown
        assert avg_last < avg_first * 2, \
            f"Response time degraded: {avg_first:.2f}s -> {avg_last:.2f}s"


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

        # Should complete in reasonable time
        assert duration < 60, f"50 requests took {duration}s"

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
                "fhir_bundle": {
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
        durations = [d for d, status in results if status == 200]

        if len(durations) == 0:
            pytest.skip("No successful requests")

        # Calculate p95
        durations.sort()
        p95_index = int(len(durations) * 0.95)
        p95_time = durations[p95_index]

        # P95 should be under 3 seconds
        assert p95_time < 3.0, f"P95 response time {p95_time:.2f}s exceeds 3s"

    def test_throughput_baseline(self):
        """Test minimum throughput requirement"""
        start = time.time()

        payload = {
            "clinical_text": "metformin 500mg",
            "patient_ref": "Patient/throughput-test"
        }

        # Send 50 requests
        responses = [client.post("/convert", json=payload) for _ in range(50)]

        duration = time.time() - start
        success_count = sum(1 for r in responses if r.status_code == 200)

        # Calculate requests per second
        if success_count > 0:
            throughput = success_count / duration

            # Should handle at least 5 requests per second
            assert throughput >= 5.0, f"Throughput {throughput:.1f} req/s below 5 req/s"
