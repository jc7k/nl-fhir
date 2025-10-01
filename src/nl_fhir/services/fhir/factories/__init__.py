"""
FHIR Factory Registry - REFACTOR-002
Enhanced registry with shared components and template method pattern support
"""

from typing import Dict, Type, Optional, Any
import logging
import time
from functools import lru_cache

from .base import BaseResourceFactory
from .validators import ValidatorRegistry
from .coders import CoderRegistry
from .references import ReferenceManager
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
        """Initialize registry with shared components and factory mappings"""
        if hasattr(self, '_initialized') and self._initialized:
            return

        start_time = time.time()

        self.settings = get_settings()

        # Initialize shared components (REFACTOR-002)
        self.validators = ValidatorRegistry()
        self.coders = CoderRegistry()
        self.reference_manager = ReferenceManager()

        # Factory management
        self._factories = {}
        self._factory_classes = {}
        self._legacy_factory = None
        self._legacy_factory_caller = None  # Track the calling legacy factory instance
        self._register_factory_mappings()
        self._initialized = True

        init_time = (time.time() - start_time) * 1000
        logger.info(f"FactoryRegistry initialized with shared components in {init_time:.2f}ms")

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
            # Patient and demographic resources (only resources PatientResourceFactory actually supports)
            'Patient': 'PatientResourceFactory',
            'RelatedPerson': 'PatientResourceFactory',
            'Person': 'PatientResourceFactory',
            'PractitionerRole': 'PatientResourceFactory',

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
            'Goal': 'EncounterResourceFactory',
            'CareTeam': 'EncounterResourceFactory',

            # Care planning resources
            'CarePlan': 'CarePlanResourceFactory',

            # Location and organization resources
            'Location': 'OrganizationalResourceFactory',
            'Organization': 'OrganizationalResourceFactory',
            'HealthcareService': 'OrganizationalResourceFactory',
        }

        if self.settings.factory_debug_logging:
            logger.debug(f"Registered {len(self._factory_classes)} factory mappings")

    def get_factory(self, resource_type: str, calling_factory=None) -> BaseResourceFactory:
        """
        Get factory for resource type with caching.

        Args:
            resource_type: FHIR resource type (e.g., 'Patient')
            calling_factory: The factory instance that is requesting another factory
                           (used to track legacy factory caller)

        Returns:
            Factory instance capable of creating the resource

        Performance: <0.1ms for cached, <10ms for first load
        """
        start_time = time.time()

        # Check feature flag for legacy mode
        if self.settings.use_legacy_factory:
            factory = self._get_legacy_factory(calling_factory)
            if self.settings.factory_debug_logging:
                load_time = (time.time() - start_time) * 1000
                logger.debug(f"Retrieved legacy factory for {resource_type} in {load_time:.2f}ms")
            return factory

        # Lazy load factory if not already loaded
        if resource_type not in self._factories:
            self._load_factory(resource_type)

        factory = self._factories.get(resource_type, self._get_legacy_factory(calling_factory))

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

        # REFACTOR-003: Check for patient-specific feature flag
        if (factory_class_name == 'PatientResourceFactory' and
            self.settings.use_new_patient_factory):
            try:
                from .patient_factory import PatientResourceFactory
                factory = PatientResourceFactory(
                    validators=self.validators,
                    coders=self.coders,
                    reference_manager=self.reference_manager
                )
                self._factories[resource_type] = factory
                if self.settings.factory_debug_logging:
                    logger.info(f"Loaded PatientResourceFactory for {resource_type}")
                return
            except ImportError as e:
                logger.warning(f"Could not import PatientResourceFactory: {e}, falling back to mock")

        # REFACTOR-004: Check for medication-specific feature flag
        if (factory_class_name == 'MedicationResourceFactory' and
            self.settings.use_new_medication_factory):
            try:
                from .medication_factory import MedicationResourceFactory
                factory = MedicationResourceFactory(
                    validators=self.validators,
                    coders=self.coders,
                    reference_manager=self.reference_manager
                )
                self._factories[resource_type] = factory
                if self.settings.factory_debug_logging:
                    logger.info(f"Loaded MedicationResourceFactory for {resource_type}")
                return
            except ImportError as e:
                logger.warning(f"Could not import MedicationResourceFactory: {e}, falling back to mock")

        # REFACTOR-005: Check for clinical-specific feature flag
        if (factory_class_name == 'ClinicalResourceFactory' and
            self.settings.use_new_clinical_factory):
            try:
                from .clinical_factory import ClinicalResourceFactory
                factory = ClinicalResourceFactory(
                    validators=self.validators,
                    coders=self.coders,
                    reference_manager=self.reference_manager
                )
                self._factories[resource_type] = factory
                if self.settings.factory_debug_logging:
                    logger.info(f"Loaded ClinicalResourceFactory for {resource_type}")
                return
            except ImportError as e:
                logger.warning(f"Could not import ClinicalResourceFactory: {e}, falling back to mock")

        # REFACTOR-006: Check for device-specific feature flag
        if (factory_class_name == 'DeviceResourceFactory'):
            try:
                from .device_factory import DeviceResourceFactory
                factory = DeviceResourceFactory(
                    validators=self.validators,
                    coders=self.coders,
                    reference_manager=self.reference_manager
                )
                self._factories[resource_type] = factory
                if self.settings.factory_debug_logging:
                    logger.info(f"Loaded DeviceResourceFactory for {resource_type}")
                return
            except ImportError as e:
                logger.warning(f"Could not import DeviceResourceFactory: {e}, falling back to mock")

        # REFACTOR-007: Check for CarePlan-specific feature flag
        if (factory_class_name == 'CarePlanResourceFactory' and
            getattr(self.settings, 'use_new_careplan_factory', True)):
            try:
                from .careplan_factory import CarePlanResourceFactory
                factory = CarePlanResourceFactory(
                    validators=self.validators,
                    coders=self.coders,
                    reference_manager=self.reference_manager
                )
                self._factories[resource_type] = factory
                if self.settings.factory_debug_logging:
                    logger.info(f"Loaded CarePlanResourceFactory for {resource_type}")
                return
            except ImportError as e:
                logger.warning(f"Could not import CarePlanResourceFactory: {e}, falling back to mock")

        # EPIC 7.4: Check for Encounter/Goal-specific feature flag
        if (factory_class_name == 'EncounterResourceFactory' and
            getattr(self.settings, 'use_new_encounter_factory', True)):
            try:
                from .encounter_factory import EncounterResourceFactory
                factory = EncounterResourceFactory(
                    validators=self.validators,
                    coders=self.coders,
                    reference_manager=self.reference_manager
                )
                self._factories[resource_type] = factory
                if self.settings.factory_debug_logging:
                    logger.info(f"Loaded EncounterResourceFactory for {resource_type}")
                return
            except ImportError as e:
                logger.warning(f"Could not import EncounterResourceFactory: {e}, falling back to mock")

        # REFACTOR-002: Create mock factory with shared components for testing
        if self.settings.factory_debug_logging:
            logger.debug(f"Loading {factory_class_name} for {resource_type} (using mock factory with shared components)")

        # Create mock factory with shared components
        mock_factory = MockResourceFactory(
            validators=self.validators,
            coders=self.coders,
            reference_manager=self.reference_manager
        )
        self._factories[resource_type] = mock_factory

        # TODO: Future implementation will dynamically import specialized factories:
        # try:
        #     module_name = f".{factory_class_name.lower()}"
        #     module = importlib.import_module(module_name, package=__name__)
        #     factory_class = getattr(module, factory_class_name)
        #     self._factories[resource_type] = factory_class(
        #         validators=self.validators,
        #         coders=self.coders,
        #         reference_manager=self.reference_manager
        #     )
        # except ImportError:
        #     logger.warning(f"Could not import {factory_class_name}, using mock factory")
        #     self._factories[resource_type] = mock_factory

    def _get_legacy_factory(self, calling_factory=None):
        """
        Get legacy factory for backward compatibility.

        Args:
            calling_factory: The factory instance that is requesting the legacy factory
                           (if provided, we return the same instance to avoid identity issues)

        Returns:
            Legacy FHIRResourceFactory instance
        """
        # If we have a calling factory, check if it's a legacy factory instance
        if calling_factory is not None:
            # Check if it's a legacy factory by looking for specific attributes
            if (hasattr(calling_factory, '_create_resource_legacy') and
                hasattr(calling_factory, 'create_resource_via_registry')):
                # Return the same instance to maintain identity
                self._legacy_factory_caller = calling_factory
                return calling_factory

        # If we have a tracked caller, return it
        if self._legacy_factory_caller is not None:
            return self._legacy_factory_caller

        # Otherwise, create a new legacy factory instance
        if self._legacy_factory is None:
            try:
                # Import here to avoid circular dependencies
                from ..resource_factory import FHIRResourceFactory
                self._legacy_factory = FHIRResourceFactory()

                if self.settings.factory_debug_logging:
                    logger.debug("Initialized legacy factory instance")
            except ImportError:
                # Legacy factory module not available - this is expected after cleanup
                logger.warning("Legacy factory module not available - using mock factory")
                # Return a mock factory instead
                self._legacy_factory = MockResourceFactory(
                    validators=self.validators,
                    coders=self.coders,
                    reference_manager=self.reference_manager
                )

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
            "cache_strategy": "manual_factory_cache",  # No LRU cache on get_factory method
            "legacy_factory_loaded": self._legacy_factory is not None,
            "legacy_factory_caller_tracked": self._legacy_factory_caller is not None,
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
        # Since we removed LRU cache from get_factory, clear the factories dict
        self._factories.clear()
        self._legacy_factory = None
        self._legacy_factory_caller = None
        if self.settings.factory_debug_logging:
            logger.debug("Factory cache cleared")


