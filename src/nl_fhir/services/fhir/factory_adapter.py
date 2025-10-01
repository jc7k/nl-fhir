"""
Factory Adapter for Legacy Compatibility
Bridges between new factory registry and legacy get_fhir_resource_factory() pattern
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .factories import get_factory_registry, FactoryRegistry
from ...config import get_settings

logger = logging.getLogger(__name__)


class FactoryAdapter:
    """
    Adapter that provides legacy FHIRResourceFactory interface using new factory registry.

    This allows gradual migration by maintaining the same API while using the new
    modular factory system under the hood.
    """

    def __init__(self):
        self.registry: FactoryRegistry = get_factory_registry()
        self.settings = get_settings()
        self._initialized = False

    def initialize(self):
        """Initialize the adapter (for legacy compatibility)"""
        if not self._initialized:
            logger.info("FactoryAdapter initialized with new factory registry")
            self._initialized = True

    async def create_resource(self, resource_type: str, data: Dict[str, Any],
                            request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create FHIR resource using appropriate factory from registry.

        Args:
            resource_type: FHIR resource type (e.g., 'Patient', 'MedicationRequest')
            data: Input data for resource creation
            request_id: Optional request identifier for tracking

        Returns:
            FHIR resource dictionary
        """
        try:
            # Get appropriate factory for this resource type
            factory = self.registry.get_factory(resource_type)

            # Create resource using the factory
            # Note: New factories use create() method, legacy uses create_resource()
            if hasattr(factory, 'create'):
                resource = factory.create(resource_type, data, request_id)
            else:
                # Legacy factory fallback
                resource = await factory.create_resource(resource_type, data, request_id)

            if self.settings.factory_debug_logging:
                logger.debug(f"Created {resource_type} using {factory.__class__.__name__}")

            return resource

        except Exception as e:
            logger.error(f"Failed to create {resource_type}: {e}")
            raise

    def supports(self, resource_type: str) -> bool:
        """
        Check if any factory in the registry supports this resource type.

        Args:
            resource_type: FHIR resource type to check

        Returns:
            True if supported, False otherwise
        """
        try:
            factory = self.registry.get_factory(resource_type)
            return factory.supports(resource_type)
        except Exception:
            return False

    def get_supported_resources(self) -> List[str]:
        """
        Get list of all supported resource types across all factories.

        Returns:
            List of supported FHIR resource types
        """
        # Get from registry mappings
        return list(self.registry._factory_classes.keys())

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the adapter and underlying registry.

        Returns:
            Health status information
        """
        try:
            registry_health = self.registry.health_check()

            return {
                "adapter_status": "healthy" if self._initialized else "not_initialized",
                "registry_health": registry_health,
                "using_legacy_factory": self.settings.use_legacy_factory,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"FactoryAdapter health check failed: {e}")
            return {
                "adapter_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    # Legacy compatibility methods

    def create_patient_resource(self, patient_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Legacy method for creating Patient resources"""
        # Use synchronous factory call since new factories are synchronous
        factory = self.registry.get_factory('Patient')
        if hasattr(factory, 'create'):
            return factory.create('Patient', patient_data, request_id)
        else:
            # Legacy fallback - but this shouldn't happen with adapter
            import asyncio
            return asyncio.run(factory.create_resource('Patient', patient_data, request_id))

    def create_practitioner_resource(self, practitioner_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Legacy method for creating Practitioner resources"""
        factory = self.registry.get_factory('Practitioner')
        if hasattr(factory, 'create'):
            return factory.create('Practitioner', practitioner_data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('Practitioner', practitioner_data, request_id))

    def create_medication_request(self, medication_data: Dict[str, Any], patient_ref: str,
                                request_id: Optional[str] = None, practitioner_ref: Optional[str] = None,
                                encounter_ref: Optional[str] = None) -> Dict[str, Any]:
        """Legacy method for creating MedicationRequest resources"""
        data = {**medication_data, 'patient_ref': patient_ref}
        if practitioner_ref:
            data['practitioner_ref'] = practitioner_ref
        if encounter_ref:
            data['encounter_ref'] = encounter_ref

        factory = self.registry.get_factory('MedicationRequest')
        if hasattr(factory, 'create'):
            return factory.create('MedicationRequest', data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('MedicationRequest', data, request_id))

    def create_medication_administration(self, medication_data: Dict[str, Any], patient_ref: str,
                                       request_id: Optional[str] = None, practitioner_ref: Optional[str] = None,
                                       encounter_ref: Optional[str] = None) -> Dict[str, Any]:
        """Legacy method for creating MedicationAdministration resources"""
        data = {**medication_data, 'patient_ref': patient_ref}

        # Map legacy field names to new factory expected names
        if 'name' in data and 'medication_name' not in data:
            data['medication_name'] = data['name']

        # Map patient_ref to patient_id for new factories and ensure proper FHIR reference format
        if 'patient_ref' in data and 'patient_id' not in data:
            patient_ref = data['patient_ref']
            # Ensure proper FHIR reference format
            if not patient_ref.startswith('Patient/'):
                patient_ref = f'Patient/{patient_ref}'
            data['patient_id'] = patient_ref

        if practitioner_ref:
            data['practitioner_ref'] = practitioner_ref
            data['practitioner_id'] = practitioner_ref  # Also map to new expected name
        if encounter_ref:
            data['encounter_ref'] = encounter_ref
            data['encounter_id'] = encounter_ref  # Also map to new expected name

        factory = self.registry.get_factory('MedicationAdministration')
        if hasattr(factory, 'create'):
            return factory.create('MedicationAdministration', data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('MedicationAdministration', data, request_id))

    def create_device_resource(self, device_data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Legacy method for creating Device resources"""
        factory = self.registry.get_factory('Device')
        if hasattr(factory, 'create'):
            return factory.create('Device', device_data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('Device', device_data, request_id))

    def create_device_use_statement(self, patient_ref: str, device_ref: str,
                                   usage_data: Optional[Dict[str, Any]] = None,
                                   use_data: Optional[Dict[str, Any]] = None,
                                   request_id: Optional[str] = None) -> Dict[str, Any]:
        """Legacy method for creating DeviceUseStatement resources"""
        data = {'patient_ref': patient_ref, 'device_ref': device_ref}

        # Handle both legacy parameter names
        if usage_data:
            data.update(usage_data)
        if use_data:
            data.update(use_data)

        # Map patient_ref to patient_id for new factories and ensure proper FHIR reference format
        if 'patient_ref' in data and 'patient_id' not in data:
            patient_ref = data['patient_ref']
            if not patient_ref.startswith('Patient/'):
                patient_ref = f'Patient/{patient_ref}'
            data['patient_id'] = patient_ref

        factory = self.registry.get_factory('DeviceUseStatement')
        if hasattr(factory, 'create'):
            return factory.create('DeviceUseStatement', data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('DeviceUseStatement', data, request_id))

    def create_observation_resource(self, observation_data: Dict[str, Any], patient_ref: str,
                                  request_id: Optional[str] = None, encounter_ref: Optional[str] = None,
                                  practitioner_ref: Optional[str] = None) -> Dict[str, Any]:
        """Legacy method for creating Observation resources"""
        data = {**observation_data, 'patient_ref': patient_ref}
        if encounter_ref:
            data['encounter_ref'] = encounter_ref
        if practitioner_ref:
            data['practitioner_ref'] = practitioner_ref

        factory = self.registry.get_factory('Observation')
        if hasattr(factory, 'create'):
            return factory.create('Observation', data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('Observation', data, request_id))

    def create_related_person_resource(self, related_person_data: Dict[str, Any], patient_ref: str,
                                      request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create RelatedPerson resource linked to Patient.

        Args:
            related_person_data: RelatedPerson data including name, relationship, contact info
            patient_ref: Reference to Patient (e.g., "Patient/patient-123")
            request_id: Optional request identifier for tracking

        Returns:
            FHIR RelatedPerson resource dictionary

        Example:
            related_data = {
                "name": "Jane Doe",
                "relationship": "spouse",
                "gender": "female",
                "telecom": [{"system": "phone", "value": "555-1234"}]
            }
            related_person = factory.create_related_person_resource(
                related_data,
                "Patient/patient-123"
            )
        """
        # Prepare data with patient reference
        data = {**related_person_data}

        # Ensure patient reference is properly formatted
        if not patient_ref.startswith('Patient/'):
            patient_ref = f'Patient/{patient_ref}'

        data['patient_reference'] = patient_ref

        # Get RelatedPerson factory
        factory = self.registry.get_factory('RelatedPerson')
        if hasattr(factory, 'create'):
            return factory.create('RelatedPerson', data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('RelatedPerson', data, request_id))

    def create_goal_resource(self, goal_data: Dict[str, Any], patient_ref: str,
                            request_id: Optional[str] = None, careplan_ref: Optional[str] = None) -> Dict[str, Any]:
        """
        Create Goal resource for patient care planning.

        Args:
            goal_data: Goal data including description, status, priority, targets
            patient_ref: Reference to Patient (e.g., "Patient/patient-123")
            request_id: Optional request identifier for tracking
            careplan_ref: Optional CarePlan reference this goal addresses

        Returns:
            FHIR Goal resource dictionary

        Example:
            goal_data = {
                "description": "Achieve HbA1c less than 7%",
                "status": "active",
                "priority": "high",
                "category": "dietary",
                "target": {
                    "measure": "HbA1c",
                    "detail_quantity": {
                        "value": 7.0,
                        "unit": "%"
                    },
                    "due_date": "2024-12-31"
                }
            }
            goal = factory.create_goal_resource(
                goal_data,
                "Patient/patient-123",
                careplan_ref="CarePlan/careplan-456"
            )
        """
        # Prepare data with patient reference
        data = {**goal_data}

        # Extract patient ID from reference
        if patient_ref.startswith('Patient/'):
            data['patient_id'] = patient_ref.replace('Patient/', '')
        else:
            data['patient_id'] = patient_ref

        # Add CarePlan reference if provided
        if careplan_ref:
            if 'addresses' not in data:
                data['addresses'] = []
            if isinstance(data['addresses'], str):
                data['addresses'] = [data['addresses']]

            # Ensure CarePlan reference is properly formatted
            if not careplan_ref.startswith('CarePlan/'):
                careplan_ref = f'CarePlan/{careplan_ref}'

            if careplan_ref not in data['addresses']:
                data['addresses'].append(careplan_ref)

        # Get Goal factory
        factory = self.registry.get_factory('Goal')
        if hasattr(factory, 'create'):
            return factory.create('Goal', data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('Goal', data, request_id))

    def create_communication_request_resource(self, communication_request_data: Dict[str, Any], patient_ref: str,
                                             request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create CommunicationRequest resource for patient care coordination.

        Args:
            communication_request_data: Communication request data including status, intent, category, priority, payload
            patient_ref: Reference to Patient (e.g., "Patient/patient-123")
            request_id: Optional request identifier for tracking

        Returns:
            FHIR CommunicationRequest resource dictionary

        Example:
            comm_req_data = {
                "status": "active",
                "intent": "order",
                "category": "reminder",
                "priority": "routine",
                "medium": ["phone", "email"],
                "payload": ["Please call the office to schedule your follow-up appointment"],
                "recipient": ["Practitioner/practitioner-456"],
                "occurrence_datetime": "2024-12-15T10:00:00Z"
            }
            comm_req = factory.create_communication_request_resource(
                comm_req_data,
                "Patient/patient-123"
            )
        """
        # Prepare data with patient reference
        data = {**communication_request_data}

        # Extract patient ID from reference
        if patient_ref.startswith('Patient/'):
            data['patient_id'] = patient_ref.replace('Patient/', '')
        else:
            data['patient_id'] = patient_ref

        # Get CommunicationRequest factory
        factory = self.registry.get_factory('CommunicationRequest')
        if hasattr(factory, 'create'):
            return factory.create('CommunicationRequest', data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('CommunicationRequest', data, request_id))

    def create_risk_assessment_resource(self, risk_assessment_data: Dict[str, Any], patient_ref: str,
                                        request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create RiskAssessment resource for clinical risk evaluation.

        Args:
            risk_assessment_data: Risk assessment data including status, method, code, prediction, mitigation
            patient_ref: Reference to Patient (e.g., "Patient/patient-123")
            request_id: Optional request identifier for tracking

        Returns:
            FHIR RiskAssessment resource dictionary

        Example:
            risk_data = {
                "status": "final",
                "method": "SCORE2 cardiovascular risk assessment",
                "code": "Cardiovascular disease risk assessment",
                "prediction": [{
                    "outcome": "Myocardial infarction",
                    "qualitative_risk": "high",
                    "probability_decimal": 0.15,
                    "when_period": {"start": "2024-01-01", "end": "2034-01-01"}
                }],
                "mitigation": "Lifestyle modifications, statin therapy, blood pressure control",
                "basis": ["Observation/cholesterol-001", "Observation/bp-001"]
            }
            risk_assessment = factory.create_risk_assessment_resource(
                risk_data,
                "Patient/patient-123"
            )
        """
        # Prepare data with patient reference
        data = {**risk_assessment_data}

        # Extract patient ID from reference
        if patient_ref.startswith('Patient/'):
            data['patient_id'] = patient_ref.replace('Patient/', '')
        else:
            data['patient_id'] = patient_ref

        # Get RiskAssessment factory
        factory = self.registry.get_factory('RiskAssessment')
        if hasattr(factory, 'create'):
            return factory.create('RiskAssessment', data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('RiskAssessment', data, request_id))

    def create_careplan_resource(self, careplan_data: Dict[str, Any], patient_ref: str,
                                request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create CarePlan resource for patient care coordination.

        Args:
            careplan_data: CarePlan data including title, status, intent, activities
            patient_ref: Reference to Patient (e.g., "Patient/patient-123")
            request_id: Optional request identifier for tracking

        Returns:
            FHIR CarePlan resource dictionary

        Example:
            careplan_data = {
                "title": "Diabetes Management Plan",
                "status": "active",
                "intent": "plan",
                "description": "Comprehensive diabetes care"
            }
            careplan = factory.create_careplan_resource(
                careplan_data,
                "Patient/patient-123"
            )
        """
        # Prepare data with patient reference
        data = {**careplan_data}

        # Extract patient ID from reference
        if patient_ref.startswith('Patient/'):
            data['patient_id'] = patient_ref.replace('Patient/', '')
        else:
            data['patient_id'] = patient_ref

        # Get CarePlan factory
        factory = self.registry.get_factory('CarePlan')
        if hasattr(factory, 'create'):
            return factory.create('CarePlan', data, request_id)
        else:
            import asyncio
            return asyncio.run(factory.create_resource('CarePlan', data, request_id))

    def initialize(self):
        """Initialize the adapter (for legacy compatibility)"""
        if not self._initialized:
            logger.info("FactoryAdapter initialized with new factory registry")
            self._initialized = True


# Global adapter instance
_factory_adapter = None


async def get_fhir_resource_factory() -> FactoryAdapter:
    """
    Get factory adapter instance for legacy compatibility.

    This function maintains the same signature as the legacy function but
    returns an adapter that uses the new factory registry system.

    Returns:
        FactoryAdapter instance that provides legacy-compatible interface
    """
    global _factory_adapter

    if _factory_adapter is None:
        _factory_adapter = FactoryAdapter()
        _factory_adapter.initialize()

        logger.info("Using FactoryAdapter with new factory registry (legacy compatibility mode)")

    return _factory_adapter


def get_factory_adapter() -> FactoryAdapter:
    """
    Get factory adapter instance synchronously.

    Returns:
        FactoryAdapter instance
    """
    global _factory_adapter

    if _factory_adapter is None:
        _factory_adapter = FactoryAdapter()
        _factory_adapter.initialize()

    return _factory_adapter