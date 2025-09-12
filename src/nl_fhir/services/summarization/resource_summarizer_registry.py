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


class ResourceSummarizerRegistry:
    """
    Registry for rule-based resource summarizers
    Enables extensible, deterministic processing for common FHIR resources
    """
    
    def __init__(self):
        self._summarizers: Dict[str, BaseResourceSummarizer] = {}
        self._initialize_default_summarizers()
    
    def _initialize_default_summarizers(self):
        """Initialize registry with default summarizers"""
        
        # Register core summarizers
        medication_summarizer = MedicationSummarizer()
        service_summarizer = ServiceRequestSummarizer()
        
        for resource_type in medication_summarizer.supported_resource_types:
            self._summarizers[resource_type] = medication_summarizer
        
        for resource_type in service_summarizer.supported_resource_types:
            self._summarizers[resource_type] = service_summarizer
    
    def get_summarizer(self, resource_type: str) -> Optional[BaseResourceSummarizer]:
        """Return appropriate rule-based summarizer for resource type"""
        return self._summarizers.get(resource_type)
    
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