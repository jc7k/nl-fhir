"""
Base Factory Pattern for FHIR Resource Creation
REFACTOR-001: Foundation for modular factory architecture
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseResourceFactory(ABC):
    """
    Abstract base class for all FHIR resource factories.

    This class defines the interface that all specialized resource factories
    must implement, ensuring consistency across the factory system.
    """

    def __init__(self, validators=None, coders=None, reference_manager=None):
        """
        Initialize base factory with common dependencies.

        Args:
            validators: Validation utilities
            coders: Medical coding utilities (RxNorm, LOINC, etc.)
            reference_manager: FHIR reference management utilities
        """
        self.validators = validators
        self.coders = coders
        self.reference_manager = reference_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def create(self, resource_type: str, data: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create FHIR resource from extracted data.

        Args:
            resource_type: FHIR resource type (e.g., 'Patient', 'MedicationRequest')
            data: Structured data extracted from NLP processing
            request_id: Optional request identifier for audit logging

        Returns:
            FHIR resource as dictionary

        Raises:
            ValueError: If resource_type is not supported
            ValidationError: If data is invalid
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

    def _log_resource_creation(self, resource_type: str, request_id: Optional[str] = None):
        """
        Log resource creation for audit purposes.

        Args:
            resource_type: FHIR resource type created
            request_id: Optional request identifier
        """
        if request_id:
            self.logger.info(f"Created {resource_type} resource for request {request_id}")
        else:
            self.logger.info(f"Created {resource_type} resource")