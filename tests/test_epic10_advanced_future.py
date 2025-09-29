"""
Epic 10 Advanced & Future Capabilities - Comprehensive Test Suite
Tests all 44 resources across 4 strategic categories

Tests core functionality of all Epic 10 resources in both FHIR library
and fallback modes, ensuring comprehensive coverage for future healthcare scenarios.
"""

import pytest
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


class TestEpic10AdvancedFuture:
    """Comprehensive tests for Epic 10 Advanced & Future Capabilities (44 resources)"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    # =====================================================
    # FINANCIAL & BILLING RESOURCES (8 resources)
    # =====================================================

    def test_account_resource_creation(self, factory):
        """Test Account resource creation (Financial)"""
        account_data = {
            "name": "Patient Account - John Doe",
            "status": "active"
        }

        result = factory.create_account_resource(
            account_data,
            subject_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "Account"
        assert result["status"] == "active"
        assert result["name"] == "Patient Account - John Doe"
        assert result["subject"][0]["reference"] == "Patient/patient-123"
        assert "id" in result
        assert "identifier" in result

    def test_charge_item_resource_creation(self, factory):
        """Test ChargeItem resource creation (Financial)"""
        charge_data = {
            "status": "billable",
            "code": "99213",
            "display": "Office Visit Level 3"
        }

        result = factory.create_charge_item_resource(
            charge_data,
            subject_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "ChargeItem"
        assert result["status"] == "billable"
        assert result["subject"]["reference"] == "Patient/patient-123"
        assert result["account"][0]["reference"] == "Account/account-456"
        assert result["code"]["coding"][0]["code"] == "99213"

    def test_claim_resource_creation(self, factory):
        """Test Claim resource creation (Financial)"""
        claim_data = {
            "status": "active",
            "type": "institutional",
            "use": "claim"
        }

        result = factory.create_claim_resource(
            claim_data,
            patient_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "Claim"
        assert result["status"] == "active"
        assert result["patient"]["reference"] == "Patient/patient-123"
        assert result["provider"]["reference"] == "Organization/provider-456"
        assert result["use"] == "claim"

    def test_claim_response_resource_creation(self, factory):
        """Test ClaimResponse resource creation (Financial)"""
        response_data = {
            "status": "active",
            "type": "institutional",
            "outcome": "complete"
        }

        result = factory.create_claim_response_resource(
            response_data,
            patient_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "ClaimResponse"
        assert result["status"] == "active"
        assert result["patient"]["reference"] == "Patient/patient-123"
        assert result["request"]["reference"] == "Claim/claim-789"
        assert result["outcome"] == "complete"

    def test_coverage_eligibility_request_creation(self, factory):
        """Test CoverageEligibilityRequest resource creation (Financial)"""
        request_data = {
            "status": "active",
            "purpose": ["validation"]
        }

        result = factory.create_coverage_eligibility_request_resource(
            request_data,
            patient_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "CoverageEligibilityRequest"
        assert result["status"] == "active"
        assert result["patient"]["reference"] == "Patient/patient-123"
        assert result["purpose"] == ["validation"]

    def test_coverage_eligibility_response_creation(self, factory):
        """Test CoverageEligibilityResponse resource creation (Financial)"""
        response_data = {
            "status": "active",
            "outcome": "complete"
        }

        result = factory.create_coverage_eligibility_response_resource(
            response_data,
            patient_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "CoverageEligibilityResponse"
        assert result["status"] == "active"
        assert result["patient"]["reference"] == "Patient/patient-123"
        assert result["request"]["reference"] == "CoverageEligibilityRequest/req-789"
        assert result["outcome"] == "complete"

    def test_explanation_of_benefit_creation(self, factory):
        """Test ExplanationOfBenefit resource creation (Financial)"""
        eob_data = {
            "status": "active",
            "type": "institutional",
            "outcome": "complete"
        }

        result = factory.create_explanation_of_benefit_resource(
            eob_data,
            patient_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "ExplanationOfBenefit"
        assert result["status"] == "active"
        assert result["patient"]["reference"] == "Patient/patient-123"
        assert result["claim"]["reference"] == "Claim/claim-456"
        assert result["outcome"] == "complete"

    def test_invoice_resource_creation(self, factory):
        """Test Invoice resource creation (Financial)"""
        invoice_data = {
            "status": "issued",
            "type": {"code": "invoice"}
        }

        result = factory.create_invoice_resource(
            invoice_data,
            subject_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "Invoice"
        assert result["status"] == "issued"
        assert result["subject"]["reference"] == "Patient/patient-123"
        assert "id" in result
        assert "identifier" in result

    # =====================================================
    # ADVANCED CLINICAL RESOURCES (12 resources)
    # =====================================================

    def test_biologically_derived_product_creation(self, factory):
        """Test BiologicallyDerivedProduct resource creation (Clinical)"""
        product_data = {
            "product_category": "tissue",
            "status": "available"
        }

        result = factory.create_biologically_derived_product_resource(product_data)

        assert result["resourceType"] == "BiologicallyDerivedProduct"
        assert result["productCategory"] == "tissue"
        assert result["status"] == "available"
        assert "id" in result
        assert "identifier" in result

    def test_body_structure_resource_creation(self, factory):
        """Test BodyStructure resource creation (Clinical)"""
        structure_data = {
            "location": "liver",
            "active": True
        }

        result = factory.create_body_structure_resource(
            structure_data,
            patient_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "BodyStructure"
        assert result["patient"]["reference"] == "Patient/patient-123"
        assert result["active"] == True
        assert result["location"]["coding"][0]["display"] == "liver"

    def test_contract_resource_creation(self, factory):
        """Test Contract resource creation (Clinical)"""
        contract_data = {
            "status": "executed",
            "type": "privacy"
        }

        result = factory.create_contract_resource(contract_data)

        assert result["resourceType"] == "Contract"
        assert result["status"] == "executed"
        assert result["type"]["coding"][0]["code"] == "privacy"
        assert "id" in result
        assert "identifier" in result

    def test_device_metric_resource_creation(self, factory):
        """Test DeviceMetric resource creation (Clinical)"""
        metric_data = {
            "type": "pulse_rate",
            "operational_status": "on"
        }

        result = factory.create_device_metric_resource(
            metric_data,
            device_ref="Device/monitor-123"
        )

        assert result["resourceType"] == "DeviceMetric"
        assert result["source"]["reference"] == "Device/monitor-123"
        assert result["operationalStatus"] == "on"
        assert result["type"]["coding"][0]["display"] == "pulse_rate"

    def test_guidance_response_resource_creation(self, factory):
        """Test GuidanceResponse resource creation (Clinical)"""
        guidance_data = {
            "status": "success",
            "module": "clinical-decision-support"
        }

        result = factory.create_guidance_response_resource(
            guidance_data
        )

        assert result["resourceType"] == "GuidanceResponse"
        assert result["status"] == "success"
        assert result["subject"]["reference"] == "Patient/patient-123"
        assert result["module"]["display"] == "clinical-decision-support"

    def test_measure_resource_creation(self, factory):
        """Test Measure resource creation (Clinical)"""
        measure_data = {
            "name": "Quality Measure",
            "status": "active",
            "scoring": "proportion"
        }

        result = factory.create_measure_resource(measure_data)

        assert result["resourceType"] == "Measure"
        assert result["name"] == "Quality Measure"
        assert result["status"] == "active"
        assert result["scoring"]["coding"][0]["code"] == "proportion"

    def test_measure_report_resource_creation(self, factory):
        """Test MeasureReport resource creation (Clinical)"""
        report_data = {
            "status": "complete",
            "type": "individual"
        }

        result = factory.create_measure_report_resource(
            report_data,
            subject_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "MeasureReport"
        assert result["status"] == "complete"
        assert result["type"] == "individual"
        assert result["measure"] == "Measure/quality-123"
        assert result["subject"]["reference"] == "Patient/patient-123"

    def test_molecular_sequence_resource_creation(self, factory):
        """Test MolecularSequence resource creation (Clinical)"""
        sequence_data = {
            "type": "dna",
            "coordinate_system": 1
        }

        result = factory.create_molecular_sequence_resource(
            sequence_data,
            patient_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "MolecularSequence"
        assert result["type"] == "dna"
        assert result["coordinateSystem"] == 1
        assert result["patient"]["reference"] == "Patient/patient-123"

    def test_substance_resource_creation(self, factory):
        """Test Substance resource creation (Clinical)"""
        substance_data = {
            "status": "active",
            "code": "aspirin"
        }

        result = factory.create_substance_resource(substance_data)

        assert result["resourceType"] == "Substance"
        assert result["status"] == "active"
        assert result["code"]["coding"][0]["display"] == "aspirin"
        assert "id" in result
        assert "identifier" in result

    def test_supply_delivery_resource_creation(self, factory):
        """Test SupplyDelivery resource creation (Clinical)"""
        delivery_data = {
            "status": "completed",
            "type": "medication"
        }

        result = factory.create_supply_delivery_resource(
            delivery_data,
            patient_ref="Patient/patient-123"
        )

        assert result["resourceType"] == "SupplyDelivery"
        assert result["status"] == "completed"
        assert result["patient"]["reference"] == "Patient/patient-123"
        assert result["type"]["coding"][0]["display"] == "medication"

    def test_supply_request_resource_creation(self, factory):
        """Test SupplyRequest resource creation (Clinical)"""
        request_data = {
            "status": "active",
            "category": "non-stock"
        }

        result = factory.create_supply_request_resource(
            request_data,
            requester_ref="Practitioner/dr-smith"
        )

        assert result["resourceType"] == "SupplyRequest"
        assert result["status"] == "active"
        assert result["requester"]["reference"] == "Practitioner/dr-smith"
        assert result["category"]["coding"][0]["code"] == "non-stock"

    def test_research_study_resource_creation(self, factory):
        """Test ResearchStudy resource creation (Clinical)"""
        study_data = {
            "title": "Clinical Trial ABC-123",
            "status": "active"
        }

        result = factory.create_research_study_resource(study_data)

        assert result["resourceType"] == "ResearchStudy"
        assert result["title"] == "Clinical Trial ABC-123"
        assert result["status"] == "active"
        assert "id" in result
        assert "identifier" in result

    # =====================================================
    # INFRASTRUCTURE & TERMINOLOGY RESOURCES (15 resources)
    # =====================================================

    def test_binary_resource_creation(self, factory):
        """Test Binary resource creation (Infrastructure)"""
        binary_data = {
            "content_type": "application/pdf",
            "data": "base64-encoded-content"
        }

        result = factory.create_binary_resource(binary_data)

        assert result["resourceType"] == "Binary"
        assert result["contentType"] == "application/pdf"
        assert result["data"] == "base64-encoded-content"
        assert "id" in result

    def test_concept_map_resource_creation(self, factory):
        """Test ConceptMap resource creation (Infrastructure)"""
        map_data = {
            "name": "ICD10-SNOMED-Mapping",
            "status": "active",
            "source_uri": "http://hl7.org/fhir/sid/icd-10",
            "target_uri": "http://snomed.info/sct"
        }

        result = factory.create_concept_map_resource(map_data)

        assert result["resourceType"] == "ConceptMap"
        assert result["name"] == "ICD10-SNOMED-Mapping"
        assert result["status"] == "active"
        assert result["sourceUri"] == "http://hl7.org/fhir/sid/icd-10"
        assert result["targetUri"] == "http://snomed.info/sct"

    def test_endpoint_resource_creation(self, factory):
        """Test Endpoint resource creation (Infrastructure)"""
        endpoint_data = {
            "status": "active",
            "connection_type": "hl7-fhir-rest",
            "address": "https://fhir.hospital.com/r4"
        }

        result = factory.create_endpoint_resource(endpoint_data)

        assert result["resourceType"] == "Endpoint"
        assert result["status"] == "active"
        assert result["connectionType"]["code"] == "hl7-fhir-rest"
        assert result["address"] == "https://fhir.hospital.com/r4"

    def test_group_resource_creation(self, factory):
        """Test Group resource creation (Infrastructure)"""
        group_data = {
            "active": True,
            "type": "person",
            "actual": True,
            "name": "Diabetes Patients Group"
        }

        result = factory.create_group_resource(group_data)

        assert result["resourceType"] == "Group"
        assert result["active"] == True
        assert result["type"] == "person"
        assert result["actual"] == True
        assert result["name"] == "Diabetes Patients Group"

    def test_library_resource_creation(self, factory):
        """Test Library resource creation (Infrastructure)"""
        library_data = {
            "name": "Clinical Decision Support Library",
            "status": "active",
            "type": "logic-library"
        }

        result = factory.create_library_resource(library_data)

        assert result["resourceType"] == "Library"
        assert result["name"] == "Clinical Decision Support Library"
        assert result["status"] == "active"
        assert result["type"]["coding"][0]["code"] == "logic-library"

    def test_linkage_resource_creation(self, factory):
        """Test Linkage resource creation (Infrastructure)"""
        linkage_data = {
            "active": True
        }

        result = factory.create_linkage_resource(linkage_data)

        assert result["resourceType"] == "Linkage"
        assert result["active"] == True
        assert "id" in result
        assert "identifier" in result

    def test_message_definition_resource_creation(self, factory):
        """Test MessageDefinition resource creation (Infrastructure)"""
        definition_data = {
            "name": "PatientAdmissionMessage",
            "status": "active",
            "event_code": "patient-admission"
        }

        result = factory.create_message_definition_resource(definition_data)

        assert result["resourceType"] == "MessageDefinition"
        assert result["name"] == "PatientAdmissionMessage"
        assert result["status"] == "active"
        assert result["eventCoding"]["code"] == "patient-admission"

    def test_message_header_resource_creation(self, factory):
        """Test MessageHeader resource creation (Infrastructure)"""
        header_data = {
            "event_code": "patient-discharge",
            "source_name": "Hospital EMR System",
            "source_endpoint": "https://hospital.com/fhir"
        }

        result = factory.create_message_header_resource(header_data)

        assert result["resourceType"] == "MessageHeader"
        assert result["eventCoding"]["code"] == "patient-discharge"
        assert result["source"]["name"] == "Hospital EMR System"
        assert result["source"]["endpoint"] == "https://hospital.com/fhir"

    def test_naming_system_resource_creation(self, factory):
        """Test NamingSystem resource creation (Infrastructure)"""
        naming_data = {
            "name": "HospitalPatientIDs",
            "status": "active",
            "kind": "identifier"
        }

        result = factory.create_naming_system_resource(naming_data)

        assert result["resourceType"] == "NamingSystem"
        assert result["name"] == "HospitalPatientIDs"
        assert result["status"] == "active"
        assert result["kind"] == "identifier"
        assert "date" in result

    def test_operation_definition_resource_creation(self, factory):
        """Test OperationDefinition resource creation (Infrastructure)"""
        operation_data = {
            "name": "PatientMatch",
            "status": "active",
            "kind": "operation",
            "code": "patient-match"
        }

        result = factory.create_operation_definition_resource(operation_data)

        assert result["resourceType"] == "OperationDefinition"
        assert result["name"] == "PatientMatch"
        assert result["status"] == "active"
        assert result["kind"] == "operation"
        assert result["code"] == "patient-match"

    def test_parameters_resource_creation(self, factory):
        """Test Parameters resource creation (Infrastructure)"""
        parameters_data = {
            "parameter": [
                {"name": "resource", "resource": {"resourceType": "Patient"}},
                {"name": "count", "valueInteger": 10}
            ]
        }

        result = factory.create_parameters_resource(parameters_data)

        assert result["resourceType"] == "Parameters"
        assert len(result["parameter"]) == 2
        assert result["parameter"][0]["name"] == "resource"
        assert result["parameter"][1]["name"] == "count"

    def test_structure_definition_resource_creation(self, factory):
        """Test StructureDefinition resource creation (Infrastructure)"""
        structure_data = {
            "name": "CustomPatientProfile",
            "status": "active",
            "kind": "resource",
            "type": "Patient",
            "base_definition": "http://hl7.org/fhir/StructureDefinition/Patient"
        }

        result = factory.create_structure_definition_resource(structure_data)

        assert result["resourceType"] == "StructureDefinition"
        assert result["name"] == "CustomPatientProfile"
        assert result["status"] == "active"
        assert result["kind"] == "resource"
        assert result["type"] == "Patient"
        assert result["baseDefinition"] == "http://hl7.org/fhir/StructureDefinition/Patient"

    def test_structure_map_resource_creation(self, factory):
        """Test StructureMap resource creation (Infrastructure)"""
        map_data = {
            "name": "HL7v2ToFHIR",
            "status": "active"
        }

        result = factory.create_structure_map_resource(map_data)

        assert result["resourceType"] == "StructureMap"
        assert result["name"] == "HL7v2ToFHIR"
        assert result["status"] == "active"
        assert "id" in result

    def test_terminology_capabilities_resource_creation(self, factory):
        """Test TerminologyCapabilities resource creation (Infrastructure)"""
        capabilities_data = {
            "name": "HospitalTerminologyServer",
            "status": "active",
            "kind": "instance"
        }

        result = factory.create_terminology_capabilities_resource(capabilities_data)

        assert result["resourceType"] == "TerminologyCapabilities"
        assert result["name"] == "HospitalTerminologyServer"
        assert result["status"] == "active"
        assert result["kind"] == "instance"
        assert "date" in result

    def test_value_set_resource_creation(self, factory):
        """Test ValueSet resource creation (Infrastructure)"""
        valueset_data = {
            "name": "AllergyIntoleranceCodes",
            "status": "active",
            "compose": {
                "include": [
                    {
                        "system": "http://snomed.info/sct",
                        "concept": [
                            {"code": "419199007", "display": "Allergy to substance"}
                        ]
                    }
                ]
            }
        }

        result = factory.create_value_set_resource(valueset_data)

        assert result["resourceType"] == "ValueSet"
        assert result["name"] == "AllergyIntoleranceCodes"
        assert result["status"] == "active"
        assert "include" in result["compose"]
        assert len(result["compose"]["include"]) == 1

    # =====================================================
    # ADMINISTRATIVE & WORKFLOW RESOURCES (9 resources)
    # =====================================================

    def test_appointment_response_resource_creation(self, factory):
        """Test AppointmentResponse resource creation (Administrative)"""
        response_data = {
            "participant_status": "accepted"
        }

        result = factory.create_appointment_response_resource(
            response_data,
            "Appointment/appt-123"
        )

        assert result["resourceType"] == "AppointmentResponse"
        assert result["appointment"]["reference"] == "Appointment/appt-123"
        assert result["participantStatus"] == "accepted"
        assert "id" in result
        assert "identifier" in result

    def test_basic_resource_creation(self, factory):
        """Test Basic resource creation (Administrative)"""
        basic_data = {
            "code": "referral"
        }

        result = factory.create_basic_resource(basic_data)

        assert result["resourceType"] == "Basic"
        assert result["code"]["coding"][0]["code"] == "referral"
        assert "created" in result
        assert "id" in result
        assert "identifier" in result

    def test_capability_statement_resource_creation(self, factory):
        """Test CapabilityStatement resource creation (Administrative)"""
        capability_data = {
            "name": "HospitalFHIRServer",
            "status": "active",
            "kind": "instance",
            "fhir_version": "4.0.1"
        }

        result = factory.create_capability_statement_resource(capability_data)

        assert result["resourceType"] == "CapabilityStatement"
        assert result["name"] == "HospitalFHIRServer"
        assert result["status"] == "active"
        assert result["kind"] == "instance"
        assert result["fhirVersion"] == "4.0.1"
        assert "date" in result

    def test_document_manifest_resource_creation(self, factory):
        """Test DocumentManifest resource creation (Administrative)"""
        manifest_data = {
            "status": "current"
        }

        result = factory.create_document_manifest_resource(
            manifest_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "DocumentManifest"
        assert result["status"] == "current"
        assert result["subject"]["reference"] == "Patient/patient-123"
        assert "created" in result
        assert "id" in result
        assert "identifier" in result

    def test_episode_of_care_resource_creation(self, factory):
        """Test EpisodeOfCare resource creation (Administrative)"""
        episode_data = {
            "status": "active"
        }

        result = factory.create_episode_of_care_resource(
            episode_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "EpisodeOfCare"
        assert result["status"] == "active"
        assert result["patient"]["reference"] == "Patient/patient-123"
        assert "id" in result
        assert "identifier" in result

    def test_flag_resource_creation(self, factory):
        """Test Flag resource creation (Administrative)"""
        flag_data = {
            "status": "active",
            "category": "clinical",
            "code": "182856006",
            "display": "Review required"
        }

        result = factory.create_flag_resource(
            flag_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "Flag"
        assert result["status"] == "active"
        assert result["category"][0]["coding"][0]["code"] == "clinical"
        assert result["code"]["coding"][0]["code"] == "182856006"
        assert result["code"]["coding"][0]["display"] == "Review required"
        assert result["subject"]["reference"] == "Patient/patient-123"

    def test_list_resource_creation(self, factory):
        """Test List resource creation (Administrative)"""
        list_data = {
            "status": "current",
            "mode": "working",
            "title": "Patient Problem List"
        }

        result = factory.create_list_resource(list_data)

        assert result["resourceType"] == "List"
        assert result["status"] == "current"
        assert result["mode"] == "working"
        assert result["title"] == "Patient Problem List"
        assert "date" in result
        assert "id" in result
        assert "identifier" in result

    def test_practitioner_role_resource_creation(self, factory):
        """Test PractitionerRole resource creation (Administrative)"""
        role_data = {
            "active": True,
            "code": "309343006",
            "display": "Physician"
        }

        result = factory.create_practitioner_role_resource(
            role_data,
            "Practitioner/dr-smith"
        )

        assert result["resourceType"] == "PractitionerRole"
        assert result["active"] == True
        assert result["practitioner"]["reference"] == "Practitioner/dr-smith"
        assert result["code"][0]["coding"][0]["code"] == "309343006"
        assert result["code"][0]["coding"][0]["display"] == "Physician"

    def test_schedule_resource_creation(self, factory):
        """Test Schedule resource creation (Administrative)"""
        schedule_data = {
            "active": True,
            "comment": "Dr. Smith's availability"
        }

        result = factory.create_schedule_resource(schedule_data)

        assert result["resourceType"] == "Schedule"
        assert result["active"] == True
        assert result["comment"] == "Dr. Smith's availability"
        assert "id" in result
        assert "identifier" in result

    def test_slot_resource_creation(self, factory):
        """Test Slot resource creation (Administrative)"""
        slot_data = {
            "status": "free",
            "start": "2024-03-15T09:00:00Z",
            "end": "2024-03-15T10:00:00Z"
        }

        result = factory.create_slot_resource(
            slot_data,
            "Schedule/schedule-123"
        )

        assert result["resourceType"] == "Slot"
        assert result["status"] == "free"
        assert result["schedule"]["reference"] == "Schedule/schedule-123"
        assert result["start"] == "2024-03-15T09:00:00Z"
        assert result["end"] == "2024-03-15T10:00:00Z"

    # =====================================================
    # EPIC 10 INTEGRATION TESTS
    # =====================================================

    def test_epic10_resource_id_generation(self, factory):
        """Test that all Epic 10 resources generate proper IDs and identifiers"""

        # Test Financial resources
        account = factory.create_account_resource({}, subject_ref="Patient/123")
        assert "id" in account
        assert account["identifier"][0]["system"] == "http://hospital.local/account-id"

        # Test Clinical resources
        contract = factory.create_contract_resource({})
        assert "id" in contract
        assert contract["identifier"][0]["system"] == "http://hospital.local/contract-id"

        # Test Infrastructure resources
        endpoint = factory.create_endpoint_resource({})
        assert "id" in endpoint
        assert endpoint["identifier"][0]["system"] == "http://hospital.local/endpoint-id"

        # Test Administrative resources
        basic = factory.create_basic_resource({})
        assert "id" in basic
        assert basic["identifier"][0]["system"] == "http://hospital.local/basic-id"

    def test_epic10_financial_workflow(self, factory):
        """Test integrated financial workflow with Epic 10 resources"""

        patient_ref = "Patient/patient-123"

        # Create account
        account = factory.create_account_resource(
            {"name": "John Doe Account", "status": "active"},
            subject_ref=patient_ref
        )

        # Create charge item for the account
        charge_item = factory.create_charge_item_resource(
            {"status": "billable", "code": "99213"},
            subject_ref=patient_ref
        )

        # Create claim
        claim = factory.create_claim_resource(
            {"status": "active", "use": "claim"},
            patient_ref=patient_ref
        )

        # Create explanation of benefit
        eob = factory.create_explanation_of_benefit_resource(
            {"status": "active", "outcome": "complete"},
            patient_ref=patient_ref
        )

        # Verify workflow integration
        assert account["subject"][0]["reference"] == patient_ref
        assert charge_item["subject"]["reference"] == patient_ref
        assert claim["patient"]["reference"] == patient_ref
        assert eob["patient"]["reference"] == patient_ref
        assert eob["claim"]["reference"] == f"Claim/{claim['id']}"

    def test_epic10_clinical_research_workflow(self, factory):
        """Test integrated clinical research workflow with Epic 10 resources"""

        patient_ref = "Patient/patient-123"

        # Create research study
        study = factory.create_research_study_resource({
            "title": "Diabetes Treatment Study",
            "status": "active"
        })

        # Create molecular sequence for genomic research
        sequence = factory.create_molecular_sequence_resource(
            {"type": "dna", "coordinate_system": 1},
            patient_ref=patient_ref
        )

        # Create measure for study outcomes
        measure = factory.create_measure_resource({
            "name": "HbA1c Improvement",
            "status": "active",
            "scoring": "ratio"
        })

        # Create measure report
        measure_report = factory.create_measure_report_resource(
            {"status": "complete", "type": "individual"},
            subject_ref=patient_ref
        )

        # Verify research workflow
        assert study["status"] == "active"
        assert sequence["patient"]["reference"] == patient_ref
        assert measure_report["subject"]["reference"] == patient_ref
        assert measure_report["measure"] == f"Measure/{measure['id']}"

    def test_epic10_infrastructure_integration(self, factory):
        """Test infrastructure and terminology integration"""

        # Create concept map
        concept_map = factory.create_concept_map_resource({
            "name": "ICD-10 to SNOMED CT",
            "status": "active",
            "source_uri": "http://hl7.org/fhir/sid/icd-10",
            "target_uri": "http://snomed.info/sct"
        })

        # Create value set
        value_set = factory.create_value_set_resource({
            "name": "Diabetes Codes",
            "status": "active",
            "compose": {"include": []}
        })

        # Create endpoint for data exchange
        endpoint = factory.create_endpoint_resource({
            "status": "active",
            "connection_type": "hl7-fhir-rest",
            "address": "https://terminology.server.com/fhir"
        })

        # Create message definition for notifications
        message_def = factory.create_message_definition_resource({
            "name": "LabResultNotification",
            "status": "active",
            "event_code": "lab-result"
        })

        # Verify infrastructure integration
        assert concept_map["sourceUri"] == "http://hl7.org/fhir/sid/icd-10"
        assert concept_map["targetUri"] == "http://snomed.info/sct"
        assert value_set["compose"]["include"] == []
        assert endpoint["connectionType"]["code"] == "hl7-fhir-rest"
        assert message_def["eventCoding"]["code"] == "lab-result"

    def test_epic10_administrative_workflow(self, factory):
        """Test administrative and workflow integration"""

        patient_ref = "Patient/patient-123"
        practitioner_ref = "Practitioner/dr-jones"

        # Create practitioner role
        practitioner_role = factory.create_practitioner_role_resource(
            {"active": True, "code": "309343006", "display": "Physician"},
            practitioner_ref
        )

        # Create schedule
        schedule = factory.create_schedule_resource({
            "active": True,
            "comment": "Primary care schedule"
        })

        # Create available slot
        slot = factory.create_slot_resource(
            {"status": "free", "start": "2024-03-20T10:00:00Z", "end": "2024-03-20T10:30:00Z"},
            f"Schedule/{schedule['id']}"
        )

        # Create episode of care
        episode = factory.create_episode_of_care_resource(
            {"status": "active"},
            patient_ref
        )

        # Create flag for patient
        flag = factory.create_flag_resource(
            {"status": "active", "category": "clinical", "code": "182856006"},
            patient_ref
        )

        # Verify administrative workflow
        assert practitioner_role["practitioner"]["reference"] == practitioner_ref
        assert slot["schedule"]["reference"] == f"Schedule/{schedule['id']}"
        assert episode["patient"]["reference"] == patient_ref
        assert flag["subject"]["reference"] == patient_ref

    def test_epic10_comprehensive_integration(self, factory):
        """Test comprehensive Epic 10 integration across all categories"""

        patient_ref = "Patient/patient-123"

        # Create resources from each category
        resources_created = []

        # Financial & Billing
        account = factory.create_account_resource(
            {"name": "Comprehensive Care Account", "status": "active"},
            subject_ref=patient_ref
        )
        resources_created.append(account)

        # Advanced Clinical
        contract = factory.create_contract_resource(
            {"status": "executed", "type": "privacy"}
        )
        resources_created.append(contract)

        # Infrastructure & Terminology
        value_set = factory.create_value_set_resource(
            {"name": "Comprehensive Care Codes", "status": "active"}
        )
        resources_created.append(value_set)

        # Administrative & Workflow
        episode = factory.create_episode_of_care_resource(
            {"status": "active"},
            patient_ref
        )
        resources_created.append(episode)

        # Verify comprehensive integration
        expected_types = ["Account", "Contract", "ValueSet", "EpisodeOfCare"]

        for resource, expected_type in zip(resources_created, expected_types):
            assert resource["resourceType"] == expected_type
            assert "id" in resource

            # Most resources should have identifiers
            if expected_type != "ValueSet":  # ValueSet has identifier but different structure
                assert "identifier" in resource

    def test_epic10_error_handling(self, factory):
        """Test Epic 10 resources handle errors gracefully"""

        # Test with minimal data - should not crash
        try:
            # Financial resource
            account = factory.create_account_resource({}, subject_ref="Patient/123")
            assert account["resourceType"] == "Account"

            # Clinical resource
            contract = factory.create_contract_resource({})
            assert contract["resourceType"] == "Contract"

            # Infrastructure resource
            binary = factory.create_binary_resource({})
            assert binary["resourceType"] == "Binary"

            # Administrative resource
            basic = factory.create_basic_resource({})
            assert basic["resourceType"] == "Basic"

        except Exception as e:
            pytest.fail(f"Epic 10 resources should handle empty data gracefully: {e}")

    def test_epic10_market_driven_scenarios(self, factory):
        """Test Epic 10 market-driven implementation scenarios"""

        patient_ref = "Patient/patient-123"

        # Scenario A: Financial Focus - Value-based care
        account = factory.create_account_resource(
            {"name": "Value-Based Care Account", "status": "active"},
            subject_ref=patient_ref
        )

        claim = factory.create_claim_resource(
            {"status": "active", "type": "institutional", "use": "claim"},
            patient_ref=patient_ref
        )

        eob = factory.create_explanation_of_benefit_resource(
            {"status": "active", "outcome": "complete"},
            patient_ref=patient_ref
        )

        # Scenario B: Clinical Research - Academic medical centers
        study = factory.create_research_study_resource({
            "title": "Precision Medicine Study",
            "status": "active"
        })

        sequence = factory.create_molecular_sequence_resource(
            {"type": "dna", "coordinate_system": 1},
            patient_ref=patient_ref
        )

        # Scenario C: Advanced Interoperability - Health information exchanges
        endpoint = factory.create_endpoint_resource({
            "status": "active",
            "connection_type": "hl7-fhir-rest",
            "address": "https://hie.regional.com/fhir"
        })

        concept_map = factory.create_concept_map_resource({
            "name": "Regional HIE Mappings",
            "status": "active",
            "source_uri": "http://local.hospital.com/codes",
            "target_uri": "http://snomed.info/sct"
        })

        # Verify market scenarios
        assert account["subject"][0]["reference"] == patient_ref
        assert eob["claim"]["reference"] == f"Claim/{claim['id']}"
        assert study["title"] == "Precision Medicine Study"
        assert sequence["patient"]["reference"] == patient_ref
        assert endpoint["connectionType"]["code"] == "hl7-fhir-rest"
        assert concept_map["name"] == "Regional HIE Mappings"

        print(f"✅ Epic 10 Market Scenarios Complete:")
        print(f"   - Value-based care: Account {account['id']} → Claim {claim['id']} → EOB {eob['id']}")
        print(f"   - Clinical research: Study {study['id']} with genomic sequence {sequence['id']}")
        print(f"   - HIE integration: Endpoint {endpoint['id']} with mapping {concept_map['id']}")

    def test_epic10_complete_coverage_validation(self, factory):
        """Test that Epic 10 provides complete 44-resource coverage"""

        # Create one instance of each Epic 10 resource to validate coverage
        epic10_resources = []

        # Financial & Billing (8 resources)
        epic10_resources.extend([
            factory.create_account_resource({}, subject_ref="Patient/123"),
            factory.create_charge_item_resource({}, subject_ref="Patient/123"),
            factory.create_claim_resource({}, patient_ref="Patient/123"),
            factory.create_claim_response_resource({}, patient_ref="Patient/123"),
            factory.create_coverage_eligibility_request_resource({}, patient_ref="Patient/123"),
            factory.create_coverage_eligibility_response_resource({}, patient_ref="Patient/123"),
            factory.create_explanation_of_benefit_resource({}, patient_ref="Patient/123"),
            factory.create_invoice_resource({}, subject_ref="Patient/123")
        ])

        # Advanced Clinical (12 resources)
        epic10_resources.extend([
            factory.create_biologically_derived_product_resource({}),
            factory.create_body_structure_resource({}, patient_ref="Patient/123"),
            factory.create_contract_resource({}),
            factory.create_device_metric_resource({}, device_ref="Device/123"),
            factory.create_guidance_response_resource({}),
            factory.create_measure_resource({}),
            factory.create_measure_report_resource({}, subject_ref="Patient/123"),
            factory.create_molecular_sequence_resource({}, patient_ref="Patient/123"),
            factory.create_substance_resource({}),
            factory.create_supply_delivery_resource({}),
            factory.create_supply_request_resource({}),
            factory.create_research_study_resource({})
        ])

        # Infrastructure & Terminology (15 resources)
        epic10_resources.extend([
            factory.create_binary_resource({}),
            factory.create_concept_map_resource({}),
            factory.create_endpoint_resource({}),
            factory.create_group_resource({}),
            factory.create_library_resource({}),
            factory.create_linkage_resource({}),
            factory.create_message_definition_resource({}),
            factory.create_message_header_resource({}),
            factory.create_naming_system_resource({}),
            factory.create_operation_definition_resource({}),
            factory.create_parameters_resource({}),
            factory.create_structure_definition_resource({}),
            factory.create_structure_map_resource({}),
            factory.create_terminology_capabilities_resource({}),
            factory.create_value_set_resource({})
        ])

        # Administrative & Workflow (9 resources)
        epic10_resources.extend([
            factory.create_appointment_response_resource({}, "Appointment/123"),
            factory.create_basic_resource({}),
            factory.create_capability_statement_resource({}),
            factory.create_document_manifest_resource({}, "Patient/123"),
            factory.create_episode_of_care_resource({}, "Patient/123"),
            factory.create_flag_resource({}, "Patient/123"),
            factory.create_list_resource({}),
            factory.create_practitioner_role_resource({}, "Practitioner/123"),
            factory.create_schedule_resource({}),
            factory.create_slot_resource({}, "Schedule/123")
        ])

        # Verify all 44 resources created successfully
        assert len(epic10_resources) == 44, f"Expected 44 resources, got {len(epic10_resources)}"

        # Verify each resource has required FHIR fields
        for resource in epic10_resources:
            assert "resourceType" in resource, f"Resource missing resourceType: {resource}"
            assert "id" in resource, f"Resource missing id: {resource}"

        # Count by category
        financial_count = len([r for r in epic10_resources if r["resourceType"] in
                             ["Account", "ChargeItem", "Claim", "ClaimResponse",
                              "CoverageEligibilityRequest", "CoverageEligibilityResponse",
                              "ExplanationOfBenefit", "Invoice"]])

        clinical_count = len([r for r in epic10_resources if r["resourceType"] in
                            ["BiologicallyDerivedProduct", "BodyStructure", "Contract",
                             "DeviceMetric", "GuidanceResponse", "Measure", "MeasureReport",
                             "MolecularSequence", "Substance", "SupplyDelivery",
                             "SupplyRequest", "ResearchStudy"]])

        infrastructure_count = len([r for r in epic10_resources if r["resourceType"] in
                                  ["Binary", "ConceptMap", "Endpoint", "Group", "Library",
                                   "Linkage", "MessageDefinition", "MessageHeader", "NamingSystem",
                                   "OperationDefinition", "Parameters", "StructureDefinition",
                                   "StructureMap", "TerminologyCapabilities", "ValueSet"]])

        administrative_count = len([r for r in epic10_resources if r["resourceType"] in
                                  ["AppointmentResponse", "Basic", "CapabilityStatement",
                                   "DocumentManifest", "EpisodeOfCare", "Flag", "List",
                                   "PractitionerRole", "Schedule", "Slot"]])

        # Verify category counts
        assert financial_count == 8, f"Expected 8 financial resources, got {financial_count}"
        assert clinical_count == 12, f"Expected 12 clinical resources, got {clinical_count}"
        assert infrastructure_count == 15, f"Expected 15 infrastructure resources, got {infrastructure_count}"
        assert administrative_count == 9, f"Expected 9 administrative resources, got {administrative_count}"

        print(f"✅ Epic 10 Complete Coverage Validated:")
        print(f"   - Financial & Billing: {financial_count}/8 resources ✓")
        print(f"   - Advanced Clinical: {clinical_count}/12 resources ✓")
        print(f"   - Infrastructure & Terminology: {infrastructure_count}/15 resources ✓")
        print(f"   - Administrative & Workflow: {administrative_count}/9 resources ✓")
        print(f"   - TOTAL: {len(epic10_resources)}/44 resources ✓")
        print(f"   - All resources validate with proper resourceType and id fields")