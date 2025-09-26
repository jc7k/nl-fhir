"""
FHIR Reference Manager - REFACTOR-002
Manages FHIR resource references and relationships for resource factories
"""

from typing import Dict, Optional, Any, List, Set
import uuid
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ReferenceManager:
    """
    Manages FHIR resource references and relationships.

    Provides functionality for creating, resolving, and validating FHIR references
    while maintaining referential integrity and resource relationships.
    """

    def __init__(self):
        self._resource_cache: Dict[str, Dict[str, Any]] = {}
        self._reference_index: Dict[str, Set[str]] = {}  # resource_id -> set of references
        self._reverse_index: Dict[str, Set[str]] = {}   # reference -> set of referencing resources
        self.logger = logging.getLogger(self.__class__.__name__)
        logger.info("ReferenceManager initialized")

    def create_reference(self, resource: Dict[str, Any], include_version: bool = False) -> str:
        """
        Create FHIR reference string for resource.

        Args:
            resource: FHIR resource dictionary
            include_version: Whether to include version in reference

        Returns:
            FHIR reference string (e.g., "Patient/123")

        Raises:
            ValueError: If resource is invalid
        """
        if not isinstance(resource, dict):
            raise ValueError("Resource must be a dictionary")

        resource_type = resource.get('resourceType')
        if not resource_type:
            raise ValueError("Resource must have resourceType")

        resource_id = resource.get('id')
        if not resource_id:
            # Generate ID if not present
            resource_id = self._generate_resource_id(resource_type)
            resource['id'] = resource_id

        # Validate resource ID format
        if not self.validate_reference_format(f"{resource_type}/{resource_id}"):
            raise ValueError(f"Invalid resource ID format: {resource_id}")

        reference = f"{resource_type}/{resource_id}"

        # Add version if requested
        if include_version:
            version = resource.get('meta', {}).get('versionId', '1')
            reference = f"{reference}/_history/{version}"

        # Cache the resource for resolution
        self._cache_resource(reference, resource)

        self.logger.debug(f"Created reference: {reference}")
        return reference

    def create_reference_dict(self, resource: Dict[str, Any], display: str = None,
                            include_version: bool = False) -> Dict[str, Any]:
        """
        Create FHIR Reference structure.

        Args:
            resource: FHIR resource dictionary
            display: Human-readable display text
            include_version: Whether to include version in reference

        Returns:
            FHIR Reference dictionary
        """
        reference = self.create_reference(resource, include_version)

        ref_dict = {'reference': reference}

        if display:
            ref_dict['display'] = display
        else:
            # Auto-generate display from resource
            auto_display = self._generate_display_text(resource)
            if auto_display:
                ref_dict['display'] = auto_display

        return ref_dict

    def resolve_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        """
        Resolve FHIR reference to actual resource.

        Args:
            reference: FHIR reference string

        Returns:
            Resource dictionary if found, None otherwise
        """
        # Clean up reference (remove version if present)
        clean_ref = self._clean_reference(reference)

        resource = self._resource_cache.get(clean_ref)
        if resource:
            self.logger.debug(f"Resolved reference: {reference}")
        else:
            self.logger.debug(f"Reference not found: {reference}")

        return resource

    def validate_reference_format(self, reference: str) -> bool:
        """
        Validate FHIR reference format.

        Args:
            reference: Reference string to validate

        Returns:
            True if format is valid
        """
        if not isinstance(reference, str) or not reference:
            return False

        # FHIR reference patterns
        patterns = [
            r'^[A-Za-z][A-Za-z0-9]*\/[A-Za-z0-9\-\.]{1,64}$',  # ResourceType/id
            r'^[A-Za-z][A-Za-z0-9]*\/[A-Za-z0-9\-\.]{1,64}\/_history\/[A-Za-z0-9\-\.]{1,64}$',  # With version
            r'^https?:\/\/.+\/[A-Za-z][A-Za-z0-9]*\/[A-Za-z0-9\-\.]{1,64}$',  # Absolute URL
        ]

        return any(re.match(pattern, reference) for pattern in patterns)

    def add_reference_relationship(self, source_resource: Dict[str, Any],
                                 target_reference: str, relationship_type: str = None):
        """
        Add a reference relationship between resources.

        Args:
            source_resource: Resource that contains the reference
            target_reference: Reference to target resource
            relationship_type: Type of relationship (optional)
        """
        source_ref = self.create_reference(source_resource)

        # Add to reference index
        if source_ref not in self._reference_index:
            self._reference_index[source_ref] = set()
        self._reference_index[source_ref].add(target_reference)

        # Add to reverse index
        if target_reference not in self._reverse_index:
            self._reverse_index[target_reference] = set()
        self._reverse_index[target_reference].add(source_ref)

        self.logger.debug(f"Added relationship: {source_ref} -> {target_reference}")

    def get_references_from(self, resource: Dict[str, Any]) -> List[str]:
        """
        Get all references from a resource.

        Args:
            resource: Source resource

        Returns:
            List of reference strings
        """
        source_ref = self.create_reference(resource)
        return list(self._reference_index.get(source_ref, set()))

    def get_references_to(self, resource: Dict[str, Any]) -> List[str]:
        """
        Get all references to a resource.

        Args:
            resource: Target resource

        Returns:
            List of reference strings that point to this resource
        """
        target_ref = self.create_reference(resource)
        return list(self._reverse_index.get(target_ref, set()))

    def validate_reference_integrity(self) -> List[str]:
        """
        Validate referential integrity across cached resources.

        Returns:
            List of broken reference errors
        """
        errors = []

        for source_ref, target_refs in self._reference_index.items():
            for target_ref in target_refs:
                clean_target = self._clean_reference(target_ref)
                if clean_target not in self._resource_cache:
                    errors.append(f"Broken reference: {source_ref} -> {target_ref}")

        return errors

    def _generate_resource_id(self, resource_type: str) -> str:
        """
        Generate unique resource ID.

        Args:
            resource_type: FHIR resource type

        Returns:
            Unique resource identifier
        """
        return f"{resource_type}-{uuid.uuid4()}"

    def _cache_resource(self, reference: str, resource: Dict[str, Any]):
        """Cache resource for reference resolution"""
        clean_ref = self._clean_reference(reference)
        self._resource_cache[clean_ref] = resource.copy()

        # Add creation timestamp to metadata
        if 'meta' not in resource:
            resource['meta'] = {}
        if 'cached_at' not in resource['meta']:
            resource['meta']['cached_at'] = datetime.now().isoformat()

    def _clean_reference(self, reference: str) -> str:
        """Remove version and URL parts from reference"""
        # Remove version if present
        if '/_history/' in reference:
            reference = reference.split('/_history/')[0]

        # Remove URL prefix if present, keep only ResourceType/id
        if '://' in reference:
            parts = reference.split('/')
            if len(parts) >= 2:
                reference = '/'.join(parts[-2:])

        return reference

    def _generate_display_text(self, resource: Dict[str, Any]) -> Optional[str]:
        """
        Generate human-readable display text for resource.

        Args:
            resource: FHIR resource

        Returns:
            Display text or None
        """
        resource_type = resource.get('resourceType')

        if resource_type == 'Patient':
            return self._get_patient_display(resource)
        elif resource_type == 'Practitioner':
            return self._get_practitioner_display(resource)
        elif resource_type == 'Medication':
            return self._get_medication_display(resource)
        elif resource_type == 'Condition':
            return self._get_condition_display(resource)
        elif resource_type == 'Observation':
            return self._get_observation_display(resource)

        # Default: use resource type and ID
        resource_id = resource.get('id', 'unknown')
        return f"{resource_type}/{resource_id}"

    def _get_patient_display(self, patient: Dict[str, Any]) -> Optional[str]:
        """Generate display text for Patient resource"""
        names = patient.get('name', [])
        if names and isinstance(names, list) and len(names) > 0:
            name = names[0]
            family = name.get('family', '')
            given = name.get('given', [])
            if given and isinstance(given, list):
                given_str = ' '.join(given)
                return f"{given_str} {family}".strip()
            return family
        return None

    def _get_practitioner_display(self, practitioner: Dict[str, Any]) -> Optional[str]:
        """Generate display text for Practitioner resource"""
        return self._get_patient_display(practitioner)  # Same logic

    def _get_medication_display(self, medication: Dict[str, Any]) -> Optional[str]:
        """Generate display text for Medication resource"""
        code = medication.get('code', {})
        codings = code.get('coding', [])
        if codings and isinstance(codings, list) and len(codings) > 0:
            return codings[0].get('display') or codings[0].get('code')
        return code.get('text')

    def _get_condition_display(self, condition: Dict[str, Any]) -> Optional[str]:
        """Generate display text for Condition resource"""
        code = condition.get('code', {})
        codings = code.get('coding', [])
        if codings and isinstance(codings, list) and len(codings) > 0:
            return codings[0].get('display') or codings[0].get('code')
        return code.get('text')

    def _get_observation_display(self, observation: Dict[str, Any]) -> Optional[str]:
        """Generate display text for Observation resource"""
        code = observation.get('code', {})
        codings = code.get('coding', [])
        if codings and isinstance(codings, list) and len(codings) > 0:
            return codings[0].get('display') or codings[0].get('code')
        return code.get('text')

    def clear_cache(self):
        """Clear all cached resources and relationships"""
        self._resource_cache.clear()
        self._reference_index.clear()
        self._reverse_index.clear()
        logger.debug("Reference cache cleared")

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache usage statistics"""
        return {
            'cached_resources': len(self._resource_cache),
            'reference_relationships': sum(len(refs) for refs in self._reference_index.values()),
            'reverse_relationships': sum(len(refs) for refs in self._reverse_index.values()),
            'memory_usage_kb': self._estimate_memory_usage()
        }

    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in KB (rough approximation)"""
        import sys
        total_size = 0

        # Estimate resource cache size
        for resource in self._resource_cache.values():
            total_size += sys.getsizeof(str(resource))

        # Estimate index sizes
        for ref_set in self._reference_index.values():
            total_size += sys.getsizeof(ref_set)
        for ref_set in self._reverse_index.values():
            total_size += sys.getsizeof(ref_set)

        return total_size / 1024  # Convert to KB