"""
Tests for AdministrativeResourceFactory (Practitioner, Specimen, Coverage).

Regression: these resource types had no registered factory, so the registry fell
back to MockResourceFactory. The mock Practitioner carried a non-R4 ``status``
element and dropped the name, which made BundleEntry creation fail on every
/convert request; Specimen lacked subject/type and Coverage lacked beneficiary.
"""

import logging

import pytest
from fhir.resources.R4B.coverage import Coverage
from fhir.resources.R4B.practitioner import Practitioner
from fhir.resources.R4B.specimen import Specimen

from nl_fhir.services.fhir.factories import (
    FactoryRegistry,
    MockResourceFactory,
    get_factory_registry,
)
from nl_fhir.services.fhir.factories.administrative_factory import AdministrativeResourceFactory
from nl_fhir.services.fhir.factories.coders import CoderRegistry
from nl_fhir.services.fhir.factories.references import ReferenceManager
from nl_fhir.services.fhir.factories.validators import ValidatorRegistry
from nl_fhir.services.fhir.factory_adapter import get_factory_adapter


@pytest.fixture
def factory():
    return AdministrativeResourceFactory(
        validators=ValidatorRegistry(),
        coders=CoderRegistry(),
        reference_manager=ReferenceManager(),
    )


class TestRegistryWiring:
    def test_supports_only_administrative_types(self, factory):
        assert factory.supports("Practitioner")
        assert factory.supports("Specimen")
        assert factory.supports("Coverage")
        assert not factory.supports("Patient")
        assert not factory.supports("PractitionerRole")

    @pytest.mark.parametrize("resource_type", ["Practitioner", "Specimen", "Coverage"])
    def test_registry_returns_real_factory(self, resource_type):
        registry = get_factory_registry()
        registry.clear_cache()

        assert resource_type in registry._factory_classes
        loaded = registry.get_factory(resource_type)

        assert isinstance(loaded, AdministrativeResourceFactory)
        assert not isinstance(loaded, MockResourceFactory)

    def test_mock_fallback_logs_error_naming_type(self, caplog):
        registry = get_factory_registry()
        registry.clear_cache()

        with caplog.at_level(logging.ERROR, logger="nl_fhir.services.fhir.factories"):
            loaded = registry.get_factory("NoSuchResource")

        assert isinstance(loaded, MockResourceFactory)
        messages = [r.getMessage() for r in caplog.records if r.levelno == logging.ERROR]
        assert any("NoSuchResource" in m and "MockResourceFactory" in m for m in messages)

    def test_cache_hit_does_not_log_fallback(self, caplog):
        registry = FactoryRegistry()
        registry.clear_cache()
        registry.get_factory("Practitioner")

        with caplog.at_level(logging.WARNING, logger="nl_fhir.services.fhir.factories"):
            registry.get_factory("Practitioner")

        assert not [r for r in caplog.records if "MockResourceFactory" in r.getMessage()]


