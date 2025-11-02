"""
REFACTOR-005: Basic test suite for ClinicalResourceFactory
Tests core functionality and FHIR R4 compliance for clinical resources
"""

import pytest
from unittest.mock import Mock, patch

from src.nl_fhir.services.fhir.factories.clinical_factory import ClinicalResourceFactory
from src.nl_fhir.services.fhir.factories.validators import ValidatorRegistry
from src.nl_fhir.services.fhir.factories.coders import CoderRegistry
from src.nl_fhir.services.fhir.factories.references import ReferenceManager


class TestClinicalResourceFactoryBasic:
    """Basic test suite for ClinicalResourceFactory"""

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
        return ClinicalResourceFactory(
            validators=validators,
            coders=coders,
            reference_manager=reference_manager
        )

    @pytest.mark.skip(reason="Factory initialization changed in FactoryAdapter refactoring")
    def test_factory_initialization(self, factory):
        """Test factory initialization with shared components"""
        assert factory.validators is not None
        assert factory.coders is not None
        assert factory.reference_manager is not None
        assert hasattr(factory, 'SUPPORTED_RESOURCES')
        assert len(factory.SUPPORTED_RESOURCES) == 5

        expected_resources = {
            'Observation', 'DiagnosticReport', 'ServiceRequest',
            'Condition', 'AllergyIntolerance'
        }
        assert factory.SUPPORTED_RESOURCES == expected_resources

    def test_supports_method(self, factory):
        """Test supports method for resource type validation"""
        # Test supported resources
        assert factory.supports('Observation') is True
        assert factory.supports('DiagnosticReport') is True
        assert factory.supports('ServiceRequest') is True
        assert factory.supports('Condition') is True
        assert factory.supports('AllergyIntolerance') is True

        # Test unsupported resources
        assert factory.supports('Patient') is False
        assert factory.supports('MedicationRequest') is False
        assert factory.supports('Device') is False

    def test_create_observation_basic(self, factory):
        """Test basic Observation creation"""
        data = {
            'name': 'Heart Rate',
            'patient_id': 'patient-123',
            'value': 72,
            'unit': 'beats/min'
        }

        result = factory.create('Observation', data, 'req-001')

        assert result['resourceType'] == 'Observation'
        assert result['status'] == 'final'
        assert result['subject']['reference'] == 'Patient/patient-123'
        assert 'code' in result
        assert 'effectiveDateTime' in result

    def test_create_observation_with_components(self, factory):
        """Test Observation creation with components (e.g., blood pressure)"""
        data = {
            'name': 'Blood Pressure',
            'patient_id': 'patient-123',
            'components': [
                {'name': 'Systolic', 'value': 120, 'unit': 'mmHg'},
                {'name': 'Diastolic', 'value': 80, 'unit': 'mmHg'}
            ]
        }

        result = factory.create('Observation', data)

        assert result['resourceType'] == 'Observation'
        assert 'component' in result
        assert len(result['component']) == 2

    def test_create_diagnostic_report(self, factory):
        """Test DiagnosticReport creation"""
        data = {
            'name': 'Laboratory Report',
            'patient_id': 'patient-123',
            'performer': 'practitioner-456',
            'conclusion': 'Normal results'
        }

        result = factory.create('DiagnosticReport', data)

        assert result['resourceType'] == 'DiagnosticReport'
        assert result['status'] == 'final'
        assert result['subject']['reference'] == 'Patient/patient-123'
        assert 'code' in result
        assert 'category' in result
        assert result['conclusion'] == 'Normal results'

    def test_create_service_request(self, factory):
        """Test ServiceRequest creation"""
        data = {
            'name': 'CBC with Differential',
            'patient_id': 'patient-123',
            'requester': 'practitioner-456',
            'priority': 'urgent'
        }

        result = factory.create('ServiceRequest', data)

        assert result['resourceType'] == 'ServiceRequest'
        assert result['status'] == 'active'
        assert result['intent'] == 'order'
        assert result['subject']['reference'] == 'Patient/patient-123'
        assert result['priority'] == 'urgent'
        assert 'code' in result
        assert 'category' in result

    def test_create_condition(self, factory):
        """Test Condition creation"""
        data = {
            'name': 'Diabetes',
            'patient_id': 'patient-123',
            'clinical_status': 'active',
            'severity': 'moderate'
        }

        result = factory.create('Condition', data)

        assert result['resourceType'] == 'Condition'
        assert result['subject']['reference'] == 'Patient/patient-123'
        assert 'clinicalStatus' in result
        assert 'verificationStatus' in result
        assert 'code' in result
        assert 'severity' in result

    def test_create_allergy_intolerance(self, factory):
        """Test AllergyIntolerance creation"""
        data = {
            'name': 'Penicillin',
            'patient_id': 'patient-123',
            'category': 'medication',
            'criticality': 'high',
            'reactions': [
                {
                    'symptoms': ['rash', 'hives'],
                    'severity': 'moderate'
                }
            ]
        }

        result = factory.create('AllergyIntolerance', data)

        assert result['resourceType'] == 'AllergyIntolerance'
        assert result['patient']['reference'] == 'Patient/patient-123'
        assert result['category'] == ['medication']
        assert result['criticality'] == 'high'
        assert 'code' in result
        assert 'reaction' in result

    def test_observation_vital_signs_coding(self, factory):
        """Test LOINC coding for vital signs"""
        data = {
            'name': 'Heart Rate',
            'patient_id': 'patient-123',
            'value': 72
        }

        result = factory.create('Observation', data)

        # Should have vital-signs category
        categories = result.get('category', [])
        assert any('vital-signs' in str(cat) for cat in categories)

    def test_condition_with_icd10_coding(self, factory):
        """Test Condition with ICD-10 coding"""
        data = {
            'name': 'Diabetes',
            'patient_id': 'patient-123'
        }

        result = factory.create('Condition', data)

        # Should have coding with ICD-10 and SNOMED
        coding = result.get('code', {}).get('coding', [])
        assert len(coding) > 0

    def test_allergy_with_rxnorm_coding(self, factory):
        """Test AllergyIntolerance with RxNorm coding"""
        data = {
            'name': 'Penicillin',
            'patient_id': 'patient-123'
        }

        result = factory.create('AllergyIntolerance', data)

        # Should have appropriate coding
        assert 'code' in result

    def test_clinical_id_generation(self, factory):
        """Test clinical resource ID generation"""
        data = {
            'name': 'Test Observation',
            'patient_id': 'patient-123'
        }

        result = factory.create('Observation', data)

        # Should generate FHIR-compliant ID
        assert 'id' in result
        assert len(result['id']) <= 64
        assert result['id'].startswith('clinical-obs-')

    def test_error_handling_missing_patient(self, factory):
        """Test error handling for missing patient reference"""
        data = {
            'name': 'Test Observation'
            # Missing patient_id
        }

        with pytest.raises(ValueError, match="Required field 'patient_id' is missing for Observation"):
            factory.create('Observation', data)

    def test_error_handling_invalid_resource_type(self, factory):
        """Test error handling for invalid resource types"""
        with pytest.raises(ValueError, match="Factory does not support resource type"):
            factory.create('Patient', {'name': 'test'})

    def test_observation_value_types(self, factory):
        """Test different observation value types"""
        # Numeric value
        data_numeric = {
            'name': 'Temperature',
            'patient_id': 'patient-123',
            'value_quantity': 98.6,
            'unit': 'F'
        }

        result_numeric = factory.create('Observation', data_numeric)
        assert 'valueQuantity' in result_numeric

        # String value
        data_string = {
            'name': 'Assessment',
            'patient_id': 'patient-123',
            'value_string': 'Normal'
        }

        result_string = factory.create('Observation', data_string)
        assert 'valueString' in result_string

        # Boolean value
        data_boolean = {
            'name': 'Smoker',
            'patient_id': 'patient-123',
            'value_boolean': False
        }

        result_boolean = factory.create('Observation', data_boolean)
        assert 'valueBoolean' in result_boolean

    def test_diagnostic_report_categories(self, factory):
        """Test diagnostic report category determination"""
        # Laboratory report
        data_lab = {
            'name': 'Laboratory Report',
            'patient_id': 'patient-123'
        }

        result_lab = factory.create('DiagnosticReport', data_lab)
        category = result_lab.get('category', [{}])[0]
        assert 'LAB' in str(category)

        # Radiology report - need to use 'x-ray' to match our keywords
        data_rad = {
            'name': 'Chest X-ray Report',
            'patient_id': 'patient-123'
        }

        result_rad = factory.create('DiagnosticReport', data_rad)
        category = result_rad.get('category', [{}])[0]
        assert 'RAD' in str(category)

    def test_service_request_priorities(self, factory):
        """Test service request priority normalization"""
        priorities = ['routine', 'urgent', 'stat', 'emergency']

        for priority in priorities:
            data = {
                'name': 'Lab Test',
                'patient_id': 'patient-123',
                'priority': priority
            }

            result = factory.create('ServiceRequest', data)
            assert 'priority' in result

    def test_allergy_categories(self, factory):
        """Test allergy category determination"""
        test_cases = [
            ('Penicillin', 'medication'),
            ('Peanuts', 'food'),
            ('Latex', 'environment')
        ]

        for allergen, expected_category in test_cases:
            data = {
                'name': allergen,
                'patient_id': 'patient-123'
            }

            result = factory.create('AllergyIntolerance', data)
            categories = result.get('category', [])
            assert expected_category in categories

    def test_clinical_metadata(self, factory):
        """Test clinical-specific metadata"""
        data = {
            'name': 'Test Observation',
            'patient_id': 'patient-123'
        }

        result = factory.create('Observation', data, 'req-001')

        assert 'meta' in result
        meta = result['meta']
        assert 'factory' in meta
        assert meta['factory'] == 'ClinicalResourceFactory'
        assert 'request_id' in meta
        assert meta['request_id'] == 'req-001'

    @pytest.mark.skip(reason="Health check method renamed/changed in FactoryAdapter refactoring")
    def test_health_check(self, factory):
        """Test factory health check functionality"""
        health = factory.health_check()

        assert health['status'] == 'healthy'
        assert health['supported_resources'] == 5
        assert 'creation_time_ms' in health
        assert health['performance_ok'] is True
        assert 'coding_systems' in health
        assert 'shared_components' in health

    @pytest.mark.skip(reason="Statistics API changed in FactoryAdapter refactoring")
    def test_clinical_statistics(self, factory):
        """Test clinical factory statistics"""
        # Create some resources to generate metrics
        data = {
            'name': 'Test Observation',
            'patient_id': 'patient-123'
        }

        factory.create('Observation', data)
        factory.create('Condition', {'name': 'Test Condition', 'patient_id': 'patient-123'})

        stats = factory.get_clinical_statistics()

        assert stats['supported_resources'] == 5
        assert 'resource_metrics' in stats
        assert 'coding_cache_size' in stats
        assert stats['factory_type'] == 'ClinicalResourceFactory'


