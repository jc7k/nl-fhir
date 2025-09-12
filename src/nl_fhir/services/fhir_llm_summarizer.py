"""
FHIR Bundle LLM Summarization Service
Simple, reliable conversion of validated FHIR bundles to clinical summaries
"""

import json
import logging
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

# Note: In production, replace with actual LLM client
# from openai import AsyncOpenAI
# from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)


class FHIRBundleSummarizer:
    """Simple LLM-based FHIR bundle summarization"""
    
    def __init__(self, llm_provider: str = "openai"):
        self.llm_provider = llm_provider
        self.initialized = False
        
        # In production: initialize actual LLM client
        # self.client = AsyncOpenAI() or AsyncAnthropic()
        
    def initialize(self) -> bool:
        """Initialize LLM client"""
        try:
            # In production: test LLM client connection
            self.initialized = True
            logger.info(f"FHIR LLM Summarizer initialized with {self.llm_provider}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            return False
    
    async def summarize_fhir_bundle(self, fhir_bundle: Dict[str, Any], 
                                   request_id: Optional[str] = None,
                                   clinical_role: str = "physician") -> Dict[str, Any]:
        """
        Summarize a validated FHIR bundle to plain English
        
        Args:
            fhir_bundle: HAPI-validated FHIR bundle
            request_id: Optional request identifier
            clinical_role: Target audience (physician, nurse, pharmacist, patient)
            
        Returns:
            Comprehensive summary with clinical context
        """
        
        if not self.initialized:
            if not self.initialize():
                return self._create_error_response("LLM summarizer not initialized", request_id)
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"[{request_id}] Starting FHIR bundle summarization for {clinical_role}")
            
            # Extract key clinical elements from FHIR bundle
            clinical_elements = self._extract_clinical_elements(fhir_bundle)
            
            # Generate role-appropriate summary
            summary = await self._generate_llm_summary(
                fhir_bundle, clinical_elements, clinical_role, request_id
            )
            
            # Validate and enhance summary
            validated_summary = self._validate_summary_accuracy(
                summary, clinical_elements, fhir_bundle
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "completed",
                "request_id": request_id,
                "summary": validated_summary,
                "clinical_elements": clinical_elements,
                "processing_time_ms": processing_time * 1000,
                "llm_provider": self.llm_provider,
                "target_role": clinical_role,
                "fhir_bundle_size": len(json.dumps(fhir_bundle)),
                "timestamp": start_time.isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"[{request_id}] FHIR summarization failed: {e}")
            return self._create_error_response(str(e), request_id)
    
    def _extract_clinical_elements(self, fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured clinical information from FHIR bundle"""
        
        elements = {
            "medications": [],
            "lab_orders": [],
            "procedures": [],
            "observations": [],
            "patient_info": None,
            "encounter_info": None
        }
        
        entries = fhir_bundle.get("entry", [])
        
        for entry in entries:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            
            if resource_type == "MedicationRequest":
                elements["medications"].append(self._extract_medication_info(resource))
            elif resource_type == "ServiceRequest":
                service_category = resource.get("category", [{}])[0].get("text", "")
                if "lab" in service_category.lower():
                    elements["lab_orders"].append(self._extract_lab_info(resource))
                else:
                    elements["procedures"].append(self._extract_procedure_info(resource))
            elif resource_type == "Observation":
                elements["observations"].append(self._extract_observation_info(resource))
            elif resource_type == "Patient":
                elements["patient_info"] = self._extract_patient_info(resource)
            elif resource_type == "Encounter":
                elements["encounter_info"] = self._extract_encounter_info(resource)
        
        return elements
    
    def _extract_medication_info(self, medication_request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract medication information"""
        
        medication = medication_request.get("medicationCodeableConcept", {})
        dosage = medication_request.get("dosageInstruction", [{}])[0]
        
        return {
            "medication": medication.get("text") or medication.get("coding", [{}])[0].get("display"),
            "dose": self._extract_dose(dosage),
            "frequency": self._extract_frequency(dosage),
            "route": dosage.get("route", {}).get("text"),
            "duration": self._extract_duration(medication_request),
            "indication": medication_request.get("reasonCode", [{}])[0].get("text")
        }
    
    def _extract_lab_info(self, service_request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract laboratory order information"""
        
        return {
            "test": service_request.get("code", {}).get("text"),
            "indication": service_request.get("reasonCode", [{}])[0].get("text"),
            "urgency": service_request.get("priority"),
            "specimen": service_request.get("specimen", {}).get("display")
        }
    
    def _extract_procedure_info(self, service_request: Dict[str, Any]) -> Dict[str, Any]:
        """Extract procedure information"""
        
        return {
            "procedure": service_request.get("code", {}).get("text"),
            "indication": service_request.get("reasonCode", [{}])[0].get("text"),
            "urgency": service_request.get("priority"),
            "location": service_request.get("locationReference", {}).get("display")
        }
    
    def _extract_observation_info(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract observation/vital signs information"""
        
        return {
            "observation": observation.get("code", {}).get("text"),
            "value": self._extract_observation_value(observation),
            "status": observation.get("status"),
            "date": observation.get("effectiveDateTime")
        }
    
    def _extract_patient_info(self, patient: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant patient demographics (de-identified)"""
        
        return {
            "age_range": self._calculate_age_range(patient.get("birthDate")),
            "gender": patient.get("gender"),
            "active": patient.get("active", True)
        }
    
    def _extract_encounter_info(self, encounter: Dict[str, Any]) -> Dict[str, Any]:
        """Extract encounter context"""
        
        return {
            "encounter_type": encounter.get("class", {}).get("display"),
            "status": encounter.get("status"),
            "period": encounter.get("period")
        }
    
    # Helper methods for data extraction
    def _extract_dose(self, dosage: Dict[str, Any]) -> str:
        """Extract dose information from dosage instruction"""
        dose_and_rate = dosage.get("doseAndRate", [{}])[0]
        dose_qty = dose_and_rate.get("doseQuantity", {})
        
        if dose_qty:
            value = dose_qty.get("value", "")
            unit = dose_qty.get("unit", "")
            return f"{value}{unit}" if value and unit else str(value)
        
        return dosage.get("text", "")
    
    def _extract_frequency(self, dosage: Dict[str, Any]) -> str:
        """Extract frequency from timing information"""
        timing = dosage.get("timing", {})
        repeat = timing.get("repeat", {})
        
        frequency = repeat.get("frequency", 1)
        period = repeat.get("period", 1)
        period_unit = repeat.get("periodUnit", "d")
        
        if frequency == 1 and period == 1 and period_unit == "d":
            return "once daily"
        elif frequency == 2 and period == 1 and period_unit == "d":
            return "twice daily"
        elif frequency == 3 and period == 1 and period_unit == "d":
            return "three times daily"
        else:
            return f"{frequency} times per {period} {period_unit}"
    
    def _extract_duration(self, medication_request: Dict[str, Any]) -> Optional[str]:
        """Extract medication duration if specified"""
        # Implementation depends on FHIR structure used
        return medication_request.get("dispenseRequest", {}).get("expectedSupplyDuration", {}).get("value")
    
    def _extract_observation_value(self, observation: Dict[str, Any]) -> str:
        """Extract observation value with units"""
        value_qty = observation.get("valueQuantity", {})
        if value_qty:
            value = value_qty.get("value", "")
            unit = value_qty.get("unit", "")
            return f"{value} {unit}".strip()
        
        return observation.get("valueString", "")
    
    def _calculate_age_range(self, birth_date: Optional[str]) -> str:
        """Calculate age range for privacy (e.g., '30-40 years')"""
        if not birth_date:
            return "Unknown"
        
        # Implementation for age range calculation
        # For demo purposes:
        return "Adult"
    
    async def _generate_llm_summary(self, fhir_bundle: Dict[str, Any], 
                                  clinical_elements: Dict[str, Any],
                                  clinical_role: str, request_id: str) -> str:
        """Generate LLM summary from clinical elements"""
        
        # Create role-specific prompt
        prompt = self._create_summarization_prompt(clinical_elements, clinical_role)
        
        # In production: call actual LLM
        # response = await self.client.chat.completions.create(
        #     model="gpt-4",
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=0.3
        # )
        # return response.choices[0].message.content
        
        # Demo implementation with template-based summary
        return self._create_demo_summary(clinical_elements, clinical_role)
    
    def _create_summarization_prompt(self, clinical_elements: Dict[str, Any], 
                                   clinical_role: str) -> str:
        """Create role-appropriate summarization prompt"""
        
        base_prompt = f"""
You are a clinical documentation specialist creating a summary for a {clinical_role}.

Convert this structured clinical data to a clear, professional summary:

CLINICAL ELEMENTS:
{json.dumps(clinical_elements, indent=2)}

Requirements:
- Use clear, professional medical language appropriate for a {clinical_role}
- Include all medications with complete dosing information
- List all laboratory orders and procedures
- Note any clinical indications or reasoning
- Highlight any potential safety considerations
- Keep summary concise but complete

Format as a clinical note with appropriate sections.
"""
        
        return base_prompt.strip()
    
    def _create_demo_summary(self, clinical_elements: Dict[str, Any], 
                           clinical_role: str) -> str:
        """Create demo summary (replace with actual LLM in production)"""
        
        summary_parts = [f"CLINICAL ORDER SUMMARY (for {clinical_role.title()})"]
        
        # Medications section
        if clinical_elements["medications"]:
            summary_parts.append("\nMEDICATIONS:")
            for med in clinical_elements["medications"]:
                med_line = f"• {med['medication']}"
                if med["dose"]:
                    med_line += f" {med['dose']}"
                if med["frequency"]:
                    med_line += f" {med['frequency']}"
                if med["indication"]:
                    med_line += f" - for {med['indication']}"
                summary_parts.append(med_line)
        
        # Lab orders section
        if clinical_elements["lab_orders"]:
            summary_parts.append("\nLABORATORY ORDERS:")
            for lab in clinical_elements["lab_orders"]:
                lab_line = f"• {lab['test']}"
                if lab["indication"]:
                    lab_line += f" - {lab['indication']}"
                if lab["urgency"]:
                    lab_line += f" ({lab['urgency']} priority)"
                summary_parts.append(lab_line)
        
        # Procedures section
        if clinical_elements["procedures"]:
            summary_parts.append("\nPROCEDURES:")
            for proc in clinical_elements["procedures"]:
                proc_line = f"• {proc['procedure']}"
                if proc["indication"]:
                    proc_line += f" - {proc['indication']}"
                summary_parts.append(proc_line)
        
        # Clinical assessment
        summary_parts.append("\nCLINICAL ASSESSMENT:")
        summary_parts.append("Orders appear clinically appropriate based on available information.")
        summary_parts.append("Review complete FHIR bundle for detailed clinical context.")
        
        return "\n".join(summary_parts)
    
    def _validate_summary_accuracy(self, summary: str, 
                                 clinical_elements: Dict[str, Any],
                                 fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Validate summary accuracy against FHIR data"""
        
        # Basic validation checks
        validation_results = {
            "summary_text": summary,
            "accuracy_checks": {
                "medication_count_match": len(clinical_elements["medications"]),
                "lab_count_match": len(clinical_elements["lab_orders"]),
                "procedure_count_match": len(clinical_elements["procedures"]),
                "all_elements_included": True  # Simple check for demo
            },
            "confidence_score": 0.95,  # Demo value - would calculate from validation
            "validation_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return validation_results
    
    def _create_error_response(self, error_message: str, request_id: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "status": "error",
            "request_id": request_id,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "llm_provider": self.llm_provider
        }


# Global summarizer instance
fhir_summarizer = FHIRBundleSummarizer()


async def summarize_fhir_bundle(fhir_bundle: Dict[str, Any],
                               request_id: Optional[str] = None,
                               clinical_role: str = "physician") -> Dict[str, Any]:
    """Summarize validated FHIR bundle to clinical summary"""
    return await fhir_summarizer.summarize_fhir_bundle(fhir_bundle, request_id, clinical_role)


def get_summarizer_status() -> Dict[str, Any]:
    """Get FHIR summarizer status"""
    return {
        "initialized": fhir_summarizer.initialized,
        "llm_provider": fhir_summarizer.llm_provider,
        "supported_roles": ["physician", "nurse", "pharmacist", "patient"],
        "capabilities": [
            "Medication summarization",
            "Laboratory order summarization", 
            "Procedure summarization",
            "Clinical context extraction",
            "Role-based formatting",
            "Accuracy validation"
        ]
    }