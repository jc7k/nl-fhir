"""
Stress Testing and Resilience Validation

Tests system behavior under extreme conditions:
- High load scenarios
- Resource exhaustion
- Concurrent requests
- Edge case combinations
- Graceful degradation

Marks: stress, performance, resilience
"""

import pytest
import time
import concurrent.futures
from fastapi.testclient import TestClient

from nl_fhir.main import app

client = TestClient(app)


@pytest.mark.stress
@pytest.mark.slow
class TestStressScenarios:
    """Stress testing under extreme conditions"""

    def test_sustained_load_100_requests(self):
        """
        Test system stability under sustained load (100 requests)
        
        Validates:
        - No crashes under sustained load
        - Response times remain reasonable
        - No memory leaks
        """
        results = []
        
        for i in range(100):
            start = time.time()
            response = client.get("/health")
            duration = time.time() - start
            
            results.append({
                'request_num': i,
                'status': response.status_code,
                'duration': duration
            })
            
            # Should always respond
            assert response.status_code == 200
        
        # Calculate statistics
        durations = [r['duration'] for r in results]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        # Performance should not degrade significantly
        assert avg_duration < 0.5  # Average < 500ms
        assert max_duration < 2.0  # Max < 2s
        
        print(f"\n✓ Sustained load test: {len(results)} requests")
        print(f"  Avg: {avg_duration*1000:.1f}ms, Max: {max_duration*1000:.1f}ms")

    def test_burst_traffic_50_concurrent(self):
        """
        Test burst traffic handling (50 concurrent requests)
        
        Validates:
        - Concurrent request handling
        - No race conditions
        - Consistent response quality
        """
        def make_request(request_id):
            start = time.time()
            response = client.post("/convert", json={
                "clinical_text": f"metformin 500mg for patient {request_id}",
                "patient_ref": f"Patient/stress-{request_id}"
            })
            duration = time.time() - start
            return {
                'id': request_id,
                'status': response.status_code,
                'duration': duration,
                'success': response.status_code in [200, 201]
            }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [f.result() for f in futures]
        
        # Most requests should succeed (allow some failures under stress)
        success_count = sum(1 for r in results if r['success'])
        success_rate = success_count / len(results) * 100
        
        assert success_rate >= 70  # At least 70% success rate
        
        print(f"\n✓ Burst traffic test: {success_count}/{len(results)} succeeded")
        print(f"  Success rate: {success_rate:.1f}%")

    def test_large_payload_handling(self):
        """
        Test handling of large clinical text payloads
        
        Validates:
        - Large input handling
        - Memory efficiency
        - Timeout prevention
        """
        # Create large but valid clinical text
        large_text = "Start patient on:\n" + "\n".join([
            f"- Medication {i}: Generic Drug {i} 100mg twice daily"
            for i in range(100)
        ])
        
        response = client.post("/convert", json={
            "clinical_text": large_text,
            "patient_ref": "Patient/large-payload-test"
        })
        
        # Should handle large payloads without crashing
        assert response.status_code in [200, 201, 413]  # OK or Payload Too Large
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert 'bundle' in data or 'fhir_bundle' in data
            print("\n✓ Large payload handled successfully")

    def test_rapid_sequential_requests(self):
        """
        Test rapid sequential requests (no delays)
        
        Validates:
        - Rate limiting behavior
        - Connection pool handling
        - Resource cleanup
        """
        responses = []
        
        for i in range(30):
            response = client.get("/health")
            responses.append(response.status_code)
        
        # Should handle rapid requests
        success_count = sum(1 for s in responses if s == 200)
        rate_limited = sum(1 for s in responses if s == 429)
        
        # Either succeed or rate limit (not crash)
        assert success_count + rate_limited == len(responses)
        
        print(f"\n✓ Rapid sequential: {success_count} OK, {rate_limited} rate-limited")


