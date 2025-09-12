"""
Bundle Analysis Models for Adaptive Processing
Supports tier selection and resource classification
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


class ProcessingTier(Enum):
    """Processing tiers for adaptive cost optimization"""
    RULE_BASED = "rule_based"         # Tier 1: Deterministic processing (70-80% target)
    GENERIC_TEMPLATE = "generic"      # Tier 2: Template-based processing (15-20% target)  
    LLM_FALLBACK = "llm_fallback"     # Tier 3: LLM-powered processing (5-10% target)
    EMERGENCY_FALLBACK = "emergency"  # Emergency: Basic resource listing


@dataclass
class BundleAnalysis:
    """Comprehensive bundle analysis for tier selection"""
    
    # Resource composition
    resource_types: List[str]
    resource_count: int
    primary_resource_type: Optional[str]
    
    # Complexity assessment
    complexity_score: float  # 0.0-10.0 scale
    has_rare_resources: bool
    has_emergency_indicators: bool
    
    # Processing hints
    recommended_tier: ProcessingTier
    confidence_score: float  # 0.0-1.0 confidence in tier recommendation
    
    # Analysis metadata
    analysis_timestamp: datetime
    analysis_duration_ms: float
    
    # Fallback information
    rule_based_coverage: float  # Percentage of resources covered by rule-based processors
    supported_resource_types: List[str]
    unsupported_resource_types: List[str]
    
    # Clinical context
    specialty_context: Optional[str]  # e.g., "emergency", "cardiology"
    urgency_level: Optional[str]      # e.g., "routine", "urgent", "stat"
    patient_demographics: Optional[Dict[str, Any]]


@dataclass
class ResourceClassification:
    """Classification result for individual FHIR resources"""
    
    resource_type: str
    resource_id: Optional[str]
    
    # Classification results
    is_supported_by_rules: bool
    is_complex: bool
    is_rare: bool
    
    # Processing recommendations
    recommended_processor: str
    confidence_score: float
    
    # Resource-specific attributes
    clinical_category: Optional[str]  # e.g., "medication", "lab", "procedure"
    priority_level: Optional[str]
    safety_considerations: List[str]


@dataclass  
class TierSelectionCriteria:
    """Criteria for intelligent tier selection"""
    
    # Rule-based tier criteria
    max_complexity_for_rules: float = 3.0
    min_rule_coverage_percent: float = 80.0
    
    # Template tier criteria  
    max_complexity_for_templates: float = 6.0
    max_resource_types_for_templates: int = 4
    
    # LLM fallback thresholds
    min_complexity_for_llm: float = 6.0
    min_rare_resource_threshold: float = 0.2
    
    # Cost optimization targets
    rule_based_target_percent: float = 75.0
    template_target_percent: float = 18.0
    llm_target_percent: float = 7.0