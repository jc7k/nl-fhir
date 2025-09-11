"""
Request Models for NL-FHIR Converter
HIPAA Compliant: No PHI in model definitions or validation messages
Medical Safety: Comprehensive input validation
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


def sanitize_clinical_text(text: str) -> str:
    """
    Sanitize clinical text input for security and safety
    Removes potentially harmful characters while preserving medical content
    """
    if not text:
        return text
    
    # Remove potentially harmful HTML/script content
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove control characters except newlines, tabs, and carriage returns  
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    
    # Limit excessive whitespace
    text = re.sub(r'\s{4,}', '   ', text)  # Max 3 consecutive spaces
    text = re.sub(r'\n{4,}', '\n\n\n', text)  # Max 3 consecutive newlines
    
    return text


class ClinicalRequest(BaseModel):
    """HIPAA-compliant clinical request model - Basic version"""
    clinical_text: str = Field(
        ..., 
        description="Free-text clinical order",
        max_length=5000  # Security: limit input size
    )
    patient_ref: Optional[str] = Field(
        None, 
        description="Patient reference ID",
        max_length=100,  # Security: limit patient ref size
        pattern=r'^[A-Za-z0-9\-_]*$'  # Security: alphanumeric + dash/underscore only
    )
    
    @field_validator('clinical_text')
    @classmethod
    def validate_clinical_text(cls, v):
        if not v or len(v.strip()) < 5:
            raise ValueError("Clinical text must be at least 5 characters")
        
        # Sanitize input for security
        sanitized = sanitize_clinical_text(v.strip())
        
        if len(sanitized) < 5:
            raise ValueError("Clinical text too short after sanitization")
        
        return sanitized
    
    @field_validator('patient_ref')
    @classmethod
    def validate_patient_ref(cls, v):
        if v is None:
            return v
        
        # Sanitize patient reference
        sanitized = v.strip()
        if not sanitized:
            return None
            
        # Validate pattern (already enforced by Field pattern, but double-check)
        if not re.match(r'^[A-Za-z0-9\-_]+$', sanitized):
            raise ValueError("Patient reference contains invalid characters")
            
        return sanitized


class ClinicalRequestAdvanced(ClinicalRequest):
    """Advanced clinical request model with additional metadata"""
    priority: Optional[str] = Field(
        "routine",
        description="Order priority level", 
        pattern=r'^(routine|urgent|stat|asap)$'
    )
    ordering_provider: Optional[str] = Field(
        None,
        description="Ordering provider identifier",
        max_length=100,
        pattern=r'^[A-Za-z0-9\-_\.]*$'
    )
    department: Optional[str] = Field(
        None,
        description="Ordering department",
        max_length=100
    )
    context_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context metadata for processing"
    )
    request_timestamp: Optional[datetime] = Field(
        None,
        description="Client-side request timestamp"
    )
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v and v not in ['routine', 'urgent', 'stat', 'asap']:
            raise ValueError("Priority must be one of: routine, urgent, stat, asap")
        return v or "routine"
    
    @field_validator('context_metadata')
    @classmethod
    def validate_context_metadata(cls, v):
        if v is None:
            return v
        
        # Limit metadata size for security
        if isinstance(v, dict) and len(str(v)) > 1000:
            raise ValueError("Context metadata too large")
        
        return v


class BulkConversionRequest(BaseModel):
    """Model for bulk clinical order processing"""
    orders: List[ClinicalRequest] = Field(
        ...,
        description="List of clinical orders to process",
        max_length=50  # Limit bulk processing size
    )
    batch_id: Optional[str] = Field(
        None,
        description="Client-provided batch identifier",
        max_length=50
    )
    processing_options: Optional[Dict[str, bool]] = Field(
        default_factory=dict,
        description="Processing configuration options"
    )
    
    @field_validator('orders')
    @classmethod
    def validate_orders(cls, v):
        if not v:
            raise ValueError("At least one clinical order required")
        
        if len(v) > 50:
            raise ValueError("Maximum 50 orders per batch")
        
        return v