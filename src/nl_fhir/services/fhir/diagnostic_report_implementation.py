"""
DiagnosticReport FHIR Resource Implementation
Story ID: NL-FHIR-DR-001
Creates FHIR R4 DiagnosticReport resources from clinical text
HIPAA Compliant: Secure resource creation with validation
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4

logger = logging.getLogger(__name__)

class DiagnosticReportFactory:
    """Factory for creating FHIR R4 DiagnosticReport resources"""

    # Category mappings for diagnostic report types
    CATEGORY_MAPPINGS = {
        "laboratory": {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
            "code": "LAB",
            "display": "Laboratory"
        },
        "radiology": {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
            "code": "RAD",
            "display": "Radiology"
        },
        "pathology": {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
            "code": "PAT",
            "display": "Pathology"
        },
        "cardiology": {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
            "code": "CUS",
            "display": "Cardiology"
        },
        "imaging": {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
            "code": "IMG",
            "display": "Imaging"
        }
    }

    # Common LOINC codes for diagnostic procedures
    LOINC_CODES = {
        "cbc": {"code": "58410-2", "display": "Complete blood count (hemogram) panel"},
        "metabolic_panel": {"code": "24323-8", "display": "Comprehensive metabolic panel"},
        "lipid_panel": {"code": "57698-3", "display": "Lipid panel"},
        "liver_panel": {"code": "24325-3", "display": "Hepatic function panel"},
        "thyroid_panel": {"code": "55204-3", "display": "Thyroid panel"},
        "urinalysis": {"code": "24357-6", "display": "Urinalysis complete"},
        "chest_xray": {"code": "36643-5", "display": "Chest X-ray"},
        "ct_scan": {"code": "24558-9", "display": "CT scan"},
        "mri": {"code": "36801-9", "display": "MRI"},
        "ecg": {"code": "11524-6", "display": "Electrocardiogram"},
        "echo": {"code": "34552-0", "display": "Echocardiogram"},
        "biopsy": {"code": "50398-7", "display": "Pathology report"}
    }

    def create_diagnostic_report(self,
                                report_data: Dict[str, Any],
                                patient_ref: str,
                                request_id: Optional[str] = None,
                                service_request_refs: Optional[List[str]] = None,
                                observation_refs: Optional[List[str]] = None,
                                practitioner_ref: Optional[str] = None,
                                encounter_ref: Optional[str] = None) -> Dict[str, Any]:
        """
        Create FHIR R4 DiagnosticReport resource

        Args:
            report_data: Diagnostic report information from NLP extraction
            patient_ref: Patient reference ID
            request_id: Request tracking ID
            service_request_refs: List of related ServiceRequest references
            observation_refs: List of related Observation references
            practitioner_ref: Performing practitioner reference
            encounter_ref: Related encounter reference

        Returns:
            FHIR DiagnosticReport resource as dict
        """

        report_id = self._generate_resource_id("DiagnosticReport")
        logger.info(f"[{request_id}] Creating DiagnosticReport: {report_id}")

        try:
            # Determine report category and status
            category = self._determine_category(report_data)
            status = self._determine_status(report_data)

            # Create base DiagnosticReport structure
            diagnostic_report = {
                "resourceType": "DiagnosticReport",
                "id": report_id,
                "status": status,
                "category": [self._create_category_coding(category)],
                "code": self._create_report_code(report_data),
                "subject": {
                    "reference": f"Patient/{patient_ref}"
                },
                "effectiveDateTime": self._get_effective_datetime(report_data)
            }

            # Add basedOn references to ServiceRequests if available
            if service_request_refs:
                diagnostic_report["basedOn"] = [
                    {"reference": f"ServiceRequest/{ref}"} for ref in service_request_refs
                ]

            # Add result references to Observations if available
            if observation_refs:
                diagnostic_report["result"] = [
                    {"reference": f"Observation/{ref}"} for ref in observation_refs
                ]

            # Add encounter reference if available
            if encounter_ref:
                diagnostic_report["encounter"] = {
                    "reference": f"Encounter/{encounter_ref}"
                }

            # Add performer if available
            if practitioner_ref:
                diagnostic_report["performer"] = [{
                    "reference": f"Practitioner/{practitioner_ref}"
                }]
            elif report_data.get("performer_organization"):
                diagnostic_report["performer"] = [{
                    "reference": f"Organization/{report_data['performer_organization']}"
                }]

            # Add clinical conclusion if available
            conclusion = self._extract_conclusion(report_data)
            if conclusion:
                diagnostic_report["conclusion"] = conclusion

            # Add interpretation if available
            interpretation = self._extract_interpretation(report_data)
            if interpretation:
                diagnostic_report["conclusionCode"] = [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": interpretation["code"],
                        "display": interpretation["display"]
                    }]
                }]

            # Add media if imaging report
            if category in ["radiology", "imaging"] and report_data.get("media"):
                diagnostic_report["media"] = self._create_media_references(report_data["media"])

            # Add presented form if report document available
            if report_data.get("document_reference"):
                diagnostic_report["presentedForm"] = [{
                    "contentType": "application/pdf",
                    "url": report_data["document_reference"]
                }]

            logger.info(f"[{request_id}] DiagnosticReport {report_id} created successfully")
            return diagnostic_report

        except Exception as e:
            logger.error(f"[{request_id}] Failed to create DiagnosticReport: {e}")
            # Fallback to simplified version
            return self._create_fallback_diagnostic_report(
                report_data, patient_ref, request_id,
                service_request_refs, observation_refs
            )

    def _create_fallback_diagnostic_report(self,
                                          report_data: Dict[str, Any],
                                          patient_ref: str,
                                          request_id: Optional[str],
                                          service_request_refs: Optional[List[str]] = None,
                                          observation_refs: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create simplified fallback DiagnosticReport for HAPI compatibility"""

        report_id = self._generate_resource_id("DiagnosticReport")
        report_text = (
            report_data.get("text") or
            report_data.get("name") or
            report_data.get("procedure") or
            "Diagnostic report"
        )

        fallback_report = {
            "resourceType": "DiagnosticReport",
            "id": report_id,
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "LAB",
                    "display": "Laboratory"
                }]
            }],
            "code": {
                "text": report_text
            },
            "subject": {
                "reference": f"Patient/{patient_ref}"
            },
            "effectiveDateTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        }

        # Add references if available
        if service_request_refs:
            fallback_report["basedOn"] = [
                {"reference": f"ServiceRequest/{ref}"} for ref in service_request_refs
            ]

        if observation_refs:
            fallback_report["result"] = [
                {"reference": f"Observation/{ref}"} for ref in observation_refs
            ]

        # Add conclusion if available
        if report_data.get("conclusion") or report_data.get("interpretation"):
            fallback_report["conclusion"] = (
                report_data.get("conclusion") or
                report_data.get("interpretation") or
                report_data.get("findings", "Results reported")
            )

        return fallback_report

    def _determine_category(self, report_data: Dict[str, Any]) -> str:
        """Determine diagnostic report category from clinical text patterns"""

        text = (report_data.get("text", "") + " " +
                report_data.get("procedure", "") + " " +
                report_data.get("type", "")).lower()

        # Pattern matching for category detection
        if any(term in text for term in ["lab", "blood", "urine", "culture", "panel"]):
            return "laboratory"
        elif any(term in text for term in ["xray", "x-ray", "ct", "mri", "scan", "imaging"]):
            return "radiology"
        elif any(term in text for term in ["biopsy", "cytology", "histology", "pathology"]):
            return "pathology"
        elif any(term in text for term in ["ecg", "ekg", "echo", "cardiac", "stress test"]):
            return "cardiology"
        else:
            return "laboratory"  # Default to laboratory

    def _determine_status(self, report_data: Dict[str, Any]) -> str:
        """Determine report status from clinical text"""

        text = str(report_data.get("text", "")).lower()

        if "preliminary" in text or "pending" in text:
            return "preliminary"
        elif "amended" in text or "corrected" in text:
            return "amended"
        elif "cancelled" in text or "canceled" in text:
            return "cancelled"
        else:
            return "final"

    def _create_category_coding(self, category: str) -> Dict[str, Any]:
        """Create category coding based on report type"""

        if category in self.CATEGORY_MAPPINGS:
            mapping = self.CATEGORY_MAPPINGS[category]
            return {
                "coding": [{
                    "system": mapping["system"],
                    "code": mapping["code"],
                    "display": mapping["display"]
                }]
            }
        else:
            return {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "OTH",
                    "display": "Other"
                }]
            }

    def _create_report_code(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create diagnostic report code with LOINC coding when identifiable"""

        procedure_name = (
            report_data.get("procedure") or
            report_data.get("test") or
            report_data.get("name") or
            "Diagnostic report"
        )

        # Try to match known LOINC codes
        procedure_lower = procedure_name.lower()
        loinc_code = None

        for key, value in self.LOINC_CODES.items():
            if key.replace("_", " ") in procedure_lower:
                loinc_code = value
                break

        if loinc_code:
            return {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": loinc_code["code"],
                    "display": loinc_code["display"]
                }],
                "text": procedure_name
            }
        else:
            return {
                "text": procedure_name
            }

    def _extract_conclusion(self, report_data: Dict[str, Any]) -> Optional[str]:
        """Extract clinical conclusion from report data"""

        # Check multiple fields for conclusion
        conclusion = (
            report_data.get("conclusion") or
            report_data.get("impression") or
            report_data.get("findings") or
            report_data.get("interpretation")
        )

        if conclusion:
            return str(conclusion)

        # Try to extract from text
        text = report_data.get("text", "")
        conclusion_markers = ["conclusion:", "impression:", "findings:", "interpretation:"]

        for marker in conclusion_markers:
            if marker in text.lower():
                start_idx = text.lower().index(marker) + len(marker)
                # Extract up to next section or end of text
                conclusion_text = text[start_idx:].strip()
                if len(conclusion_text) > 0:
                    # Limit to first sentence or 200 chars
                    end_idx = min(
                        conclusion_text.find(".") + 1 if "." in conclusion_text else 200,
                        200
                    )
                    return conclusion_text[:end_idx].strip()

        return None

    def _extract_interpretation(self, report_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract clinical interpretation codes"""

        text = str(report_data.get("text", "")).lower()
        interpretation_text = str(report_data.get("interpretation", "")).lower()
        combined_text = f"{text} {interpretation_text}"

        # Map text patterns to interpretation codes
        if any(term in combined_text for term in ["normal", "within normal limits", "unremarkable"]):
            return {"code": "N", "display": "Normal"}
        elif any(term in combined_text for term in ["abnormal", "elevated", "high", "increased"]):
            return {"code": "H", "display": "High"}
        elif any(term in combined_text for term in ["low", "decreased", "reduced"]):
            return {"code": "L", "display": "Low"}
        elif any(term in combined_text for term in ["critical", "panic", "urgent"]):
            return {"code": "HH", "display": "Critical high"}

        return None

    def _get_effective_datetime(self, report_data: Dict[str, Any]) -> str:
        """Get effective date/time for the report"""

        if report_data.get("datetime"):
            # Parse datetime field (could be various formats)
            datetime_str = report_data["datetime"]
            try:
                from datetime import datetime as dt
                if "/" in datetime_str:  # MM/DD/YYYY format
                    parsed_date = dt.strptime(datetime_str, "%m/%d/%Y")
                    return parsed_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                elif "-" in datetime_str:  # YYYY-MM-DD format
                    parsed_date = dt.strptime(datetime_str, "%Y-%m-%d")
                    return parsed_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                else:
                    # If it's already in ISO format, return as is
                    return datetime_str
            except ValueError:
                # If parsing fails, use current time
                return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        elif report_data.get("date"):
            # Parse various date formats and convert to ISO
            date_str = report_data["date"]
            try:
                # Try parsing common formats
                from datetime import datetime as dt
                if "/" in date_str:  # MM/DD/YYYY format
                    parsed_date = dt.strptime(date_str, "%m/%d/%Y")
                elif "-" in date_str:  # YYYY-MM-DD format
                    parsed_date = dt.strptime(date_str, "%Y-%m-%d")
                else:
                    # If parsing fails, use current date
                    parsed_date = dt.now(timezone.utc)
                return parsed_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                # If parsing fails, use current date
                return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def _create_media_references(self, media_data: Any) -> List[Dict[str, Any]]:
        """Create media references for imaging reports"""

        if isinstance(media_data, list):
            return [{"reference": f"Media/{item}"} for item in media_data]
        elif isinstance(media_data, str):
            return [{"reference": f"Media/{media_data}"}]
        else:
            return []

    def _generate_resource_id(self, resource_type: str) -> str:
        """Generate unique resource ID"""
        return f"{resource_type.lower()}-{str(uuid4())[:8]}"


# Integration with existing FHIRResourceFactory
def integrate_diagnostic_report(resource_factory_instance):
    """
    Add DiagnosticReport creation method to existing FHIRResourceFactory
    This should be added to resource_factory.py
    """

    diagnostic_factory = DiagnosticReportFactory()

    # Add method to existing factory class
    resource_factory_instance.create_diagnostic_report = diagnostic_factory.create_diagnostic_report
    resource_factory_instance._create_fallback_diagnostic_report = diagnostic_factory._create_fallback_diagnostic_report

    # Copy helper methods
    for attr_name in dir(diagnostic_factory):
        if attr_name.startswith('_') and not attr_name.startswith('__'):
            attr_value = getattr(diagnostic_factory, attr_name)
            if callable(attr_value) and attr_name not in ['_generate_resource_id']:
                setattr(resource_factory_instance, attr_name, attr_value)

    # Copy class attributes
    resource_factory_instance.DIAGNOSTIC_CATEGORY_MAPPINGS = diagnostic_factory.CATEGORY_MAPPINGS
    resource_factory_instance.DIAGNOSTIC_LOINC_CODES = diagnostic_factory.LOINC_CODES

    return resource_factory_instance