# Mock Factory for Testing Base Factory Pattern (REFACTOR-002)
class MockResourceFactory(BaseResourceFactory):
    """
    Mock factory implementation for testing the base factory pattern.

    This factory creates basic FHIR resources with proper validation
    and shared component integration. Will be replaced by specialized
    factories in future refactoring stories.
    """

    def _create_resource(self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create basic FHIR resource with minimal required fields.

        Args:
            resource_type: FHIR resource type
            data: Input data
            request_id: Optional request identifier

        Returns:
            Basic FHIR resource dictionary
        """
        # Create basic resource structure
        resource = {
            'resourceType': resource_type,
            'id': self._generate_resource_id(resource_type)
        }

        # Add resource-specific fields based on type
        if resource_type == 'Patient':
            resource.update(self._create_patient_fields(data))
        elif resource_type == 'Observation':
            resource.update(self._create_observation_fields(data))
        elif resource_type == 'MedicationRequest':
            resource.update(self._create_medication_request_fields(data))
        elif resource_type == 'Device':
            resource.update(self._create_device_fields(data))
        else:
            # Generic resource with minimal fields
            resource.update({
                'status': data.get('status', 'active'),
                'text': {
                    'status': 'generated',
                    'div': f'<div>Mock {resource_type} resource</div>'
                }
            })

        return resource

    def _create_patient_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Patient-specific fields"""
        fields = {'active': True}

        if data.get('name'):
            fields['name'] = [{
                'use': 'official',
                'text': data['name']
            }]

        if data.get('gender'):
            fields['gender'] = data['gender']

        if data.get('birthDate'):
            fields['birthDate'] = data['birthDate']

        return fields

    def _create_observation_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Observation-specific fields"""
        fields = {
            'status': data.get('status', 'final'),
            'code': self.create_codeable_concept('LOINC', '12345-6', 'Test Code'),
            'subject': {'reference': data.get('subject', 'Patient/test-patient')}
        }

        if data.get('value'):
            fields['valueString'] = str(data['value'])

        return fields

    def _create_medication_request_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create MedicationRequest-specific fields"""
        fields = {
            'status': data.get('status', 'active'),
            'intent': data.get('intent', 'order'),
            'subject': {'reference': data.get('subject', 'Patient/test-patient')},
            'medicationCodeableConcept': self.create_codeable_concept('RXNORM', '12345', 'Test Medication')
        }

        if data.get('dosage'):
            fields['dosageInstruction'] = [{
                'text': data['dosage']
            }]

        return fields

    def _create_device_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Device-specific fields"""
        fields = {
            'status': data.get('status', 'active'),
            'deviceName': [{
                'name': data.get('name', 'Test Device'),
                'type': 'user-friendly-name'
            }]
        }

        if data.get('type'):
            fields['type'] = self.create_codeable_concept('SNOMED', '12345678', data['type'])

        return fields

    def supports(self, resource_type: str) -> bool:
        """
        Check if mock factory supports resource type.

        For testing purposes, supports common FHIR resource types.
        """
        supported_types = {
            'Patient', 'Practitioner', 'Observation', 'MedicationRequest',
            'MedicationAdministration', 'Device', 'DeviceUseStatement',
            'ServiceRequest', 'Condition', 'Encounter', 'DiagnosticReport',
            'AllergyIntolerance', 'Medication', 'CarePlan', 'Immunization',
            'Location'
        }
        return resource_type in supported_types


# Global registry instance
factory_registry = FactoryRegistry()


def get_factory_registry() -> FactoryRegistry:
    """
    Get global factory registry instance.

    Returns:
        Singleton FactoryRegistry instance
    """
    return factory_registry