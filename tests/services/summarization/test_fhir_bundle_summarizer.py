"""
Epic 4 Story 4.1: Comprehensive Tests for FHIR Bundle Summarizer
Tests the main orchestrator for adaptive FHIR bundle summarization

Coverage:
- Bundle summarization end-to-end workflow
- Tier-based routing and processing
- Rule-based processing with 100% coverage
- Bundle summary composition
- Patient demographics extraction
- Clinical order categorization
- Quality indicators calculation
- Error handling and fallback summaries
- Monitoring and event logging
- Performance validation
"""

import pytest
import time
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.nl_fhir.services.summarization.fhir_bundle_summarizer import FHIRBundleSummarizer
from src.nl_fhir.services.summarization.models import (
    ClinicalSummary,
    BundleAnalysis,
    ProcessingTier,
    SummarizationEvent,
    QualityIndicators,
    ClinicalOrder,
    ResourceClassification
)


class TestFHIRBundleSummarizerInitialization:
    """Test summarizer initialization and setup"""

    def test_summarizer_initialization(self):
        """Test summarizer initializes with required components"""
        summarizer = FHIRBundleSummarizer()

        assert summarizer.resource_registry is not None
        assert summarizer.bundle_analyzer is not None
        assert summarizer.monitoring is not None
        assert summarizer._generic_engine is None  # Lazy-loaded
        assert summarizer._llm_service is None  # Lazy-loaded

    def test_summarizer_lazy_loading(self):
        """Test lazy-loaded components start as None"""
        summarizer = FHIRBundleSummarizer()

        # Lazy-loaded tier processors should be None initially
        assert summarizer._generic_engine is None
        assert summarizer._llm_service is None


