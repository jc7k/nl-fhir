"""
Medication-related Pydantic models for LLM structured output
"""

import logging
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator, model_validator

logger = logging.getLogger(__name__)


class MedicationRoute(str, Enum):
    """Standardized medication routes"""
    ORAL = "oral"
    IV = "intravenous"
    IM = "intramuscular"
    SUBLINGUAL = "sublingual"
    TOPICAL = "topical"
    INHALATION = "inhalation"
    UNKNOWN = "unknown"


class MedicationOrder(BaseModel):
    """Enhanced medication order with validation"""

    name: str = Field(..., description="Medication name (required)")
    dosage: Optional[str] = Field(None, description="Dosage amount with units (e.g., '100mg') - CRITICAL for safety")
    frequency: Optional[str] = Field(None, description="Frequency of administration (e.g., 'twice daily') - CRITICAL for safety")
    route: MedicationRoute = Field(MedicationRoute.UNKNOWN, description="Route of administration")
    indication: Optional[str] = Field(None, description="Medical reason for prescription")
    duration: Optional[str] = Field(None, description="Treatment duration")
    special_instructions: List[str] = Field(default_factory=list, description="Special administration instructions")
    safety_flag: bool = Field(default=False, description="Flag if dosage/frequency missing for safety review")

    @validator('name')
    def validate_medication_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Medication name cannot be empty")
        return v.strip().lower()

    @model_validator(mode='after')
    def check_safety_critical_fields(self):
        """Flag medications missing dosage or frequency for safety review"""
        # Set safety flag if critical information is missing
        if self.name and (not self.dosage or not self.frequency):
            self.safety_flag = True
            # Log warning for clinical review
            logger.warning(f"Medication '{self.name}' missing critical safety information - dosage: {bool(self.dosage)}, frequency: {bool(self.frequency)}")

        return self