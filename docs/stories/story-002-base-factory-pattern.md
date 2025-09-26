# Story: Implement Base Factory Pattern for FHIR Resource Factories

**Story ID:** REFACTOR-002
**Epic:** FHIRResourceFactory Decomposition (Phase 1: Foundation)
**Status:** READY FOR DEVELOPMENT
**Estimated Effort:** 6 hours
**Priority:** P0 - Critical
**Depends On:** REFACTOR-001 (Factory Registry)

## User Story

**As a** developer implementing specialized FHIR resource factories
**I want** a robust base factory class with shared functionality
**So that** all factories have consistent validation, coding, and reference management

## Background & Context

With the Factory Registry in place, we need a solid foundation for all specialized factories. The base factory provides common FHIR functionality like validation, coding systems (LOINC, SNOMED, RxNorm), and reference management that all resource factories need.

**Current State:**
- Factory Registry exists but returns legacy factory as placeholder
- No standardized factory interface
- Validation, coding, and references scattered across monolithic class

**Target State:**
- Abstract BaseResourceFactory with core FHIR functionality
- Shared components (validators, coders, reference manager)
- Template method pattern for consistent resource creation
- Dependency injection for testability

## Acceptance Criteria

### Must Have
- [ ] Abstract BaseResourceFactory class with template methods
- [ ] ValidatorRegistry for FHIR R4 validation rules
- [ ] CoderRegistry for medical coding systems (LOINC, SNOMED, RxNorm)
- [ ] ReferenceManager for FHIR reference creation and resolution
- [ ] Factory initialization with shared components
- [ ] Template method pattern for create() workflow
- [ ] 100% unit test coverage
- [ ] Performance requirement: <1ms for validation checks

### Should Have
- [ ] Caching for frequently used codes and validators
- [ ] Audit logging for resource creation events
- [ ] Metrics collection for factory performance
- [ ] Debug mode with detailed logging

### Could Have
- [ ] Async validation for complex resources
- [ ] Custom validation rule registration
- [ ] Pluggable coding system providers

## Technical Specifications

### 1. Abstract Base Factory

```python
# src/nl_fhir/services/fhir/factories/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from fhir.resources.resource import Resource
from datetime import datetime
import logging
import time

class BaseResourceFactory(ABC):
    """
    Abstract base class for all FHIR resource factories.
    Provides common functionality for validation, coding, and references.
    """

    def __init__(self,
                 validators: 'ValidatorRegistry',
                 coders: 'CoderRegistry',
                 reference_manager: 'ReferenceManager'):
        self.validators = validators
        self.coders = coders
        self.reference_manager = reference_manager
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._metrics = {'created': 0, 'validated': 0, 'failed': 0}

    def create(self, data: Dict[str, Any]) -> Resource:
        """Template method for resource creation workflow"""
        start_time = time.time()

        try:
            # 1. Pre-creation validation
            self._validate_input_data(data)

            # 2. Create resource (implemented by subclasses)
            resource = self._create_resource(data)

            # 3. Post-creation validation
            self._validate_fhir_resource(resource)

            # 4. Add metadata
            self._add_metadata(resource)

            # 5. Log and metrics
            duration_ms = (time.time() - start_time) * 1000
            self.logger.debug(f"Created {resource.resource_type} in {duration_ms:.2f}ms")
            self._metrics['created'] += 1

            return resource

        except Exception as e:
            self._metrics['failed'] += 1
            self.logger.error(f"Failed to create resource: {str(e)}")
            raise

    @abstractmethod
    def _create_resource(self, data: Dict[str, Any]) -> Resource:
        """Create the specific FHIR resource - implemented by subclasses"""
        pass

    @abstractmethod
    def supports(self, resource_type: str) -> bool:
        """Check if factory supports the resource type"""
        pass

    def _validate_input_data(self, data: Dict[str, Any]):
        """Validate input data before resource creation"""
        if not data:
            raise ValueError("Input data cannot be empty")

        resource_type = data.get('resource_type')
        if not resource_type:
            raise ValueError("resource_type is required in input data")

        if not self.supports(resource_type):
            raise ValueError(f"Factory does not support resource type: {resource_type}")

    def _validate_fhir_resource(self, resource: Resource):
        """Validate created resource against FHIR R4 specification"""
        is_valid = self.validators.validate_fhir_r4(resource)

        if not is_valid:
            validation_errors = self.validators.get_validation_errors(resource)
            raise ValueError(f"FHIR validation failed: {validation_errors}")

        self._metrics['validated'] += 1

    def _add_metadata(self, resource: Resource):
        """Add metadata to track factory usage"""
        if not hasattr(resource, 'meta'):
            resource.meta = {}

        resource.meta.update({
            'factory': self.__class__.__name__,
            'created_at': datetime.now().isoformat(),
            'version': '1.0.0'
        })

    def add_coding(self, resource: Resource, system: str, code: str, display: str = None):
        """Add standardized coding to resource"""
        return self.coders.add_coding(resource, system, code, display)

    def create_reference(self, resource: Resource) -> str:
        """Create FHIR reference for resource"""
        return self.reference_manager.create_reference(resource)

    def resolve_reference(self, reference: str) -> Optional[Resource]:
        """Resolve FHIR reference to actual resource"""
        return self.reference_manager.resolve_reference(reference)

    def get_metrics(self) -> Dict[str, Any]:
        """Get factory performance metrics"""
        return self._metrics.copy()
```

