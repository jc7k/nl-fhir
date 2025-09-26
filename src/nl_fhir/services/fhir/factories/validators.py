"""
FHIR Validation Registry - REFACTOR-002
Provides comprehensive FHIR R4 validation functionality for resource factories
"""

from typing import Dict, List, Any, Optional
from functools import lru_cache
import re
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class ValidatorRegistry:
    """
    Registry for FHIR validation rules and checks.

    Provides both structural validation (FHIR specification compliance)
    and semantic validation (medical domain rules).
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._validators = {}
        self._validation_errors = []
        self._validation_cache = {}  # Manual cache for dict hashing
        self._register_standard_validators()
        logger.info("ValidatorRegistry initialized with standard FHIR R4 validators")

    def _register_standard_validators(self):
        """Register standard FHIR R4 validators"""
        self._validators.update({
            'required_fields': self._validate_required_fields,
            'identifier_format': self._validate_identifiers,
            'reference_format': self._validate_references,
            'coding_format': self._validate_codings,
            'date_format': self._validate_dates,
            'resource_type': self._validate_resource_type,
            'id_format': self._validate_id_format,
        })

    def validate_fhir_r4(self, resource_dict: Dict[str, Any]) -> bool:
        """
        Validate resource against FHIR R4 specification.

        Args:
            resource_dict: Resource as dictionary

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(resource_dict, dict):
            self._validation_errors = ["Resource must be a dictionary"]
            return False

        # Create cache key from resource content
        try:
            cache_key = json.dumps(resource_dict, sort_keys=True)
            if cache_key in self._validation_cache:
                cached_result, cached_errors = self._validation_cache[cache_key]
                self._validation_errors = cached_errors.copy()
                return cached_result
        except (TypeError, ValueError):
            # If JSON serialization fails, proceed without caching
            cache_key = None

        self._validation_errors.clear()

        try:
            # Run all registered validators
            for validator_name, validator_func in self._validators.items():
                try:
                    if not validator_func(resource_dict):
                        self._validation_errors.append(f"Failed {validator_name} validation")
                        logger.debug(f"Validation failed: {validator_name}")
                except Exception as e:
                    self._validation_errors.append(f"{validator_name}: {str(e)}")
                    logger.error(f"Validator {validator_name} raised exception: {e}")

            result = len(self._validation_errors) == 0

            # Cache the result if we have a valid cache key
            if cache_key is not None:
                self._validation_cache[cache_key] = (result, self._validation_errors.copy())

            return result

        except Exception as e:
            self._validation_errors.append(f"Validation error: {str(e)}")
            logger.error(f"Validation process failed: {e}")
            return False

    def get_validation_errors(self) -> List[str]:
        """
        Get detailed validation error messages from last validation.

        Returns:
            List of error messages
        """
        return self._validation_errors.copy()

    def _validate_required_fields(self, resource_dict: Dict[str, Any]) -> bool:
        """Validate required fields are present for resource type"""
        required_fields = {
            'Patient': ['resourceType'],
            'MedicationRequest': ['resourceType', 'subject', 'medicationCodeableConcept'],
            'MedicationAdministration': ['resourceType', 'subject', 'medicationCodeableConcept', 'status'],
            'Observation': ['resourceType', 'subject', 'code', 'status'],
            'Device': ['resourceType'],
            'DeviceUseStatement': ['resourceType', 'subject', 'device'],
            'ServiceRequest': ['resourceType', 'subject', 'code', 'status'],
            'Condition': ['resourceType', 'subject', 'code'],
            'Encounter': ['resourceType', 'subject', 'status', 'class'],
            'DiagnosticReport': ['resourceType', 'subject', 'code', 'status'],
            'AllergyIntolerance': ['resourceType', 'patient', 'code'],
            'Medication': ['resourceType'],
            'CarePlan': ['resourceType', 'subject', 'status'],
            'Immunization': ['resourceType', 'patient', 'vaccineCode', 'status'],
            'Location': ['resourceType'],
        }

        resource_type = resource_dict.get('resourceType')
        if resource_type not in required_fields:
            return True  # No specific requirements for unknown types

        for field in required_fields[resource_type]:
            # Check nested fields (e.g., 'subject.reference')
            if '.' in field:
                if not self._check_nested_field(resource_dict, field):
                    return False
            else:
                if field not in resource_dict or resource_dict[field] is None:
                    return False

        return True

    def _check_nested_field(self, resource_dict: Dict[str, Any], field_path: str) -> bool:
        """Check nested field existence (e.g., 'subject.reference')"""
        parts = field_path.split('.')
        current = resource_dict

        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]

        return current is not None

    def _validate_identifiers(self, resource_dict: Dict[str, Any]) -> bool:
        """Validate identifier format"""
        identifiers = resource_dict.get('identifier', [])
        if not identifiers:
            return True  # No identifiers to validate

        for identifier in identifiers:
            if not isinstance(identifier, dict):
                return False

            # Must have either value or system+value
            value = identifier.get('value')
            system = identifier.get('system')

            if not value or len(str(value).strip()) == 0:
                return False

            # If system provided, should be valid URI
            if system and not self._is_valid_uri(system):
                return False

        return True

    def _validate_references(self, resource_dict: Dict[str, Any]) -> bool:
        """Validate FHIR reference format throughout resource"""
        reference_pattern = re.compile(r'^[A-Za-z][A-Za-z0-9]*\/[A-Za-z0-9\-\.]{1,64}$')

        return self._validate_references_recursive(resource_dict, reference_pattern)

    def _validate_references_recursive(self, obj: Any, pattern: re.Pattern) -> bool:
        """Recursively validate references in nested structures"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == 'reference' and isinstance(value, str):
                    if not pattern.match(value):
                        return False
                elif not self._validate_references_recursive(value, pattern):
                    return False
        elif isinstance(obj, list):
            for item in obj:
                if not self._validate_references_recursive(item, pattern):
                    return False

        return True

    def _validate_codings(self, resource_dict: Dict[str, Any]) -> bool:
        """Validate coding system format"""
        return self._validate_codings_recursive(resource_dict)

    def _validate_codings_recursive(self, obj: Any) -> bool:
        """Recursively validate codings in nested structures"""
        if isinstance(obj, dict):
            # Check if this is a Coding object
            if 'system' in obj and 'code' in obj:
                system = obj.get('system')
                code = obj.get('code')

                if not system or not code:
                    return False

                if not self._is_valid_uri(system):
                    return False

                if not isinstance(code, str) or len(code.strip()) == 0:
                    return False

            # Recursively check all values
            for value in obj.values():
                if not self._validate_codings_recursive(value):
                    return False

        elif isinstance(obj, list):
            for item in obj:
                if not self._validate_codings_recursive(item):
                    return False

        return True

    def _validate_dates(self, resource_dict: Dict[str, Any]) -> bool:
        """Validate date format (FHIR date/dateTime)"""
        return self._validate_dates_recursive(resource_dict)

    def _validate_dates_recursive(self, obj: Any) -> bool:
        """Recursively validate dates in nested structures"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Check for date/dateTime fields
                if key in ['date', 'dateTime', 'effectiveDateTime', 'authoredOn', 'created'] and value:
                    if not self._is_valid_fhir_date(value):
                        return False
                elif not self._validate_dates_recursive(value):
                    return False
        elif isinstance(obj, list):
            for item in obj:
                if not self._validate_dates_recursive(item):
                    return False

        return True

    def _validate_resource_type(self, resource_dict: Dict[str, Any]) -> bool:
        """Validate resourceType field"""
        resource_type = resource_dict.get('resourceType')

        if not resource_type:
            return False

        if not isinstance(resource_type, str):
            return False

        # Must be valid FHIR resource type (starts with capital letter)
        if not re.match(r'^[A-Z][A-Za-z0-9]*$', resource_type):
            return False

        return True

    def _validate_id_format(self, resource_dict: Dict[str, Any]) -> bool:
        """Validate resource ID format"""
        resource_id = resource_dict.get('id')

        if resource_id is None:
            return True  # ID is optional

        if not isinstance(resource_id, str):
            return False

        # FHIR ID format: [A-Za-z0-9\-\.]{1,64}
        if not re.match(r'^[A-Za-z0-9\-\.]{1,64}$', resource_id):
            return False

        return True

    def _is_valid_uri(self, uri: str) -> bool:
        """Validate URI format"""
        if not isinstance(uri, str) or len(uri) == 0:
            return False

        # Basic URI validation
        uri_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return bool(uri_pattern.match(uri))

    def _is_valid_fhir_date(self, date_str: str) -> bool:
        """Validate FHIR date/dateTime format"""
        if not isinstance(date_str, str):
            return False

        # FHIR date patterns
        patterns = [
            r'^\d{4}$',  # YYYY
            r'^\d{4}-\d{2}$',  # YYYY-MM
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$',  # full dateTime
        ]

        return any(re.match(pattern, date_str) for pattern in patterns)

    def register_custom_validator(self, name: str, validator_func):
        """
        Register a custom validator function.

        Args:
            name: Validator name
            validator_func: Function that takes resource_dict and returns bool
        """
        self._validators[name] = validator_func
        logger.info(f"Registered custom validator: {name}")

    def get_validator_names(self) -> List[str]:
        """Get list of all registered validator names"""
        return list(self._validators.keys())

    def clear_cache(self):
        """Clear validation cache"""
        self._validation_cache.clear()
        logger.debug("Validation cache cleared")