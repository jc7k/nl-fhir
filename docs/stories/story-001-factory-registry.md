# Story: Implement Factory Registry Pattern for FHIR Resource Creation

**Story ID:** REFACTOR-001
**Epic:** FHIRResourceFactory Decomposition (Phase 1: Foundation)
**Status:** READY FOR DEVELOPMENT
**Estimated Effort:** 8 hours
**Priority:** P0 - Critical

## User Story

**As a** developer working with FHIR resources
**I want** a Factory Registry that dynamically manages resource factories
**So that** resource creation is modular and maintainable without a 10,600-line God class

## Background & Context

The current `FHIRResourceFactory` class has grown to 10,600 lines with 219 methods, making it unmaintainable and risky to modify. This story implements the foundation of the refactoring: a Factory Registry pattern that will manage specialized factories for different FHIR resource types.

**Current State:**
- Single monolithic class: `src/nl_fhir/services/fhir/resource_factory.py`
- All resource creation logic in one place
- Tight coupling, impossible to unit test individual resource types
- Any change risks breaking entire FHIR pipeline

**Target State:**
- Factory Registry managing multiple specialized factories
- Each factory responsible for related resource types
- Lazy loading for performance optimization
- Feature flag support for gradual migration

## Acceptance Criteria

### Must Have
- [ ] Factory Registry class implemented with singleton pattern
- [ ] Registry supports dynamic factory registration and retrieval
- [ ] Lazy loading of factories (only instantiate when first requested)
- [ ] Feature flag integration for legacy/new factory switching
- [ ] Backward compatibility adapter maintaining existing API
- [ ] 100% unit test coverage for Registry
- [ ] Performance benchmarks showing <5ms initialization time
- [ ] No breaking changes to existing `/convert` API endpoint

### Should Have
- [ ] Factory caching with LRU cache for frequently used factories
- [ ] Metrics collection for factory usage patterns
- [ ] Debug logging for factory loading and instantiation
- [ ] Registry health check endpoint

### Could Have
- [ ] Factory preloading option for high-traffic resources
- [ ] Registry configuration from external config file

## Technical Specifications

### 1. Create Factory Registry Structure

```python
# src/nl_fhir/services/fhir/factories/__init__.py

from typing import Dict, Type, Optional
from abc import ABC
import logging
from functools import lru_cache
from ..config import feature_flags

class BaseResourceFactory(ABC):
    """Abstract base class for all FHIR resource factories"""

    def __init__(self, validators=None, coders=None, reference_manager=None):
        self.validators = validators
        self.coders = coders
        self.reference_manager = reference_manager

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Resource:
        """Create FHIR resource from extracted data"""
        pass

    @abstractmethod
    def supports(self, resource_type: str) -> bool:
        """Check if factory supports resource type"""
        pass

class FactoryRegistry:
    """
    Singleton registry for managing FHIR resource factories.
    Supports lazy loading and feature flag switching.
    """

    _instance = None
    _factories: Dict[str, BaseResourceFactory] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._factories = {}
        self._factory_classes = {}
        self._register_factory_mappings()
        self._initialized = True

        logger.info("FactoryRegistry initialized")

    def _register_factory_mappings(self):
        """Register factory class mappings (lazy loading)"""
        # Will be populated with actual factories in next stories
        self._factory_classes = {
            'Patient': 'PatientResourceFactory',
            'MedicationRequest': 'MedicationResourceFactory',
            'Observation': 'ClinicalResourceFactory',
            # ... more mappings
        }

    @lru_cache(maxsize=32)
    def get_factory(self, resource_type: str) -> BaseResourceFactory:
        """Get factory for resource type with caching"""

        # Check feature flag for legacy mode
        if feature_flags.is_enabled('use_legacy_factory'):
            return self._get_legacy_factory()

        # Lazy load factory if not already loaded
        if resource_type not in self._factories:
            self._load_factory(resource_type)

        return self._factories.get(resource_type)

    def _load_factory(self, resource_type: str):
        """Dynamically load factory for resource type"""
        factory_class_name = self._factory_classes.get(resource_type)

        if not factory_class_name:
            # Fall back to legacy for unknown types
            logger.warning(f"No factory registered for {resource_type}, using legacy")
            self._factories[resource_type] = self._get_legacy_factory()
            return

        # Dynamic import (will be implemented with actual factories)
        # For now, return legacy factory as placeholder
        self._factories[resource_type] = self._get_legacy_factory()

    def _get_legacy_factory(self):
        """Get legacy factory for backward compatibility"""
        from ..resource_factory import FHIRResourceFactory
        return FHIRResourceFactory()
```

### 2. Backward Compatibility Adapter

