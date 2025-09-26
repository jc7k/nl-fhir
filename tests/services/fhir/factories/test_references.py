"""
Tests for ReferenceManager - REFACTOR-002
Tests FHIR reference management and shared component integration
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from nl_fhir.services.fhir.factories.references import ReferenceManager


class TestReferenceManager:
    """Test suite for ReferenceManager FHIR reference functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.ref_manager = ReferenceManager()

    def test_reference_manager_initialization(self):
        """ReferenceManager should initialize with empty caches"""
        assert self.ref_manager is not None
        assert hasattr(self.ref_manager, 'logger')
        assert hasattr(self.ref_manager, '_resource_cache')
        assert hasattr(self.ref_manager, '_reference_index')
        assert hasattr(self.ref_manager, '_reverse_index')

        # Should start empty
        assert len(self.ref_manager._resource_cache) == 0
        assert len(self.ref_manager._reference_index) == 0
        assert len(self.ref_manager._reverse_index) == 0

    def test_create_reference_basic(self):
        """Should create basic FHIR reference string"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123'
        }

        reference = self.ref_manager.create_reference(patient)
        assert reference == 'Patient/test-patient-123'

    def test_create_reference_without_id(self):
        """Should generate ID if resource doesn't have one"""
        patient = {
            'resourceType': 'Patient',
            'name': [{'family': 'Doe', 'given': ['John']}]
        }

        reference = self.ref_manager.create_reference(patient)
        assert reference.startswith('Patient/Patient-')
        assert 'id' in patient  # Should have added ID to resource

    def test_create_reference_with_version(self):
        """Should create versioned reference when requested"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123',
            'meta': {'versionId': '2'}
        }

        reference = self.ref_manager.create_reference(patient, include_version=True)
        assert reference == 'Patient/test-patient-123/_history/2'

    def test_create_reference_with_version_default(self):
        """Should use default version if not specified"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123'
        }

        reference = self.ref_manager.create_reference(patient, include_version=True)
        assert reference == 'Patient/test-patient-123/_history/1'

    def test_create_reference_invalid_resource(self):
        """Should raise ValueError for invalid resources"""
        # Non-dict resource
        with pytest.raises(ValueError, match="Resource must be a dictionary"):
            self.ref_manager.create_reference("not a dict")

        # Missing resourceType
        with pytest.raises(ValueError, match="Resource must have resourceType"):
            self.ref_manager.create_reference({'id': 'test-123'})

    def test_create_reference_invalid_id_format(self):
        """Should raise ValueError for invalid ID format"""
        patient = {
            'resourceType': 'Patient',
            'id': 'invalid id with spaces'  # Invalid characters
        }

        with pytest.raises(ValueError, match="Invalid resource ID format"):
            self.ref_manager.create_reference(patient)

    def test_create_reference_dict_basic(self):
        """Should create FHIR Reference dictionary"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123'
        }

        ref_dict = self.ref_manager.create_reference_dict(patient)

        assert ref_dict['reference'] == 'Patient/test-patient-123'
        assert 'display' not in ref_dict  # No auto-generated display for basic patient

    def test_create_reference_dict_with_display(self):
        """Should create Reference dictionary with custom display"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123'
        }

        ref_dict = self.ref_manager.create_reference_dict(patient, display='John Doe')

        assert ref_dict['reference'] == 'Patient/test-patient-123'
        assert ref_dict['display'] == 'John Doe'

    def test_create_reference_dict_auto_display(self):
        """Should auto-generate display text for Patient with name"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123',
            'name': [{
                'family': 'Doe',
                'given': ['John', 'Michael']
            }]
        }

        ref_dict = self.ref_manager.create_reference_dict(patient)

        assert ref_dict['reference'] == 'Patient/test-patient-123'
        assert ref_dict['display'] == 'John Michael Doe'

    def test_resolve_reference_cached(self):
        """Should resolve reference to cached resource"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123',
            'name': [{'family': 'Doe'}]
        }

        # Create reference (this caches the resource)
        reference = self.ref_manager.create_reference(patient)

        # Resolve reference
        resolved = self.ref_manager.resolve_reference(reference)

        assert resolved is not None
        assert resolved['resourceType'] == 'Patient'
        assert resolved['id'] == 'test-patient-123'
        assert resolved['name'][0]['family'] == 'Doe'

    def test_resolve_reference_not_found(self):
        """Should return None for uncached reference"""
        resolved = self.ref_manager.resolve_reference('Patient/non-existent')
        assert resolved is None

    def test_resolve_reference_with_version(self):
        """Should resolve versioned reference"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123',
            'meta': {'versionId': '2'}
        }

        # Create versioned reference
        reference = self.ref_manager.create_reference(patient, include_version=True)

        # Should resolve to the same resource (version ignored for resolution)
        resolved = self.ref_manager.resolve_reference(reference)
        assert resolved is not None
        assert resolved['id'] == 'test-patient-123'

    def test_validate_reference_format_valid(self):
        """Should validate valid FHIR reference formats"""
        # Basic format
        assert self.ref_manager.validate_reference_format('Patient/123') is True
        assert self.ref_manager.validate_reference_format('Observation/test-obs-456') is True

        # With version
        assert self.ref_manager.validate_reference_format('Patient/123/_history/1') is True

        # Absolute URL
        assert self.ref_manager.validate_reference_format('https://example.com/fhir/Patient/123') is True

    def test_validate_reference_format_invalid(self):
        """Should reject invalid FHIR reference formats"""
        # Empty or None
        assert self.ref_manager.validate_reference_format('') is False
        assert self.ref_manager.validate_reference_format(None) is False

        # Missing parts
        assert self.ref_manager.validate_reference_format('Patient/') is False
        assert self.ref_manager.validate_reference_format('/123') is False

        # Invalid characters
        assert self.ref_manager.validate_reference_format('Patient/123 456') is False
        assert self.ref_manager.validate_reference_format('Patient/test@id') is False

        # Non-string
        assert self.ref_manager.validate_reference_format(123) is False

    def test_add_reference_relationship(self):
        """Should track reference relationships between resources"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123'
        }

        observation = {
            'resourceType': 'Observation',
            'id': 'test-obs-456'
        }

        patient_ref = 'Patient/test-patient-123'

        # Add relationship
        self.ref_manager.add_reference_relationship(observation, patient_ref)

        # Check forward index
        obs_refs = self.ref_manager.get_references_from(observation)
        assert patient_ref in obs_refs

        # Check reverse index
        refs_to_patient = self.ref_manager.get_references_to(patient)
        assert 'Observation/test-obs-456' in refs_to_patient

    def test_get_references_from_empty(self):
        """Should return empty list for resource with no references"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123'
        }

        references = self.ref_manager.get_references_from(patient)
        assert references == []

    def test_get_references_to_empty(self):
        """Should return empty list for unreferenced resource"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123'
        }

        references = self.ref_manager.get_references_to(patient)
        assert references == []

    def test_validate_reference_integrity_valid(self):
        """Should validate intact reference integrity"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123'
        }

        observation = {
            'resourceType': 'Observation',
            'id': 'test-obs-456'
        }

        # Cache both resources
        patient_ref = self.ref_manager.create_reference(patient)
        obs_ref = self.ref_manager.create_reference(observation)

        # Add relationship
        self.ref_manager.add_reference_relationship(observation, patient_ref)

        # Should have no errors
        errors = self.ref_manager.validate_reference_integrity()
        assert errors == []

    def test_validate_reference_integrity_broken(self):
        """Should detect broken references"""
        observation = {
            'resourceType': 'Observation',
            'id': 'test-obs-456'
        }

        # Add reference to non-existent patient
        missing_patient_ref = 'Patient/missing-patient'
        self.ref_manager.add_reference_relationship(observation, missing_patient_ref)

        # Should detect broken reference
        errors = self.ref_manager.validate_reference_integrity()
        assert len(errors) > 0
        assert 'Broken reference' in errors[0]
        assert missing_patient_ref in errors[0]

    def test_generate_display_text_patient(self):
        """Should generate display text for Patient resources"""
        # Patient with full name
        patient_full = {
            'resourceType': 'Patient',
            'name': [{
                'family': 'Doe',
                'given': ['John', 'Michael']
            }]
        }

        display = self.ref_manager._generate_display_text(patient_full)
        assert display == 'John Michael Doe'

        # Patient with family name only
        patient_family = {
            'resourceType': 'Patient',
            'name': [{
                'family': 'Doe'
            }]
        }

        display = self.ref_manager._generate_display_text(patient_family)
        assert display == 'Doe'

        # Patient without name
        patient_no_name = {
            'resourceType': 'Patient',
            'id': 'test-123'
        }

        display = self.ref_manager._generate_display_text(patient_no_name)
        assert display == 'Patient/test-123'

    def test_generate_display_text_medication(self):
        """Should generate display text for Medication resources"""
        medication = {
            'resourceType': 'Medication',
            'code': {
                'coding': [{
                    'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                    'code': '1049502',
                    'display': 'acetaminophen 325 MG Oral Tablet'
                }]
            }
        }

        display = self.ref_manager._generate_display_text(medication)
        assert display == 'acetaminophen 325 MG Oral Tablet'

    def test_generate_display_text_condition(self):
        """Should generate display text for Condition resources"""
        condition = {
            'resourceType': 'Condition',
            'code': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '44054006',
                    'display': 'Diabetes mellitus type 2'
                }]
            }
        }

        display = self.ref_manager._generate_display_text(condition)
        assert display == 'Diabetes mellitus type 2'

    def test_generate_display_text_observation(self):
        """Should generate display text for Observation resources"""
        observation = {
            'resourceType': 'Observation',
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': '29463-7',
                    'display': 'Body Weight'
                }]
            }
        }

        display = self.ref_manager._generate_display_text(observation)
        assert display == 'Body Weight'

    def test_generate_display_text_default(self):
        """Should generate default display text for unknown resource types"""
        custom_resource = {
            'resourceType': 'CustomResource',
            'id': 'test-123'
        }

        display = self.ref_manager._generate_display_text(custom_resource)
        assert display == 'CustomResource/test-123'

    def test_clear_cache(self):
        """Should clear all caches and relationships"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123'
        }

        observation = {
            'resourceType': 'Observation',
            'id': 'test-obs-456'
        }

        # Create references and relationships
        patient_ref = self.ref_manager.create_reference(patient)
        self.ref_manager.add_reference_relationship(observation, patient_ref)

        # Should have cached data
        assert len(self.ref_manager._resource_cache) > 0
        assert len(self.ref_manager._reference_index) > 0
        assert len(self.ref_manager._reverse_index) > 0

        # Clear cache
        self.ref_manager.clear_cache()

        # Should be empty
        assert len(self.ref_manager._resource_cache) == 0
        assert len(self.ref_manager._reference_index) == 0
        assert len(self.ref_manager._reverse_index) == 0

    def test_get_cache_statistics(self):
        """Should provide cache usage statistics"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient-123'
        }

        observation = {
            'resourceType': 'Observation',
            'id': 'test-obs-456'
        }

        # Create some cached data
        patient_ref = self.ref_manager.create_reference(patient)
        obs_ref = self.ref_manager.create_reference(observation)
        self.ref_manager.add_reference_relationship(observation, patient_ref)

        stats = self.ref_manager.get_cache_statistics()

        assert 'cached_resources' in stats
        assert 'reference_relationships' in stats
        assert 'reverse_relationships' in stats
        assert 'memory_usage_kb' in stats

        assert stats['cached_resources'] == 2
        assert stats['reference_relationships'] == 1
        assert stats['reverse_relationships'] == 1
        assert stats['memory_usage_kb'] > 0

    def test_clean_reference_with_version(self):
        """Should clean version information from references"""
        versioned_ref = 'Patient/test-123/_history/2'
        clean_ref = self.ref_manager._clean_reference(versioned_ref)
        assert clean_ref == 'Patient/test-123'

    def test_clean_reference_with_url(self):
        """Should clean URL prefix from references"""
        url_ref = 'https://example.com/fhir/Patient/test-123'
        clean_ref = self.ref_manager._clean_reference(url_ref)
        assert clean_ref == 'Patient/test-123'

    def test_clean_reference_basic(self):
        """Should leave basic references unchanged"""
        basic_ref = 'Patient/test-123'
        clean_ref = self.ref_manager._clean_reference(basic_ref)
        assert clean_ref == 'Patient/test-123'

    def test_performance_requirement(self):
        """Should meet performance requirements"""
        import time

        patient = {
            'resourceType': 'Patient',
            'id': 'perf-test-patient'
        }

        start_time = time.time()
        reference = self.ref_manager.create_reference(patient)
        duration_ms = (time.time() - start_time) * 1000

        assert reference is not None
        # Should be very fast (allowing for test environment variance)
        assert duration_ms < 50  # 50ms tolerance

    def test_concurrent_reference_operations(self):
        """Should handle concurrent reference operations"""
        resources = []
        for i in range(5):
            resource = {
                'resourceType': 'Patient',
                'id': f'patient-{i}'
            }
            resources.append(resource)

        # Create references concurrently
        references = []
        for resource in resources:
            ref = self.ref_manager.create_reference(resource)
            references.append(ref)

        # All should be unique and valid
        assert len(references) == 5
        assert len(set(references)) == 5  # All unique

        # All should be resolvable
        for ref in references:
            resolved = self.ref_manager.resolve_reference(ref)
            assert resolved is not None


class TestReferenceManagerIntegration:
    """Test ReferenceManager integration with other components"""

    def test_shared_reference_manager(self):
        """Should work as shared component across multiple factories"""
        ref_mgr1 = ReferenceManager()
        ref_mgr2 = ReferenceManager()

        # Both should work independently
        patient = {
            'resourceType': 'Patient',
            'id': 'shared-patient'
        }

        ref1 = ref_mgr1.create_reference(patient)
        ref2 = ref_mgr2.create_reference(patient)

        # Same reference string
        assert ref1 == ref2

        # But independent caches
        resolved1 = ref_mgr1.resolve_reference(ref1)
        resolved2 = ref_mgr2.resolve_reference(ref2)

        assert resolved1 is not None
        assert resolved2 is None  # Not cached in ref_mgr2

    def test_cross_resource_relationships(self):
        """Should handle complex cross-resource relationships"""
        ref_manager = ReferenceManager()

        # Create a web of relationships
        patient = {'resourceType': 'Patient', 'id': 'patient-1'}
        practitioner = {'resourceType': 'Practitioner', 'id': 'practitioner-1'}
        encounter = {'resourceType': 'Encounter', 'id': 'encounter-1'}
        observation = {'resourceType': 'Observation', 'id': 'observation-1'}

        # Create references
        patient_ref = ref_manager.create_reference(patient)
        practitioner_ref = ref_manager.create_reference(practitioner)
        encounter_ref = ref_manager.create_reference(encounter)

        # Add relationships
        ref_manager.add_reference_relationship(encounter, patient_ref)
        ref_manager.add_reference_relationship(encounter, practitioner_ref)
        ref_manager.add_reference_relationship(observation, patient_ref)
        ref_manager.add_reference_relationship(observation, encounter_ref)

        # Verify complex relationships
        encounter_refs = ref_manager.get_references_from(encounter)
        assert patient_ref in encounter_refs
        assert practitioner_ref in encounter_refs

        patient_refs = ref_manager.get_references_to(patient)
        assert 'Encounter/encounter-1' in patient_refs
        assert 'Observation/observation-1' in patient_refs

        # Should have no broken references
        errors = ref_manager.validate_reference_integrity()
        assert errors == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])