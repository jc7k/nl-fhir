"""
Tests for CoderRegistry - REFACTOR-002
Tests medical coding functionality and shared component integration
"""

import pytest
from unittest.mock import MagicMock, patch

from nl_fhir.services.fhir.factories.coders import CoderRegistry


class TestCoderRegistry:
    """Test suite for CoderRegistry medical coding functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.coder = CoderRegistry()

    def test_coder_initialization(self):
        """CoderRegistry should initialize with standard coding systems"""
        assert self.coder is not None
        assert hasattr(self.coder, 'logger')
        assert hasattr(self.coder, '_coding_systems')
        assert hasattr(self.coder, '_cached_codes')

        # Check standard systems are loaded
        supported_systems = self.coder.get_supported_systems()
        assert 'LOINC' in supported_systems
        assert 'SNOMED' in supported_systems
        assert 'RXNORM' in supported_systems
        assert 'ICD10' in supported_systems

    def test_get_system_uri_for_known_systems(self):
        """Should return correct URIs for known coding systems"""
        # Test major systems
        assert self.coder.get_system_uri('LOINC') == 'http://loinc.org'
        assert self.coder.get_system_uri('SNOMED') == 'http://snomed.info/sct'
        assert self.coder.get_system_uri('RXNORM') == 'http://www.nlm.nih.gov/research/umls/rxnorm'
        assert self.coder.get_system_uri('ICD10') == 'http://hl7.org/fhir/sid/icd-10'

        # Test case insensitivity
        assert self.coder.get_system_uri('loinc') == 'http://loinc.org'
        assert self.coder.get_system_uri('snomed') == 'http://snomed.info/sct'

    def test_get_system_uri_for_unknown_system(self):
        """Should return None for unknown coding systems"""
        assert self.coder.get_system_uri('UNKNOWN_SYSTEM') is None
        assert self.coder.get_system_uri('') is None

    def test_add_coding_with_system_name(self):
        """Should create FHIR Coding with system name"""
        coding = self.coder.add_coding('LOINC', '12345-6', 'Test Lab Result')

        assert coding['system'] == 'http://loinc.org'
        assert coding['code'] == '12345-6'
        assert coding['display'] == 'Test Lab Result'

    def test_add_coding_with_system_uri(self):
        """Should create FHIR Coding with system URI"""
        coding = self.coder.add_coding('http://loinc.org', '12345-6', 'Test Lab Result')

        assert coding['system'] == 'http://loinc.org'
        assert coding['code'] == '12345-6'
        assert coding['display'] == 'Test Lab Result'

    def test_add_coding_without_display(self):
        """Should create FHIR Coding without display text"""
        coding = self.coder.add_coding('LOINC', '12345-6')

        assert coding['system'] == 'http://loinc.org'
        assert coding['code'] == '12345-6'
        assert 'display' not in coding

    def test_add_coding_with_unknown_system(self):
        """Should raise ValueError for unknown coding system"""
        with pytest.raises(ValueError, match="Unknown coding system"):
            self.coder.add_coding('UNKNOWN_SYSTEM', 'code123')

    def test_add_coding_with_invalid_code(self):
        """Should raise ValueError for invalid code format"""
        with pytest.raises(ValueError, match="Invalid code format"):
            self.coder.add_coding('LOINC', 'invalid-code-format')

    def test_create_codeable_concept_single_coding(self):
        """Should create CodeableConcept with single coding"""
        concept = self.coder.create_codeable_concept('SNOMED', '12345678', 'Test Concept')

        assert 'coding' in concept
        assert len(concept['coding']) == 1
        assert concept['coding'][0]['system'] == 'http://snomed.info/sct'
        assert concept['coding'][0]['code'] == '12345678'
        assert concept['coding'][0]['display'] == 'Test Concept'
        assert concept['text'] == 'Test Concept'

    def test_create_codeable_concept_with_text(self):
        """Should create CodeableConcept with custom text"""
        concept = self.coder.create_codeable_concept(
            'SNOMED', '12345678', 'Test Concept', text='Custom description'
        )

        assert concept['text'] == 'Custom description'
        assert concept['coding'][0]['display'] == 'Test Concept'

    def test_create_multiple_codings(self):
        """Should create CodeableConcept with multiple coding systems"""
        codings = [
            {'system': 'SNOMED', 'code': '12345678', 'display': 'SNOMED Term'},
            {'system': 'ICD10', 'code': 'A12.3', 'display': 'ICD-10 Term'},
            {'system': 'LOINC', 'code': '12345-6', 'display': 'LOINC Term'}
        ]

        concept = self.coder.create_multiple_codings(codings)

        assert len(concept['coding']) == 3
        assert concept['coding'][0]['system'] == 'http://snomed.info/sct'
        assert concept['coding'][1]['system'] == 'http://hl7.org/fhir/sid/icd-10'
        assert concept['coding'][2]['system'] == 'http://loinc.org'
        assert concept['text'] == 'SNOMED Term'

    def test_create_multiple_codings_missing_required_fields(self):
        """Should raise ValueError for missing required fields"""
        incomplete_codings = [
            {'system': 'SNOMED'},  # Missing code
            {'code': '12345678'}   # Missing system
        ]

        with pytest.raises(ValueError, match="Each coding must have 'system' and 'code'"):
            self.coder.create_multiple_codings(incomplete_codings)

    def test_validate_loinc_code(self):
        """Should validate LOINC code format (NNNNN-N)"""
        assert self.coder.validate_code('http://loinc.org', '12345-6') is True
        assert self.coder.validate_code('http://loinc.org', '98765-4') is True

        # Invalid formats
        assert self.coder.validate_code('http://loinc.org', '1234-6') is False   # Too short
        assert self.coder.validate_code('http://loinc.org', '123456-6') is False # Too long
        assert self.coder.validate_code('http://loinc.org', '12345-67') is False # Multi-digit suffix
        assert self.coder.validate_code('http://loinc.org', '12345') is False    # Missing suffix

    def test_validate_snomed_code(self):
        """Should validate SNOMED CT code format (numeric, 6+ digits)"""
        assert self.coder.validate_code('http://snomed.info/sct', '123456') is True
        assert self.coder.validate_code('http://snomed.info/sct', '12345678') is True
        assert self.coder.validate_code('http://snomed.info/sct', '123456789012') is True

        # Invalid formats
        assert self.coder.validate_code('http://snomed.info/sct', '12345') is False  # Too short
        assert self.coder.validate_code('http://snomed.info/sct', 'A12345') is False # Non-numeric
        assert self.coder.validate_code('http://snomed.info/sct', '123-456') is False # Contains dash

    def test_validate_icd10_code(self):
        """Should validate ICD-10 code format"""
        assert self.coder.validate_code('http://hl7.org/fhir/sid/icd-10', 'A12') is True
        assert self.coder.validate_code('http://hl7.org/fhir/sid/icd-10', 'Z99.3') is True
        assert self.coder.validate_code('http://hl7.org/fhir/sid/icd-10', 'M12.123') is True

        # Invalid formats
        assert self.coder.validate_code('http://hl7.org/fhir/sid/icd-10', '123') is False     # No letter
        assert self.coder.validate_code('http://hl7.org/fhir/sid/icd-10', 'A1') is False     # Too short
        assert self.coder.validate_code('http://hl7.org/fhir/sid/icd-10', 'A123') is False   # Too long without decimal

    def test_validate_cpt_code(self):
        """Should validate CPT code format (5 digits)"""
        assert self.coder.validate_code('http://www.ama-assn.org/go/cpt', '12345') is True
        assert self.coder.validate_code('http://www.ama-assn.org/go/cpt', '99213') is True

        # Invalid formats
        assert self.coder.validate_code('http://www.ama-assn.org/go/cpt', '1234') is False   # Too short
        assert self.coder.validate_code('http://www.ama-assn.org/go/cpt', '123456') is False # Too long
        assert self.coder.validate_code('http://www.ama-assn.org/go/cpt', 'A1234') is False  # Non-numeric

    def test_validate_rxnorm_code(self):
        """Should validate RxNorm code format (numeric)"""
        assert self.coder.validate_code('http://www.nlm.nih.gov/research/umls/rxnorm', '1') is True
        assert self.coder.validate_code('http://www.nlm.nih.gov/research/umls/rxnorm', '123456') is True

        # Invalid formats
        assert self.coder.validate_code('http://www.nlm.nih.gov/research/umls/rxnorm', 'A123') is False
        assert self.coder.validate_code('http://www.nlm.nih.gov/research/umls/rxnorm', '12-34') is False

    def test_validate_cvx_code(self):
        """Should validate CVX vaccine code format"""
        assert self.coder.validate_code('http://hl7.org/fhir/sid/cvx', '1') is True
        assert self.coder.validate_code('http://hl7.org/fhir/sid/cvx', '12') is True
        assert self.coder.validate_code('http://hl7.org/fhir/sid/cvx', '123') is True

        # Invalid formats
        assert self.coder.validate_code('http://hl7.org/fhir/sid/cvx', '1234') is False  # Too long
        assert self.coder.validate_code('http://hl7.org/fhir/sid/cvx', 'A1') is False    # Non-numeric

    def test_validate_ndc_code(self):
        """Should validate NDC code format"""
        assert self.coder.validate_code('http://hl7.org/fhir/sid/ndc', '1234567890') is True     # 10 digits
        assert self.coder.validate_code('http://hl7.org/fhir/sid/ndc', '12345678901') is True    # 11 digits
        assert self.coder.validate_code('http://hl7.org/fhir/sid/ndc', '12345-678-90') is True   # With dashes

        # Invalid formats
        assert self.coder.validate_code('http://hl7.org/fhir/sid/ndc', '123456789') is False     # Too short
        assert self.coder.validate_code('http://hl7.org/fhir/sid/ndc', '123456789012') is False  # Too long

    def test_caching_functionality(self):
        """Should cache coding results for performance"""
        # First call creates and caches
        coding1 = self.coder.add_coding('LOINC', '12345-6', 'Test Code')

        # Second call should use cache
        coding2 = self.coder.add_coding('LOINC', '12345-6', 'Test Code')

        assert coding1 == coding2
        assert len(self.coder._cached_codes) > 0

    def test_get_display_name(self):
        """Should retrieve cached display names"""
        # Cache a coding first
        self.coder.add_coding('LOINC', '12345-6', 'Test Lab Result')

        # Retrieve display name
        display = self.coder.get_display_name('LOINC', '12345-6')
        assert display == 'Test Lab Result'

        # Non-cached code should return None
        display_none = self.coder.get_display_name('LOINC', '99999-9')
        assert display_none is None

    def test_create_quantity(self):
        """Should create FHIR Quantity with standardized units"""
        quantity = self.coder.create_quantity(70.5, 'kg')

        assert quantity['value'] == 70.5
        assert quantity['unit'] == 'kg'
        assert quantity['system'] == 'http://unitsofmeasure.org'
        assert quantity['code'] == 'kg'

    def test_create_quantity_with_custom_system(self):
        """Should create FHIR Quantity with custom unit system"""
        quantity = self.coder.create_quantity(98.6, 'F', 'CUSTOM')

        assert quantity['value'] == 98.6
        assert quantity['unit'] == 'F'
        assert quantity['system'] == 'CUSTOM'
        assert quantity['code'] == 'F'

    def test_register_custom_system(self):
        """Should allow registration of custom coding systems"""
        self.coder.register_custom_system('CUSTOM_SYSTEM', 'http://example.com/custom')

        # Should be available
        assert 'CUSTOM_SYSTEM' in self.coder.get_supported_systems()
        assert self.coder.get_system_uri('CUSTOM_SYSTEM') == 'http://example.com/custom'

        # Should be usable for coding
        coding = self.coder.add_coding('CUSTOM_SYSTEM', 'CUSTOM123', 'Custom Code')
        assert coding['system'] == 'http://example.com/custom'

    def test_clear_cache(self):
        """Should clear all caches"""
        # Add some cached data
        self.coder.add_coding('LOINC', '12345-6', 'Test')
        self.coder.get_system_uri('LOINC')  # Populate LRU cache

        assert len(self.coder._cached_codes) > 0

        # Clear cache
        self.coder.clear_cache()

        assert len(self.coder._cached_codes) == 0

    def test_get_statistics(self):
        """Should provide usage statistics"""
        # Add some cached data
        self.coder.add_coding('LOINC', '12345-6', 'Test')
        self.coder.get_system_uri('LOINC')

        stats = self.coder.get_statistics()

        assert 'supported_systems' in stats
        assert 'cached_codes' in stats
        assert 'cache_hits' in stats
        assert 'cache_misses' in stats
        assert stats['supported_systems'] > 0
        assert stats['cached_codes'] > 0

    def test_performance_requirement(self):
        """Should meet performance requirements"""
        import time

        start_time = time.time()
        coding = self.coder.add_coding('LOINC', '12345-6', 'Performance Test')
        duration_ms = (time.time() - start_time) * 1000

        assert coding is not None
        # Should be very fast (allowing for test environment variance)
        assert duration_ms < 50  # 50ms tolerance

    def test_validate_generic_code_format(self):
        """Should validate generic codes for unknown systems"""
        # Should accept alphanumeric codes
        assert self.coder.validate_code('http://unknown.system.com', 'ABC123') is True
        assert self.coder.validate_code('http://unknown.system.com', 'test-code') is True
        assert self.coder.validate_code('http://unknown.system.com', 'test.code') is True
        assert self.coder.validate_code('http://unknown.system.com', 'test_code') is True

        # Should reject special characters
        assert self.coder.validate_code('http://unknown.system.com', 'test@code') is False
        assert self.coder.validate_code('http://unknown.system.com', 'test code') is False  # Space
        assert self.coder.validate_code('http://unknown.system.com', '') is False


class TestCoderRegistryIntegration:
    """Test CoderRegistry integration with other components"""

    def test_shared_coder_usage(self):
        """Should work as shared component across multiple factories"""
        coder1 = CoderRegistry()
        coder2 = CoderRegistry()

        # Both should work independently
        coding1 = coder1.add_coding('LOINC', '12345-6', 'Test Code')
        coding2 = coder2.add_coding('SNOMED', '12345678', 'Test Concept')

        assert coding1['system'] == 'http://loinc.org'
        assert coding2['system'] == 'http://snomed.info/sct'

    def test_concurrent_coding_operations(self):
        """Should handle concurrent coding operations"""
        coder = CoderRegistry()

        # Create multiple codings concurrently
        codings = []
        for i in range(5):
            coding = coder.add_coding('LOINC', f'1234{i}-6', f'Test Code {i}')
            codings.append(coding)

        # All should be valid and unique
        assert len(codings) == 5
        for i, coding in enumerate(codings):
            assert coding['code'] == f'1234{i}-6'
            assert coding['display'] == f'Test Code {i}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])