class TestPractitioner:
    def test_basic_practitioner_has_name_and_no_status(self, factory):
        practitioner = factory.create(
            "Practitioner", {"name": "Dr. Jane Smith", "identifier": "temp-practitioner"}, "req-1"
        )

        assert practitioner["resourceType"] == "Practitioner"
        assert "status" not in practitioner
        assert "Mock" not in str(practitioner)
        assert practitioner["active"] is True
        assert practitioner["name"] == [
            {
                "use": "official",
                "text": "Dr. Jane Smith",
                "prefix": ["Dr."],
                "given": ["Jane"],
                "family": "Smith",
            }
        ]
        assert practitioner["identifier"] == [
            {"system": "http://hospital.local/practitioner-id", "value": "temp-practitioner"}
        ]
        Practitioner.model_validate(practitioner)

    def test_npi_telecom_and_qualification(self, factory):
        practitioner = factory.create(
            "Practitioner",
            {
                "name": "John Q Public, MD",
                "npi": "1234567890",
                "qualification": "MD",
                "specialties": ["internal_medicine"],
                "phone": "555-0100",
                "email": "jqp@example.org",
            },
        )

        npi = practitioner["identifier"][0]
        assert npi["system"] == "http://hl7.org/fhir/sid/us-npi"
        assert npi["value"] == "1234567890"
        assert npi["type"]["coding"][0]["code"] == "NPI"

        assert practitioner["name"][0]["suffix"] == ["MD"]
        assert practitioner["name"][0]["family"] == "Public"
        assert practitioner["name"][0]["given"] == ["John", "Q"]

        assert {"system": "phone", "value": "555-0100", "use": "work"} in practitioner["telecom"]
        assert {"system": "email", "value": "jqp@example.org", "use": "work"} in practitioner[
            "telecom"
        ]

        md = practitioner["qualification"][0]["code"]
        assert md["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/v2-0360"
        assert md["coding"][0]["code"] == "MD"
        assert practitioner["qualification"][1]["code"] == {"text": "Internal medicine"}
        Practitioner.model_validate(practitioner)

    def test_structured_name_and_supplied_id(self, factory):
        practitioner = factory.create(
            "Practitioner",
            {
                "id": "prac-1",
                "given": ["Mary"],
                "family": "Jones",
                "prefix": "Dr.",
                "active": False,
            },
        )

        assert practitioner["id"] == "prac-1"
        assert practitioner["active"] is False
        assert practitioner["name"][0]["family"] == "Jones"
        assert practitioner["name"][0]["prefix"] == ["Dr."]
        Practitioner.model_validate(practitioner)

    def test_family_first_name_format(self, factory):
        practitioner = factory.create("Practitioner", {"name": "Smith, John"})

        assert practitioner["name"][0]["family"] == "Smith"
        assert practitioner["name"][0]["given"] == ["John"]
        Practitioner.model_validate(practitioner)


class TestSpecimen:
    def test_specimen_with_snomed_type_and_collection(self, factory):
        specimen = factory.create(
            "Specimen",
            {
                "type": "blood",
                "patient_id": "p1",
                "patient_ref": "Patient/p1",
                "collection": {
                    "collected_date": "2024-02-15T09:00:00Z",
                    "method": "venipuncture",
                    "site": "left_antecubital_fossa",
                },
                "processing": {"procedure": "centrifugation", "temperature": "room_temperature"},
                "status": "available",
                "note": "fasting sample",
            },
            "req-2",
        )

        assert specimen["status"] == "available"
        assert specimen["subject"] == {"reference": "Patient/p1"}
        assert specimen["type"]["coding"][0] == {
            "system": "http://snomed.info/sct",
            "code": "119297000",
            "display": "Blood specimen",
        }
        assert specimen["collection"]["collectedDateTime"] == "2024-02-15T09:00:00Z"
        assert specimen["collection"]["method"]["coding"][0]["code"] == "28520004"
        assert specimen["collection"]["bodySite"] == {"text": "Left antecubital fossa"}
        assert specimen["processing"][0]["procedure"] == {"text": "Centrifugation"}
        assert specimen["note"] == [{"text": "fasting sample"}]
        Specimen.model_validate(specimen)

    def test_minimal_specimen_has_subject(self, factory):
        specimen = factory.create("Specimen", {"patient_ref": "Patient/p1", "patient_id": "p1"})

        assert specimen["subject"] == {"reference": "Patient/p1"}
        assert specimen["status"] == "available"
        assert "type" not in specimen
        Specimen.model_validate(specimen)

    def test_unknown_type_becomes_text_and_bare_patient_id_is_typed(self, factory):
        specimen = factory.create(
            "Specimen", {"specimen_type": "mystery fluid", "patient_id": "abc"}
        )

        assert specimen["type"] == {"text": "mystery fluid"}
        assert specimen["subject"] == {"reference": "Patient/abc"}
        Specimen.model_validate(specimen)

    def test_naive_collection_time_gets_timezone(self, factory):
        specimen = factory.create(
            "Specimen",
            {"type": "urine", "patient_id": "p1", "collected_date": "2024-02-15T09:00:00"},
        )

        assert specimen["collection"]["collectedDateTime"] == "2024-02-15T09:00:00Z"
        Specimen.model_validate(specimen)


class TestCoverage:
    def test_coverage_with_payor_type_and_period(self, factory):
        coverage = factory.create(
            "Coverage",
            {
                "type": "medical",
                "status": "active",
                "payor": {"id": "fhir-r4-insurance", "name": "FHIR R4 Test Insurance"},
                "plan_class": "individual",
                "member_id": "FHIR123456",
                "effective_period": {"start": "2024-01-01", "end": "2024-12-31"},
                "patient_id": "p1",
                "patient_ref": "Patient/p1",
            },
            "req-3",
        )

        assert coverage["status"] == "active"
        assert coverage["beneficiary"] == {"reference": "Patient/p1"}
        assert coverage["payor"] == [
            {"reference": "Organization/fhir-r4-insurance", "display": "FHIR R4 Test Insurance"}
        ]
        assert coverage["type"]["coding"][0]["code"] == "EHCPOL"
        assert coverage["subscriberId"] == "FHIR123456"
        assert coverage["subscriber"] == {"reference": "Patient/p1"}
        assert coverage["period"] == {"start": "2024-01-01", "end": "2024-12-31"}
        assert coverage["class"][0]["value"] == "individual"
        Coverage.model_validate(coverage)

    def test_minimal_coverage_has_beneficiary_status_and_payor(self, factory):
        coverage = factory.create("Coverage", {"patient_ref": "Patient/p1", "patient_id": "p1"})

        assert coverage["beneficiary"] == {"reference": "Patient/p1"}
        assert coverage["status"] == "active"
        assert coverage["payor"] == [{"display": "Unknown payor"}]
        Coverage.model_validate(coverage)

    def test_payor_aliases_and_identifier(self, factory):
        coverage = factory.create(
            "Coverage",
            {
                "patient_id": "p1",
                "payer": "Acme Health",
                "policy_number": "POL-77",
                "group_number": "G-1",
                "status": "inactive",
            },
        )

        assert coverage["payor"] == [{"display": "Acme Health"}]
        assert coverage["identifier"][0]["value"] == "POL-77"
        assert coverage["class"][0]["type"]["coding"][0]["code"] == "group"
        assert coverage["status"] == "cancelled"
        Coverage.model_validate(coverage)


class TestAdapterIntegration:
    """The FactoryAdapter is what conversion.py and the legacy tests call."""

    def test_adapter_practitioner_is_real_and_valid(self):
        adapter = get_factory_adapter()
        practitioner = adapter.create_practitioner_resource(
            {"name": "Unknown Practitioner", "identifier": "temp-practitioner"}, "req-4"
        )

        assert "status" not in practitioner
        assert "Mock" not in str(practitioner)
        assert practitioner["name"][0]["family"] == "Practitioner"
        assert practitioner["meta"]["tag"][0]["code"] == "AdministrativeResourceFactory"
        Practitioner.model_validate(practitioner)

    @pytest.mark.parametrize(
        "patient_ref", ["Patient/p1", "p1", "InvalidReference", "Patient/", ""]
    )
    def test_adapter_specimen_and_coverage_always_reference_a_patient(self, patient_ref):
        adapter = get_factory_adapter()

        specimen = adapter.create_specimen_resource({"type": "blood"}, patient_ref)
        coverage = adapter.create_coverage_resource({"payor": "invalid_format"}, patient_ref)

        assert specimen["subject"]["reference"].startswith("Patient/")
        assert coverage["beneficiary"]["reference"].startswith("Patient/")
        Specimen.model_validate(specimen)
        Coverage.model_validate(coverage)
