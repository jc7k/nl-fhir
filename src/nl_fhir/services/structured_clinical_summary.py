"""
Structured Clinical Summary with Dynamic Pydantic Schemas
Uses Instructor + Pydantic to ensure consistent, human-readable clinical summaries
"""

from typing import Dict, Any, List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum
import instructor
from openai import AsyncOpenAI

# Note: In production, uncomment and configure
# client = instructor.patch(AsyncOpenAI())


class ClinicalUrgency(str, Enum):
    """Clinical urgency levels for human readability"""
    ROUTINE = "routine"
    URGENT = "urgent" 
    STAT = "stat/immediate"
    ASAP = "as soon as possible"


class MedicationSummary(BaseModel):
    """Human-readable medication summary with consistent structure"""
    
    medication_name: str = Field(description="Clear medication name (e.g., 'Lisinopril', not 'ACE inhibitor')")
    dosage_instruction: str = Field(description="Complete human-readable dosing (e.g., 'Take 10mg by mouth once daily')")
    clinical_indication: Optional[str] = Field(description="Why this medication was prescribed (e.g., 'for blood pressure control')")
    duration_note: Optional[str] = Field(description="How long to take it (e.g., 'ongoing therapy', '7-day course')")
    special_instructions: Optional[str] = Field(description="Important patient instructions (e.g., 'take with food', 'monitor blood pressure')")
    
    class Config:
        schema_extra = {
            "example": {
                "medication_name": "Lisinopril",
                "dosage_instruction": "Take 10mg by mouth once daily",
                "clinical_indication": "for blood pressure control",
                "duration_note": "ongoing therapy",
                "special_instructions": "Monitor blood pressure weekly"
            }
        }


class LaboratoryOrderSummary(BaseModel):
    """Human-readable lab order summary"""
    
    test_description: str = Field(description="Clear test name (e.g., 'Complete Blood Count', not 'CBC')")
    clinical_reason: str = Field(description="Why this test was ordered (e.g., 'to monitor kidney function')")
    timing_requirement: ClinicalUrgency = Field(description="When this should be done")
    special_preparation: Optional[str] = Field(description="Patient prep instructions (e.g., 'fasting required', 'no prep needed')")
    
    class Config:
        schema_extra = {
            "example": {
                "test_description": "Complete Blood Count with differential",
                "clinical_reason": "to monitor for infection and blood disorders",
                "timing_requirement": "routine",
                "special_preparation": "no special preparation required"
            }
        }


class ProcedureSummary(BaseModel):
    """Human-readable procedure summary"""
    
    procedure_name: str = Field(description="Clear procedure name for patient understanding")
    clinical_purpose: str = Field(description="Why this procedure is needed")
    timing_requirement: ClinicalUrgency = Field(description="How soon this should be done")
    location_note: Optional[str] = Field(description="Where this will be performed")
    preparation_instructions: Optional[str] = Field(description="What patient needs to do beforehand")


class ClinicalAssessment(BaseModel):
    """Overall clinical assessment and safety notes"""
    
    summary_statement: str = Field(description="One-sentence overall assessment (e.g., 'These orders support routine hypertension management')")
    safety_considerations: List[str] = Field(description="Important safety notes for clinical review", default=[])
    follow_up_required: Optional[str] = Field(description="What follow-up is needed (e.g., 'recheck blood pressure in 2 weeks')")
    clinical_complexity: Literal["straightforward", "moderate", "complex"] = Field(description="Complexity level for clinical review prioritization")


class MedicationOnlySummary(BaseModel):
    """Schema for FHIR bundles containing only medications"""
    
    summary_type: Literal["medication_orders"] = "medication_orders"
    patient_context: str = Field(description="Brief patient context (e.g., 'Adult patient', 'Pediatric patient')")
    medications: List[MedicationSummary] = Field(description="All medication orders")
    clinical_assessment: ClinicalAssessment = Field(description="Overall assessment")
    
    class Config:
        schema_extra = {
            "example": {
                "summary_type": "medication_orders",
                "patient_context": "Adult patient",
                "medications": [
                    {
                        "medication_name": "Lisinopril",
                        "dosage_instruction": "Take 10mg by mouth once daily",
                        "clinical_indication": "for blood pressure control"
                    }
                ],
                "clinical_assessment": {
                    "summary_statement": "Standard antihypertensive therapy initiation",
                    "safety_considerations": ["Monitor blood pressure response"],
                    "clinical_complexity": "straightforward"
                }
            }
        }