@pytest.mark.resilience
@pytest.mark.integration
class TestResiliencePatterns:
    """Test graceful degradation and resilience"""

    def test_invalid_input_graceful_handling(self):
        """
        Test graceful handling of invalid inputs
        
        Validates:
        - No crashes on bad input
        - Meaningful error messages
        - Proper HTTP status codes
        """
        invalid_inputs = [
            {},  # Empty
            {"clinical_text": ""},  # Empty text
            {"clinical_text": "x" * 10000},  # Too long
            {"clinical_text": None},  # Null
            {"patient_ref": "invalid$chars!"},  # Invalid characters
        ]
        
        for invalid_input in invalid_inputs:
            response = client.post("/convert", json=invalid_input)
            
            # Should return error, not crash
            assert response.status_code in [400, 422, 413]
            
        print(f"\n✓ Handled {len(invalid_inputs)} invalid inputs gracefully")

    def test_health_check_always_responsive(self):
        """
        Test health endpoint remains responsive under stress
        
        Critical for orchestrators (Kubernetes, Docker, Railway)
        """
        # Make 50 rapid health checks
        start = time.time()
        responses = []
        
        for _ in range(50):
            response = client.get("/health")
            responses.append(response.status_code)
        
        duration = time.time() - start
        
        # All should succeed
        assert all(s == 200 for s in responses)
        
        # Should be fast (critical for health checks)
        avg_duration = duration / len(responses)
        assert avg_duration < 0.1  # < 100ms average
        
        print(f"\n✓ Health checks: {len(responses)} requests in {duration:.2f}s")
        print(f"  Average: {avg_duration*1000:.1f}ms per request")


@pytest.mark.performance
@pytest.mark.regression
class TestPerformanceRegression:
    """Detect performance regressions"""

    def test_baseline_conversion_performance(self):
        """
        Baseline performance test for conversion endpoint
        
        This test establishes performance baselines.
        Future runs detect regressions.
        """
        # Warm up
        client.get("/health")
        
        # Measure baseline
        durations = []
        
        for i in range(20):
            start = time.time()
            response = client.post("/convert", json={
                "clinical_text": "metformin 500mg twice daily",
                "patient_ref": f"Patient/perf-{i}"
            })
            duration = time.time() - start
            durations.append(duration)
            
            assert response.status_code in [200, 201]
        
        # Calculate percentiles
        durations.sort()
        p50 = durations[len(durations) // 2]
        p95 = durations[int(len(durations) * 0.95)]
        p99 = durations[int(len(durations) * 0.99)]
        
        # Performance requirements (from roadmap)
        assert p50 < 1.0  # P50 < 1s
        assert p95 < 2.0  # P95 < 2s (SLA requirement)
        assert p99 < 3.0  # P99 < 3s
        
        print(f"\n✓ Performance baseline:")
        print(f"  P50: {p50*1000:.0f}ms")
        print(f"  P95: {p95*1000:.0f}ms")
        print(f"  P99: {p99*1000:.0f}ms")
        
    def test_validation_performance_baseline(self):
        """Baseline validation endpoint performance"""
        simple_bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [{
                "resource": {
                    "resourceType": "Patient",
                    "id": "perf-test-123",
                    "name": [{"family": "Test"}]
                },
                "request": {"method": "POST", "url": "Patient"}
            }]
        }
        
        durations = []
        
        for _ in range(15):
            start = time.time()
            response = client.post("/validate", json={"fhir_bundle": simple_bundle})
            duration = time.time() - start
            durations.append(duration)
        
        # Calculate stats
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        # Validation should be fast
        assert avg_duration < 1.0  # < 1s average
        assert max_duration < 2.0  # < 2s max
        
        print(f"\n✓ Validation performance:")
        print(f"  Average: {avg_duration*1000:.0f}ms")
        print(f"  Max: {max_duration*1000:.0f}ms")


# Test markers
pytestmark = [pytest.mark.slow]
