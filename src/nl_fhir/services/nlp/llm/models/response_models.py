"""
Response and wrapper models for LLM structured output
"""

import logging
from typing import List
from pydantic import BaseModel, Field, model_validator

from .medication_models import MedicationOrder
from .procedure_models import LabTest, DiagnosticProcedure, UrgencyLevel
from .clinical_models import MedicalCondition, ClinicalSetting

logger = logging.getLogger(__name__)


class ClinicalStructure(BaseModel):
    """Enhanced structured clinical data model for Instructor LLM output"""

    medications: List[MedicationOrder] = Field(
        default_factory=list,
        description="List of medication orders with complete dosing information"
    )

    lab_tests: List[LabTest] = Field(
        default_factory=list,
        description="List of laboratory tests and diagnostic blood work"
    )

    procedures: List[DiagnosticProcedure] = Field(
        default_factory=list,
        description="List of diagnostic procedures and imaging studies"
    )

    conditions: List[MedicalCondition] = Field(
        default_factory=list,
        description="List of medical conditions and diagnoses"
    )

    patients: List[str] = Field(
        default_factory=list,
        description="List of patient names mentioned in the clinical text"
    )

    clinical_instructions: List[str] = Field(
        default_factory=list,
        description="General clinical instructions and patient care notes"
    )

    urgency_level: UrgencyLevel = Field(
        UrgencyLevel.ROUTINE,
        description="Overall urgency level of the clinical orders"
    )

    clinical_setting: ClinicalSetting = Field(
        ClinicalSetting.OUTPATIENT,
        description="Clinical care setting"
    )

    patient_safety_alerts: List[str] = Field(
        default_factory=list,
        description="Important safety considerations and alerts"
    )

    @model_validator(mode='after')
    def validate_has_orders(self):
        """Ensure at least one clinical order is present"""
        if not self.medications and not self.lab_tests and not self.procedures:
            logger.warning("No clinical orders found in structured output")

        return self