class TestBundleSummarizationWorkflow:
    """Test end-to-end bundle summarization workflow"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    @pytest.fixture
    def mock_bundle_analysis(self):
        """Create mock bundle analysis result"""
        return BundleAnalysis(
            resource_count=3,
            resource_types=["Patient", "MedicationRequest", "Observation"],
            complexity_score=4.5,
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.95,
            specialty_context="General Medicine",
            resource_classifications=[
                ResourceClassification(
                    resource_type="Patient",
                    count=1,
                    has_rule_based_summarizer=True,
                    complexity_contribution=1.0
                ),
                ResourceClassification(
                    resource_type="MedicationRequest",
                    count=1,
                    has_rule_based_summarizer=True,
                    complexity_contribution=2.5
                ),
                ResourceClassification(
                    resource_type="Observation",
                    count=1,
                    has_rule_based_summarizer=True,
                    complexity_contribution=1.0
                )
            ]
        )

    def create_test_bundle(self, resource_types: List[str]) -> Dict[str, Any]:
        """Helper to create test FHIR bundle"""
        entries = []

        for i, resource_type in enumerate(resource_types):
            entry = {
                "fullUrl": f"http://example.com/{resource_type}/{i+1}",
                "resource": {
                    "resourceType": resource_type,
                    "id": f"{resource_type.lower()}-{i+1}"
                }
            }

            # Add type-specific fields
            if resource_type == "Patient":
                entry["resource"]["gender"] = "male"
                entry["resource"]["birthDate"] = "1980-01-01"
            elif resource_type == "MedicationRequest":
                entry["resource"]["medicationCodeableConcept"] = {
                    "coding": [{
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "197361",
                        "display": "Lisinopril 10 MG Oral Tablet"
                    }]
                }
            elif resource_type == "Observation":
                entry["resource"]["code"] = {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "8480-6",
                        "display": "Systolic blood pressure"
                    }]
                }

            entries.append(entry)

        return {
            "resourceType": "Bundle",
            "id": "test-bundle-1",
            "type": "transaction",
            "entry": entries
        }

    @pytest.mark.asyncio
    async def test_summarize_simple_bundle(self, summarizer, mock_bundle_analysis):
        """Test summarization of simple bundle"""
        bundle = self.create_test_bundle(["Patient", "MedicationRequest"])

        with patch.object(summarizer, '_analyze_bundle_composition',
                         new_callable=AsyncMock, return_value=mock_bundle_analysis):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock):
                summary = await summarizer.summarize_bundle(bundle, role="physician")

        assert isinstance(summary, ClinicalSummary)
        assert summary.processing_tier == ProcessingTier.RULE_BASED
        assert summary.confidence_score > 0.0
        assert len(summary.primary_orders) > 0

    @pytest.mark.asyncio
    async def test_summarize_bundle_with_request_id(self, summarizer, mock_bundle_analysis):
        """Test summarization with explicit request ID"""
        bundle = self.create_test_bundle(["Patient"])
        request_id = "custom-request-123"

        with patch.object(summarizer, '_analyze_bundle_composition',
                         new_callable=AsyncMock, return_value=mock_bundle_analysis):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock) as mock_log:
                summary = await summarizer.summarize_bundle(
                    bundle,
                    role="nurse",
                    request_id=request_id
                )

        # Verify request ID was used in monitoring
        mock_log.assert_called_once()
        event = mock_log.call_args[0][0]
        assert event.request_id == request_id

    @pytest.mark.asyncio
    async def test_summarize_bundle_with_context(self, summarizer, mock_bundle_analysis):
        """Test summarization with additional context"""
        bundle = self.create_test_bundle(["Patient", "Observation"])
        context = {"department": "ER", "priority": "high"}

        with patch.object(summarizer, '_analyze_bundle_composition',
                         new_callable=AsyncMock, return_value=mock_bundle_analysis):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock):
                summary = await summarizer.summarize_bundle(
                    bundle,
                    role="physician",
                    context=context
                )

        assert isinstance(summary, ClinicalSummary)

    @pytest.mark.asyncio
    async def test_summarize_empty_bundle(self, summarizer):
        """Test summarization of empty bundle"""
        bundle = {
            "resourceType": "Bundle",
            "id": "empty-bundle",
            "type": "transaction",
            "entry": []
        }

        # Mock empty bundle analysis
        empty_analysis = BundleAnalysis(
            resource_count=0,
            resource_types=[],
            complexity_score=0.0,
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.5,
            resource_classifications=[]
        )

        with patch.object(summarizer, '_analyze_bundle_composition',
                         new_callable=AsyncMock, return_value=empty_analysis):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock):
                summary = await summarizer.summarize_bundle(bundle)

        assert summary.summary_type == "minimal"
        assert len(summary.primary_orders) == 0

    @pytest.mark.asyncio
    async def test_summarize_complex_bundle(self, summarizer):
        """Test summarization of complex bundle with many resources"""
        resource_types = [
            "Patient", "MedicationRequest", "MedicationRequest", "MedicationRequest",
            "Observation", "Observation", "Procedure", "Condition", "DiagnosticReport"
        ]
        bundle = self.create_test_bundle(resource_types)

        complex_analysis = BundleAnalysis(
            resource_count=9,
            resource_types=list(set(resource_types)),
            complexity_score=10.0,  # High complexity
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.90,
            specialty_context="Internal Medicine",
            resource_classifications=[
                ResourceClassification(
                    resource_type=rt,
                    count=resource_types.count(rt),
                    has_rule_based_summarizer=True,
                    complexity_contribution=2.0
                ) for rt in set(resource_types)
            ]
        )

        with patch.object(summarizer, '_analyze_bundle_composition',
                         new_callable=AsyncMock, return_value=complex_analysis):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock):
                summary = await summarizer.summarize_bundle(bundle)

        assert summary.summary_type == "complex"
        assert len(summary.primary_orders) > 0


class TestRuleBasedProcessing:
    """Test rule-based processing tier"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    @pytest.fixture
    def mock_analysis(self):
        """Create mock analysis"""
        return BundleAnalysis(
            resource_count=2,
            resource_types=["Patient", "MedicationRequest"],
            complexity_score=3.5,
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.95,
            resource_classifications=[]
        )

    @pytest.mark.asyncio
    async def test_process_with_rule_based_success(self, summarizer, mock_analysis):
        """Test successful rule-based processing"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient-1",
                        "gender": "male",
                        "birthDate": "1970-01-01"
                    }
                }
            ]
        }

        # Mock the summarizer to return a valid ClinicalOrder
        mock_order = ClinicalOrder(
            order_type="Patient",
            description="Patient demographic information",
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.95
        )

        with patch.object(summarizer.resource_registry, 'get_summarizer') as mock_get:
            mock_summarizer = AsyncMock()
            mock_summarizer.summarize_resource.return_value = mock_order
            mock_get.return_value = mock_summarizer

            summary = await summarizer._process_with_rule_based(bundle, "physician", mock_analysis)

        assert summary.processing_tier == ProcessingTier.RULE_BASED
        assert len(summary.primary_orders) == 1
        assert summary.confidence_score > 0.0

    @pytest.mark.asyncio
    async def test_process_with_rule_based_error_handling(self, summarizer, mock_analysis):
        """Test rule-based processing with error handling"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "MedicationRequest",
                        "id": "med-1"
                    }
                }
            ]
        }

        # Mock summarizer that raises an exception
        with patch.object(summarizer.resource_registry, 'get_summarizer') as mock_get:
            mock_summarizer = AsyncMock()
            mock_summarizer.summarize_resource.side_effect = Exception("Processing error")
            mock_get.return_value = mock_summarizer

            summary = await summarizer._process_with_rule_based(bundle, "physician", mock_analysis)

        # Should still return a summary with fallback order
        assert len(summary.primary_orders) == 1
        assert summary.primary_orders[0].confidence_score == 0.3
        assert "processing error" in summary.primary_orders[0].description.lower()

    @pytest.mark.asyncio
    async def test_process_multiple_resources_with_mixed_success(self, summarizer, mock_analysis):
        """Test processing multiple resources with some failures"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "p1"}},
                {"resource": {"resourceType": "MedicationRequest", "id": "m1"}},
                {"resource": {"resourceType": "Observation", "id": "o1"}}
            ]
        }

        # Mock registry to return different behaviors
        success_order = ClinicalOrder(
            order_type="Patient",
            description="Success",
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.95
        )

        def mock_get_summarizer(resource_type):
            mock_sum = AsyncMock()
            if resource_type == "MedicationRequest":
                mock_sum.summarize_resource.side_effect = Exception("Error")
            else:
                mock_sum.summarize_resource.return_value = success_order
            return mock_sum

        with patch.object(summarizer.resource_registry, 'get_summarizer',
                         side_effect=mock_get_summarizer):
            summary = await summarizer._process_with_rule_based(bundle, "physician", mock_analysis)

        assert len(summary.primary_orders) == 3
        # One should be fallback order with low confidence
        low_confidence_orders = [o for o in summary.primary_orders if o.confidence_score < 0.5]
        assert len(low_confidence_orders) == 1


class TestBundleSummaryComposition:
    """Test bundle-level summary composition"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    def create_clinical_orders(self, order_types: List[str]) -> List[ClinicalOrder]:
        """Helper to create clinical orders"""
        orders = []
        for order_type in order_types:
            orders.append(ClinicalOrder(
                order_type=order_type,
                description=f"Test {order_type} order",
                processing_tier=ProcessingTier.RULE_BASED,
                confidence_score=0.9
            ))
        return orders

    def test_comprehensive_bundle_summary_medications(self, summarizer):
        """Test bundle summary with medications"""
        orders = self.create_clinical_orders(["MedicationRequest", "MedicationRequest"])
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {"resourceType": "Patient", "gender": "female", "birthDate": "1990-01-01"}},
                {"resource": {"resourceType": "MedicationRequest"}},
                {"resource": {"resourceType": "MedicationRequest"}}
            ]
        }

        result = summarizer._create_comprehensive_bundle_summary(orders, bundle, "physician")

        assert "2 medications prescribed" in result["patient_context"]
        assert "adult, female" in result["patient_context"]

    def test_comprehensive_bundle_summary_diagnostics(self, summarizer):
        """Test bundle summary with diagnostic tests"""
        orders = self.create_clinical_orders(["Observation", "DiagnosticReport"])
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {"resourceType": "Observation"}},
                {"resource": {"resourceType": "DiagnosticReport"}}
            ]
        }

        result = summarizer._create_comprehensive_bundle_summary(orders, bundle, "nurse")

        assert "2 diagnostic tests ordered" in result["patient_context"]

    def test_comprehensive_bundle_summary_procedures(self, summarizer):
        """Test bundle summary with procedures"""
        orders = self.create_clinical_orders(["Procedure"])
        bundle = {"resourceType": "Bundle", "entry": []}

        result = summarizer._create_comprehensive_bundle_summary(orders, bundle, "physician")

        assert "1 procedure scheduled" in result["patient_context"]

    def test_comprehensive_bundle_summary_conditions(self, summarizer):
        """Test bundle summary with conditions"""
        orders = self.create_clinical_orders(["Condition", "Condition", "Condition"])
        bundle = {"resourceType": "Bundle", "entry": []}

        result = summarizer._create_comprehensive_bundle_summary(orders, bundle, "physician")

        assert "3 conditions documented" in result["patient_context"]

    def test_comprehensive_bundle_summary_mixed(self, summarizer):
        """Test bundle summary with mixed order types"""
        orders = self.create_clinical_orders([
            "MedicationRequest", "MedicationRequest",
            "Observation",
            "Procedure",
            "Condition"
        ])
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {"resourceType": "Patient", "gender": "male", "birthDate": "1950-01-01"}}
            ]
        }

        result = summarizer._create_comprehensive_bundle_summary(orders, bundle, "physician")

        context = result["patient_context"]
        assert "2 medications prescribed" in context
        assert "1 diagnostic test ordered" in context
        assert "1 procedure scheduled" in context
        assert "1 condition documented" in context

    def test_comprehensive_bundle_summary_safety_alerts(self, summarizer):
        """Test bundle summary with safety alerts"""
        orders = [
            ClinicalOrder(
                order_type="MedicationRequest",
                description="High-risk medication",
                processing_tier=ProcessingTier.RULE_BASED,
                confidence_score=0.9,
                safety_alerts=["Drug interaction warning"]
            ),
            ClinicalOrder(
                order_type="MedicationRequest",
                description="Normal medication",
                processing_tier=ProcessingTier.RULE_BASED,
                confidence_score=0.95
            )
        ]
        bundle = {"resourceType": "Bundle", "entry": []}

        result = summarizer._create_comprehensive_bundle_summary(orders, bundle, "physician")

        assert len(result["clinical_alerts"]) > 0
        assert any("Safety review required" in alert for alert in result["clinical_alerts"])

    def test_comprehensive_bundle_summary_low_confidence(self, summarizer):
        """Test bundle summary with low confidence orders"""
        orders = [
            ClinicalOrder(
                order_type="Observation",
                description="Low confidence observation",
                processing_tier=ProcessingTier.RULE_BASED,
                confidence_score=0.5  # Low confidence
            )
        ]
        bundle = {"resourceType": "Bundle", "entry": []}

        result = summarizer._create_comprehensive_bundle_summary(orders, bundle, "physician")

        assert any("Manual review recommended" in alert for alert in result["clinical_alerts"])

    def test_comprehensive_bundle_summary_composition_details(self, summarizer):
        """Test bundle summary composition details"""
        orders = self.create_clinical_orders(["MedicationRequest", "Observation", "Procedure"])
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {"resourceType": "Patient", "gender": "female"}}
            ]
        }

        result = summarizer._create_comprehensive_bundle_summary(orders, bundle, "pharmacist")

        composition = result["composition_details"]
        assert composition["total_orders"] == 3
        assert composition["patient_info_available"] == True
        assert composition["role_based_context"] == "pharmacist"
        assert "medication" in composition["order_categories"]


