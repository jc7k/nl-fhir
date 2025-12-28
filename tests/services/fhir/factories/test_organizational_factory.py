"""
Tests for OrganizationalResourceFactory
FHIR R4 Location, Organization, and HealthcareService resource creation.

Part of Priority Tier 1 implementation - completing the "Critical 20" resources
"""

from typing import Any

import pytest

from src.nl_fhir.services.fhir.factories import get_factory_registry


@pytest.fixture
def factory_registry():
    """Get factory registry instance"""
    return get_factory_registry()


@pytest.fixture
def org_factory(factory_registry):
    """Get OrganizationalResourceFactory instance"""
    return factory_registry.get_factory("Location")


# =============================================================================
# LOCATION RESOURCE TESTS
# =============================================================================


@pytest.fixture
def sample_location_basic() -> dict[str, Any]:
    """Sample data for basic location"""
    return {
        "name": "Main Hospital Building",
        "status": "active",
        "description": "Primary hospital facility for inpatient care",
    }


@pytest.fixture
def sample_location_full() -> dict[str, Any]:
    """Sample data for full location with all features"""
    return {
        "name": "Emergency Department",
        "alias": ["ED", "ER", "Emergency Room"],
        "status": "active",
        "description": "24/7 Emergency care services",
        "mode": "instance",
        "type": "emergency",
        "physical_type": "wing",
        "phone": "555-123-4567",
        "email": "ed@hospital.local",
        "address": {
            "line1": "123 Healthcare Way",
            "city": "Medical City",
            "state": "CA",
            "postal_code": "90210",
            "country": "USA",
        },
        "latitude": 34.0522,
        "longitude": -118.2437,
        "managing_organization": "org-main-hospital",
        "hours_of_operation": [
            {
                "days_of_week": ["mon", "tue", "wed", "thu", "fri"],
                "all_day": True,
            },
            {
                "days_of_week": ["sat", "sun"],
                "opening_time": "08:00",
                "closing_time": "20:00",
            },
        ],
    }


@pytest.fixture
def sample_location_hierarchical() -> dict[str, Any]:
    """Sample data for hierarchical location (room within a ward)"""
    return {
        "name": "Room 101",
        "status": "active",
        "physical_type": "room",
        "type": "ward",
        "part_of": "location-ward-a",
    }


class TestLocationCreation:
    """Test Location resource creation"""

    def test_create_basic_location(self, org_factory, sample_location_basic):
        """Test creating a basic location"""
        location = org_factory.create("Location", sample_location_basic)

        assert location is not None
        assert location["resourceType"] == "Location"
        assert location["name"] == "Main Hospital Building"
        assert location["status"] == "active"
        assert location["description"] == "Primary hospital facility for inpatient care"
        assert "id" in location

    def test_create_full_location(self, org_factory, sample_location_full):
        """Test creating a location with all features"""
        location = org_factory.create("Location", sample_location_full)

        assert location is not None
        assert location["resourceType"] == "Location"
        assert location["name"] == "Emergency Department"
        assert location["alias"] == ["ED", "ER", "Emergency Room"]
        assert location["mode"] == "instance"

        # Check type coding
        assert len(location["type"]) == 1
        assert location["type"][0]["coding"][0]["system"] == "http://snomed.info/sct"
        assert location["type"][0]["coding"][0]["code"] == "225728007"

        # Check physical type
        assert location["physicalType"]["coding"][0]["code"] == "wi"

        # Check telecom
        assert any(t["system"] == "phone" and "555" in t["value"] for t in location["telecom"])
        assert any(t["system"] == "email" for t in location["telecom"])

        # Check address
        assert location["address"]["city"] == "Medical City"
        assert location["address"]["state"] == "CA"

        # Check position
        assert "position" in location
        assert location["position"]["latitude"] == 34.0522
        assert location["position"]["longitude"] == -118.2437

        # Check managing organization reference
        assert location["managingOrganization"]["reference"] == "Organization/org-main-hospital"

        # Check hours of operation
        assert len(location["hoursOfOperation"]) == 2
        assert location["hoursOfOperation"][0]["allDay"] is True

    def test_create_hierarchical_location(self, org_factory, sample_location_hierarchical):
        """Test creating a location with part-of hierarchy"""
        location = org_factory.create("Location", sample_location_hierarchical)

        assert location is not None
        assert location["partOf"]["reference"] == "Location/location-ward-a"
        assert location["physicalType"]["coding"][0]["code"] == "ro"

    def test_location_type_mappings(self, org_factory):
        """Test various location type mappings"""
        type_tests = [
            ("hospital", "22232009"),
            ("clinic", "35971002"),
            ("pharmacy", "264372000"),
            ("laboratory", "261904005"),
            ("icu", "309904001"),
        ]

        for type_name, expected_code in type_tests:
            location = org_factory.create(
                "Location", {"name": f"Test {type_name}", "type": type_name}
            )
            assert location["type"][0]["coding"][0]["code"] == expected_code

    def test_location_with_gps_position(self, org_factory):
        """Test location with GPS coordinates"""
        location = org_factory.create(
            "Location",
            {
                "name": "Mobile Unit",
                "position": {"latitude": 40.7128, "longitude": -74.0060, "altitude": 10.5},
            },
        )

        assert location["position"]["latitude"] == 40.7128
        assert location["position"]["longitude"] == -74.0060
        assert location["position"]["altitude"] == 10.5