### 2. Validator Registry

```python
# src/nl_fhir/services/fhir/factories/validators.py

from typing import Dict, List, Any
from fhir.resources.resource import Resource
from functools import lru_cache
import re

class ValidatorRegistry:
    """Registry for FHIR validation rules and checks"""

    def __init__(self):
        self._validators = {}
        self._register_standard_validators()

    def _register_standard_validators(self):
        """Register standard FHIR R4 validators"""
        self._validators.update({
            'required_fields': self._validate_required_fields,
            'identifier_format': self._validate_identifiers,
            'reference_format': self._validate_references,
            'coding_format': self._validate_codings,
            'date_format': self._validate_dates,
        })

    @lru_cache(maxsize=128)
    def validate_fhir_r4(self, resource: Resource) -> bool:
        """Validate resource against FHIR R4 specification"""
        try:
            # Use fhir.resources library validation
            resource.dict()  # This triggers validation

            # Additional custom validations
            for validator_name, validator_func in self._validators.items():
                if not validator_func(resource):
                    return False

            return True
        except Exception:
            return False

    def get_validation_errors(self, resource: Resource) -> List[str]:
        """Get detailed validation error messages"""
        errors = []

        for validator_name, validator_func in self._validators.items():
            try:
                if not validator_func(resource):
                    errors.append(f"Failed {validator_name} validation")
            except Exception as e:
                errors.append(f"{validator_name}: {str(e)}")

        return errors

    def _validate_required_fields(self, resource: Resource) -> bool:
        """Validate required fields are present"""
        required_fields = {
            'Patient': ['resourceType'],
            'MedicationRequest': ['resourceType', 'subject'],
            'Observation': ['resourceType', 'subject', 'code'],
        }

        resource_type = resource.resource_type
        if resource_type not in required_fields:
            return True  # No specific requirements

        resource_dict = resource.dict()
        for field in required_fields[resource_type]:
            if field not in resource_dict or resource_dict[field] is None:
                return False

        return True

    def _validate_identifiers(self, resource: Resource) -> bool:
        """Validate identifier format"""
        if hasattr(resource, 'identifier') and resource.identifier:
            for identifier in resource.identifier:
                if not identifier.value or len(identifier.value.strip()) == 0:
                    return False
        return True

    def _validate_references(self, resource: Resource) -> bool:
        """Validate FHIR reference format"""
        reference_pattern = re.compile(r'^[A-Za-z][A-Za-z0-9]*\/[A-Za-z0-9\-\.]{1,64}$')

        resource_dict = resource.dict()
        for key, value in resource_dict.items():
            if key.endswith('Reference') and value:
                if isinstance(value, dict) and 'reference' in value:
                    if not reference_pattern.match(value['reference']):
                        return False

        return True

    def _validate_codings(self, resource: Resource) -> bool:
        """Validate coding system format"""
        # Implementation for coding validation
        return True

    def _validate_dates(self, resource: Resource) -> bool:
        """Validate date format (FHIR date/dateTime)"""
        # Implementation for date validation
        return True
```

### 3. Coder Registry