class TestClinicalOrderCategorization:
    """Test clinical order categorization"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    def test_categorize_medication_orders(self, summarizer):
        """Test categorization of medication-related orders"""
        assert summarizer._categorize_clinical_order("MedicationRequest") == "medication"
        assert summarizer._categorize_clinical_order("medication") == "medication"
        assert summarizer._categorize_clinical_order("drug_prescription") == "medication"
        assert summarizer._categorize_clinical_order("prescription") == "medication"

    def test_categorize_diagnostic_orders(self, summarizer):
        """Test categorization of diagnostic orders"""
        assert summarizer._categorize_clinical_order("Observation") == "diagnostic"
        assert summarizer._categorize_clinical_order("DiagnosticReport") == "diagnostic"
        assert summarizer._categorize_clinical_order("lab_test") == "diagnostic"
        assert summarizer._categorize_clinical_order("diagnostic") == "diagnostic"

    def test_categorize_procedure_orders(self, summarizer):
        """Test categorization of procedure orders"""
        assert summarizer._categorize_clinical_order("Procedure") == "procedure"
        assert summarizer._categorize_clinical_order("surgery") == "procedure"
        assert summarizer._categorize_clinical_order("operation") == "procedure"

    def test_categorize_condition_orders(self, summarizer):
        """Test categorization of condition orders"""
        assert summarizer._categorize_clinical_order("Condition") == "condition"
        assert summarizer._categorize_clinical_order("diagnosis") == "condition"
        assert summarizer._categorize_clinical_order("problem") == "condition"

    def test_categorize_other_orders(self, summarizer):
        """Test categorization of other order types"""
        assert summarizer._categorize_clinical_order("AllergyIntolerance") == "other"
        assert summarizer._categorize_clinical_order("Immunization") == "other"
        assert summarizer._categorize_clinical_order("unknown_type") == "other"

    def test_categorize_case_insensitive(self, summarizer):
        """Test categorization is case-insensitive"""
        assert summarizer._categorize_clinical_order("MEDICATIONREQUEST") == "medication"
        assert summarizer._categorize_clinical_order("observation") == "diagnostic"
        assert summarizer._categorize_clinical_order("Procedure") == "procedure"


class TestPatientDemographics:
    """Test patient demographics extraction"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    def test_extract_demographics_pediatric(self, summarizer):
        """Test extraction of pediatric patient demographics"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "gender": "male",
                        "birthDate": f"{datetime.now().year - 10}-01-01"
                    }
                }
            ]
        }

        demographics = summarizer._extract_patient_demographics(bundle)

        assert "pediatric" in demographics
        assert "male" in demographics

    def test_extract_demographics_young_adult(self, summarizer):
        """Test extraction of young adult demographics"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "gender": "female",
                        "birthDate": f"{datetime.now().year - 25}-01-01"
                    }
                }
            ]
        }

        demographics = summarizer._extract_patient_demographics(bundle)

        assert "young adult" in demographics
        assert "female" in demographics

    def test_extract_demographics_adult(self, summarizer):
        """Test extraction of adult demographics"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "gender": "male",
                        "birthDate": f"{datetime.now().year - 40}-01-01"
                    }
                }
            ]
        }

        demographics = summarizer._extract_patient_demographics(bundle)

        assert "adult" in demographics

    def test_extract_demographics_middle_aged(self, summarizer):
        """Test extraction of middle-aged demographics"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "gender": "female",
                        "birthDate": f"{datetime.now().year - 60}-01-01"
                    }
                }
            ]
        }

        demographics = summarizer._extract_patient_demographics(bundle)

        assert "middle-aged adult" in demographics

    def test_extract_demographics_senior(self, summarizer):
        """Test extraction of senior demographics"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "gender": "male",
                        "birthDate": f"{datetime.now().year - 75}-01-01"
                    }
                }
            ]
        }

        demographics = summarizer._extract_patient_demographics(bundle)

        assert "senior adult" in demographics

    def test_extract_demographics_no_birthdate(self, summarizer):
        """Test extraction with missing birth date"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "gender": "female"
                    }
                }
            ]
        }

        demographics = summarizer._extract_patient_demographics(bundle)

        assert demographics == "female"

    def test_extract_demographics_no_patient(self, summarizer):
        """Test extraction with no patient resource"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Observation"
                    }
                }
            ]
        }

        demographics = summarizer._extract_patient_demographics(bundle)

        assert demographics is None

    def test_extract_demographics_invalid_birthdate(self, summarizer):
        """Test extraction with invalid birth date format"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "gender": "male",
                        "birthDate": "invalid-date"
                    }
                }
            ]
        }

        demographics = summarizer._extract_patient_demographics(bundle)

        # Should fallback to just gender
        assert demographics == "male"


