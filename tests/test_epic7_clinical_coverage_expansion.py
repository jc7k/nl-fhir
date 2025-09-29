"""
Epic 7 Clinical Coverage Expansion Tests
Tests for Stories 7.1-7.3: Specimen, Coverage, and Appointment FHIR resources

Validates comprehensive clinical workflow coverage with laboratory processes,
insurance integration, and appointment scheduling functionality.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


class TestEpic7ClinicalCoverageExpansion:
    """Test Epic 7 resources: Specimen, Coverage, Appointment"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    # =================================================================
    # Story 7.1: Specimen Resource Tests
    # =================================================================

    def test_specimen_basic_creation(self, factory):
        """Test basic Specimen resource creation (Story 7.1)"""

        specimen_data = {
            "specimen_id": "SPEC-2024-001",
            "type": "blood",
            "status": "available"
        }

        patient_ref = "Patient/patient-123"

        result = factory.create_specimen_resource(
            specimen_data,
            patient_ref,
            request_id="req-001"
        )

        assert result["resourceType"] == "Specimen"
        assert result["status"] == "available"
        assert result["subject"]["reference"] == patient_ref

        # Handle both FHIR library and fallback modes
        if "coding" in result["type"]:
            assert result["type"]["coding"][0]["code"] == "119297000"
            assert result["type"]["coding"][0]["display"] == "Blood specimen"
        else:
            assert result["type"]["text"] == "blood"

    def test_specimen_with_collection_details(self, factory):
        """Test Specimen with detailed collection information"""

        specimen_data = {
            "type": "urine",
            "collection": {
                "collected_date": "2024-01-15T10:30:00Z",
                "site": "clean catch",
                "method": "clean catch",
                "collector_ref": "Practitioner/nurse-456"
            },
            "container": {
                "type": "urine container",
                "capacity": {"value": 100, "unit": "mL"}
            }
        }

        result = factory.create_specimen_resource(
            specimen_data,
            "Patient/patient-123",
            service_request_ref="ServiceRequest/lab-order-789"
        )

        assert result["type"]["coding"][0]["code"] == "122575003"
        assert result["collection"]["collectedDateTime"] == "2024-01-15T10:30:00Z"
        assert result["collection"]["collector"]["reference"] == "Practitioner/nurse-456"
        assert result["container"][0]["capacity"]["value"] == 100
        assert result["request"][0]["reference"] == "ServiceRequest/lab-order-789"

    def test_specimen_with_processing(self, factory):
        """Test Specimen with processing procedures"""

        specimen_data = {
            "type": "blood",
            "processing": [
                {
                    "procedure": "centrifugation",
                    "description": "Separate serum from blood",
                    "time": "2024-01-15T11:00:00Z"
                },
                {
                    "procedure": "refrigeration",
                    "description": "Store at 4°C",
                    "time": "2024-01-15T11:15:00Z"
                }
            ]
        }

        result = factory.create_specimen_resource(
            specimen_data,
            "Patient/patient-123"
        )

        assert len(result["processing"]) == 2
        assert result["processing"][0]["procedure"]["coding"][0]["code"] == "85457002"
        assert result["processing"][1]["procedure"]["coding"][0]["code"] == "428648005"

    # =================================================================
    # Story 7.2: Coverage Resource Tests
    # =================================================================

    def test_coverage_basic_creation(self, factory):
        """Test basic Coverage resource creation (Story 7.2)"""

        coverage_data = {
            "coverage_id": "COV-2024-001",
            "type": "medical",
            "status": "active",
            "subscriber_id": "SUB123456",
            "payor": {
                "id": "anthem-bcbs",
                "name": "Anthem Blue Cross Blue Shield"
            }
        }

        patient_ref = "Patient/patient-123"

        result = factory.create_coverage_resource(
            coverage_data,
            patient_ref,
            request_id="req-001"
        )

        assert result["resourceType"] == "Coverage"
        assert result["status"] == "active"
        assert result["subscriber"]["reference"] == patient_ref
        assert result["beneficiary"]["reference"] == patient_ref
        assert result["subscriberId"] == "SUB123456"
        assert result["type"]["coding"][0]["code"] == "MCPOL"

    def test_coverage_with_plan_details(self, factory):
        """Test Coverage with plan class information"""

        coverage_data = {
            "type": "medical",
            "relationship": "self",
            "class": [
                {
                    "type": "group",
                    "value": "ABC123",
                    "name": "Corporate Health Plan"
                },
                {
                    "type": "plan",
                    "value": "GOLD-PPO",
                    "name": "Gold PPO Plan"
                }
            ],
            "period": {
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-12-31T23:59:59Z"
            }
        }

        result = factory.create_coverage_resource(
            coverage_data,
            "Patient/patient-123"
        )

        assert result["relationship"]["coding"][0]["code"] == "self"
        assert len(result["class"]) == 2
        assert result["class"][0]["type"]["coding"][0]["code"] == "group"
        assert result["class"][0]["value"] == "ABC123"
        assert result["period"]["start"] == "2024-01-01T00:00:00Z"

    def test_coverage_with_cost_sharing(self, factory):
        """Test Coverage with cost-sharing information"""

        coverage_data = {
            "type": "medical",
            "cost_to_beneficiary": [
                {
                    "type": "copay",
                    "value": {"amount": 25.00, "currency": "USD"}
                },
                {
                    "type": "deductible",
                    "value": {"amount": 1000.00, "currency": "USD"},
                    "exception": [
                        {
                            "type": "generic",
                            "period": {
                                "start": "2024-01-01T00:00:00Z"
                            }
                        }
                    ]
                }
            ]
        }

        result = factory.create_coverage_resource(
            coverage_data,
            "Patient/patient-123"
        )

        assert len(result["costToBeneficiary"]) == 2
        assert result["costToBeneficiary"][0]["valueMoney"]["value"] == 25.00
        assert result["costToBeneficiary"][1]["valueMoney"]["value"] == 1000.00
        assert len(result["costToBeneficiary"][1]["exception"]) == 1

    # =================================================================
    # Story 7.3: Appointment Resource Tests
    # =================================================================

    def test_appointment_basic_creation(self, factory):
        """Test basic Appointment resource creation (Story 7.3)"""

        appointment_data = {
            "appointment_id": "APPT-2024-001",
            "status": "booked",
            "start": "2024-02-15T14:00:00Z",
            "end": "2024-02-15T14:30:00Z",
            "appointment_type": "routine",
            "description": "Annual physical examination"
        }

        patient_ref = "Patient/patient-123"
        practitioner_ref = "Practitioner/dr-smith"

        result = factory.create_appointment_resource(
            appointment_data,
            patient_ref,
            practitioner_ref=practitioner_ref
        )

        assert result["resourceType"] == "Appointment"
        assert result["status"] == "booked"
        assert result["start"] == "2024-02-15T14:00:00Z"
        assert result["end"] == "2024-02-15T14:30:00Z"
        assert result["appointmentType"]["coding"][0]["code"] == "ROUTINE"
        assert len(result["participant"]) >= 2  # Patient + Practitioner

    def test_appointment_with_specialty_service(self, factory):
        """Test Appointment with specialty and service information"""

        appointment_data = {
            "status": "proposed",
            "appointment_type": "consultation",
            "service_category": "specialty",
            "service_type": "consultation",
            "specialty": "cardiology",
            "reason_code": "follow up",
            "duration_minutes": 60,
            "priority": 5
        }

        result = factory.create_appointment_resource(
            appointment_data,
            "Patient/patient-123",
            practitioner_ref="Practitioner/cardiologist-456",
            location_ref="Location/cardio-clinic"
        )

        assert result["specialty"][0]["coding"][0]["code"] == "394579002"
        assert result["reasonCode"][0]["coding"][0]["code"] == "390906007"
        assert result["minutesDuration"] == 60
        assert result["priority"] == 5
        assert len(result["participant"]) == 3  # Patient + Practitioner + Location

    def test_appointment_with_multiple_participants(self, factory):
        """Test Appointment with multiple custom participants"""

        appointment_data = {
            "status": "booked",
            "participants": [
                {
                    "actor_ref": "RelatedPerson/spouse-789",
                    "type": "relative",
                    "required": "optional",
                    "status": "accepted"
                },
                {
                    "actor_ref": "Practitioner/nurse-123",
                    "type": "practitioner",
                    "required": "required",
                    "status": "tentative"
                }
            ],
            "requested_period": [
                {
                    "start": "2024-02-15T09:00:00Z",
                    "end": "2024-02-15T17:00:00Z"
                }
            ]
        }

        result = factory.create_appointment_resource(
            appointment_data,
            "Patient/patient-123"
        )

        # Should have patient + 2 custom participants = 3 total
        assert len(result["participant"]) == 3
        custom_participants = [p for p in result["participant"]
                             if p.get("actor", {}).get("reference") != "Patient/patient-123"]
        assert len(custom_participants) == 2

    # =================================================================
    # Epic 7 Integration Tests
    # =================================================================

    def test_epic7_laboratory_workflow_integration(self, factory):
        """Test complete laboratory workflow with Specimen + Appointment"""

        # Create appointment for lab collection
        appointment_data = {
            "status": "booked",
            "appointment_type": "routine",
            "service_type": "diagnostic",
            "reason_code": "diagnostic",
            "start": "2024-02-15T08:00:00Z",
            "duration_minutes": 15
        }

        appointment = factory.create_appointment_resource(
            appointment_data,
            "Patient/patient-123",
            practitioner_ref="Practitioner/lab-tech-456"
        )

        # Create specimen collected during appointment
        specimen_data = {
            "type": "blood",
            "collection": {
                "collected_date": "2024-02-15T08:10:00Z",
                "site": "left arm",
                "method": "venipuncture",
                "collector_ref": "Practitioner/lab-tech-456"
            },
            "container": {
                "type": "red top",
                "capacity": {"value": 10, "unit": "mL"}
            }
        }

        specimen = factory.create_specimen_resource(
            specimen_data,
            "Patient/patient-123",
            service_request_ref="ServiceRequest/cbc-order"
        )

        # Verify integration
        assert appointment["serviceType"][0]["coding"][0]["code"] == "103693007"
        assert specimen["collection"]["collector"]["reference"] == "Practitioner/lab-tech-456"
        assert specimen["request"][0]["reference"] == "ServiceRequest/cbc-order"

    def test_epic7_insurance_appointment_integration(self, factory):
        """Test insurance verification with appointment booking"""

        # Create coverage for insurance verification
        coverage_data = {
            "type": "medical",
            "status": "active",
            "subscriber_id": "SUB789",
            "payor": {
                "id": "united-healthcare",
                "name": "United Healthcare"
            },
            "cost_to_beneficiary": [
                {
                    "type": "copay",
                    "value": {"amount": 30.00, "currency": "USD"}
                }
            ]
        }

        coverage = factory.create_coverage_resource(
            coverage_data,
            "Patient/patient-123"
        )

        # Create appointment with coverage context
        appointment_data = {
            "status": "booked",
            "appointment_type": "routine",
            "service_category": "primary care",
            "start": "2024-02-20T10:00:00Z",
            "duration_minutes": 30
        }

        appointment = factory.create_appointment_resource(
            appointment_data,
            "Patient/patient-123",
            practitioner_ref="Practitioner/pcp-doctor"
        )

        # Verify integration
        assert coverage["status"] == "active"
        assert coverage["costToBeneficiary"][0]["valueMoney"]["value"] == 30.00
        assert appointment["serviceCategory"][0]["text"] == "primary care"

    def test_epic7_complete_outpatient_workflow(self, factory):
        """Test complete outpatient workflow: Coverage + Appointment + Specimen"""

        patient_ref = "Patient/patient-123"

        # 1. Insurance coverage verification
        coverage_data = {
            "type": "medical",
            "status": "active",
            "class": [
                {
                    "type": "plan",
                    "value": "PPO-PREMIUM",
                    "name": "Premium PPO Plan"
                }
            ]
        }

        coverage = factory.create_coverage_resource(coverage_data, patient_ref)

        # 2. Schedule appointment
        appointment_data = {
            "status": "booked",
            "appointment_type": "consultation",
            "specialty": "endocrinology",
            "reason_code": "follow up",
            "start": "2024-03-01T14:00:00Z",
            "duration_minutes": 45
        }

        appointment = factory.create_appointment_resource(
            appointment_data,
            patient_ref,
            practitioner_ref="Practitioner/endocrinologist-789"
        )

        # 3. Collect specimen during visit
        specimen_data = {
            "type": "blood",
            "collection": {
                "collected_date": "2024-03-01T14:30:00Z",
                "site": "right arm",
                "method": "venipuncture"
            },
            "processing": [
                {
                    "procedure": "centrifugation",
                    "description": "Separate serum for hormone analysis"
                }
            ]
        }

        specimen = factory.create_specimen_resource(
            specimen_data,
            patient_ref,
            service_request_ref="ServiceRequest/hormone-panel"
        )

        # Verify complete workflow
        assert coverage["class"][0]["value"] == "PPO-PREMIUM"
        assert appointment["specialty"][0]["coding"][0]["display"] == "Endocrinology"
        assert specimen["processing"][0]["procedure"]["coding"][0]["display"] == "Centrifugation"

        # All resources reference same patient
        assert coverage["beneficiary"]["reference"] == patient_ref
        assert appointment["participant"][0]["actor"]["reference"] == patient_ref
        assert specimen["subject"]["reference"] == patient_ref

    # =================================================================
    # FHIR Validation Tests
    # =================================================================

    def test_epic7_resources_fhir_compliance(self, factory):
        """Test that all Epic 7 resources meet FHIR R4 compliance"""

        patient_ref = "Patient/test-patient"

        # Test Specimen compliance
        specimen = factory.create_specimen_resource(
            {"type": "blood", "status": "available"},
            patient_ref
        )

        assert "resourceType" in specimen
        assert "id" in specimen
        assert "status" in specimen
        assert "subject" in specimen

        # Test Coverage compliance
        coverage = factory.create_coverage_resource(
            {"type": "medical", "status": "active"},
            patient_ref
        )

        assert "resourceType" in coverage
        assert "id" in coverage
        assert "status" in coverage
        assert "beneficiary" in coverage

        # Test Appointment compliance
        appointment = factory.create_appointment_resource(
            {"status": "proposed"},
            patient_ref
        )

        assert "resourceType" in appointment
        assert "id" in appointment
        assert "status" in appointment
        assert "participant" in appointment

    def test_epic7_fallback_mode(self, factory):
        """Test Epic 7 resources in fallback mode when FHIR library unavailable"""

        with patch('src.nl_fhir.services.fhir.resource_factory.FHIR_AVAILABLE', False):

            # Test fallback Specimen
            specimen = factory.create_specimen_resource(
                {"type": "urine", "status": "available"},
                "Patient/patient-123"
            )

            assert specimen["resourceType"] == "Specimen"
            assert specimen["type"]["text"] == "urine"

            # Test fallback Coverage
            coverage = factory.create_coverage_resource(
                {"type": "dental", "status": "active"},
                "Patient/patient-123"
            )

            assert coverage["resourceType"] == "Coverage"
            assert coverage["type"]["text"] == "dental"

            # Test fallback Appointment
            appointment = factory.create_appointment_resource(
                {"status": "booked", "description": "Dental cleaning"},
                "Patient/patient-123"
            )

            assert appointment["resourceType"] == "Appointment"
            assert appointment["description"] == "Dental cleaning"

    # =================================================================
    # Performance and Error Handling Tests
    # =================================================================

    def test_epic7_error_handling(self, factory):
        """Test Epic 7 resource error handling and graceful degradation"""

        # Test with invalid data - should not crash
        try:
            specimen = factory.create_specimen_resource(
                {"invalid_field": "bad_data"},
                "Patient/patient-123"
            )
            assert specimen["resourceType"] == "Specimen"  # Should still create basic resource
        except Exception as e:
            pytest.fail(f"Should handle invalid data gracefully: {e}")

        # Test with missing required references
        try:
            appointment = factory.create_appointment_resource(
                {"status": "booked"},
                ""  # Empty patient reference
            )
            # Should handle gracefully or use fallback
            assert "participant" in appointment
        except Exception as e:
            pytest.fail(f"Should handle missing references gracefully: {e}")

    def test_epic7_resource_performance(self, factory):
        """Test Epic 7 resource creation performance for multiple resources"""

        import time

        start_time = time.time()

        # Create multiple resources rapidly
        for i in range(10):
            factory.create_specimen_resource(
                {"type": "blood", "status": "available"},
                f"Patient/patient-{i}"
            )

            factory.create_coverage_resource(
                {"type": "medical", "status": "active"},
                f"Patient/patient-{i}"
            )

            factory.create_appointment_resource(
                {"status": "booked"},
                f"Patient/patient-{i}"
            )

        end_time = time.time()
        total_time = end_time - start_time

        # Should create 30 resources in under 1 second
        assert total_time < 1.0, f"Performance issue: {total_time}s for 30 resources"

        # Average should be well under 50ms per resource
        avg_time = total_time / 30
        assert avg_time < 0.05, f"Average creation time too slow: {avg_time}s per resource"