```python
# src/nl_fhir/services/fhir/factories/coders.py

from typing import Dict, Optional, List
from functools import lru_cache
import logging

class CoderRegistry:
    """Registry for medical coding systems"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._coding_systems = {
            'LOINC': 'http://loinc.org',
            'SNOMED': 'http://snomed.info/sct',
            'RXNORM': 'http://www.nlm.nih.gov/research/umls/rxnorm',
            'ICD10': 'http://hl7.org/fhir/sid/icd-10',
            'CPT': 'http://www.ama-assn.org/go/cpt'
        }

    @lru_cache(maxsize=256)
    def get_system_uri(self, system_name: str) -> Optional[str]:
        """Get URI for coding system"""
        return self._coding_systems.get(system_name.upper())

    def add_coding(self, resource, system: str, code: str, display: str = None) -> Dict:
        """Add coding to resource"""
        system_uri = self.get_system_uri(system)
        if not system_uri:
            raise ValueError(f"Unknown coding system: {system}")

        coding = {
            'system': system_uri,
            'code': code
        }

        if display:
            coding['display'] = display

        self.logger.debug(f"Added {system} coding {code} to {resource.resource_type}")
        return coding

    def create_codeable_concept(self, system: str, code: str, display: str = None) -> Dict:
        """Create CodeableConcept structure"""
        coding = self.add_coding(None, system, code, display)

        return {
            'coding': [coding],
            'text': display or code
        }

    @lru_cache(maxsize=128)
    def validate_code(self, system: str, code: str) -> bool:
        """Validate code format for system"""
        # Basic format validation - can be enhanced with actual code lookups
        if not code or len(code.strip()) == 0:
            return False

        # System-specific validation rules
        if system.upper() == 'LOINC':
            return self._validate_loinc_code(code)
        elif system.upper() == 'SNOMED':
            return self._validate_snomed_code(code)
        elif system.upper() == 'RXNORM':
            return self._validate_rxnorm_code(code)

        return True  # Default to valid for unknown systems

    def _validate_loinc_code(self, code: str) -> bool:
        """Validate LOINC code format (NNNNN-N)"""
        import re
        return bool(re.match(r'^\d{5}-\d$', code))

    def _validate_snomed_code(self, code: str) -> bool:
        """Validate SNOMED CT code format (numeric)"""
        return code.isdigit() and len(code) >= 6

    def _validate_rxnorm_code(self, code: str) -> bool:
        """Validate RxNorm code format (numeric)"""
        return code.isdigit()
```

### 4. Reference Manager

```python
# src/nl_fhir/services/fhir/factories/references.py

from typing import Dict, Optional
from fhir.resources.resource import Resource
import uuid

class ReferenceManager:
    """Manages FHIR resource references and relationships"""

    def __init__(self):
        self._resource_cache = {}

    def create_reference(self, resource: Resource) -> str:
        """Create FHIR reference string for resource"""
        resource_type = resource.resource_type
        resource_id = getattr(resource, 'id', None)

        if not resource_id:
            # Generate ID if not present
            resource_id = str(uuid.uuid4())
            resource.id = resource_id

        reference = f"{resource_type}/{resource_id}"

        # Cache for resolution
        self._resource_cache[reference] = resource

        return reference

    def resolve_reference(self, reference: str) -> Optional[Resource]:
        """Resolve reference to actual resource"""
        return self._resource_cache.get(reference)

    def create_reference_dict(self, resource: Resource, display: str = None) -> Dict:
        """Create FHIR Reference structure"""
        reference = self.create_reference(resource)

        ref_dict = {'reference': reference}
        if display:
            ref_dict['display'] = display

        return ref_dict

    def validate_reference_format(self, reference: str) -> bool:
        """Validate FHIR reference format"""
        import re
        pattern = r'^[A-Za-z][A-Za-z0-9]*\/[A-Za-z0-9\-\.]{1,64}$'
        return bool(re.match(pattern, reference))

    def clear_cache(self):
        """Clear reference cache"""
        self._resource_cache.clear()
```

### 5. Factory Component Integration