class TestSummaryTypeDetection:
    """Test summary type determination"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    def test_determine_summary_type_empty(self, summarizer):
        """Test summary type for empty orders"""
        assert summarizer._determine_summary_type([]) == "minimal"

    def test_determine_summary_type_single(self, summarizer):
        """Test summary type for single order"""
        orders = [ClinicalOrder(
            order_type="Patient",
            description="Test",
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.9
        )]

        assert summarizer._determine_summary_type(orders) == "minimal"

    def test_determine_summary_type_few(self, summarizer):
        """Test summary type for 2-3 orders"""
        orders = [
            ClinicalOrder(order_type="Patient", description="Test",
                         processing_tier=ProcessingTier.RULE_BASED, confidence_score=0.9),
            ClinicalOrder(order_type="MedicationRequest", description="Test",
                         processing_tier=ProcessingTier.RULE_BASED, confidence_score=0.9)
        ]

        assert summarizer._determine_summary_type(orders) == "comprehensive"

    def test_determine_summary_type_medium(self, summarizer):
        """Test summary type for 4-8 orders"""
        orders = [
            ClinicalOrder(order_type=f"Type{i}", description="Test",
                         processing_tier=ProcessingTier.RULE_BASED, confidence_score=0.9)
            for i in range(5)
        ]

        assert summarizer._determine_summary_type(orders) == "comprehensive"

    def test_determine_summary_type_complex(self, summarizer):
        """Test summary type for many orders (>8)"""
        orders = [
            ClinicalOrder(order_type=f"Type{i}", description="Test",
                         processing_tier=ProcessingTier.RULE_BASED, confidence_score=0.9)
            for i in range(10)
        ]

        assert summarizer._determine_summary_type(orders) == "complex"


class TestErrorHandling:
    """Test error handling and fallback summaries"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_bundle_with_exception(self, summarizer):
        """Test bundle summarization when exception occurs"""
        bundle = {"resourceType": "Bundle", "id": "error-bundle", "entry": []}

        # Force an exception during analysis
        with patch.object(summarizer, '_analyze_bundle_composition',
                         side_effect=Exception("Analysis failed")):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock) as mock_log:
                summary = await summarizer.summarize_bundle(bundle)

        # Should return error summary
        assert summary.summary_type == "emergency"
        assert summary.confidence_score == 0.1
        assert "Critical processing error" in summary.patient_context
        assert len(summary.clinical_alerts) > 0

        # Should log error event
        mock_log.assert_called()
        error_event = mock_log.call_args_list[-1][0][0]
        assert error_event.error_occurred == True
        assert error_event.error_type == "Exception"

    @pytest.mark.asyncio
    async def test_create_error_summary(self, summarizer):
        """Test creation of error summary"""
        bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle",
            "entry": [
                {"resource": {"resourceType": "Patient"}}
            ]
        }
        error_message = "Database connection failed"

        summary = await summarizer._create_error_summary(bundle, error_message)

        assert summary.summary_type == "emergency"
        assert summary.processing_tier == ProcessingTier.RULE_BASED
        assert summary.confidence_score == 0.1
        assert "Critical processing error" in summary.patient_context
        assert len(summary.primary_orders) == 1
        assert summary.primary_orders[0].order_type == "system_error"
        assert error_message in summary.primary_orders[0].safety_alerts[0]
        assert summary.quality_indicators.completeness_score == 0.1
        assert summary.quality_indicators.missing_critical_information == True

    @pytest.mark.asyncio
    async def test_error_summary_minimal_content(self, summarizer):
        """Test error summary with minimal bundle content"""
        bundle = {"resourceType": "Bundle", "entry": []}

        summary = await summarizer._create_error_summary(bundle, "Unknown error")

        assert isinstance(summary, ClinicalSummary)
        assert summary.confidence_score < 0.5
        assert "manual review required" in summary.primary_orders[0].description.lower()


