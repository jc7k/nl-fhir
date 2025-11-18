"""
Epic 4: Comprehensive Tests for Resource Summarizer Registry
Tests rule-based resource summarizers and registry functionality

Coverage:
- BaseResourceSummarizer utility methods
- 12 specific resource summarizers (Medication, ServiceRequest, Condition, etc.)
- GenericFHIRResourceSummarizer (universal fallback)
- ResourceSummarizerRegistry (100% FHIR coverage)
- Code extraction and text processing
- Clinical order generation
- Registry management and statistics
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from src.nl_fhir.services.summarization.resource_summarizer_registry import (
    BaseResourceSummarizer,
    MedicationSummarizer,
    ServiceRequestSummarizer,
    ConditionSummarizer,
    ObservationSummarizer,
    ProcedureSummarizer,
    DiagnosticReportSummarizer,
    PatientSummarizer,
    EncounterSummarizer,
    CarePlanSummarizer,
    AllergyIntoleranceSummarizer,
    ImmunizationSummarizer,
    DeviceRequestSummarizer,
    GenericFHIRResourceSummarizer,
    ResourceSummarizerRegistry
)
from src.nl_fhir.services.summarization.models import ClinicalOrder, ProcessingTier


class TestBaseResourceSummarizer:
    """Test BaseResourceSummarizer utility methods"""

    class ConcreteSummarizer(BaseResourceSummarizer):
        """Concrete implementation for testing"""

        def _get_supported_resource_types(self):
            return {"TestResource"}

        async def summarize_resource(self, fhir_resource, role="physician"):
            return ClinicalOrder(
                order_type="test",
                description="Test order",
                processing_tier=ProcessingTier.RULE_BASED,
                confidence_score=0.9
            )

    def test_base_summarizer_initialization(self):
        """Test base summarizer initializes correctly"""
        summarizer = self.ConcreteSummarizer()

        assert summarizer.supported_resource_types == {"TestResource"}
        assert summarizer.clinical_templates == {}

    def test_supports_resource_type_true(self):
        """Test supports_resource_type returns True for supported types"""
        summarizer = self.ConcreteSummarizer()

        assert summarizer.supports_resource_type("TestResource") is True

    def test_supports_resource_type_false(self):
        """Test supports_resource_type returns False for unsupported types"""
        summarizer = self.ConcreteSummarizer()

        assert summarizer.supports_resource_type("UnsupportedResource") is False

    def test_extract_coding_display_with_display(self):
        """Test extract coding display when display field exists"""
        summarizer = self.ConcreteSummarizer()

        coding = {
            "system": "http://loinc.org",
            "code": "12345-6",
            "display": "Hemoglobin A1c"
        }

        result = summarizer._extract_coding_display(coding)
        assert result == "Hemoglobin A1c"

    def test_extract_coding_display_with_code_only(self):
        """Test extract coding display falls back to code"""
        summarizer = self.ConcreteSummarizer()

        coding = {
            "system": "http://loinc.org",
            "code": "blood_glucose_test"
        }

        result = summarizer._extract_coding_display(coding)
        assert result == "Blood Glucose Test"  # Code transformed to readable text

    def test_extract_coding_display_invalid_input(self):
        """Test extract coding display with invalid input"""
        summarizer = self.ConcreteSummarizer()

        result = summarizer._extract_coding_display(None)
        assert result == "Unknown"

    def test_extract_code_text_from_text_field(self):
        """Test code text extraction from text field"""
        summarizer = self.ConcreteSummarizer()

        resource = {
            "code": {
                "text": "Complete Blood Count"
            }
        }

        result = summarizer._extract_code_text(resource, "code")
        assert result == "Complete Blood Count"

    def test_extract_code_text_from_coding_array(self):
        """Test code text extraction from coding array"""
        summarizer = self.ConcreteSummarizer()

        resource = {
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "12345-6",
                        "display": "Test Name"
                    }
                ]
            }
        }

        result = summarizer._extract_code_text(resource, "code")
        assert result == "Test Name"

    def test_extract_code_text_missing_field(self):
        """Test code text extraction with missing field"""
        summarizer = self.ConcreteSummarizer()

        resource = {}
        result = summarizer._extract_code_text(resource, "code")
        assert result == "Unknown"


class TestMedicationSummarizer:
    """Test MedicationSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create medication summarizer"""
        return MedicationSummarizer()

    def test_supported_resource_types(self, summarizer):
        """Test supported resource types"""
        assert summarizer.supported_resource_types == {"MedicationRequest"}

    @pytest.mark.asyncio
    async def test_summarize_basic_medication(self, summarizer):
        """Test summarization of basic medication request"""
        resource = {
            "resourceType": "MedicationRequest",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "197361",
                    "display": "Lisinopril 10 MG Oral Tablet"
                }]
            }
        }

        order = await summarizer.summarize_resource(resource)

        assert order.order_type == "medication"
        assert "Lisinopril 10 MG Oral Tablet" in order.description
        assert order.processing_tier == ProcessingTier.RULE_BASED
        assert order.confidence_score == 0.95

    @pytest.mark.asyncio
    async def test_summarize_medication_with_dosage(self, summarizer):
        """Test medication with complete dosage information"""
        resource = {
            "resourceType": "MedicationRequest",
            "medicationCodeableConcept": {
                "text": "Amoxicillin"
            },
            "dosageInstruction": [{
                "doseAndRate": [{
                    "doseQuantity": {
                        "value": 500,
                        "unit": "mg"
                    }
                }],
                "route": {
                    "coding": [{
                        "display": "Oral"
                    }]
                },
                "timing": {
                    "repeat": {
                        "frequency": 3,
                        "period": 1,
                        "periodUnit": "day"
                    }
                }
            }]
        }

        order = await summarizer.summarize_resource(resource)

        assert "Amoxicillin" in order.description
        assert "500 mg" in order.description
        assert "Oral" in order.description
        assert "three times daily" in order.description

    @pytest.mark.asyncio
    async def test_summarize_medication_with_priority(self, summarizer):
        """Test medication with priority"""
        resource = {
            "resourceType": "MedicationRequest",
            "medicationCodeableConcept": {
                "text": "Epinephrine"
            },
            "priority": "URGENT"
        }

        order = await summarizer.summarize_resource(resource)

        assert order.priority == "urgent"

    @pytest.mark.asyncio
    async def test_extract_frequency_once_daily(self, summarizer):
        """Test extraction of once daily frequency"""
        timing = {
            "repeat": {
                "frequency": 1,
                "period": 1,
                "periodUnit": "day"
            }
        }

        frequency = summarizer._extract_frequency_text(timing)
        assert frequency == "once daily"

    @pytest.mark.asyncio
    async def test_extract_frequency_twice_daily(self, summarizer):
        """Test extraction of twice daily frequency"""
        timing = {
            "repeat": {
                "frequency": 2,
                "period": 1,
                "periodUnit": "day"
            }
        }

        frequency = summarizer._extract_frequency_text(timing)
        assert frequency == "twice daily"

    @pytest.mark.asyncio
    async def test_extract_clinical_rationale(self, summarizer):
        """Test extraction of clinical rationale"""
        resource = {
            "reasonCode": [{
                "text": "Hypertension"
            }]
        }

        rationale = summarizer._extract_clinical_rationale(resource)
        assert rationale == "Hypertension"


class TestServiceRequestSummarizer:
    """Test ServiceRequestSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create service request summarizer"""
        return ServiceRequestSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_laboratory_request(self, summarizer):
        """Test laboratory service request"""
        resource = {
            "resourceType": "ServiceRequest",
            "code": {
                "text": "Complete Blood Count"
            },
            "category": [{
                "coding": [{
                    "display": "Laboratory"
                }]
            }]
        }

        order = await summarizer.summarize_resource(resource)

        assert order.order_type == "service_request"
        assert "laboratory test" in order.description.lower()
        assert "Complete Blood Count" in order.description

    @pytest.mark.asyncio
    async def test_summarize_imaging_request(self, summarizer):
        """Test imaging service request"""
        resource = {
            "resourceType": "ServiceRequest",
            "code": {
                "text": "Chest X-Ray"
            },
            "category": [{
                "coding": [{
                    "display": "Imaging"
                }]
            }]
        }

        order = await summarizer.summarize_resource(resource)

        assert "imaging study" in order.description.lower()
        assert "Chest X-Ray" in order.description

    @pytest.mark.asyncio
    async def test_classify_service_type_from_code(self, summarizer):
        """Test service type classification from code"""
        # Laboratory test
        resource = {"code": {"text": "Blood glucose test"}}
        assert summarizer._classify_service_type(resource) == "laboratory"

        # Imaging
        resource = {"code": {"text": "CT scan chest"}}
        assert summarizer._classify_service_type(resource) == "imaging"

        # Procedure
        resource = {"code": {"text": "Biopsy liver"}}
        assert summarizer._classify_service_type(resource) == "procedure"


class TestConditionSummarizer:
    """Test ConditionSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create condition summarizer"""
        return ConditionSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_active_condition(self, summarizer):
        """Test active condition"""
        resource = {
            "resourceType": "Condition",
            "code": {
                "text": "Type 2 Diabetes Mellitus"
            },
            "clinicalStatus": {
                "coding": [{
                    "code": "active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "code": "confirmed"
                }]
            }
        }

        order = await summarizer.summarize_resource(resource)

        assert "Active diagnosis" in order.description
        assert "Type 2 Diabetes Mellitus" in order.description

    @pytest.mark.asyncio
    async def test_summarize_resolved_condition(self, summarizer):
        """Test resolved condition"""
        resource = {
            "resourceType": "Condition",
            "code": {
                "text": "Acute Bronchitis"
            },
            "clinicalStatus": {
                "coding": [{
                    "code": "resolved"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "code": "confirmed"
                }]
            }
        }

        order = await summarizer.summarize_resource(resource)

        assert "Resolved condition" in order.description

    @pytest.mark.asyncio
    async def test_summarize_provisional_diagnosis(self, summarizer):
        """Test provisional diagnosis"""
        resource = {
            "resourceType": "Condition",
            "code": {
                "text": "Suspected Appendicitis"
            },
            "clinicalStatus": {
                "coding": [{
                    "code": "active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "code": "provisional"
                }]
            }
        }

        order = await summarizer.summarize_resource(resource)

        assert "(provisional)" in order.description


class TestObservationSummarizer:
    """Test ObservationSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create observation summarizer"""
        return ObservationSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_observation_with_quantity(self, summarizer):
        """Test observation with quantity value"""
        resource = {
            "resourceType": "Observation",
            "code": {
                "text": "Blood Glucose"
            },
            "status": "final",
            "valueQuantity": {
                "value": 95,
                "unit": "mg/dL"
            }
        }

        order = await summarizer.summarize_resource(resource)

        assert "Final result" in order.description
        assert "Blood Glucose" in order.description
        assert "95 mg/dL" in order.description

    @pytest.mark.asyncio
    async def test_summarize_observation_with_string(self, summarizer):
        """Test observation with string value"""
        resource = {
            "resourceType": "Observation",
            "code": {
                "text": "Patient Note"
            },
            "status": "preliminary",
            "valueString": "Patient appears stable"
        }

        order = await summarizer.summarize_resource(resource)

        assert "Preliminary result" in order.description
        assert "Patient appears stable" in order.description

    @pytest.mark.asyncio
    async def test_summarize_observation_with_boolean(self, summarizer):
        """Test observation with boolean value"""
        resource = {
            "resourceType": "Observation",
            "code": {
                "text": "Fever Present"
            },
            "status": "final",
            "valueBoolean": True
        }

        order = await summarizer.summarize_resource(resource)

        assert "Yes" in order.description

    @pytest.mark.asyncio
    async def test_summarize_observation_with_components(self, summarizer):
        """Test observation with component values"""
        resource = {
            "resourceType": "Observation",
            "code": {
                "text": "Blood Pressure"
            },
            "status": "final",
            "component": [
                {
                    "code": {
                        "text": "Systolic"
                    },
                    "valueQuantity": {
                        "value": 120,
                        "unit": "mmHg"
                    }
                },
                {
                    "code": {
                        "text": "Diastolic"
                    },
                    "valueQuantity": {
                        "value": 80,
                        "unit": "mmHg"
                    }
                }
            ]
        }

        order = await summarizer.summarize_resource(resource)

        assert "Systolic" in order.description
        assert "120 mmHg" in order.description


class TestProcedureSummarizer:
    """Test ProcedureSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create procedure summarizer"""
        return ProcedureSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_completed_procedure(self, summarizer):
        """Test completed procedure"""
        resource = {
            "resourceType": "Procedure",
            "code": {
                "text": "Appendectomy"
            },
            "status": "completed",
            "performedDateTime": "2024-01-15T10:30:00Z"
        }

        order = await summarizer.summarize_resource(resource)

        assert "Completed procedure" in order.description
        assert "Appendectomy" in order.description
        assert "2024-01-15" in order.description

    @pytest.mark.asyncio
    async def test_summarize_in_progress_procedure(self, summarizer):
        """Test in-progress procedure"""
        resource = {
            "resourceType": "Procedure",
            "code": {
                "text": "Cardiac Catheterization"
            },
            "status": "in-progress"
        }

        order = await summarizer.summarize_resource(resource)

        assert "in progress" in order.description.lower()


class TestDiagnosticReportSummarizer:
    """Test DiagnosticReportSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create diagnostic report summarizer"""
        return DiagnosticReportSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_final_report(self, summarizer):
        """Test final diagnostic report"""
        resource = {
            "resourceType": "DiagnosticReport",
            "code": {
                "text": "Chest X-Ray"
            },
            "status": "final",
            "category": [{
                "coding": [{
                    "display": "Radiology"
                }]
            }],
            "conclusion": "No acute findings"
        }

        order = await summarizer.summarize_resource(resource)

        assert "Final diagnostic report" in order.description
        assert "Chest X-Ray" in order.description
        assert "Radiology" in order.description
        assert "No acute findings" in order.description

    @pytest.mark.asyncio
    async def test_summarize_preliminary_report(self, summarizer):
        """Test preliminary report"""
        resource = {
            "resourceType": "DiagnosticReport",
            "code": {
                "text": "Lab Panel"
            },
            "status": "preliminary"
        }

        order = await summarizer.summarize_resource(resource)

        assert "Preliminary report" in order.description


class TestPatientSummarizer:
    """Test PatientSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create patient summarizer"""
        return PatientSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_patient_with_demographics(self, summarizer):
        """Test patient with full demographics"""
        resource = {
            "resourceType": "Patient",
            "active": True,
            "gender": "female",
            "birthDate": f"{datetime.now().year - 45}-01-01"
        }

        order = await summarizer.summarize_resource(resource)

        assert "Patient record" in order.description
        assert "female" in order.description
        assert "~45" in order.description

    @pytest.mark.asyncio
    async def test_summarize_inactive_patient(self, summarizer):
        """Test inactive patient"""
        resource = {
            "resourceType": "Patient",
            "active": False,
            "gender": "male"
        }

        order = await summarizer.summarize_resource(resource)

        assert "inactive" in order.description


class TestEncounterSummarizer:
    """Test EncounterSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create encounter summarizer"""
        return EncounterSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_emergency_encounter(self, summarizer):
        """Test emergency encounter"""
        resource = {
            "resourceType": "Encounter",
            "status": "in-progress",
            "class": {
                "code": "EMER"
            },
            "type": [{
                "coding": [{
                    "display": "Trauma evaluation"
                }]
            }]
        }

        order = await summarizer.summarize_resource(resource)

        assert "emergency" in order.description
        assert "Trauma evaluation" in order.description

    @pytest.mark.asyncio
    async def test_summarize_ambulatory_encounter(self, summarizer):
        """Test ambulatory encounter"""
        resource = {
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "code": "AMB"
            }
        }

        order = await summarizer.summarize_resource(resource)

        assert "ambulatory" in order.description


class TestCarePlanSummarizer:
    """Test CarePlanSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create care plan summarizer"""
        return CarePlanSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_care_plan_with_title(self, summarizer):
        """Test care plan with title"""
        resource = {
            "resourceType": "CarePlan",
            "status": "active",
            "intent": "plan",
            "title": "Diabetes Management Plan"
        }

        order = await summarizer.summarize_resource(resource)

        assert "Diabetes Management Plan" in order.description
        assert "active" in order.description

    @pytest.mark.asyncio
    async def test_summarize_care_plan_with_category(self, summarizer):
        """Test care plan with category"""
        resource = {
            "resourceType": "CarePlan",
            "status": "draft",
            "intent": "proposal",
            "category": [{
                "coding": [{
                    "display": "Oncology"
                }]
            }]
        }

        order = await summarizer.summarize_resource(resource)

        assert "Oncology" in order.description


class TestAllergyIntoleranceSummarizer:
    """Test AllergyIntoleranceSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create allergy intolerance summarizer"""
        return AllergyIntoleranceSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_active_allergy(self, summarizer):
        """Test active allergy"""
        resource = {
            "resourceType": "AllergyIntolerance",
            "code": {
                "text": "Penicillin"
            },
            "clinicalStatus": {
                "coding": [{
                    "code": "active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "code": "confirmed"
                }]
            },
            "category": ["medication"],
            "criticality": "high"
        }

        order = await summarizer.summarize_resource(resource)

        assert "Active allergy" in order.description
        assert "Penicillin" in order.description
        assert "high" in order.description

    @pytest.mark.asyncio
    async def test_summarize_resolved_allergy(self, summarizer):
        """Test resolved allergy"""
        resource = {
            "resourceType": "AllergyIntolerance",
            "code": {
                "text": "Shellfish"
            },
            "clinicalStatus": {
                "coding": [{
                    "code": "resolved"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "code": "confirmed"
                }]
            }
        }

        order = await summarizer.summarize_resource(resource)

        assert "Resolved allergy" in order.description


class TestImmunizationSummarizer:
    """Test ImmunizationSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create immunization summarizer"""
        return ImmunizationSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_completed_immunization(self, summarizer):
        """Test completed immunization"""
        resource = {
            "resourceType": "Immunization",
            "vaccineCode": {
                "text": "Influenza Vaccine"
            },
            "status": "completed",
            "occurrenceDateTime": "2024-01-15"
        }

        order = await summarizer.summarize_resource(resource)

        assert "Immunization completed" in order.description
        assert "Influenza Vaccine" in order.description
        assert "2024-01-15" in order.description

    @pytest.mark.asyncio
    async def test_summarize_not_done_immunization(self, summarizer):
        """Test immunization not administered"""
        resource = {
            "resourceType": "Immunization",
            "vaccineCode": {
                "text": "COVID-19 Vaccine"
            },
            "status": "not-done"
        }

        order = await summarizer.summarize_resource(resource)

        assert "not administered" in order.description


class TestDeviceRequestSummarizer:
    """Test DeviceRequestSummarizer functionality"""

    @pytest.fixture
    def summarizer(self):
        """Create device request summarizer"""
        return DeviceRequestSummarizer()

    @pytest.mark.asyncio
    async def test_summarize_active_device_request(self, summarizer):
        """Test active device request"""
        resource = {
            "resourceType": "DeviceRequest",
            "codeCodeableConcept": {
                "text": "Insulin Pump"
            },
            "status": "active",
            "intent": "order"
        }

        order = await summarizer.summarize_resource(resource)

        assert "Device request" in order.description
        assert "Insulin Pump" in order.description

    @pytest.mark.asyncio
    async def test_summarize_completed_device_request(self, summarizer):
        """Test completed device request"""
        resource = {
            "resourceType": "DeviceRequest",
            "code": {
                "text": "Wheelchair"
            },
            "status": "completed",
            "intent": "order"
        }

        order = await summarizer.summarize_resource(resource)

        assert "Device provided" in order.description


class TestGenericFHIRResourceSummarizer:
    """Test GenericFHIRResourceSummarizer (universal fallback)"""

    @pytest.fixture
    def summarizer(self):
        """Create generic summarizer"""
        return GenericFHIRResourceSummarizer()

    def test_supports_all_types(self, summarizer):
        """Test generic summarizer has no specific supported types"""
        # Empty set means it's a fallback for all types
        assert summarizer.supported_resource_types == set()

    @pytest.mark.asyncio
    async def test_summarize_unknown_resource_basic(self, summarizer):
        """Test summarization of unknown resource type"""
        resource = {
            "resourceType": "CustomResource",
            "id": "custom-123"
        }

        order = await summarizer.summarize_resource(resource)

        assert order.order_type == "customresource"
        assert "CustomResource resource" in order.description
        assert order.confidence_score == 0.75  # Lower confidence for generic

    @pytest.mark.asyncio
    async def test_summarize_with_status_field(self, summarizer):
        """Test generic summarization extracts status"""
        resource = {
            "resourceType": "UnknownType",
            "status": "active"
        }

        order = await summarizer.summarize_resource(resource)

        assert "status: active" in order.description

    @pytest.mark.asyncio
    async def test_summarize_with_code_field(self, summarizer):
        """Test generic summarization extracts code"""
        resource = {
            "resourceType": "UnknownType",
            "code": {
                "text": "Some clinical code"
            }
        }

        order = await summarizer.summarize_resource(resource)

        assert "Some clinical code" in order.description

    @pytest.mark.asyncio
    async def test_summarize_with_patient_reference(self, summarizer):
        """Test generic summarization detects patient link"""
        resource = {
            "resourceType": "UnknownType",
            "subject": {
                "reference": "Patient/12345"
            }
        }

        order = await summarizer.summarize_resource(resource)

        assert "linked to patient" in order.description

    @pytest.mark.asyncio
    async def test_summarize_with_priority(self, summarizer):
        """Test generic summarization extracts priority"""
        resource = {
            "resourceType": "UnknownType",
            "priority": "urgent"
        }

        order = await summarizer.summarize_resource(resource)

        assert "priority: urgent" in order.description


class TestResourceSummarizerRegistry:
    """Test ResourceSummarizerRegistry functionality"""

    @pytest.fixture
    def registry(self):
        """Create registry instance"""
        return ResourceSummarizerRegistry()

    def test_registry_initialization(self, registry):
        """Test registry initializes with all summarizers"""
        supported_types = registry.get_supported_resource_types()

        # Should have at least the 12 core resource types
        assert "MedicationRequest" in supported_types
        assert "ServiceRequest" in supported_types
        assert "Condition" in supported_types
        assert "Observation" in supported_types
        assert "Procedure" in supported_types
        assert "DiagnosticReport" in supported_types
        assert "Patient" in supported_types
        assert "Encounter" in supported_types
        assert "CarePlan" in supported_types
        assert "AllergyIntolerance" in supported_types
        assert "Immunization" in supported_types
        assert "DeviceRequest" in supported_types

    def test_get_summarizer_for_medication(self, registry):
        """Test getting summarizer for MedicationRequest"""
        summarizer = registry.get_summarizer("MedicationRequest")

        assert isinstance(summarizer, MedicationSummarizer)
        assert summarizer.supports_resource_type("MedicationRequest")

    def test_get_summarizer_for_observation(self, registry):
        """Test getting summarizer for Observation"""
        summarizer = registry.get_summarizer("Observation")

        assert isinstance(summarizer, ObservationSummarizer)

    def test_get_summarizer_for_unknown_type(self, registry):
        """Test getting summarizer for unknown resource type"""
        summarizer = registry.get_summarizer("UnknownResourceType")

        # Should return generic fallback
        assert isinstance(summarizer, GenericFHIRResourceSummarizer)

    def test_register_custom_summarizer(self, registry):
        """Test registering a custom summarizer"""

        class CustomSummarizer(BaseResourceSummarizer):
            def _get_supported_resource_types(self):
                return {"CustomType"}

            async def summarize_resource(self, resource, role="physician"):
                return ClinicalOrder(
                    order_type="custom",
                    description="Custom order",
                    processing_tier=ProcessingTier.RULE_BASED,
                    confidence_score=0.9
                )

        custom = CustomSummarizer()
        registry.register_summarizer("CustomType", custom)

        # Should now return custom summarizer
        summarizer = registry.get_summarizer("CustomType")
        assert isinstance(summarizer, CustomSummarizer)

    def test_register_invalid_summarizer(self, registry):
        """Test registering invalid summarizer raises error"""

        class NotASummarizer:
            pass

        with pytest.raises(ValueError, match="must inherit from BaseResourceSummarizer"):
            registry.register_summarizer("InvalidType", NotASummarizer())

    def test_calculate_rule_coverage_full(self, registry):
        """Test rule coverage calculation with full coverage"""
        resource_types = ["MedicationRequest", "Observation", "Patient"]

        coverage = registry.calculate_rule_coverage(resource_types)

        assert coverage == 1.0  # 100% coverage

    def test_calculate_rule_coverage_partial(self, registry):
        """Test rule coverage calculation with partial coverage"""
        resource_types = ["MedicationRequest", "UnknownType1", "UnknownType2"]

        coverage = registry.calculate_rule_coverage(resource_types)

        assert coverage == pytest.approx(0.333, rel=0.01)  # 1/3 coverage

    def test_calculate_rule_coverage_empty(self, registry):
        """Test rule coverage calculation with empty list"""
        coverage = registry.calculate_rule_coverage([])

        assert coverage == 0.0

    def test_get_unsupported_resource_types(self, registry):
        """Test getting unsupported resource types"""
        resource_types = [
            "MedicationRequest",  # Supported
            "UnknownType1",        # Unsupported
            "Observation",         # Supported
            "UnknownType2"         # Unsupported
        ]

        unsupported = registry.get_unsupported_resource_types(resource_types)

        assert set(unsupported) == {"UnknownType1", "UnknownType2"}

    def test_get_registry_stats(self, registry):
        """Test getting registry statistics"""
        stats = registry.get_registry_stats()

        assert "total_summarizers" in stats
        assert "supported_resource_types" in stats
        assert "resource_types" in stats
        assert "last_updated" in stats

        # Should have 12+ supported resource types
        assert stats["supported_resource_types"] >= 12

        # Resource types should be sorted
        assert stats["resource_types"] == sorted(stats["resource_types"])

    def test_100_percent_coverage_guarantee(self, registry):
        """Test that registry provides 100% FHIR coverage via fallback"""
        # Test a variety of known and unknown resource types
        test_types = [
            "MedicationRequest",  # Known
            "RandomResourceType", # Unknown
            "Patient",           # Known
            "CompletelyMadeUp",  # Unknown
        ]

        for resource_type in test_types:
            summarizer = registry.get_summarizer(resource_type)
            # Should always return a summarizer (never None)
            assert summarizer is not None


class TestIntegrationScenarios:
    """Test integration scenarios across multiple summarizers"""

    @pytest.fixture
    def registry(self):
        """Create registry instance"""
        return ResourceSummarizerRegistry()

    @pytest.mark.asyncio
    async def test_summarize_multi_resource_bundle(self, registry):
        """Test summarizing resources from a multi-resource bundle"""
        resources = [
            {
                "resourceType": "Patient",
                "gender": "female",
                "birthDate": "1980-01-01"
            },
            {
                "resourceType": "MedicationRequest",
                "medicationCodeableConcept": {
                    "text": "Metformin"
                }
            },
            {
                "resourceType": "Condition",
                "code": {
                    "text": "Type 2 Diabetes"
                },
                "clinicalStatus": {
                    "coding": [{"code": "active"}]
                },
                "verificationStatus": {
                    "coding": [{"code": "confirmed"}]
                }
            }
        ]

        orders = []
        for resource in resources:
            summarizer = registry.get_summarizer(resource["resourceType"])
            order = await summarizer.summarize_resource(resource)
            orders.append(order)

        assert len(orders) == 3
        assert orders[0].order_type == "patient"
        assert orders[1].order_type == "medication"
        assert orders[2].order_type == "condition"

    @pytest.mark.asyncio
    async def test_all_registered_summarizers_work(self, registry):
        """Test that all registered summarizers can process resources"""
        supported_types = registry.get_supported_resource_types()

        for resource_type in supported_types:
            summarizer = registry.get_summarizer(resource_type)

            # Create minimal valid resource
            resource = {
                "resourceType": resource_type,
                "id": f"test-{resource_type.lower()}"
            }

            # Should not raise exception
            order = await summarizer.summarize_resource(resource)
            assert isinstance(order, ClinicalOrder)
            assert order.processing_tier == ProcessingTier.RULE_BASED


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def registry(self):
        """Create registry instance"""
        return ResourceSummarizerRegistry()

    @pytest.mark.asyncio
    async def test_resource_with_missing_fields(self, registry):
        """Test handling resource with missing fields"""
        resource = {
            "resourceType": "MedicationRequest"
            # Missing medicationCodeableConcept and other fields
        }

        summarizer = registry.get_summarizer("MedicationRequest")
        order = await summarizer.summarize_resource(resource)

        # Should still produce an order
        assert isinstance(order, ClinicalOrder)

    @pytest.mark.asyncio
    async def test_resource_with_malformed_coding(self, registry):
        """Test handling resource with malformed coding"""
        resource = {
            "resourceType": "Observation",
            "code": {
                "coding": "not-an-array"  # Malformed
            },
            "status": "final"
        }

        summarizer = registry.get_summarizer("Observation")
        order = await summarizer.summarize_resource(resource)

        assert isinstance(order, ClinicalOrder)

    @pytest.mark.asyncio
    async def test_empty_resource(self, registry):
        """Test handling completely empty resource"""
        resource = {}

        summarizer = registry.get_summarizer("Unknown")
        order = await summarizer.summarize_resource(resource)

        assert isinstance(order, ClinicalOrder)
        assert "Unknown resource" in order.description
