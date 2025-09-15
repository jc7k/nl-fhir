"""
Resource Summarizer Registry for Epic 4 Adaptive Framework
Extensible registry for rule-based resource processing
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Set, Any
from datetime import datetime

from .models import ClinicalOrder, ProcessingTier


class BaseResourceSummarizer(ABC):
    """
    Abstract base class for all rule-based resource summarizers
    Ensures consistent interface and behavior across implementations
    """
    
    def __init__(self):
        self.supported_resource_types = self._get_supported_resource_types()
        self.clinical_templates = self._load_clinical_templates()
    
    @abstractmethod
    def _get_supported_resource_types(self) -> Set[str]:
        """Return set of FHIR resource types this summarizer supports"""
        pass
    
    @abstractmethod
    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        """Generate clinical order summary for FHIR resource"""
        pass
    
    def supports_resource_type(self, resource_type: str) -> bool:
        """Check if summarizer supports given FHIR resource type"""
        return resource_type in self.supported_resource_types
    
    def _load_clinical_templates(self) -> Dict[str, str]:
        """Load clinical language templates - override in subclasses"""
        return {}
    
    def _extract_coding_display(self, coding: Dict[str, Any]) -> str:
        """Utility to extract human-readable display from FHIR Coding"""
        if isinstance(coding, dict):
            if coding.get('display'):
                return coding['display']
            elif coding.get('code'):
                # Simple fallback - in production would use terminology mapping
                return coding['code'].replace('_', ' ').title()
        return "Unknown"
    
    def _extract_code_text(self, resource: Dict[str, Any], field_name: str = 'code') -> str:
        """Extract readable text from FHIR CodeableConcept"""
        code_field = resource.get(field_name, {})
        
        if isinstance(code_field, dict):
            # Try text field first
            if code_field.get('text'):
                return code_field['text']
            
            # Try coding array
            coding = code_field.get('coding', [])
            if isinstance(coding, list) and len(coding) > 0:
                return self._extract_coding_display(coding[0])
        
        return "Unknown"


class MedicationSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for MedicationRequest resources"""
    
    def _get_supported_resource_types(self) -> Set[str]:
        return {"MedicationRequest"}
    
    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        """Generate medication order summary"""
        
        # Extract medication name
        medication_name = self._extract_medication_name(fhir_resource)
        
        # Extract dosage information
        dosage_info = self._extract_dosage_info(fhir_resource)
        
        # Generate clinical description
        description_parts = [f"Prescribe {medication_name}"]
        if dosage_info['dose']:
            description_parts.append(dosage_info['dose'])
        if dosage_info['route']:
            description_parts.append(f"via {dosage_info['route']}")
        if dosage_info['frequency']:
            description_parts.append(dosage_info['frequency'])
        
        description = " ".join(description_parts)
        
        # Determine priority
        priority = self._extract_priority(fhir_resource)
        
        return ClinicalOrder(
            order_type="medication",
            description=description,
            priority=priority,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.95,
            clinical_rationale=self._extract_clinical_rationale(fhir_resource)
        )
    
    def _extract_medication_name(self, resource: Dict[str, Any]) -> str:
        """Extract medication name from MedicationRequest"""
        # Try medicationCodeableConcept first
        med_concept = resource.get('medicationCodeableConcept')
        if med_concept:
            return self._extract_code_text({'code': med_concept})
        
        # Try medication reference (simplified)
        med_ref = resource.get('medication', {})
        if isinstance(med_ref, dict):
            return self._extract_code_text(med_ref)
        
        return "Unknown medication"
    
    def _extract_dosage_info(self, resource: Dict[str, Any]) -> Dict[str, str]:
        """Extract dosage, route, and frequency information"""
        dosage_instruction = resource.get('dosageInstruction', [])
        
        result = {'dose': '', 'route': '', 'frequency': ''}
        
        if isinstance(dosage_instruction, list) and len(dosage_instruction) > 0:
            dosage = dosage_instruction[0]
            
            # Extract dose quantity
            dose_quantity = dosage.get('doseAndRate', [{}])[0].get('doseQuantity', {})
            if dose_quantity.get('value') and dose_quantity.get('unit'):
                result['dose'] = f"{dose_quantity['value']} {dose_quantity['unit']}"
            
            # Extract route
            route = dosage.get('route', {})
            if route:
                result['route'] = self._extract_code_text({'code': route})
            
            # Extract timing/frequency
            timing = dosage.get('timing', {})
            if timing:
                result['frequency'] = self._extract_frequency_text(timing)
        
        return result
    
    def _extract_frequency_text(self, timing: Dict[str, Any]) -> str:
        """Convert FHIR timing to readable frequency"""
        repeat = timing.get('repeat', {})
        
        if repeat.get('frequency') and repeat.get('period'):
            freq = repeat['frequency']
            period = repeat['period']
            period_unit = repeat.get('periodUnit', 'day')
            
            if freq == 1 and period == 1:
                if period_unit == 'day':
                    return "once daily"
                elif period_unit == 'hour':
                    return "every hour"
            elif freq == 2 and period == 1 and period_unit == 'day':
                return "twice daily"
            elif freq == 3 and period == 1 and period_unit == 'day':
                return "three times daily"
            
            return f"{freq} times per {period} {period_unit}{'s' if period > 1 else ''}"
        
        # Try code field for common frequencies
        code = timing.get('code', {})
        if code:
            code_text = self._extract_code_text({'code': code})
            if code_text and code_text != "Unknown":
                return code_text.lower()
        
        return ""
    
    def _extract_priority(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract priority from MedicationRequest"""
        priority = resource.get('priority')
        if priority:
            return priority.lower()
        return None
    
    def _extract_clinical_rationale(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract clinical reasoning if available"""
        reason_code = resource.get('reasonCode', [])
        if isinstance(reason_code, list) and len(reason_code) > 0:
            return self._extract_code_text({'code': reason_code[0]})
        
        reason_reference = resource.get('reasonReference', [])
        if isinstance(reason_reference, list) and len(reason_reference) > 0:
            # In a full implementation, would resolve the reference
            return "For documented clinical indication"
        
        return None


class ServiceRequestSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for ServiceRequest resources (labs, procedures)"""
    
    def _get_supported_resource_types(self) -> Set[str]:
        return {"ServiceRequest"}
    
    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        """Generate service request order summary"""
        
        # Extract service/test name
        service_name = self._extract_code_text(fhir_resource, 'code')
        
        # Classify service type
        service_type = self._classify_service_type(fhir_resource)
        
        # Generate description based on service type
        if service_type == "laboratory":
            description = f"Order laboratory test: {service_name}"
        elif service_type == "imaging":
            description = f"Order imaging study: {service_name}"
        elif service_type == "procedure":
            description = f"Schedule procedure: {service_name}"
        else:
            description = f"Order clinical service: {service_name}"
        
        # Extract priority
        priority = self._extract_priority(fhir_resource)
        
        return ClinicalOrder(
            order_type="service_request",
            description=description,
            priority=priority,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.90,
            clinical_rationale=self._extract_clinical_rationale(fhir_resource)
        )
    
    def _classify_service_type(self, resource: Dict[str, Any]) -> str:
        """Classify service request type based on category or code"""
        category = resource.get('category', [])
        
        if isinstance(category, list) and len(category) > 0:
            category_text = self._extract_code_text({'code': category[0]}).lower()
            
            if 'lab' in category_text or 'laboratory' in category_text:
                return "laboratory"
            elif 'imaging' in category_text or 'radiology' in category_text:
                return "imaging"
            elif 'procedure' in category_text:
                return "procedure"
        
        # Try to infer from code
        code_text = self._extract_code_text(resource, 'code').lower()
        if any(term in code_text for term in ['blood', 'urine', 'lab', 'test']):
            return "laboratory"
        elif any(term in code_text for term in ['ct', 'mri', 'x-ray', 'ultrasound', 'scan']):
            return "imaging"
        elif any(term in code_text for term in ['biopsy', 'surgery', 'procedure']):
            return "procedure"
        
        return "general"
    
    def _extract_priority(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract priority from ServiceRequest"""
        priority = resource.get('priority')
        if priority:
            return priority.lower()
        return None
    
    def _extract_clinical_rationale(self, resource: Dict[str, Any]) -> Optional[str]:
        """Extract clinical reasoning if available"""
        reason_code = resource.get('reasonCode', [])
        if isinstance(reason_code, list) and len(reason_code) > 0:
            return self._extract_code_text({'code': reason_code[0]})
        return None


class ConditionSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for Condition resources"""

    def _get_supported_resource_types(self) -> Set[str]:
        return {"Condition"}

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        condition_name = self._extract_code_text(fhir_resource, 'code')
        clinical_status = fhir_resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'unknown')
        verification_status = fhir_resource.get('verificationStatus', {}).get('coding', [{}])[0].get('code', 'unknown')

        # Determine description based on status
        if clinical_status == 'active':
            description = f"Active diagnosis: {condition_name}"
        elif clinical_status == 'resolved':
            description = f"Resolved condition: {condition_name}"
        elif clinical_status == 'inactive':
            description = f"Inactive diagnosis: {condition_name}"
        else:
            description = f"Clinical condition: {condition_name}"

        if verification_status == 'provisional':
            description += " (provisional)"
        elif verification_status == 'differential':
            description += " (differential diagnosis)"

        return ClinicalOrder(
            order_type="condition",
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.93,
            clinical_rationale=f"Status: {clinical_status}, Verification: {verification_status}"
        )


class ObservationSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for Observation resources"""

    def _get_supported_resource_types(self) -> Set[str]:
        return {"Observation"}

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        observation_name = self._extract_code_text(fhir_resource, 'code')
        status = fhir_resource.get('status', 'unknown')

        # Extract value
        value_text = self._extract_observation_value(fhir_resource)

        if status == 'final':
            description = f"Final result: {observation_name}"
        elif status == 'preliminary':
            description = f"Preliminary result: {observation_name}"
        else:
            description = f"Observation: {observation_name}"

        if value_text:
            description += f" = {value_text}"

        return ClinicalOrder(
            order_type="observation",
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.92,
            clinical_rationale=f"Status: {status}"
        )

    def _extract_observation_value(self, resource: Dict[str, Any]) -> str:
        """Extract observation value in human-readable format"""
        if 'valueQuantity' in resource:
            qty = resource['valueQuantity']
            value = qty.get('value', '')
            unit = qty.get('unit', qty.get('code', ''))
            return f"{value} {unit}".strip()
        elif 'valueString' in resource:
            return resource['valueString']
        elif 'valueCodeableConcept' in resource:
            return self._extract_code_text({'code': resource['valueCodeableConcept']})
        elif 'valueBoolean' in resource:
            return "Yes" if resource['valueBoolean'] else "No"
        elif 'component' in resource:
            components = []
            for comp in resource['component'][:3]:  # Limit to first 3 components
                comp_code = self._extract_code_text(comp, 'code')
                comp_value = self._extract_observation_value(comp)
                if comp_value:
                    components.append(f"{comp_code}: {comp_value}")
            return "; ".join(components)
        return ""


class ProcedureSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for Procedure resources"""

    def _get_supported_resource_types(self) -> Set[str]:
        return {"Procedure"}

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        procedure_name = self._extract_code_text(fhir_resource, 'code')
        status = fhir_resource.get('status', 'unknown')

        if status == 'completed':
            description = f"Completed procedure: {procedure_name}"
        elif status == 'in-progress':
            description = f"Procedure in progress: {procedure_name}"
        elif status == 'preparation':
            description = f"Procedure preparation: {procedure_name}"
        else:
            description = f"Procedure ({status}): {procedure_name}"

        # Add performed date if available
        performed = fhir_resource.get('performedDateTime')
        if performed:
            description += f" on {performed[:10]}"  # Just date part

        return ClinicalOrder(
            order_type="procedure",
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.91,
            clinical_rationale=f"Status: {status}"
        )


class DiagnosticReportSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for DiagnosticReport resources"""

    def _get_supported_resource_types(self) -> Set[str]:
        return {"DiagnosticReport"}

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        report_name = self._extract_code_text(fhir_resource, 'code')
        status = fhir_resource.get('status', 'unknown')
        category = fhir_resource.get('category', [{}])[0] if fhir_resource.get('category') else {}
        category_text = self._extract_code_text({'code': category}) if category else ""

        if status == 'final':
            description = f"Final diagnostic report: {report_name}"
        elif status == 'preliminary':
            description = f"Preliminary report: {report_name}"
        else:
            description = f"Diagnostic report ({status}): {report_name}"

        if category_text and category_text != "Unknown":
            description += f" ({category_text})"

        # Add conclusion if available
        conclusion = fhir_resource.get('conclusion')
        if conclusion and len(conclusion) < 100:
            description += f" - {conclusion}"

        return ClinicalOrder(
            order_type="diagnostic_report",
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.90,
            clinical_rationale=f"Status: {status}, Category: {category_text}"
        )


class PatientSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for Patient resources"""

    def _get_supported_resource_types(self) -> Set[str]:
        return {"Patient"}

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        # Extract basic demographics (non-PHI)
        active = fhir_resource.get('active', True)
        gender = fhir_resource.get('gender', 'unknown')
        birth_date = fhir_resource.get('birthDate', '')

        description = "Patient record"
        details = []

        if not active:
            details.append("inactive")

        if gender != 'unknown':
            details.append(f"gender: {gender}")

        if birth_date:
            # Calculate age without exposing exact birth date
            from datetime import datetime
            try:
                birth_year = int(birth_date[:4])
                current_year = datetime.now().year
                age = current_year - birth_year
                details.append(f"age: ~{age}")
            except:
                pass

        if details:
            description += f" ({', '.join(details)})"

        return ClinicalOrder(
            order_type="patient",
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.95,
            clinical_rationale="Patient demographic information"
        )


class EncounterSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for Encounter resources"""

    def _get_supported_resource_types(self) -> Set[str]:
        return {"Encounter"}

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        status = fhir_resource.get('status', 'unknown')
        encounter_class = fhir_resource.get('class', {}).get('code', 'unknown')
        encounter_type = fhir_resource.get('type', [{}])[0] if fhir_resource.get('type') else {}
        type_text = self._extract_code_text({'code': encounter_type}) if encounter_type else ""

        # Map class codes to readable descriptions
        class_mapping = {
            'AMB': 'ambulatory',
            'EMER': 'emergency',
            'IMP': 'inpatient',
            'OBSENC': 'observation',
            'PRENC': 'pre-admission'
        }

        class_text = class_mapping.get(encounter_class, encounter_class)

        description = f"Healthcare encounter ({status})"
        if class_text != 'unknown':
            description += f" - {class_text}"
        if type_text and type_text != "Unknown":
            description += f": {type_text}"

        return ClinicalOrder(
            order_type="encounter",
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.88,
            clinical_rationale=f"Status: {status}, Class: {class_text}"
        )


class CarePlanSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for CarePlan resources"""

    def _get_supported_resource_types(self) -> Set[str]:
        return {"CarePlan"}

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        status = fhir_resource.get('status', 'unknown')
        intent = fhir_resource.get('intent', 'unknown')
        title = fhir_resource.get('title', '')
        category = fhir_resource.get('category', [{}])[0] if fhir_resource.get('category') else {}
        category_text = self._extract_code_text({'code': category}) if category else ""

        if title:
            description = f"Care plan: {title}"
        elif category_text and category_text != "Unknown":
            description = f"Care plan ({category_text})"
        else:
            description = "Care plan"

        description += f" - {status}"
        if intent != 'unknown':
            description += f", {intent}"

        return ClinicalOrder(
            order_type="care_plan",
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.87,
            clinical_rationale=f"Status: {status}, Intent: {intent}"
        )


class AllergyIntoleranceSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for AllergyIntolerance resources"""

    def _get_supported_resource_types(self) -> Set[str]:
        return {"AllergyIntolerance"}

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        allergen = self._extract_code_text(fhir_resource, 'code')
        clinical_status = fhir_resource.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'unknown')
        verification_status = fhir_resource.get('verificationStatus', {}).get('coding', [{}])[0].get('code', 'unknown')
        category = fhir_resource.get('category', ['unknown'])[0]
        criticality = fhir_resource.get('criticality', 'unknown')

        if clinical_status == 'active':
            description = f"Active allergy: {allergen}"
        elif clinical_status == 'resolved':
            description = f"Resolved allergy: {allergen}"
        else:
            description = f"Allergy/intolerance: {allergen}"

        details = []
        if category != 'unknown':
            details.append(f"category: {category}")
        if criticality in ['high', 'low']:
            details.append(f"criticality: {criticality}")

        if details:
            description += f" ({', '.join(details)})"

        return ClinicalOrder(
            order_type="allergy",
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.94,
            clinical_rationale=f"Status: {clinical_status}, Verification: {verification_status}"
        )


class ImmunizationSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for Immunization resources"""

    def _get_supported_resource_types(self) -> Set[str]:
        return {"Immunization"}

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        vaccine = self._extract_code_text(fhir_resource, 'vaccineCode')
        status = fhir_resource.get('status', 'unknown')
        occurrence = fhir_resource.get('occurrenceDateTime', '')

        if status == 'completed':
            description = f"Immunization completed: {vaccine}"
        elif status == 'not-done':
            description = f"Immunization not administered: {vaccine}"
        else:
            description = f"Immunization ({status}): {vaccine}"

        if occurrence:
            description += f" on {occurrence[:10]}"  # Just date part

        return ClinicalOrder(
            order_type="immunization",
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.92,
            clinical_rationale=f"Status: {status}"
        )


class DeviceRequestSummarizer(BaseResourceSummarizer):
    """Rule-based summarizer for DeviceRequest resources"""

    def _get_supported_resource_types(self) -> Set[str]:
        return {"DeviceRequest"}

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        device = self._extract_code_text(fhir_resource, 'codeCodeableConcept')
        if not device or device == "Unknown":
            device = self._extract_code_text(fhir_resource, 'code')

        status = fhir_resource.get('status', 'unknown')
        intent = fhir_resource.get('intent', 'unknown')

        if status == 'active':
            description = f"Device request: {device}"
        elif status == 'completed':
            description = f"Device provided: {device}"
        else:
            description = f"Device request ({status}): {device}"

        if intent != 'unknown':
            description += f" ({intent})"

        return ClinicalOrder(
            order_type="device_request",
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.89,
            clinical_rationale=f"Status: {status}, Intent: {intent}"
        )


class GenericFHIRResourceSummarizer(BaseResourceSummarizer):
    """Universal fallback summarizer for ANY FHIR resource type - 100% coverage guarantee"""

    def _get_supported_resource_types(self) -> Set[str]:
        return set()  # Supports everything as fallback

    async def summarize_resource(self, fhir_resource: Dict[str, Any], role: str = "physician") -> ClinicalOrder:
        resource_type = fhir_resource.get('resourceType', 'Unknown')
        resource_id = fhir_resource.get('id', 'unknown-id')

        # Try to extract meaningful information from common FHIR patterns
        description = f"{resource_type} resource"

        # Look for common fields and extract readable information
        extracted_info = []

        # Status field (most FHIR resources have this)
        if 'status' in fhir_resource:
            extracted_info.append(f"status: {fhir_resource['status']}")

        # Text/display fields
        if 'text' in fhir_resource and isinstance(fhir_resource['text'], dict):
            status = fhir_resource['text'].get('status')
            if status:
                extracted_info.append(f"text: {status}")

        # Code fields (try multiple common patterns)
        code_text = None
        for code_field in ['code', 'type', 'category', 'class']:
            if code_field in fhir_resource:
                code_text = self._extract_code_text(fhir_resource, code_field)
                if code_text and code_text != "Unknown":
                    extracted_info.append(f"{code_field}: {code_text}")
                    break

        # Subject reference (patient link)
        if 'subject' in fhir_resource and isinstance(fhir_resource['subject'], dict):
            subject_ref = fhir_resource['subject'].get('reference', '')
            if 'Patient' in subject_ref:
                extracted_info.append("linked to patient")

        # Intent field (common in request resources)
        if 'intent' in fhir_resource:
            extracted_info.append(f"intent: {fhir_resource['intent']}")

        # Priority field
        if 'priority' in fhir_resource:
            extracted_info.append(f"priority: {fhir_resource['priority']}")

        if extracted_info:
            description += f" ({', '.join(extracted_info[:3])})"  # Limit to first 3 pieces of info

        return ClinicalOrder(
            order_type=resource_type.lower(),
            description=description,
            processing_tier=ProcessingTier.RULE_BASED,
            confidence_score=0.75,  # Lower confidence for generic processing
            clinical_rationale=f"Generic FHIR resource processing for {resource_type}"
        )


class ResourceSummarizerRegistry:
    """
    Registry for rule-based resource summarizers
    100% FHIR resource coverage - handles ALL resource types programmatically
    """

    def __init__(self):
        self._summarizers: Dict[str, BaseResourceSummarizer] = {}
        self._generic_summarizer = GenericFHIRResourceSummarizer()
        self._initialize_comprehensive_summarizers()

    def _initialize_comprehensive_summarizers(self):
        """Initialize registry with comprehensive FHIR resource coverage"""

        # Core clinical summarizers
        medication_summarizer = MedicationSummarizer()
        service_summarizer = ServiceRequestSummarizer()
        condition_summarizer = ConditionSummarizer()
        observation_summarizer = ObservationSummarizer()
        procedure_summarizer = ProcedureSummarizer()
        diagnostic_report_summarizer = DiagnosticReportSummarizer()
        patient_summarizer = PatientSummarizer()
        encounter_summarizer = EncounterSummarizer()
        care_plan_summarizer = CarePlanSummarizer()
        allergy_summarizer = AllergyIntoleranceSummarizer()
        immunization_summarizer = ImmunizationSummarizer()
        device_request_summarizer = DeviceRequestSummarizer()

        # Register all summarizers
        summarizers = [
            medication_summarizer, service_summarizer, condition_summarizer,
            observation_summarizer, procedure_summarizer, diagnostic_report_summarizer,
            patient_summarizer, encounter_summarizer, care_plan_summarizer,
            allergy_summarizer, immunization_summarizer, device_request_summarizer
        ]

        for summarizer in summarizers:
            for resource_type in summarizer.supported_resource_types:
                self._summarizers[resource_type] = summarizer
    
    def get_summarizer(self, resource_type: str) -> BaseResourceSummarizer:
        """Return appropriate rule-based summarizer for resource type - 100% coverage guaranteed"""
        return self._summarizers.get(resource_type, self._generic_summarizer)
    
    def register_summarizer(self, resource_type: str, summarizer: BaseResourceSummarizer):
        """Register a new summarizer for a resource type"""
        if not isinstance(summarizer, BaseResourceSummarizer):
            raise ValueError("Summarizer must inherit from BaseResourceSummarizer")
        
        self._summarizers[resource_type] = summarizer
    
    def get_supported_resource_types(self) -> Set[str]:
        """Get all resource types supported by registered summarizers"""
        return set(self._summarizers.keys())
    
    def calculate_rule_coverage(self, resource_types: list) -> float:
        """Calculate percentage of resources covered by rule-based processing"""
        if not resource_types:
            return 0.0
        
        supported_count = sum(1 for rt in resource_types if rt in self._summarizers)
        return supported_count / len(resource_types)
    
    def get_unsupported_resource_types(self, resource_types: list) -> list:
        """Get list of resource types not supported by rule-based processing"""
        return [rt for rt in resource_types if rt not in self._summarizers]
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics for monitoring"""
        return {
            "total_summarizers": len(set(self._summarizers.values())),
            "supported_resource_types": len(self._summarizers),
            "resource_types": sorted(self._summarizers.keys()),
            "last_updated": datetime.now().isoformat()
        }