class TestMonitoringIntegration:
    """Test monitoring and event logging"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    @pytest.mark.asyncio
    async def test_monitoring_event_logged_on_success(self, summarizer):
        """Test monitoring event is logged on successful summarization"""
        bundle = {
            "resourceType": "Bundle",
            "id": "test-bundle",
            "entry": [{"resource": {"resourceType": "Patient"}}]
        }

        mock_analysis = BundleAnalysis(
            resource_count=1,
            resource_types=["Patient"],
            complexity_score=1.0,
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.95,
            specialty_context="General",
            resource_classifications=[]
        )

        with patch.object(summarizer, '_analyze_bundle_composition',
                         new_callable=AsyncMock, return_value=mock_analysis):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock) as mock_log:
                await summarizer.summarize_bundle(bundle, role="physician")

        # Verify event was logged
        mock_log.assert_called_once()
        event = mock_log.call_args[0][0]

        assert isinstance(event, SummarizationEvent)
        assert event.resource_count == 1
        assert event.bundle_id == "test-bundle"
        assert event.tier_selected == ProcessingTier.RULE_BASED
        assert event.user_role == "physician"

    @pytest.mark.asyncio
    async def test_monitoring_event_includes_timing(self, summarizer):
        """Test monitoring event includes timing information"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [{"resource": {"resourceType": "Patient"}}]
        }

        mock_analysis = BundleAnalysis(
            resource_count=1,
            resource_types=["Patient"],
            complexity_score=1.0,
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.95,
            resource_classifications=[]
        )

        with patch.object(summarizer, '_analyze_bundle_composition',
                         new_callable=AsyncMock, return_value=mock_analysis):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock) as mock_log:
                await summarizer.summarize_bundle(bundle)

        event = mock_log.call_args[0][0]

        assert event.analysis_time_ms > 0
        assert event.processing_time_ms >= 0
        assert event.total_time_ms > 0

    @pytest.mark.asyncio
    async def test_monitoring_error_event_logged(self, summarizer):
        """Test monitoring logs error events"""
        bundle = {"resourceType": "Bundle", "id": "error-bundle", "entry": []}

        with patch.object(summarizer, '_analyze_bundle_composition',
                         side_effect=RuntimeError("Critical error")):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock) as mock_log:
                await summarizer.summarize_bundle(bundle, role="nurse")

        # Should log error event
        event = mock_log.call_args[0][0]

        assert event.error_occurred == True
        assert event.error_type == "RuntimeError"
        assert "Critical error" in event.error_message
        assert event.user_role == "nurse"


