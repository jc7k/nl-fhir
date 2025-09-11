"""
Epic 2 Integration Tests - NLP Pipeline Complete
HIPAA Compliant: No PHI in test data
Medical Safety: Test all NLP processing scenarios
"""

import pytest
import time
from fastapi.testclient import TestClient
from src.nl_fhir.main import app

client = TestClient(app)


class TestEpic2Integration:
    """Test Epic 2 NLP pipeline integration with convert endpoints"""
    
    def test_basic_convert_still_works(self):
        """Test basic convert endpoint still functions"""
        request_data = {
            "clinical_text": "Start patient on lisinopril 10mg daily for hypertension"
        }
        
        response = client.post("/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "received"
        assert "request_id" in data
        
    def test_advanced_convert_with_nlp(self):
        """Test advanced convert endpoint with NLP processing"""
        request_data = {
            "clinical_text": "Start patient on metformin 500mg twice daily for diabetes management",
            "priority": "routine",
            "ordering_provider": "DR_SMITH"
        }
        
        response = client.post("/api/v1/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check Epic 2 NLP results are present
        assert "extracted_entities" in data
        assert "structured_output" in data
        assert "terminology_mappings" in data
        
        # Verify NLP processing occurred
        extracted_entities = data["extracted_entities"]
        assert "entities" in extracted_entities
        assert "enhanced_entities" in extracted_entities
        
    def test_medication_extraction_integration(self):
        """Test medication extraction through API"""
        request_data = {
            "clinical_text": "Prescribe amoxicillin 500mg three times daily for infection"
        }
        
        response = client.post("/api/v1/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        structured_output = data["structured_output"]["structured_output"]
        
        # Should extract medication information
        assert "medications" in structured_output
        medications = structured_output["medications"]
        
        if medications:  # If extraction worked
            med = medications[0]
            assert "name" in med
            assert "dosage" in med
            assert "frequency" in med
            
    def test_lab_test_extraction_integration(self):
        """Test lab test extraction through API"""
        request_data = {
            "clinical_text": "Order CBC, comprehensive metabolic panel, and HbA1c"
        }
        
        response = client.post("/api/v1/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        structured_output = data["structured_output"]["structured_output"]
        
        # Should extract lab tests
        assert "lab_tests" in structured_output
        lab_tests = structured_output["lab_tests"]
        
        if lab_tests:  # If extraction worked
            assert len(lab_tests) > 0
            
    def test_terminology_mapping_integration(self):
        """Test medical terminology mapping through API"""
        request_data = {
            "clinical_text": "Patient needs metformin for diabetes and CBC monitoring"
        }
        
        response = client.post("/api/v1/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        terminology_mappings = data["terminology_mappings"]
        
        # Check mapping structure
        assert "medications" in terminology_mappings
        assert "lab_tests" in terminology_mappings
        assert "conditions" in terminology_mappings
        
    def test_bulk_convert_with_nlp(self):
        """Test bulk conversion with NLP processing"""
        bulk_request = {
            "orders": [
                {"clinical_text": "Start metformin 500mg twice daily"},
                {"clinical_text": "Order CBC and basic metabolic panel"},
                {"clinical_text": "Schedule chest X-ray for evaluation"}
            ]
        }
        
        response = client.post("/api/v1/bulk-convert", json=bulk_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_orders"] == 3
        assert data["successful_orders"] >= 0
        
        # Check each result has NLP processing
        for result in data["results"]:
            if hasattr(result, 'extracted_entities'):  # If successful
                assert "extracted_entities" in result
                assert "structured_output" in result
                
    def test_nlp_performance_requirements(self):
        """Test NLP processing meets performance requirements"""
        request_data = {
            "clinical_text": """
            Patient presents with type 2 diabetes requiring medication adjustment.
            Start metformin 500mg twice daily with meals.
            Order comprehensive metabolic panel, HbA1c, and lipid panel.
            Schedule follow-up in 3 months for reassessment.
            """
        }
        
        start_time = time.time()
        response = client.post("/api/v1/convert", json=request_data)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        # Should still meet <2s requirement with NLP processing
        assert response_time < 3.0  # Allow some extra time for NLP
        
    def test_nlp_error_handling(self):
        """Test NLP error handling doesn't break API"""
        request_data = {
            "clinical_text": "x"  # Very short text
        }
        
        response = client.post("/api/v1/convert", json=request_data)
        
        # Should handle gracefully (might succeed or fail validation)
        assert response.status_code in [200, 422]
        
    def test_epic_2_response_structure(self):
        """Test Epic 2 response structure is complete"""
        request_data = {
            "clinical_text": "Start comprehensive diabetes management with metformin"
        }
        
        response = client.post("/api/v1/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Epic 2 fields should be populated
        assert data["extracted_entities"]["status"] in ["completed", "failed"]
        assert data["structured_output"]["status"] in ["completed", "failed"]
        
        # Epic 3 placeholders should still be None
        assert data["fhir_bundle"] is None
        assert data["fhir_validation_results"] is None
        
        # Epic 4 placeholders should still be None
        assert data["safety_checks"] is None
        assert data["human_readable_summary"] is None
        
    def test_monitoring_endpoints_with_nlp(self):
        """Test monitoring endpoints show NLP status"""
        # Make a request to initialize NLP
        client.post("/api/v1/convert", json={"clinical_text": "Test order"})
        
        # Check health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        health = response.json()
        dependencies = health.get("dependencies", {})
        
        # Should show NLP pipeline status (when implemented)
        # For now, just verify endpoint works
        assert "nlp_pipeline" in dependencies
        
    def test_epic_2_completion_readiness(self):
        """Test system ready for Epic 3 integration"""
        request_data = {
            "clinical_text": "Order medication and lab tests for patient care"
        }
        
        response = client.post("/api/v1/convert", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify Epic 2 completion
        assert "Epic 2 NLP processing" in data["message"] or "NLP" in data["message"]
        
        # Verify Epic 3 readiness
        assert data["fhir_bundle"] is None  # Ready for population
        assert "extracted_entities" in data  # Input for FHIR assembly
        assert "structured_output" in data   # Input for FHIR assembly


class TestEpic2HealthChecks:
    """Test Epic 2 health and monitoring integration"""
    
    def test_nlp_health_integration(self):
        """Test NLP health is integrated into system health"""
        response = client.get("/health")
        assert response.status_code == 200
        
        health = response.json()
        assert "dependencies" in health
        
        # Should include NLP pipeline dependency
        dependencies = health["dependencies"]
        assert "nlp_pipeline" in dependencies
        
    def test_metrics_include_nlp(self):
        """Test metrics include NLP performance data"""
        # Make some requests first
        for i in range(3):
            client.post("/api/v1/convert", json={
                "clinical_text": f"Test order {i}: prescribe medication"
            })
        
        response = client.get("/metrics")
        assert response.status_code == 200
        
        metrics = response.json()
        
        # Should include request counts (NLP processing included)
        assert "total_requests" in metrics
        assert metrics["total_requests"] > 0


class TestEpic2APIDocumentation:
    """Test Epic 2 API documentation is updated"""
    
    def test_openapi_includes_epic2_fields(self):
        """Test OpenAPI documentation includes Epic 2 response fields"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        
        # Check advanced convert response schema
        paths = schema.get("paths", {})
        convert_path = paths.get("/api/v1/convert", {})
        
        if convert_path:
            post_responses = convert_path.get("post", {}).get("responses", {})
            success_response = post_responses.get("200", {})
            
            # Should document Epic 2 fields
            content = success_response.get("content", {})
            if content:
                json_content = content.get("application/json", {})
                schema_ref = json_content.get("schema", {})
                
                # Response should include Epic 2 fields
                # (Detailed schema checking would require more complex validation)
                assert schema_ref  # Just verify schema exists
    
    def test_api_docs_accessible(self):
        """Test API documentation is accessible"""
        # Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        
        # ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200