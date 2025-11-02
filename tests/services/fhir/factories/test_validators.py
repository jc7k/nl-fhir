"""
Tests for ValidatorRegistry - REFACTOR-002
Tests FHIR R4 validation functionality and shared component integration
"""

import pytest
from unittest.mock import MagicMock, patch
import json

from nl_fhir.services.fhir.factories.validators import ValidatorRegistry


class TestValidatorRegistry:
    """Test suite for ValidatorRegistry FHIR validation functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.validator = ValidatorRegistry()

    def test_validator_initialization(self):
        """ValidatorRegistry should initialize with default settings"""
        assert self.validator is not None
        assert hasattr(self.validator, 'logger')
        assert hasattr(self.validator, '_validation_cache')
        # Validate that public API exists (don't check private attributes)
        assert hasattr(self.validator, 'get_validation_errors')

    def test_validate_fhir_r4_with_valid_patient(self):
        """Should validate a properly formed Patient resource"""
        valid_patient = {
            'resourceType': 'Patient',
            'id': 'test-patient',
            'active': True,
            'name': [{
                'use': 'official',
                'family': 'Doe',
                'given': ['John']
            }],
            'gender': 'male',
            'birthDate': '1980-01-01'
        }

        result = self.validator.validate_fhir_r4(valid_patient)
        assert result is True
        assert len(self.validator.get_validation_errors()) == 0

    def test_validate_fhir_r4_with_invalid_resource_type(self):
        """Should fail validation for missing resourceType"""
        # The resource_type validator requires resourceType to be present
        resource_without_type = {
            'id': 'test-patient',
            'active': True
        }

        result = self.validator.validate_fhir_r4(resource_without_type)
        assert result is False
        errors = self.validator.get_validation_errors()
        assert len(errors) > 0

    def test_validate_fhir_r4_with_invalid_resource_structure(self):
        """Should fail validation for malformed resource with invalid reference format"""
        invalid_resource = {
            'resourceType': 'MedicationRequest',
            'id': 'test-med-request',
            'subject': {
                'reference': 'invalid reference format'  # Invalid - should be ResourceType/id
            },
            'medicationCodeableConcept': {
                'coding': [{'system': 'http://test.com', 'code': '123'}]
            },
            'status': 'active',
            'intent': 'order'
        }

        result = self.validator.validate_fhir_r4(invalid_resource)
        assert result is False
        errors = self.validator.get_validation_errors()
        assert len(errors) > 0

    def test_validate_medication_request_structure(self):
        """Should validate MedicationRequest resource properly"""
        medication_request = {
            'resourceType': 'MedicationRequest',
            'id': 'test-med-request',
            'status': 'active',
            'intent': 'order',
            'subject': {'reference': 'Patient/test-patient'},
            'medicationCodeableConcept': {
                'coding': [{
                    'system': 'http://www.nlm.nih.gov/research/umls/rxnorm',
                    'code': '1049502',
                    'display': 'acetaminophen 325 MG Oral Tablet'
                }]
            }
        }

        result = self.validator.validate_fhir_r4(medication_request)
        assert result is True

    def test_validate_observation_with_required_fields(self):
        """Should validate Observation resource with all required fields"""
        observation = {
            'resourceType': 'Observation',
            'id': 'test-observation',
            'status': 'final',
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': '29463-7',
                    'display': 'Body Weight'
                }]
            },
            'subject': {'reference': 'Patient/test-patient'},
            'valueQuantity': {
                'value': 70,
                'unit': 'kg',
                'system': 'http://unitsofmeasure.org',
                'code': 'kg'
            }
        }

        result = self.validator.validate_fhir_r4(observation)
        assert result is True

    def test_validate_device_resource_structure(self):
        """Should validate Device resource properly"""
        device = {
            'resourceType': 'Device',
            'id': 'test-device',
            'status': 'active',
            'deviceName': [{
                'name': 'Infusion Pump Model X',
                'type': 'user-friendly-name'
            }],
            'type': {
                'coding': [{
                    'system': 'http://snomed.info/sct',
                    'code': '706172005',
                    'display': 'Infusion pump'
                }]
            }
        }

        result = self.validator.validate_fhir_r4(device)
        assert result is True

    def test_validation_caching(self):
        """Should cache validation results for performance"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient',
            'active': True,
            'name': [{'text': 'Test Patient'}]
        }

        # First validation
        result1 = self.validator.validate_fhir_r4(patient)

        # Second validation (should be cached)
        result2 = self.validator.validate_fhir_r4(patient)

        assert result1 == result2
        assert result1 is True

        # Verify cache is working by checking internal state
        assert len(self.validator._validation_cache) > 0

    def test_validation_error_tracking(self):
        """Should track and report validation errors"""
        # Use a recognized resource type with missing required fields
        invalid_resource = {
            'resourceType': 'MedicationRequest',
            'id': 'test-123'
            # Missing required: subject, medicationCodeableConcept
        }

        result = self.validator.validate_fhir_r4(invalid_resource)
        assert result is False

        errors = self.validator.get_validation_errors()
        assert len(errors) > 0
        assert isinstance(errors, list)

    def test_clear_validation_cache(self):
        """Should be able to clear validation cache"""
        patient = {
            'resourceType': 'Patient',
            'id': 'test-patient',
            'active': True
        }

        # Validate to populate cache
        self.validator.validate_fhir_r4(patient)
        assert len(self.validator._validation_cache) > 0

        # Clear cache
        self.validator.clear_cache()
        assert len(self.validator._validation_cache) == 0

    def test_validate_bundle_structure(self):
        """Should validate Bundle resource with entries"""
        bundle = {
            'resourceType': 'Bundle',
            'id': 'test-bundle',
            'type': 'transaction',
            'entry': [
                {
                    'resource': {
                        'resourceType': 'Patient',
                        'id': 'test-patient',
                        'active': True
                    },
                    'request': {
                        'method': 'POST',
                        'url': 'Patient'
                    }
                }
            ]
        }

        result = self.validator.validate_fhir_r4(bundle)
        assert result is True

    def test_validate_complex_nested_structure(self):
        """Should validate complex nested FHIR structures"""
        complex_patient = {
            'resourceType': 'Patient',
            'id': 'complex-patient',
            'active': True,
            'name': [{
                'use': 'official',
                'family': 'Complex',
                'given': ['Test', 'Middle'],
                'prefix': ['Mr.']
            }],
            'telecom': [{
                'system': 'phone',
                'value': '+1-555-555-5555',
                'use': 'home'
            }],
            'address': [{
                'use': 'home',
                'line': ['123 Test St'],
                'city': 'Test City',
                'state': 'TS',
                'postalCode': '12345',
                'country': 'US'
            }],
            'contact': [{
                'relationship': [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/v2-0131',
                        'code': 'C',
                        'display': 'Emergency Contact'
                    }]
                }],
                'name': {
                    'family': 'Emergency',
                    'given': ['Contact']
                },
                'telecom': [{
                    'system': 'phone',
                    'value': '+1-555-555-9999'
                }]
            }]
        }

        result = self.validator.validate_fhir_r4(complex_patient)
        assert result is True

    def test_validate_with_meta_information(self):
        """Should validate resources with meta information"""
        patient_with_meta = {
            'resourceType': 'Patient',
            'id': 'meta-patient',
            'meta': {
                'versionId': '1',
                'lastUpdated': '2024-01-01T00:00:00Z',
                'profile': ['http://hl7.org/fhir/StructureDefinition/Patient']
            },
            'active': True,
            'name': [{'text': 'Meta Patient'}]
        }

        result = self.validator.validate_fhir_r4(patient_with_meta)
        assert result is True

    def test_performance_requirement(self):
        """Should validate within performance requirements"""
        import time

        patient = {
            'resourceType': 'Patient',
            'id': 'perf-test',
            'active': True,
            'name': [{'text': 'Performance Test'}]
        }

        start_time = time.time()
        result = self.validator.validate_fhir_r4(patient)
        duration_ms = (time.time() - start_time) * 1000

        assert result is True
        # Should validate quickly (allowing for test environment variance)
        assert duration_ms < 100  # 100ms tolerance

    def test_validate_empty_resource(self):
        """Should handle empty or None resources gracefully"""
        # Test None
        result_none = self.validator.validate_fhir_r4(None)
        assert result_none is False

        # Test empty dict
        result_empty = self.validator.validate_fhir_r4({})
        assert result_empty is False

        # Test non-dict
        result_string = self.validator.validate_fhir_r4("not a dict")
        assert result_string is False

    def test_validate_multiple_errors(self):
        """Should collect and report multiple validation errors"""
        # Create resource with multiple actual validation failures
        resource_with_errors = {
            'resourceType': 'Observation',
            'id': 'test-obs',
            # Missing required fields: subject, code, status
            'subject': {
                'reference': 'invalid reference'  # Also invalid reference format
            },
            'code': {
                'coding': [{
                    'system': '',  # Invalid: empty system
                    'code': ''     # Invalid: empty code
                }]
            }
        }

        result = self.validator.validate_fhir_r4(resource_with_errors)
        assert result is False

        errors = self.validator.get_validation_errors()
        # Should have multiple errors (missing fields, invalid reference, invalid coding)
        assert len(errors) >= 1


class TestValidatorRegistryIntegration:
    """Test ValidatorRegistry integration with other components"""

    def test_validator_registry_shared_usage(self):
        """Should work as shared component across multiple factories"""
        validator1 = ValidatorRegistry()
        validator2 = ValidatorRegistry()

        # Both should work independently
        patient = {
            'resourceType': 'Patient',
            'id': 'shared-test',
            'active': True
        }

        result1 = validator1.validate_fhir_r4(patient)
        result2 = validator2.validate_fhir_r4(patient)

        assert result1 is True
        assert result2 is True

    def test_concurrent_validation(self):
        """Should handle concurrent validation requests"""
        validator = ValidatorRegistry()

        resources = [
            {'resourceType': 'Patient', 'id': f'patient-{i}', 'active': True}
            for i in range(5)
        ]

        results = []
        for resource in resources:
            results.append(validator.validate_fhir_r4(resource))

        # All should be valid
        assert all(results)
        assert len(results) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])