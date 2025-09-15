"""
Clinical condition and context models for LLM structured output
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, validator


class ClinicalSetting(str, Enum):
    """Clinical care settings"""
    OUTPATIENT = "outpatient"
    INPATIENT = "inpatient"
    EMERGENCY = "emergency"
    ICU = "intensive_care"
    UNKNOWN = "unknown"


class MedicalCondition(BaseModel):
    """Medical condition with context"""

    name: str = Field(..., description="Condition name (required)")
    severity: Optional[str] = Field(None, description="Condition severity")
    onset: Optional[str] = Field(None, description="When condition started")
    status: str = Field("active", description="Condition status (active, resolved, etc.)")

    @validator('name')
    def validate_condition_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Condition name cannot be empty")
        return v.strip().lower()