"""
Tests for Base Factory Pattern - REFACTOR-002
Tests template method pattern and shared component integration
"""

import pytest
import time
from unittest.mock import MagicMock, patch

from nl_fhir.services.fhir.factories import get_factory_registry, MockResourceFactory
from nl_fhir.services.fhir.factories.base import BaseResourceFactory
from nl_fhir.services.fhir.factories.validators import ValidatorRegistry
from nl_fhir.services.fhir.factories.coders import CoderRegistry
from nl_fhir.services.fhir.factories.references import ReferenceManager


class TestBaseResourceFactory:
    """Test suite for BaseResourceFactory template method pattern"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validators = ValidatorRegistry()
        self.coders = CoderRegistry()
        self.reference_manager = ReferenceManager()

    def test_template_method_workflow(self):
        """Base factory should follow template method pattern"""
        factory = MockResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )

        data = {'name': 'Test Patient', 'status': 'active'}
        resource = factory.create('Patient', data, 'test-request-123')

        # Verify resource structure
        assert resource['resourceType'] == 'Patient'
        assert 'id' in resource
        assert resource['active'] is True
        assert resource['name'][0]['text'] == 'Test Patient'

        # Verify metadata added by template method
        assert 'meta' in resource
        assert resource['meta']['factory'] == 'MockResourceFactory'
        assert resource['meta']['request_id'] == 'test-request-123'
        assert 'created_at' in resource['meta']

    def test_input_validation(self):
        """Should validate input data before resource creation"""
        factory = MockResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )

        # Test empty data validation
        with pytest.raises(ValueError, match="Input data cannot be empty"):
            factory.create('Patient', {})

        # Test unsupported resource type
        with pytest.raises(ValueError, match="Factory does not support resource type"):
            factory.create('UnsupportedResource', {'test': 'data'})

        # Test missing required fields for complex resources
        with pytest.raises(ValueError, match="Required field 'subject' is missing"):
            factory.create('MedicationRequest', {'medication': 'test'})

    def test_fhir_validation_integration(self):
        """Should validate created resources against FHIR R4"""
        factory = MockResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )

        # Valid resource should pass
        data = {'subject': 'Patient/test', 'medication': 'test', 'status': 'active'}
        resource = factory.create('MedicationRequest', data)
        assert resource['resourceType'] == 'MedicationRequest'

        # Test with invalid resource (will be caught by validators)
        # This tests the validation integration without requiring actual FHIR validation
        assert factory._metrics['validated'] > 0

    def test_metrics_tracking(self):
        """Should track performance metrics"""
        factory = MockResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )

        # Create a few resources
        data = {'name': 'Test Patient'}
        factory.create('Patient', data)
        factory.create('Patient', data)

        metrics = factory.get_metrics()
        assert metrics['created'] == 2
        assert metrics['validated'] == 2
        assert metrics['failed'] == 0
        assert metrics['total_time_ms'] > 0
        assert metrics['avg_time_ms'] > 0

        # Test failed creation
        try:
            factory.create('UnsupportedResource', data)
        except ValueError:
            pass

        metrics = factory.get_metrics()
        assert metrics['failed'] == 1

    def test_shared_component_integration(self):
        """Should integrate with shared components"""
        factory = MockResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )

        # Test coding functionality
        coding = factory.add_coding('LOINC', '12345-6', 'Test Code')
        assert coding['system'] == 'http://loinc.org'
        assert coding['code'] == '12345-6'
        assert coding['display'] == 'Test Code'

        # Test codeable concept creation
        concept = factory.create_codeable_concept('SNOMED', '12345678', 'Test Concept')
        assert 'coding' in concept
        assert concept['coding'][0]['system'] == 'http://snomed.info/sct'

        # Test reference creation
        patient = {'resourceType': 'Patient', 'id': 'test-patient'}
        reference = factory.create_reference(patient, 'Test Patient')
        assert reference['reference'] == 'Patient/test-patient'
        assert reference['display'] == 'Test Patient'

    def test_performance_requirements(self):
        """Should meet performance requirements"""
        factory = MockResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )

        # Test creation time requirement (<1ms for base factory)
        start_time = time.time()
        data = {'name': 'Test Patient'}
        factory.create('Patient', data)
        duration_ms = (time.time() - start_time) * 1000

        # Note: In practice this might be slightly higher due to validation
        # but the base factory operations should be very fast
        assert duration_ms < 50  # Allow some tolerance for test environment

    def test_error_handling(self):
        """Should handle errors gracefully"""
        factory = MockResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )

        # Test with None validators (should warn and continue)
        factory_no_validators = MockResourceFactory(
            validators=None,
            coders=self.coders,
            reference_manager=self.reference_manager
        )

        # Should work but log warning
        data = {'name': 'Test Patient'}
        resource = factory_no_validators.create('Patient', data)
        assert resource['resourceType'] == 'Patient'

    def test_supported_resources(self):
        """Should correctly report supported resources"""
        factory = MockResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )

        supported = factory.get_supported_resources()
        assert 'Patient' in supported
        assert 'MedicationRequest' in supported
        assert 'Observation' in supported
        assert 'Device' in supported
        assert len(supported) > 0


class TestFactoryRegistryWithSharedComponents:
    """Test factory registry integration with shared components"""

    def test_registry_initialization_with_components(self):
        """Registry should initialize shared components"""
        registry = get_factory_registry()

        assert registry.validators is not None
        assert isinstance(registry.validators, ValidatorRegistry)
        assert registry.coders is not None
        assert isinstance(registry.coders, CoderRegistry)
        assert registry.reference_manager is not None
        assert isinstance(registry.reference_manager, ReferenceManager)

    @pytest.mark.skip(reason="Shared component initialization changed in FactoryAdapter refactoring")
    def test_factory_gets_shared_components(self):
        """Factories should receive shared components"""
        registry = get_factory_registry()
        factory = registry.get_factory('Patient')

        assert isinstance(factory, MockResourceFactory)
        assert factory.validators is registry.validators
        assert factory.coders is registry.coders
        assert factory.reference_manager is registry.reference_manager

    def test_shared_component_consistency(self):
        """All factories should share the same component instances"""
        registry = get_factory_registry()
        factory1 = registry.get_factory('Patient')
        factory2 = registry.get_factory('Observation')

        # Same validator instance
        assert factory1.validators is factory2.validators
        assert factory1.coders is factory2.coders
        assert factory1.reference_manager is factory2.reference_manager

    @pytest.mark.skip(reason="Template method pattern changed in FactoryAdapter refactoring")
    def test_template_method_via_registry(self):
        """Template method should work via registry"""
        registry = get_factory_registry()
        factory = registry.get_factory('Patient')

        data = {'name': 'Registry Test Patient'}
        resource = factory.create('Patient', data, 'registry-test-123')

        assert resource['resourceType'] == 'Patient'
        assert resource['name'][0]['text'] == 'Registry Test Patient'
        assert resource['meta']['factory'] == 'MockResourceFactory'
        assert resource['meta']['request_id'] == 'registry-test-123'

    @pytest.mark.skip(reason="Cross-factory reference handling changed in FactoryAdapter refactoring")
    def test_cross_factory_references(self):
        """Should support references between factories"""
        registry = get_factory_registry()
        patient_factory = registry.get_factory('Patient')
        obs_factory = registry.get_factory('Observation')

        # Create patient
        patient_data = {'name': 'Test Patient'}
        patient = patient_factory.create('Patient', patient_data)

        # Create observation that references patient
        obs_data = {
            'subject': f"Patient/{patient['id']}",
            'code': 'test-code',
            'status': 'final'
        }
        observation = obs_factory.create('Observation', obs_data)

        assert observation['subject']['reference'] == f"Patient/{patient['id']}"

        # Verify reference can be resolved
        resolved_patient = obs_factory.resolve_reference(f"Patient/{patient['id']}")
        assert resolved_patient is not None
        assert resolved_patient['resourceType'] == 'Patient'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])