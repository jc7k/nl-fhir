"""
Base Factory Pattern for FHIR Resource Creation
REFACTOR-002: Enhanced with template method pattern and shared components
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
import logging
import time
from datetime import datetime

if TYPE_CHECKING:
    from .validators import ValidatorRegistry
    from .coders import CoderRegistry
    from .references import ReferenceManager

logger = logging.getLogger(__name__)


class BaseResourceFactory(ABC):
    """
    Abstract base class for all FHIR resource factories.

    Implements the template method pattern for consistent resource creation workflow
    with shared validation, coding, and reference management capabilities.
    """

    def __init__(self,
                 validators: 'ValidatorRegistry',
                 coders: 'CoderRegistry',
                 reference_manager: 'ReferenceManager'):
        """
        Initialize base factory with shared components.

        Args:
            validators: FHIR validation registry
            coders: Medical coding registry
            reference_manager: FHIR reference management
        """
        self.validators = validators
        self.coders = coders
        self.reference_manager = reference_manager
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._metrics = {
            'created': 0,
            'validated': 0,
            'failed': 0,
            'total_time_ms': 0.0,
            'avg_time_ms': 0.0
        }

    def create(self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Template method for FHIR resource creation workflow.

        This method defines the standard workflow that all factories follow:
        1. Input validation
        2. Resource creation (implemented by subclasses)
        3. FHIR validation
        4. Metadata addition
        5. Performance tracking

        Args:
            resource_type: FHIR resource type
            data: Input data for resource creation
            request_id: Optional request identifier

        Returns:
            Valid FHIR resource dictionary

        Raises:
            ValueError: If input data or resource type is invalid
            ValidationError: If created resource fails FHIR validation
        """
        start_time = time.time()

        try:
            # 1. Pre-creation validation
            self._validate_input_data(resource_type, data)

            # 2. Create resource (implemented by subclasses)
            resource = self._create_resource(resource_type, data, request_id)

            # 3. Post-creation FHIR validation
            self._validate_fhir_resource(resource)

            # 4. Add metadata and references
            self._add_metadata(resource, request_id)

            # 5. Update metrics and logging
            duration_ms = (time.time() - start_time) * 1000
            self._update_metrics(duration_ms, success=True)
            self._log_resource_creation(resource_type, request_id, duration_ms)

            return resource

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._update_metrics(duration_ms, success=False)
            self.logger.error(f"Failed to create {resource_type} for request {request_id}: {str(e)}")
            raise

    @abstractmethod
    def _create_resource(self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create the specific FHIR resource - implemented by subclasses.

        Args:
            resource_type: FHIR resource type
            data: Input data
            request_id: Optional request identifier

        Returns:
            FHIR resource dictionary
        """
        pass

    @abstractmethod
    def supports(self, resource_type: str) -> bool:
        """
        Check if factory supports the given resource type.

        Args:
            resource_type: FHIR resource type to check

        Returns:
            True if factory can create this resource type
        """
        pass

    def _validate_input_data(self, resource_type: str, data: Dict[str, Any]):
        """
        Validate input data before resource creation.

        Args:
            resource_type: FHIR resource type
            data: Input data to validate

        Raises:
            ValueError: If input data is invalid
        """
        if not data:
            raise ValueError("Input data cannot be empty")

        if not resource_type:
            raise ValueError("resource_type is required")

        if not self.supports(resource_type):
            raise ValueError(f"Factory does not support resource type: {resource_type}")

        # Validate required fields based on resource type
        required_fields = self._get_required_fields(resource_type)
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Required field '{field}' is missing for {resource_type}")

    def _validate_fhir_resource(self, resource: Dict[str, Any]):
        """
        Validate created resource against FHIR R4 specification.

        Args:
            resource: FHIR resource to validate

        Raises:
            ValueError: If FHIR validation fails
        """
        if not self.validators:
            self.logger.warning("No validators available, skipping FHIR validation")
            return

        is_valid = self.validators.validate_fhir_r4(resource)

        if not is_valid:
            validation_errors = self.validators.get_validation_errors()
            error_msg = f"FHIR validation failed: {', '.join(validation_errors)}"
            raise ValueError(error_msg)

        self._metrics['validated'] += 1

    def _add_metadata(self, resource: Dict[str, Any], request_id: Optional[str] = None):
        """
        Add metadata to track factory usage and provenance.

        Args:
            resource: FHIR resource to enhance
            request_id: Optional request identifier
        """
        if 'meta' not in resource:
            resource['meta'] = {}

        # Add factory metadata
        resource['meta'].update({
            'factory': self.__class__.__name__,
            'created_at': datetime.now().isoformat(),
            'version': '1.0.0'
        })

        if request_id:
            resource['meta']['request_id'] = request_id

        # Ensure resource has an ID
        if 'id' not in resource or not resource['id']:
            resource['id'] = self._generate_resource_id(resource.get('resourceType', 'Unknown'))

    def _get_required_fields(self, resource_type: str) -> list[str]:
        """
        Get list of required fields for resource type.

        Args:
            resource_type: FHIR resource type

        Returns:
            List of required field names
        """
        # Basic required fields by resource type
        required_fields_map = {
            'Patient': [],
            'MedicationRequest': ['subject', 'medication'],
            'MedicationAdministration': ['subject', 'medication', 'status'],
            'Observation': ['subject', 'code', 'status'],
            'Device': [],
            'DeviceUseStatement': ['subject', 'device'],
            'ServiceRequest': ['subject', 'code', 'status'],
            'Condition': ['subject', 'code'],
            'Encounter': ['subject', 'status', 'class'],
            'DiagnosticReport': ['subject', 'code', 'status'],
            'AllergyIntolerance': ['patient', 'code'],
            'Medication': [],
            'CarePlan': ['subject', 'status'],
            'Immunization': ['patient', 'vaccineCode', 'status'],
            'Location': [],
        }

        return required_fields_map.get(resource_type, [])

    def _update_metrics(self, duration_ms: float, success: bool):
        """
        Update factory performance metrics.

        Args:
            duration_ms: Operation duration in milliseconds
            success: Whether operation was successful
        """
        if success:
            self._metrics['created'] += 1
        else:
            self._metrics['failed'] += 1

        self._metrics['total_time_ms'] += duration_ms

        total_operations = self._metrics['created'] + self._metrics['failed']
        if total_operations > 0:
            self._metrics['avg_time_ms'] = self._metrics['total_time_ms'] / total_operations

    def get_supported_resources(self) -> list[str]:
        """
        Get list of all resource types this factory supports.

        Returns:
            List of supported FHIR resource types
        """
        # Default implementation - subclasses should override for efficiency
        common_resources = [
            'Patient', 'Practitioner', 'MedicationRequest', 'MedicationAdministration',
            'Device', 'DeviceUseStatement', 'ServiceRequest', 'Condition',
            'Encounter', 'Observation', 'DiagnosticReport', 'AllergyIntolerance',
            'Medication', 'CarePlan', 'Immunization', 'Location'
        ]
        return [resource for resource in common_resources if self.supports(resource)]

    def add_coding(self, system: str, code: str, display: str = None) -> Dict[str, Any]:
        """
        Add standardized coding using the coder registry.

        Args:
            system: Coding system name or URI
            code: Code value
            display: Display text

        Returns:
            FHIR Coding dictionary
        """
        if not self.coders:
            raise ValueError("No coders available")

        return self.coders.add_coding(system, code, display)

    def create_codeable_concept(self, system: str, code: str, display: str = None, text: str = None) -> Dict[str, Any]:
        """
        Create FHIR CodeableConcept using the coder registry.

        Args:
            system: Coding system name or URI
            code: Code value
            display: Display text
            text: Additional text

        Returns:
            FHIR CodeableConcept dictionary
        """
        if not self.coders:
            raise ValueError("No coders available")

        return self.coders.create_codeable_concept(system, code, display, text)

    def create_reference(self, resource: Dict[str, Any], display: str = None) -> Dict[str, Any]:
        """
        Create FHIR reference using the reference manager.

        Args:
            resource: FHIR resource to reference
            display: Optional display text

        Returns:
            FHIR Reference dictionary
        """
        if not self.reference_manager:
            raise ValueError("No reference manager available")

        return self.reference_manager.create_reference_dict(resource, display)

    def resolve_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        """
        Resolve FHIR reference to actual resource.

        Args:
            reference: FHIR reference string

        Returns:
            Resource dictionary if found, None otherwise
        """
        if not self.reference_manager:
            return None

        return self.reference_manager.resolve_reference(reference)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get factory performance metrics.

        Returns:
            Dictionary with performance metrics
        """
        return self._metrics.copy()

    def _generate_resource_id(self, resource_type: str) -> str:
        """
        Generate unique resource ID.

        Args:
            resource_type: FHIR resource type

        Returns:
            Unique resource identifier
        """
        from uuid import uuid4
        return f"{resource_type}-{uuid4()}"

    def _log_resource_creation(self, resource_type: str, request_id: Optional[str] = None, duration_ms: float = 0.0):
        """
        Log resource creation for audit purposes.

        Args:
            resource_type: FHIR resource type created
            request_id: Optional request identifier
            duration_ms: Creation duration in milliseconds
        """
        if request_id:
            self.logger.info(f"Created {resource_type} resource for request {request_id} in {duration_ms:.2f}ms")
        else:
            self.logger.info(f"Created {resource_type} resource in {duration_ms:.2f}ms")