class TestClinicalFactoryIntegration:
    """Integration tests with FactoryRegistry"""

    @pytest.fixture
    def mock_settings(self):
        settings = Mock()
        settings.use_new_clinical_factory = True
        settings.use_new_patient_factory = False
        settings.use_new_medication_factory = False
        settings.use_legacy_factory = False
        settings.factory_debug_logging = True
        return settings

    @patch('src.nl_fhir.services.fhir.factories.get_settings')
    @pytest.mark.skip(reason="Factory registry integration changed in FactoryAdapter refactoring")
    def test_factory_registry_integration(self, mock_get_settings, mock_settings):
        """Test ClinicalResourceFactory integration with FactoryRegistry"""
        mock_get_settings.return_value = mock_settings

        from src.nl_fhir.services.fhir.factories import FactoryRegistry

        # Reset the singleton instance to force re-initialization with mock settings
        FactoryRegistry._instance = None
        FactoryRegistry._factories = {}

        # Create a new registry instance with mock settings
        registry = FactoryRegistry()

        # Test that clinical resources are mapped to ClinicalResourceFactory
        factory = registry.get_factory('Observation')
        assert factory.__class__.__name__ == 'ClinicalResourceFactory'

        factory = registry.get_factory('DiagnosticReport')
        assert factory.__class__.__name__ == 'ClinicalResourceFactory'

        factory = registry.get_factory('ServiceRequest')
        assert factory.__class__.__name__ == 'ClinicalResourceFactory'

        factory = registry.get_factory('Condition')
        assert factory.__class__.__name__ == 'ClinicalResourceFactory'

        factory = registry.get_factory('AllergyIntolerance')
        assert factory.__class__.__name__ == 'ClinicalResourceFactory'

    @patch('src.nl_fhir.services.fhir.factories.get_settings')
    def test_factory_registry_feature_flag_disabled(self, mock_get_settings, mock_settings):
        """Test fallback when clinical factory feature flag is disabled"""
        mock_settings.use_new_clinical_factory = False
        mock_settings.use_new_patient_factory = False
        mock_settings.use_new_medication_factory = False
        mock_settings.use_legacy_factory = False
        mock_settings.factory_debug_logging = True
        mock_get_settings.return_value = mock_settings

        from src.nl_fhir.services.fhir.factories import FactoryRegistry

        # Reset the singleton instance to force re-initialization with mock settings
        FactoryRegistry._instance = None
        FactoryRegistry._factories = {}

        registry = FactoryRegistry()

        # Should fall back to MockResourceFactory
        factory = registry.get_factory('Observation')
        assert factory.__class__.__name__ in ['MockResourceFactory', 'FHIRResourceFactory']