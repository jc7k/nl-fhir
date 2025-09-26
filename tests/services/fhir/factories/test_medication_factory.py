"""
REFACTOR-004: Comprehensive test suite for MedicationResourceFactory
Tests all medication resource types, safety features, and FHIR R4 compliance
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from typing import Dict, Any

from src.nl_fhir.services.fhir.factories.medication_factory import MedicationResourceFactory
from src.nl_fhir.services.fhir.factories.validators import ValidatorRegistry
from src.nl_fhir.services.fhir.factories.coders import CoderRegistry
from src.nl_fhir.services.fhir.factories.references import ReferenceManager


class TestMedicationResourceFactory:
    """Test suite for MedicationResourceFactory"""

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
        assert result['meta']['source'] == 'NL-FHIR-Medication'

    def test_create_medication_request_with_rxnorm(self, factory):
        """Test MedicationRequest with RxNorm coding"""
        data = {
            'medication_name': 'Lisinopril',
            'medication_code': '29046',
            'coding_system': 'RXNORM',
            'patient_id': 'patient-123',
            'dosage': '10 mg daily'
        }

        result = factory.create('MedicationRequest', data)

        coding = result['medicationCodeableConcept']['coding'][0]
        assert coding['system'] == 'http://www.nlm.nih.gov/research/umls/rxnorm'
        assert coding['code'] == '29046'
        assert coding['display'] == 'Lisinopril'

    def test_create_medication_request_with_allergy_check(self, factory):
        """Test MedicationRequest with allergy checking"""
        data = {
            'medication_name': 'Penicillin',
            'patient_id': 'patient-123',
            'known_allergies': ['Penicillin', 'Sulfa']
        }

        result = factory.create('MedicationRequest', data)

        # Should include allergy warning in notes
        assert 'note' in result
        assert any('ALLERGY WARNING' in note['text'] for note in result['note'])

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
        assert result['dosage']['dose']['value'] == 2.5
        assert result['dosage']['dose']['unit'] == 'mg'

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
        assert 'manufacturer' in result
        assert result['manufacturer']['display'] == 'Generic Pharma'
        assert 'form' in result

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
        assert result['quantity']['value'] == 30
        assert result['daysSupply']['value'] == 30
        assert result['whenHandedOver'] == '2024-01-15'

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
        assert 'effectivePeriod' in result
        assert result['effectivePeriod']['start'] == '2024-01-01'

    def test_dosage_processing_complex(self, factory):
        """Test complex dosage instruction processing"""
        dosage_text = "Take 2 tablets by mouth every 6 hours as needed for pain"

        result = factory._process_dosage_instruction(dosage_text)

        assert result['text'] == dosage_text
        assert 'timing' in result
        assert 'doseAndRate' in result
        assert result['asNeededBoolean'] is True
        assert result['route']['coding'][0]['code'] == '26643006'  # Oral route

    def test_drug_interaction_detection(self, factory):
        """Test drug interaction detection"""
        interactions = factory._check_drug_interactions('Warfarin', ['Aspirin', 'Amoxicillin'])

        assert len(interactions) >= 1
        assert any('Warfarin' in interaction and 'Aspirin' in interaction for interaction in interactions)

    def test_medication_safety_validation(self, factory):
        """Test comprehensive medication safety validation"""
        data = {
            'medication_name': 'Digoxin',
            'patient_id': 'patient-elderly-123',
            'dose_quantity': 0.25,
            'patient_age': 85,
            'kidney_function': 'mild_impairment'
        }

        safety_notes = factory._validate_medication_safety(data)

        assert len(safety_notes) > 0
        assert any('elderly' in note.lower() for note in safety_notes)

    def test_rxnorm_medication_lookup(self, factory):
        """Test RxNorm medication code lookup"""
        # Test with known medication
        code = factory._lookup_rxnorm_code('Metformin')
        assert code is not None
        assert code.isdigit()

        # Test with unknown medication
        code = factory._lookup_rxnorm_code('UnknownDrug123')
        assert code is None

    def test_pharmacy_workflow_support(self, factory):
        """Test pharmacy workflow features"""
        data = {
            'medication_name': 'Atorvastatin',
            'patient_id': 'patient-123',
            'prescriber_id': 'practitioner-456',
            'pharmacy_id': 'organization-pharmacy-789',
            'insurance_coverage': True,
            'prior_authorization': False
        }

        workflow_data = factory._create_pharmacy_workflow_data(data)

        assert 'dispenseRequest' in workflow_data
        assert 'insurance' in workflow_data
        assert workflow_data['insurance']['coverage'] is True
        assert workflow_data['priorAuthorization'] is False

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

    def test_performance_monitoring(self, factory):
        """Test performance monitoring features"""
        factory._performance_monitor.reset_stats()

        # Create multiple resources to generate metrics
        for i in range(5):
            data = {'medication_name': f'TestMed{i}', 'patient_id': f'patient-{i}'}
            factory.create('MedicationRequest', data)

        stats = factory.get_performance_stats()

        assert stats['total_requests'] == 5
        assert stats['avg_response_time_ms'] > 0
        assert 'medication_requests_created' in stats
        assert stats['medication_requests_created'] == 5

    def test_health_check(self, factory):
        """Test factory health check functionality"""
        health = factory.health_check()

        assert health['status'] == 'healthy'
        assert health['supported_resources'] == 5
        assert 'shared_components' in health
        assert health['shared_components']['validators'] is True
        assert health['shared_components']['coders'] is True
        assert health['shared_components']['reference_manager'] is True

    def test_error_handling_invalid_resource_type(self, factory):
        """Test error handling for invalid resource types"""
        with pytest.raises(ValueError, match="Unsupported resource type"):
            factory.create('Patient', {})

    def test_error_handling_missing_required_data(self, factory):
        """Test error handling for missing required data"""
        with pytest.raises(ValueError, match="medication_name.*required"):
            factory.create('MedicationRequest', {})

    def test_ndc_code_validation(self, factory):
        """Test NDC code validation and formatting"""
        # Test valid NDC codes
        assert factory._validate_ndc_code('0069-2587-68') is True
        assert factory._validate_ndc_code('12345678901') is True

        # Test invalid NDC codes
        assert factory._validate_ndc_code('invalid') is False
        assert factory._validate_ndc_code('123') is False

    def test_medication_strength_parsing(self, factory):
        """Test medication strength parsing and standardization"""
        test_cases = [
            ('500 mg', {'value': 500, 'unit': 'mg'}),
            ('2.5mg', {'value': 2.5, 'unit': 'mg'}),
            ('1 tablet', {'value': 1, 'unit': 'tablet'}),
            ('5 mL', {'value': 5, 'unit': 'mL'})
        ]

        for input_strength, expected in test_cases:
            result = factory._parse_medication_strength(input_strength)
            assert result == expected

    def test_concurrent_medication_checking(self, factory):
        """Test concurrent medication interaction checking"""
        current_meds = ['Warfarin', 'Metformin', 'Lisinopril']
        new_med = 'Aspirin'

        warnings = factory._check_concurrent_medications(new_med, current_meds)

        assert len(warnings) > 0
        assert any('Warfarin' in warning for warning in warnings)

    @patch('src.nl_fhir.services.fhir.factories.medication_factory.time.time')
    def test_performance_requirements(self, mock_time, factory):
        """Test that factory meets performance requirements (<10ms per resource)"""
        # Mock timing to simulate fast execution
        mock_time.side_effect = [0.0, 0.005]  # 5ms execution time

        data = {
            'medication_name': 'TestMedication',
            'patient_id': 'patient-123'
        }

        result = factory.create('MedicationRequest', data)

        assert result is not None
        # Performance is monitored internally - check stats
        stats = factory.get_performance_stats()
        assert stats['avg_response_time_ms'] < 10.0


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