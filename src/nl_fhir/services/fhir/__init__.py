"""
FHIR Services Package for Epic 3
FHIR R4 Resource Creation and Bundle Assembly
HIPAA Compliant: Secure FHIR processing with validation

Note: Avoid importing heavy submodules at package import time to prevent
optional dependency issues during lightweight tests. Import modules directly:
    from nl_fhir.services.fhir.resource_factory import FHIRResourceFactory
    from nl_fhir.services.fhir.bundle_assembler import FHIRBundleAssembler
    from nl_fhir.services.fhir.hapi_client import HAPIFHIRClient
    from nl_fhir.services.fhir.validator import FHIRValidator
"""

__all__ = [
    "resource_factory",
    "bundle_assembler",
    "hapi_client",
    "validator",
]
