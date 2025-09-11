"""
Story 3.4: Epic 3 Production Readiness Tests
Comprehensive testing of production-ready FHIR pipeline
HIPAA Compliant: No PHI in test data
"""

import pytest
import asyncio
import time
import json
from datetime import datetime
from typing import Dict, Any

# Import Story 3.4 services
from src.nl_fhir.services.fhir.unified_pipeline import get_unified_fhir_pipeline, FHIRProcessingResult
from src.nl_fhir.services.fhir.quality_optimizer import get_quality_optimizer
from src.nl_fhir.services.fhir.performance_manager import get_performance_manager


class TestUnifiedFHIRPipeline:
    """Test unified FHIR pipeline for production readiness"""
    
    @pytest.fixture
    def sample_nlp_entities(self):
        """Sample NLP entities for pipeline testing"""
        return {
            "patient_info": {
                "age": "52",
                "gender": "female",
                "patient_ref": "patient-prod-test"
            },
            "medications": [
                {
                    "name": "Metformin",
                    "dosage": "500mg",
                    "frequency": "twice daily",
                    "rxnorm_code": "860975"
                },
                {
                    "name": "Lisinopril",
                    "dosage": "10mg",
                    "frequency": "once daily",
                    "rxnorm_code": "617296"
                }
            ],
            "conditions": [
                {
                    "name": "Type 2 Diabetes",
                    "icd10_code": "E11.9",
                    "status": "active"
                },
                {
                    "name": "Hypertension",
                    "icd10_code": "I10",
                    "status": "active"
                }
            ],
            "procedures": [
                {
                    "name": "HbA1c test",
                    "loinc_code": "4548-4",
                    "frequency": "quarterly"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_unified_pipeline_initialization(self):
        """Test unified pipeline initialization"""
        pipeline = await get_unified_fhir_pipeline()
        
        assert pipeline.initialized == True
        assert pipeline.resource_factory is not None
        assert pipeline.bundle_assembler is not None
        assert pipeline.validation_service is not None
        assert pipeline.execution_service is not None
        assert pipeline.failover_manager is not None
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_processing(self, sample_nlp_entities):
        """Test complete end-to-end pipeline processing"""
        pipeline = await get_unified_fhir_pipeline()
        
        # Process through complete pipeline
        result = await pipeline.process_nlp_to_fhir(
            nlp_entities=sample_nlp_entities,
            validate_bundle=True,
            execute_bundle=False  # Don't execute in tests
        )
        
        # Verify result structure
        assert isinstance(result, FHIRProcessingResult)
        assert result.request_id is not None
        assert result.success == True
        assert len(result.fhir_resources) >= 4  # Patient + 2 medications + 2 conditions
        assert result.fhir_bundle is not None
        assert result.validation_results is not None
        assert result.quality_metrics is not None
        assert result.bundle_summary_data is not None
        
        # Verify Epic 4 preparation data
        summary_data = result.bundle_summary_data
        assert "patient_summary" in summary_data
        assert "medications" in summary_data
        assert "conditions" in summary_data
        assert "bundle_metadata" in summary_data
        assert "quality_indicators" in summary_data
        
        # Verify performance tracking
        metadata = result.processing_metadata
        assert "resource_creation" in metadata.processing_steps
        assert "bundle_assembly" in metadata.processing_steps
        assert "bundle_validation" in metadata.processing_steps
        assert metadata.performance_metrics["total_processing_time"] < 2.0  # <2s requirement
    
    @pytest.mark.asyncio
    async def test_pipeline_performance_requirements(self, sample_nlp_entities):
        """Test pipeline meets <2s performance requirement"""
        pipeline = await get_unified_fhir_pipeline()
        
        # Test multiple runs for consistent performance
        processing_times = []
        
        for i in range(5):
            start_time = time.time()
            
            result = await pipeline.process_nlp_to_fhir(
                nlp_entities=sample_nlp_entities,
                request_id=f"perf-test-{i}",
                validate_bundle=True,
                execute_bundle=False
            )
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            # Each individual request should be under 2s
            assert processing_time < 2.0, f"Processing time {processing_time:.3f}s exceeds 2s requirement"
            assert result.success == True
        
        # Average should also be well under 2s
        avg_time = sum(processing_times) / len(processing_times)
        assert avg_time < 1.5, f"Average processing time {avg_time:.3f}s is too close to 2s limit"
    
    @pytest.mark.asyncio
    async def test_pipeline_status_and_metrics(self):
        """Test pipeline status and metrics collection"""
        pipeline = await get_unified_fhir_pipeline()
        
        # Get pipeline status
        status = pipeline.get_pipeline_status()
        
        # Verify status structure
        assert "pipeline_initialized" in status
        assert "service_status" in status
        assert "processing_statistics" in status
        assert "quality_metrics" in status
        assert "error_tracking" in status
        
        # Verify service status
        service_status = status["service_status"]
        assert service_status["resource_factory"] == True
        assert service_status["bundle_assembler"] == True
        assert service_status["validation_service"] == True
        assert service_status["execution_service"] == True
        assert service_status["failover_manager"] == True
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self):
        """Test pipeline error handling and resilience"""
        pipeline = await get_unified_fhir_pipeline()
        
        # Test with invalid NLP entities
        invalid_entities = {
            "invalid_structure": "this should fail gracefully"
        }
        
        result = await pipeline.process_nlp_to_fhir(
            nlp_entities=invalid_entities,
            request_id="error-test"
        )
        
        # Should handle errors gracefully
        assert result.success == False or len(result.errors) > 0
        assert result.request_id == "error-test"
        assert result.processing_metadata is not None


class TestFHIRQualityOptimizer:
    """Test FHIR quality optimizer for ≥95% validation success"""
    
    @pytest.fixture
    def sample_bundle(self):
        """Sample FHIR bundle for optimization testing"""
        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-test",
                        "active": True
                    },
                    "request": {
                        "method": "POST",
                        "url": "Patient"
                    }
                },
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "med-req-test",
                        "status": "active",
                        "intent": "order",
                        "subject": {"reference": "Patient/patient-test"}
                    },
                    "request": {
                        "method": "POST",
                        "url": "MedicationRequest"
                    }
                }
            ]
        }
    
    def test_quality_optimizer_initialization(self):
        """Test quality optimizer initialization"""
        optimizer = get_quality_optimizer()
        
        assert optimizer is not None
        assert optimizer.quality_rules is not None
        assert "patient_requirements" in optimizer.quality_rules
        assert "medication_request_requirements" in optimizer.quality_rules
        assert "bundle_requirements" in optimizer.quality_rules
    
    def test_bundle_optimization(self, sample_bundle):
        """Test bundle optimization for better validation success"""
        optimizer = get_quality_optimizer()
        
        # Optimize bundle
        optimized_bundle = optimizer.optimize_bundle_for_validation(sample_bundle, "test-optimization")
        
        # Verify optimization occurred
        assert optimized_bundle["resourceType"] == "Bundle"
        assert optimized_bundle["type"] == "transaction"
        assert "id" in optimized_bundle  # Should add missing ID
        assert "timestamp" in optimized_bundle  # Should add missing timestamp
        assert "meta" in optimized_bundle  # Should add meta information
        
        # Check optimization metadata
        assert "meta" in optimized_bundle
        optimization_meta = optimized_bundle["meta"].get("optimization", {})
        assert "optimized_at" in optimization_meta
        assert "optimization_count" in optimization_meta
    
    def test_validation_success_tracking(self, sample_bundle):
        """Test validation success rate tracking"""
        optimizer = get_quality_optimizer()
        
        # Simulate validation results
        validation_result = {
            "is_valid": True,
            "bundle_quality_score": 0.95,
            "issues": {"errors": [], "warnings": []},
            "validation_result": "success"
        }
        
        # Analyze validation result
        analysis = optimizer.analyze_validation_result(validation_result, sample_bundle, "success-test")
        
        # Verify analysis structure
        assert "quality_score" in analysis
        assert "validation_success" in analysis
        assert "identified_issues" in analysis
        assert "improvement_suggestions" in analysis
        assert "resource_quality" in analysis
        assert "bundle_quality" in analysis
        assert analysis["quality_score"] == 0.95
        assert analysis["validation_success"] == True
    
    def test_quality_trends_analysis(self):
        """Test quality trends and analytics"""
        optimizer = get_quality_optimizer()
        
        # Get quality trends (may be empty initially)
        trends = optimizer.get_quality_trends()
        
        # Verify trends structure
        if "message" not in trends:  # If we have data
            assert "validation_history_count" in trends
            assert "current_success_rate" in trends
            assert "target_met" in trends
            assert "improvement_opportunity" in trends
        else:
            # Should handle empty state gracefully
            assert trends["message"] == "No validation history available"
    
    def test_error_pattern_analysis(self, sample_bundle):
        """Test error pattern identification and learning"""
        optimizer = get_quality_optimizer()
        
        # Simulate validation with errors
        error_validation_result = {
            "is_valid": False,
            "bundle_quality_score": 0.6,
            "issues": {
                "errors": [
                    "Field required: medication",
                    "Unable to resolve reference 'Patient/invalid-id'",
                    "Invalid code value in system"
                ],
                "warnings": ["Recommendation: add dosage information"]
            },
            "validation_result": "error"
        }
        
        # Analyze errors
        analysis = optimizer.analyze_validation_result(error_validation_result, sample_bundle, "error-test")
        
        # Verify error categorization
        issues = analysis["identified_issues"]
        assert "missing_required_fields" in issues
        assert "reference_errors" in issues
        assert "code_system_issues" in issues
        
        # Verify improvement suggestions
        suggestions = analysis["improvement_suggestions"]
        assert len(suggestions) > 0
        assert any("required field" in suggestion for suggestion in suggestions)


