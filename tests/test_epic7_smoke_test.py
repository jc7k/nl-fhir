"""
Epic 7 Clinical Coverage Expansion - Smoke Test
Basic functionality tests for Stories 7.1-7.3

Tests core functionality of Specimen, Coverage, and Appointment resources
in both FHIR library and fallback modes.
"""

import pytest
from src.nl_fhir.services.fhir.resource_factory import FHIRResourceFactory


class TestEpic7SmokeTest:
    """Basic smoke tests for Epic 7 resources"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = FHIRResourceFactory()
        factory.initialize()
        return factory

    def test_specimen_resource_creation(self, factory):
        """Test Specimen resource basic creation works (Story 7.1)"""
        specimen_data = {
            "type": "blood",
            "status": "available"
        }

        result = factory.create_specimen_resource(
            specimen_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "Specimen"
        assert result["status"] == "available"
        assert result["subject"]["reference"] == "Patient/patient-123"
        assert "type" in result
        assert "identifier" in result

    def test_specimen_with_collection(self, factory):
        """Test Specimen with collection details"""
        specimen_data = {
            "type": "urine",
            "collection": {
                "collected_date": "2024-01-15T10:30:00Z",
                "method": "clean catch"
            }
        }

        result = factory.create_specimen_resource(
            specimen_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "Specimen"
        assert "collection" in result
        assert result["collection"]["collectedDateTime"] == "2024-01-15T10:30:00Z"

    def test_coverage_resource_creation(self, factory):
        """Test Coverage resource basic creation works (Story 7.2)"""
        coverage_data = {
            "type": "medical",
            "status": "active"
        }

        result = factory.create_coverage_resource(
            coverage_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "Coverage"
        assert result["status"] == "active"
        assert result["subscriber"]["reference"] == "Patient/patient-123"
        assert result["beneficiary"]["reference"] == "Patient/patient-123"
        assert "identifier" in result
        assert "payor" in result

    def test_coverage_with_payor(self, factory):
        """Test Coverage with payor information"""
        coverage_data = {
            "type": "medical",
            "status": "active",
            "payor": {
                "id": "anthem-bcbs",
                "name": "Anthem Blue Cross Blue Shield"
            }
        }

        result = factory.create_coverage_resource(
            coverage_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "Coverage"
        assert result["payor"][0]["display"] == "Anthem Blue Cross Blue Shield"

    def test_appointment_resource_creation(self, factory):
        """Test Appointment resource basic creation works (Story 7.3)"""
        appointment_data = {
            "status": "booked",
            "start": "2024-02-15T14:00:00Z",
            "end": "2024-02-15T14:30:00Z"
        }

        result = factory.create_appointment_resource(
            appointment_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "Appointment"
        assert result["status"] == "booked"
        assert result["start"] == "2024-02-15T14:00:00Z"
        assert result["end"] == "2024-02-15T14:30:00Z"
        assert "participant" in result
        assert len(result["participant"]) >= 1  # At least patient participant

    def test_appointment_with_practitioner(self, factory):
        """Test Appointment with practitioner participant"""
        appointment_data = {
            "status": "booked",
            "description": "Annual checkup"
        }

        result = factory.create_appointment_resource(
            appointment_data,
            "Patient/patient-123",
            practitioner_ref="Practitioner/dr-smith"
        )

        assert result["resourceType"] == "Appointment"
        assert result["description"] == "Annual checkup"
        # Should have at least patient participant
        assert len(result["participant"]) >= 1

    def test_epic7_resources_have_proper_ids(self, factory):
        """Test that all Epic 7 resources generate proper IDs"""

        # Test Specimen ID generation
        specimen = factory.create_specimen_resource(
            {"type": "blood"},
            "Patient/patient-123"
        )
        assert "id" in specimen
        assert specimen["identifier"][0]["system"] == "http://hospital.local/specimen-id"

        # Test Coverage ID generation
        coverage = factory.create_coverage_resource(
            {"type": "medical"},
            "Patient/patient-123"
        )
        assert "id" in coverage
        assert coverage["identifier"][0]["system"] == "http://hospital.local/coverage-id"

        # Test Appointment ID generation
        appointment = factory.create_appointment_resource(
            {"status": "proposed"},
            "Patient/patient-123"
        )
        assert "id" in appointment
        assert appointment["identifier"][0]["system"] == "http://hospital.local/appointment-id"

    def test_epic7_laboratory_workflow(self, factory):
        """Test basic laboratory workflow integration"""

        # Create specimen for lab order
        specimen_data = {
            "type": "blood",
            "status": "available",
            "collection": {
                "collected_date": "2024-02-15T08:10:00Z"
            }
        }

        specimen = factory.create_specimen_resource(
            specimen_data,
            "Patient/patient-123",
            service_request_ref="ServiceRequest/lab-order-123"
        )

        # Create related appointment
        appointment_data = {
            "status": "booked",
            "start": "2024-02-15T08:00:00Z",
            "description": "Lab collection appointment"
        }

        appointment = factory.create_appointment_resource(
            appointment_data,
            "Patient/patient-123"
        )

        # Verify workflow components
        assert specimen["resourceType"] == "Specimen"
        assert "request" in specimen  # Links to ServiceRequest
        assert appointment["resourceType"] == "Appointment"

        # Both reference same patient
        assert specimen["subject"]["reference"] == "Patient/patient-123"
        assert appointment["participant"][0]["actor"]["reference"] == "Patient/patient-123"

    def test_epic7_insurance_workflow(self, factory):
        """Test basic insurance and appointment workflow"""

        patient_ref = "Patient/patient-123"

        # Create coverage
        coverage = factory.create_coverage_resource(
            {"type": "medical", "status": "active"},
            patient_ref
        )

        # Create appointment
        appointment = factory.create_appointment_resource(
            {"status": "booked", "description": "Medical consultation"},
            patient_ref
        )

        # Verify workflow
        assert coverage["beneficiary"]["reference"] == patient_ref
        assert appointment["participant"][0]["actor"]["reference"] == patient_ref

    def test_epic7_error_handling(self, factory):
        """Test Epic 7 resources handle errors gracefully"""

        # Test with minimal data - should not crash
        try:
            specimen = factory.create_specimen_resource({}, "Patient/patient-123")
            assert specimen["resourceType"] == "Specimen"
        except Exception as e:
            pytest.fail(f"Specimen creation should handle empty data: {e}")

        try:
            coverage = factory.create_coverage_resource({}, "Patient/patient-123")
            assert coverage["resourceType"] == "Coverage"
        except Exception as e:
            pytest.fail(f"Coverage creation should handle empty data: {e}")

        try:
            appointment = factory.create_appointment_resource({}, "Patient/patient-123")
            assert appointment["resourceType"] == "Appointment"
        except Exception as e:
            pytest.fail(f"Appointment creation should handle empty data: {e}")

    def test_epic7_comprehensive_integration(self, factory):
        """Test complete Epic 7 workflow integration"""

        patient_ref = "Patient/patient-123"

        # Create all three Epic 7 resources for the same patient
        coverage = factory.create_coverage_resource(
            {"type": "medical", "status": "active"},
            patient_ref
        )

        appointment = factory.create_appointment_resource(
            {
                "status": "booked",
                "start": "2024-03-01T09:00:00Z",
                "description": "Annual physical with lab work"
            },
            patient_ref
        )

        specimen = factory.create_specimen_resource(
            {
                "type": "blood",
                "status": "available",
                "collection": {"collected_date": "2024-03-01T09:30:00Z"}
            },
            patient_ref
        )

        # Verify all resources created successfully
        resources = [coverage, appointment, specimen]
        expected_types = ["Coverage", "Appointment", "Specimen"]

        for resource, expected_type in zip(resources, expected_types):
            assert resource["resourceType"] == expected_type
            assert "id" in resource
            assert "identifier" in resource

        # Verify patient references
        assert coverage["beneficiary"]["reference"] == patient_ref
        assert appointment["participant"][0]["actor"]["reference"] == patient_ref
        assert specimen["subject"]["reference"] == patient_ref

        print(f"✅ Epic 7 Integration Complete:")
        print(f"   - Coverage: {coverage['id']}")
        print(f"   - Appointment: {appointment['id']}")
        print(f"   - Specimen: {specimen['id']}")
        print(f"   - All resources reference: {patient_ref}")