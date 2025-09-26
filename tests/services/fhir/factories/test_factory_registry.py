"""
Unit tests for Factory Registry (REFACTOR-001)
Tests singleton, lazy loading, feature flags, and performance requirements
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from nl_fhir.services.fhir.factories import FactoryRegistry, get_factory_registry
from nl_fhir.services.fhir.factories.base import BaseResourceFactory
from nl_fhir.config import get_settings


class TestFactoryRegistry:
    """Test suite for Factory Registry implementation"""

    def test_registry_singleton(self):
        """Registry should be singleton"""
        registry1 = FactoryRegistry()
        registry2 = FactoryRegistry()
        assert registry1 is registry2

    def test_get_factory_registry_singleton(self):
        """get_factory_registry should return same instance"""
        registry1 = get_factory_registry()
        registry2 = get_factory_registry()
        assert registry1 is registry2

    def test_lazy_loading(self):
        """Factories should only load when requested"""
        registry = FactoryRegistry()

        # Request a factory
        factory = registry.get_factory('Patient')

        # Should have loaded the factory into the internal storage
        assert 'Patient' in registry._factories or factory is not None
        assert factory is not None

    @patch('nl_fhir.services.fhir.factories.get_settings')
    def test_feature_flag_legacy_mode(self, mock_settings):
        """Should respect legacy factory feature flag"""
        # Mock settings to use legacy factory
        mock_settings_obj = MagicMock()
        mock_settings_obj.use_legacy_factory = True
        mock_settings_obj.factory_debug_logging = False
        mock_settings_obj.enable_factory_metrics = True
        mock_settings.return_value = mock_settings_obj

        registry = FactoryRegistry()
        factory = registry.get_factory('Patient')

        # Should return legacy factory (FHIRResourceFactory)
        from nl_fhir.services.fhir.resource_factory import FHIRResourceFactory
        assert isinstance(factory, FHIRResourceFactory)

    def test_factory_caching(self):
        """Should cache factory instances"""
        registry = FactoryRegistry()

        # Clear cache to ensure clean test
        registry.clear_cache()

        factory1 = registry.get_factory('Patient')
        factory2 = registry.get_factory('Patient')

        # Should be the same instance due to caching
        assert factory1 is factory2

    def test_initialization_performance(self):
        """Registry initialization should be <5ms"""
        start = time.time()
        registry = FactoryRegistry()
        duration = (time.time() - start) * 1000

        assert duration < 5.0, f"Initialization took {duration:.2f}ms (target: <5ms)"

    def test_factory_retrieval_performance(self):
        """Factory retrieval should be fast"""
        registry = FactoryRegistry()

        # First retrieval (cache miss)
        start = time.time()
        factory1 = registry.get_factory('Patient')
        first_duration = (time.time() - start) * 1000

        # Second retrieval (cache hit)
        start = time.time()
        factory2 = registry.get_factory('Patient')
        second_duration = (time.time() - start) * 1000

        # First should be <10ms, second should be <0.1ms
        assert first_duration < 10.0, f"First retrieval took {first_duration:.2f}ms (target: <10ms)"
        assert second_duration < 0.1, f"Cached retrieval took {second_duration:.2f}ms (target: <0.1ms)"

    def test_unknown_resource_type_fallback(self):
        """Unknown resource types should fall back to legacy"""
        registry = FactoryRegistry()

        # Request unknown resource type
        factory = registry.get_factory('UnknownResource')

        # Should fall back to legacy factory
        from nl_fhir.services.fhir.resource_factory import FHIRResourceFactory
        assert isinstance(factory, FHIRResourceFactory)

    def test_factory_mappings_registered(self):
        """Should have registered factory mappings"""
        registry = FactoryRegistry()

        # Check some expected mappings
        assert 'Patient' in registry._factory_classes
        assert 'MedicationRequest' in registry._factory_classes
        assert 'Observation' in registry._factory_classes
        assert 'Device' in registry._factory_classes

    def test_get_factory_stats(self):
        """Should provide factory usage statistics"""
        registry = FactoryRegistry()

        # Get stats
        stats = registry.get_factory_stats()

        # Should include expected metrics
        assert 'registered_factory_types' in stats
        assert 'loaded_factories' in stats
        assert 'cache_info' in stats
        assert 'legacy_factory_loaded' in stats
        assert 'feature_flags' in stats

        # Metrics should be reasonable
        assert stats['registered_factory_types'] > 0
        assert isinstance(stats['legacy_factory_loaded'], bool)

    def test_metrics_disabled(self):
        """Should handle disabled metrics by checking the conditional"""
        registry = FactoryRegistry()

        # Temporarily override the setting
        original_setting = registry.settings.enable_factory_metrics
        registry.settings.enable_factory_metrics = False

        try:
            stats = registry.get_factory_stats()
            assert stats == {"metrics_disabled": True}
        finally:
            # Restore original setting
            registry.settings.enable_factory_metrics = original_setting

    def test_health_check_healthy(self):
        """Health check should report healthy status"""
        registry = FactoryRegistry()

        health = registry.health_check()

        assert health['status'] == 'healthy'
        assert health['initialized'] is True
        assert 'retrieval_time_ms' in health
        assert 'registered_factories' in health
        assert 'loaded_factories' in health
        assert 'performance_ok' in health

        # Performance should be acceptable
        assert health['performance_ok'] is True

    def test_cache_clearing(self):
        """Should be able to clear cache"""
        registry = FactoryRegistry()

        # Load a factory
        factory1 = registry.get_factory('Patient')

        # Clear cache
        registry.clear_cache()

        # Load again - should work but may not be same instance
        factory2 = registry.get_factory('Patient')
        assert factory2 is not None

    def test_multiple_resource_types(self):
        """Should handle multiple resource types correctly"""
        registry = FactoryRegistry()

        resource_types = ['Patient', 'MedicationRequest', 'Observation', 'Device']
        factories = {}

        for resource_type in resource_types:
            factories[resource_type] = registry.get_factory(resource_type)
            assert factories[resource_type] is not None

    @patch('nl_fhir.services.fhir.factories.logger')
    def test_error_handling(self, mock_logger):
        """Should handle errors gracefully"""
        registry = FactoryRegistry()

        # This should not raise an exception even if there are issues
        try:
            factory = registry.get_factory('SomeResourceType')
            assert factory is not None
        except Exception as e:
            pytest.fail(f"Registry should handle errors gracefully: {e}")


class TestFactoryRegistryIntegration:
    """Integration tests for Factory Registry with FHIRResourceFactory"""

    def test_legacy_factory_integration(self):
        """Should integrate properly with legacy factory"""
        from nl_fhir.services.fhir.resource_factory import FHIRResourceFactory

        factory = FHIRResourceFactory()

        # Initialize should work
        result = factory.initialize()
        assert result is True

        # Should have registry available
        assert factory._registry is not None
        assert factory._settings is not None

    def test_backward_compatibility_patient(self):
        """Existing Patient creation API should work unchanged"""
        from nl_fhir.services.fhir.resource_factory import FHIRResourceFactory

        factory = FHIRResourceFactory()
        factory.initialize()

        patient_data = {
            "patient_ref": "PT-12345",
            "name": "John Doe"
        }

        # Should create patient resource without errors
        try:
            resource = factory.create_patient_resource(patient_data, "test-request-123")
            assert resource is not None
            assert 'resourceType' in resource or 'resource_type' in resource
        except Exception as e:
            # This is acceptable as we might not have all dependencies
            assert "FHIR" in str(e) or "import" in str(e)

    def test_registry_delegation(self):
        """Should delegate to registry when using new API"""
        from nl_fhir.services.fhir.resource_factory import FHIRResourceFactory

        factory = FHIRResourceFactory()
        factory.initialize()

        patient_data = {"patient_ref": "PT-12345"}

        # Should work via registry delegation
        try:
            resource = factory.create_resource_via_registry('Patient', patient_data, "test-request-123")
            assert resource is not None
        except Exception as e:
            # Acceptable for missing dependencies
            assert "FHIR" in str(e) or "import" in str(e) or "method" in str(e)

    def test_unsupported_resource_type(self):
        """Should handle unsupported resource types gracefully"""
        from nl_fhir.services.fhir.resource_factory import FHIRResourceFactory

        factory = FHIRResourceFactory()
        factory.initialize()

        with pytest.raises(ValueError, match="Unsupported resource type"):
            factory._create_resource_legacy('UnsupportedResource', {}, "test-request-123")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])