class TestFHIRPerformanceManager:
    """Test FHIR performance manager for production optimization"""
    
    def test_performance_manager_initialization(self):
        """Test performance manager initialization"""
        manager = get_performance_manager()
        
        assert manager is not None
        assert manager.cache_size > 0
        assert manager.performance_targets is not None
        assert "validation_time_ms" in manager.performance_targets
        assert "total_pipeline_ms" in manager.performance_targets
        assert manager.performance_targets["total_pipeline_ms"] == 2000  # 2s requirement
    
    def test_performance_tracking(self):
        """Test performance tracking and metrics collection"""
        manager = get_performance_manager()
        
        # Start tracking an operation
        tracking_id = manager.start_performance_tracking("test_operation", resource_count=3)
        
        assert tracking_id is not None
        assert "test_operation" in tracking_id
        
        # Simulate some work
        time.sleep(0.01)  # 10ms
        
        # End tracking
        metrics = manager.end_performance_tracking(tracking_id, success=True, cache_hit=False)
        
        assert metrics is not None
        assert metrics.operation_type == "test_operation"
        assert metrics.resource_count == 3
        assert metrics.duration_ms >= 10  # At least 10ms
        assert metrics.success == True
        assert metrics.cache_hit == False
    
    def test_caching_functionality(self):
        """Test validation result caching"""
        manager = get_performance_manager()
        
        # Test bundle hash generation
        test_bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "test"}}
            ]
        }
        
        bundle_hash = manager.generate_bundle_hash(test_bundle)
        assert bundle_hash is not None
        assert len(bundle_hash) > 0
        
        # Test caching
        validation_result = {
            "is_valid": True,
            "bundle_quality_score": 0.9,
            "validation_result": "success"
        }
        
        # Cache the result
        manager.cache_validation_result(bundle_hash, validation_result)
        
        # Retrieve from cache
        cached_result = manager.get_cached_validation_result(bundle_hash)
        assert cached_result is not None
        assert cached_result["is_valid"] == True
        assert cached_result["bundle_quality_score"] == 0.9
    
    def test_performance_summary(self):
        """Test performance summary generation"""
        manager = get_performance_manager()
        
        # Generate some metrics
        for i in range(3):
            tracking_id = manager.start_performance_tracking(f"test_op_{i}", resource_count=i+1)
            time.sleep(0.001)  # 1ms
            manager.end_performance_tracking(tracking_id, success=True)
        
        # Get performance summary
        summary = manager.get_performance_summary()
        
        # Verify summary structure
        assert "overall_statistics" in summary
        assert "operation_breakdown" in summary
        assert "cache_performance" in summary
        assert "performance_targets" in summary
        
        # Verify statistics
        overall_stats = summary["overall_statistics"]
        assert "total_operations" in overall_stats
        assert "success_rate" in overall_stats
        assert "average_duration_ms" in overall_stats
        assert overall_stats["total_operations"] >= 3
    
    def test_real_time_metrics(self):
        """Test real-time performance metrics"""
        manager = get_performance_manager()
        
        # Generate some recent activity
        tracking_id = manager.start_performance_tracking("real_time_test")
        time.sleep(0.001)
        manager.end_performance_tracking(tracking_id, success=True)
        
        # Get real-time metrics
        metrics = manager.get_real_time_metrics()
        
        # May be empty if no recent activity, but structure should be correct
        if "message" not in metrics:
            assert "time_window" in metrics
            assert "total_operations" in metrics
            assert "success_rate" in metrics
            assert "average_duration_ms" in metrics
            assert "performance_target_met" in metrics
    
    def test_cache_clearing(self):
        """Test cache clearing functionality"""
        manager = get_performance_manager()
        
        # Add some cached data
        manager.cache_validation_result("test_hash_1", {"result": "test1"})
        manager.cache_fhir_resource("test_resource_1", {"resource": "test1"})
        
        # Clear caches
        cleared_counts = manager.clear_caches()
        
        # Verify clearing results
        assert "validation_entries_cleared" in cleared_counts
        assert "resource_entries_cleared" in cleared_counts
        assert cleared_counts["validation_entries_cleared"] >= 0
        assert cleared_counts["resource_entries_cleared"] >= 0
        
        # Verify caches are actually cleared
        assert manager.get_cached_validation_result("test_hash_1") is None
        assert manager.get_cached_fhir_resource("test_resource_1") is None


