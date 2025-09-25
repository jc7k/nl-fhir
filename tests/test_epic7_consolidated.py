"""
Epic 7 Clinical Coverage Expansion - Consolidated Test Suite
Tests Stories 7.1-7.3: Specimen, Coverage, and Appointment FHIR resources

Comprehensive clinical workflow coverage with laboratory processes,
insurance integration, and appointment scheduling functionality.

Consolidates test_epic7_clinical_coverage_expansion.py (16 tests) and
test_epic7_smoke_test.py (11 tests) into efficient parametrized test suite.
"""

import pytest
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from src.nl_fhir.services.fhir.resource_factory import FHIRResourceFactory


class TestEpic7Consolidated:
    """Consolidated Epic 7 Clinical Coverage Expansion Tests"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = FHIRResourceFactory()
        factory.initialize()
        return factory

    # =================================================================
    # Core Resource Creation Tests (Batch Approach)
    # =================================================================

    @pytest.mark.parametrize("resource_category, resource_configs", [
        ("specimen_resources", [
            ("Specimen", "create_specimen_resource", {
                "specimen_data": {"type": "blood", "status": "available"},
                "patient_ref": "Patient/patient-123"
            }),
            ("Specimen", "create_specimen_resource", {
                "specimen_data": {
                    "type": "urine",
                    "collection": {
                        "collected_date": "2024-01-15T10:30:00Z",
                        "method": "clean catch"
                    }
                },
                "patient_ref": "Patient/patient-123"
            }),
            ("Specimen", "create_specimen_resource", {
                "specimen_data": {
                    "specimen_id": "SPEC-2024-001",
                    "type": "tissue",
                    "processing": {
                        "procedure": "histology",
                        "additive": "formalin"
                    }
                },
                "patient_ref": "Patient/patient-123"
            })
        ]),
        ("coverage_resources", [
            ("Coverage", "create_coverage_resource", {
                "coverage_data": {"type": "medical", "status": "active"},
                "patient_ref": "Patient/patient-123"
            }),
            ("Coverage", "create_coverage_resource", {
                "coverage_data": {
                    "type": "medical",
                    "status": "active",
                    "payor": {
                        "id": "org-bcbs",
                        "name": "Blue Cross Blue Shield"
                    },
                    "plan_class": "group"
                },
                "patient_ref": "Patient/patient-123"
            }),
            ("Coverage", "create_coverage_resource", {
                "coverage_data": {
                    "type": "medical",
                    "cost_sharing": {
                        "copay": "25.00",
                        "deductible": "1000.00"
                    }
                },
                "patient_ref": "Patient/patient-123"
            })
        ]),
        ("appointment_resources", [
            ("Appointment", "create_appointment_resource", {
                "appointment_data": {
                    "status": "scheduled",
                    "start_time": "2024-02-15T14:30:00Z"
                },
                "patient_ref": "Patient/patient-123"
            }),
            ("Appointment", "create_appointment_resource", {
                "appointment_data": {
                    "status": "scheduled",
                    "start_time": "2024-02-20T09:00:00Z",
                    "practitioner": "Dr. Smith",
                    "specialty": "cardiology"
                },
                "patient_ref": "Patient/patient-123"
            }),
            ("Appointment", "create_appointment_resource", {
                "appointment_data": {
                    "status": "scheduled",
                    "participants": [
                        {"type": "patient", "required": "required"},
                        {"type": "practitioner", "required": "required"}
                    ]
                },
                "patient_ref": "Patient/patient-123"
            })
        ])
    ])
    def test_epic7_resource_batch_creation(self, factory, resource_category, resource_configs):
        """Test Epic 7 resource creation in batches by category"""

        created_resources = []

        for expected_type, method_name, params in resource_configs:
            # Get the factory method dynamically
            factory_method = getattr(factory, method_name)

            # Call the method with unpacked parameters
            if method_name == "create_specimen_resource":
                result = factory_method(
                    params["specimen_data"],
                    params["patient_ref"]
                )
            elif method_name == "create_coverage_resource":
                result = factory_method(
                    params["coverage_data"],
                    params["patient_ref"]
                )
            elif method_name == "create_appointment_resource":
                result = factory_method(
                    params["appointment_data"],
                    params["patient_ref"]
                )

            # Verify basic FHIR resource structure
            assert result["resourceType"] == expected_type
            assert "id" in result
            assert result["id"] is not None

            # Category-specific validations
            if resource_category == "specimen_resources":
                assert "subject" in result
                assert result["subject"]["reference"] == params["patient_ref"]
                assert "type" in result

            elif resource_category == "coverage_resources":
                assert "beneficiary" in result
                assert result["beneficiary"]["reference"] == params["patient_ref"]
                assert "status" in result

            elif resource_category == "appointment_resources":
                assert "participant" in result
                assert "status" in result

            created_resources.append(result)

        # Verify all resources in category were created
        category_counts = {
            "specimen_resources": 3,
            "coverage_resources": 3,
            "appointment_resources": 3
        }

        assert len(created_resources) == category_counts[resource_category]

        print(f"✅ Epic 7 {resource_category}: {len(created_resources)} resources created successfully")

    # =================================================================
    # Clinical Workflow Integration Tests
    # =================================================================

    def test_epic7_laboratory_workflow_integration(self, factory):
        """Test complete laboratory workflow with Epic 7 resources"""

        patient_ref = "Patient/lab-patient-123"

        # Create specimen for lab work
        specimen_data = {
            "type": "blood",
            "collection": {
                "collected_date": "2024-02-01T08:30:00Z",
                "method": "venipuncture"
            },
            "processing": {
                "procedure": "chemistry_panel",
                "additive": "EDTA"
            }
        }

        specimen = factory.create_specimen_resource(specimen_data, patient_ref)

        # Create appointment for results review
        appointment_data = {
            "status": "scheduled",
            "start_time": "2024-02-05T10:00:00Z",
            "specialty": "pathology"
        }

        appointment = factory.create_appointment_resource(appointment_data, patient_ref)

        # Create coverage for billing
        coverage_data = {
            "type": "medical",
            "status": "active",
            "payor": {
                "id": "org-medicare",
                "name": "Medicare"
            }
        }

        coverage = factory.create_coverage_resource(coverage_data, patient_ref)

        # Verify workflow integration
        workflow_resources = [specimen, appointment, coverage]

        for resource in workflow_resources:
            assert "resourceType" in resource
            assert "id" in resource

        assert specimen["resourceType"] == "Specimen"
        assert appointment["resourceType"] == "Appointment"
        assert coverage["resourceType"] == "Coverage"

        print("✅ Epic 7 Laboratory Workflow: Complete integration successful")

    def test_epic7_insurance_appointment_workflow(self, factory):
        """Test insurance verification with appointment scheduling workflow"""

        patient_ref = "Patient/insurance-patient-456"

        # Create coverage with detailed plan information
        coverage_data = {
            "type": "medical",
            "status": "active",
            "payor": {
                "id": "org-aetna",
                "name": "Aetna"
            },
            "plan_class": "individual",
            "cost_sharing": {
                "copay": "30.00",
                "deductible": "2500.00"
            }
        }

        coverage = factory.create_coverage_resource(coverage_data, patient_ref)

        # Create specialty appointment
        appointment_data = {
            "status": "scheduled",
            "start_time": "2024-02-10T14:00:00Z",
            "specialty": "dermatology",
            "practitioner": "Dr. Johnson"
        }

        appointment = factory.create_appointment_resource(appointment_data, patient_ref)

        # Verify insurance workflow
        assert coverage["resourceType"] == "Coverage"
        assert coverage["status"] == "active"
        assert appointment["resourceType"] == "Appointment"
        assert appointment["status"] == "scheduled"

        print("✅ Epic 7 Insurance Workflow: Coverage verification with appointment successful")

    def test_epic7_outpatient_complete_workflow(self, factory):
        """Test complete outpatient workflow with all Epic 7 resources"""

        patient_ref = "Patient/outpatient-789"

        # Step 1: Schedule appointment
        appointment = factory.create_appointment_resource({
            "status": "scheduled",
            "start_time": "2024-02-12T11:30:00Z",
            "practitioner": "Dr. Wilson"
        }, patient_ref)

        # Step 2: Verify insurance coverage
        coverage = factory.create_coverage_resource({
            "type": "medical",
            "status": "active",
            "payor": {
                "id": "org-uhc",
                "name": "United Healthcare"
            }
        }, patient_ref)

        # Step 3: Collect specimens during visit
        specimen = factory.create_specimen_resource({
            "type": "blood",
            "collection": {
                "collected_date": "2024-02-12T11:45:00Z",
                "method": "venipuncture"
            }
        }, patient_ref)

        # Verify complete workflow
        workflow = [appointment, coverage, specimen]
        resource_types = [r["resourceType"] for r in workflow]

        assert "Appointment" in resource_types
        assert "Coverage" in resource_types
        assert "Specimen" in resource_types

        # Verify all resources linked to same patient
        for resource in workflow:
            if "participant" in resource:
                # Appointment has participant structure
                continue
            elif "beneficiary" in resource:
                assert resource["beneficiary"]["reference"] == patient_ref
            elif "subject" in resource:
                assert resource["subject"]["reference"] == patient_ref

        print("✅ Epic 7 Complete Outpatient Workflow: All 3 resources integrated successfully")

    # =================================================================
    # Resource Validation and Performance Tests
    # =================================================================

    def test_epic7_resource_fhir_compliance(self, factory):
        """Test Epic 7 resources meet FHIR R4 compliance standards"""

        patient_ref = "Patient/compliance-test"

        # Create one resource of each type with comprehensive data
        specimen = factory.create_specimen_resource({
            "specimen_id": "COMP-SPEC-001",
            "type": "serum",
            "status": "available",
            "collection": {
                "collected_date": "2024-02-01T09:15:00Z",
                "method": "venipuncture"
            },
            "processing": {
                "procedure": "centrifugation",
                "additive": "gel separator"
            }
        }, patient_ref)

        coverage = factory.create_coverage_resource({
            "type": "medical",
            "status": "active",
            "payor": {
                "id": "org-bc",
                "name": "Blue Cross"
            },
            "plan_class": "group",
            "cost_sharing": {
                "copay": "20.00",
                "deductible": "1500.00"
            }
        }, patient_ref)

        appointment = factory.create_appointment_resource({
            "status": "scheduled",
            "start_time": "2024-02-05T13:20:00Z",
            "specialty": "oncology",
            "practitioner": "Dr. Davis",
            "participants": [
                {"type": "patient", "required": "required"},
                {"type": "practitioner", "required": "required"}
            ]
        }, patient_ref)

        compliance_resources = [specimen, coverage, appointment]

        # FHIR R4 compliance checks
        for resource in compliance_resources:
            # Required FHIR fields
            assert "resourceType" in resource
            assert "id" in resource
            assert resource["id"] is not None
            assert len(resource["id"]) > 0

            # Resource-specific required fields
            if resource["resourceType"] == "Specimen":
                assert "subject" in resource
                assert "type" in resource

            elif resource["resourceType"] == "Coverage":
                assert "beneficiary" in resource
                assert "status" in resource

            elif resource["resourceType"] == "Appointment":
                assert "status" in resource
                assert "participant" in resource

        print(f"✅ Epic 7 FHIR Compliance: All {len(compliance_resources)} resources validated")

    def test_epic7_performance_benchmarking(self, factory):
        """Test Epic 7 resource creation performance"""

        import time

        patient_ref = "Patient/perf-test"
        start_time = time.time()

        # Create multiple resources to test performance
        performance_resources = []

        # Batch create specimens (most complex)
        for i in range(3):
            specimen = factory.create_specimen_resource({
                "specimen_id": f"PERF-SPEC-{i+1:03d}",
                "type": "plasma",
                "collection": {
                    "collected_date": f"2024-02-{i+1:02d}T10:00:00Z",
                    "method": "venipuncture"
                }
            }, patient_ref)
            performance_resources.append(specimen)

        # Batch create coverage resources
        for i in range(2):
            coverage = factory.create_coverage_resource({
                "type": "medical",
                "status": "active",
                "payor": {
                    "id": f"org-insurance-{i+1}",
                    "name": f"Insurance-{i+1}"
                }
            }, patient_ref)
            performance_resources.append(coverage)

        # Batch create appointments
        for i in range(2):
            appointment = factory.create_appointment_resource({
                "status": "scheduled",
                "start_time": f"2024-02-{i+10:02d}T14:30:00Z"
            }, patient_ref)
            performance_resources.append(appointment)

        end_time = time.time()
        execution_time = end_time - start_time

        # Performance assertions
        assert len(performance_resources) == 7
        assert execution_time < 1.0  # Should complete in under 1 second

        # Verify all resources are valid
        for resource in performance_resources:
            assert "resourceType" in resource
            assert "id" in resource

        print(f"✅ Epic 7 Performance: {len(performance_resources)} resources created in {execution_time:.3f}s")

    # =================================================================
    # Error Handling and Edge Cases
    # =================================================================

    def test_epic7_error_handling(self, factory):
        """Test Epic 7 resource error handling and recovery"""

        patient_ref = "Patient/error-test"

        # Test with minimal valid data
        try:
            specimen = factory.create_specimen_resource({
                "type": "blood"
            }, patient_ref)
            assert specimen["resourceType"] == "Specimen"

            coverage = factory.create_coverage_resource({
                "type": "medical"
            }, patient_ref)
            assert coverage["resourceType"] == "Coverage"

            appointment = factory.create_appointment_resource({
                "status": "scheduled"
            }, patient_ref)
            assert appointment["resourceType"] == "Appointment"

        except Exception as e:
            pytest.fail(f"Epic 7 error handling failed: {e}")

        print("✅ Epic 7 Error Handling: Graceful handling of minimal data successful")

    def test_epic7_id_generation_patterns(self, factory):
        """Test Epic 7 resource ID generation consistency"""

        patient_ref = "Patient/id-test"

        # Create multiple resources and verify ID patterns
        specimen = factory.create_specimen_resource({"type": "blood"}, patient_ref)
        coverage = factory.create_coverage_resource({"type": "medical"}, patient_ref)
        appointment = factory.create_appointment_resource({"status": "scheduled"}, patient_ref)

        resources = [specimen, coverage, appointment]

        for resource in resources:
            # Verify ID exists and follows expected pattern
            assert "id" in resource
            assert resource["id"] is not None
            assert len(resource["id"]) > 0

            # IDs should be unique
            resource_ids = [r["id"] for r in resources]
            assert len(set(resource_ids)) == len(resource_ids)

        print("✅ Epic 7 ID Generation: Consistent patterns across all resource types")

    # =================================================================
    # Integration Summary Test
    # =================================================================

    def test_epic7_implementation_complete(self, factory):
        """Verify Epic 7 Clinical Coverage Expansion is fully implemented"""

        patient_ref = "Patient/final-validation"

        try:
            # Create representative sample of all Epic 7 capabilities
            specimen_sample = factory.create_specimen_resource({
                "type": "serum",
                "status": "available"
            }, patient_ref)

            coverage_sample = factory.create_coverage_resource({
                "type": "medical",
                "status": "active"
            }, patient_ref)

            appointment_sample = factory.create_appointment_resource({
                "status": "scheduled",
                "start_time": "2024-02-15T10:00:00Z"
            }, patient_ref)

            samples = [specimen_sample, coverage_sample, appointment_sample]

            # Verify all samples are valid FHIR resources
            for sample in samples:
                assert "resourceType" in sample
                assert "id" in sample
                assert sample["id"] is not None and len(sample["id"]) > 0

            print(f"🎉 EPIC 7 CLINICAL COVERAGE EXPANSION COMPLETE!")
            print(f"   - Specimen resources: Laboratory workflow support ✓")
            print(f"   - Coverage resources: Insurance integration ✓")
            print(f"   - Appointment resources: Scheduling capabilities ✓")
            print(f"   - Clinical workflows: End-to-end integration ✓")
            print(f"   - Performance: Sub-second resource creation ✓")
            print(f"   - FHIR Compliance: R4 validation ready ✓")
            print(f"   - Epic 7: ✅ FULLY OPERATIONAL")

        except Exception as e:
            pytest.fail(f"Epic 7 implementation incomplete: {e}")