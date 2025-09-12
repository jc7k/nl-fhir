"""
Clinical Summary Models for Structured Output
Pydantic models ensuring consistent summary format across all processing tiers
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from .bundle_analysis import ProcessingTier


class QualityIndicators(BaseModel):
    """Quality and completeness indicators for generated summaries"""
    
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Overall summary completeness")
    clinical_accuracy_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in clinical accuracy") 
    terminology_consistency: float = Field(..., ge=0.0, le=1.0, description="Medical terminology consistency score")
    missing_critical_information: bool = Field(..., description="Whether critical clinical information is missing")
    
    # Processing quality indicators
    processing_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in processing method used")
    fallback_quality_impact: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality impact if fallback processing was used")


class ClinicalOrder(BaseModel):
    """Individual clinical order within the summary"""
    
    order_type: str = Field(..., description="Type of clinical order (medication, lab, procedure, etc.)")
    description: str = Field(..., description="Natural language order description")
    priority: Optional[str] = Field(None, description="Order priority level (routine, urgent, stat)")
    clinical_rationale: Optional[str] = Field(None, description="Clinical reasoning for order")
    
    # Safety and compliance
    safety_alerts: List[str] = Field(default_factory=list, description="Safety alerts or contraindications")
    drug_interactions: List[str] = Field(default_factory=list, description="Potential drug interactions")
    
    # Processing metadata
    processing_tier: ProcessingTier = Field(..., description="Tier used to process this order")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in order interpretation")


class ClinicalSummary(BaseModel):
    """
    Structured clinical summary model for consistent output across all processing tiers
    Used by rule-based, template, and LLM processing for unified response format
    """
    
    # Summary metadata
    summary_type: Literal["medication_only", "comprehensive", "emergency", "complex", "minimal"] = Field(
        ..., description="Type of summary based on bundle content"
    )
    processing_tier: ProcessingTier = Field(..., description="Processing tier used to generate summary")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall summary confidence")
    
    # Core clinical content
    patient_context: str = Field(..., description="Brief patient context and demographics (non-PHI)")
    primary_orders: List[ClinicalOrder] = Field(..., description="Main clinical orders from bundle")
    supporting_information: Optional[str] = Field(None, description="Additional clinical context or notes")
    
    # Safety and quality indicators
    clinical_alerts: List[str] = Field(default_factory=list, description="System-wide safety alerts or contraindications")
    quality_indicators: QualityIndicators = Field(..., description="Summary quality and completeness metrics")
    
    # Role-specific customization (populated based on user role)
    physician_notes: Optional[str] = Field(None, description="Physician-specific clinical notes")
    nursing_considerations: Optional[str] = Field(None, description="Nursing care considerations") 
    pharmacy_notes: Optional[str] = Field(None, description="Pharmacy review and drug interactions")
    
    # Processing information  
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing tier metadata")
    fallback_information: Optional[str] = Field(None, description="Information about fallback processing if used")
    
    # Timestamps
    created_timestamp: datetime = Field(default_factory=datetime.now, description="Summary creation timestamp")
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MinimalSummary(BaseModel):
    """Minimal fallback summary for emergency situations"""
    
    summary_type: Literal["minimal"] = "minimal"
    processing_tier: ProcessingTier = ProcessingTier.EMERGENCY_FALLBACK
    resource_count: int = Field(..., description="Total number of resources in bundle")
    resource_types: List[str] = Field(..., description="Types of resources found")
    error_message: str = Field(..., description="Reason for minimal processing")
    created_timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True