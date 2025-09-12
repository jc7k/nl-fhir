"""
Event Tracking Models for Production Monitoring
Comprehensive event logging for cost optimization and quality tracking
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from .bundle_analysis import ProcessingTier


@dataclass
class SummarizationEvent:
    """Comprehensive event tracking for all processing decisions and performance metrics"""
    
    # Core identification - required fields first
    timestamp: datetime
    request_id: str
    bundle_id: str
    
    # Resource analysis - required fields
    resource_types: List[str]
    resource_count: int
    bundle_complexity_score: float
    has_rare_resources: bool
    
    # Processing decisions - required fields  
    tier_selected: ProcessingTier
    
    # Performance metrics - required fields
    analysis_time_ms: float
    processing_time_ms: float
    total_time_ms: float
    
    # System context - required fields
    server_instance: str
    api_version: str
    user_role: str
    
    # Optional fields with defaults - all at the end
    session_id: Optional[str] = None
    tier_fallback_occurred: bool = False
    fallback_reason: Optional[str] = None
    original_tier_attempted: Optional[ProcessingTier] = None
    
    # Cost impact (LLM usage only)
    llm_tokens_used: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    
    # Quality indicators
    output_quality_score: Optional[float] = None
    user_satisfaction_rating: Optional[int] = None  # 1-5 scale
    
    # Additional context
    specialty_context: Optional[str] = None  # cardiology, emergency, etc.
    
    # Error information (if applicable)
    error_occurred: bool = False
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class TierUsageAnalytics:
    """Analytics for tier usage patterns over time"""
    
    # Required fields first
    time_window_hours: int
    total_requests: int
    
    # Tier usage counts
    rule_based_count: int
    generic_template_count: int
    llm_fallback_count: int
    emergency_fallback_count: int
    
    # Tier usage percentages
    rule_based_percentage: float
    generic_template_percentage: float
    llm_fallback_percentage: float
    emergency_fallback_percentage: float
    
    # Cost metrics
    total_llm_tokens: int
    estimated_total_cost_usd: float
    cost_per_request_usd: float
    
    # Performance metrics
    average_processing_time_ms: float
    p95_processing_time_ms: float
    p99_processing_time_ms: float
    
    # Quality metrics
    average_quality_score: float
    fallback_rate: float
    error_rate: float
    
    # Variance from targets - required fields
    rule_based_variance: float  # Actual vs target percentage
    llm_variance: float
    cost_optimization_score: float  # 0.0-1.0 effectiveness score
    
    # Optional fields with defaults at the end
    baseline_rule_based_target: float = 75.0
    baseline_llm_target: float = 7.0


@dataclass
class UsageDriftAlert:
    """Alert for significant deviations from expected usage patterns"""
    
    alert_timestamp: datetime
    alert_type: str  # "cost_spike", "tier_drift", "performance_degradation"
    severity: str    # "warning", "critical"
    
    # Drift details
    metric_name: str
    current_value: float
    baseline_value: float
    variance_percentage: float
    
    # Context
    time_window_hours: int
    affected_requests: int
    
    # Recommendations
    recommended_actions: List[str]
    requires_immediate_attention: bool


@dataclass
class SystemChangeEvent:
    """Event indicating significant system behavior changes requiring baseline updates"""
    
    detection_timestamp: datetime
    change_type: str  # "new_resource_pattern", "specialty_shift", "usage_pattern_change"
    
    # Change details
    affected_resource_types: List[str]
    confidence_score: float
    impact_assessment: str
    
    # Recommendations
    baseline_update_recommended: bool
    suggested_tier_adjustments: Dict[ProcessingTier, float]
    monitoring_period_days: int