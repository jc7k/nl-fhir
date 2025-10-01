"""
Epic 7.5: CommunicationRequest Resource Tests
Tests for CommunicationRequest resource implementation - communication coordination and care team notifications

Validates FHIR R4 compliance, patient linkage, and communication workflow management.
"""

import pytest
from datetime import datetime, timedelta
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


class TestCommunicationRequestResource:
    """Test Epic 7.5: CommunicationRequest Resource Implementation"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    # =================================================================
    # Story 7.5: Basic CommunicationRequest Resource Tests
    # =================================================================

    def test_communication_request_basic_creation(self, factory):
        """Test basic CommunicationRequest resource creation (Story 7.5)"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "payload": ["Please call the office to schedule your follow-up appointment"]
        }

        patient_ref = "Patient/patient-123"

        result = factory.create_communication_request_resource(
            comm_req_data,
            patient_ref,
            request_id="req-commreq-001"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert result["status"] == "active"
        assert result["intent"] == "order"
        assert result["subject"]["reference"] == patient_ref
        assert "payload" in result

    def test_communication_request_with_priority(self, factory):
        """Test CommunicationRequest with priority levels"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "priority": "urgent",
            "payload": ["URGENT: Patient requires immediate callback"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-456"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert result["priority"] == "urgent"

    def test_communication_request_with_category(self, factory):
        """Test CommunicationRequest with communication category"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "category": "reminder",
            "payload": ["Appointment reminder: You have an appointment tomorrow at 2pm"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-789"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "category" in result
        if isinstance(result["category"], list):
            assert len(result["category"]) > 0

    def test_communication_request_with_medium(self, factory):
        """Test CommunicationRequest with communication medium/channel"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "medium": ["phone", "email"],
            "payload": ["Follow-up required - please contact patient"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-321"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "medium" in result
        if isinstance(result["medium"], list):
            assert len(result["medium"]) == 2

    # =================================================================
    # Recipient and Sender Tests
    # =================================================================

    def test_communication_request_with_recipient(self, factory):
        """Test CommunicationRequest with specified recipient"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "recipient": ["Practitioner/practitioner-123"],
            "payload": ["Please review patient's lab results"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-recipient-test"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "recipient" in result
        if isinstance(result["recipient"], list):
            assert len(result["recipient"]) > 0
            assert "Practitioner" in result["recipient"][0]["reference"]

    def test_communication_request_with_multiple_recipients(self, factory):
        """Test CommunicationRequest with multiple recipients"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "recipient": [
                "Practitioner/practitioner-123",
                "Practitioner/practitioner-456",
                "RelatedPerson/family-member-789"
            ],
            "payload": ["Team notification: Patient requires coordinated care"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-multi-recipient"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "recipient" in result
        if isinstance(result["recipient"], list):
            assert len(result["recipient"]) == 3

    def test_communication_request_with_sender(self, factory):
        """Test CommunicationRequest with sender information"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "sender": "Practitioner/ordering-physician-123",
            "recipient": ["Practitioner/consulting-physician-456"],
            "payload": ["Consult requested for patient evaluation"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-sender-test"
        )

        assert result["resourceType"] == "CommunicationRequest"
        if "sender" in result:
            assert "Practitioner" in result["sender"]["reference"]

    # =================================================================
    # Payload and Content Tests
    # =================================================================

    def test_communication_request_simple_string_payload(self, factory):
        """Test CommunicationRequest with simple string payload"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "payload": "Please call patient regarding test results"
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-string-payload"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "payload" in result
        if isinstance(result["payload"], list):
            assert len(result["payload"]) > 0
            assert "contentString" in result["payload"][0]

    def test_communication_request_multiple_payloads(self, factory):
        """Test CommunicationRequest with multiple payload items"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "payload": [
                "First message: Lab results are ready",
                "Second message: Please schedule follow-up",
                "Third message: Prescription ready for pickup"
            ]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-multi-payload"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "payload" in result
        if isinstance(result["payload"], list):
            assert len(result["payload"]) == 3

    def test_communication_request_structured_payload(self, factory):
        """Test CommunicationRequest with structured payload"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "payload": [
                {
                    "contentString": "Structured message content"
                }
            ]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-structured-payload"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "payload" in result

    # =================================================================
    # Status and Intent Tests
    # =================================================================

    def test_communication_request_statuses(self, factory):
        """Test different CommunicationRequest statuses"""

        statuses = [
            ("draft", "draft"),
            ("active", "active"),
            ("on-hold", "on-hold"),
            ("completed", "completed"),
            ("revoked", "revoked")
        ]

        for status_input, expected_status in statuses:
            comm_req_data = {
                "status": status_input,
                "intent": "order",
                "payload": [f"Request in {status_input} status"]
            }

            result = factory.create_communication_request_resource(
                comm_req_data,
                "Patient/patient-status-test"
            )

            assert result["resourceType"] == "CommunicationRequest"
            assert result["status"] == expected_status

    def test_communication_request_intents(self, factory):
        """Test different CommunicationRequest intents"""

        intents = ["proposal", "plan", "directive", "order"]

        for intent in intents:
            comm_req_data = {
                "status": "active",
                "intent": intent,
                "payload": [f"Request with {intent} intent"]
            }

            result = factory.create_communication_request_resource(
                comm_req_data,
                "Patient/patient-intent-test"
            )

            assert result["resourceType"] == "CommunicationRequest"
            assert result["intent"] == intent

    # =================================================================
    # Priority Tests
    # =================================================================

    def test_communication_request_priority_levels(self, factory):
        """Test different priority levels"""

        priorities = ["routine", "urgent", "asap", "stat"]

        for priority in priorities:
            comm_req_data = {
                "status": "active",
                "intent": "order",
                "priority": priority,
                "payload": [f"Request with {priority} priority"]
            }

            result = factory.create_communication_request_resource(
                comm_req_data,
                "Patient/patient-priority-test"
            )

            assert result["resourceType"] == "CommunicationRequest"
            assert result["priority"] == priority

    # =================================================================
    # Timing and Occurrence Tests
    # =================================================================

    def test_communication_request_with_occurrence_datetime(self, factory):
        """Test CommunicationRequest with specific occurrence time"""

        occurrence_time = (datetime.utcnow() + timedelta(hours=2)).isoformat() + 'Z'

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "occurrence_datetime": occurrence_time,
            "payload": ["Call patient at scheduled time"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-occurrence"
        )

        assert result["resourceType"] == "CommunicationRequest"
        if "occurrenceDateTime" in result:
            assert result["occurrenceDateTime"] == occurrence_time

    def test_communication_request_with_occurrence_period(self, factory):
        """Test CommunicationRequest with occurrence period"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "occurrence_period": {
                "start": "2024-12-01T09:00:00Z",
                "end": "2024-12-01T17:00:00Z"
            },
            "payload": ["Contact patient during business hours"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-period"
        )

        assert result["resourceType"] == "CommunicationRequest"
        if "occurrencePeriod" in result:
            assert "start" in result["occurrencePeriod"]
            assert "end" in result["occurrencePeriod"]

    def test_communication_request_with_authored_on(self, factory):
        """Test CommunicationRequest with authoredOn timestamp"""

        authored_time = datetime.utcnow().isoformat() + 'Z'

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "authored_on": authored_time,
            "payload": ["Request created at specific time"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-authored"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "authoredOn" in result

    # =================================================================
    # Reason and Context Tests
    # =================================================================

    def test_communication_request_with_reason_code(self, factory):
        """Test CommunicationRequest with reason code"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "reason_code": ["Follow-up after discharge"],
            "payload": ["Contact patient for post-discharge check-in"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-reason-code"
        )

        assert result["resourceType"] == "CommunicationRequest"
        if "reasonCode" in result:
            assert isinstance(result["reasonCode"], list)
            assert len(result["reasonCode"]) > 0

    def test_communication_request_with_reason_reference(self, factory):
        """Test CommunicationRequest with reason reference"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "reason_reference": ["Condition/diabetes-123"],
            "payload": ["Diabetes management follow-up required"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-reason-ref"
        )

        assert result["resourceType"] == "CommunicationRequest"
        if "reasonReference" in result:
            assert isinstance(result["reasonReference"], list)

    def test_communication_request_with_encounter(self, factory):
        """Test CommunicationRequest linked to encounter"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "encounter": "Encounter/encounter-123",
            "payload": ["Follow-up communication for this encounter"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-encounter"
        )

        assert result["resourceType"] == "CommunicationRequest"
        if "encounter" in result:
            assert "Encounter" in result["encounter"]["reference"]

    def test_communication_request_with_notes(self, factory):
        """Test CommunicationRequest with clinical notes"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "note": "Patient prefers morning calls. Has hearing difficulty, speak clearly.",
            "payload": ["Call patient regarding appointment"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-notes"
        )

        assert result["resourceType"] == "CommunicationRequest"
        if "note" in result:
            assert isinstance(result["note"], list)
            assert len(result["note"]) > 0

    # =================================================================
    # FHIR Compliance and Validation Tests
    # =================================================================

    def test_communication_request_fhir_r4_compliance(self, factory):
        """Test CommunicationRequest resource FHIR R4 compliance"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "category": ["alert", "reminder"],
            "priority": "urgent",
            "medium": ["phone", "email"],
            "recipient": ["Practitioner/practitioner-123"],
            "sender": "Practitioner/ordering-physician-456",
            "payload": ["URGENT: Critical lab results require immediate discussion"],
            "occurrence_datetime": "2024-12-15T14:00:00Z",
            "reason_code": ["Abnormal lab results"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-compliance"
        )

        # FHIR R4 required fields
        assert result["resourceType"] == "CommunicationRequest"
        assert "status" in result
        assert "intent" in result
        assert "subject" in result
        assert result["subject"]["reference"] == "Patient/patient-compliance"

        # Optional but important fields
        if "id" in result:
            assert isinstance(result["id"], str)
        if "payload" in result:
            assert isinstance(result["payload"], list)
        if "recipient" in result:
            assert isinstance(result["recipient"], list)

    def test_communication_request_identifier_generation(self, factory):
        """Test CommunicationRequest resource identifier generation"""

        comm_req_data = {
            "identifier": "COMMREQ-2024-001",
            "status": "active",
            "intent": "order",
            "payload": ["Test communication request with custom ID"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-id-test"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert "id" in result


class TestCommunicationRequestEdgeCases:
    """Test edge cases and error handling for CommunicationRequest resources"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    def test_communication_request_minimal_data(self, factory):
        """Test CommunicationRequest creation with minimal required data"""

        comm_req_data = {
            "status": "active",
            "intent": "order"
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-minimal"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert result["status"] == "active"
        assert result["intent"] == "order"
        assert result["subject"]["reference"] == "Patient/patient-minimal"

    def test_communication_request_with_complex_workflow(self, factory):
        """Test CommunicationRequest with complex care coordination workflow"""

        comm_req_data = {
            "status": "active",
            "intent": "order",
            "category": ["instruction", "notification"],
            "priority": "urgent",
            "medium": ["phone", "sms", "email"],
            "recipient": [
                "Practitioner/primary-care-123",
                "Practitioner/specialist-456",
                "RelatedPerson/family-789"
            ],
            "sender": "Practitioner/care-coordinator-999",
            "payload": [
                "Primary message: Patient requires coordinated follow-up",
                "Instructions: Schedule appointments with both providers",
                "Note: Family member should be included in discussion"
            ],
            "occurrence_datetime": (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z',
            "reason_code": ["Care coordination", "Post-hospitalization"],
            "reason_reference": ["Encounter/hospital-stay-001"],
            "encounter": "Encounter/hospital-stay-001",
            "note": ["Patient has complex care needs requiring team approach"]
        }

        result = factory.create_communication_request_resource(
            comm_req_data,
            "Patient/patient-complex"
        )

        assert result["resourceType"] == "CommunicationRequest"
        assert result["status"] == "active"
        assert result["priority"] == "urgent"
        if "recipient" in result:
            assert len(result["recipient"]) == 3
        if "payload" in result:
            assert len(result["payload"]) >= 3
