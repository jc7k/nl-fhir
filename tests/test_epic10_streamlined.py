"""
Epic 10 Advanced & Future Capabilities - Streamlined Test Suite
Tests all 44 resources with essential validations for successful implementation
"""

import pytest
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


class TestEpic10Streamlined:
    """Streamlined tests for Epic 10 Advanced & Future Capabilities (44 resources)"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    # =====================================================
    # FINANCIAL & BILLING RESOURCES (8 resources)
    # =====================================================

    def test_financial_resources_creation(self, factory):
        """Test all 8 Financial & Billing resources creation"""
        patient_ref = "Patient/patient-123"

        # Account
        account = factory.create_account_resource(
            {"name": "Test Account", "status": "active"},
            subject_ref=patient_ref
        )
        assert account["resourceType"] == "Account"
        assert "id" in account

        # ChargeItem
        charge_item = factory.create_charge_item_resource(
            {"status": "billable"},
            subject_ref=patient_ref
        )
        assert charge_item["resourceType"] == "ChargeItem"
        assert "id" in charge_item

        # Claim
        claim = factory.create_claim_resource(
            {"status": "active", "use": "claim"},
            patient_ref=patient_ref
        )
        assert claim["resourceType"] == "Claim"
        assert "id" in claim

        # ClaimResponse
        claim_response = factory.create_claim_response_resource(
            {"status": "active", "outcome": "complete"},
            patient_ref=patient_ref
        )
        assert claim_response["resourceType"] == "ClaimResponse"
        assert "id" in claim_response

        # CoverageEligibilityRequest
        eligibility_request = factory.create_coverage_eligibility_request_resource(
            {"status": "active", "purpose": ["validation"]},
            patient_ref=patient_ref
        )
        assert eligibility_request["resourceType"] == "CoverageEligibilityRequest"
        assert "id" in eligibility_request

        # CoverageEligibilityResponse
        eligibility_response = factory.create_coverage_eligibility_response_resource(
            {"status": "active", "outcome": "complete"},
            patient_ref=patient_ref
        )
        assert eligibility_response["resourceType"] == "CoverageEligibilityResponse"
        assert "id" in eligibility_response

        # ExplanationOfBenefit
        eob = factory.create_explanation_of_benefit_resource(
            {"status": "active", "outcome": "complete"},
            patient_ref=patient_ref
        )
        assert eob["resourceType"] == "ExplanationOfBenefit"
        assert "id" in eob

        # Invoice
        invoice = factory.create_invoice_resource(
            {"status": "issued"},
            subject_ref=patient_ref
        )
        assert invoice["resourceType"] == "Invoice"
        assert "id" in invoice

        print(f"✅ Financial & Billing Resources: 8/8 created successfully")

    # =====================================================
    # ADVANCED CLINICAL RESOURCES (12 resources)
    # =====================================================

    def test_advanced_clinical_resources_creation(self, factory):
        """Test all 12 Advanced Clinical resources creation"""
        patient_ref = "Patient/patient-123"

        # BiologicallyDerivedProduct
        bio_product = factory.create_biologically_derived_product_resource(
            {"product_category": "tissue", "status": "available"}
        )
        assert bio_product["resourceType"] == "BiologicallyDerivedProduct"
        assert "id" in bio_product

        # BodyStructure
        body_structure = factory.create_body_structure_resource(
            {"active": True},
            patient_ref=patient_ref
        )
        assert body_structure["resourceType"] == "BodyStructure"
        assert "id" in body_structure

        # Contract
        contract = factory.create_contract_resource(
            {"status": "executed"}
        )
        assert contract["resourceType"] == "Contract"
        assert "id" in contract

        # DeviceMetric
        device_metric = factory.create_device_metric_resource(
            {"operational_status": "on"},
            device_ref="Device/monitor-123"
        )
        assert device_metric["resourceType"] == "DeviceMetric"
        assert "id" in device_metric

        # GuidanceResponse
        guidance = factory.create_guidance_response_resource(
            {"status": "success"}
        )
        assert guidance["resourceType"] == "GuidanceResponse"
        assert "id" in guidance

        # Measure
        measure = factory.create_measure_resource(
            {"name": "Quality Measure", "status": "active"}
        )
        assert measure["resourceType"] == "Measure"
        assert "id" in measure

        # MeasureReport
        measure_report = factory.create_measure_report_resource(
            {"status": "complete", "type": "individual"},
            subject_ref=patient_ref
        )
        assert measure_report["resourceType"] == "MeasureReport"
        assert "id" in measure_report

        # MolecularSequence
        sequence = factory.create_molecular_sequence_resource(
            {"type": "dna", "coordinate_system": 1},
            patient_ref=patient_ref
        )
        assert sequence["resourceType"] == "MolecularSequence"
        assert "id" in sequence

        # Substance
        substance = factory.create_substance_resource(
            {"status": "active"}
        )
        assert substance["resourceType"] == "Substance"
        assert "id" in substance

        # SupplyDelivery
        supply_delivery = factory.create_supply_delivery_resource(
            {"status": "completed"}
        )
        assert supply_delivery["resourceType"] == "SupplyDelivery"
        assert "id" in supply_delivery

        # SupplyRequest
        supply_request = factory.create_supply_request_resource(
            {"status": "active"}
        )
        assert supply_request["resourceType"] == "SupplyRequest"
        assert "id" in supply_request

        # ResearchStudy
        research_study = factory.create_research_study_resource(
            {"title": "Clinical Trial", "status": "active"}
        )
        assert research_study["resourceType"] == "ResearchStudy"
        assert "id" in research_study

        print(f"✅ Advanced Clinical Resources: 12/12 created successfully")

    # =====================================================
    # INFRASTRUCTURE & TERMINOLOGY RESOURCES (15 resources)
    # =====================================================

    def test_infrastructure_terminology_resources_creation(self, factory):
        """Test all 15 Infrastructure & Terminology resources creation"""

        resources = [
            (factory.create_binary_resource, {"content_type": "application/pdf"}, "Binary"),
            (factory.create_concept_map_resource, {"name": "Test Map", "status": "active"}, "ConceptMap"),
            (factory.create_endpoint_resource, {"status": "active"}, "Endpoint"),
            (factory.create_group_resource, {"active": True, "type": "person"}, "Group"),
            (factory.create_library_resource, {"name": "Test Library", "status": "active"}, "Library"),
            (factory.create_linkage_resource, {"active": True}, "Linkage"),
            (factory.create_message_definition_resource, {"name": "Test Message", "status": "active"}, "MessageDefinition"),
            (factory.create_message_header_resource, {}, "MessageHeader"),
            (factory.create_naming_system_resource, {"name": "Test System", "status": "active"}, "NamingSystem"),
            (factory.create_operation_definition_resource, {"name": "Test Operation", "status": "active"}, "OperationDefinition"),
            (factory.create_parameters_resource, {"parameter": []}, "Parameters"),
            (factory.create_structure_definition_resource, {"name": "Test Structure", "status": "active"}, "StructureDefinition"),
            (factory.create_structure_map_resource, {"name": "Test Map", "status": "active"}, "StructureMap"),
            (factory.create_terminology_capabilities_resource, {"name": "Test Capabilities", "status": "active"}, "TerminologyCapabilities"),
            (factory.create_value_set_resource, {"name": "Test ValueSet", "status": "active"}, "ValueSet")
        ]

        for create_func, data, expected_type in resources:
            resource = create_func(data)
            assert resource["resourceType"] == expected_type
            assert "id" in resource

        print(f"✅ Infrastructure & Terminology Resources: 15/15 created successfully")

    # =====================================================
    # ADMINISTRATIVE & WORKFLOW RESOURCES (9 resources)
    # =====================================================

    def test_administrative_workflow_resources_creation(self, factory):
        """Test all 9 Administrative & Workflow resources creation"""

        patient_ref = "Patient/patient-123"
        practitioner_ref = "Practitioner/dr-jones"

        resources_data = [
            (factory.create_appointment_response_resource, {"participant_status": "accepted"}, "AppointmentResponse", "Appointment/appt-123"),
            (factory.create_basic_resource, {"code": "referral"}, "Basic", None),
            (factory.create_capability_statement_resource, {"name": "Test Server", "status": "active"}, "CapabilityStatement", None),
            (factory.create_document_manifest_resource, {"status": "current"}, "DocumentManifest", patient_ref),
            (factory.create_episode_of_care_resource, {"status": "active"}, "EpisodeOfCare", patient_ref),
            (factory.create_flag_resource, {"status": "active"}, "Flag", patient_ref),
            (factory.create_list_resource, {"status": "current", "mode": "working"}, "List", None),
            (factory.create_practitioner_role_resource, {"active": True}, "PractitionerRole", practitioner_ref),
        ]

        for create_func, data, expected_type, ref in resources_data:
            if ref:
                resource = create_func(data, ref)
            else:
                resource = create_func(data)
            assert resource["resourceType"] == expected_type
            assert "id" in resource

        # Schedule (no additional parameters)
        schedule = factory.create_schedule_resource({"active": True})
        assert schedule["resourceType"] == "Schedule"
        assert "id" in schedule

        # Slot (needs schedule reference)
        slot = factory.create_slot_resource(
            {"status": "free"},
            f"Schedule/{schedule['id']}"
        )
        assert slot["resourceType"] == "Slot"
        assert "id" in slot

        print(f"✅ Administrative & Workflow Resources: 9/9 created successfully")

    # =====================================================
    # EPIC 10 INTEGRATION TESTS
    # =====================================================

    def test_epic10_complete_44_resource_coverage(self, factory):
        """Test that Epic 10 provides complete 44-resource coverage"""

        patient_ref = "Patient/patient-123"
        all_resources = []

        # Financial & Billing (8 resources)
        financial_resources = [
            factory.create_account_resource({}, subject_ref=patient_ref),
            factory.create_charge_item_resource({}, subject_ref=patient_ref),
            factory.create_claim_resource({}, patient_ref=patient_ref),
            factory.create_claim_response_resource({}, patient_ref=patient_ref),
            factory.create_coverage_eligibility_request_resource({}, patient_ref=patient_ref),
            factory.create_coverage_eligibility_response_resource({}, patient_ref=patient_ref),
            factory.create_explanation_of_benefit_resource({}, patient_ref=patient_ref),
            factory.create_invoice_resource({}, subject_ref=patient_ref)
        ]
        all_resources.extend(financial_resources)

        # Advanced Clinical (12 resources)
        clinical_resources = [
            factory.create_biologically_derived_product_resource({}),
            factory.create_body_structure_resource({}, patient_ref=patient_ref),
            factory.create_contract_resource({}),
            factory.create_device_metric_resource({}, device_ref="Device/123"),
            factory.create_guidance_response_resource({}),
            factory.create_measure_resource({}),
            factory.create_measure_report_resource({}, subject_ref=patient_ref),
            factory.create_molecular_sequence_resource({}, patient_ref=patient_ref),
            factory.create_substance_resource({}),
            factory.create_supply_delivery_resource({}),
            factory.create_supply_request_resource({}),
            factory.create_research_study_resource({})
        ]
        all_resources.extend(clinical_resources)

        # Infrastructure & Terminology (15 resources)
        infrastructure_resources = [
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
        ]
        all_resources.extend(infrastructure_resources)

        # Administrative & Workflow (9 resources)
        administrative_resources = [
            factory.create_appointment_response_resource({}, "Appointment/123"),
            factory.create_basic_resource({}),
            factory.create_capability_statement_resource({}),
            factory.create_document_manifest_resource({}, patient_ref),
            factory.create_episode_of_care_resource({}, patient_ref),
            factory.create_flag_resource({}, patient_ref),
            factory.create_list_resource({}),
            factory.create_practitioner_role_resource({}, "Practitioner/123"),
            factory.create_schedule_resource({}),
            factory.create_slot_resource({}, "Schedule/123")
        ]
        all_resources.extend(administrative_resources)

        # Verify total count
        assert len(all_resources) == 44, f"Expected 44 resources, got {len(all_resources)}"

        # Verify each resource has required fields
        for i, resource in enumerate(all_resources):
            assert "resourceType" in resource, f"Resource {i} missing resourceType"
            assert "id" in resource, f"Resource {i} missing id"

        # Count by category
        resource_types = [r["resourceType"] for r in all_resources]

        financial_types = [
            "Account", "ChargeItem", "Claim", "ClaimResponse",
            "CoverageEligibilityRequest", "CoverageEligibilityResponse",
            "ExplanationOfBenefit", "Invoice"
        ]
        clinical_types = [
            "BiologicallyDerivedProduct", "BodyStructure", "Contract",
            "DeviceMetric", "GuidanceResponse", "Measure", "MeasureReport",
            "MolecularSequence", "Substance", "SupplyDelivery",
            "SupplyRequest", "ResearchStudy"
        ]
        infrastructure_types = [
            "Binary", "ConceptMap", "Endpoint", "Group", "Library",
            "Linkage", "MessageDefinition", "MessageHeader", "NamingSystem",
            "OperationDefinition", "Parameters", "StructureDefinition",
            "StructureMap", "TerminologyCapabilities", "ValueSet"
        ]
        administrative_types = [
            "AppointmentResponse", "Basic", "CapabilityStatement",
            "DocumentManifest", "EpisodeOfCare", "Flag", "List",
            "PractitionerRole", "Schedule", "Slot"
        ]

        financial_count = len([rt for rt in resource_types if rt in financial_types])
        clinical_count = len([rt for rt in resource_types if rt in clinical_types])
        infrastructure_count = len([rt for rt in resource_types if rt in infrastructure_types])
        administrative_count = len([rt for rt in resource_types if rt in administrative_types])

        assert financial_count == 8, f"Expected 8 financial resources, got {financial_count}"
        assert clinical_count == 12, f"Expected 12 clinical resources, got {clinical_count}"
        assert infrastructure_count == 15, f"Expected 15 infrastructure resources, got {infrastructure_count}"
        assert administrative_count == 9, f"Expected 9 administrative resources, got {administrative_count}"

        print(f"✅ Epic 10 Complete Coverage Validation:")
        print(f"   - Financial & Billing: {financial_count}/8 ✓")
        print(f"   - Advanced Clinical: {clinical_count}/12 ✓")
        print(f"   - Infrastructure & Terminology: {infrastructure_count}/15 ✓")
        print(f"   - Administrative & Workflow: {administrative_count}/9 ✓")
        print(f"   - TOTAL: {len(all_resources)}/44 Epic 10 resources ✓")

    def test_epic10_market_scenarios(self, factory):
        """Test Epic 10 market-driven scenarios"""

        patient_ref = "Patient/patient-123"

        # Scenario A: Financial Focus - Value-based care
        account = factory.create_account_resource(
            {"name": "Value-Based Care Account", "status": "active"},
            subject_ref=patient_ref
        )
        claim = factory.create_claim_resource(
            {"status": "active", "use": "claim"},
            patient_ref=patient_ref
        )
        eob = factory.create_explanation_of_benefit_resource(
            {"status": "active", "outcome": "complete"},
            patient_ref=patient_ref
        )

        # Scenario B: Clinical Research
        study = factory.create_research_study_resource({
            "title": "Precision Medicine Study", "status": "active"
        })
        sequence = factory.create_molecular_sequence_resource(
            {"type": "dna", "coordinate_system": 1},
            patient_ref=patient_ref
        )

        # Scenario C: Advanced Interoperability
        endpoint = factory.create_endpoint_resource({
            "status": "active", "address": "https://hie.regional.com/fhir"
        })
        concept_map = factory.create_concept_map_resource({
            "name": "Regional HIE Mappings", "status": "active"
        })

        # Verify all scenarios work
        scenarios = [account, claim, eob, study, sequence, endpoint, concept_map]
        for resource in scenarios:
            assert "resourceType" in resource
            assert "id" in resource

        print(f"✅ Epic 10 Market Scenarios:")
        print(f"   - Value-based care: {len([account, claim, eob])} financial resources")
        print(f"   - Clinical research: {len([study, sequence])} research resources")
        print(f"   - HIE integration: {len([endpoint, concept_map])} interoperability resources")

    def test_epic10_error_handling(self, factory):
        """Test Epic 10 resources handle minimal data gracefully"""

        # Test each category with minimal data
        try:
            financial = factory.create_account_resource({}, subject_ref="Patient/123")
            clinical = factory.create_contract_resource({})
            infrastructure = factory.create_binary_resource({})
            administrative = factory.create_basic_resource({})

            resources = [financial, clinical, infrastructure, administrative]
            for resource in resources:
                assert "resourceType" in resource
                assert "id" in resource

            print(f"✅ Epic 10 Error Handling: All resources handle minimal data gracefully")

        except Exception as e:
            pytest.fail(f"Epic 10 resources should handle minimal data: {e}")