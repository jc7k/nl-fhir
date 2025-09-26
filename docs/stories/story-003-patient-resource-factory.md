# Story: Extract Patient Resource Factory from Monolithic Class

**Story ID:** REFACTOR-003
**Epic:** FHIRResourceFactory Decomposition (Phase 2: Core Refactoring)
**Status:** READY FOR DEVELOPMENT
**Estimated Effort:** 12 hours
**Priority:** P0 - Critical
**Depends On:** REFACTOR-001, REFACTOR-002

## User Story

**As a** developer working with patient-related FHIR resources
**I want** a dedicated PatientResourceFactory that handles all patient resource types
**So that** patient logic is isolated, maintainable, and can be modified without affecting other resources

## Background & Context

Patient resources are the most frequently created in NL-FHIR (40% of all requests). Extracting patient logic from the 10,600-line God class reduces risk and improves maintainability. This is the first specialized factory implementation.

**Current State:**
- Patient creation logic scattered across 45+ methods in monolithic class
- Handles Patient, RelatedPerson, Person, and Practitioner resources
- No isolation - changes affect entire FHIR pipeline
- Impossible to unit test patient-specific logic

**Target State:**
- Dedicated PatientResourceFactory with focused responsibility
- Handles Patient, RelatedPerson, Person, PractitionerRole resources
- Feature flag controlled gradual rollout
- 100% backward compatibility maintained

## Acceptance Criteria

### Must Have
- [ ] PatientResourceFactory class extending BaseResourceFactory
- [ ] Support for Patient, RelatedPerson, Person, PractitionerRole resources
- [ ] Identifier generation with MRN support
- [ ] Name parsing and normalization
- [ ] Address standardization
- [ ] Telecom (phone/email) validation and formatting
- [ ] Feature flag integration (`use_new_patient_factory`)
- [ ] 100% functional parity with legacy implementation
- [ ] Performance requirement: <50ms p95 for patient creation
- [ ] Zero production incidents during gradual rollout

### Should Have
- [ ] Patient matching/deduplication logic
- [ ] Demographics validation (DOB, gender, etc.)
- [ ] Insurance information handling
- [ ] Emergency contact processing
- [ ] Audit trail for patient creation

### Could Have
- [ ] Patient photo/attachment support
- [ ] Advanced name matching algorithms
- [ ] Integration with external patient registries

## Technical Specifications

### 1. Patient Resource Factory Implementation