class ComprehensiveOrderSummary(BaseModel):
    """Schema for complex FHIR bundles with multiple order types"""
    
    summary_type: Literal["comprehensive_orders"] = "comprehensive_orders"
    patient_context: str = Field(description="Brief patient context")
    medications: List[MedicationSummary] = Field(description="Medication orders", default=[])
    laboratory_orders: List[LaboratoryOrderSummary] = Field(description="Lab orders", default=[])
    procedures: List[ProcedureSummary] = Field(description="Procedures ordered", default=[])
    clinical_assessment: ClinicalAssessment = Field(description="Overall clinical assessment")
    coordination_notes: Optional[str] = Field(description="Notes about care coordination between different orders")


class EmergencyOrderSummary(BaseModel):
    """Schema for urgent/emergency orders requiring immediate attention"""
    
    summary_type: Literal["emergency_orders"] = "emergency_orders"
    urgency_level: Literal["urgent", "stat", "emergent"] = Field(description="Level of urgency")
    patient_context: str = Field(description="Patient context emphasizing acuity")
    immediate_orders: List[Union[MedicationSummary, LaboratoryOrderSummary, ProcedureSummary]] = Field(description="All orders requiring immediate action")
    clinical_assessment: ClinicalAssessment = Field(description="Assessment with emphasis on urgency and safety")
    critical_actions: List[str] = Field(description="Time-sensitive actions that must be completed", default=[])


