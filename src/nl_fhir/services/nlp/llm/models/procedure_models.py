"""
Procedure and lab test related Pydantic models for LLM structured output
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class UrgencyLevel(str, Enum):
    """Standardized urgency levels"""
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"
    ASAP = "asap"


class LabTest(BaseModel):
    """Enhanced lab test order with validation"""

    name: str = Field(..., description="Lab test name (required)")
    test_type: str = Field("laboratory", description="Type of test (laboratory, pathology, etc.)")
    urgency: UrgencyLevel = Field(UrgencyLevel.ROUTINE, description="Test urgency level")
    fasting_required: bool = Field(False, description="Whether fasting is required")
    special_instructions: List[str] = Field(default_factory=list, description="Special collection instructions")
    expected_turnaround: Optional[str] = Field(None, description="Expected result timeframe")

    @validator('name')
    def validate_test_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Lab test name cannot be empty")
        return v.strip().lower()


class DiagnosticProcedure(BaseModel):
    """Enhanced diagnostic procedure with validation"""

    name: str = Field(..., description="Procedure name (required)")
    procedure_type: str = Field("diagnostic", description="Type of procedure")
    urgency: UrgencyLevel = Field(UrgencyLevel.ROUTINE, description="Procedure urgency")
    body_site: Optional[str] = Field(None, description="Anatomical location")
    contrast_needed: bool = Field(False, description="Whether contrast is required")
    special_prep: List[str] = Field(default_factory=list, description="Special preparation instructions")

    @validator('name')
    def validate_procedure_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Procedure name cannot be empty")
        return v.strip().lower()