class TestLocationValidation:
    """Test Location validation and edge cases"""

    def test_location_with_minimal_data(self, org_factory):
        """Test location with minimal data"""
        location = org_factory.create("Location", {"name": "Minimal Location"})

        assert location["resourceType"] == "Location"
        assert location["name"] == "Minimal Location"
        assert location["status"] == "active"

    def test_location_id_generation(self, org_factory):
        """Test location ID generation patterns"""
        # With provided ID
        loc1 = org_factory.create("Location", {"id": "custom-id", "name": "Custom"})
        assert loc1["id"] == "custom-id"

        # Without ID, using name-based generation
        loc2 = org_factory.create("Location", {"name": "Test Location"})
        assert "location-test-location" in loc2["id"]

    def test_location_mode_validation(self, org_factory):
        """Test location mode values"""
        for mode in ["instance", "kind"]:
            location = org_factory.create("Location", {"name": "Test", "mode": mode})
            assert location["mode"] == mode


# =============================================================================
# ORGANIZATION RESOURCE TESTS
# =============================================================================


@pytest.fixture
def sample_organization_basic() -> dict[str, Any]:
    """Sample data for basic organization"""
    return {
        "name": "General Hospital",
        "type": "provider",
        "active": True,
    }


@pytest.fixture
def sample_organization_full() -> dict[str, Any]:
    """Sample data for full organization"""
    return {
        "name": "Medical Center Corporation",
        "alias": ["MCC", "Med Center"],
        "type": ["provider", "department"],
        "npi": "1234567890",
        "tax_id": "12-3456789",
        "phone": "555-987-6543",
        "email": "info@medcenter.org",
        "address": {
            "line1": "456 Hospital Drive",
            "city": "Healthcare City",
            "state": "NY",
            "postal_code": "10001",
        },
        "contact": [
            {
                "purpose": "ADMIN",
                "name": "John Smith",
                "phone": "555-111-2222",
                "email": "jsmith@medcenter.org",
            }
        ],
    }


@pytest.fixture
def sample_organization_hierarchical() -> dict[str, Any]:
    """Sample data for organization with parent"""
    return {
        "name": "Cardiology Department",
        "type": "department",
        "part_of": "org-main-hospital",
    }


class TestOrganizationCreation:
    """Test Organization resource creation"""

    def test_create_basic_organization(self, org_factory, sample_organization_basic):
        """Test creating a basic organization"""
        org = org_factory.create("Organization", sample_organization_basic)

        assert org is not None
        assert org["resourceType"] == "Organization"
        assert org["name"] == "General Hospital"
        assert org["active"] is True
        assert len(org["type"]) == 1
        assert org["type"][0]["coding"][0]["code"] == "prov"

    def test_create_full_organization(self, org_factory, sample_organization_full):
        """Test creating an organization with all features"""
        org = org_factory.create("Organization", sample_organization_full)

        assert org is not None
        assert org["name"] == "Medical Center Corporation"
        assert org["alias"] == ["MCC", "Med Center"]

        # Check multiple types
        assert len(org["type"]) == 2

        # Check identifiers (NPI and Tax ID)
        npi_ids = [i for i in org["identifier"] if "us-npi" in i.get("system", "")]
        assert len(npi_ids) == 1
        assert npi_ids[0]["value"] == "1234567890"

        tax_ids = [i for i in org["identifier"] if "2.16.840" in i.get("system", "")]
        assert len(tax_ids) == 1

        # Check telecom
        assert any(t["system"] == "phone" for t in org["telecom"])
        assert any(t["system"] == "email" for t in org["telecom"])

        # Check address
        assert org["address"][0]["city"] == "Healthcare City"

        # Check contact
        assert len(org["contact"]) == 1
        assert org["contact"][0]["name"]["text"] == "John Smith"

    def test_create_hierarchical_organization(self, org_factory, sample_organization_hierarchical):
        """Test creating an organization with parent reference"""
        org = org_factory.create("Organization", sample_organization_hierarchical)

        assert org["partOf"]["reference"] == "Organization/org-main-hospital"
        assert org["type"][0]["coding"][0]["code"] == "dept"

    def test_organization_type_mappings(self, org_factory):
        """Test various organization type mappings"""
        type_tests = [
            ("provider", "prov"),
            ("department", "dept"),
            ("government", "govt"),
            ("insurance", "ins"),
            ("payer", "pay"),
        ]

        for type_name, expected_code in type_tests:
            org = org_factory.create(
                "Organization", {"name": f"Test {type_name}", "type": type_name}
            )
            assert org["type"][0]["coding"][0]["code"] == expected_code


