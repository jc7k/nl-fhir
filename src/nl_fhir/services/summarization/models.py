"""
Epic 4 Data Models for FHIR Bundle Summarization
Structured data types for clinical summaries and processing analytics
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ProcessingTier(Enum):
    """Processing tier enumeration for adaptive summarization"""
    TEMPLATE = "template"  # Rule-based template processing
    GENERIC = "generic"   # Generic engine processing
    LLM = "llm"          # LLM-enhanced processing


class ClinicalOrder(BaseModel):
    """Clinical order extracted from FHIR bundle"""
    resource_type: str
    resource_id: str
    display_name: str
    status: str
    priority: Optional[str] = None
    timing: Optional[str] = None
    dosage: Optional[str] = None
    notes: Optional[str] = None


class QualityIndicators(BaseModel):
    """Quality indicators for summarization assessment"""
    completeness_score: float = Field(ge=0.0, le=1.0)
    accuracy_confidence: float = Field(ge=0.0, le=1.0)
    clinical_relevance: float = Field(ge=0.0, le=1.0)
    missing_fields: List[str] = Field(default_factory=list)
    assumptions_made: List[str] = Field(default_factory=list)
    data_conflicts: List[str] = Field(default_factory=list)


class BundleAnalysis(BaseModel):
    """Analysis results for FHIR bundle content"""
    total_resources: int
    resource_types: Dict[str, int]
    complexity_score: float = Field(ge=0.0, le=1.0)
    recommended_tier: ProcessingTier
    analysis_time_ms: float
    key_findings: List[str] = Field(default_factory=list)


class SummarizationEvent(BaseModel):
    """Processing event for monitoring and analytics"""
    request_id: str
    timestamp: datetime
    event_type: str
    tier_used: ProcessingTier
    processing_time_ms: float
    success: bool
    error_message: Optional[str] = None
    bundle_complexity: Optional[float] = None
    quality_score: Optional[float] = None


class TierUsageAnalytics(BaseModel):
    """Analytics for tier usage patterns"""
    total_requests: int
    tier_distribution: Dict[ProcessingTier, int]
    avg_processing_time: Dict[ProcessingTier, float]
    success_rates: Dict[ProcessingTier, float]
    cost_analysis: Dict[str, float]


class MinimalSummary(BaseModel):
    """Minimal summary structure for basic processing"""
    patient_summary: str
    orders_summary: List[str]
    key_findings: List[str] = Field(default_factory=list)
    processing_tier: ProcessingTier
    confidence_score: float = Field(ge=0.0, le=1.0)


class TierSelectionCriteria(BaseModel):
    """Criteria for selecting processing tiers"""
    template_max_resources: int = 20
    generic_max_resources: int = 100
    complexity_threshold: float = 0.7
    cost_optimization_enabled: bool = True


class ResourceClassification(BaseModel):
    """Classification of FHIR resource complexity"""
    resource_type: str
    complexity_weight: float = Field(ge=0.1, le=2.0)
    template_supported: bool = True
    requires_llm: bool = False


class ClinicalSummary(BaseModel):
    """Complete clinical summary with all Epic 4 features"""
    # Core summary content
    patient_summary: str
    orders_list: List[ClinicalOrder]
    clinical_narrative: str
    key_findings: List[str] = Field(default_factory=list)

    # Metadata
    request_id: str
    generated_at: datetime
    processing_tier: ProcessingTier

    # Quality assessment
    quality_indicators: QualityIndicators
    bundle_analysis: BundleAnalysis

    # Optional LLM enhancement
    llm_enhanced: bool = False
    enhancement_details: Optional[Dict[str, Any]] = None

    # Clinical context
    clinical_context: Optional[Dict[str, Any]] = None
    user_role: str = "clinician"

    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility"""
        return {
            "human_readable_summary": self.clinical_narrative,
            "bundle_summary": {
                "patient": self.patient_summary,
                "orders": [order.dict() for order in self.orders_list],
                "findings": self.key_findings
            },
            "confidence_indicators": {
                "completeness": self.quality_indicators.completeness_score,
                "accuracy": self.quality_indicators.accuracy_confidence,
                "clinical_relevance": self.quality_indicators.clinical_relevance,
                "missing_fields": self.quality_indicators.missing_fields,
                "assumptions": self.quality_indicators.assumptions_made
            },
            "processing_details": {
                "tier": self.processing_tier.value,
                "enhanced": self.llm_enhanced,
                "complexity": self.bundle_analysis.complexity_score
            }
        }