```python
# src/nl_fhir/services/fhir/factories/patient_factory.py

from typing import Dict, Any, List, Optional
from fhir.resources.patient import Patient
from fhir.resources.relatedperson import RelatedPerson
from fhir.resources.person import Person
from fhir.resources.practitionerrole import PractitionerRole
from .base import BaseResourceFactory
import re
from datetime import datetime
import uuid

class PatientResourceFactory(BaseResourceFactory):
    """
    Factory for patient-related FHIR resources.
    Handles Patient, RelatedPerson, Person, PractitionerRole.
    """

    SUPPORTED_RESOURCES = {
        'Patient', 'RelatedPerson', 'Person', 'PractitionerRole'
    }

    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the resource type"""
        return resource_type in self.SUPPORTED_RESOURCES

    def _create_resource(self, data: Dict[str, Any]) -> Any:
        """Create patient-related resource based on type"""
        resource_type = data['resource_type']

        if resource_type == 'Patient':
            return self._create_patient(data)
        elif resource_type == 'RelatedPerson':
            return self._create_related_person(data)
        elif resource_type == 'Person':
            return self._create_person(data)
        elif resource_type == 'PractitionerRole':
            return self._create_practitioner_role(data)
        else:
            raise ValueError(f"Unsupported resource type: {resource_type}")

    def _create_patient(self, data: Dict[str, Any]) -> Patient:
        """Create Patient resource with full demographics"""
        patient = Patient()
        patient.resourceType = "Patient"
        patient.id = self._generate_patient_id()

        # Required fields
        patient.active = data.get('active', True)

        # Names - support multiple names
        if 'name' in data or 'names' in data:
            patient.name = self._process_names(data)

        # Identifiers (MRN, SSN, etc.)
        if 'mrn' in data or 'identifiers' in data:
            patient.identifier = self._process_identifiers(data)

        # Demographics
        if 'gender' in data:
            patient.gender = self._normalize_gender(data['gender'])

        if 'birth_date' in data or 'dob' in data:
            patient.birthDate = self._normalize_birth_date(data)

        # Contact information
        if 'phone' in data or 'email' in data or 'telecom' in data:
            patient.telecom = self._process_telecom(data)

        # Addresses
        if 'address' in data or 'addresses' in data:
            patient.address = self._process_addresses(data)

        # Marital status
        if 'marital_status' in data:
            patient.maritalStatus = self._process_marital_status(data['marital_status'])

        # Communication preferences
        if 'language' in data or 'languages' in data:
            patient.communication = self._process_communication(data)

        # Emergency contacts
        if 'emergency_contact' in data or 'emergency_contacts' in data:
            patient.contact = self._process_emergency_contacts(data)

        # General practitioner
        if 'primary_care_provider' in data:
            patient.generalPractitioner = self._process_general_practitioner(data)

        # Managing organization
        if 'organization' in data:
            patient.managingOrganization = self._create_organization_reference(data['organization'])

        return patient

    def _generate_patient_id(self) -> str:
        """Generate unique patient ID"""
        return f"patient-{uuid.uuid4()}"

    def _process_names(self, data: Dict[str, Any]) -> List[Dict]:
        """Process patient names with normalization"""
        names = []

        # Handle single name or multiple names
        name_data = data.get('names', [data.get('name')] if 'name' in data else [])

        for name_info in name_data:
            if isinstance(name_info, str):
                # Parse string name
                parsed_name = self._parse_name_string(name_info)
                names.append(parsed_name)
            elif isinstance(name_info, dict):
                # Structured name data
                name = {
                    'use': name_info.get('use', 'official'),
                    'family': name_info.get('family', name_info.get('last_name')),
                    'given': name_info.get('given', [name_info.get('first_name')])
                }

                if 'middle_name' in name_info:
                    if isinstance(name['given'], str):
                        name['given'] = [name['given']]
                    name['given'].append(name_info['middle_name'])

                if 'prefix' in name_info:
                    name['prefix'] = [name_info['prefix']]

                if 'suffix' in name_info:
                    name['suffix'] = [name_info['suffix']]

                names.append(name)

        return names if names else [{'family': 'Unknown', 'given': ['Unknown']}]

    def _parse_name_string(self, name_str: str) -> Dict:
        """Parse name string into components"""
        # Handle common patterns: "Last, First Middle", "First Last", "First Middle Last"
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
            'use': 'official',
            'family': family,
            'given': given
        }

    def _process_identifiers(self, data: Dict[str, Any]) -> List[Dict]:
        """Process patient identifiers (MRN, SSN, etc.)"""
        identifiers = []

        # Medical Record Number
        if 'mrn' in data:
            identifiers.append({
                'use': 'usual',
                'type': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                        'code': 'MR',
                        'display': 'Medical record number'
                    }]
                },
                'system': 'http://hospital.example.org/patients',
                'value': str(data['mrn'])
            })

        # Social Security Number
        if 'ssn' in data:
            ssn = self._format_ssn(data['ssn'])
            identifiers.append({
                'use': 'secondary',
                'type': {
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                        'code': 'SS',
                        'display': 'Social Security number'
                    }]
                },
                'system': 'http://hl7.org/fhir/sid/us-ssn',
                'value': ssn
            })

        # Additional identifiers
        if 'identifiers' in data:
            for id_info in data['identifiers']:
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
            'u': 'unknown'
        }

        normalized = gender.lower().strip()
        return gender_map.get(normalized, 'unknown')

    def _normalize_birth_date(self, data: Dict[str, Any]) -> str:
        """Normalize birth date to FHIR date format (YYYY-MM-DD)"""
        birth_date = data.get('birth_date') or data.get('dob')

        if isinstance(birth_date, str):
            # Try to parse various date formats
            date_formats = [
                '%Y-%m-%d',     # 1990-01-15
                '%m/%d/%Y',     # 01/15/1990
                '%d/%m/%Y',     # 15/01/1990
                '%m-%d-%Y',     # 01-15-1990
                '%Y/%m/%d',     # 1990/01/15
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

    def _process_telecom(self, data: Dict[str, Any]) -> List[Dict]:
        """Process phone numbers and email addresses"""
        telecom = []

        # Phone numbers
        if 'phone' in data:
            phone = self._format_phone_number(data['phone'])
            telecom.append({
                'system': 'phone',
                'value': phone,
                'use': 'home'
            })

        if 'mobile_phone' in data:
            mobile = self._format_phone_number(data['mobile_phone'])
            telecom.append({
                'system': 'phone',
                'value': mobile,
                'use': 'mobile'
            })

        if 'work_phone' in data:
            work = self._format_phone_number(data['work_phone'])
            telecom.append({
                'system': 'phone',
                'value': work,
                'use': 'work'
            })

        # Email addresses
        if 'email' in data:
            email = self._validate_email(data['email'])
            telecom.append({
                'system': 'email',
                'value': email,
                'use': 'home'
            })

        # Structured telecom data
        if 'telecom' in data:
            for telecom_info in data['telecom']:
                item = {
                    'system': telecom_info['system'],
                    'value': telecom_info['value']
                }

                if 'use' in telecom_info:
                    item['use'] = telecom_info['use']

                telecom.append(item)

        return telecom

    def _format_phone_number(self, phone: str) -> str:
        """Format phone number to standard format"""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)

        if len(digits) == 10:
            # US format: (XXX) XXX-XXXX
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            # US with country code: +1 (XXX) XXX-XXXX
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            # International or unknown format - return as is
            return phone

    def _validate_email(self, email: str) -> str:
        """Validate email format"""
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

        if not email_pattern.match(email):
            raise ValueError(f"Invalid email format: {email}")

        return email.lower()

    def _process_addresses(self, data: Dict[str, Any]) -> List[Dict]:
        """Process patient addresses"""
        addresses = []

        if 'address' in data:
            address = self._create_address(data['address'])
            addresses.append(address)

        if 'addresses' in data:
            for addr_data in data['addresses']:
                address = self._create_address(addr_data)
                addresses.append(address)

        return addresses

    def _create_address(self, addr_data: Any) -> Dict:
        """Create FHIR address structure"""
        if isinstance(addr_data, str):
            # Parse address string
            return {
                'use': 'home',
                'type': 'both',
                'text': addr_data
            }

        address = {
            'use': addr_data.get('use', 'home'),
            'type': addr_data.get('type', 'both')
        }

        # Address lines
        lines = []
        if 'line1' in addr_data:
            lines.append(addr_data['line1'])
        if 'line2' in addr_data:
            lines.append(addr_data['line2'])
        if 'street' in addr_data:
            lines.append(addr_data['street'])

        if lines:
            address['line'] = lines

        # City, state, postal code
        if 'city' in addr_data:
            address['city'] = addr_data['city']
        if 'state' in addr_data:
            address['state'] = addr_data['state']
        if 'postal_code' in addr_data or 'zip' in addr_data:
            address['postalCode'] = addr_data.get('postal_code') or addr_data.get('zip')
        if 'country' in addr_data:
            address['country'] = addr_data['country']

        return address

    def _create_related_person(self, data: Dict[str, Any]) -> RelatedPerson:
        """Create RelatedPerson resource"""
        related_person = RelatedPerson()
        related_person.resourceType = "RelatedPerson"
        related_person.id = f"related-person-{uuid.uuid4()}"

        # Patient reference (required)
        if 'patient_reference' in data:
            related_person.patient = {'reference': data['patient_reference']}

        # Relationship type
        if 'relationship' in data:
            related_person.relationship = [self._create_relationship_coding(data['relationship'])]

        # Name and contact info (reuse patient methods)
        if 'name' in data:
            related_person.name = self._process_names(data)

        if 'phone' in data or 'email' in data:
            related_person.telecom = self._process_telecom(data)

        return related_person

    def _create_relationship_coding(self, relationship: str) -> Dict:
        """Create relationship coding"""
        relationship_codes = {
            'spouse': {'code': 'SPS', 'display': 'spouse'},
            'child': {'code': 'CHILD', 'display': 'child'},
            'parent': {'code': 'PRN', 'display': 'parent'},
            'sibling': {'code': 'SIB', 'display': 'sibling'},
            'emergency': {'code': 'C', 'display': 'emergency contact'}
        }

        code_info = relationship_codes.get(relationship.lower(), {
            'code': 'O', 'display': 'other'
        })

        return {
            'coding': [{
                'system': 'http://terminology.hl7.org/CodeSystem/v3-RoleCode',
                'code': code_info['code'],
                'display': code_info['display']
            }]
        }
```

