"""
REFACTOR-004: Basic test suite for MedicationResourceFactory
Tests core functionality and FHIR R4 compliance
"""

import pytest
from unittest.mock import Mock, patch

from src.nl_fhir.services.fhir.factories.medication_factory import MedicationResourceFactory
from src.nl_fhir.services.fhir.factories.validators import ValidatorRegistry
from src.nl_fhir.services.fhir.factories.coders import CoderRegistry
from src.nl_fhir.services.fhir.factories.references import ReferenceManager


class TestMedicationResourceFactoryBasic:
    """Basic test suite for MedicationResourceFactory"""

    @pytest.fixture
    def validators(self):
        return ValidatorRegistry()

    @pytest.fixture
    def coders(self):
        return CoderRegistry()

    @pytest.fixture
    def reference_manager(self):
        return ReferenceManager()

    @pytest.fixture
    def factory(self, validators, coders, reference_manager):
        return MedicationResourceFactory(
            validators=validators,
            coders=coders,
            reference_manager=reference_manager
        )

    def test_factory_initialization(self, factory):
        """Test factory initialization with shared components"""
        assert factory.validators is not None
        assert factory.coders is not None
        assert factory.reference_manager is not None
        assert hasattr(factory, 'SUPPORTED_RESOURCES')
        assert len(factory.SUPPORTED_RESOURCES) == 5

        expected_resources = {
            'MedicationRequest', 'MedicationAdministration', 'Medication',
            'MedicationDispense', 'MedicationStatement'
        }
        assert factory.SUPPORTED_RESOURCES == expected_resources

    def test_supports_method(self, factory):
        """Test supports method for resource type validation"""
        # Test supported resources
        assert factory.supports('MedicationRequest') is True
        assert factory.supports('MedicationAdministration') is True
        assert factory.supports('Medication') is True
        assert factory.supports('MedicationDispense') is True
        assert factory.supports('MedicationStatement') is True

        # Test unsupported resources
        assert factory.supports('Patient') is False
        assert factory.supports('Observation') is False
        assert factory.supports('Device') is False

    def test_create_medication_request_basic(self, factory):
        """Test basic MedicationRequest creation"""
        data = {
            'medication_name': 'Amoxicillin',
            'patient_id': 'patient-123',
            'prescriber_id': 'practitioner-456',
            'dosage': '500 mg twice daily',
            'duration': '7 days'
        }

        result = factory.create('MedicationRequest', data, 'req-001')

        assert result['resourceType'] == 'MedicationRequest'
        assert result['status'] == 'active'
        assert result['intent'] == 'order'
        assert result['subject']['reference'] == 'Patient/patient-123'
        assert result['requester']['reference'] == 'Practitioner/practitioner-456'
        assert 'medicationCodeableConcept' in result
        assert 'dosageInstruction' in result

    def test_create_medication_administration(self, factory):
        """Test MedicationAdministration creation"""
        data = {
            'medication_name': 'Morphine',
            'patient_id': 'patient-123',
            'performer_id': 'practitioner-456',
            'administration_time': '2024-01-15T10:30:00Z',
            'dose_quantity': 2.5,
            'dose_unit': 'mg'
        }

        result = factory.create('MedicationAdministration', data)

        assert result['resourceType'] == 'MedicationAdministration'
        assert result['status'] == 'completed'
        assert result['subject']['reference'] == 'Patient/patient-123'
        assert 'performer' in result
        assert result['effectiveDateTime'] == '2024-01-15T10:30:00Z'
        assert 'dosage' in result

    def test_create_medication_basic(self, factory):
        """Test basic Medication resource creation"""
        data = {
            'medication_name': 'Acetaminophen',
            'manufacturer': 'Generic Pharma',
            'strength': '500 mg',
            'form': 'tablet'
        }

        result = factory.create('Medication', data)

        assert result['resourceType'] == 'Medication'
        assert result['status'] == 'active'
        assert 'code' in result

    def test_create_medication_dispense(self, factory):
        """Test MedicationDispense creation"""
        data = {
            'medication_name': 'Metformin',
            'patient_id': 'patient-123',
            'pharmacy_id': 'organization-pharmacy-456',
            'quantity_dispensed': 30,
            'days_supply': 30,
            'dispense_date': '2024-01-15'
        }

        result = factory.create('MedicationDispense', data)

        assert result['resourceType'] == 'MedicationDispense'
        assert result['status'] == 'completed'
        assert result['subject']['reference'] == 'Patient/patient-123'
        assert 'performer' in result

    def test_create_medication_statement(self, factory):
        """Test MedicationStatement creation"""
        data = {
            'medication_name': 'Aspirin',
            'patient_id': 'patient-123',
            'status': 'active',
            'effective_period_start': '2024-01-01',
            'dosage': '81 mg daily'
        }

        result = factory.create('MedicationStatement', data)

        assert result['resourceType'] == 'MedicationStatement'
        assert result['status'] == 'active'
        assert result['subject']['reference'] == 'Patient/patient-123'
        assert 'medicationCodeableConcept' in result

    def test_fhir_r4_validation(self, factory):
        """Test FHIR R4 compliance validation"""
        data = {
            'medication_name': 'Insulin',
            'patient_id': 'patient-123'
        }

        result = factory.create('MedicationRequest', data)

        # Validate using the ValidatorRegistry
        is_valid = factory.validators.validate_fhir_r4(result)
        assert is_valid is True

        if not is_valid:
            errors = factory.validators.get_validation_errors()
            pytest.fail(f"FHIR validation failed: {errors}")

    def test_error_handling_invalid_resource_type(self, factory):
        """Test error handling for invalid resource types"""
        with pytest.raises(ValueError, match="Factory does not support resource type"):
            factory.create('Patient', {'name': 'test'})

    def test_error_handling_missing_required_data(self, factory):
        """Test error handling for missing required data"""
        with pytest.raises(ValueError, match="Input data cannot be empty"):
            factory.create('MedicationRequest', {})


class TestMedicationFactoryIntegration:
    """Integration tests with FactoryRegistry"""

    @pytest.fixture
    def mock_settings(self):
        settings = Mock()
        settings.use_new_medication_factory = True
        settings.factory_debug_logging = True
        return settings

    @patch('src.nl_fhir.services.fhir.factories.get_settings')
    def test_factory_registry_integration(self, mock_get_settings, mock_settings):
        """Test MedicationResourceFactory integration with FactoryRegistry"""
        mock_get_settings.return_value = mock_settings

        from src.nl_fhir.services.fhir.factories import FactoryRegistry

        registry = FactoryRegistry()

        # Test that medication resources are mapped to MedicationResourceFactory
        factory = registry.get_factory('MedicationRequest')
        assert factory.__class__.__name__ == 'MedicationResourceFactory'

        factory = registry.get_factory('MedicationAdministration')
        assert factory.__class__.__name__ == 'MedicationResourceFactory'

        factory = registry.get_factory('Medication')
        assert factory.__class__.__name__ == 'MedicationResourceFactory'

    @patch('src.nl_fhir.services.fhir.factories.get_settings')
    def test_factory_registry_feature_flag_disabled(self, mock_get_settings, mock_settings):
        """Test fallback when medication factory feature flag is disabled"""
        mock_settings.use_new_medication_factory = False
        mock_get_settings.return_value = mock_settings

        from src.nl_fhir.services.fhir.factories import FactoryRegistry

        registry = FactoryRegistry()

        # Should fall back to MockResourceFactory
        factory = registry.get_factory('MedicationRequest')
        assert factory.__class__.__name__ in ['MockResourceFactory', 'FHIRResourceFactory']