```python
# src/nl_fhir/services/fhir/factories/__init__.py (update)

from .base import BaseResourceFactory
from .validators import ValidatorRegistry
from .coders import CoderRegistry
from .references import ReferenceManager
from typing import Dict, Type
import logging

class FactoryRegistry:
    """Updated registry with component initialization"""

    def __init__(self):
        # Initialize shared components
        self.validators = ValidatorRegistry()
        self.coders = CoderRegistry()
        self.reference_manager = ReferenceManager()

        self._factories = {}
        self._factory_classes = {}
        self._register_factory_mappings()

        logger.info("FactoryRegistry initialized with shared components")

    def get_factory(self, resource_type: str) -> BaseResourceFactory:
        """Get factory with shared components injected"""
        if resource_type not in self._factories:
            self._load_factory(resource_type)
        return self._factories[resource_type]

    def _load_factory(self, resource_type: str):
        """Load factory with dependency injection"""
        # For now, create mock factory that extends BaseResourceFactory
        factory = MockResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )
        self._factories[resource_type] = factory

class MockResourceFactory(BaseResourceFactory):
    """Temporary mock factory for testing base functionality"""

    def _create_resource(self, data: Dict) -> Resource:
        """Create mock resource for testing"""
        from fhir.resources.patient import Patient

        # Create basic patient for testing
        patient = Patient()
        patient.resourceType = "Patient"
        patient.id = str(uuid.uuid4())

        return patient

    def supports(self, resource_type: str) -> bool:
        """Support all types for testing"""
        return True
```

## Test Requirements

### Unit Tests

```python
# tests/services/fhir/factories/test_base_factory.py

def test_template_method_workflow():
    """Base factory should follow template method pattern"""
    registry = FactoryRegistry()
    factory = registry.get_factory('Patient')

    data = {'resource_type': 'Patient', 'name': 'Test'}
    resource = factory.create(data)

    assert resource.resourceType == 'Patient'
    assert hasattr(resource, 'meta')
    assert resource.meta['factory'] == 'MockResourceFactory'

def test_validation_integration():
    """Should validate input and output"""
    factory = MockResourceFactory(
        ValidatorRegistry(), CoderRegistry(), ReferenceManager()
    )

    # Test input validation
    with pytest.raises(ValueError, match="Input data cannot be empty"):
        factory.create({})

    # Test resource type validation
    with pytest.raises(ValueError, match="resource_type is required"):
        factory.create({'name': 'Test'})

def test_coding_functionality():
    """Should integrate with coding systems"""
    coders = CoderRegistry()

    coding = coders.add_coding(None, 'LOINC', '12345-6', 'Test Code')
    assert coding['system'] == 'http://loinc.org'
    assert coding['code'] == '12345-6'
    assert coding['display'] == 'Test Code'

def test_reference_management():
    """Should manage FHIR references"""
    ref_manager = ReferenceManager()

    from fhir.resources.patient import Patient
    patient = Patient()
    patient.resourceType = "Patient"

    reference = ref_manager.create_reference(patient)
    assert reference.startswith('Patient/')

    resolved = ref_manager.resolve_reference(reference)
    assert resolved is patient
```

## Performance Requirements

- Base factory creation: <1ms
- Validation checks: <0.5ms per validator
- Coding lookup: <0.1ms (cached)
- Reference creation: <0.1ms
- Memory overhead: <5MB for all shared components

## File List

**Files to Create:**
- `src/nl_fhir/services/fhir/factories/base.py` - Base factory class
- `src/nl_fhir/services/fhir/factories/validators.py` - Validation registry
- `src/nl_fhir/services/fhir/factories/coders.py` - Coding systems
- `src/nl_fhir/services/fhir/factories/references.py` - Reference manager
- `tests/services/fhir/factories/test_base_factory.py` - Unit tests
- `tests/services/fhir/factories/test_validators.py` - Validator tests
- `tests/services/fhir/factories/test_coders.py` - Coder tests

**Files to Update:**
- `src/nl_fhir/services/fhir/factories/__init__.py` - Add component initialization

## Definition of Done

- [ ] All base factory components implemented
- [ ] Shared components (validators, coders, references) working
- [ ] Template method pattern working correctly
- [ ] 100% unit test coverage
- [ ] Performance benchmarks met
- [ ] Integration with Factory Registry
- [ ] Mock factory for testing other stories
- [ ] Code reviewed and approved

---
**Story Status:** READY FOR DEVELOPMENT
**Next Story:** REFACTOR-003 - Extract Patient Resource Factory