### 2. Feature Flag Integration

```python
# Update to FactoryRegistry in __init__.py

def _load_factory(self, resource_type: str):
    """Load factory with patient factory support"""

    # Check for patient-specific feature flag
    if (resource_type in PatientResourceFactory.SUPPORTED_RESOURCES and
        feature_flags.is_enabled('use_new_patient_factory')):

        from .patient_factory import PatientResourceFactory
        factory = PatientResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )
        self._factories[resource_type] = factory
        self.logger.info(f"Loaded PatientResourceFactory for {resource_type}")
        return

    # Fall back to legacy factory
    self._factories[resource_type] = self._get_legacy_factory()
```

### 3. Performance Monitoring

```python
# src/nl_fhir/services/fhir/factories/patient_factory.py (addition)

class PatientResourceFactory(BaseResourceFactory):

    def create(self, data: Dict[str, Any]) -> Any:
        """Override to add patient-specific metrics"""
        start_time = time.time()

        try:
            resource = super().create(data)

            # Patient-specific metrics
            duration_ms = (time.time() - start_time) * 1000
            self._record_patient_metrics(resource.resource_type, duration_ms)

            return resource

        except Exception as e:
            self._record_patient_error(data.get('resource_type'), str(e))
            raise

    def _record_patient_metrics(self, resource_type: str, duration_ms: float):
        """Record patient factory specific metrics"""
        if not hasattr(self, '_patient_metrics'):
            self._patient_metrics = {}

        if resource_type not in self._patient_metrics:
            self._patient_metrics[resource_type] = {
                'count': 0,
                'total_duration_ms': 0,
                'errors': 0
            }

        metrics = self._patient_metrics[resource_type]
        metrics['count'] += 1
        metrics['total_duration_ms'] += duration_ms

        # Log performance warning if slow
        if duration_ms > 100:  # >100ms warning threshold
            self.logger.warning(f"Slow {resource_type} creation: {duration_ms:.2f}ms")

    def get_patient_metrics(self) -> Dict:
        """Get patient factory performance metrics"""
        return getattr(self, '_patient_metrics', {})
```

