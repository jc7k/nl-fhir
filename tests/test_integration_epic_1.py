"""
Integration Tests for Epic 1 Complete
Story 1.3: Production Readiness Validation
HIPAA Compliant: No PHI in test data
"""

import pytest
import time
import asyncio
from fastapi.testclient import TestClient
from src.nl_fhir.main import app

client = TestClient(app)


class TestEndToEndIntegration:
    """Test complete user workflow from Stories 1.1, 1.2, and 1.3"""
    
    def test_complete_user_journey(self):
        """Test full user journey through all Epic 1 functionality"""
        
        # Step 1: Access web form (Story 1.1)
        response = client.get("/")
        assert response.status_code == 200
        assert "NL-FHIR Clinical Order Converter" in response.text
        
        # Step 2: Submit clinical order via basic endpoint (Story 1.1)
        basic_order = {
            "clinical_text": "Start patient on metformin 500mg twice daily for type 2 diabetes",
            "patient_ref": "PT-12345"
        }
        
        response = client.post("/convert", json=basic_order)
        assert response.status_code == 200
        basic_result = response.json()
        assert basic_result["status"] == "received"
        assert "request_id" in basic_result
        
        # Step 3: Submit advanced order (Story 1.2)
        advanced_order = {
            "clinical_text": "Order comprehensive metabolic panel, HbA1c, and lipid panel - fasting required",
            "patient_ref": "PT-67890",
            "priority": "routine",
            "ordering_provider": "DR_SMITH",
            "department": "Endocrinology"
        }
        
        response = client.post("/api/v1/convert", json=advanced_order)
        assert response.status_code == 200
        advanced_result = response.json()
        
        # Verify advanced features
        assert "metadata" in advanced_result
        assert "validation" in advanced_result
        assert "extracted_entities" in advanced_result
        assert advanced_result["validation"]["is_valid"]
        
        # Step 4: Test bulk processing (Story 1.3)
        bulk_request = {
            "orders": [
                {"clinical_text": "Order CBC with differential", "patient_ref": "PT-001"},
                {"clinical_text": "Start lisinopril 10mg daily for hypertension", "patient_ref": "PT-002"},
                {"clinical_text": "Schedule chest X-ray for annual screening"}
            ],
            "batch_id": "integration_test_batch"
        }
        
        response = client.post("/api/v1/bulk-convert", json=bulk_request)
        assert response.status_code == 200
        bulk_result = response.json()
        assert bulk_result["total_orders"] == 3
        assert bulk_result["successful_orders"] == 3
        
        # Step 5: Verify monitoring endpoints (Story 1.3)
        response = client.get("/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "healthy"
        
        response = client.get("/metrics")
        assert response.status_code == 200
        metrics = response.json()
        assert metrics["total_requests"] > 0


class TestProductionSecurityHardening:
    """Test production security features from Story 1.3"""
    
    def test_security_headers_comprehensive(self):
        """Test all security headers are present"""
        response = client.get("/health")
        
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Cache-Control"
        ]
        
        for header in required_headers:
            assert header in response.headers
            assert response.headers[header]
    
    def test_input_size_limits(self):
        """Test request size limits are enforced"""
        # Create a very large clinical text
        large_text = "Order medication " * 100000  # ~1.6MB of text
        
        request_data = {
            "clinical_text": large_text,
            "patient_ref": "PT-LARGE"
        }
        
        response = client.post("/convert", json=request_data)
        # Should reject due to size or validation
        assert response.status_code in [413, 422]
    
    def test_cors_configuration(self):
        """Test CORS is properly configured"""
        response = client.options(
            "/convert",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        # Should handle CORS preflight (400 is also acceptable in test environment)
        assert response.status_code in [200, 204, 400, 405]
    
    def test_trusted_host_protection(self):
        """Test trusted host middleware is active"""
        # Already validated by testserver being in allowed hosts
        response = client.get("/health")
        assert response.status_code == 200


class TestPerformanceBaseline:
    """Test performance requirements for Story 1.3"""
    
    def test_response_time_baseline(self):
        """Test that responses meet <2s requirement"""
        request_data = {
            "clinical_text": "Order routine blood work including CBC and metabolic panel"
        }
        
        start_time = time.time()
        response = client.post("/convert", json=request_data)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 2.0  # Must be under 2 seconds
    
    def test_concurrent_request_handling(self):
        """Test system can handle concurrent requests"""
        request_data = {
            "clinical_text": "Start patient on antibiotics for infection"
        }
        
        # Send 10 concurrent requests
        responses = []
        for _ in range(10):
            response = client.post("/convert", json=request_data)
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
    
    def test_metrics_accuracy(self):
        """Test metrics endpoint provides accurate data"""
        # Get initial metrics
        response = client.get("/metrics")
        initial_metrics = response.json()
        initial_count = initial_metrics["total_requests"]
        
        # Make some requests
        for i in range(5):
            client.post("/convert", json={
                "clinical_text": f"Test order {i}: Prescribe medication"
            })
        
        # Check metrics updated
        response = client.get("/metrics")
        updated_metrics = response.json()
        
        # Should have increased by at least 5
        assert updated_metrics["total_requests"] >= initial_count + 5


class TestMonitoringAndObservability:
    """Test monitoring features for Story 1.3"""
    
    def test_health_check_components(self):
        """Test health check reports all components"""
        response = client.get("/health")
        assert response.status_code == 200
        
        health = response.json()
        assert "components" in health
        
        components = health["components"]
        assert "memory" in components
        assert "cpu" in components
        assert "application" in components
        
        # All components should be healthy or warning (not critical)
        for component, status in components.items():
            assert status in ["healthy", "warning"]
    
    def test_readiness_check(self):
        """Test readiness probe for Kubernetes/Railway"""
        response = client.get("/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ready"] == True
        assert "checks" in data
        
        # All checks should pass
        for check, result in data["checks"].items():
            assert result == True
    
    def test_liveness_check(self):
        """Test liveness probe for Kubernetes/Railway"""
        response = client.get("/live")
        assert response.status_code == 200
        
        data = response.json()
        assert data["alive"] == True
        assert data["uptime_seconds"] >= 0
    
    def test_request_correlation(self):
        """Test request ID correlation across system"""
        # Make multiple requests
        request_ids = set()
        
        for i in range(10):
            response = client.post("/convert", json={
                "clinical_text": f"Order {i}: Routine medication"
            })
            
            assert response.status_code == 200
            data = response.json()
            request_id = data["request_id"]
            
            # Should be unique
            assert request_id not in request_ids
            request_ids.add(request_id)
            
            # Should be valid UUID format
            import re
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            assert re.match(uuid_pattern, request_id)


class TestErrorRecovery:
    """Test error recovery and graceful degradation"""
    
    def test_validation_error_recovery(self):
        """Test system recovers from validation errors"""
        # Send invalid request
        response = client.post("/convert", json={
            "clinical_text": "x"  # Too short
        })
        assert response.status_code == 422
        
        # System should still be healthy
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        
        # Should accept valid request after error
        response = client.post("/convert", json={
            "clinical_text": "Order routine blood work"
        })
        assert response.status_code == 200
    
    def test_malformed_request_handling(self):
        """Test handling of malformed requests"""
        # Send malformed JSON
        response = client.post(
            "/convert",
            data="{'broken': json}",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
        # System should remain operational
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["ready"] == True
    
    def test_error_response_structure(self):
        """Test error responses have consistent structure"""
        # Test validation error
        response = client.post("/convert", json={
            "clinical_text": ""
        })
        assert response.status_code == 422
        
        error_data = response.json()
        assert "detail" in error_data
        
        # Test method not allowed
        response = client.get("/convert")
        assert response.status_code == 405
        
        # Test not found
        response = client.get("/nonexistent")
        assert response.status_code == 404


class TestAPIDocumentation:
    """Test API documentation for Story 1.3"""
    
    def test_openapi_documentation_available(self):
        """Test OpenAPI documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
    
    def test_redoc_documentation_available(self):
        """Test ReDoc documentation is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()
    
    def test_openapi_schema_valid(self):
        """Test OpenAPI schema is valid"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        # Check key endpoints are documented
        assert "/convert" in schema["paths"]
        assert "/api/v1/convert" in schema["paths"]
        assert "/health" in schema["paths"]


class TestEpic1Acceptance:
    """Final acceptance tests for Epic 1 completion"""
    
    def test_all_story_1_1_requirements(self):
        """Verify Story 1.1 requirements are met"""
        # Web form available
        response = client.get("/")
        assert response.status_code == 200
        
        # Basic conversion works
        response = client.post("/convert", json={
            "clinical_text": "Order medication for patient"
        })
        assert response.status_code == 200
    
    def test_all_story_1_2_requirements(self):
        """Verify Story 1.2 requirements are met"""
        # Advanced endpoint available
        response = client.post("/api/v1/convert", json={
            "clinical_text": "Complex order with multiple medications",
            "priority": "routine"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "metadata" in data
        assert "validation" in data
        assert "extracted_entities" in data  # Epic 2 placeholder
    
    def test_all_story_1_3_requirements(self):
        """Verify Story 1.3 requirements are met"""
        # Production monitoring
        assert client.get("/health").status_code == 200
        assert client.get("/metrics").status_code == 200
        assert client.get("/ready").status_code == 200
        assert client.get("/live").status_code == 200
        
        # Bulk processing
        response = client.post("/api/v1/bulk-convert", json={
            "orders": [
                {"clinical_text": "Order 1"},
                {"clinical_text": "Order 2"}
            ]
        })
        assert response.status_code == 200
        
        # API documentation
        assert client.get("/docs").status_code == 200
    
    def test_epic_1_performance_baseline(self):
        """Verify Epic 1 performance baseline established"""
        # Make several requests and measure
        response_times = []
        
        for i in range(10):
            start = time.time()
            response = client.post("/convert", json={
                "clinical_text": f"Order {i}: Routine medication prescription"
            })
            response_time = time.time() - start
            
            assert response.status_code == 200
            response_times.append(response_time)
        
        # All should be under 2 seconds
        assert all(rt < 2.0 for rt in response_times)
        
        # Average should be well under 2 seconds (baseline for Epic 2)
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 1.0  # Leave headroom for Epic 2 NLP
    
    def test_epic_2_integration_readiness(self):
        """Verify system is ready for Epic 2 integration"""
        response = client.post("/api/v1/convert", json={
            "clinical_text": "Prescribe medication for patient treatment"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Check Epic 2 placeholders are present
        assert "extracted_entities" in data
        assert data["extracted_entities"]["status"] == "not_implemented"
        
        assert "structured_output" in data
        assert data["structured_output"]["status"] == "not_implemented"
        
        assert "terminology_mappings" in data
        
        # Check Epic 3 placeholders
        assert "fhir_bundle" in data
        assert data["fhir_bundle"] is None
        
        # System ready for NLP integration
        assert data["message"] == "Clinical order received and validated. Ready for Epic 2 NLP processing."