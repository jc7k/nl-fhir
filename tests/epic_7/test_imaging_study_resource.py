"""
Epic 7.8: ImagingStudy Resource Tests
Tests for ImagingStudy resource implementation - diagnostic imaging study management

Validates FHIR R4 compliance, DICOM integration, and imaging workflow management.
"""

import pytest
from datetime import datetime
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


class TestImagingStudyResource:
    """Test Epic 7.8: ImagingStudy Resource Implementation"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    # =================================================================
    # Story 7.8: Basic ImagingStudy Resource Tests
    # =================================================================

    def test_imaging_study_basic_creation(self, factory):
        """Test basic ImagingStudy resource creation (Story 7.8)"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:30:00Z"
        }

        patient_ref = "Patient/patient-123"

        result = factory.create_imaging_study_resource(
            imaging_data,
            patient_ref,
            request_id="req-img-001"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert result["status"] == "available"
        assert result["subject"]["reference"] == patient_ref
        assert result["started"] == "2024-12-01T10:30:00Z"

    def test_imaging_study_with_status(self, factory):
        """Test ImagingStudy with different statuses"""

        statuses = ["registered", "available", "cancelled"]

        for status in statuses:
            imaging_data = {
                "status": status,
                "started": "2024-12-01T10:00:00Z"
            }

            result = factory.create_imaging_study_resource(
                imaging_data,
                "Patient/patient-status-test"
            )

            assert result["resourceType"] == "ImagingStudy"
            assert result["status"] == status

    def test_imaging_study_with_started_datetime(self, factory):
        """Test ImagingStudy with started datetime"""

        started_time = datetime.utcnow().isoformat() + 'Z'

        imaging_data = {
            "status": "available",
            "started": started_time
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-started"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert result["started"] == started_time

    # =================================================================
    # Series Tests
    # =================================================================

    def test_imaging_study_with_single_series(self, factory):
        """Test ImagingStudy with single series"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:30:00Z",
            "series": [{
                "modality": "CT",
                "description": "Chest CT",
                "numberOfInstances": 150
            }]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-series"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "series" in result
        assert len(result["series"]) == 1
        assert result["numberOfSeries"] == 1
        assert result["numberOfInstances"] == 150

    def test_imaging_study_with_multiple_series(self, factory):
        """Test ImagingStudy with multiple series"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T14:00:00Z",
            "series": [
                {
                    "uid": "2.25.123456789",
                    "modality": "MR",
                    "description": "T1-weighted",
                    "numberOfInstances": 180
                },
                {
                    "uid": "2.25.987654321",
                    "modality": "MR",
                    "description": "T2-weighted",
                    "numberOfInstances": 180
                }
            ]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-multi-series"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert len(result["series"]) == 2
        assert result["numberOfSeries"] == 2
        assert result["numberOfInstances"] == 360

    def test_imaging_study_modality_types(self, factory):
        """Test ImagingStudy with different modality types"""

        modalities = ["CT", "MR", "XR", "US", "DX", "MG", "PT", "NM"]

        for modality in modalities:
            imaging_data = {
                "status": "available",
                "started": "2024-12-01T10:00:00Z",
                "series": [{
                    "modality": modality,
                    "numberOfInstances": 100
                }]
            }

            result = factory.create_imaging_study_resource(
                imaging_data,
                "Patient/patient-modality-test"
            )

            assert result["resourceType"] == "ImagingStudy"
            assert len(result["series"]) > 0
            # Check that modality was processed
            if "modality" in result["series"][0]:
                assert "system" in result["series"][0]["modality"]

    def test_imaging_study_series_with_body_site(self, factory):
        """Test ImagingStudy series with body site"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "series": [{
                "modality": "CT",
                "description": "Brain CT",
                "numberOfInstances": 200,
                "bodySite": "Brain"
            }]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-body-site"
        )

        assert result["resourceType"] == "ImagingStudy"
        if "series" in result and result["series"]:
            if "bodySite" in result["series"][0]:
                assert result["series"][0]["bodySite"] is not None

    def test_imaging_study_series_auto_uid_generation(self, factory):
        """Test ImagingStudy auto-generates DICOM UIDs"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "series": [{
                "modality": "CT",
                "numberOfInstances": 100
                # No UID provided - should auto-generate
            }]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-auto-uid"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert len(result["series"]) > 0
        assert "uid" in result["series"][0]
        # DICOM UID should start with 2.25.
        assert result["series"][0]["uid"].startswith("2.25.")

    # =================================================================
    # Clinical Context Tests
    # =================================================================

    def test_imaging_study_with_encounter(self, factory):
        """Test ImagingStudy linked to encounter"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "encounter": "Encounter/encounter-001"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-encounter"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "encounter" in result
        assert "Encounter" in result["encounter"]["reference"]

    def test_imaging_study_with_based_on(self, factory):
        """Test ImagingStudy based on ServiceRequest"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "basedOn": ["ServiceRequest/imaging-order-123"]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-based-on"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "basedOn" in result
        assert len(result["basedOn"]) > 0

    def test_imaging_study_with_referrer(self, factory):
        """Test ImagingStudy with referring physician"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "referrer": "Practitioner/referring-physician-456"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-referrer"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "referrer" in result
        assert "Practitioner" in result["referrer"]["reference"]

    def test_imaging_study_with_endpoint(self, factory):
        """Test ImagingStudy with PACS endpoint"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "endpoint": ["Endpoint/pacs-endpoint-1"]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-endpoint"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "endpoint" in result
        assert len(result["endpoint"]) > 0

    # =================================================================
    # Procedure Tests
    # =================================================================

    def test_imaging_study_with_procedure_code(self, factory):
        """Test ImagingStudy with procedure code"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "procedureCode": "CT chest with contrast"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-proc-code"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "procedureCode" in result

    def test_imaging_study_with_procedure_reference(self, factory):
        """Test ImagingStudy with procedure reference"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "procedureReference": "Procedure/ct-chest-001"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-proc-ref"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "procedureReference" in result

    # =================================================================
    # Reason Tests
    # =================================================================

    def test_imaging_study_with_reason_code(self, factory):
        """Test ImagingStudy with reason code"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "reasonCode": ["Suspected pulmonary embolism"]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-reason-code"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "reasonCode" in result
        assert len(result["reasonCode"]) > 0

    def test_imaging_study_with_reason_reference(self, factory):
        """Test ImagingStudy with reason reference"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "reasonReference": ["Condition/suspected-pe-001"]
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-reason-ref"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "reasonReference" in result
        assert len(result["reasonReference"]) > 0

    # =================================================================
    # Metadata Tests
    # =================================================================

    def test_imaging_study_with_description(self, factory):
        """Test ImagingStudy with description"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "description": "CT angiography chest for suspected PE"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-description"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "description" in result

    def test_imaging_study_with_location(self, factory):
        """Test ImagingStudy with location"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:00:00Z",
            "location": "Location/radiology-suite-1"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-location"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert "location" in result
        assert "Location" in result["location"]["reference"]

    # =================================================================
    # FHIR Compliance Tests
    # =================================================================

    def test_imaging_study_fhir_r4_compliance(self, factory):
        """Test ImagingStudy resource FHIR R4 compliance"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T09:00:00Z",
            "basedOn": ["ServiceRequest/imaging-order-789"],
            "referrer": "Practitioner/cardiologist-123",
            "encounter": "Encounter/cardiology-visit-001",
            "procedureCode": "CT angiography chest",
            "procedureReference": "Procedure/cta-chest-001",
            "reasonCode": ["Suspected pulmonary embolism"],
            "reasonReference": ["Condition/suspected-pe-001"],
            "series": [
                {
                    "uid": "2.25.111111111",
                    "modality": "CT",
                    "description": "Scout images",
                    "numberOfInstances": 3,
                    "bodySite": "Chest"
                },
                {
                    "uid": "2.25.222222222",
                    "modality": "CT",
                    "description": "Arterial phase CTA",
                    "numberOfInstances": 250,
                    "bodySite": "Chest"
                }
            ],
            "endpoint": ["Endpoint/pacs-endpoint-1"],
            "description": "CT angiography chest for suspected PE",
            "location": "Location/radiology-suite-1"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-compliance"
        )

        # FHIR R4 required fields
        assert result["resourceType"] == "ImagingStudy"
        assert "status" in result
        assert "subject" in result
        assert result["subject"]["reference"] == "Patient/patient-compliance"

        # Optional but important fields
        if "id" in result:
            assert isinstance(result["id"], str)
        if "series" in result:
            assert isinstance(result["series"], list)
            assert len(result["series"]) == 2
        if "numberOfSeries" in result:
            assert result["numberOfSeries"] == 2
        if "numberOfInstances" in result:
            assert result["numberOfInstances"] == 253


class TestImagingStudyEdgeCases:
    """Test edge cases and error handling for ImagingStudy resources"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    def test_imaging_study_minimal_data(self, factory):
        """Test ImagingStudy creation with minimal required data"""

        imaging_data = {
            "status": "available"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-minimal"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert result["status"] == "available"
        assert result["subject"]["reference"] == "Patient/patient-minimal"
        # Should auto-generate started time
        assert "started" in result

    def test_imaging_study_complex_mri_brain(self, factory):
        """Test ImagingStudy with complex MRI brain protocol"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T08:00:00Z",
            "basedOn": ["ServiceRequest/mri-brain-order-001"],
            "referrer": "Practitioner/neurologist-456",
            "encounter": "Encounter/neurology-clinic-001",
            "procedureCode": "MRI brain with and without contrast",
            "reasonCode": ["Suspected brain tumor"],
            "reasonReference": ["Condition/brain-mass-001"],
            "series": [
                {
                    "uid": "2.25.100000001",
                    "modality": "MR",
                    "description": "Localizer",
                    "numberOfInstances": 3,
                    "bodySite": "Brain"
                },
                {
                    "uid": "2.25.100000002",
                    "modality": "MR",
                    "description": "T1-weighted axial pre-contrast",
                    "numberOfInstances": 180,
                    "bodySite": "Brain"
                },
                {
                    "uid": "2.25.100000003",
                    "modality": "MR",
                    "description": "T2-weighted axial",
                    "numberOfInstances": 180,
                    "bodySite": "Brain"
                },
                {
                    "uid": "2.25.100000004",
                    "modality": "MR",
                    "description": "FLAIR axial",
                    "numberOfInstances": 180,
                    "bodySite": "Brain"
                },
                {
                    "uid": "2.25.100000005",
                    "modality": "MR",
                    "description": "T1-weighted axial post-contrast",
                    "numberOfInstances": 180,
                    "bodySite": "Brain"
                },
                {
                    "uid": "2.25.100000006",
                    "modality": "MR",
                    "description": "T1-weighted coronal post-contrast",
                    "numberOfInstances": 180,
                    "bodySite": "Brain"
                }
            ],
            "endpoint": ["Endpoint/pacs-endpoint-1"],
            "description": "Complete brain MRI protocol with gadolinium contrast for tumor evaluation",
            "location": "Location/mri-suite-2"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-complex-mri"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert result["status"] == "available"
        assert len(result["series"]) == 6
        assert result["numberOfSeries"] == 6
        assert result["numberOfInstances"] == 903  # 3 + 180*5

    def test_imaging_study_ct_angiography_complex(self, factory):
        """Test ImagingStudy with complex CT angiography protocol"""

        imaging_data = {
            "status": "available",
            "started": "2024-12-01T10:30:00Z",
            "basedOn": ["ServiceRequest/cta-order-999"],
            "referrer": "Practitioner/vascular-surgeon-789",
            "encounter": "Encounter/vascular-clinic-001",
            "procedureCode": "CT angiography abdomen and pelvis",
            "reasonCode": ["Abdominal aortic aneurysm screening"],
            "reasonReference": ["Condition/aaa-suspected-001"],
            "series": [
                {
                    "uid": "2.25.200000001",
                    "modality": "CT",
                    "description": "Scout AP and lateral",
                    "numberOfInstances": 2,
                    "bodySite": "Abdomen"
                },
                {
                    "uid": "2.25.200000002",
                    "modality": "CT",
                    "description": "Arterial phase",
                    "numberOfInstances": 350,
                    "bodySite": "Abdomen and pelvis"
                },
                {
                    "uid": "2.25.200000003",
                    "modality": "CT",
                    "description": "Venous phase",
                    "numberOfInstances": 350,
                    "bodySite": "Abdomen and pelvis"
                },
                {
                    "uid": "2.25.200000004",
                    "modality": "CT",
                    "description": "3D reconstruction",
                    "numberOfInstances": 50,
                    "bodySite": "Abdominal aorta"
                }
            ],
            "endpoint": ["Endpoint/pacs-endpoint-1", "Endpoint/3d-workstation-1"],
            "description": "CT angiography of abdominal aorta and iliac arteries for AAA evaluation",
            "location": "Location/ct-suite-1"
        }

        result = factory.create_imaging_study_resource(
            imaging_data,
            "Patient/patient-cta-complex"
        )

        assert result["resourceType"] == "ImagingStudy"
        assert len(result["series"]) == 4
        assert result["numberOfSeries"] == 4
        assert result["numberOfInstances"] == 752
        assert len(result["endpoint"]) == 2