class SchemaSelector:
    """Dynamically selects appropriate Pydantic schema based on FHIR bundle content"""
    
    @staticmethod
    def analyze_bundle_content(fhir_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze FHIR bundle to determine content types and complexity"""
        
        analysis = {
            "has_medications": False,
            "has_lab_orders": False,
            "has_procedures": False,
            "has_emergency_indicators": False,
            "resource_count": 0,
            "complexity_indicators": []
        }
        
        entries = fhir_bundle.get("entry", [])
        analysis["resource_count"] = len(entries)
        
        for entry in entries:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            
            if resource_type == "MedicationRequest":
                analysis["has_medications"] = True
                # Check for high-risk medications
                medication = resource.get("medicationCodeableConcept", {}).get("text", "").lower()
                if any(risk_med in medication for risk_med in ["warfarin", "insulin", "digoxin", "chemotherapy"]):
                    analysis["complexity_indicators"].append("high_risk_medications")
            
            elif resource_type == "ServiceRequest":
                priority = resource.get("priority", "").lower()
                category = resource.get("category", [{}])[0].get("text", "").lower()
                
                if "lab" in category:
                    analysis["has_lab_orders"] = True
                else:
                    analysis["has_procedures"] = True
                
                if priority in ["urgent", "stat", "asap"]:
                    analysis["has_emergency_indicators"] = True
                    analysis["complexity_indicators"].append("urgent_orders")
        
        # Complexity assessment
        if analysis["resource_count"] > 5:
            analysis["complexity_indicators"].append("multiple_orders")
        
        return analysis
    
    @staticmethod
    def select_schema(bundle_analysis: Dict[str, Any]) -> type[BaseModel]:
        """Select most appropriate Pydantic schema based on bundle analysis"""
        
        # Emergency/urgent orders take priority
        if bundle_analysis["has_emergency_indicators"]:
            return EmergencyOrderSummary
        
        # Simple medication-only orders
        if (bundle_analysis["has_medications"] and 
            not bundle_analysis["has_lab_orders"] and 
            not bundle_analysis["has_procedures"] and
            bundle_analysis["resource_count"] <= 3):
            return MedicationOnlySummary
        
        # Default to comprehensive summary for complex cases
        return ComprehensiveOrderSummary
    
    @staticmethod
    def create_dynamic_prompt(fhir_bundle: Dict[str, Any], schema_class: type[BaseModel], 
                             clinical_role: str = "physician") -> str:
        """Create context-aware prompt based on selected schema"""
        
        base_prompt = f"""
You are creating a clinical summary for a {clinical_role} to review and verify that orders were correctly interpreted from natural language.

CRITICAL REQUIREMENTS:
- Use clear, natural clinical language that reads like a human-written note
- Be precise about dosages, frequencies, and clinical indications
- Include safety considerations relevant to clinical practice
- Make it easy for the {clinical_role} to quickly verify accuracy

FHIR Bundle to Summarize:
{fhir_bundle}

Create a summary that follows the required structure but reads naturally for clinical review.
Focus on what the {clinical_role} needs to verify for patient safety and care quality.
"""
        
        # Add schema-specific guidance
        if schema_class == EmergencyOrderSummary:
            base_prompt += "\n\nEMPHASIS: This appears to contain urgent orders. Highlight time-sensitive elements and safety considerations."
        elif schema_class == MedicationOnlySummary:
            base_prompt += "\n\nFOCUS: This is primarily medication orders. Ensure dosing accuracy and drug safety considerations."
        
        return base_prompt.strip()


class StructuredClinicalSummarizer:
    """Main service for generating structured, consistent clinical summaries"""
    
    def __init__(self):
        self.schema_selector = SchemaSelector()
        # In production: self.client = instructor.patch(AsyncOpenAI())
        self.initialized = False
    
    async def generate_structured_summary(self, fhir_bundle: Dict[str, Any], 
                                        clinical_role: str = "physician",
                                        request_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate human-readable but structurally consistent clinical summary"""
        
        try:
            # Analyze bundle to select appropriate schema
            bundle_analysis = self.schema_selector.analyze_bundle_content(fhir_bundle)
            selected_schema = self.schema_selector.select_schema(bundle_analysis)
            
            # Create context-aware prompt
            prompt = self.schema_selector.create_dynamic_prompt(fhir_bundle, selected_schema, clinical_role)
            
            # In production: Generate structured response using Instructor
            """
            response = await self.client.chat.completions.create(
                model="gpt-4",
                response_model=selected_schema,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1  # Low temperature for consistency
            )
            return {
                "status": "completed",
                "schema_used": selected_schema.__name__,
                "bundle_analysis": bundle_analysis,
                "structured_summary": response.dict(),
                "clinical_role": clinical_role,
                "request_id": request_id
            }
            """
            
            # Demo implementation
            demo_summary = self._create_demo_structured_summary(fhir_bundle, selected_schema, clinical_role)
            
            return {
                "status": "completed",
                "schema_used": selected_schema.__name__,
                "bundle_analysis": bundle_analysis,
                "structured_summary": demo_summary,
                "clinical_role": clinical_role,
                "request_id": request_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "request_id": request_id
            }
    
    def _create_demo_structured_summary(self, fhir_bundle: Dict[str, Any], 
                                      schema_class: type[BaseModel], 
                                      clinical_role: str) -> Dict[str, Any]:
        """Demo implementation of structured summary (replace with actual LLM in production)"""
        
        if schema_class == MedicationOnlySummary:
            return {
                "summary_type": "medication_orders",
                "patient_context": "Adult patient with hypertension",
                "medications": [
                    {
                        "medication_name": "Lisinopril",
                        "dosage_instruction": "Take 10mg by mouth once daily in the morning",
                        "clinical_indication": "for blood pressure control",
                        "duration_note": "ongoing therapy",
                        "special_instructions": "Monitor blood pressure at home and report readings above 140/90"
                    }
                ],
                "clinical_assessment": {
                    "summary_statement": "Standard first-line antihypertensive therapy initiation with ACE inhibitor",
                    "safety_considerations": [
                        "Monitor for dry cough (common ACE inhibitor side effect)",
                        "Check kidney function and potassium levels in 2-4 weeks"
                    ],
                    "follow_up_required": "Blood pressure recheck in 2 weeks to assess response",
                    "clinical_complexity": "straightforward"
                }
            }
        
        # Default comprehensive summary
        return {
            "summary_type": "comprehensive_orders",
            "patient_context": "Adult patient with multiple medical management needs",
            "medications": [],
            "laboratory_orders": [],
            "procedures": [],
            "clinical_assessment": {
                "summary_statement": "Comprehensive care plan with multiple interventions",
                "safety_considerations": ["Review all orders for interactions and contraindications"],
                "clinical_complexity": "moderate"
            }
        }


# Demo usage function
async def demo_structured_summarization():
    """Demonstrate how structured summarization works"""
    
    # Sample FHIR bundle (simplified)
    sample_fhir = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "resource": {
                    "resourceType": "MedicationRequest",
                    "medicationCodeableConcept": {"text": "Lisinopril"},
                    "dosageInstruction": [{
                        "text": "10mg once daily",
                        "doseAndRate": [{"doseQuantity": {"value": 10, "unit": "mg"}}],
                        "timing": {"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}}
                    }]
                }
            }
        ]
    }
    
    summarizer = StructuredClinicalSummarizer()
    result = await summarizer.generate_structured_summary(sample_fhir, "physician")
    
    print("=== STRUCTURED CLINICAL SUMMARY ===")
    print(f"Schema Used: {result['schema_used']}")
    print(f"Bundle Analysis: {result['bundle_analysis']}")
    print("\nStructured Summary:")
    
    summary = result['structured_summary']
    if summary['summary_type'] == 'medication_orders':
        print(f"\nPatient Context: {summary['patient_context']}")
        print("\nMEDICATIONS:")
        for med in summary['medications']:
            print(f"• {med['medication_name']}: {med['dosage_instruction']}")
            if med.get('clinical_indication'):
                print(f"  Purpose: {med['clinical_indication']}")
            if med.get('special_instructions'):
                print(f"  Instructions: {med['special_instructions']}")
        
        assessment = summary['clinical_assessment']
        print(f"\nClinical Assessment: {assessment['summary_statement']}")
        if assessment.get('safety_considerations'):
            print("Safety Notes:")
            for safety in assessment['safety_considerations']:
                print(f"  - {safety}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_structured_summarization())