class TestOrganizationValidation:
    """Test Organization validation and edge cases"""

    def test_organization_id_with_npi(self, org_factory):
        """Test organization ID generation with NPI"""
        org = org_factory.create("Organization", {"name": "Test Org", "npi": "9876543210"})
        assert org["id"] == "org-npi-9876543210"

    def test_organization_multiple_types(self, org_factory):
        """Test organization with multiple types"""
        org = org_factory.create(
            "Organization",
            {"name": "Multi-Type Org", "type": ["provider", "insurance", "educational"]},
        )
        assert len(org["type"]) == 3


# =============================================================================
# HEALTHCARESERVICE RESOURCE TESTS
# =============================================================================


@pytest.fixture
def sample_service_basic() -> dict[str, Any]:
    """Sample data for basic healthcare service"""
    return {
        "name": "Emergency Care Service",
        "active": True,
        "category": "emergency",
    }


@pytest.fixture
def sample_service_full() -> dict[str, Any]:
    """Sample data for full healthcare service"""
    return {
        "name": "Cardiology Outpatient Services",
        "comment": "Comprehensive cardiac care and consultation",
        "provided_by": "org-medical-center",
        "category": ["specialist", "diagnostic"],
        "type": ["394579002"],  # Cardiology service SNOMED
        "specialty": ["Cardiology"],
        "location": ["location-cardiology-wing"],
        "phone": "555-HEART-01",
        "email": "cardio@hospital.org",
        "communication": ["en", "es"],
        "referral_method": ["phone", "fax", "elec"],
        "appointment_required": True,
        "available_time": [
            {
                "days_of_week": ["mon", "tue", "wed", "thu", "fri"],
                "available_start_time": "08:00",
                "available_end_time": "17:00",
            }
        ],
        "not_available": [
            {
                "description": "Holiday closure",
                "during": {"start": "2025-12-25", "end": "2025-12-26"},
            }
        ],
    }


class TestHealthcareServiceCreation:
    """Test HealthcareService resource creation"""

    def test_create_basic_service(self, org_factory, sample_service_basic):
        """Test creating a basic healthcare service"""
        service = org_factory.create("HealthcareService", sample_service_basic)

        assert service is not None
        assert service["resourceType"] == "HealthcareService"
        assert service["name"] == "Emergency Care Service"
        assert service["active"] is True
        assert len(service["category"]) == 1

    def test_create_full_service(self, org_factory, sample_service_full):
        """Test creating a healthcare service with all features"""
        service = org_factory.create("HealthcareService", sample_service_full)

        assert service is not None
        assert service["name"] == "Cardiology Outpatient Services"
        assert service["comment"] == "Comprehensive cardiac care and consultation"

        # Check provided by reference
        assert service["providedBy"]["reference"] == "Organization/org-medical-center"

        # Check categories
        assert len(service["category"]) == 2

        # Check specialty
        assert len(service["specialty"]) == 1

        # Check location references
        assert len(service["location"]) == 1

        # Check communication languages
        assert len(service["communication"]) == 2

        # Check referral methods
        assert len(service["referralMethod"]) == 3

        # Check appointment required
        assert service["appointmentRequired"] is True

        # Check available time
        assert len(service["availableTime"]) == 1
        assert service["availableTime"][0]["availableStartTime"] == "08:00"

        # Check not available
        assert len(service["notAvailable"]) == 1
        assert service["notAvailable"][0]["description"] == "Holiday closure"

    def test_service_category_mappings(self, org_factory):
        """Test various service category mappings"""
        category_tests = [
            ("general_practice", "1"),
            ("emergency", "2"),
            ("specialist", "3"),
            ("pharmacy", "5"),
            ("mental_health", "6"),
        ]

        for cat_name, expected_code in category_tests:
            service = org_factory.create(
                "HealthcareService", {"name": f"Test {cat_name}", "category": cat_name}
            )
            assert service["category"][0]["coding"][0]["code"] == expected_code


