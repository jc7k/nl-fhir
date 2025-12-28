"""
FHIR Organizational Resource Factory
Specialized factory for Location, Organization, and HealthcareService resources

Part of Priority Tier 1 implementation - completing the "Critical 20" resources
- Location: Score 8.6, Care delivery context and resource management
- Organization: Administrative infrastructure
- HealthcareService: Service directories and capacity planning
"""

import logging
import time
import uuid
from datetime import datetime
from typing import Any

from .base import BaseResourceFactory

logger = logging.getLogger(__name__)


class OrganizationalResourceFactory(BaseResourceFactory):
    """
    Factory for organizational FHIR resources.

    Handles Location, Organization, and HealthcareService resources
    with features:
    - Geographic position support (latitude/longitude)
    - Operating hours and availability
    - Contact information
    - Hierarchical organization structures
    - Service categorization and specialties
    """

    SUPPORTED_RESOURCES = {"Location", "Organization", "HealthcareService"}

    # Location type mappings (SNOMED CT codes)
    LOCATION_TYPE_CODES = {
        "hospital": {"code": "22232009", "display": "Hospital"},
        "clinic": {"code": "35971002", "display": "Ambulatory care site"},
        "pharmacy": {"code": "264372000", "display": "Pharmacy"},
        "laboratory": {"code": "261904005", "display": "Laboratory"},
        "imaging": {"code": "309964003", "display": "Radiology department"},
        "emergency": {"code": "225728007", "display": "Emergency department"},
        "icu": {"code": "309904001", "display": "Intensive care unit"},
        "operating_room": {"code": "225746001", "display": "Operating room"},
        "ward": {"code": "225747005", "display": "Ward"},
        "outpatient": {"code": "33022008", "display": "Outpatient clinic"},
        "home": {"code": "264362003", "display": "Home"},
        "nursing_home": {"code": "42665001", "display": "Nursing home"},
        "mobile": {"code": "261904005", "display": "Mobile unit"},
    }

    # Location physical type mappings
    PHYSICAL_TYPE_CODES = {
        "site": {"code": "si", "display": "Site"},
        "building": {"code": "bu", "display": "Building"},
        "wing": {"code": "wi", "display": "Wing"},
        "ward": {"code": "wa", "display": "Ward"},
        "level": {"code": "lvl", "display": "Level"},
        "corridor": {"code": "co", "display": "Corridor"},
        "room": {"code": "ro", "display": "Room"},
        "bed": {"code": "bd", "display": "Bed"},
        "vehicle": {"code": "ve", "display": "Vehicle"},
        "house": {"code": "ho", "display": "House"},
        "cabinet": {"code": "ca", "display": "Cabinet"},
        "road": {"code": "rd", "display": "Road"},
        "area": {"code": "area", "display": "Area"},
        "jurisdiction": {"code": "jdn", "display": "Jurisdiction"},
    }

    # Organization type mappings
    ORGANIZATION_TYPE_CODES = {
        "provider": {"code": "prov", "display": "Healthcare Provider"},
        "department": {"code": "dept", "display": "Hospital Department"},
        "team": {"code": "team", "display": "Organizational team"},
        "government": {"code": "govt", "display": "Government"},
        "insurance": {"code": "ins", "display": "Insurance Company"},
        "educational": {"code": "edu", "display": "Educational Institute"},
        "religious": {"code": "reli", "display": "Religious Institution"},
        "clinical_research": {"code": "crs", "display": "Clinical Research Sponsor"},
        "community_group": {"code": "cg", "display": "Community Group"},
        "payer": {"code": "pay", "display": "Payer"},
        "other": {"code": "other", "display": "Other"},
    }

    # Healthcare service category codes
    SERVICE_CATEGORY_CODES = {
        "general_practice": {"code": "1", "display": "General Practice"},
        "emergency": {"code": "2", "display": "Emergency"},
        "specialist": {"code": "3", "display": "Specialist Medical"},
        "diagnostic": {"code": "4", "display": "Diagnostic"},
        "pharmacy": {"code": "5", "display": "Pharmacy"},
        "mental_health": {"code": "6", "display": "Mental Health"},
        "rehabilitation": {"code": "7", "display": "Rehabilitation"},
        "aged_care": {"code": "8", "display": "Aged Care"},
        "palliative": {"code": "9", "display": "Palliative Care"},
        "dental": {"code": "10", "display": "Dental"},
        "allied_health": {"code": "11", "display": "Allied Health"},
        "hospital": {"code": "12", "display": "Hospital"},
        "transport": {"code": "13", "display": "Transport"},
    }

    def __init__(self, validators=None, coders=None, reference_manager=None):
        """Initialize organizational factory with shared components"""
        super().__init__(validators, coders, reference_manager)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._org_metrics = {}
        self.logger.info(
            "OrganizationalResourceFactory initialized for Location, Organization, HealthcareService"
        )

    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the resource type"""
        return resource_type in self.SUPPORTED_RESOURCES

    def _create_resource(
        self, resource_type: str, data: dict[str, Any], request_id: str | None = None
    ) -> dict[str, Any]:
        """Create organizational resource based on type"""
        self.logger.debug(
            f"[{request_id}] Creating {resource_type} with OrganizationalResourceFactory"
        )

        start_time = time.time()

        try:
            if resource_type == "Location":
                resource = self._create_location(data, request_id)
            elif resource_type == "Organization":
                resource = self._create_organization(data, request_id)
            elif resource_type == "HealthcareService":
                resource = self._create_healthcare_service(data, request_id)
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")

            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            self._record_org_metrics(resource_type, duration_ms, success=True)

            self.logger.info(f"[{request_id}] Created {resource_type} in {duration_ms:.2f}ms")
            return resource

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._record_org_metrics(resource_type, duration_ms, success=False)
            self.logger.error(f"[{request_id}] Failed to create {resource_type}: {e}")
            raise

    # =========================================================================
    # LOCATION RESOURCE CREATION
    # =========================================================================

    def _create_location(
        self, data: dict[str, Any], request_id: str | None = None
    ) -> dict[str, Any]:
        """
        Create Location resource with full FHIR R4 support.

        Supports:
        - Location naming and identifiers
        - Physical type and mode
        - Address and position (GPS coordinates)
        - Operating hours
        - Contact information
        - Part-of hierarchy
        """
        location = {
            "resourceType": "Location",
            "id": self._generate_location_id(data),
            "status": data.get("status", "active"),
        }

        # Name (required for meaningful location)
        if "name" in data:
            location["name"] = str(data["name"])

        # Aliases (alternative names)
        if "alias" in data:
            aliases = data["alias"]
            if isinstance(aliases, str):
                location["alias"] = [aliases]
            elif isinstance(aliases, list):
                location["alias"] = aliases

        # Description
        if "description" in data:
            location["description"] = str(data["description"])

        # Mode (instance vs kind)
        if "mode" in data:
            mode = str(data["mode"]).lower()
            if mode in ["instance", "kind"]:
                location["mode"] = mode

        # Location type (SNOMED CT coded)
        if "type" in data:
            location["type"] = [self._get_location_type_coding(data["type"])]

        # Physical type
        if "physical_type" in data:
            location["physicalType"] = self._get_physical_type_coding(data["physical_type"])

        # Identifiers
        if self._has_identifier_data(data):
            location["identifier"] = self._process_identifiers(data)

        # Telecom (contact information)
        if self._has_telecom_data(data):
            location["telecom"] = self._process_telecom(data)

        # Address
        if self._has_address_data(data):
            location["address"] = self._create_address(data.get("address", data))

        # Position (GPS coordinates)
        if self._has_position_data(data):
            location["position"] = self._create_position(data)

        # Managing organization
        if "managing_organization" in data:
            org_ref = data["managing_organization"]
            if isinstance(org_ref, str):
                location["managingOrganization"] = {"reference": f"Organization/{org_ref}"}
            elif isinstance(org_ref, dict):
                location["managingOrganization"] = org_ref

        # Part of (hierarchical location)
        if "part_of" in data:
            part_of_ref = data["part_of"]
            if isinstance(part_of_ref, str):
                location["partOf"] = {"reference": f"Location/{part_of_ref}"}
            elif isinstance(part_of_ref, dict):
                location["partOf"] = part_of_ref

        # Operating hours
        if "hours_of_operation" in data:
            location["hoursOfOperation"] = self._process_hours_of_operation(
                data["hours_of_operation"]
            )

        # Availability exceptions
        if "availability_exceptions" in data:
            location["availabilityExceptions"] = str(data["availability_exceptions"])

        # Endpoints (for electronic services)
        if "endpoint" in data:
            location["endpoint"] = self._process_endpoints(data["endpoint"])

        # Add metadata
        self._add_location_metadata(location, request_id)

        return location

    def _generate_location_id(self, data: dict[str, Any]) -> str:
        """Generate unique location ID"""
        if "id" in data:
            return str(data["id"])

        # Use name-based ID if available
        if "name" in data:
            # Create slug from name
            name_slug = str(data["name"]).lower().replace(" ", "-")[:30]
            return f"location-{name_slug}-{uuid.uuid4().hex[:8]}"

        return f"location-{uuid.uuid4()}"

    def _get_location_type_coding(self, location_type: str | dict) -> dict[str, Any]:
        """Get SNOMED CT coding for location type"""
        if isinstance(location_type, dict):
            return location_type

        type_key = str(location_type).lower().replace(" ", "_")
        type_info = self.LOCATION_TYPE_CODES.get(
            type_key, {"code": "43741000", "display": str(location_type)}
        )

        return self.create_codeable_concept(
            system="http://snomed.info/sct", code=type_info["code"], display=type_info["display"]
        )

    def _get_physical_type_coding(self, physical_type: str | dict) -> dict[str, Any]:
        """Get coding for physical type"""
        if isinstance(physical_type, dict):
            return physical_type

        type_key = str(physical_type).lower()
        type_info = self.PHYSICAL_TYPE_CODES.get(
            type_key, {"code": "area", "display": str(physical_type)}
        )

        return self.create_codeable_concept(
            system="http://terminology.hl7.org/CodeSystem/location-physical-type",
            code=type_info["code"],
            display=type_info["display"],
        )

    def _has_position_data(self, data: dict[str, Any]) -> bool:
        """Check if data contains GPS position information"""
        return any(
            key in data for key in ["latitude", "longitude", "position", "lat", "lng", "lon"]
        )

    def _create_position(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create GPS position element"""
        position = {}

        # Handle nested position object
        if "position" in data and isinstance(data["position"], dict):
            pos_data = data["position"]
            if "latitude" in pos_data:
                position["latitude"] = float(pos_data["latitude"])
            if "longitude" in pos_data:
                position["longitude"] = float(pos_data["longitude"])
            if "altitude" in pos_data:
                position["altitude"] = float(pos_data["altitude"])
            return position

        # Handle flat data
        lat = data.get("latitude") or data.get("lat")
        lng = data.get("longitude") or data.get("lng") or data.get("lon")

        if lat is not None:
            position["latitude"] = float(lat)
        if lng is not None:
            position["longitude"] = float(lng)
        if "altitude" in data:
            position["altitude"] = float(data["altitude"])

        return position

    def _process_hours_of_operation(self, hours_data: list | dict) -> list[dict[str, Any]]:
        """Process operating hours into FHIR format"""
        hours_list = []

        if isinstance(hours_data, dict):
            hours_data = [hours_data]

        for hours in hours_data:
            if not isinstance(hours, dict):
                continue

            hour_entry = {}

            # Days of week
            if "days_of_week" in hours:
                days = hours["days_of_week"]
                if isinstance(days, str):
                    hour_entry["daysOfWeek"] = [days.lower()]
                elif isinstance(days, list):
                    hour_entry["daysOfWeek"] = [d.lower() for d in days]

            # All day flag
            if "all_day" in hours:
                hour_entry["allDay"] = bool(hours["all_day"])

            # Opening time
            if "opening_time" in hours:
                hour_entry["openingTime"] = hours["opening_time"]

            # Closing time
            if "closing_time" in hours:
                hour_entry["closingTime"] = hours["closing_time"]

            if hour_entry:
                hours_list.append(hour_entry)

        return hours_list

    def _add_location_metadata(self, location: dict[str, Any], request_id: str | None):
        """Add metadata to location resource"""
        if "meta" not in location:
            location["meta"] = {}

        location["meta"]["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        if request_id:
            if "tag" not in location["meta"]:
                location["meta"]["tag"] = []
            location["meta"]["tag"].append(
                {"system": "http://hospital.local/request-id", "code": request_id}
            )

    # =========================================================================
    # ORGANIZATION RESOURCE CREATION
    # =========================================================================

    def _create_organization(
        self, data: dict[str, Any], request_id: str | None = None
    ) -> dict[str, Any]:
        """
        Create Organization resource with full FHIR R4 support.

        Supports:
        - Organization naming and identifiers (NPI, etc.)
        - Organization type coding
        - Contact information
        - Hierarchical part-of relationships
        - Address and endpoints
        """
        organization = {
            "resourceType": "Organization",
            "id": self._generate_organization_id(data),
            "active": data.get("active", True),
        }

        # Name (required)
        if "name" in data:
            organization["name"] = str(data["name"])

        # Aliases
        if "alias" in data:
            aliases = data["alias"]
            if isinstance(aliases, str):
                organization["alias"] = [aliases]
            elif isinstance(aliases, list):
                organization["alias"] = aliases

        # Organization type
        if "type" in data:
            org_type = data["type"]
            if isinstance(org_type, str):
                organization["type"] = [self._get_organization_type_coding(org_type)]
            elif isinstance(org_type, list):
                organization["type"] = [self._get_organization_type_coding(t) for t in org_type]

        # Identifiers (NPI, Tax ID, etc.)
        if self._has_identifier_data(data):
            organization["identifier"] = self._process_org_identifiers(data)

        # Telecom
        if self._has_telecom_data(data):
            organization["telecom"] = self._process_telecom(data)

        # Address
        if self._has_address_data(data):
            addresses = self._process_addresses(data)
            if addresses:
                organization["address"] = addresses

        # Part of (parent organization)
        if "part_of" in data:
            part_of_ref = data["part_of"]
            if isinstance(part_of_ref, str):
                organization["partOf"] = {"reference": f"Organization/{part_of_ref}"}
            elif isinstance(part_of_ref, dict):
                organization["partOf"] = part_of_ref

        # Contact persons
        if "contact" in data:
            organization["contact"] = self._process_org_contacts(data["contact"])

        # Endpoints
        if "endpoint" in data:
            organization["endpoint"] = self._process_endpoints(data["endpoint"])

        # Add metadata
        self._add_organization_metadata(organization, request_id)

        return organization

    def _generate_organization_id(self, data: dict[str, Any]) -> str:
        """Generate unique organization ID"""
        if "id" in data:
            return str(data["id"])

        # Use NPI if available
        if "npi" in data:
            return f"org-npi-{data['npi']}"

        # Use name-based ID if available
        if "name" in data:
            name_slug = str(data["name"]).lower().replace(" ", "-")[:30]
            return f"org-{name_slug}-{uuid.uuid4().hex[:8]}"

        return f"organization-{uuid.uuid4()}"

    def _get_organization_type_coding(self, org_type: str | dict) -> dict[str, Any]:
        """Get coding for organization type"""
        if isinstance(org_type, dict):
            return org_type

        type_key = str(org_type).lower().replace(" ", "_")
        type_info = self.ORGANIZATION_TYPE_CODES.get(
            type_key, {"code": "other", "display": str(org_type)}
        )

        return self.create_codeable_concept(
            system="http://terminology.hl7.org/CodeSystem/organization-type",
            code=type_info["code"],
            display=type_info["display"],
        )

    def _process_org_identifiers(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Process organization identifiers including NPI"""
        identifiers = []

        # National Provider Identifier (NPI)
        if "npi" in data:
            identifiers.append(
                {
                    "use": "official",
                    "type": self.create_codeable_concept(
                        system="http://terminology.hl7.org/CodeSystem/v2-0203",
                        code="NPI",
                        display="National provider identifier",
                    ),
                    "system": "http://hl7.org/fhir/sid/us-npi",
                    "value": str(data["npi"]),
                }
            )

        # Tax ID / EIN
        if "tax_id" in data or "ein" in data:
            tax_id = data.get("tax_id") or data.get("ein")
            identifiers.append(
                {
                    "use": "official",
                    "type": self.create_codeable_concept(
                        system="http://terminology.hl7.org/CodeSystem/v2-0203",
                        code="TAX",
                        display="Tax ID number",
                    ),
                    "system": "urn:oid:2.16.840.1.113883.4.4",
                    "value": str(tax_id),
                }
            )

        # Generic identifiers
        if "identifier" in data:
            id_data = data["identifier"]
            if isinstance(id_data, list):
                for id_info in id_data:
                    if isinstance(id_info, dict) and "value" in id_info:
                        identifier = {
                            "use": id_info.get("use", "secondary"),
                            "value": str(id_info["value"]),
                        }
                        if "system" in id_info:
                            identifier["system"] = id_info["system"]
                        if "type" in id_info:
                            identifier["type"] = id_info["type"]
                        identifiers.append(identifier)

        return identifiers

    def _process_org_contacts(self, contact_data: list | dict) -> list[dict[str, Any]]:
        """Process organization contact persons"""
        contacts = []

        if isinstance(contact_data, dict):
            contact_data = [contact_data]

        for contact in contact_data:
            if not isinstance(contact, dict):
                continue

            contact_entry = {}

            # Purpose
            if "purpose" in contact:
                contact_entry["purpose"] = self.create_codeable_concept(
                    system="http://terminology.hl7.org/CodeSystem/contactentity-type",
                    code=contact["purpose"],
                    display=contact.get("purpose_display", contact["purpose"]),
                )

            # Name
            if "name" in contact:
                name_data = contact["name"]
                if isinstance(name_data, str):
                    contact_entry["name"] = {"text": name_data}
                elif isinstance(name_data, dict):
                    contact_entry["name"] = name_data

            # Telecom
            if any(k in contact for k in ["phone", "email", "telecom"]):
                contact_entry["telecom"] = self._process_telecom(contact)

            # Address
            if "address" in contact:
                contact_entry["address"] = self._create_address(contact["address"])

            if contact_entry:
                contacts.append(contact_entry)

        return contacts

    def _add_organization_metadata(self, organization: dict[str, Any], request_id: str | None):
        """Add metadata to organization resource"""
        if "meta" not in organization:
            organization["meta"] = {}

        organization["meta"]["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        if request_id:
            if "tag" not in organization["meta"]:
                organization["meta"]["tag"] = []
            organization["meta"]["tag"].append(
                {"system": "http://hospital.local/request-id", "code": request_id}
            )

    # =========================================================================
    # HEALTHCARESERVICE RESOURCE CREATION
    # =========================================================================

    def _create_healthcare_service(
        self, data: dict[str, Any], request_id: str | None = None
    ) -> dict[str, Any]:
        """
        Create HealthcareService resource with full FHIR R4 support.

        Supports:
        - Service naming and identifiers
        - Category and type coding
        - Specialty information
        - Location and organization references
        - Availability and eligibility
        - Communication and referral methods
        """
        service = {
            "resourceType": "HealthcareService",
            "id": self._generate_service_id(data),
            "active": data.get("active", True),
        }

        # Name
        if "name" in data:
            service["name"] = str(data["name"])

        # Comment/description
        if "comment" in data:
            service["comment"] = str(data["comment"])

        # Extra details
        if "extra_details" in data:
            service["extraDetails"] = str(data["extra_details"])

        # Identifiers
        if self._has_identifier_data(data):
            service["identifier"] = self._process_identifiers(data)

        # Provided by (organization)
        if "provided_by" in data:
            org_ref = data["provided_by"]
            if isinstance(org_ref, str):
                service["providedBy"] = {"reference": f"Organization/{org_ref}"}
            elif isinstance(org_ref, dict):
                service["providedBy"] = org_ref

        # Category
        if "category" in data:
            categories = data["category"]
            if isinstance(categories, str):
                service["category"] = [self._get_service_category_coding(categories)]
            elif isinstance(categories, list):
                service["category"] = [self._get_service_category_coding(c) for c in categories]

        # Type
        if "type" in data:
            types = data["type"]
            if isinstance(types, str):
                service["type"] = [
                    self.create_codeable_concept(
                        system="http://terminology.hl7.org/CodeSystem/service-type",
                        code=types,
                        display=types,
                    )
                ]
            elif isinstance(types, list):
                service["type"] = [
                    self.create_codeable_concept(
                        system="http://terminology.hl7.org/CodeSystem/service-type",
                        code=t if isinstance(t, str) else t.get("code", "unknown"),
                        display=t if isinstance(t, str) else t.get("display", ""),
                    )
                    for t in types
                ]

        # Specialty (SNOMED CT coded)
        if "specialty" in data:
            specialties = data["specialty"]
            if isinstance(specialties, str):
                service["specialty"] = [
                    self.create_codeable_concept(
                        system="http://snomed.info/sct",
                        code="394814009",
                        display=specialties,
                    )
                ]
            elif isinstance(specialties, list):
                service["specialty"] = [
                    self.create_codeable_concept(
                        system="http://snomed.info/sct",
                        code=s.get("code", "394814009") if isinstance(s, dict) else "394814009",
                        display=s.get("display", s) if isinstance(s, dict) else s,
                    )
                    for s in specialties
                ]

        # Location references
        if "location" in data:
            locations = data["location"]
            if isinstance(locations, str):
                service["location"] = [{"reference": f"Location/{locations}"}]
            elif isinstance(locations, list):
                service["location"] = [
                    {
                        "reference": f"Location/{loc}"
                        if isinstance(loc, str)
                        else loc.get("reference", "")
                    }
                    for loc in locations
                ]

        # Telecom
        if self._has_telecom_data(data):
            service["telecom"] = self._process_telecom(data)

        # Coverage area
        if "coverage_area" in data:
            coverage = data["coverage_area"]
            if isinstance(coverage, str):
                service["coverageArea"] = [{"reference": f"Location/{coverage}"}]
            elif isinstance(coverage, list):
                service["coverageArea"] = [
                    {"reference": f"Location/{c}" if isinstance(c, str) else c.get("reference", "")}
                    for c in coverage
                ]

        # Service provision codes
        if "service_provision_code" in data:
            codes = data["service_provision_code"]
            if isinstance(codes, str):
                service["serviceProvisionCode"] = [
                    self.create_codeable_concept(
                        system="http://terminology.hl7.org/CodeSystem/service-provision-conditions",
                        code=codes,
                        display=codes,
                    )
                ]
            elif isinstance(codes, list):
                service["serviceProvisionCode"] = [
                    self.create_codeable_concept(
                        system="http://terminology.hl7.org/CodeSystem/service-provision-conditions",
                        code=c,
                        display=c,
                    )
                    for c in codes
                ]

        # Eligibility
        if "eligibility" in data:
            service["eligibility"] = self._process_eligibility(data["eligibility"])

        # Programs
        if "program" in data:
            programs = data["program"]
            if isinstance(programs, str):
                service["program"] = [
                    self.create_codeable_concept(
                        system="http://terminology.hl7.org/CodeSystem/program",
                        code=programs,
                        display=programs,
                    )
                ]
            elif isinstance(programs, list):
                service["program"] = [
                    self.create_codeable_concept(
                        system="http://terminology.hl7.org/CodeSystem/program",
                        code=p,
                        display=p,
                    )
                    for p in programs
                ]

        # Characteristics
        if "characteristic" in data:
            service["characteristic"] = self._process_characteristics(data["characteristic"])

        # Communication languages
        if "communication" in data:
            communications = data["communication"]
            if isinstance(communications, str):
                service["communication"] = [
                    self.create_codeable_concept(
                        system="urn:ietf:bcp:47", code=communications, display=communications
                    )
                ]
            elif isinstance(communications, list):
                service["communication"] = [
                    self.create_codeable_concept(system="urn:ietf:bcp:47", code=c, display=c)
                    for c in communications
                ]

        # Referral method
        if "referral_method" in data:
            methods = data["referral_method"]
            if isinstance(methods, str):
                service["referralMethod"] = [
                    self.create_codeable_concept(
                        system="http://terminology.hl7.org/CodeSystem/service-referral-method",
                        code=methods,
                        display=methods,
                    )
                ]
            elif isinstance(methods, list):
                service["referralMethod"] = [
                    self.create_codeable_concept(
                        system="http://terminology.hl7.org/CodeSystem/service-referral-method",
                        code=m,
                        display=m,
                    )
                    for m in methods
                ]

        # Appointment required
        if "appointment_required" in data:
            service["appointmentRequired"] = bool(data["appointment_required"])

        # Available time
        if "available_time" in data:
            service["availableTime"] = self._process_available_time(data["available_time"])

        # Not available
        if "not_available" in data:
            service["notAvailable"] = self._process_not_available(data["not_available"])

        # Availability exceptions
        if "availability_exceptions" in data:
            service["availabilityExceptions"] = str(data["availability_exceptions"])

        # Endpoints
        if "endpoint" in data:
            service["endpoint"] = self._process_endpoints(data["endpoint"])

        # Add metadata
        self._add_service_metadata(service, request_id)

        return service

    def _generate_service_id(self, data: dict[str, Any]) -> str:
        """Generate unique service ID"""
        if "id" in data:
            return str(data["id"])

        if "name" in data:
            name_slug = str(data["name"]).lower().replace(" ", "-")[:30]
            return f"service-{name_slug}-{uuid.uuid4().hex[:8]}"

        return f"healthcare-service-{uuid.uuid4()}"

    def _get_service_category_coding(self, category: str | dict) -> dict[str, Any]:
        """Get coding for service category"""
        if isinstance(category, dict):
            return category

        cat_key = str(category).lower().replace(" ", "_")
        cat_info = self.SERVICE_CATEGORY_CODES.get(cat_key, {"code": "0", "display": str(category)})

        return self.create_codeable_concept(
            system="http://terminology.hl7.org/CodeSystem/service-category",
            code=cat_info["code"],
            display=cat_info["display"],
        )

    def _process_eligibility(self, eligibility_data: list | dict) -> list[dict[str, Any]]:
        """Process service eligibility criteria"""
        eligibility_list = []

        if isinstance(eligibility_data, dict):
            eligibility_data = [eligibility_data]

        for elig in eligibility_data:
            if not isinstance(elig, dict):
                continue

            entry = {}

            if "code" in elig:
                entry["code"] = self.create_codeable_concept(
                    system="http://terminology.hl7.org/CodeSystem/service-eligibility",
                    code=elig["code"],
                    display=elig.get("display", elig["code"]),
                )

            if "comment" in elig:
                entry["comment"] = str(elig["comment"])

            if entry:
                eligibility_list.append(entry)

        return eligibility_list

    def _process_characteristics(self, char_data: list | str) -> list[dict[str, Any]]:
        """Process service characteristics"""
        if isinstance(char_data, str):
            return [
                self.create_codeable_concept(
                    system="http://terminology.hl7.org/CodeSystem/service-characteristic",
                    code=char_data,
                    display=char_data,
                )
            ]

        return [
            self.create_codeable_concept(
                system="http://terminology.hl7.org/CodeSystem/service-characteristic",
                code=c if isinstance(c, str) else c.get("code", ""),
                display=c if isinstance(c, str) else c.get("display", ""),
            )
            for c in char_data
        ]

    def _process_available_time(self, time_data: list | dict) -> list[dict[str, Any]]:
        """Process available time slots"""
        time_list = []

        if isinstance(time_data, dict):
            time_data = [time_data]

        for slot in time_data:
            if not isinstance(slot, dict):
                continue

            entry = {}

            if "days_of_week" in slot:
                days = slot["days_of_week"]
                entry["daysOfWeek"] = [days] if isinstance(days, str) else days

            if "all_day" in slot:
                entry["allDay"] = bool(slot["all_day"])

            if "available_start_time" in slot:
                entry["availableStartTime"] = slot["available_start_time"]

            if "available_end_time" in slot:
                entry["availableEndTime"] = slot["available_end_time"]

            if entry:
                time_list.append(entry)

        return time_list

    def _process_not_available(self, not_avail_data: list | dict) -> list[dict[str, Any]]:
        """Process not available periods"""
        not_avail_list = []

        if isinstance(not_avail_data, dict):
            not_avail_data = [not_avail_data]

        for period in not_avail_data:
            if not isinstance(period, dict):
                continue

            entry = {}

            if "description" in period:
                entry["description"] = str(period["description"])

            if "during" in period:
                during = period["during"]
                entry["during"] = {}
                if "start" in during:
                    entry["during"]["start"] = during["start"]
                if "end" in during:
                    entry["during"]["end"] = during["end"]

            if entry:
                not_avail_list.append(entry)

        return not_avail_list

    def _add_service_metadata(self, service: dict[str, Any], request_id: str | None):
        """Add metadata to healthcare service resource"""
        if "meta" not in service:
            service["meta"] = {}

        service["meta"]["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        if request_id:
            if "tag" not in service["meta"]:
                service["meta"]["tag"] = []
            service["meta"]["tag"].append(
                {"system": "http://hospital.local/request-id", "code": request_id}
            )

    # =========================================================================
    # SHARED HELPER METHODS
    # =========================================================================

    def _has_identifier_data(self, data: dict[str, Any]) -> bool:
        """Check if data contains identifier information"""
        return any(key in data for key in ["identifier", "npi", "tax_id", "ein"])

    def _process_identifiers(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Process generic identifiers"""
        identifiers = []

        if "identifier" in data:
            id_data = data["identifier"]
            if isinstance(id_data, list):
                for id_info in id_data:
                    if isinstance(id_info, dict) and "value" in id_info:
                        identifier = {
                            "use": id_info.get("use", "usual"),
                            "value": str(id_info["value"]),
                        }
                        if "system" in id_info:
                            identifier["system"] = id_info["system"]
                        if "type" in id_info:
                            identifier["type"] = id_info["type"]
                        identifiers.append(identifier)
            elif isinstance(id_data, dict) and "value" in id_data:
                identifiers.append(
                    {
                        "use": id_data.get("use", "usual"),
                        "system": id_data.get("system"),
                        "value": str(id_data["value"]),
                    }
                )

        return identifiers

    def _has_telecom_data(self, data: dict[str, Any]) -> bool:
        """Check if data contains telecom information"""
        return any(key in data for key in ["phone", "email", "fax", "url", "telecom"])

    def _process_telecom(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Process telecom contact information"""
        telecom = []

        # Phone
        if "phone" in data:
            telecom.append({"system": "phone", "value": str(data["phone"]), "use": "work"})

        # Email
        if "email" in data:
            telecom.append({"system": "email", "value": str(data["email"]), "use": "work"})

        # Fax
        if "fax" in data:
            telecom.append({"system": "fax", "value": str(data["fax"]), "use": "work"})

        # URL
        if "url" in data:
            telecom.append({"system": "url", "value": str(data["url"]), "use": "work"})

        # Structured telecom
        if "telecom" in data:
            for t in data["telecom"]:
                if isinstance(t, dict) and "system" in t and "value" in t:
                    telecom.append(
                        {
                            "system": t["system"],
                            "value": str(t["value"]),
                            "use": t.get("use", "work"),
                        }
                    )

        return telecom

    def _has_address_data(self, data: dict[str, Any]) -> bool:
        """Check if data contains address information"""
        return any(key in data for key in ["address", "addresses"])

    def _create_address(self, addr_data: Any) -> dict[str, Any] | None:
        """Create FHIR address structure"""
        if not addr_data:
            return None

        if isinstance(addr_data, str):
            return {"use": "work", "type": "both", "text": addr_data.strip()}

        if not isinstance(addr_data, dict):
            return None

        address = {"use": addr_data.get("use", "work"), "type": addr_data.get("type", "both")}

        # Address lines
        lines = []
        for line_key in ["line1", "line2", "line", "street"]:
            if line_key in addr_data:
                line_data = addr_data[line_key]
                if isinstance(line_data, list):
                    lines.extend(line_data)
                elif line_data:
                    lines.append(str(line_data))

        if lines:
            address["line"] = lines

        # City, state, postal code, country
        for fhir_key, data_keys in [
            ("city", ["city"]),
            ("district", ["district", "county"]),
            ("state", ["state", "region"]),
            ("postalCode", ["postal_code", "zip", "zipcode", "postalCode"]),
            ("country", ["country"]),
        ]:
            for key in data_keys:
                if key in addr_data and addr_data[key]:
                    address[fhir_key] = str(addr_data[key])
                    break

        # Build text if components exist
        if any(key in address for key in ["line", "city", "state", "postalCode"]):
            text_parts = []
            if "line" in address:
                text_parts.extend(address["line"])
            if "city" in address:
                text_parts.append(address["city"])
            if "state" in address:
                text_parts.append(address["state"])
            if "postalCode" in address:
                text_parts.append(address["postalCode"])
            address["text"] = ", ".join(text_parts)

        return address if len(address) > 2 else None

    def _process_addresses(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Process multiple addresses"""
        addresses = []

        if "address" in data:
            addr = self._create_address(data["address"])
            if addr:
                addresses.append(addr)

        if "addresses" in data:
            for addr_data in data["addresses"]:
                addr = self._create_address(addr_data)
                if addr:
                    addresses.append(addr)

        return addresses

    def _process_endpoints(self, endpoint_data: list | str) -> list[dict[str, Any]]:
        """Process endpoint references"""
        endpoints = []

        if isinstance(endpoint_data, str):
            endpoints.append({"reference": f"Endpoint/{endpoint_data}"})
        elif isinstance(endpoint_data, list):
            for ep in endpoint_data:
                if isinstance(ep, str):
                    endpoints.append({"reference": f"Endpoint/{ep}"})
                elif isinstance(ep, dict):
                    endpoints.append(ep)

        return endpoints

    # =========================================================================
    # METRICS AND HEALTH
    # =========================================================================

    def _record_org_metrics(self, resource_type: str, duration_ms: float, success: bool = True):
        """Record organizational factory specific metrics"""
        if resource_type not in self._org_metrics:
            self._org_metrics[resource_type] = {
                "count": 0,
                "success_count": 0,
                "error_count": 0,
                "total_duration_ms": 0,
                "max_duration_ms": 0,
                "min_duration_ms": float("inf"),
            }

        metrics = self._org_metrics[resource_type]
        metrics["count"] += 1
        metrics["total_duration_ms"] += duration_ms
        metrics["max_duration_ms"] = max(metrics["max_duration_ms"], duration_ms)
        metrics["min_duration_ms"] = min(metrics["min_duration_ms"], duration_ms)

        if success:
            metrics["success_count"] += 1
        else:
            metrics["error_count"] += 1

        # Log performance warning if slow
        if duration_ms > 50:
            self.logger.warning(f"Slow {resource_type} creation: {duration_ms:.2f}ms")

    def get_org_metrics(self) -> dict[str, Any]:
        """Get organizational factory performance metrics"""
        metrics = {}
        for resource_type, data in self._org_metrics.items():
            if data["count"] > 0:
                metrics[resource_type] = {
                    "count": data["count"],
                    "success_rate": data["success_count"] / data["count"],
                    "error_rate": data["error_count"] / data["count"],
                    "avg_duration_ms": data["total_duration_ms"] / data["count"],
                    "max_duration_ms": data["max_duration_ms"],
                    "min_duration_ms": (
                        data["min_duration_ms"] if data["min_duration_ms"] != float("inf") else 0
                    ),
                }
        return metrics

    def get_health_status(self) -> dict[str, Any]:
        """Get organizational factory health status"""
        total_requests = sum(m["count"] for m in self._org_metrics.values())
        total_errors = sum(m["error_count"] for m in self._org_metrics.values())

        if total_requests > 0:
            error_rate = total_errors / total_requests
            avg_duration = (
                sum(m["total_duration_ms"] for m in self._org_metrics.values()) / total_requests
            )
        else:
            error_rate = 0
            avg_duration = 0

        return {
            "status": "healthy" if error_rate < 0.05 and avg_duration < 50 else "degraded",
            "total_requests": total_requests,
            "error_rate": error_rate,
            "avg_duration_ms": avg_duration,
            "supported_resources": list(self.SUPPORTED_RESOURCES),
            "performance_target_met": avg_duration < 50,
        }
