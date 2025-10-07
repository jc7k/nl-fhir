"""
Tests for ConsentFactory - Epic 9 Phase 3: User Story 2
FHIR R4 Consent resource creation with granular privacy controls.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from src.nl_fhir.services.fhir.factories import get_factory_registry


@pytest.fixture
def factory_registry():
    """Get factory registry instance"""
    return get_factory_registry()


@pytest.fixture
def consent_factory(factory_registry):
    """Get Consent factory instance"""
    return factory_registry.get_factory('Consent')


@pytest.fixture
def sample_consent_basic() -> Dict[str, Any]:
    """Sample data for basic patient privacy consent"""
    return {
        'status': 'active',
        'category': ['HIPAA'],
        'patient_id': 'Patient/patient-12345',
        'date_time': datetime.now().date().isoformat(),
        'decision': 'permit',
        'purpose': ['TREAT'],
    }


@pytest.fixture
def sample_consent_granular() -> Dict[str, Any]:
    """Sample data for granular consent with actors and data categories"""
    return {
        'status': 'active',
        'category': ['HIPAA', 'research'],
        'patient_id': 'Patient/patient-12345',
        'date_time': datetime.now().date().isoformat(),
        'decision': 'permit',
        'purpose': ['TREAT', 'HPAYMT'],
        'actor_id': 'Practitioner/dr-smith-67890',
        'actor_role': 'PRCP',  # Primary care provider
        'data_category': ['MedicationRequest', 'Observation'],
        'period_start': datetime.now().date().isoformat(),
        'period_end': (datetime.now() + timedelta(days=365)).date().isoformat(),
    }


@pytest.fixture
def sample_consent_deny() -> Dict[str, Any]:
    """Sample data for deny consent (opt-out)"""
    return {
        'status': 'active',
        'category': ['HIPAA'],
        'patient_id': 'Patient/patient-12345',
        'date_time': datetime.now().date().isoformat(),
        'decision': 'deny',
        'purpose': ['HMARKT'],  # Marketing purposes
    }


class TestConsentFactoryCreation:
    """Test Consent resource creation"""

    def test_create_basic_consent(self, consent_factory, sample_consent_basic):
        """Test creating a basic patient privacy consent"""
        consent = consent_factory.create('Consent', sample_consent_basic)

        assert consent is not None
        assert consent['resourceType'] == 'Consent'
        assert consent['status'] == 'active'
        assert consent['decision'] == 'permit'
        assert consent['subject']['reference'] == 'Patient/patient-12345'
        assert len(consent['category']) == 1
        assert consent['category'][0]['coding'][0]['code'] == 'HIPAA'
        assert len(consent['provision']) == 1
        assert consent['provision'][0]['purpose'][0]['code'] == 'TREAT'

    def test_create_granular_consent(self, consent_factory, sample_consent_granular):
        """Test creating a granular consent with actors and data categories"""
        consent = consent_factory.create('Consent', sample_consent_granular)

        assert consent is not None
        assert consent['resourceType'] == 'Consent'
        assert consent['decision'] == 'permit'
        assert len(consent['category']) == 2
        assert len(consent['provision']) == 1

        provision = consent['provision'][0]
        assert len(provision['purpose']) == 2
        assert provision['actor'][0]['reference']['reference'] == 'Practitioner/dr-smith-67890'
        assert provision['actor'][0]['role']['coding'][0]['code'] == 'PRCP'
        # Note: data_category is stored as metadata, not in provision.data
        # provision.data is for specific resource instances in FHIR R4
        assert provision['period']['start'] is not None
        assert provision['period']['end'] is not None

    def test_create_deny_consent(self, consent_factory, sample_consent_deny):
        """Test creating a deny consent (opt-out)"""
        consent = consent_factory.create('Consent', sample_consent_deny)

        assert consent is not None
        assert consent['decision'] == 'deny'
        assert consent['provision'][0]['purpose'][0]['code'] == 'HMARKT'


class TestConsentCompliance:
    """Test consent compliance and validation"""

    def test_consent_required_fields(self, consent_factory):
        """Test that missing required fields raise validation errors"""
        invalid_data = {
            'status': 'active',
            # Missing category, patient_id, decision
        }

        with pytest.raises(ValueError, match="Missing required field"):
            consent_factory.create('Consent', invalid_data)

    def test_consent_fhir_validation(self, consent_factory, sample_consent_basic):
        """Test that created consent passes FHIR R4 validation"""
        consent = consent_factory.create('Consent', sample_consent_basic)

        # Validate FHIR R4 structure
        assert 'resourceType' in consent
        assert 'status' in consent
        assert 'decision' in consent
        assert 'category' in consent
        assert 'subject' in consent
        assert 'provision' in consent


class TestConsentEnforcement:
    """Test consent enforcement logic"""

    def test_check_consent_permit(self, consent_factory, sample_consent_basic):
        """Test consent checking for permitted purposes"""
        consent = consent_factory.create('Consent', sample_consent_basic)

        # Should permit treatment purposes
        is_permitted = consent_factory.check_consent(consent, purpose='TREAT')
        assert is_permitted is True

    def test_check_consent_deny(self, consent_factory, sample_consent_deny):
        """Test consent checking for denied purposes"""
        consent = consent_factory.create('Consent', sample_consent_deny)

        # Should deny marketing purposes
        is_permitted = consent_factory.check_consent(consent, purpose='HMARKT')
        assert is_permitted is False

    def test_check_consent_expired(self, consent_factory):
        """Test consent checking for expired consents"""
        expired_data = {
            'status': 'active',
            'category': ['HIPAA'],
            'patient_id': 'Patient/patient-12345',
            'date_time': datetime.now().date().isoformat(),
            'decision': 'permit',
            'purpose': ['TREAT'],
            'period_start': (datetime.now() - timedelta(days=400)).date().isoformat(),
            'period_end': (datetime.now() - timedelta(days=10)).date().isoformat(),
        }

        consent = consent_factory.create('Consent', expired_data)

        # Should not be active due to expired period
        is_active = consent_factory.is_consent_active(consent)
        assert is_active is False


class TestConsentQueryMethods:
    """Test consent query and search methods"""

    def test_query_consent_by_patient(self, consent_factory, sample_consent_basic):
        """Test querying consents by patient ID"""
        consent = consent_factory.create('Consent', sample_consent_basic)

        # Verify patient reference is queryable
        assert consent['subject']['reference'] == 'Patient/patient-12345'

    def test_query_active_consents(self, consent_factory, sample_consent_basic):
        """Test querying only active consents"""
        consent = consent_factory.create('Consent', sample_consent_basic)

        is_active = consent_factory.is_consent_active(consent)
        assert is_active is True
        assert consent['status'] == 'active'
