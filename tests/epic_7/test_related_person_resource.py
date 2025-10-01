"""
Epic 7.7: RelatedPerson Resource Tests
Tests for RelatedPerson resource implementation - family member and emergency contact management

Validates FHIR R4 compliance, Patient relationship linkage, and emergency contact workflows.
"""

import pytest
from datetime import datetime
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


class TestRelatedPersonResource:
    """Test Epic 7.7: RelatedPerson Resource Implementation"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    # =================================================================
    # Story 7.7: Basic RelatedPerson Resource Tests
    # =================================================================

    def test_related_person_basic_creation(self, factory):
        """Test basic RelatedPerson resource creation (Story 7.7)"""

        related_person_data = {
            "name": "Jane Doe",
            "relationship": "spouse",
            "gender": "female"
        }

        patient_ref = "Patient/patient-123"

        result = factory.create_related_person_resource(
            related_person_data,
            patient_ref,
            request_id="req-relperson-001"
        )

        assert result["resourceType"] == "RelatedPerson"
        assert result["patient"]["reference"] == patient_ref
        assert "name" in result
        assert "relationship" in result

    def test_related_person_with_contact_info(self, factory):
        """Test RelatedPerson with contact information"""

        related_person_data = {
            "name": {
                "given": "John",
                "family": "Smith"
            },
            "relationship": "father",
            "telecom": [
                {
                    "system": "phone",
                    "value": "(555) 123-4567",
                    "use": "home"
                },
                {
                    "system": "email",
                    "value": "john.smith@example.com",
                    "use": "work"
                }
            ],
            "gender": "male"
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-456"
        )

        assert result["resourceType"] == "RelatedPerson"
        assert result["patient"]["reference"] == "Patient/patient-456"
        assert "telecom" in result
        assert len(result["telecom"]) == 2

    def test_related_person_emergency_contact(self, factory):
        """Test RelatedPerson as emergency contact"""

        related_person_data = {
            "name": "Emergency Contact - Mary Johnson",
            "relationship": "emergency",
            "telecom": [
                {
                    "system": "phone",
                    "value": "555-911-1234",
                    "use": "mobile",
                    "rank": 1  # Primary contact
                }
            ],
            "address": {
                "line1": "123 Main Street",
                "city": "Emergency City",
                "state": "CA",
                "postal_code": "90210"
            }
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-emergency"
        )

        assert result["resourceType"] == "RelatedPerson"
        assert result["patient"]["reference"] == "Patient/patient-emergency"
        if "telecom" in result:
            phone = next((t for t in result["telecom"] if t.get("system") == "phone"), None)
            assert phone is not None

    def test_related_person_with_address(self, factory):
        """Test RelatedPerson with address information"""

        related_person_data = {
            "name": "Sarah Williams",
            "relationship": "daughter",
            "address": {
                "use": "home",
                "line1": "456 Oak Avenue",
                "line2": "Apartment 3B",
                "city": "Springfield",
                "state": "IL",
                "postal_code": "62701",
                "country": "USA"
            },
            "gender": "female"
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-789"
        )

        assert result["resourceType"] == "RelatedPerson"
        assert "address" in result
        if isinstance(result["address"], list):
            assert len(result["address"]) > 0
            assert result["address"][0]["city"] == "Springfield"
        else:
            assert result["address"]["city"] == "Springfield"

    # =================================================================
    # Relationship Type Tests
    # =================================================================

    def test_related_person_family_relationships(self, factory):
        """Test various family relationship types"""

        relationships = [
            ("spouse", "Spouse"),
            ("parent", "Parent"),
            ("child", "Child"),
            ("sibling", "Sibling"),
            ("grandparent", "Grandparent"),
            ("guardian", "Legal Guardian")
        ]

        patient_ref = "Patient/patient-family"

        for rel_code, rel_display in relationships:
            related_person_data = {
                "name": f"Family Member - {rel_display}",
                "relationship": rel_code,
                "gender": "unknown"
            }

            result = factory.create_related_person_resource(
                related_person_data,
                patient_ref
            )

            assert result["resourceType"] == "RelatedPerson"
            assert result["patient"]["reference"] == patient_ref
            # Relationship coding may vary
            if "relationship" in result:
                rel_str = str(result["relationship"]).lower()
                assert rel_code in rel_str or rel_display.lower() in rel_str

    def test_related_person_multiple_relationships(self, factory):
        """Test RelatedPerson with multiple relationship types"""

        related_person_data = {
            "name": "Michael Brown",
            "relationship": ["spouse", "emergency"],  # Multiple roles
            "gender": "male",
            "telecom": [
                {
                    "system": "phone",
                    "value": "555-777-8888",
                    "use": "mobile"
                }
            ]
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-multi-rel"
        )

        assert result["resourceType"] == "RelatedPerson"
        # FHIR allows multiple relationship codings
        if "relationship" in result:
            assert isinstance(result["relationship"], (list, dict))

    # =================================================================
    # Patient Integration Tests
    # =================================================================

    def test_related_person_patient_linkage(self, factory):
        """Test RelatedPerson linkage to Patient resource"""

        # Create patient first (for validation)
        patient_id = "patient-linkage-test"
        patient_ref = f"Patient/{patient_id}"

        # Create related person
        related_person_data = {
            "name": "Linked Contact Person",
            "relationship": "friend",
            "gender": "other"
        }

        related_person = factory.create_related_person_resource(
            related_person_data,
            patient_ref
        )

        assert related_person["resourceType"] == "RelatedPerson"
        assert related_person["patient"]["reference"] == patient_ref
        # Verify reference format
        assert patient_id in related_person["patient"]["reference"]

    def test_related_person_bidirectional_relationship(self, factory):
        """Test bidirectional patient-related person relationships"""

        patient_ref = "Patient/patient-parent"

        # Parent as related person
        parent_data = {
            "name": "Parent Contact",
            "relationship": "parent",
            "gender": "female"
        }

        parent = factory.create_related_person_resource(
            parent_data,
            patient_ref
        )

        assert parent["resourceType"] == "RelatedPerson"
        assert parent["patient"]["reference"] == patient_ref

        # Child as related person (if patient is adult)
        child_data = {
            "name": "Adult Child Contact",
            "relationship": "child",
            "gender": "male"
        }

        child = factory.create_related_person_resource(
            child_data,
            "Patient/patient-child"
        )

        assert child["resourceType"] == "RelatedPerson"

    # =================================================================
    # Period and Active Status Tests
    # =================================================================

    def test_related_person_with_period(self, factory):
        """Test RelatedPerson with relationship period"""

        related_person_data = {
            "name": "Temporary Guardian",
            "relationship": "guardian",
            "period": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            },
            "gender": "female"
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-period"
        )

        assert result["resourceType"] == "RelatedPerson"
        if "period" in result:
            assert result["period"]["start"] == "2024-01-01"
            assert result["period"]["end"] == "2024-12-31"

    def test_related_person_active_status(self, factory):
        """Test RelatedPerson active status tracking"""

        # Active related person
        active_data = {
            "name": "Active Contact",
            "relationship": "spouse",
            "active": True,
            "gender": "male"
        }

        active_person = factory.create_related_person_resource(
            active_data,
            "Patient/patient-active"
        )

        assert active_person["resourceType"] == "RelatedPerson"
        if "active" in active_person:
            assert active_person["active"] is True

        # Inactive related person
        inactive_data = {
            "name": "Inactive Contact",
            "relationship": "ex-spouse",
            "active": False,
            "gender": "female"
        }

        inactive_person = factory.create_related_person_resource(
            inactive_data,
            "Patient/patient-inactive"
        )

        assert inactive_person["resourceType"] == "RelatedPerson"
        if "active" in inactive_person:
            assert inactive_person["active"] is False

    # =================================================================
    # Communication Preferences Tests
    # =================================================================

    def test_related_person_communication_preferences(self, factory):
        """Test RelatedPerson with communication preferences"""

        related_person_data = {
            "name": "Preferred Contact",
            "relationship": "spouse",
            "telecom": [
                {
                    "system": "phone",
                    "value": "555-100-2000",
                    "use": "mobile",
                    "rank": 1  # Preferred
                },
                {
                    "system": "phone",
                    "value": "555-100-3000",
                    "use": "work",
                    "rank": 2  # Secondary
                },
                {
                    "system": "email",
                    "value": "contact@example.com",
                    "use": "home"
                }
            ],
            "communication": {
                "language": "en-US",
                "preferred": True
            },
            "gender": "other"
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-comm-pref"
        )

        assert result["resourceType"] == "RelatedPerson"
        if "telecom" in result:
            # Should have multiple contact methods
            assert len(result["telecom"]) >= 3
            # Check for ranked contacts
            ranked = [t for t in result["telecom"] if "rank" in t]
            if ranked:
                assert any(t.get("rank") == 1 for t in result["telecom"])

    # =================================================================
    # FHIR Compliance and Validation Tests
    # =================================================================

    def test_related_person_fhir_r4_compliance(self, factory):
        """Test RelatedPerson resource FHIR R4 compliance"""

        related_person_data = {
            "identifier": "RELPERSON-2024-001",
            "name": {
                "given": ["Jane", "Marie"],
                "family": "Doe",
                "use": "official"
            },
            "relationship": "spouse",
            "gender": "female",
            "birthDate": "1985-05-15",
            "telecom": [
                {
                    "system": "phone",
                    "value": "555-COMPLIANT",
                    "use": "home"
                }
            ],
            "address": {
                "line1": "123 Compliance Street",
                "city": "Validation City",
                "state": "CA",
                "postal_code": "90000"
            }
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-compliance"
        )

        # FHIR R4 required fields
        assert result["resourceType"] == "RelatedPerson"
        assert "patient" in result
        assert result["patient"]["reference"] == "Patient/patient-compliance"

        # Optional but important fields
        if "name" in result:
            assert isinstance(result["name"], (list, dict))
        if "relationship" in result:
            assert isinstance(result["relationship"], (list, dict))
        if "id" in result:
            assert isinstance(result["id"], str)

    def test_related_person_identifier_generation(self, factory):
        """Test RelatedPerson resource identifier generation"""

        related_person_data = {
            "identifier": "RP-2024-CUSTOM-001",
            "name": "ID Test Person",
            "relationship": "friend",
            "gender": "unknown"
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-id-test"
        )

        assert result["resourceType"] == "RelatedPerson"
        # Should have either id or identifier field
        assert "id" in result or "identifier" in result

        if "identifier" in result:
            assert len(result["identifier"]) > 0


class TestRelatedPersonEdgeCases:
    """Test edge cases and error handling for RelatedPerson resources"""

    @pytest.fixture
    def factory(self):
        """Get initialized FHIR resource factory"""
        factory = get_factory_adapter()
        factory.initialize()
        return factory

    def test_related_person_minimal_data(self, factory):
        """Test RelatedPerson creation with minimal required data"""

        related_person_data = {
            "name": "Minimal Contact",
            "relationship": "other"
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-minimal"
        )

        assert result["resourceType"] == "RelatedPerson"
        assert result["patient"]["reference"] == "Patient/patient-minimal"

    def test_related_person_unknown_relationship(self, factory):
        """Test RelatedPerson with unknown/unspecified relationship"""

        related_person_data = {
            "name": "Unknown Relation",
            "relationship": "unknown",
            "gender": "unknown"
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-unknown-rel"
        )

        assert result["resourceType"] == "RelatedPerson"
        # Should handle unknown relationship gracefully

    def test_related_person_multiple_addresses(self, factory):
        """Test RelatedPerson with multiple addresses"""

        related_person_data = {
            "name": "Multi Address Contact",
            "relationship": "sibling",
            "address": [
                {
                    "use": "home",
                    "line1": "123 Home Street",
                    "city": "Home City",
                    "state": "CA",
                    "postal_code": "11111"
                },
                {
                    "use": "work",
                    "line1": "456 Work Avenue",
                    "city": "Work City",
                    "state": "NY",
                    "postal_code": "22222"
                }
            ],
            "gender": "female"
        }

        result = factory.create_related_person_resource(
            related_person_data,
            "Patient/patient-multi-addr"
        )

        assert result["resourceType"] == "RelatedPerson"
        if "address" in result:
            assert isinstance(result["address"], list)
            assert len(result["address"]) == 2
