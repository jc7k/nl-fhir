"""
Test configuration and fixtures for Enhanced Test Suite Modernization
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path for test imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Set environment for testing
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "INFO")

from unittest.mock import Mock, patch

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables and configurations"""
    # Ensure test environment is properly configured
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "INFO"

    # Mock external dependencies for factory tests
    with patch("nl_fhir.services.fhir.factories.get_settings") as mock_settings:
        # Configure mock settings for factory tests
        mock_settings_obj = Mock()
        mock_settings_obj.use_legacy_factory = False
        mock_settings_obj.factory_debug_logging = False
        mock_settings_obj.enable_factory_metrics = True
        mock_settings_obj.use_new_medication_factory = True
        mock_settings_obj.use_new_patient_factory = True
        mock_settings_obj.use_new_clinical_factory = True
        mock_settings_obj.use_new_careplan_factory = True
        mock_settings_obj.use_new_encounter_factory = True
        mock_settings.return_value = mock_settings_obj

        yield mock_settings_obj


@pytest.fixture
def mock_factory_settings():
    """Mock factory settings for consistent testing"""
    settings = Mock()
    settings.use_legacy_factory = False
    settings.factory_debug_logging = False
    settings.enable_factory_metrics = True
    settings.use_new_medication_factory = True
    settings.use_new_patient_factory = True
    settings.use_new_clinical_factory = True
    settings.use_new_careplan_factory = True
    settings.use_new_encounter_factory = True
    return settings


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "patient_ref": "Patient/test-patient-123",
        "name": "Test Patient",
        "gender": "male",
        "birthDate": "1990-01-01",
    }


@pytest.fixture
def sample_medication_data():
    """Sample medication data for testing"""
    return {
        "medication_name": "morphine",
        "dosage": "4mg",
        "route": "IV",
        "frequency": "every 4 hours",
    }


@pytest.fixture
def request_id():
    """Sample request ID for testing"""
    return "test-request-123"


@pytest.fixture(scope="session")
def mock_clinical_structure():
    """Mock ClinicalStructure response from Instructor LLM"""
    from nl_fhir.services.nlp.llm.models.clinical_models import ClinicalSetting
    from nl_fhir.services.nlp.llm.models.medication_models import MedicationOrder, MedicationRoute
    from nl_fhir.services.nlp.llm.models.procedure_models import UrgencyLevel
    from nl_fhir.services.nlp.llm.models.response_models import ClinicalStructure

    return ClinicalStructure(
        medications=[
            MedicationOrder(
                name="metformin",
                dosage="500mg",
                frequency="twice daily",
                route=MedicationRoute.ORAL,
                indication="diabetes management",
                duration="ongoing",
                safety_flag=False,
            )
        ],
        lab_tests=[],
        procedures=[],
        conditions=[],
        patients=[],
        clinical_instructions=["Take with food"],
        urgency_level=UrgencyLevel.ROUTINE,
        clinical_setting=ClinicalSetting.OUTPATIENT,
        patient_safety_alerts=[],
    )


@pytest.fixture(scope="session")
def mock_openai_env():
    """Set mock OpenAI API key for testing to prevent real API calls"""
    old_api_key = os.environ.get("OPENAI_API_KEY")
    # Set a fake API key to enable mocking
    os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-testing"

    yield

    # Restore original API key
    if old_api_key:
        os.environ["OPENAI_API_KEY"] = old_api_key
    else:
        os.environ.pop("OPENAI_API_KEY", None)


@pytest.fixture(scope="session", autouse=True)
def mock_instructor_processor(mock_clinical_structure, mock_openai_env):
    """Mock InstructorProcessor to avoid real OpenAI API calls

    This fixture patches at the OpenAI client level to intercept API calls
    before they're made over the network.

    IMPORTANT: autouse=True ensures this patch is applied globally BEFORE any
    test executes, preventing real API calls even if OPENAI_API_KEY is set
    in the environment. This guarantees deterministic, offline test execution.
    """
    # Mock at the openai.OpenAI client level to intercept chat.completions.create
    with patch("openai.OpenAI") as mock_openai_class:
        # Create mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.model_dump.return_value = mock_clinical_structure.model_dump()

        # Mock the chat completions create method
        mock_client.chat.completions.create.return_value = mock_response

        # Return the mock client when OpenAI() is instantiated
        mock_openai_class.return_value = mock_client

        # Also patch instructor.from_openai to return a properly structured mock
        with patch("instructor.from_openai") as mock_from_openai:
            # Create a mock instructor client that has the same structure
            mock_instructor_client = Mock()
            mock_instructor_client.chat.completions.create.return_value = mock_response

            mock_from_openai.return_value = mock_instructor_client

            yield mock_instructor_client


# Performance testing configuration
# pytest_plugins = ["pytest_benchmark"]  # Not installed, commented out


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "factory: marks tests as factory tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on path"""
    for item in items:
        # Add markers based on test path
        if "factories" in str(item.fspath):
            item.add_marker(pytest.mark.factory)
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
