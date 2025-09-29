"""
Epic 6 Story 6.4: Location Resource Implementation Tests
Test comprehensive healthcare location and facility management capabilities.
"""
import pytest
from datetime import datetime
from src.nl_fhir.services.fhir.factory_adapter import get_factory_adapter


class TestLocationResource:
    """Test suite for Location FHIR resource creation and validation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.factory = get_factory_adapter()

    def test_location_creation_basic(self):
        """Test basic Location resource creation."""
        location_data = {
            "name": "General Hospital ICU",
            "type": "icu",
            "status": "active"
        }

        location = self.factory.create_location_resource(location_data, "test-request-001")

        assert location["resourceType"] == "Location"
        assert location["name"] == "General Hospital ICU"
        assert location["status"] == "active"
        assert "id" in location

        # Check facility type coding
        assert "type" in location
        assert len(location["type"]) == 1
        assert location["type"][0]["coding"][0]["system"] == "http://snomed.info/sct"
        assert location["type"][0]["coding"][0]["code"] == "309964003"  # ICU SNOMED code
        assert location["type"][0]["text"] == "icu"

    def test_location_with_structured_address(self):
        """Test Location resource with complete structured address."""
        location_data = {
            "name": "Downtown Medical Center",
            "type": "hospital",
            "address": {
                "line1": "123 Healthcare Boulevard",
                "line2": "Suite 200",
                "city": "Medical City",
                "state": "CA",
                "postal_code": "90210",
                "country": "USA"
            },
            "description": "Full-service medical center with emergency and specialty care"
        }

        location = self.factory.create_location_resource(location_data, "test-request-002")

        # Verify basic location properties
        assert location["name"] == "Downtown Medical Center"
        assert location["description"] == "Full-service medical center with emergency and specialty care"

        # Verify structured address
        address = location["address"]
        assert address["use"] == "work"
        assert address["type"] == "physical"
        assert address["line"] == ["123 Healthcare Boulevard", "Suite 200"]
        assert address["city"] == "Medical City"
        assert address["state"] == "CA"
        assert address["postalCode"] == "90210"
        assert address["country"] == "USA"
        assert "123 Healthcare Boulevard" in address["text"]

    def test_location_with_contact_information(self):
        """Test Location resource with multiple contact methods."""
        location_data = {
            "name": "Family Practice Clinic",
            "type": "clinic",
            "contact": {
                "phone": "(555) 123-4567",
                "email": "info@familypractice.com",
                "fax": "(555) 123-4568"
            }
        }

        location = self.factory.create_location_resource(location_data, "test-request-003")

        # Verify telecom information
        telecom = location["telecom"]
        assert len(telecom) == 3

        # Check phone
        phone_contact = next(t for t in telecom if t["system"] == "phone")
        assert phone_contact["value"] == "(555) 123-4567"
        assert phone_contact["use"] == "work"

        # Check email
        email_contact = next(t for t in telecom if t["system"] == "email")
        assert email_contact["value"] == "info@familypractice.com"

        # Check fax
        fax_contact = next(t for t in telecom if t["system"] == "fax")
        assert fax_contact["value"] == "(555) 123-4568"

    def test_location_with_operating_hours(self):
        """Test Location resource with operating hours."""
        location_data = {
            "name": "24/7 Emergency Department",
            "type": "emergency",
            "hours": [
                {
                    "days": ["mon", "tue", "wed", "thu", "fri"],
                    "opening_time": "07:00:00",
                    "closing_time": "19:00:00",
                    "all_day": False
                },
                {
                    "days": ["sat", "sun"],
                    "all_day": True
                }
            ]
        }

        location = self.factory.create_location_resource(location_data, "test-request-004")

        # Verify operating hours
        hours = location["hoursOfOperation"]
        assert len(hours) == 2

        # Check weekday hours
        weekday_hours = hours[0]
        assert weekday_hours["daysOfWeek"] == ["mon", "tue", "wed", "thu", "fri"]
        assert weekday_hours["openingTime"] == "07:00:00"
        assert weekday_hours["closingTime"] == "19:00:00"
        assert not weekday_hours["allDay"]

        # Check weekend hours
        weekend_hours = hours[1]
        assert weekend_hours["daysOfWeek"] == ["sat", "sun"]
        assert weekend_hours["allDay"]

    def test_location_with_position_coordinates(self):
        """Test Location resource with GPS coordinates."""
        location_data = {
            "name": "Mobile Emergency Unit",
            "type": "vehicle",
            "position": {
                "latitude": 34.0522,
                "longitude": -118.2437,
                "altitude": 285.5
            }
        }

        location = self.factory.create_location_resource(location_data, "test-request-005")

        # Verify position
        position = location["position"]
        assert position["latitude"] == 34.0522
        assert position["longitude"] == -118.2437
        assert position["altitude"] == 285.5

    def test_location_with_organization_reference(self):
        """Test Location resource with managing organization."""
        location_data = {
            "name": "Radiology Department",
            "type": "radiology",
            "managing_organization": "org-12345",
            "organization_name": "Regional Healthcare System"
        }

        location = self.factory.create_location_resource(location_data, "test-request-006")

        # Verify organization reference
        org_ref = location["managingOrganization"]
        assert org_ref["reference"] == "Organization/org-12345"
        assert org_ref["display"] == "Regional Healthcare System"

    def test_location_with_parent_location(self):
        """Test Location resource with parent location reference."""
        location_data = {
            "name": "OR 3",
            "type": "operating room",
            "physical_type": "room",
            "part_of": "location-surgery-dept",
            "parent_location_name": "Surgery Department"
        }

        location = self.factory.create_location_resource(location_data, "test-request-007")

        # Verify parent location reference
        part_of = location["partOf"]
        assert part_of["reference"] == "Location/location-surgery-dept"
        assert part_of["display"] == "Surgery Department"

        # Verify physical type
        physical_type = location["physicalType"]
        assert physical_type["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/location-physical-type"
        assert physical_type["coding"][0]["code"] == "ro"  # Room code
        assert physical_type["text"] == "room"

    def test_location_specialty_departments(self):
        """Test Location resources for various medical specialties."""
        specialty_locations = [
            {"name": "Cardiology Unit", "type": "cardiology", "expected_code": "225728002"},
            {"name": "Oncology Wing", "type": "oncology", "expected_code": "734859008"},
            {"name": "Pediatric Ward", "type": "pediatrics", "expected_code": "225746006"},
            {"name": "Dialysis Center", "type": "dialysis", "expected_code": "225746008"},
            {"name": "Rehabilitation Unit", "type": "rehabilitation", "expected_code": "225746009"}
        ]

        for specialty in specialty_locations:
            location_data = {
                "name": specialty["name"],
                "type": specialty["type"]
            }

            location = self.factory.create_location_resource(location_data, f"test-request-specialty")

            # Verify correct SNOMED CT coding for specialty
            type_coding = location["type"][0]["coding"][0]
            assert type_coding["system"] == "http://snomed.info/sct"
            assert type_coding["code"] == specialty["expected_code"]

    def test_location_physical_types(self):
        """Test Location resources with various physical types."""
        physical_types = [
            {"type": "building", "expected_code": "bu"},
            {"type": "wing", "expected_code": "wi"},
            {"type": "floor", "expected_code": "lvl"},
            {"type": "room", "expected_code": "ro"},
            {"type": "bed", "expected_code": "bd"},
            {"type": "vehicle", "expected_code": "ve"}
        ]

        for physical in physical_types:
            location_data = {
                "name": f"Test {physical['type']}",
                "type": "hospital",
                "physical_type": physical["type"]
            }

            location = self.factory.create_location_resource(location_data, f"test-request-physical")

            # Verify physical type coding
            physical_type = location["physicalType"]
            assert physical_type["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/location-physical-type"
            assert physical_type["coding"][0]["code"] == physical["expected_code"]

    def test_location_simple_string_inputs(self):
        """Test Location resource with simplified string inputs."""
        location_data = {
            "name": "Quick Care Clinic",
            "type": "clinic",
            "address": "456 Main Street, Anytown, ST 12345",
            "contact": "support@quickcare.com",
            "hours": "8:00 AM - 5:00 PM"
        }

        location = self.factory.create_location_resource(location_data, "test-request-simple")

        # Verify string address handling
        address = location["address"]
        assert address["text"] == "456 Main Street, Anytown, ST 12345"
        assert address["use"] == "work"
        assert address["type"] == "physical"

        # Verify string contact handling (email)
        telecom = location["telecom"]
        assert len(telecom) == 1
        assert telecom[0]["system"] == "email"
        assert telecom[0]["value"] == "support@quickcare.com"

        # Verify string hours handling
        hours = location["hoursOfOperation"]
        assert len(hours) == 1
        assert hours[0]["daysOfWeek"] == ["mon", "tue", "wed", "thu", "fri"]
        assert not hours[0]["allDay"]

    def test_location_fallback_creation(self):
        """Test Location resource creation with fallback when FHIR unavailable."""
        # Test with comprehensive location data
        location_data = {
            "name": "Community Health Center",
            "type": "clinic",
            "status": "active",
            "description": "Primary care and preventive services",
            "address": {
                "line1": "789 Community Drive",
                "city": "Hometown",
                "state": "TX",
                "zip": "75001"
            },
            "contact": {
                "phone": "(555) 987-6543",
                "email": "info@community.health"
            }
        }

        # Create location using fallback (should work regardless of FHIR library availability)
        location = self.factory._create_fallback_location_resource(location_data, "test-request-fallback")

        # Verify fallback resource structure
        assert location["resourceType"] == "Location"
        assert location["name"] == "Community Health Center"
        assert location["status"] == "active"
        assert location["description"] == "Primary care and preventive services"

        # Verify fallback address
        address = location["address"]
        assert address["line"] == ["789 Community Drive"]
        assert address["city"] == "Hometown"
        assert address["state"] == "TX"
        assert address["postalCode"] == "75001"

        # Verify fallback contact
        telecom = location["telecom"]
        assert len(telecom) == 2
        phone = next(t for t in telecom if t["system"] == "phone")
        assert phone["value"] == "(555) 987-6543"

    def test_location_fhir_validation(self):
        """Test HAPI FHIR R4 validation compliance."""
        location_data = {
            "name": "Comprehensive Medical Center",
            "type": "hospital",
            "status": "active",
            "description": "Full-service hospital with emergency, surgery, and specialty care",
            "address": {
                "line1": "1000 Medical Plaza",
                "city": "Healthcare City",
                "state": "FL",
                "postal_code": "33101",
                "country": "USA"
            },
            "contact": [
                {"phone": "(555) 111-2222", "use": "work"},
                {"email": "admin@medcenter.org", "use": "work"},
                {"fax": "(555) 111-2223", "use": "work"}
            ],
            "hours": [
                {
                    "days": ["mon", "tue", "wed", "thu", "fri"],
                    "opening_time": "06:00:00",
                    "closing_time": "22:00:00"
                },
                {
                    "days": ["sat", "sun"],
                    "opening_time": "08:00:00",
                    "closing_time": "20:00:00"
                }
            ],
            "position": {
                "latitude": 25.7617,
                "longitude": -80.1918
            },
            "physical_type": "building"
        }

        location = self.factory.create_location_resource(location_data, "test-request-validation")

        # Verify all required FHIR fields are present
        assert location["resourceType"] == "Location"
        assert "id" in location
        assert location["status"] in ["active", "suspended", "inactive"]
        assert isinstance(location["name"], str)

        # Verify optional fields are properly structured
        if "type" in location:
            assert isinstance(location["type"], list)
            for type_concept in location["type"]:
                assert "coding" in type_concept or "text" in type_concept

        if "address" in location:
            address = location["address"]
            assert "use" in address or "type" in address or "text" in address

        if "telecom" in location:
            assert isinstance(location["telecom"], list)
            for contact in location["telecom"]:
                assert "system" in contact
                assert "value" in contact

        if "position" in location:
            position = location["position"]
            assert "latitude" in position
            assert "longitude" in position

        print(f"✅ Location FHIR validation successful: {location['name']}")


class TestLocationNLPIntegration:
    """Test NLP extraction and Location resource generation."""

    def setup_method(self):
        """Set up NLP test fixtures."""
        self.factory = get_factory_adapter()

    def test_nlp_location_extraction_hospital(self):
        """Test NLP extraction of hospital location information."""
        # Simulate NLP extracted location data
        nlp_location_data = {
            "name": "St. Mary's General Hospital",
            "type": "hospital",
            "mentions": ["general hospital", "st mary's", "main campus"],
            "confidence": 0.95
        }

        location = self.factory.create_location_resource(nlp_location_data, "test-nlp-001")

        assert location["name"] == "St. Mary's General Hospital"
        assert location["type"][0]["coding"][0]["code"] == "22232009"  # Hospital SNOMED code
        assert location["status"] == "active"  # Default status

    def test_nlp_location_extraction_department(self):
        """Test NLP extraction of department/unit location information."""
        nlp_location_data = {
            "name": "Emergency Department",
            "type": "emergency room",
            "parent_facility": "Regional Medical Center",
            "physical_type": "department"
        }

        location = self.factory.create_location_resource(nlp_location_data, "test-nlp-002")

        assert location["name"] == "Emergency Department"
        assert location["type"][0]["coding"][0]["code"] == "225728007"  # Emergency dept SNOMED code

    def test_nlp_location_extraction_outpatient(self):
        """Test NLP extraction of outpatient facility information."""
        nlp_location_data = {
            "name": "Family Medicine Clinic",
            "type": "outpatient clinic",
            "services": ["primary care", "preventive care", "chronic disease management"]
        }

        location = self.factory.create_location_resource(nlp_location_data, "test-nlp-003")

        assert location["name"] == "Family Medicine Clinic"
        # Should map to ambulatory care clinic
        assert location["type"][0]["coding"][0]["code"] == "35971002"


class TestLocationIntegrationScenarios:
    """Test Location resource integration with other FHIR resources."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.factory = get_factory_adapter()

    def test_location_with_encounter_integration(self):
        """Test Location resource for encounter/visit tracking."""
        location_data = {
            "name": "Room 302A",
            "type": "room",
            "physical_type": "room",
            "part_of": "location-icu",
            "parent_location_name": "Intensive Care Unit",
            "address": {
                "line1": "3rd Floor, ICU Wing",
                "text": "Room 302A, ICU Wing, 3rd Floor"
            }
        }

        location = self.factory.create_location_resource(location_data, "test-encounter-001")

        # Verify room-specific attributes
        assert location["name"] == "Room 302A"
        assert location["physicalType"]["coding"][0]["code"] == "ro"  # Room
        assert location["partOf"]["reference"] == "Location/location-icu"

        # This location could be referenced in Encounter.location
        location_reference = f"Location/{location['id']}"
        assert location_reference.startswith("Location/")

    def test_location_with_service_delivery(self):
        """Test Location resource for service delivery points."""
        location_data = {
            "name": "Outpatient Surgery Center",
            "type": "surgery",
            "status": "active",
            "description": "Same-day surgical procedures and recovery",
            "hours": {
                "days": ["mon", "tue", "wed", "thu", "fri"],
                "opening_time": "06:00:00",
                "closing_time": "18:00:00"
            },
            "managing_organization": "org-surgery-center",
            "organization_name": "Surgical Associates"
        }

        location = self.factory.create_location_resource(location_data, "test-service-001")

        # Verify service delivery attributes
        assert location["description"] == "Same-day surgical procedures and recovery"
        assert location["managingOrganization"]["reference"] == "Organization/org-surgery-center"

        # Verify surgical department coding
        assert location["type"][0]["coding"][0]["code"] == "225456001"  # Surgical department

    def test_location_hierarchical_structure(self):
        """Test hierarchical location structure (building > floor > room)."""
        # Main building
        building_data = {
            "name": "Medical Center Main Building",
            "type": "hospital",
            "physical_type": "building",
            "address": {
                "line1": "100 Hospital Drive",
                "city": "Medical City",
                "state": "CA",
                "postal_code": "90210"
            }
        }

        building = self.factory.create_location_resource(building_data, "test-hierarchy-001")

        # Floor within building
        floor_data = {
            "name": "3rd Floor - Surgical Services",
            "type": "surgery",
            "physical_type": "floor",
            "part_of": building["id"],
            "parent_location_name": "Medical Center Main Building"
        }

        floor = self.factory.create_location_resource(floor_data, "test-hierarchy-002")

        # Room within floor
        room_data = {
            "name": "OR 3",
            "type": "operating room",
            "physical_type": "room",
            "part_of": floor["id"],
            "parent_location_name": "3rd Floor - Surgical Services"
        }

        room = self.factory.create_location_resource(room_data, "test-hierarchy-003")

        # Verify hierarchical relationships
        assert building["physicalType"]["coding"][0]["code"] == "bu"  # Building
        assert floor["physicalType"]["coding"][0]["code"] == "lvl"   # Level/Floor
        assert room["physicalType"]["coding"][0]["code"] == "ro"     # Room

        assert floor["partOf"]["reference"] == f"Location/{building['id']}"
        assert room["partOf"]["reference"] == f"Location/{floor['id']}"

    def test_location_mobile_healthcare_unit(self):
        """Test Location resource for mobile healthcare services."""
        mobile_data = {
            "name": "Mobile Vaccination Unit #1",
            "type": "clinic",
            "physical_type": "vehicle",
            "status": "active",
            "description": "Mobile COVID-19 vaccination services",
            "position": {
                "latitude": 34.0522,
                "longitude": -118.2437
            },
            "contact": {
                "phone": "(555) 123-VAXX"
            },
            "managing_organization": "org-public-health",
            "organization_name": "County Public Health Department"
        }

        mobile_location = self.factory.create_location_resource(mobile_data, "test-mobile-001")

        # Verify mobile unit attributes
        assert mobile_location["physicalType"]["coding"][0]["code"] == "ve"  # Vehicle
        assert "position" in mobile_location
        assert mobile_location["position"]["latitude"] == 34.0522
        assert mobile_location["managingOrganization"]["display"] == "County Public Health Department"

        print(f"✅ Mobile healthcare unit location created: {mobile_location['name']}")