class TestEpic3ProductionReadiness:
    """Test Epic 3 production readiness and Epic 4 preparation"""
    
    @pytest.fixture
    def production_nlp_entities(self):
        """Production-level NLP entities for comprehensive testing"""
        return {
            "patient_info": {
                "age": "67",
                "gender": "male",
                "patient_ref": "patient-prod-comprehensive"
            },
            "medications": [
                {
                    "name": "Atorvastatin",
                    "dosage": "20mg",
                    "frequency": "once daily",
                    "rxnorm_code": "617312"
                },
                {
                    "name": "Metoprolol",
                    "dosage": "50mg",
                    "frequency": "twice daily",
                    "rxnorm_code": "866924"
                },
                {
                    "name": "Aspirin",
                    "dosage": "81mg",
                    "frequency": "once daily",
                    "rxnorm_code": "1191"
                }
            ],
            "conditions": [
                {
                    "name": "Coronary Artery Disease",
                    "icd10_code": "I25.10",
                    "status": "active"
                },
                {
                    "name": "Hyperlipidemia",
                    "icd10_code": "E78.5",
                    "status": "active"
                }
            ],
            "procedures": [
                {
                    "name": "Lipid Panel",
                    "loinc_code": "57698-3",
                    "frequency": "annually"
                },
                {
                    "name": "ECG",
                    "loinc_code": "11524-6",
                    "frequency": "as needed"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_production_validation_success_rate(self, production_nlp_entities):
        """Test that pipeline achieves ≥95% validation success rate"""
        pipeline = await get_unified_fhir_pipeline()
        quality_optimizer = get_quality_optimizer()
        
        # Process multiple requests to build success rate
        successful_validations = 0
        total_validations = 10
        
        for i in range(total_validations):
            result = await pipeline.process_nlp_to_fhir(
                nlp_entities=production_nlp_entities,
                request_id=f"validation-success-test-{i}",
                validate_bundle=True,
                execute_bundle=False
            )
            
            # Check if validation was successful
            if (result.validation_results and 
                result.validation_results.get("is_valid", False)):
                successful_validations += 1
        
        # Calculate success rate
        success_rate = (successful_validations / total_validations) * 100
        
        # Should achieve ≥95% success rate
        assert success_rate >= 95.0, f"Validation success rate {success_rate:.1f}% below 95% target"
        
        # Verify quality optimizer tracking
        optimizer_success_rate = quality_optimizer.get_validation_success_rate()
        assert optimizer_success_rate >= 0.0  # Should be tracking
    
    @pytest.mark.asyncio
    async def test_epic4_integration_preparation(self, production_nlp_entities):
        """Test Epic 4 integration data preparation"""
        pipeline = await get_unified_fhir_pipeline()
        
        # Process with full Epic 4 preparation
        result = await pipeline.process_nlp_to_fhir(
            nlp_entities=production_nlp_entities,
            validate_bundle=True,
            execute_bundle=False
        )
        
        # Verify Epic 4 preparation data
        summary_data = result.bundle_summary_data
        
        # Check patient summary
        patient_summary = summary_data["patient_summary"]
        assert patient_summary["age"] == "67"
        assert patient_summary["gender"] == "male"
        assert patient_summary["patient_reference"] == "patient-prod-comprehensive"
        
        # Check clinical orders
        assert len(summary_data["medications"]) == 3
        assert len(summary_data["conditions"]) == 2
        assert len(summary_data["procedures"]) == 2
        
        # Check bundle metadata
        bundle_metadata = summary_data["bundle_metadata"]
        assert bundle_metadata["bundle_type"] == "transaction"
        assert bundle_metadata["entry_count"] >= 6  # Patient + 3 meds + 2 conditions
        
        # Check quality indicators for summary confidence
        quality_indicators = summary_data["quality_indicators"]
        assert "validation_result" in quality_indicators
        assert "bundle_quality_score" in quality_indicators
        assert "validation_source" in quality_indicators
        assert quality_indicators["bundle_quality_score"] >= 0.7  # Good quality for summarization
    
    @pytest.mark.asyncio
    async def test_production_performance_under_load(self, production_nlp_entities):
        """Test production performance under concurrent load"""
        pipeline = await get_unified_fhir_pipeline()
        
        # Simulate concurrent requests
        concurrent_requests = 5
        
        async def process_request(request_id: int):
            start_time = time.time()
            result = await pipeline.process_nlp_to_fhir(
                nlp_entities=production_nlp_entities,
                request_id=f"load-test-{request_id}",
                validate_bundle=True,
                execute_bundle=False
            )
            processing_time = time.time() - start_time
            return processing_time, result.success
        
        # Execute concurrent requests
        tasks = [process_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        # Verify all requests completed successfully within time limits
        for processing_time, success in results:
            assert processing_time < 2.0, f"Request took {processing_time:.3f}s, exceeds 2s limit"
            assert success == True, "Request failed under load"
        
        # Verify average performance
        avg_time = sum(result[0] for result in results) / len(results)
        assert avg_time < 1.5, f"Average time {avg_time:.3f}s too close to 2s limit under load"
    
    @pytest.mark.asyncio
    async def test_epic3_completion_criteria(self):
        """Test all Epic 3 completion criteria are met"""
        
        # Test 1: Complete FHIR Pipeline Integration
        pipeline = await get_unified_fhir_pipeline()
        pipeline_status = pipeline.get_pipeline_status()
        assert pipeline_status["pipeline_initialized"] == True
        
        # Test 2: Quality Optimizer for ≥95% Success
        quality_optimizer = get_quality_optimizer()
        assert quality_optimizer is not None
        
        # Test 3: Performance Manager for <2s Response Time
        performance_manager = get_performance_manager()
        assert performance_manager.performance_targets["total_pipeline_ms"] == 2000
        
        # Test 4: Production Monitoring
        performance_summary = performance_manager.get_performance_summary()
        assert "overall_statistics" in performance_summary
        assert "cache_performance" in performance_summary
        
        # Test 5: Epic 4 Integration Readiness
        # Should have all required components for reverse validation
        sample_entities = {
            "patient_info": {"age": "45", "gender": "female", "patient_ref": "test"},
            "medications": [{"name": "Test Med", "dosage": "10mg", "frequency": "daily"}]
        }
        
        result = await pipeline.process_nlp_to_fhir(
            nlp_entities=sample_entities,
            validate_bundle=True,
            execute_bundle=False
        )
        
        # Verify Epic 4 readiness
        assert result.bundle_summary_data is not None
        assert "patient_summary" in result.bundle_summary_data
        assert "quality_indicators" in result.bundle_summary_data
        assert result.quality_metrics is not None
        
        logger.info("✅ All Epic 3 completion criteria verified!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])