## Test Requirements

### Unit Tests

```python
# tests/services/fhir/factories/test_patient_factory.py

def test_patient_creation_basic():
    """Test basic patient creation"""
    factory = PatientResourceFactory(validators, coders, ref_manager)

    data = {
        'resource_type': 'Patient',
        'name': 'John Doe',
        'mrn': '12345678',
        'gender': 'male',
        'birth_date': '1980-01-15'
    }

    patient = factory.create(data)

    assert patient.resourceType == 'Patient'
    assert patient.name[0]['family'] == 'Doe'
    assert patient.name[0]['given'] == ['John']
    assert patient.gender == 'male'
    assert patient.birthDate == '1980-01-15'

def test_patient_identifiers():
    """Test patient identifier processing"""
    factory = PatientResourceFactory(validators, coders, ref_manager)

    data = {
        'resource_type': 'Patient',
        'name': 'Jane Smith',
        'mrn': 'MRN123456',
        'ssn': '123-45-6789'
    }

    patient = factory.create(data)

    # Check MRN identifier
    mrn_id = next(id for id in patient.identifier if id['type']['coding'][0]['code'] == 'MR')
    assert mrn_id['value'] == 'MRN123456'

    # Check SSN identifier
    ssn_id = next(id for id in patient.identifier if id['type']['coding'][0]['code'] == 'SS')
    assert ssn_id['value'] == '123-45-6789'

def test_name_parsing():
    """Test various name format parsing"""
    factory = PatientResourceFactory(validators, coders, ref_manager)

    test_cases = [
        ('John Doe', 'Doe', ['John']),
        ('Smith, Jane', 'Smith', ['Jane']),
        ('Brown, Mary Jane', 'Brown', ['Mary', 'Jane']),
        ('Dr. John Michael Smith Jr.', 'Smith', ['John', 'Michael'])
    ]

    for name_str, expected_family, expected_given in test_cases:
        data = {'resource_type': 'Patient', 'name': name_str}
        patient = factory.create(data)

        assert patient.name[0]['family'] == expected_family
        assert patient.name[0]['given'] == expected_given

def test_phone_formatting():
    """Test phone number formatting"""
    factory = PatientResourceFactory(validators, coders, ref_manager)

    data = {
        'resource_type': 'Patient',
        'name': 'Test Patient',
        'phone': '1234567890'
    }

    patient = factory.create(data)
    phone = next(t for t in patient.telecom if t['system'] == 'phone')

    assert phone['value'] == '(123) 456-7890'

def test_feature_flag_integration():
    """Test feature flag switching"""
    # Test with flag disabled (should use legacy)
    feature_flags.set('use_new_patient_factory', False)
    registry = FactoryRegistry()
    factory = registry.get_factory('Patient')
    assert not isinstance(factory, PatientResourceFactory)

    # Test with flag enabled (should use new factory)
    feature_flags.set('use_new_patient_factory', True)
    registry = FactoryRegistry()
    registry._factories.clear()  # Clear cache
    factory = registry.get_factory('Patient')
    assert isinstance(factory, PatientResourceFactory)
```

