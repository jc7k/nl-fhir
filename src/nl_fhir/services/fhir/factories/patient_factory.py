"""
FHIR Patient Resource Factory - REFACTOR-003
Specialized factory for patient-related FHIR resources with enhanced functionality
"""

from typing import Dict, Any, List, Optional, Union
import logging
import re
import time
import uuid
from datetime import datetime

from .base import BaseResourceFactory

logger = logging.getLogger(__name__)


class PatientResourceFactory(BaseResourceFactory):
    """
    Factory for patient-related FHIR resources.

    Handles Patient, RelatedPerson, Person, PractitionerRole resources
    with advanced features:
    - Name parsing and normalization
    - Identifier generation with MRN support
    - Address standardization
    - Telecom validation and formatting
    - Demographics validation
    """

    SUPPORTED_RESOURCES = {
        'Patient', 'RelatedPerson', 'Person', 'PractitionerRole'
    }

    def __init__(self, validators=None, coders=None, reference_manager=None):
        """Initialize patient factory with shared components"""
        super().__init__(validators, coders, reference_manager)
        self.logger = logging.getLogger(self.__class__.__name__)
        self._patient_metrics = {}
        self.logger.info("PatientResourceFactory initialized with specialized patient handling")

    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the resource type"""
        return resource_type in self.SUPPORTED_RESOURCES

    def _create_resource(self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create patient-related resource based on type"""
        self.logger.debug(f"[{request_id}] Creating {resource_type} resource with PatientResourceFactory")

        start_time = time.time()

        try:
            if resource_type == 'Patient':
                resource = self._create_patient(data, request_id)
            elif resource_type == 'RelatedPerson':
                resource = self._create_related_person(data, request_id)
            elif resource_type == 'Person':
                resource = self._create_person(data, request_id)
            elif resource_type == 'PractitionerRole':
                resource = self._create_practitioner_role(data, request_id)
            else:
                raise ValueError(f"Unsupported resource type: {resource_type}")

            # Record metrics
            duration_ms = (time.time() - start_time) * 1000
            self._record_patient_metrics(resource_type, duration_ms, success=True)

            self.logger.info(f"[{request_id}] Created {resource_type} resource in {duration_ms:.2f}ms")
            return resource

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._record_patient_metrics(resource_type, duration_ms, success=False)
            self.logger.error(f"[{request_id}] Failed to create {resource_type}: {e}")
            raise

    def _create_patient(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create Patient resource with full demographics"""
        # Start with basic structure
        patient = {
            'resourceType': 'Patient',
            'id': self._generate_patient_id(data),
            'active': data.get('active', True)
        }

        # Process names - support multiple formats
        if self._has_name_data(data):
            patient['name'] = self._process_names(data)

        # Process identifiers (MRN, SSN, etc.)
        if self._has_identifier_data(data):
            patient['identifier'] = self._process_identifiers(data)

        # Demographics
        if 'gender' in data:
            patient['gender'] = self._normalize_gender(data['gender'])

        if self._has_birth_date_data(data):
            patient['birthDate'] = self._normalize_birth_date(data)

        # Contact information
        if self._has_telecom_data(data):
            patient['telecom'] = self._process_telecom(data)

        # Addresses
        if self._has_address_data(data):
            patient['address'] = self._process_addresses(data)

        # Marital status
        if 'marital_status' in data:
            patient['maritalStatus'] = self._process_marital_status(data['marital_status'])

        # Communication preferences
        if self._has_language_data(data):
            patient['communication'] = self._process_communication(data)

        # Emergency contacts
        if self._has_emergency_contact_data(data):
            patient['contact'] = self._process_emergency_contacts(data)

        # General practitioner
        if 'primary_care_provider' in data:
            patient['generalPractitioner'] = self._process_general_practitioner(data)

        # Managing organization
        if 'organization' in data:
            org_resource = {'resourceType': 'Organization', 'id': data['organization']}
            patient['managingOrganization'] = self.create_reference(org_resource)

        # Add metadata
        self._add_patient_metadata(patient, request_id)

        return patient

    def _generate_patient_id(self, data: Dict[str, Any]) -> str:
        """Generate unique patient ID with optional prefix"""
        # Use provided ID if available
        if 'id' in data:
            return str(data['id'])

        # Use MRN-based ID if available
        if 'mrn' in data:
            return f"patient-mrn-{data['mrn']}"

        # Use patient_ref if provided (legacy compatibility)
        if 'patient_ref' in data:
            return str(data['patient_ref']).replace('PT-', 'patient-')

        # Generate UUID-based ID
        return f"patient-{uuid.uuid4()}"

    def _has_name_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains name information"""
        return any(key in data for key in ['name', 'names', 'first_name', 'last_name', 'family', 'given'])

    def _has_identifier_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains identifier information"""
        return any(key in data for key in ['mrn', 'ssn', 'identifiers', 'identifier'])

    def _has_birth_date_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains birth date information"""
        return any(key in data for key in ['birth_date', 'dob', 'birthDate'])

    def _has_telecom_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains telecom information"""
        return any(key in data for key in ['phone', 'mobile_phone', 'work_phone', 'email', 'telecom'])

    def _has_address_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains address information"""
        return any(key in data for key in ['address', 'addresses'])

    def _has_language_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains language information"""
        return any(key in data for key in ['language', 'languages', 'communication'])

    def _has_emergency_contact_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains emergency contact information"""
        return any(key in data for key in ['emergency_contact', 'emergency_contacts', 'contact'])

    def _process_names(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process patient names with normalization"""
        names = []

        # Handle legacy single name field
        if 'name' in data and isinstance(data['name'], str):
            names.append(self._parse_name_string(data['name']))

        # Handle structured name fields
        if any(key in data for key in ['first_name', 'last_name', 'family', 'given']):
            name = self._build_structured_name(data)
            if name:
                names.append(name)

        # Handle multiple names
        if 'names' in data:
            for name_info in data['names']:
                if isinstance(name_info, str):
                    names.append(self._parse_name_string(name_info))
                elif isinstance(name_info, dict):
                    names.append(self._build_structured_name(name_info))

        # Default name if none provided
        if not names:
            names.append({
                'use': 'usual',
                'family': 'Unknown',
                'given': ['Unknown']
            })

        return names

    def _parse_name_string(self, name_str: str) -> Dict[str, Any]:
        """Parse name string into FHIR HumanName components"""
        name_str = name_str.strip()

        if ',' in name_str:
            # "Last, First Middle" format
            parts = name_str.split(',', 1)
            family = parts[0].strip()
            given_part = parts[1].strip()
            given = given_part.split() if given_part else ['Unknown']
        else:
            # "First [Middle] Last" format
            parts = name_str.split()
            if len(parts) == 1:
                family = parts[0]
                given = ['Unknown']
            elif len(parts) == 2:
                given = [parts[0]]
                family = parts[1]
            else:
                given = parts[:-1]
                family = parts[-1]

        return {
            'use': 'usual',
            'family': family,
            'given': given,
            'text': name_str
        }

    def _build_structured_name(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build name from structured data fields"""
        name = {
            'use': data.get('use', 'usual')
        }

        # Family name
        family = data.get('family') or data.get('last_name')
        if family:
            name['family'] = str(family)

        # Given names
        given = []
        if data.get('given'):
            if isinstance(data['given'], list):
                given.extend(data['given'])
            else:
                given.append(str(data['given']))
        elif data.get('first_name'):
            given.append(str(data['first_name']))

        if data.get('middle_name'):
            given.append(str(data['middle_name']))

        if given:
            name['given'] = given

        # Prefix and suffix
        if 'prefix' in data:
            name['prefix'] = [str(data['prefix'])] if isinstance(data['prefix'], str) else data['prefix']

        if 'suffix' in data:
            name['suffix'] = [str(data['suffix'])] if isinstance(data['suffix'], str) else data['suffix']

        # Generate text representation
        if family or given:
            text_parts = []
            if given:
                text_parts.extend(given)
            if family:
                text_parts.append(family)
            name['text'] = ' '.join(text_parts)

        return name if (family or given) else None

    def _process_identifiers(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process patient identifiers (MRN, SSN, etc.)"""
        identifiers = []

        # Medical Record Number
        if 'mrn' in data:
            identifiers.append({
                'use': 'usual',
                'type': self.create_codeable_concept(
                    system='http://terminology.hl7.org/CodeSystem/v2-0203',
                    code='MR',
                    display='Medical record number'
                ),
                'system': 'http://hospital.local/patient-id',
                'value': str(data['mrn'])
            })

        # Social Security Number
        if 'ssn' in data:
            try:
                ssn = self._format_ssn(data['ssn'])
                identifiers.append({
                    'use': 'secondary',
                    'type': self.create_codeable_concept(
                        system='http://terminology.hl7.org/CodeSystem/v2-0203',
                        code='SS',
                        display='Social Security number'
                    ),
                    'system': 'http://hl7.org/fhir/sid/us-ssn',
                    'value': ssn
                })
            except ValueError as e:
                self.logger.warning(f"Invalid SSN format: {e}")

        # Legacy identifier field (for backward compatibility)
        if 'identifier' in data and isinstance(data['identifier'], list):
            for id_info in data['identifier']:
                if isinstance(id_info, dict) and 'value' in id_info:
                    identifier = {
                        'use': id_info.get('use', 'secondary'),
                        'value': str(id_info['value'])
                    }
                    if 'system' in id_info:
                        identifier['system'] = id_info['system']
                    if 'type' in id_info:
                        identifier['type'] = id_info['type']
                    identifiers.append(identifier)

        # Additional identifiers
        if 'identifiers' in data:
            for id_info in data['identifiers']:
                if isinstance(id_info, dict) and 'value' in id_info:
                    identifier = {
                        'use': id_info.get('use', 'secondary'),
                        'value': str(id_info['value'])
                    }
                    if 'system' in id_info:
                        identifier['system'] = id_info['system']
                    if 'type' in id_info:
                        identifier['type'] = id_info['type']
                    identifiers.append(identifier)

        return identifiers

    def _format_ssn(self, ssn: str) -> str:
        """Format SSN with proper validation"""
        # Remove all non-digits
        digits = re.sub(r'\D', '', ssn)

        if len(digits) != 9:
            raise ValueError(f"Invalid SSN format: {ssn}")

        # Format as XXX-XX-XXXX
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"

    def _normalize_gender(self, gender: str) -> str:
        """Normalize gender to FHIR values"""
        gender_map = {
            'male': 'male',
            'female': 'female',
            'other': 'other',
            'unknown': 'unknown',
            'm': 'male',
            'f': 'female',
            'u': 'unknown',
            'man': 'male',
            'woman': 'female'
        }

        normalized = str(gender).lower().strip()
        return gender_map.get(normalized, 'unknown')

    def _normalize_birth_date(self, data: Dict[str, Any]) -> str:
        """Normalize birth date to FHIR date format (YYYY-MM-DD)"""
        birth_date = data.get('birth_date') or data.get('dob') or data.get('birthDate')

        if isinstance(birth_date, str):
            # Try to parse various date formats
            date_formats = [
                '%Y-%m-%d',     # 1990-01-15
                '%m/%d/%Y',     # 01/15/1990
                '%d/%m/%Y',     # 15/01/1990
                '%m-%d-%Y',     # 01-15-1990
                '%Y/%m/%d',     # 1990/01/15
                '%B %d, %Y',    # January 15, 1990
                '%b %d, %Y',    # Jan 15, 1990
            ]

            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(birth_date, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            raise ValueError(f"Unable to parse birth date: {birth_date}")

        elif isinstance(birth_date, datetime):
            return birth_date.strftime('%Y-%m-%d')

        else:
            raise ValueError(f"Invalid birth date type: {type(birth_date)}")

    def _process_telecom(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process phone numbers and email addresses"""
        telecom = []

        # Phone numbers
        if 'phone' in data:
            try:
                phone = self._format_phone_number(data['phone'])
                telecom.append({
                    'system': 'phone',
                    'value': phone,
                    'use': 'home'
                })
            except ValueError as e:
                self.logger.warning(f"Invalid phone format: {e}")

        if 'mobile_phone' in data:
            try:
                mobile = self._format_phone_number(data['mobile_phone'])
                telecom.append({
                    'system': 'phone',
                    'value': mobile,
                    'use': 'mobile'
                })
            except ValueError as e:
                self.logger.warning(f"Invalid mobile phone format: {e}")

        if 'work_phone' in data:
            try:
                work = self._format_phone_number(data['work_phone'])
                telecom.append({
                    'system': 'phone',
                    'value': work,
                    'use': 'work'
                })
            except ValueError as e:
                self.logger.warning(f"Invalid work phone format: {e}")

        # Email addresses
        if 'email' in data:
            try:
                email = self._validate_email(data['email'])
                telecom.append({
                    'system': 'email',
                    'value': email,
                    'use': 'home'
                })
            except ValueError as e:
                self.logger.warning(f"Invalid email format: {e}")

        # Structured telecom data
        if 'telecom' in data:
            for telecom_info in data['telecom']:
                if isinstance(telecom_info, dict) and 'system' in telecom_info and 'value' in telecom_info:
                    item = {
                        'system': telecom_info['system'],
                        'value': str(telecom_info['value'])
                    }
                    if 'use' in telecom_info:
                        item['use'] = telecom_info['use']
                    telecom.append(item)

        return telecom

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number to standard format"""
        if not phone:
            raise ValueError("Empty phone number")

        # Remove all non-digits
        digits = re.sub(r'\D', '', str(phone))

        if len(digits) == 10:
            # US format: (XXX) XXX-XXXX
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            # US with country code: +1 (XXX) XXX-XXXX
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        elif len(digits) >= 7:
            # International or other format - return formatted
            return f"+{digits}"
        else:
            raise ValueError(f"Invalid phone number length: {phone}")

    def _validate_email(self, email: str) -> str:
        """Validate email format"""
        if not email:
            raise ValueError("Empty email address")

        email = str(email).strip()
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

        if not email_pattern.match(email):
            raise ValueError(f"Invalid email format: {email}")

        return email.lower()

    def _process_addresses(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process patient addresses"""
        addresses = []

        if 'address' in data:
            address = self._create_address(data['address'])
            if address:
                addresses.append(address)

        if 'addresses' in data:
            for addr_data in data['addresses']:
                address = self._create_address(addr_data)
                if address:
                    addresses.append(address)

        return addresses

    def _create_address(self, addr_data: Any) -> Optional[Dict[str, Any]]:
        """Create FHIR address structure"""
        if not addr_data:
            return None

        if isinstance(addr_data, str):
            # Parse address string
            return {
                'use': 'home',
                'type': 'both',
                'text': addr_data.strip()
            }

        if not isinstance(addr_data, dict):
            return None

        address = {
            'use': addr_data.get('use', 'home'),
            'type': addr_data.get('type', 'both')
        }

        # Address lines
        lines = []
        for line_key in ['line1', 'line2', 'street', 'address_line_1', 'address_line_2']:
            if line_key in addr_data and addr_data[line_key]:
                lines.append(str(addr_data[line_key]))

        if lines:
            address['line'] = lines

        # City, state, postal code, country
        for fhir_key, data_keys in [
            ('city', ['city']),
            ('state', ['state', 'region']),
            ('postalCode', ['postal_code', 'zip', 'zipcode']),
            ('country', ['country'])
        ]:
            for key in data_keys:
                if key in addr_data and addr_data[key]:
                    address[fhir_key] = str(addr_data[key])
                    break

        # Add text representation if we have components
        if any(key in address for key in ['line', 'city', 'state', 'postalCode']):
            text_parts = []
            if 'line' in address:
                text_parts.extend(address['line'])
            if 'city' in address:
                text_parts.append(address['city'])
            if 'state' in address:
                text_parts.append(address['state'])
            if 'postalCode' in address:
                text_parts.append(address['postalCode'])
            address['text'] = ', '.join(text_parts)

        return address if len(address) > 2 else None  # More than just use and type

    def _process_marital_status(self, marital_status: str) -> Dict[str, Any]:
        """Process marital status"""
        status_map = {
            'single': {'code': 'S', 'display': 'Never Married'},
            'married': {'code': 'M', 'display': 'Married'},
            'divorced': {'code': 'D', 'display': 'Divorced'},
            'widowed': {'code': 'W', 'display': 'Widowed'},
            'separated': {'code': 'L', 'display': 'Legally Separated'},
            'unknown': {'code': 'UNK', 'display': 'Unknown'}
        }

        status_info = status_map.get(str(marital_status).lower(), status_map['unknown'])

        return self.create_codeable_concept(
            system='http://terminology.hl7.org/CodeSystem/v3-MaritalStatus',
            code=status_info['code'],
            display=status_info['display']
        )

    def _process_communication(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process communication preferences"""
        communications = []

        languages = []
        if 'language' in data:
            languages.append(data['language'])
        if 'languages' in data:
            languages.extend(data['languages'])

        for lang in languages:
            if isinstance(lang, str):
                communications.append({
                    'language': self.create_codeable_concept(
                        system='LANGUAGE',
                        code=lang.lower()[:2],  # ISO 639-1 two-letter code
                        display=lang
                    )
                })
            elif isinstance(lang, dict) and 'code' in lang:
                communications.append({
                    'language': self.create_codeable_concept(
                        system='LANGUAGE',
                        code=lang['code'],
                        display=lang.get('display', lang['code'])
                    ),
                    'preferred': lang.get('preferred', False)
                })

        return communications

    def _process_emergency_contacts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process emergency contacts"""
        contacts = []

        contact_data_list = []
        if 'emergency_contact' in data:
            contact_data_list.append(data['emergency_contact'])
        if 'emergency_contacts' in data:
            contact_data_list.extend(data['emergency_contacts'])
        if 'contact' in data:
            contact_data_list.extend(data['contact'] if isinstance(data['contact'], list) else [data['contact']])

        for contact_data in contact_data_list:
            if not isinstance(contact_data, dict):
                continue

            contact = {}

            # Relationship
            if 'relationship' in contact_data:
                contact['relationship'] = [self._create_relationship_coding(contact_data['relationship'])]

            # Name
            if 'name' in contact_data:
                contact['name'] = self._process_names({'name': contact_data['name']})[0]

            # Telecom
            if any(key in contact_data for key in ['phone', 'email', 'telecom']):
                contact['telecom'] = self._process_telecom(contact_data)

            # Address
            if 'address' in contact_data:
                address = self._create_address(contact_data['address'])
                if address:
                    contact['address'] = address

            if contact:
                contacts.append(contact)

        return contacts

    def _create_relationship_coding(self, relationship: str) -> Dict[str, Any]:
        """Create relationship coding"""
        relationship_codes = {
            'spouse': {'code': 'SPS', 'display': 'spouse'},
            'partner': {'code': 'DOMPART', 'display': 'domestic partner'},
            'child': {'code': 'CHILD', 'display': 'child'},
            'parent': {'code': 'PRN', 'display': 'parent'},
            'mother': {'code': 'MTH', 'display': 'mother'},
            'father': {'code': 'FTH', 'display': 'father'},
            'sibling': {'code': 'SIB', 'display': 'sibling'},
            'brother': {'code': 'BRO', 'display': 'brother'},
            'sister': {'code': 'SIS', 'display': 'sister'},
            'emergency': {'code': 'C', 'display': 'emergency contact'},
            'friend': {'code': 'FRND', 'display': 'unrelated friend'},
            'neighbor': {'code': 'NBOR', 'display': 'neighbor'}
        }

        code_info = relationship_codes.get(str(relationship).lower(), {
            'code': 'O', 'display': 'other'
        })

        return self.create_codeable_concept(
            system='http://terminology.hl7.org/CodeSystem/v3-RoleCode',
            code=code_info['code'],
            display=code_info['display']
        )

    def _process_general_practitioner(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process general practitioner references"""
        practitioners = []

        pcp_data = data.get('primary_care_provider')
        if isinstance(pcp_data, str):
            practitioners.append({
                'reference': f"Practitioner/{pcp_data}"
            })
        elif isinstance(pcp_data, dict):
            if 'id' in pcp_data:
                practitioners.append({
                    'reference': f"Practitioner/{pcp_data['id']}"
                })
            elif 'reference' in pcp_data:
                practitioners.append({
                    'reference': pcp_data['reference']
                })

        return practitioners

    def _add_patient_metadata(self, patient: Dict[str, Any], request_id: Optional[str]):
        """Add metadata to patient resource"""
        if not patient.get('meta'):
            patient['meta'] = {}

        patient['meta']['lastUpdated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        if request_id:
            if 'tag' not in patient['meta']:
                patient['meta']['tag'] = []
            patient['meta']['tag'].append({
                'system': 'http://hospital.local/request-id',
                'code': request_id
            })

    def _create_related_person(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create RelatedPerson resource with comprehensive FHIR R4 support"""
        # Generate ID - handle both string and structured identifier formats
        identifier_data = data.get('identifier')
        if identifier_data:
            # If identifier is a dict with 'value', extract the value for the ID
            if isinstance(identifier_data, dict):
                related_id = identifier_data.get('value', f"related-person-{uuid.uuid4().hex[:8]}")
            # If identifier is a list, use the first identifier's value
            elif isinstance(identifier_data, list) and len(identifier_data) > 0:
                first_id = identifier_data[0]
                related_id = first_id.get('value', f"related-person-{uuid.uuid4().hex[:8]}") if isinstance(first_id, dict) else str(first_id)
            # If identifier is a simple string, use it directly
            elif isinstance(identifier_data, str):
                related_id = identifier_data
            else:
                related_id = f"related-person-{uuid.uuid4().hex[:8]}"
        else:
            related_id = f"related-person-{uuid.uuid4().hex[:8]}"

        related_person = {
            'resourceType': 'RelatedPerson',
            'id': related_id,
            'active': data.get('active', True)
        }

        # Identifier (optional but useful) - preserve structured format
        if 'identifier' in data:
            identifier_input = data['identifier']
            # If it's already a list of identifier objects, use as-is
            if isinstance(identifier_input, list):
                related_person['identifier'] = identifier_input
            # If it's a single identifier object, wrap in list
            elif isinstance(identifier_input, dict):
                related_person['identifier'] = [identifier_input]
            # If it's a simple string, create a structured identifier
            elif isinstance(identifier_input, str):
                related_person['identifier'] = [{
                    'system': 'urn:ietf:rfc:3986',
                    'value': identifier_input
                }]

        # Patient reference (required)
        if 'patient_reference' in data:
            related_person['patient'] = {'reference': data['patient_reference']}
        elif 'patient' in data:
            related_person['patient'] = {'reference': f"Patient/{data['patient']}"}

        # Relationship type (can be single or multiple)
        if 'relationship' in data:
            relationships = data['relationship']
            if isinstance(relationships, list):
                related_person['relationship'] = [
                    self._create_relationship_coding(rel) for rel in relationships
                ]
            else:
                related_person['relationship'] = [self._create_relationship_coding(relationships)]

        # Name and contact info (reuse patient methods)
        if self._has_name_data(data):
            related_person['name'] = self._process_names(data)

        # Gender
        if 'gender' in data:
            related_person['gender'] = self._normalize_gender(data['gender'])

        # Birth date
        if self._has_birth_date_data(data):
            related_person['birthDate'] = self._normalize_birth_date(data)

        # Telecom (phone, email)
        if self._has_telecom_data(data):
            related_person['telecom'] = self._process_telecom(data)

        # Address
        if self._has_address_data(data):
            related_person['address'] = self._process_addresses(data)

        # Period (relationship timeframe)
        if 'period' in data:
            period_data = data['period']
            related_person['period'] = {}
            if 'start' in period_data:
                related_person['period']['start'] = period_data['start']
            if 'end' in period_data:
                related_person['period']['end'] = period_data['end']

        # Communication preferences - handle both dict and list formats
        if 'communication' in data:
            comm_input = data['communication']
            # If it's already a properly formatted list, use as-is
            if isinstance(comm_input, list):
                related_person['communication'] = comm_input
            # If it's a single dict, format it as FHIR communication element
            elif isinstance(comm_input, dict):
                related_person['communication'] = [{
                    'language': {
                        'coding': [{
                            'system': 'urn:ietf:bcp:47',
                            'code': comm_input.get('language', 'en-US'),
                            'display': comm_input.get('language', 'en-US')
                        }]
                    },
                    'preferred': comm_input.get('preferred', False)
                }]

        return related_person

    def _create_person(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create Person resource"""
        person = {
            'resourceType': 'Person',
            'id': f"person-{uuid.uuid4()}",
            'active': data.get('active', True)
        }

        # Process basic demographics
        if self._has_name_data(data):
            person['name'] = self._process_names(data)

        if 'gender' in data:
            person['gender'] = self._normalize_gender(data['gender'])

        if self._has_birth_date_data(data):
            person['birthDate'] = self._normalize_birth_date(data)

        if self._has_telecom_data(data):
            person['telecom'] = self._process_telecom(data)

        if self._has_address_data(data):
            person['address'] = self._process_addresses(data)

        # Links to other resources
        if 'links' in data:
            person['link'] = []
            for link_data in data['links']:
                if isinstance(link_data, dict) and 'target' in link_data:
                    person['link'].append({
                        'target': {'reference': link_data['target']},
                        'assurance': link_data.get('assurance', 'level2')
                    })

        return person

    def _create_practitioner_role(self, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Create PractitionerRole resource"""
        role = {
            'resourceType': 'PractitionerRole',
            'id': f"practitioner-role-{uuid.uuid4()}",
            'active': data.get('active', True)
        }

        # Practitioner reference
        if 'practitioner' in data:
            role['practitioner'] = {'reference': f"Practitioner/{data['practitioner']}"}

        # Organization reference
        if 'organization' in data:
            role['organization'] = {'reference': f"Organization/{data['organization']}"}

        # Code (role type)
        if 'code' in data:
            if isinstance(data['code'], str):
                role['code'] = [self.create_codeable_concept(
                    system='http://terminology.hl7.org/CodeSystem/practitioner-role',
                    code='doctor',
                    display=data['code']
                )]
            elif isinstance(data['code'], list):
                role['code'] = [self.create_codeable_concept(
                    system='http://terminology.hl7.org/CodeSystem/practitioner-role',
                    code=code,
                    display=code
                ) for code in data['code']]

        # Specialty
        if 'specialty' in data:
            role['specialty'] = [self.create_codeable_concept(
                system='http://snomed.info/sct',
                code='408443003',
                display=data['specialty']
            )]

        # Period
        if 'period' in data:
            role['period'] = data['period']

        # Telecom and location
        if self._has_telecom_data(data):
            role['telecom'] = self._process_telecom(data)

        if 'location' in data:
            role['location'] = [{'reference': f"Location/{data['location']}"}]

        return role

    def _record_patient_metrics(self, resource_type: str, duration_ms: float, success: bool = True):
        """Record patient factory specific metrics"""
        if resource_type not in self._patient_metrics:
            self._patient_metrics[resource_type] = {
                'count': 0,
                'success_count': 0,
                'error_count': 0,
                'total_duration_ms': 0,
                'max_duration_ms': 0,
                'min_duration_ms': float('inf')
            }

        metrics = self._patient_metrics[resource_type]
        metrics['count'] += 1
        metrics['total_duration_ms'] += duration_ms
        metrics['max_duration_ms'] = max(metrics['max_duration_ms'], duration_ms)
        metrics['min_duration_ms'] = min(metrics['min_duration_ms'], duration_ms)

        if success:
            metrics['success_count'] += 1
        else:
            metrics['error_count'] += 1

        # Log performance warning if slow
        if duration_ms > 50:  # >50ms warning threshold (per requirements)
            self.logger.warning(f"Slow {resource_type} creation: {duration_ms:.2f}ms")

    def get_patient_metrics(self) -> Dict[str, Any]:
        """Get patient factory performance metrics"""
        metrics = {}
        for resource_type, data in self._patient_metrics.items():
            if data['count'] > 0:
                metrics[resource_type] = {
                    'count': data['count'],
                    'success_rate': data['success_count'] / data['count'],
                    'error_rate': data['error_count'] / data['count'],
                    'avg_duration_ms': data['total_duration_ms'] / data['count'],
                    'max_duration_ms': data['max_duration_ms'],
                    'min_duration_ms': data['min_duration_ms'] if data['min_duration_ms'] != float('inf') else 0
                }
        return metrics

    def get_health_status(self) -> Dict[str, Any]:
        """Get patient factory health status"""
        total_requests = sum(m['count'] for m in self._patient_metrics.values())
        total_errors = sum(m['error_count'] for m in self._patient_metrics.values())

        if total_requests > 0:
            error_rate = total_errors / total_requests
            avg_duration = sum(m['total_duration_ms'] for m in self._patient_metrics.values()) / total_requests
        else:
            error_rate = 0
            avg_duration = 0

        return {
            'status': 'healthy' if error_rate < 0.05 and avg_duration < 50 else 'degraded',
            'total_requests': total_requests,
            'error_rate': error_rate,
            'avg_duration_ms': avg_duration,
            'supported_resources': list(self.SUPPORTED_RESOURCES),
            'performance_target_met': avg_duration < 50  # <50ms requirement
        }