class TestHealthcareServiceValidation:
    """Test HealthcareService validation and edge cases"""

    def test_service_with_eligibility(self, org_factory):
        """Test service with eligibility criteria"""
        service = org_factory.create(
            "HealthcareService",
            {
                "name": "Medicare Service",
                "eligibility": [{"code": "medicare", "comment": "Must be Medicare eligible"}],
            },
        )

        assert len(service["eligibility"]) == 1
        assert service["eligibility"][0]["comment"] == "Must be Medicare eligible"

    def test_service_with_programs(self, org_factory):
        """Test service with program affiliations"""
        service = org_factory.create(
            "HealthcareService",
            {"name": "Cancer Screening", "program": ["breast-screening", "colorectal-screening"]},
        )

        assert len(service["program"]) == 2


# =============================================================================
# FACTORY SUPPORT TESTS
# =============================================================================


class TestFactorySupport:
    """Test factory support and registration"""

    def test_supports_location(self, org_factory):
        """Test that factory supports Location"""
        assert org_factory.supports("Location") is True

    def test_supports_organization(self, org_factory):
        """Test that factory supports Organization"""
        assert org_factory.supports("Organization") is True

    def test_supports_healthcare_service(self, org_factory):
        """Test that factory supports HealthcareService"""
        assert org_factory.supports("HealthcareService") is True

    def test_does_not_support_other_types(self, org_factory):
        """Test that factory does not support unrelated types"""
        assert org_factory.supports("Patient") is False
        assert org_factory.supports("Observation") is False
        assert org_factory.supports("MedicationRequest") is False


class TestFactoryMetrics:
    """Test factory metrics and health status"""

    def test_get_org_metrics(self, org_factory, sample_location_basic):
        """Test getting factory metrics"""
        # Create a few resources
        for _ in range(3):
            org_factory.create("Location", sample_location_basic)

        metrics = org_factory.get_org_metrics()
        assert "Location" in metrics
        assert metrics["Location"]["count"] >= 3
        assert metrics["Location"]["success_rate"] > 0

    def test_get_health_status(self, org_factory, sample_location_basic):
        """Test getting factory health status"""
        org_factory.create("Location", sample_location_basic)

        health = org_factory.get_health_status()
        assert health["status"] in ["healthy", "degraded"]
        assert "supported_resources" in health
        assert "Location" in health["supported_resources"]
        assert "Organization" in health["supported_resources"]
        assert "HealthcareService" in health["supported_resources"]


# =============================================================================
# FHIR R4 COMPLIANCE TESTS
# =============================================================================


class TestFhirR4Compliance:
    """Test FHIR R4 structure compliance"""

    def test_location_fhir_structure(self, org_factory, sample_location_full):
        """Test Location FHIR R4 structure"""
        location = org_factory.create("Location", sample_location_full)

        # Validate required FHIR R4 elements
        assert "resourceType" in location
        assert location["resourceType"] == "Location"
        assert "id" in location
        assert "status" in location
        assert "meta" in location

    def test_organization_fhir_structure(self, org_factory, sample_organization_full):
        """Test Organization FHIR R4 structure"""
        org = org_factory.create("Organization", sample_organization_full)

        # Validate required FHIR R4 elements
        assert "resourceType" in org
        assert org["resourceType"] == "Organization"
        assert "id" in org
        assert "active" in org
        assert "meta" in org

        # Validate identifier structure
        for identifier in org["identifier"]:
            assert "value" in identifier
            if "type" in identifier:
                assert "coding" in identifier["type"]

    def test_healthcare_service_fhir_structure(self, org_factory, sample_service_full):
        """Test HealthcareService FHIR R4 structure"""
        service = org_factory.create("HealthcareService", sample_service_full)

        # Validate required FHIR R4 elements
        assert "resourceType" in service
        assert service["resourceType"] == "HealthcareService"
        assert "id" in service
        assert "active" in service
        assert "meta" in service

        # Validate reference structures
        if "providedBy" in service:
            assert "reference" in service["providedBy"]

    def test_codeable_concept_structure(self, org_factory):
        """Test that CodeableConcept elements are properly structured"""
        location = org_factory.create("Location", {"name": "Test", "type": "hospital"})

        # Verify CodeableConcept structure
        loc_type = location["type"][0]
        assert "coding" in loc_type
        assert len(loc_type["coding"]) > 0
        assert "system" in loc_type["coding"][0]
        assert "code" in loc_type["coding"][0]
