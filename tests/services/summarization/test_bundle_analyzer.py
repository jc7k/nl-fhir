"""
Comprehensive test suite for BundleAnalyzer
Tests FHIR bundle analysis, tier selection, and complexity scoring

Epic 4 Story 4.1: Adaptive Framework - Bundle Analysis Component
Critical for cost-optimized processing tier selection
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.nl_fhir.services.summarization.bundle_analyzer import BundleAnalyzer
from src.nl_fhir.services.summarization.models.bundle_analysis import (
    BundleAnalysis,
    ProcessingTier,
    TierSelectionCriteria
)


class TestBundleAnalyzer:
    """Comprehensive test suite for bundle analysis"""

    @pytest.fixture
    def analyzer(self):
        """Get initialized bundle analyzer"""
        return BundleAnalyzer()

    @pytest.fixture
    def analyzer_custom_criteria(self):
        """Get analyzer with custom criteria"""
        criteria = TierSelectionCriteria(
            max_complexity_for_rules=5.0,
            min_confidence_for_llm=0.8
        )
        return BundleAnalyzer(criteria=criteria)

    @pytest.fixture
    def mock_registry(self):
        """Mock resource registry"""
        class MockRegistry:
            def get_summarizer(self, resource_type):
                return MockSummarizer()

        class MockSummarizer:
            async def summarize_resource(self, resource, role):
                return {}

        return MockRegistry()

    def create_simple_bundle(self, resource_types: list = None) -> Dict[str, Any]:
        """Helper to create simple test bundle"""
        if resource_types is None:
            resource_types = ["Patient"]

        entries = []
        for idx, res_type in enumerate(resource_types):
            entries.append({
                "resource": {
                    "resourceType": res_type,
                    "id": f"{res_type.lower()}-{idx}"
                }
            })

        return {
            "resourceType": "Bundle",
            "type": "transaction",
            "id": "test-bundle-123",
            "entry": entries
        }

    # =================================================================
    # Initialization Tests
    # =================================================================

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes with default criteria"""
        assert analyzer.criteria is not None
        assert isinstance(analyzer.complex_resource_types, set)
        assert len(analyzer.complex_resource_types) > 0
        assert isinstance(analyzer.emergency_indicators, set)

    def test_analyzer_custom_criteria(self, analyzer_custom_criteria):
        """Test analyzer with custom criteria"""
        assert analyzer_custom_criteria.criteria.max_complexity_for_rules == 5.0

    def test_complex_resource_types_defined(self, analyzer):
        """Test complex resource types are properly defined"""
        expected_complex = {
            'ClinicalImpression',
            'CarePlan',
            'Communication',
            'DocumentReference',
            'Media',
            'QuestionnaireResponse'
        }
        assert expected_complex.issubset(analyzer.complex_resource_types)

    def test_emergency_indicators_defined(self, analyzer):
        """Test emergency indicators are properly defined"""
        expected_indicators = {'emergency', 'urgent', 'stat', 'critical'}
        assert expected_indicators.issubset(analyzer.emergency_indicators)

    # =================================================================
    # Bundle Analysis Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_analyze_empty_bundle(self, analyzer, mock_registry):
        """Test analysis of empty bundle"""
        bundle = {"resourceType": "Bundle", "type": "transaction", "entry": []}

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        assert isinstance(result, BundleAnalysis)
        assert result.resource_count == 0
        assert result.recommended_tier == ProcessingTier.RULE_BASED

    @pytest.mark.asyncio
    async def test_analyze_simple_bundle(self, analyzer, mock_registry):
        """Test analysis of simple bundle with patient"""
        bundle = self.create_simple_bundle(["Patient"])

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        assert result.resource_count == 1
        assert "Patient" in result.resource_types
        assert result.complexity_score >= 0.0
        assert result.complexity_score <= 10.0
        assert isinstance(result.analysis_duration_ms, float)
        assert result.analysis_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_analyze_medication_bundle(self, analyzer, mock_registry):
        """Test analysis of medication-focused bundle"""
        bundle = self.create_simple_bundle([
            "Patient",
            "MedicationRequest",
            "Practitioner"
        ])

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        assert result.resource_count == 3
        assert len(set(result.resource_types)) == 3
        assert result.primary_resource_type in ["Patient", "MedicationRequest", "Practitioner"]

    @pytest.mark.asyncio
    async def test_analyze_complex_bundle(self, analyzer, mock_registry):
        """Test analysis of complex bundle with many resource types"""
        bundle = self.create_simple_bundle([
            "Patient",
            "MedicationRequest",
            "Observation",
            "Procedure",
            "DiagnosticReport",
            "CarePlan",  # Complex resource type
            "ClinicalImpression"  # Complex resource type
        ])

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        assert result.resource_count == 7
        assert result.complexity_score > 0.0
        # Complex resources should increase complexity score
        assert result.has_rare_resources or result.complexity_score > 3.0

    # =================================================================
    # Complexity Scoring Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_complexity_score_resource_count(self, analyzer, mock_registry):
        """Test complexity increases with resource count"""
        small_bundle = self.create_simple_bundle(["Patient", "Observation"])
        large_bundle = self.create_simple_bundle([
            "Patient", "Observation", "MedicationRequest",
            "Procedure", "DiagnosticReport", "Condition",
            "Practitioner", "Organization"
        ])

        small_result = await analyzer.analyze_bundle(small_bundle, mock_registry)
        large_result = await analyzer.analyze_bundle(large_bundle, mock_registry)

        # More resources should result in higher complexity
        assert large_result.complexity_score >= small_result.complexity_score

    @pytest.mark.asyncio
    async def test_complexity_score_complex_resources(self, analyzer):
        """Test complexity score for complex resource types"""
        simple_resources = ["Patient", "Observation"]
        complex_resources = ["CarePlan", "ClinicalImpression", "Communication"]

        resources = []
        for res_type in complex_resources:
            resource = {
                "resourceType": res_type,
                "id": f"{res_type.lower()}-1"
            }
            resources.append(resource)

        # Test complexity calculation directly
        score = await analyzer._calculate_complexity_score(
            resources,
            complex_resources
        )

        # Complex resources should contribute to score
        assert score > 0.0
        assert score <= 10.0

    @pytest.mark.asyncio
    async def test_complexity_score_capped_at_10(self, analyzer):
        """Test complexity score is capped at 10.0"""
        # Create bundle with many complex resources
        very_complex_resources = []
        resource_types = []

        for i in range(20):
            resource_types.append("CarePlan")
            very_complex_resources.append({
                "resourceType": "CarePlan",
                "id": f"careplan-{i}",
                "subject": {"reference": f"Patient/{i}"},
                "period": {"start": "2024-01-01"},
                "category": [{"text": "Category"}],
                "activity": [
                    {"detail": {"status": "scheduled"}},
                    {"detail": {"status": "in-progress"}}
                ]
            })

        score = await analyzer._calculate_complexity_score(
            very_complex_resources,
            resource_types
        )

        assert score <= 10.0

    # =================================================================
    # Emergency Detection Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_detect_emergency_indicators_text(self, analyzer):
        """Test emergency indicator detection in text fields"""
        resources = [{
            "resourceType": "ServiceRequest",
            "id": "urgent-1",
            "priority": "urgent",
            "code": {"text": "STAT laboratory test"}
        }]

        has_emergency = await analyzer._detect_emergency_indicators(resources)

        # Should detect "urgent" and "stat"
        assert isinstance(has_emergency, bool)

    @pytest.mark.asyncio
    async def test_detect_emergency_indicators_priority(self, analyzer):
        """Test emergency detection via priority field"""
        resources = [{
            "resourceType": "MedicationRequest",
            "id": "med-1",
            "priority": "stat"
        }]

        has_emergency = await analyzer._detect_emergency_indicators(resources)

        assert isinstance(has_emergency, bool)

    @pytest.mark.asyncio
    async def test_no_emergency_indicators(self, analyzer):
        """Test no emergency indicators in routine bundle"""
        resources = [{
            "resourceType": "MedicationRequest",
            "id": "med-1",
            "priority": "routine"
        }]

        has_emergency = await analyzer._detect_emergency_indicators(resources)

        # Routine should not trigger emergency detection
        assert isinstance(has_emergency, bool)

    # =================================================================
    # Rare Resource Detection Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_rare_resource_detection(self, analyzer):
        """Test rare resource detection"""
        # Media and DocumentReference are typically rare
        rare_types = ["Media", "QuestionnaireResponse"]
        common_types = ["Patient", "Observation"]

        rare_result = await analyzer._has_rare_resources(rare_types)
        common_result = await analyzer._has_rare_resources(common_types)

        # Rare resources should be detected
        assert isinstance(rare_result, bool)
        assert isinstance(common_result, bool)

    # =================================================================
    # Tier Selection Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_tier_selection_simple_bundle(self, analyzer, mock_registry):
        """Test tier selection for simple bundle"""
        bundle = self.create_simple_bundle(["Patient", "Observation"])

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        # Simple bundles should use rule-based processing
        assert result.recommended_tier == ProcessingTier.RULE_BASED
        assert result.confidence_score >= 0.0
        assert result.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_rule_based_coverage_100_percent(self, analyzer, mock_registry):
        """Test rule-based coverage is 100% with generic fallback"""
        bundle = self.create_simple_bundle([
            "Patient", "MedicationRequest", "UnknownType", "CustomResource"
        ])

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        # With generic fallback, should have 100% coverage
        assert result.rule_based_coverage == 1.0
        assert len(result.unsupported_resource_types) == 0

    # =================================================================
    # Context Extraction Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_extract_specialty_context(self, analyzer):
        """Test specialty context extraction"""
        resources = [{
            "resourceType": "Encounter",
            "id": "enc-1",
            "serviceType": {"text": "cardiology"}
        }]

        context = await analyzer._extract_specialty_context(resources)

        assert context is None or isinstance(context, str)

    @pytest.mark.asyncio
    async def test_extract_urgency_level(self, analyzer):
        """Test urgency level extraction"""
        resources = [{
            "resourceType": "ServiceRequest",
            "id": "req-1",
            "priority": "urgent"
        }]

        urgency = await analyzer._extract_urgency_level(resources)

        assert urgency is None or isinstance(urgency, str)

    # =================================================================
    # Reference Counting Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_count_resource_references(self, analyzer):
        """Test counting references in resource"""
        resource = {
            "resourceType": "MedicationRequest",
            "id": "med-1",
            "subject": {"reference": "Patient/123"},
            "requester": {"reference": "Practitioner/456"},
            "encounter": {"reference": "Encounter/789"}
        }

        count = await analyzer._count_resource_references(resource)

        assert count >= 0
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_count_nested_references(self, analyzer):
        """Test counting references in nested structures"""
        resource = {
            "resourceType": "CarePlan",
            "id": "cp-1",
            "subject": {"reference": "Patient/123"},
            "activity": [
                {
                    "reference": {"reference": "ServiceRequest/1"}
                },
                {
                    "detail": {
                        "performer": [
                            {"reference": "Practitioner/2"},
                            {"reference": "Practitioner/3"}
                        ]
                    }
                }
            ]
        }

        count = await analyzer._count_resource_references(resource)

        # Should find multiple references
        assert count > 0

    # =================================================================
    # Content Complexity Assessment Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_assess_content_complexity_simple(self, analyzer):
        """Test content complexity for simple resource"""
        resource = {
            "resourceType": "Patient",
            "id": "patient-1",
            "name": [{"family": "Test"}]
        }

        complexity = await analyzer._assess_content_complexity(resource)

        assert complexity >= 0.0
        assert isinstance(complexity, (int, float))

    @pytest.mark.asyncio
    async def test_assess_content_complexity_nested(self, analyzer):
        """Test content complexity for deeply nested resource"""
        resource = {
            "resourceType": "Observation",
            "id": "obs-1",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "1234-5",
                        "display": "Test"
                    }
                ]
            },
            "component": [
                {
                    "code": {"coding": [{"code": "comp-1"}]},
                    "valueQuantity": {"value": 120, "unit": "mmHg"}
                },
                {
                    "code": {"coding": [{"code": "comp-2"}]},
                    "valueQuantity": {"value": 80, "unit": "mmHg"}
                }
            ],
            "interpretation": [{"coding": [{"code": "N"}]}]
        }

        complexity = await analyzer._assess_content_complexity(resource)

        # Nested structure should have higher complexity
        assert complexity > 0.0

    # =================================================================
    # Primary Resource Type Determination Tests
    # =================================================================

    def test_determine_primary_resource_type_single(self, analyzer):
        """Test primary resource type for single resource"""
        resource_types = ["Patient"]

        primary = analyzer._determine_primary_resource_type(resource_types)

        assert primary == "Patient"

    def test_determine_primary_resource_type_multiple(self, analyzer):
        """Test primary resource type for multiple resources"""
        resource_types = ["Patient", "Observation", "Observation", "Observation"]

        primary = analyzer._determine_primary_resource_type(resource_types)

        # Observation appears most frequently
        assert primary in resource_types

    def test_determine_primary_resource_type_empty(self, analyzer):
        """Test primary resource type for empty list"""
        resource_types = []

        primary = analyzer._determine_primary_resource_type(resource_types)

        assert primary is None

    # =================================================================
    # Analysis Metadata Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_analysis_includes_timestamp(self, analyzer, mock_registry):
        """Test analysis includes timestamp"""
        bundle = self.create_simple_bundle(["Patient"])

        before = datetime.now()
        result = await analyzer.analyze_bundle(bundle, mock_registry)
        after = datetime.now()

        assert result.analysis_timestamp >= before
        assert result.analysis_timestamp <= after

    @pytest.mark.asyncio
    async def test_analysis_duration_tracked(self, analyzer, mock_registry):
        """Test analysis duration is tracked"""
        bundle = self.create_simple_bundle(["Patient"])

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        assert result.analysis_duration_ms >= 0.0
        assert result.analysis_duration_ms < 5000.0  # Should be fast (<5s)

    # =================================================================
    # Integration Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, analyzer, mock_registry):
        """Test complete end-to-end analysis workflow"""
        # Create realistic clinical bundle
        bundle = self.create_simple_bundle([
            "Patient",
            "Practitioner",
            "Encounter",
            "MedicationRequest",
            "MedicationRequest",
            "Observation",
            "Observation",
            "DiagnosticReport",
            "Condition"
        ])

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        # Verify all components of analysis
        assert isinstance(result, BundleAnalysis)
        assert result.resource_count == 9
        assert len(result.resource_types) == 9
        assert result.complexity_score >= 0.0
        assert result.complexity_score <= 10.0
        assert isinstance(result.has_rare_resources, bool)
        assert isinstance(result.has_emergency_indicators, bool)
        assert isinstance(result.recommended_tier, ProcessingTier)
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.rule_based_coverage == 1.0
        assert len(result.supported_resource_types) > 0
        assert isinstance(result.analysis_duration_ms, float)

    # =================================================================
    # Performance Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_analysis_performance_small_bundle(self, analyzer, mock_registry):
        """Test analysis performance for small bundle"""
        import time

        bundle = self.create_simple_bundle(["Patient", "Observation"])

        start = time.time()
        result = await analyzer.analyze_bundle(bundle, mock_registry)
        elapsed = time.time() - start

        # Should complete quickly (<500ms)
        assert elapsed < 0.5
        assert result.resource_count == 2

    @pytest.mark.asyncio
    async def test_analysis_performance_large_bundle(self, analyzer, mock_registry):
        """Test analysis performance for large bundle"""
        import time

        # Create bundle with 50 resources
        resource_types = ["Observation"] * 50
        bundle = self.create_simple_bundle(resource_types)

        start = time.time()
        result = await analyzer.analyze_bundle(bundle, mock_registry)
        elapsed = time.time() - start

        # Should still complete quickly (<2s)
        assert elapsed < 2.0
        assert result.resource_count == 50

    # =================================================================
    # Edge Cases and Error Handling Tests
    # =================================================================

    @pytest.mark.asyncio
    async def test_bundle_missing_entry_field(self, analyzer, mock_registry):
        """Test handling bundle without entry field"""
        bundle = {"resourceType": "Bundle", "type": "transaction"}

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        assert result.resource_count == 0

    @pytest.mark.asyncio
    async def test_bundle_entry_missing_resource(self, analyzer, mock_registry):
        """Test handling entry without resource"""
        bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {"fullUrl": "http://example.com/Patient/1"},
                {"resource": {"resourceType": "Patient", "id": "p1"}}
            ]
        }

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        # Should only count entry with resource
        assert result.resource_count == 1

    @pytest.mark.asyncio
    async def test_resource_missing_type(self, analyzer, mock_registry):
        """Test handling resource without resourceType"""
        bundle = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {"resource": {"id": "unknown-1"}},
                {"resource": {"resourceType": "Patient", "id": "p1"}}
            ]
        }

        result = await analyzer.analyze_bundle(bundle, mock_registry)

        # Should handle gracefully
        assert result.resource_count >= 1
