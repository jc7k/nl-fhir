"""
Epic 9 Infrastructure & Compliance - Comprehensive Test Suite
Tests all 7 infrastructure and compliance FHIR resources for enterprise-grade capabilities

Tests Epic 9 Stories:
- 9.1 AuditEvent - Security and compliance logging
- 9.2 Consent - Patient privacy and consent management
- 9.3 Subscription - Real-time notifications and event-driven architecture
- 9.4 OperationOutcome - Enhanced error handling and system feedback
- 9.5 Composition - Clinical document management and attestation
- 9.6 DocumentReference - Document metadata and content management
- 9.7 HealthcareService - Service directory and capacity management
"""

import pytest
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


class TestEpic9InfrastructureCompliance:
    """Comprehensive test suite for Epic 9 infrastructure and compliance resources"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    def test_audit_event_resource_creation(self, factory):
        """Test AuditEvent resource basic creation (Story 9.1)"""
        event_data = {
            "type": "rest",
            "action": "C",
            "outcome": "0",
            "outcome_desc": "Success"
        }

        result = factory.create_audit_event_resource(
            event_data,
            request_id="req-123",
            agent_ref="Practitioner/dr-smith",
            entity_refs=["Patient/patient-123"]
        )

        assert result["resourceType"] == "AuditEvent"
        assert result["type"]["code"] == "rest"
        assert result["outcome"] == "0"
        assert result["action"] == "C"
        assert len(result["agent"]) >= 1
        assert len(result["entity"]) == 1
        assert "source" in result
        assert "identifier" in result

    def test_audit_event_with_multiple_entities(self, factory):
        """Test AuditEvent with multiple affected resources"""
        event_data = {
            "type": "access",
            "type_display": "Data Access",
            "outcome": "0"
        }

        result = factory.create_audit_event_resource(
            event_data,
            agent_ref="User/user-123",
            entity_refs=["Patient/patient-123", "Observation/obs-456", "MedicationRequest/med-789"]
        )

        assert result["resourceType"] == "AuditEvent"
        assert len(result["entity"]) == 3
        assert result["entity"][0]["what"]["reference"] == "Patient/patient-123"
        assert result["entity"][1]["what"]["reference"] == "Observation/obs-456"
        assert result["entity"][2]["what"]["reference"] == "MedicationRequest/med-789"

    def test_consent_resource_creation(self, factory):
        """Test Consent resource basic creation (Story 9.2)"""
        consent_data = {
            "status": "active",
            "scope": "patient-privacy",
            "category": "hipaa"
        }

        result = factory.create_consent_resource(
            consent_data,
            "Patient/patient-123",
            request_id="req-123",
            performer_ref="Practitioner/dr-smith"
        )

        assert result["resourceType"] == "Consent"
        assert result["status"] == "active"
        assert result["patient"]["reference"] == "Patient/patient-123"
        assert result["scope"]["coding"][0]["code"] == "patient-privacy"
        assert result["category"][0]["coding"][0]["code"] == "hipaa"
        assert result["performer"][0]["reference"] == "Practitioner/dr-smith"
        assert "identifier" in result
        assert "dateTime" in result

    def test_consent_with_provisions(self, factory):
        """Test Consent with detailed provisions"""
        consent_data = {
            "status": "active",
            "provisions": {
                "type": "permit",
                "start": "2024-01-01T00:00:00Z",
                "end": "2024-12-31T23:59:59Z",
                "purposes": [
                    {"code": "TREAT", "display": "Treatment"},
                    {"code": "HPAYMT", "display": "Healthcare Payment"}
                ]
            },
            "policy": {
                "authority": "http://hospital.local",
                "uri": "http://hospital.local/policies/hipaa-consent"
            }
        }

        result = factory.create_consent_resource(
            consent_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "Consent"
        assert result["provision"]["type"] == "permit"
        assert "period" in result["provision"]
        assert len(result["provision"]["purpose"]) == 2
        assert "policy" in result

    def test_subscription_resource_creation(self, factory):
        """Test Subscription resource basic creation (Story 9.3)"""
        subscription_data = {
            "status": "active",
            "criteria": "Observation?patient=Patient/patient-123",
            "reason": "Patient monitoring notifications",
            "channel": {
                "type": "rest-hook",
                "endpoint": "https://hospital.local/notifications",
                "payload": "application/fhir+json"
            }
        }

        result = factory.create_subscription_resource(
            subscription_data,
            request_id="req-123"
        )

        assert result["resourceType"] == "Subscription"
        assert result["status"] == "active"
        assert result["criteria"] == "Observation?patient=Patient/patient-123"
        assert result["channel"]["type"] == "rest-hook"
        assert result["channel"]["endpoint"] == "https://hospital.local/notifications"
        assert "identifier" in result

    def test_subscription_with_headers(self, factory):
        """Test Subscription with custom headers"""
        subscription_data = {
            "status": "active",
            "criteria": "Patient?active=true",
            "channel": {
                "type": "rest-hook",
                "endpoint": "https://external-system.com/webhook",
                "payload": "application/fhir+json",
                "headers": ["Authorization: Bearer token123", "X-Custom-Header: value"]
            },
            "end": "2024-12-31T23:59:59Z"
        }

        result = factory.create_subscription_resource(subscription_data)

        assert result["resourceType"] == "Subscription"
        assert result["channel"]["header"] == ["Authorization: Bearer token123", "X-Custom-Header: value"]
        assert result["end"] == "2024-12-31T23:59:59Z"

    def test_operation_outcome_resource_creation(self, factory):
        """Test OperationOutcome resource basic creation (Story 9.4)"""
        outcome_data = {
            "severity": "error",
            "code": "processing",
            "diagnostics": "Patient not found"
        }

        result = factory.create_operation_outcome_resource(
            outcome_data,
            request_id="req-123"
        )

        assert result["resourceType"] == "OperationOutcome"
        assert len(result["issue"]) == 1
        assert result["issue"][0]["severity"] == "error"
        assert result["issue"][0]["code"] == "processing"
        assert result["issue"][0]["diagnostics"] == "Patient not found"
        assert "identifier" in result

    def test_operation_outcome_with_multiple_issues(self, factory):
        """Test OperationOutcome with multiple issues"""
        outcome_data = {
            "issues": [
                {
                    "severity": "error",
                    "code": "required",
                    "diagnostics": "Patient.name is required",
                    "location": ["Patient.name"],
                    "expression": ["Patient.name"]
                },
                {
                    "severity": "warning",
                    "code": "code-invalid",
                    "diagnostics": "Unknown diagnosis code",
                    "details": {
                        "system": "http://terminology.hl7.org/CodeSystem/operation-outcome",
                        "code": "MSG_UNKNOWN_CODE",
                        "display": "Unknown code",
                        "text": "The code 'ABC123' is not recognized"
                    }
                }
            ]
        }

        result = factory.create_operation_outcome_resource(outcome_data)

        assert result["resourceType"] == "OperationOutcome"
        assert len(result["issue"]) == 2
        assert result["issue"][0]["severity"] == "error"
        assert result["issue"][0]["location"] == ["Patient.name"]
        assert result["issue"][1]["severity"] == "warning"
        assert "details" in result["issue"][1]

    def test_composition_resource_creation(self, factory):
        """Test Composition resource basic creation (Story 9.5)"""
        composition_data = {
            "status": "final",
            "title": "Discharge Summary",
            "type_code": "18842-5",
            "type_display": "Discharge summary"
        }

        result = factory.create_composition_resource(
            composition_data,
            "Patient/patient-123",
            request_id="req-123",
            author_ref="Practitioner/dr-smith"
        )

        assert result["resourceType"] == "Composition"
        assert result["status"] == "final"
        assert result["title"] == "Discharge Summary"
        assert result["subject"]["reference"] == "Patient/patient-123"
        assert result["author"][0]["reference"] == "Practitioner/dr-smith"
        assert result["type"]["coding"][0]["code"] == "18842-5"
        assert "identifier" in result
        assert "date" in result

    def test_composition_with_sections(self, factory):
        """Test Composition with multiple sections"""
        composition_data = {
            "status": "final",
            "title": "Consultation Note",
            "sections": [
                {
                    "title": "History of Present Illness",
                    "text": "Patient presents with acute chest pain...",
                    "code": {
                        "system": "http://loinc.org",
                        "code": "10164-2",
                        "display": "History of present illness Narrative"
                    }
                },
                {
                    "title": "Assessment and Plan",
                    "text": "Differential diagnosis includes...",
                    "code": {
                        "code": "51847-2",
                        "display": "Assessment and plan Narrative"
                    },
                    "entries": ["Condition/condition-123", "MedicationRequest/med-456"]
                }
            ],
            "confidentiality": "N"
        }

        result = factory.create_composition_resource(
            composition_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "Composition"
        assert len(result["section"]) == 2
        assert result["section"][0]["title"] == "History of Present Illness"
        assert result["section"][1]["title"] == "Assessment and Plan"
        assert len(result["section"][1]["entry"]) == 2
        assert result["confidentiality"] == "N"

    def test_document_reference_resource_creation(self, factory):
        """Test DocumentReference resource basic creation (Story 9.6)"""
        document_data = {
            "status": "current",
            "type_code": "34133-9",
            "type_display": "Summary of episode note"
        }

        result = factory.create_document_reference_resource(
            document_data,
            "Patient/patient-123",
            request_id="req-123",
            author_ref="Practitioner/dr-smith"
        )

        assert result["resourceType"] == "DocumentReference"
        assert result["status"] == "current"
        assert result["subject"]["reference"] == "Patient/patient-123"
        assert result["author"][0]["reference"] == "Practitioner/dr-smith"
        assert result["type"]["coding"][0]["code"] == "34133-9"
        assert "identifier" in result
        assert "date" in result

    def test_document_reference_with_content(self, factory):
        """Test DocumentReference with content attachments"""
        document_data = {
            "status": "current",
            "type_code": "11488-4",
            "type_display": "Consultation note",
            "content": [
                {
                    "content_type": "application/pdf",
                    "language": "en",
                    "url": "https://hospital.local/documents/consultation-note-123.pdf",
                    "size": 245760,
                    "title": "Cardiology Consultation Note",
                    "format": {
                        "code": "urn:ihe:pcc:xphr:2007",
                        "display": "Personal Health Records"
                    }
                },
                {
                    "content_type": "text/plain",
                    "data": "Q29uc3VsdGF0aW9uIG5vdGUgdGV4dCBoZXJl",  # Base64 encoded
                    "title": "Plain Text Version"
                }
            ],
            "security_labels": [
                {"code": "N", "display": "Normal"},
                {"code": "NOAUTH", "display": "No disclosure without authorization"}
            ]
        }

        result = factory.create_document_reference_resource(
            document_data,
            "Patient/patient-123"
        )

        assert result["resourceType"] == "DocumentReference"
        assert len(result["content"]) == 2
        assert result["content"][0]["attachment"]["contentType"] == "application/pdf"
        assert result["content"][0]["attachment"]["size"] == 245760
        assert result["content"][1]["attachment"]["data"] == "Q29uc3VsdGF0aW9uIG5vdGUgdGV4dCBoZXJl"
        assert len(result["securityLabel"]) == 2

    def test_healthcare_service_resource_creation(self, factory):
        """Test HealthcareService resource basic creation (Story 9.7)"""
        service_data = {
            "name": "Cardiology Consultation Service",
            "active": True,
            "comment": "Comprehensive cardiac care services"
        }

        result = factory.create_healthcare_service_resource(
            service_data,
            request_id="req-123",
            location_ref="Location/cardiology-clinic",
            organization_ref="Organization/hospital-main"
        )

        assert result["resourceType"] == "HealthcareService"
        assert result["name"] == "Cardiology Consultation Service"
        assert result["active"] == True
        assert result["comment"] == "Comprehensive cardiac care services"
        assert result["location"][0]["reference"] == "Location/cardiology-clinic"
        assert result["providedBy"]["reference"] == "Organization/hospital-main"
        assert "identifier" in result

    def test_healthcare_service_with_details(self, factory):
        """Test HealthcareService with detailed service information"""
        service_data = {
            "name": "Emergency Department",
            "active": True,
            "category": [
                {
                    "code": "35",
                    "display": "Emergency Department",
                    "system": "http://terminology.hl7.org/CodeSystem/service-category"
                }
            ],
            "type": [
                {
                    "code": "124",
                    "display": "General Practice",
                    "system": "http://terminology.hl7.org/CodeSystem/service-type"
                }
            ],
            "specialty": [
                {
                    "code": "773568002",
                    "display": "Emergency medicine",
                    "system": "http://snomed.info/sct"
                }
            ],
            "availability": [
                {
                    "days_of_week": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
                    "all_day": True
                }
            ]
        }

        result = factory.create_healthcare_service_resource(
            service_data,
            location_ref="Location/emergency-dept"
        )

        assert result["resourceType"] == "HealthcareService"
        assert result["name"] == "Emergency Department"
        assert len(result["category"]) == 1
        assert len(result["type"]) == 1
        assert len(result["specialty"]) == 1
        assert len(result["availableTime"]) == 1
        assert result["availableTime"][0]["allDay"] == True
        assert len(result["availableTime"][0]["daysOfWeek"]) == 7

    def test_healthcare_service_business_hours(self, factory):
        """Test HealthcareService with business hours"""
        service_data = {
            "name": "Outpatient Clinic",
            "availability": [
                {
                    "days_of_week": ["mon", "tue", "wed", "thu", "fri"],
                    "all_day": False,
                    "start_time": "08:00:00",
                    "end_time": "17:00:00"
                },
                {
                    "days_of_week": ["sat"],
                    "all_day": False,
                    "start_time": "09:00:00",
                    "end_time": "13:00:00"
                }
            ]
        }

        result = factory.create_healthcare_service_resource(service_data)

        assert result["resourceType"] == "HealthcareService"
        assert len(result["availableTime"]) == 2
        assert result["availableTime"][0]["availableStartTime"] == "08:00:00"
        assert result["availableTime"][0]["availableEndTime"] == "17:00:00"
        assert result["availableTime"][1]["availableStartTime"] == "09:00:00"
        assert result["availableTime"][1]["availableEndTime"] == "13:00:00"

    def test_epic9_resources_have_proper_ids(self, factory):
        """Test that all Epic 9 resources generate proper IDs"""

        # Test AuditEvent ID generation
        audit_event = factory.create_audit_event_resource(
            {"type": "rest", "outcome": "0"}
        )
        assert "id" in audit_event
        assert audit_event["identifier"][0]["system"] == "http://hospital.local/audit-event-id"

        # Test Consent ID generation
        consent = factory.create_consent_resource(
            {"status": "active"},
            "Patient/patient-123"
        )
        assert "id" in consent
        assert consent["identifier"][0]["system"] == "http://hospital.local/consent-id"

        # Test Subscription ID generation
        subscription = factory.create_subscription_resource(
            {"status": "active", "criteria": "Patient?active=true"}
        )
        assert "id" in subscription
        assert subscription["identifier"][0]["system"] == "http://hospital.local/subscription-id"

        # Test OperationOutcome ID generation
        outcome = factory.create_operation_outcome_resource(
            {"severity": "info", "code": "informational"}
        )
        assert "id" in outcome
        assert outcome["identifier"][0]["system"] == "http://hospital.local/operation-outcome-id"

        # Test Composition ID generation
        composition = factory.create_composition_resource(
            {"title": "Test Document"},
            "Patient/patient-123"
        )
        assert "id" in composition
        assert composition["identifier"][0]["system"] == "http://hospital.local/composition-id"

        # Test DocumentReference ID generation
        document_ref = factory.create_document_reference_resource(
            {"status": "current"},
            "Patient/patient-123"
        )
        assert "id" in document_ref
        assert document_ref["identifier"][0]["system"] == "http://hospital.local/document-reference-id"

        # Test HealthcareService ID generation
        healthcare_service = factory.create_healthcare_service_resource(
            {"name": "Test Service"}
        )
        assert "id" in healthcare_service
        assert healthcare_service["identifier"][0]["system"] == "http://hospital.local/healthcare-service-id"

    def test_epic9_audit_trail_workflow(self, factory):
        """Test complete audit trail workflow"""

        patient_ref = "Patient/patient-123"

        # Create audit events for various actions
        create_event = factory.create_audit_event_resource(
            {
                "type": "rest",
                "action": "C",
                "outcome": "0",
                "outcome_desc": "Patient record created successfully"
            },
            agent_ref="User/admin-user",
            entity_refs=[patient_ref]
        )

        read_event = factory.create_audit_event_resource(
            {
                "type": "access",
                "action": "R",
                "outcome": "0"
            },
            agent_ref="Practitioner/dr-smith",
            entity_refs=[patient_ref, "Observation/obs-456"]
        )

        update_event = factory.create_audit_event_resource(
            {
                "type": "rest",
                "action": "U",
                "outcome": "0"
            },
            agent_ref="Nurse/nurse-jones",
            entity_refs=[patient_ref]
        )

        # Verify audit trail
        assert create_event["action"] == "C"
        assert read_event["action"] == "R"
        assert update_event["action"] == "U"

        # All reference same patient
        assert create_event["entity"][0]["what"]["reference"] == patient_ref
        assert read_event["entity"][0]["what"]["reference"] == patient_ref
        assert update_event["entity"][0]["what"]["reference"] == patient_ref

    def test_epic9_consent_management_workflow(self, factory):
        """Test patient consent management workflow"""

        patient_ref = "Patient/patient-123"

        # Create initial consent
        initial_consent = factory.create_consent_resource(
            {
                "status": "active",
                "category": "hipaa",
                "provisions": {
                    "type": "permit",
                    "purposes": [{"code": "TREAT", "display": "Treatment"}]
                }
            },
            patient_ref,
            performer_ref="Patient/patient-123"
        )

        # Create research consent
        research_consent = factory.create_consent_resource(
            {
                "status": "active",
                "category": "research",
                "provisions": {
                    "type": "permit",
                    "purposes": [{"code": "HRESCH", "display": "Healthcare Research"}],
                    "start": "2024-01-01T00:00:00Z",
                    "end": "2025-12-31T23:59:59Z"
                }
            },
            patient_ref
        )

        # Create withdrawal consent
        withdrawal_consent = factory.create_consent_resource(
            {
                "status": "inactive",
                "category": "research",
                "provisions": {"type": "deny"}
            },
            patient_ref
        )

        # Verify consent workflow
        assert initial_consent["status"] == "active"
        assert research_consent["provision"]["type"] == "permit"
        assert withdrawal_consent["provision"]["type"] == "deny"

        # All reference same patient
        assert initial_consent["patient"]["reference"] == patient_ref
        assert research_consent["patient"]["reference"] == patient_ref
        assert withdrawal_consent["patient"]["reference"] == patient_ref

    def test_epic9_document_management_workflow(self, factory):
        """Test clinical document management workflow"""

        patient_ref = "Patient/patient-123"
        author_ref = "Practitioner/dr-smith"

        # Create composition
        composition = factory.create_composition_resource(
            {
                "status": "final",
                "title": "Discharge Summary",
                "type_code": "18842-5",
                "sections": [
                    {
                        "title": "Hospital Course",
                        "text": "Patient admitted for acute MI...",
                        "entries": ["Condition/acute-mi", "Procedure/pci"]
                    }
                ]
            },
            patient_ref,
            author_ref=author_ref
        )

        # Create document reference
        document_ref = factory.create_document_reference_resource(
            {
                "status": "current",
                "type_code": "18842-5",
                "content": [
                    {
                        "content_type": "application/pdf",
                        "url": "https://hospital.local/documents/discharge-123.pdf",
                        "title": "Discharge Summary PDF"
                    }
                ]
            },
            patient_ref,
            author_ref=author_ref
        )

        # Verify document workflow
        assert composition["status"] == "final"
        assert document_ref["status"] == "current"
        assert composition["subject"]["reference"] == patient_ref
        assert document_ref["subject"]["reference"] == patient_ref
        assert composition["author"][0]["reference"] == author_ref
        assert document_ref["author"][0]["reference"] == author_ref

    def test_epic9_notification_system_workflow(self, factory):
        """Test real-time notification system workflow"""

        # Create subscriptions for different events
        patient_subscription = factory.create_subscription_resource(
            {
                "status": "active",
                "criteria": "Patient?active=true",
                "reason": "Patient demographic changes",
                "channel": {
                    "type": "rest-hook",
                    "endpoint": "https://external-system.com/patient-updates",
                    "payload": "application/fhir+json"
                }
            }
        )

        observation_subscription = factory.create_subscription_resource(
            {
                "status": "active",
                "criteria": "Observation?category=vital-signs",
                "reason": "Critical vital signs monitoring",
                "channel": {
                    "type": "websocket",
                    "endpoint": "wss://monitoring.hospital.local/vitals",
                    "payload": "application/fhir+json"
                }
            }
        )

        # Verify subscription workflow
        assert patient_subscription["criteria"] == "Patient?active=true"
        assert observation_subscription["criteria"] == "Observation?category=vital-signs"
        assert patient_subscription["channel"]["type"] == "rest-hook"
        assert observation_subscription["channel"]["type"] == "websocket"

    def test_epic9_error_handling(self, factory):
        """Test Epic 9 resources handle errors gracefully"""

        # Test with minimal data - should not crash
        try:
            audit_event = factory.create_audit_event_resource({})
            assert audit_event["resourceType"] == "AuditEvent"
        except Exception as e:
            pytest.fail(f"AuditEvent creation should handle empty data: {e}")

        try:
            consent = factory.create_consent_resource({}, "Patient/patient-123")
            assert consent["resourceType"] == "Consent"
        except Exception as e:
            pytest.fail(f"Consent creation should handle empty data: {e}")

        try:
            subscription = factory.create_subscription_resource({})
            assert subscription["resourceType"] == "Subscription"
        except Exception as e:
            pytest.fail(f"Subscription creation should handle empty data: {e}")

        try:
            outcome = factory.create_operation_outcome_resource({})
            assert outcome["resourceType"] == "OperationOutcome"
        except Exception as e:
            pytest.fail(f"OperationOutcome creation should handle empty data: {e}")

        try:
            composition = factory.create_composition_resource({}, "Patient/patient-123")
            assert composition["resourceType"] == "Composition"
        except Exception as e:
            pytest.fail(f"Composition creation should handle empty data: {e}")

        try:
            document_ref = factory.create_document_reference_resource({}, "Patient/patient-123")
            assert document_ref["resourceType"] == "DocumentReference"
        except Exception as e:
            pytest.fail(f"DocumentReference creation should handle empty data: {e}")

        try:
            healthcare_service = factory.create_healthcare_service_resource({})
            assert healthcare_service["resourceType"] == "HealthcareService"
        except Exception as e:
            pytest.fail(f"HealthcareService creation should handle empty data: {e}")

    def test_epic9_comprehensive_enterprise_integration(self, factory):
        """Test complete Epic 9 enterprise infrastructure integration"""

        patient_ref = "Patient/patient-123"

        # Create all Epic 9 resources for enterprise scenario
        audit_event = factory.create_audit_event_resource(
            {"type": "rest", "action": "C", "outcome": "0"},
            agent_ref="User/admin",
            entity_refs=[patient_ref]
        )

        consent = factory.create_consent_resource(
            {"status": "active", "category": "hipaa"},
            patient_ref
        )

        subscription = factory.create_subscription_resource(
            {
                "status": "active",
                "criteria": f"Patient?_id={patient_ref.split('/')[1]}",
                "channel": {"type": "rest-hook", "endpoint": "https://enterprise.com/notify"}
            }
        )

        outcome = factory.create_operation_outcome_resource(
            {"severity": "information", "code": "informational", "diagnostics": "Operation completed successfully"}
        )

        composition = factory.create_composition_resource(
            {"status": "final", "title": "Enterprise Integration Document"},
            patient_ref
        )

        document_ref = factory.create_document_reference_resource(
            {"status": "current", "type_code": "34133-9"},
            patient_ref
        )

        healthcare_service = factory.create_healthcare_service_resource(
            {"name": "Enterprise Integration Service", "active": True}
        )

        # Verify all resources created successfully
        resources = [audit_event, consent, subscription, outcome, composition, document_ref, healthcare_service]
        expected_types = ["AuditEvent", "Consent", "Subscription", "OperationOutcome",
                         "Composition", "DocumentReference", "HealthcareService"]

        for resource, expected_type in zip(resources, expected_types):
            assert resource["resourceType"] == expected_type
            assert "id" in resource
            assert "identifier" in resource

        # Verify patient references where applicable
        patient_resources = [consent, composition, document_ref]
        for resource in patient_resources:
            if "patient" in resource:
                assert resource["patient"]["reference"] == patient_ref
            elif "subject" in resource:
                assert resource["subject"]["reference"] == patient_ref

        print(f"✅ Epic 9 Enterprise Infrastructure Complete:")
        print(f"   - AuditEvent: {audit_event['id']} (Security & Compliance)")
        print(f"   - Consent: {consent['id']} (Privacy Management)")
        print(f"   - Subscription: {subscription['id']} (Real-time Notifications)")
        print(f"   - OperationOutcome: {outcome['id']} (Error Handling)")
        print(f"   - Composition: {composition['id']} (Document Management)")
        print(f"   - DocumentReference: {document_ref['id']} (Document Metadata)")
        print(f"   - HealthcareService: {healthcare_service['id']} (Service Directory)")
        print(f"   - All resources support enterprise compliance and infrastructure")