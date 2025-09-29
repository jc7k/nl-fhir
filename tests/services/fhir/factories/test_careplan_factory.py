"""
REFACTOR-006: Comprehensive test suite for CarePlanResourceFactory
Tests all CarePlan features, SNOMED CT coding, and FHIR R4 compliance
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from src.nl_fhir.services.fhir.factories.careplan_factory import CarePlanResourceFactory
from src.nl_fhir.services.fhir.factories.validators import ValidatorRegistry
from src.nl_fhir.services.fhir.factories.coders import CoderRegistry
from src.nl_fhir.services.fhir.factories.references import ReferenceManager


class TestCarePlanResourceFactory:
    """Test suite for CarePlanResourceFactory"""

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
        return CarePlanResourceFactory(
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
        assert len(factory.SUPPORTED_RESOURCES) == 1
        assert 'CarePlan' in factory.SUPPORTED_RESOURCES

    def test_supports_method(self, factory):
        """Test supports method for resource type validation"""
        # Test supported resources
        assert factory.supports('CarePlan') is True

        # Test unsupported resources
        assert factory.supports('Patient') is False
        assert factory.supports('Observation') is False
        assert factory.supports('MedicationRequest') is False

    def test_create_basic_careplan(self, factory):
        """Test basic CarePlan creation"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Diabetes Management Plan',
            'description': 'Comprehensive care plan for Type 2 diabetes management',
            'status': 'active',
            'intent': 'plan'
        }

        result = factory.create('CarePlan', data, 'req-001')

        assert result['resourceType'] == 'CarePlan'
        assert result['status'] == 'active'
        assert result['intent'] == 'plan'
        assert result['title'] == 'Diabetes Management Plan'
        assert result['description'] == 'Comprehensive care plan for Type 2 diabetes management'
        assert result['subject']['reference'] == 'Patient/patient-123'
        assert 'created' in result
        assert 'meta' in result
        assert result['meta']['factory'] == 'CarePlanResourceFactory'

    def test_careplan_with_period(self, factory):
        """Test CarePlan with period specification"""
        data = {
            'patient_id': 'patient-123',
            'title': '30-Day Recovery Plan',
            'period_start': '2024-01-01',
            'period_end': '2024-01-31'
        }

        result = factory.create('CarePlan', data)

        assert 'period' in result
        assert result['period']['start'] == '2024-01-01'
        assert result['period']['end'] == '2024-01-31'

    def test_careplan_with_duration(self, factory):
        """Test CarePlan with duration-based period"""
        data = {
            'patient_id': 'patient-123',
            'title': '90-Day Treatment Plan',
            'period_start': '2024-01-01',
            'duration_days': 90
        }

        result = factory.create('CarePlan', data)

        assert 'period' in result
        assert result['period']['start'] == '2024-01-01'
        assert result['period']['end'] == '2024-03-31'  # 90 days from start

    def test_careplan_categories(self, factory):
        """Test CarePlan category determination"""
        test_cases = [
            ('Assessment Plan', 'assessment'),
            ('Physical Therapy Plan', 'therapy'),
            ('Patient Education Program', 'education'),
            ('Medication Management', 'medication'),
            ('Dietary Management Plan', 'diet'),
            ('Exercise Program', 'exercise'),
            ('Discharge Planning', 'discharge')
        ]

        for title, expected_category in test_cases:
            data = {
                'patient_id': 'patient-123',
                'title': title
            }
            result = factory.create('CarePlan', data)

            assert 'category' in result
            category = result['category'][0]
            assert 'coding' in category
            # Category should be correctly identified based on title

    def test_careplan_with_author(self, factory):
        """Test CarePlan with author reference"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Care Plan',
            'author': 'practitioner-456'
        }

        result = factory.create('CarePlan', data)

        assert 'author' in result
        assert result['author']['reference'] == 'Practitioner/practitioner-456'

    def test_careplan_with_contributors(self, factory):
        """Test CarePlan with multiple contributors"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Multidisciplinary Care Plan',
            'author': 'practitioner-primary',
            'contributors': ['practitioner-nurse', 'practitioner-therapist', 'practitioner-dietitian']
        }

        result = factory.create('CarePlan', data)

        assert 'contributor' in result
        assert len(result['contributor']) == 3
        assert result['contributor'][0]['reference'] == 'Practitioner/practitioner-nurse'
        assert result['contributor'][1]['reference'] == 'Practitioner/practitioner-therapist'
        assert result['contributor'][2]['reference'] == 'Practitioner/practitioner-dietitian'

    def test_careplan_with_care_team(self, factory):
        """Test CarePlan with care team reference"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Coordinated Care Plan',
            'care_team_id': 'team-789'
        }

        result = factory.create('CarePlan', data)

        assert 'careTeam' in result
        assert result['careTeam'][0]['reference'] == 'CareTeam/team-789'

    def test_careplan_addressing_conditions(self, factory):
        """Test CarePlan addressing specific conditions"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Treatment Plan',
            'conditions': ['diabetes-001', 'hypertension-002']
        }

        result = factory.create('CarePlan', data)

        assert 'addresses' in result
        assert len(result['addresses']) == 2
        assert result['addresses'][0]['reference'] == 'Condition/diabetes-001'
        assert result['addresses'][1]['reference'] == 'Condition/hypertension-002'

    def test_careplan_with_goals(self, factory):
        """Test CarePlan with goal references"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Weight Management Plan',
            'goals': [
                'goal-weight-loss',
                'goal-exercise-routine',
                {'id': 'goal-diet', 'description': 'Maintain healthy diet'}
            ]
        }

        result = factory.create('CarePlan', data)

        assert 'goal' in result
        assert len(result['goal']) == 3
        assert result['goal'][0]['reference'] == 'Goal/goal-weight-loss'
        assert result['goal'][1]['reference'] == 'Goal/goal-exercise-routine'
        assert result['goal'][2]['reference'].startswith('Goal/')

    def test_careplan_with_simple_activities(self, factory):
        """Test CarePlan with simple activity descriptions"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Daily Care Plan',
            'activities': [
                'Daily blood glucose monitoring',
                'Medication administration twice daily',
                'Physical therapy session 3x per week'
            ]
        }

        result = factory.create('CarePlan', data)

        assert 'activity' in result
        assert len(result['activity']) == 3
        assert result['activity'][0]['detail']['description'] == 'Daily blood glucose monitoring'
        assert result['activity'][0]['detail']['status'] == 'not-started'

    def test_careplan_with_structured_activities(self, factory):
        """Test CarePlan with structured activity data"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Complex Care Plan',
            'activities': [
                {
                    'name': 'Medication Administration',
                    'kind': 'medication',
                    'status': 'in-progress',
                    'description': 'Administer insulin as prescribed',
                    'frequency': 2,
                    'period_unit': 'd',
                    'performer': 'nurse-001'
                },
                {
                    'name': 'Vital Signs Monitoring',
                    'kind': 'observation',
                    'status': 'scheduled',
                    'scheduled_time': '2024-01-15T08:00:00Z',
                    'location': 'room-101',
                    'quantity': 1,
                    'unit': 'measurement'
                },
                {
                    'reference': 'ServiceRequest/physical-therapy-001',
                    'progress': 'Patient showing improvement in mobility',
                    'outcome_codes': ['improved', 'continue-therapy']
                }
            ]
        }

        result = factory.create('CarePlan', data)

        assert 'activity' in result
        assert len(result['activity']) == 3

        # Check first activity (medication)
        activity1 = result['activity'][0]
        assert activity1['detail']['kind'] == 'MedicationRequest'
        assert activity1['detail']['status'] == 'in-progress'
        assert 'scheduledTiming' in activity1['detail']
        assert activity1['detail']['performer'][0]['reference'] == 'Practitioner/nurse-001'

        # Check second activity (observation)
        activity2 = result['activity'][1]
        assert activity2['detail']['kind'] == 'ServiceRequest'
        assert activity2['detail']['status'] == 'scheduled'
        assert 'scheduledTiming' in activity2['detail']
        assert activity2['detail']['location']['reference'] == 'Location/room-101'

        # Check third activity (with reference)
        activity3 = result['activity'][2]
        assert activity3['reference']['reference'] == 'ServiceRequest/physical-therapy-001'
        assert activity3['progress'][0]['text'] == 'Patient showing improvement in mobility'
        assert len(activity3['outcomeCodeableConcept']) == 2

    def test_careplan_with_notes(self, factory):
        """Test CarePlan with notes"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Care Plan with Notes',
            'notes': [
                'Patient prefers morning appointments',
                'Family involved in care decisions'
            ]
        }

        result = factory.create('CarePlan', data)

        assert 'note' in result
        assert len(result['note']) == 2
        assert result['note'][0]['text'] == 'Patient prefers morning appointments'
        assert result['note'][1]['text'] == 'Family involved in care decisions'
        assert 'time' in result['note'][0]

    def test_careplan_status_validation(self, factory):
        """Test CarePlan status validation"""
        valid_statuses = ['draft', 'active', 'on-hold', 'revoked', 'completed', 'entered-in-error', 'unknown']

        for status in valid_statuses:
            data = {
                'patient_id': 'patient-123',
                'title': 'Test Plan',
                'status': status
            }
            result = factory.create('CarePlan', data)
            assert result['status'] == status

        # Test invalid status defaults to 'active'
        data = {
            'patient_id': 'patient-123',
            'title': 'Test Plan',
            'status': 'invalid-status'
        }
        result = factory.create('CarePlan', data)
        assert result['status'] == 'active'

    def test_careplan_intent_validation(self, factory):
        """Test CarePlan intent validation"""
        valid_intents = ['proposal', 'plan', 'order', 'option', 'directive']

        for intent in valid_intents:
            data = {
                'patient_id': 'patient-123',
                'title': 'Test Plan',
                'intent': intent
            }
            result = factory.create('CarePlan', data)
            assert result['intent'] == intent

        # Test invalid intent defaults to 'plan'
        data = {
            'patient_id': 'patient-123',
            'title': 'Test Plan',
            'intent': 'invalid-intent'
        }
        result = factory.create('CarePlan', data)
        assert result['intent'] == 'plan'

    def test_careplan_activity_with_product(self, factory):
        """Test CarePlan activity with product references"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Medication Plan',
            'activities': [
                {
                    'name': 'Insulin Administration',
                    'product_reference': 'Medication/insulin-001',
                    'quantity': 10,
                    'unit': 'units'
                },
                {
                    'name': 'Blood Glucose Testing',
                    'product_code': 'Blood glucose test strips',
                    'quantity': 100,
                    'unit': 'strips'
                }
            ]
        }

        result = factory.create('CarePlan', data)

        activity1 = result['activity'][0]
        assert 'productReference' in activity1['detail']
        assert activity1['detail']['productReference']['reference'] == 'Medication/insulin-001'
        assert activity1['detail']['quantity']['value'] == 10

        activity2 = result['activity'][1]
        assert 'productCodeableConcept' in activity2['detail']
        assert activity2['detail']['productCodeableConcept']['text'] == 'Blood glucose test strips'

    def test_careplan_activity_with_goals(self, factory):
        """Test CarePlan activity linked to specific goals"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Rehabilitation Plan',
            'activities': [
                {
                    'name': 'Physical Therapy',
                    'description': 'Daily PT exercises',
                    'goals': ['goal-mobility', 'goal-strength']
                }
            ]
        }

        result = factory.create('CarePlan', data)

        activity = result['activity'][0]
        assert 'goal' in activity['detail']
        assert len(activity['detail']['goal']) == 2
        assert activity['detail']['goal'][0]['reference'] == 'Goal/goal-mobility'
        assert activity['detail']['goal'][1]['reference'] == 'Goal/goal-strength'

    def test_careplan_metrics_tracking(self, factory):
        """Test CarePlan metrics tracking"""
        # Create several care plans to generate metrics
        for i in range(5):
            data = {
                'patient_id': f'patient-{i}',
                'title': f'Care Plan {i}',
                'status': 'active' if i < 3 else 'draft',
                'goals': ['goal-1'] if i < 2 else [],
                'activities': ['activity-1'] if i < 4 else []
            }
            factory.create('CarePlan', data)

        stats = factory.get_careplan_statistics()

        assert stats['careplan_metrics']['total_careplans'] == 5
        assert stats['careplan_metrics']['active_careplans'] == 3
        assert stats['careplan_metrics']['careplans_with_goals'] == 2
        assert stats['careplan_metrics']['careplans_with_activities'] == 4

    def test_careplan_health_check(self, factory):
        """Test factory health check functionality"""
        health = factory.health_check()

        assert health['status'] == 'healthy'
        assert health['supported_resources'] == 1
        assert 'creation_time_ms' in health
        assert health['performance_ok'] is True
        assert health['careplan_categories'] > 0
        assert health['activity_kinds'] > 0
        assert 'shared_components' in health

    def test_careplan_error_handling_missing_patient(self, factory):
        """Test error handling for missing patient reference"""
        data = {
            'title': 'Test CarePlan'
            # Missing patient_id
        }

        with pytest.raises(ValueError, match="Required field 'patient_id' is missing for CarePlan"):
            factory.create('CarePlan', data)

    def test_careplan_error_handling_invalid_resource_type(self, factory):
        """Test error handling for invalid resource types"""
        with pytest.raises(ValueError, match="Factory does not support resource type"):
            factory.create('Patient', {'name': 'test'})

    def test_careplan_performance(self, factory):
        """Test CarePlan creation performance"""
        import time

        data = {
            'patient_id': 'patient-123',
            'title': 'Performance Test Plan',
            'activities': [
                {'description': f'Activity {i}'} for i in range(10)
            ]
        }

        start_time = time.time()
        result = factory.create('CarePlan', data)
        duration = (time.time() - start_time) * 1000

        assert result is not None
        assert duration < 10.0  # Should complete in less than 10ms

    def test_careplan_with_prohibited_activities(self, factory):
        """Test CarePlan with prohibited/do-not-perform activities"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Restricted Care Plan',
            'activities': [
                {
                    'name': 'Avoid heavy lifting',
                    'description': 'Patient should not lift more than 10 pounds',
                    'prohibited': True
                }
            ]
        }

        result = factory.create('CarePlan', data)

        activity = result['activity'][0]
        assert activity['detail']['doNotPerform'] is True

    def test_careplan_with_multiple_performers(self, factory):
        """Test CarePlan activity with multiple performers"""
        data = {
            'patient_id': 'patient-123',
            'title': 'Team-Based Care Plan',
            'activities': [
                {
                    'name': 'Coordinated Assessment',
                    'performers': ['practitioner-1', 'practitioner-2', 'practitioner-3']
                }
            ]
        }

        result = factory.create('CarePlan', data)

        activity = result['activity'][0]
        assert len(activity['detail']['performer']) == 3
        assert activity['detail']['performer'][0]['reference'] == 'Practitioner/practitioner-1'

    def test_careplan_fhir_r4_compliance(self, factory):
        """Test FHIR R4 compliance validation"""
        data = {
            'patient_id': 'patient-123',
            'title': 'FHIR Compliant Care Plan',
            'status': 'active',
            'intent': 'plan'
        }

        result = factory.create('CarePlan', data)

        # Validate using the ValidatorRegistry
        is_valid = factory.validators.validate_fhir_r4(result)
        assert is_valid is True

        if not is_valid:
            errors = factory.validators.get_validation_errors()
            pytest.fail(f"FHIR validation failed: {errors}")


class TestCarePlanFactoryIntegration:
    """Integration tests with FactoryRegistry"""

    @pytest.fixture
    def mock_settings(self):
        settings = Mock()
        settings.use_new_careplan_factory = True
        settings.factory_debug_logging = True
        return settings

    @patch('src.nl_fhir.services.fhir.factories.get_settings')
    def test_factory_registry_integration(self, mock_get_settings, mock_settings):
        """Test CarePlanResourceFactory integration with FactoryRegistry"""
        mock_get_settings.return_value = mock_settings

        from src.nl_fhir.services.fhir.factories import FactoryRegistry

        # Reset the singleton instance to force re-initialization with mock settings
        FactoryRegistry._instance = None
        FactoryRegistry._factories = {}

        # Create a new registry instance with mock settings
        registry = FactoryRegistry()

        # Test that CarePlan is mapped to CarePlanResourceFactory
        factory = registry.get_factory('CarePlan')
        assert factory.__class__.__name__ == 'CarePlanResourceFactory'

    @patch('src.nl_fhir.services.fhir.factories.get_settings')
    def test_factory_registry_feature_flag_disabled(self, mock_get_settings, mock_settings):
        """Test fallback when CarePlan factory feature flag is disabled"""
        mock_settings.use_new_careplan_factory = False
        mock_get_settings.return_value = mock_settings

        from src.nl_fhir.services.fhir.factories import FactoryRegistry

        # Reset the singleton instance
        FactoryRegistry._instance = None
        FactoryRegistry._factories = {}

        registry = FactoryRegistry()

        # Should fall back to MockResourceFactory
        factory = registry.get_factory('CarePlan')
        assert factory.__class__.__name__ in ['MockResourceFactory', 'FHIRResourceFactory']