"""
FHIR Factory Registry - REFACTOR-001
Singleton registry for managing FHIR resource factories with lazy loading
"""

from typing import Dict, Type, Optional, Any
import logging
import time
from functools import lru_cache

from .base import BaseResourceFactory
from ....config import get_settings

logger = logging.getLogger(__name__)


class FactoryRegistry:
    """
    Singleton registry for managing FHIR resource factories.

    Features:
    - Lazy loading of factories (only instantiate when first requested)
    - Feature flag integration for gradual migration
    - LRU caching for performance
    - Backward compatibility with legacy factory
    """

    _instance = None
    _factories: Dict[str, BaseResourceFactory] = {}

    def __new__(cls):
        """Ensure singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize registry with factory mappings"""
        if hasattr(self, '_initialized') and self._initialized:
            return

        start_time = time.time()

        self.settings = get_settings()
        self._factories = {}
        self._factory_classes = {}
        self._legacy_factory = None
        self._register_factory_mappings()
        self._initialized = True

        init_time = (time.time() - start_time) * 1000
        logger.info(f"FactoryRegistry initialized in {init_time:.2f}ms")

        # Log performance requirement compliance
        if init_time > 5.0:
            logger.warning(f"Registry initialization took {init_time:.2f}ms (target: <5ms)")

    def _register_factory_mappings(self):
        """
        Register factory class mappings for lazy loading.

        Maps resource types to their corresponding factory classes.
        Will be expanded as specialized factories are implemented.
        """
        self._factory_classes = {
            # Patient and demographic resources
            'Patient': 'PatientResourceFactory',
            'Practitioner': 'PatientResourceFactory',
            'RelatedPerson': 'PatientResourceFactory',

            # Medication resources
            'MedicationRequest': 'MedicationResourceFactory',
            'MedicationAdministration': 'MedicationResourceFactory',
            'Medication': 'MedicationResourceFactory',
            'MedicationDispense': 'MedicationResourceFactory',
            'MedicationStatement': 'MedicationResourceFactory',

            # Clinical observation resources
            'Observation': 'ClinicalResourceFactory',
            'DiagnosticReport': 'ClinicalResourceFactory',
            'ServiceRequest': 'ClinicalResourceFactory',
            'Condition': 'ClinicalResourceFactory',
            'AllergyIntolerance': 'ClinicalResourceFactory',

            # Device and equipment resources
            'Device': 'DeviceResourceFactory',
            'DeviceUseStatement': 'DeviceResourceFactory',
            'DeviceMetric': 'DeviceResourceFactory',

            # Encounter and workflow resources
            'Encounter': 'EncounterResourceFactory',
            'CarePlan': 'EncounterResourceFactory',
            'Goal': 'EncounterResourceFactory',
            'CareTeam': 'EncounterResourceFactory',

            # Location and organization resources
            'Location': 'OrganizationalResourceFactory',
            'Organization': 'OrganizationalResourceFactory',
            'HealthcareService': 'OrganizationalResourceFactory',
        }

        if self.settings.factory_debug_logging:
            logger.debug(f"Registered {len(self._factory_classes)} factory mappings")

    @lru_cache(maxsize=32)
    def get_factory(self, resource_type: str) -> BaseResourceFactory:
        """
        Get factory for resource type with caching.

        Args:
            resource_type: FHIR resource type (e.g., 'Patient')

        Returns:
            Factory instance capable of creating the resource

        Performance: <0.1ms for cached, <10ms for first load
        """
        start_time = time.time()

        # Check feature flag for legacy mode
        if self.settings.use_legacy_factory:
            factory = self._get_legacy_factory()
            if self.settings.factory_debug_logging:
                load_time = (time.time() - start_time) * 1000
                logger.debug(f"Retrieved legacy factory for {resource_type} in {load_time:.2f}ms")
            return factory

        # Lazy load factory if not already loaded
        if resource_type not in self._factories:
            self._load_factory(resource_type)

        factory = self._factories.get(resource_type, self._get_legacy_factory())

        if self.settings.factory_debug_logging:
            load_time = (time.time() - start_time) * 1000
            logger.debug(f"Retrieved factory for {resource_type} in {load_time:.2f}ms")

        return factory

    def _load_factory(self, resource_type: str):
        """
        Dynamically load factory for resource type.

        Args:
            resource_type: FHIR resource type to load factory for
        """
        factory_class_name = self._factory_classes.get(resource_type)

        if not factory_class_name:
            # Fall back to legacy for unknown types
            if self.settings.factory_debug_logging:
                logger.debug(f"No factory registered for {resource_type}, using legacy")
            self._factories[resource_type] = self._get_legacy_factory()
            return

        # For Phase 1, all specialized factories delegate to legacy
        # This will be replaced with actual factory imports in future stories
        if self.settings.factory_debug_logging:
            logger.debug(f"Loading {factory_class_name} for {resource_type} (delegating to legacy)")

        self._factories[resource_type] = self._get_legacy_factory()

        # TODO: Future implementation will dynamically import specialized factories:
        # try:
        #     module_name = f".{factory_class_name.lower()}"
        #     module = importlib.import_module(module_name, package=__name__)
        #     factory_class = getattr(module, factory_class_name)
        #     self._factories[resource_type] = factory_class()
        # except ImportError:
        #     logger.warning(f"Could not import {factory_class_name}, using legacy")
        #     self._factories[resource_type] = self._get_legacy_factory()

    def _get_legacy_factory(self):
        """
        Get legacy factory for backward compatibility.

        Returns:
            Legacy FHIRResourceFactory instance
        """
        if self._legacy_factory is None:
            # Import here to avoid circular dependencies
            from ..resource_factory import FHIRResourceFactory
            self._legacy_factory = FHIRResourceFactory()

            if self.settings.factory_debug_logging:
                logger.debug("Initialized legacy factory instance")

        return self._legacy_factory

    def get_factory_stats(self) -> Dict[str, Any]:
        """
        Get factory usage statistics for monitoring.

        Returns:
            Dictionary with factory metrics
        """
        if not self.settings.enable_factory_metrics:
            return {"metrics_disabled": True}

        return {
            "registered_factory_types": len(self._factory_classes),
            "loaded_factories": len(self._factories),
            "cache_info": dict(self.get_factory.cache_info()._asdict()),
            "legacy_factory_loaded": self._legacy_factory is not None,
            "feature_flags": {
                "use_legacy_factory": self.settings.use_legacy_factory,
                "use_new_patient_factory": self.settings.use_new_patient_factory,
                "use_new_medication_factory": self.settings.use_new_medication_factory,
                "use_new_clinical_factory": self.settings.use_new_clinical_factory,
            }
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on factory registry.

        Returns:
            Health status information
        """
        try:
            # Test factory retrieval performance
            start_time = time.time()
            test_factory = self.get_factory('Patient')
            retrieval_time = (time.time() - start_time) * 1000

            return {
                "status": "healthy",
                "initialized": self._initialized,
                "retrieval_time_ms": retrieval_time,
                "registered_factories": len(self._factory_classes),
                "loaded_factories": len(self._factories),
                "performance_ok": retrieval_time < 10.0  # <10ms requirement
            }
        except Exception as e:
            logger.error(f"Factory registry health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": getattr(self, '_initialized', False)
            }

    def clear_cache(self):
        """Clear factory cache for testing purposes"""
        self.get_factory.cache_clear()
        if self.settings.factory_debug_logging:
            logger.debug("Factory cache cleared")


# Global registry instance
factory_registry = FactoryRegistry()


def get_factory_registry() -> FactoryRegistry:
    """
    Get global factory registry instance.

    Returns:
        Singleton FactoryRegistry instance
    """
    return factory_registry