```python
# src/nl_fhir/services/fhir/resource_factory.py (modified)

class FHIRResourceFactory:
    """
    Legacy interface maintained during migration.
    Delegates to Factory Registry when new factories available.
    """

    def __init__(self):
        self.registry = FactoryRegistry()
        self._legacy_mode = feature_flags.is_enabled('use_legacy_factory')

    def create_resource(self, resource_type: str, data: Dict) -> Resource:
        """Maintain existing API while delegating to registry"""

        if self._legacy_mode:
            # Use existing implementation
            return self._legacy_create_resource(resource_type, data)

        # Delegate to appropriate factory via registry
        factory = self.registry.get_factory(resource_type)
        return factory.create(data)

    # ... existing 219 methods remain but will be migrated gradually
```

### 3. Feature Flag Configuration

```python
# src/nl_fhir/services/config.py

FEATURE_FLAGS = {
    'use_legacy_factory': True,  # Start with legacy, switch per factory
    'use_new_patient_factory': False,
    'use_new_medication_factory': False,
    'use_new_clinical_factory': False,
    'enable_factory_metrics': True,
    'factory_debug_logging': True,
}

class FeatureFlags:
    @classmethod
    def is_enabled(cls, flag: str) -> bool:
        return FEATURE_FLAGS.get(flag, False)

    @classmethod
    def set(cls, flag: str, value: bool):
        FEATURE_FLAGS[flag] = value
        logger.info(f"Feature flag {flag} set to {value}")
```

## Test Requirements

### Unit Tests

```python
# tests/services/fhir/factories/test_factory_registry.py

def test_registry_singleton():
    """Registry should be singleton"""
    registry1 = FactoryRegistry()
    registry2 = FactoryRegistry()
    assert registry1 is registry2

def test_lazy_loading():
    """Factories should only load when requested"""
    registry = FactoryRegistry()
    assert len(registry._factories) == 0

    factory = registry.get_factory('Patient')
    assert 'Patient' in registry._factories

def test_feature_flag_switching():
    """Should respect feature flags"""
    feature_flags.set('use_legacy_factory', True)
    registry = FactoryRegistry()
    factory = registry.get_factory('Patient')
    assert isinstance(factory, FHIRResourceFactory)

def test_factory_caching():
    """Should cache factory instances"""
    registry = FactoryRegistry()
    factory1 = registry.get_factory('Patient')
    factory2 = registry.get_factory('Patient')
    assert factory1 is factory2

def test_initialization_performance():
    """Registry init should be <5ms"""
    start = time.time()
    registry = FactoryRegistry()
    duration = (time.time() - start) * 1000
    assert duration < 5.0
```

### Integration Tests

```python
# tests/integration/test_factory_registry_integration.py

def test_backward_compatibility():
    """Existing API should work unchanged"""
    factory = FHIRResourceFactory()
    patient_data = {"name": "John Doe", "dob": "1980-01-01"}

    resource = factory.create_resource('Patient', patient_data)
    assert resource.resourceType == 'Patient'

def test_gradual_migration():
    """Can switch individual factories"""
    feature_flags.set('use_legacy_factory', False)
    feature_flags.set('use_new_patient_factory', True)

    factory = FHIRResourceFactory()
    patient = factory.create_resource('Patient', {})
    medication = factory.create_resource('MedicationRequest', {})

    # Patient uses new factory, medication uses legacy
    assert patient.meta.get('factory') == 'new'
    assert medication.meta.get('factory') == 'legacy'
```

## Performance Requirements

- Registry initialization: <5ms
- Factory retrieval (cached): <0.1ms
- Factory retrieval (first load): <10ms
- Memory overhead: <10MB for registry + all factory metadata
- No degradation in resource creation time

## Rollback Plan

If issues occur:
1. Set `use_legacy_factory` feature flag to `true`
2. Registry automatically returns legacy factory for all requests
3. No code deployment needed, just configuration change
4. Monitor error rates and performance

## Dependencies

- No external dependencies
- Must be completed before any specialized factory implementation
- Blocks all other refactoring stories

## Implementation Notes

1. Start with empty factory classes that delegate to legacy
2. Implement one resource type at a time in subsequent stories
3. Use performance baseline script to validate no degradation
4. Run rollback tests after implementation

## File List

**Files to Create:**
- `src/nl_fhir/services/fhir/factories/__init__.py` - Registry and base class
- `src/nl_fhir/services/fhir/factories/base.py` - BaseResourceFactory
- `src/nl_fhir/services/config.py` - Feature flags configuration
- `tests/services/fhir/factories/test_factory_registry.py` - Unit tests
- `tests/integration/test_factory_registry_integration.py` - Integration tests

**Files to Modify:**
- `src/nl_fhir/services/fhir/resource_factory.py` - Add compatibility adapter

## Definition of Done

- [ ] All code implemented according to specifications
- [ ] 100% unit test coverage
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] Feature flags tested and working
- [ ] Rollback procedure validated
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] No breaking changes to existing API

---
**Story Status:** READY FOR DEVELOPMENT
**Next Story:** REFACTOR-002 - Implement Base Factory Pattern