class TestQualityIndicators:
    """Test quality indicators calculation"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    @pytest.mark.asyncio
    async def test_quality_indicators_high_confidence(self, summarizer):
        """Test quality indicators for high-confidence processing"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [{"resource": {"resourceType": "Patient"}}]
        }

        mock_analysis = BundleAnalysis(
            resource_count=1,
            resource_types=["Patient"],
            complexity_score=1.0,
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.95,
            resource_classifications=[]
        )

        mock_order = ClinicalOrder(
            order_type="Patient",
            description="Test",
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.95
        )

        with patch.object(summarizer.resource_registry, 'get_summarizer') as mock_get:
            mock_sum = AsyncMock()
            mock_sum.summarize_resource.return_value = mock_order
            mock_get.return_value = mock_sum

            summary = await summarizer._process_with_rule_based(bundle, "physician", mock_analysis)

        qi = summary.quality_indicators
        assert qi.completeness_score > 0.9
        assert qi.clinical_accuracy_confidence == 0.95
        assert qi.terminology_consistency == 1.0
        assert qi.missing_critical_information == False

    @pytest.mark.asyncio
    async def test_quality_indicators_with_errors(self, summarizer):
        """Test quality indicators when processing errors occur"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {"resourceType": "Patient"}},
                {"resource": {"resourceType": "MedicationRequest"}}
            ]
        }

        mock_analysis = BundleAnalysis(
            resource_count=2,
            resource_types=["Patient", "MedicationRequest"],
            complexity_score=3.0,
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.90,
            resource_classifications=[]
        )

        # Mock one success and one failure
        def mock_get_summarizer(resource_type):
            mock_sum = AsyncMock()
            if resource_type == "Patient":
                mock_sum.summarize_resource.return_value = ClinicalOrder(
                    order_type="Patient",
                    description="Success",
                    processing_tier=ProcessingTier.RULE_BASED,
                    confidence_score=0.95
                )
            else:
                mock_sum.summarize_resource.side_effect = Exception("Error")
            return mock_sum

        with patch.object(summarizer.resource_registry, 'get_summarizer',
                         side_effect=mock_get_summarizer):
            summary = await summarizer._process_with_rule_based(bundle, "physician", mock_analysis)

        qi = summary.quality_indicators
        assert qi.missing_critical_information == True
        assert qi.completeness_score < 1.0


class TestPerformance:
    """Test performance characteristics"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    @pytest.mark.asyncio
    async def test_summarization_performance(self, summarizer):
        """Test summarization completes within reasonable time"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {"resourceType": "Patient", "id": f"p{i}"}}
                for i in range(5)
            ]
        }

        mock_analysis = BundleAnalysis(
            resource_count=5,
            resource_types=["Patient"],
            complexity_score=5.0,
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.95,
            resource_classifications=[]
        )

        mock_order = ClinicalOrder(
            order_type="Patient",
            description="Test",
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.95
        )

        with patch.object(summarizer, '_analyze_bundle_composition',
                         new_callable=AsyncMock, return_value=mock_analysis):
            with patch.object(summarizer.resource_registry, 'get_summarizer') as mock_get:
                mock_sum = AsyncMock()
                mock_sum.summarize_resource.return_value = mock_order
                mock_get.return_value = mock_sum

                with patch.object(summarizer.monitoring, 'log_summarization_event',
                                new_callable=AsyncMock):
                    start = time.time()
                    await summarizer.summarize_bundle(bundle)
                    elapsed = time.time() - start

        # Should complete in under 1 second for 5 resources
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_analysis_timing_recorded(self, summarizer):
        """Test that analysis timing is properly recorded"""
        bundle = {"resourceType": "Bundle", "entry": []}

        mock_analysis = BundleAnalysis(
            resource_count=0,
            resource_types=[],
            complexity_score=0.0,
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.5,
            resource_classifications=[]
        )

        with patch.object(summarizer, '_analyze_bundle_composition',
                         new_callable=AsyncMock, return_value=mock_analysis):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock) as mock_log:
                await summarizer.summarize_bundle(bundle)

        event = mock_log.call_args[0][0]

        # Timing values should be non-negative
        assert event.analysis_time_ms >= 0
        assert event.processing_time_ms >= 0
        assert event.total_time_ms >= 0


class TestEdgeCases:
    """Test edge cases and validation"""

    @pytest.fixture
    def summarizer(self):
        """Create summarizer instance"""
        return FHIRBundleSummarizer()

    @pytest.mark.asyncio
    async def test_bundle_without_id(self, summarizer):
        """Test processing bundle without explicit ID"""
        bundle = {
            "resourceType": "Bundle",
            "entry": []
        }

        mock_analysis = BundleAnalysis(
            resource_count=0,
            resource_types=[],
            complexity_score=0.0,
            recommended_tier=ProcessingTier.RULE_BASED,
            has_rare_resources=False,
            has_emergency_context=False,
            confidence_score=0.5,
            resource_classifications=[]
        )

        with patch.object(summarizer, '_analyze_bundle_composition',
                         new_callable=AsyncMock, return_value=mock_analysis):
            with patch.object(summarizer.monitoring, 'log_summarization_event',
                            new_callable=AsyncMock) as mock_log:
                summary = await summarizer.summarize_bundle(bundle)

        # Should generate bundle ID automatically
        event = mock_log.call_args[0][0]
        assert event.bundle_id.startswith("bundle-")

    def test_extract_patient_context(self, summarizer):
        """Test patient context extraction"""
        bundle = {
            "resourceType": "Bundle",
            "entry": [
                {"resource": {"resourceType": "Patient"}},
                {"resource": {"resourceType": "MedicationRequest"}}
            ]
        }

        context = summarizer._extract_patient_context(bundle, "rule_based_processing")

        assert "2 resources" in context
        assert "Patient" in context
        assert "MedicationRequest" in context
        assert "rule based processing" in context