### Performance Tests

```python
# tests/performance/test_patient_factory_performance.py

def test_patient_creation_performance():
    """Patient creation should be <50ms p95"""
    factory = PatientResourceFactory(validators, coders, ref_manager)

    data = create_complex_patient_data()
    latencies = []

    for _ in range(100):
        start = time.time()
        patient = factory.create(data)
        latency = (time.time() - start) * 1000
        latencies.append(latency)

    p95_latency = np.percentile(latencies, 95)
    assert p95_latency < 50, f"P95 latency {p95_latency:.2f}ms exceeds 50ms target"

def test_patient_factory_memory_usage():
    """Patient factory should not leak memory"""
    factory = PatientResourceFactory(validators, coders, ref_manager)
    initial_memory = psutil.Process().memory_info().rss

    for _ in range(1000):
        data = create_patient_data()
        patient = factory.create(data)
        del patient

    final_memory = psutil.Process().memory_info().rss
    memory_growth = (final_memory - initial_memory) / 1024 / 1024  # MB

    assert memory_growth < 10, f"Memory growth {memory_growth:.2f}MB too high"
```

## Rollback Plan

1. **Immediate Rollback**: Set `use_new_patient_factory` to `false`
2. **Validation**: Run patient creation tests against legacy
3. **Monitoring**: Check error rates return to baseline
4. **Performance**: Verify latency returns to expected levels

## Performance Requirements

- Patient creation: <50ms p95 latency
- Name parsing: <5ms for complex names
- Identifier processing: <2ms per identifier
- Memory usage: <1MB per patient resource
- No performance degradation vs baseline

## File List

**Files to Create:**
- `src/nl_fhir/services/fhir/factories/patient_factory.py` - Main factory
- `tests/services/fhir/factories/test_patient_factory.py` - Unit tests
- `tests/performance/test_patient_factory_performance.py` - Performance tests

**Files to Update:**
- `src/nl_fhir/services/fhir/factories/__init__.py` - Registry integration
- `src/nl_fhir/services/config.py` - Add patient factory feature flag

## Definition of Done

- [ ] PatientResourceFactory fully implemented
- [ ] All patient resource types supported
- [ ] Feature flag integration working
- [ ] 100% unit test coverage
- [ ] Performance requirements met
- [ ] Gradual rollout plan tested
- [ ] Legacy fallback validated
- [ ] Production monitoring added
- [ ] Code reviewed and approved

---
**Story Status:** READY FOR DEVELOPMENT
**Next Story:** REFACTOR-004 - Extract Medication Resource Factory