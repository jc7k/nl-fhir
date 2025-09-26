"""
Medical Coding Registry - REFACTOR-002
Provides standardized medical coding functionality for FHIR resources
"""

from typing import Dict, Optional, List, Any
from functools import lru_cache
import logging
import re

logger = logging.getLogger(__name__)


class CoderRegistry:
    """
    Registry for medical coding systems and standardized coding operations.

    Supports major medical coding systems including LOINC, SNOMED CT, RxNorm,
    ICD-10, CPT, and custom coding systems.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._coding_systems = self._initialize_coding_systems()
        self._cached_codes = {}
        logger.info("CoderRegistry initialized with standard medical coding systems")

    def _initialize_coding_systems(self) -> Dict[str, str]:
        """Initialize standard medical coding system URIs"""
        return {
            # Laboratory and clinical observations
            'LOINC': 'http://loinc.org',

            # Clinical terminology
            'SNOMED': 'http://snomed.info/sct',
            'SNOMED-CT': 'http://snomed.info/sct',

            # Medications
            'RXNORM': 'http://www.nlm.nih.gov/research/umls/rxnorm',
            'NDC': 'http://hl7.org/fhir/sid/ndc',

            # Diagnosis and procedures
            'ICD10': 'http://hl7.org/fhir/sid/icd-10',
            'ICD10CM': 'http://hl7.org/fhir/sid/icd-10-cm',
            'ICD10PCS': 'http://hl7.org/fhir/sid/icd-10-pcs',
            'CPT': 'http://www.ama-assn.org/go/cpt',

            # Units and measurements
            'UCUM': 'http://unitsofmeasure.org',

            # Healthcare providers and organizations
            'NPI': 'http://hl7.org/fhir/sid/us-npi',

            # Other important systems
            'CVX': 'http://hl7.org/fhir/sid/cvx',  # Vaccine codes
            'HL7': 'http://terminology.hl7.org/CodeSystem/',
        }

    @lru_cache(maxsize=256)
    def get_system_uri(self, system_name: str) -> Optional[str]:
        """
        Get URI for coding system.

        Args:
            system_name: Name of the coding system (case-insensitive)

        Returns:
            System URI if found, None otherwise
        """
        return self._coding_systems.get(system_name.upper())

    def add_coding(self, system: str, code: str, display: str = None) -> Dict[str, Any]:
        """
        Create a FHIR Coding object.

        Args:
            system: Coding system name or URI
            code: Code value
            display: Human-readable display name

        Returns:
            FHIR Coding dictionary

        Raises:
            ValueError: If system is unknown or code is invalid
        """
        # Convert system name to URI if needed
        if not system.startswith('http'):
            system_uri = self.get_system_uri(system)
            if not system_uri:
                raise ValueError(f"Unknown coding system: {system}")
            system = system_uri

        # Validate code format for known systems
        if not self.validate_code(system, code):
            raise ValueError(f"Invalid code format for {system}: {code}")

        coding = {
            'system': system,
            'code': code
        }

        if display:
            coding['display'] = display

        # Cache the coding for future lookups
        cache_key = f"{system}|{code}"
        self._cached_codes[cache_key] = coding

        self.logger.debug(f"Created coding: {system} {code}")
        return coding

    def create_codeable_concept(self, system: str, code: str, display: str = None, text: str = None) -> Dict[str, Any]:
        """
        Create a FHIR CodeableConcept object.

        Args:
            system: Coding system name or URI
            code: Code value
            display: Human-readable display name
            text: Additional descriptive text

        Returns:
            FHIR CodeableConcept dictionary
        """
        coding = self.add_coding(system, code, display)

        codeable_concept = {
            'coding': [coding]
        }

        if text:
            codeable_concept['text'] = text
        elif display:
            codeable_concept['text'] = display

        return codeable_concept

    def create_multiple_codings(self, codings: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Create CodeableConcept with multiple coding systems.

        Args:
            codings: List of coding dictionaries with 'system', 'code', 'display'

        Returns:
            FHIR CodeableConcept with multiple codings
        """
        coding_objects = []

        for coding_info in codings:
            system = coding_info.get('system')
            code = coding_info.get('code')
            display = coding_info.get('display')

            if not system or not code:
                raise ValueError("Each coding must have 'system' and 'code'")

            coding_objects.append(self.add_coding(system, code, display))

        return {
            'coding': coding_objects,
            'text': codings[0].get('display', codings[0].get('code'))
        }

    @lru_cache(maxsize=128)
    def validate_code(self, system: str, code: str) -> bool:
        """
        Validate code format for specific coding system.

        Args:
            system: Coding system URI
            code: Code to validate

        Returns:
            True if code format is valid
        """
        if not code or len(str(code).strip()) == 0:
            return False

        # System-specific validation rules
        if 'loinc.org' in system.lower():
            return self._validate_loinc_code(code)
        elif 'snomed.info' in system.lower():
            return self._validate_snomed_code(code)
        elif 'rxnorm' in system.lower():
            return self._validate_rxnorm_code(code)
        elif 'icd-10' in system.lower():
            return self._validate_icd10_code(code)
        elif 'cpt' in system.lower():
            return self._validate_cpt_code(code)
        elif 'cvx' in system.lower():
            return self._validate_cvx_code(code)
        elif 'ndc' in system.lower():
            return self._validate_ndc_code(code)

        # Default validation for unknown systems
        return self._validate_generic_code(code)

    def _validate_loinc_code(self, code: str) -> bool:
        """Validate LOINC code format (NNNNN-N)"""
        return bool(re.match(r'^\d{5}-\d$', str(code)))

    def _validate_snomed_code(self, code: str) -> bool:
        """Validate SNOMED CT code format (numeric, 6+ digits)"""
        return str(code).isdigit() and len(str(code)) >= 6

    def _validate_rxnorm_code(self, code: str) -> bool:
        """Validate RxNorm code format (numeric)"""
        return str(code).isdigit() and len(str(code)) >= 1

    def _validate_icd10_code(self, code: str) -> bool:
        """Validate ICD-10 code format (letter + numbers + optional decimal)"""
        # ICD-10 format: A00-Z99 with optional decimal extensions
        return bool(re.match(r'^[A-Z]\d{2}(\.\d{1,4})?$', str(code).upper()))

    def _validate_cpt_code(self, code: str) -> bool:
        """Validate CPT code format (5 digits)"""
        return bool(re.match(r'^\d{5}$', str(code)))

    def _validate_cvx_code(self, code: str) -> bool:
        """Validate CVX vaccine code format (numeric)"""
        return str(code).isdigit() and 1 <= len(str(code)) <= 3

    def _validate_ndc_code(self, code: str) -> bool:
        """Validate NDC code format (various formats)"""
        # NDC can be in formats: NNNNN-NNNN-NN, NNNNN-NNN-NN, etc.
        code_str = str(code).replace('-', '')
        return code_str.isdigit() and len(code_str) in [10, 11]

    def _validate_generic_code(self, code: str) -> bool:
        """Generic code validation (alphanumeric)"""
        return bool(re.match(r'^[A-Za-z0-9\-\.\_]+$', str(code)))

    def get_display_name(self, system: str, code: str) -> Optional[str]:
        """
        Get cached display name for a code.

        Args:
            system: Coding system name or URI
            code: Code value

        Returns:
            Display name if cached, None otherwise
        """
        if not system.startswith('http'):
            system_uri = self.get_system_uri(system)
            if system_uri:
                system = system_uri

        cache_key = f"{system}|{code}"
        cached_coding = self._cached_codes.get(cache_key)

        return cached_coding.get('display') if cached_coding else None

    def create_quantity(self, value: float, unit: str, system: str = 'UCUM') -> Dict[str, Any]:
        """
        Create FHIR Quantity object with standardized units.

        Args:
            value: Numeric value
            unit: Unit of measurement
            system: Unit system (default: UCUM)

        Returns:
            FHIR Quantity dictionary
        """
        system_uri = self.get_system_uri(system)
        if not system_uri:
            system_uri = system  # Use as-is if not in registry

        return {
            'value': value,
            'unit': unit,
            'system': system_uri,
            'code': unit
        }

    def register_custom_system(self, name: str, uri: str):
        """
        Register a custom coding system.

        Args:
            name: System name (will be converted to uppercase)
            uri: System URI
        """
        self._coding_systems[name.upper()] = uri
        logger.info(f"Registered custom coding system: {name} -> {uri}")

    def get_supported_systems(self) -> List[str]:
        """Get list of all supported coding system names"""
        return list(self._coding_systems.keys())

    def clear_cache(self):
        """Clear coding caches"""
        self.get_system_uri.cache_clear()
        self.validate_code.cache_clear()
        self._cached_codes.clear()
        logger.debug("Coding cache cleared")

    def get_statistics(self) -> Dict[str, Any]:
        """Get registry usage statistics"""
        return {
            'supported_systems': len(self._coding_systems),
            'cached_codes': len(self._cached_codes),
            'cache_hits': self.get_system_uri.cache_info().hits + self.validate_code.cache_info().hits,
            'cache_misses': self.get_system_uri.cache_info().misses + self.validate_code.cache_info().misses,
        }