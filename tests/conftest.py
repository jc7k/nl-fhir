"""
Test configuration and fixtures for Enhanced Test Suite Modernization
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path for test imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Set environment for testing
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "INFO")

import pytest
from unittest.mock import Mock, patch


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables and configurations"""
    # Ensure test environment is properly configured
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "INFO"

    # Mock external dependencies for factory tests
    with patch('nl_fhir.config.get_settings') as mock_settings:
        # Configure mock settings for factory tests
        mock_settings_obj = Mock()
        mock_settings_obj.use_legacy_factory = False
        mock_settings_obj.factory_debug_logging = False
        mock_settings_obj.enable_factory_metrics = True
        mock_settings_obj.use_new_medication_factory = True
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
    return settings


@pytest.fixture
def sample_patient_data():
    """Sample patient data for testing"""
    return {
        "patient_ref": "Patient/test-patient-123",
        "name": "Test Patient",
        "gender": "male",
        "birthDate": "1990-01-01"
    }


@pytest.fixture
def sample_medication_data():
    """Sample medication data for testing"""
    return {
        "medication_name": "morphine",
        "dosage": "4mg",
        "route": "IV",
        "frequency": "every 4 hours"
    }


@pytest.fixture
def request_id():
    """Sample request ID for testing"""
    return "test-request-123"


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