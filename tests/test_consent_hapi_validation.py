"""
Test ConsentFactory FHIR R4 compliance using HAPI FHIR server.
Epic 9 Phase 3 - HAPI FHIR validation requirement.
"""

import pytest
import requests
from datetime import datetime
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
def hapi_fhir_url():
    """HAPI FHIR server base URL"""
    return "http://localhost:8080/fhir"


@pytest.fixture
def sample_consent_data() -> Dict[str, Any]:
    """Sample consent data for HAPI validation"""
    return {
        'status': 'active',
        'scope': 'patient-privacy',
        'category': ['HIPAA'],
        'patient_id': 'Patient/patient-12345',
        'date_time': datetime.now().date().isoformat(),
        'policy_rule': 'OPTIN',  # FHIR R4 uses policyRule (OPTIN = permit)
        'purpose': ['TREAT'],
    }


def check_hapi_server(hapi_url: str) -> bool:
    """Check if HAPI FHIR server is accessible"""
    try:
        response = requests.get(f"{hapi_url}/metadata", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


class TestConsentHAPIValidation:
    """Test Consent resources against HAPI FHIR server"""

    def test_hapi_server_accessible(self, hapi_fhir_url):
        """Verify HAPI FHIR server is running and accessible"""
        is_accessible = check_hapi_server(hapi_fhir_url)
        if not is_accessible:
            pytest.skip("HAPI FHIR server not accessible at http://localhost:8080/fhir")

        assert is_accessible, "HAPI FHIR server should be accessible"

    def test_consent_validates_with_hapi(self, consent_factory, sample_consent_data, hapi_fhir_url):
        """Test that ConsentFactory creates HAPI FHIR-valid Consent resources"""
        # Check HAPI server
        if not check_hapi_server(hapi_fhir_url):
            pytest.skip("HAPI FHIR server not accessible")

        # Create Consent resource
        consent = consent_factory.create('Consent', sample_consent_data)

        assert consent is not None
        assert consent['resourceType'] == 'Consent'

        # Validate against HAPI FHIR using $validate operation
        try:
            response = requests.post(
                f"{hapi_fhir_url}/Consent/$validate",
                json=consent,
                headers={'Content-Type': 'application/fhir+json'},
                timeout=10
            )

            # HAPI returns 200 for validation requests
            assert response.status_code == 200, f"HAPI validation failed: {response.status_code}"

            result = response.json()

            # Check OperationOutcome for issues
            if result.get('resourceType') == 'OperationOutcome':
                issues = result.get('issue', [])

                # Filter out informational messages, focus on errors/warnings
                errors = [i for i in issues if i.get('severity') in ['error', 'fatal']]
                warnings = [i for i in issues if i.get('severity') == 'warning']

                # Log warnings for visibility
                if warnings:
                    print(f"\nHAPI Validation Warnings ({len(warnings)}):")
                    for w in warnings:
                        print(f"  - {w.get('diagnostics', w.get('details', {}).get('text', 'No details'))}")

                # Assert no errors
                assert len(errors) == 0, f"HAPI validation errors: {errors}"

                print(f"\n✅ HAPI FHIR validation passed (0 errors, {len(warnings)} warnings)")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Could not connect to HAPI FHIR server: {e}")

    def test_consent_can_be_created_in_hapi(self, consent_factory, sample_consent_data, hapi_fhir_url):
        """Test that Consent resource can be created in HAPI FHIR server"""
        # Check HAPI server
        if not check_hapi_server(hapi_fhir_url):
            pytest.skip("HAPI FHIR server not accessible")

        # Create Consent resource
        consent = consent_factory.create('Consent', sample_consent_data)

        try:
            # Create resource in HAPI
            response = requests.post(
                f"{hapi_fhir_url}/Consent",
                json=consent,
                headers={'Content-Type': 'application/fhir+json'},
                timeout=10
            )

            # 201 Created is success
            assert response.status_code == 201, f"HAPI resource creation failed: {response.status_code} - {response.text}"

            created_consent = response.json()
            assert created_consent['resourceType'] == 'Consent'
            assert 'id' in created_consent  # HAPI assigns server ID

            print(f"\n✅ Consent resource created in HAPI with ID: {created_consent['id']}")

            # Clean up: delete the resource
            consent_id = created_consent['id']
            delete_response = requests.delete(
                f"{hapi_fhir_url}/Consent/{consent_id}",
                timeout=10
            )
            print(f"Cleanup: Deleted Consent/{consent_id} (status: {delete_response.status_code})")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Could not connect to HAPI FHIR server: {e}")

    def test_consent_with_granular_controls_validates(self, consent_factory, hapi_fhir_url):
        """Test granular consent with actors and time periods validates with HAPI"""
        # Check HAPI server
        if not check_hapi_server(hapi_fhir_url):
            pytest.skip("HAPI FHIR server not accessible")

        # Create granular consent
        from datetime import timedelta

        granular_data = {
            'status': 'active',
            'scope': 'patient-privacy',
            'category': ['HIPAA', 'research'],
            'patient_id': 'Patient/patient-12345',
            'date_time': datetime.now().date().isoformat(),
            'policy_rule': 'OPTIN',  # FHIR R4 uses policyRule (OPTIN = permit)
            'purpose': ['TREAT', 'HPAYMT'],
            'actor_id': 'Practitioner/dr-smith-67890',
            'actor_role': 'PRCP',
            'period_start': datetime.now().date().isoformat(),
            'period_end': (datetime.now() + timedelta(days=365)).date().isoformat(),
        }

        consent = consent_factory.create('Consent', granular_data)

        try:
            # Validate against HAPI
            response = requests.post(
                f"{hapi_fhir_url}/Consent/$validate",
                json=consent,
                headers={'Content-Type': 'application/fhir+json'},
                timeout=10
            )

            assert response.status_code == 200

            result = response.json()
            if result.get('resourceType') == 'OperationOutcome':
                errors = [i for i in result.get('issue', []) if i.get('severity') in ['error', 'fatal']]
                assert len(errors) == 0, f"Granular consent validation errors: {errors}"

                print("\n✅ Granular Consent (with actors & periods) HAPI validation passed")

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Could not connect to HAPI FHIR server: {e}")
