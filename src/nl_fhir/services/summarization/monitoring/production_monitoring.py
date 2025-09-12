"""
Production Monitoring Mixin for Epic 4
Basic monitoring and event logging for Story 4.1 implementation
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

from ..models import SummarizationEvent, TierUsageAnalytics, ProcessingTier

logger = logging.getLogger(__name__)


class ProductionMonitoringMixin:
    """
    Basic production monitoring for adaptive FHIR summarization
    Provides event logging and basic analytics for Story 4.1
    Full implementation in Story 4.3
    """
    
    def __init__(self):
        # Simple in-memory event storage for Story 4.1
        # Will be replaced with persistent storage in Story 4.3
        self.events: deque = deque(maxlen=1000)  # Last 1000 events
        self.tier_counters = defaultdict(int)
        self.start_time = datetime.now()
        
        logger.info("ProductionMonitoringMixin initialized for Epic 4 Story 4.1")
    
    async def log_summarization_event(self, event: SummarizationEvent):
        """Log processing event with basic metrics tracking"""
        
        try:
            # Store event
            self.events.append(event)
            
            # Update tier counters
            self.tier_counters[event.tier_selected] += 1
            
            # Basic logging
            logger.info(
                f"Summarization event logged: "
                f"request_id={event.request_id}, "
                f"tier={event.tier_selected.value}, "
                f"processing_time={event.processing_time_ms:.1f}ms, "
                f"complexity={event.bundle_complexity_score:.1f}, "
                f"resource_count={event.resource_count}"
            )
            
            # Log cost-related events
            if event.tier_selected == ProcessingTier.LLM_FALLBACK:
                logger.warning(
                    f"LLM fallback used: request_id={event.request_id}, "
                    f"tokens={event.llm_tokens_used}, "
                    f"estimated_cost=${event.estimated_cost_usd:.4f}"
                )
            
            # Log fallback events
            if event.tier_fallback_occurred:
                logger.warning(
                    f"Tier fallback occurred: request_id={event.request_id}, "
                    f"original_tier={event.original_tier_attempted}, "
                    f"final_tier={event.tier_selected}, "
                    f"reason={event.fallback_reason}"
                )
            
            # Log errors
            if event.error_occurred:
                logger.error(
                    f"Processing error: request_id={event.request_id}, "
                    f"error_type={event.error_type}, "
                    f"error_message={event.error_message}"
                )
        
        except Exception as e:
            logger.error(f"Failed to log summarization event: {e}")
    
    async def get_tier_usage_analytics(self, window_hours: int = 24) -> TierUsageAnalytics:
        """Get basic tier usage analytics for the specified time window"""
        
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        
        # Filter events within time window
        recent_events = [e for e in self.events if e.timestamp >= cutoff_time]
        
        if not recent_events:
            return self._create_empty_analytics(window_hours)
        
        # Calculate tier usage
        tier_counts = defaultdict(int)
        total_llm_tokens = 0
        total_cost = 0.0
        processing_times = []
        quality_scores = []
        error_count = 0
        fallback_count = 0
        
        for event in recent_events:
            tier_counts[event.tier_selected] += 1
            processing_times.append(event.processing_time_ms)
            
            if event.output_quality_score:
                quality_scores.append(event.output_quality_score)
            
            if event.llm_tokens_used:
                total_llm_tokens += event.llm_tokens_used
            
            if event.estimated_cost_usd:
                total_cost += event.estimated_cost_usd
            
            if event.error_occurred:
                error_count += 1
            
            if event.tier_fallback_occurred:
                fallback_count += 1
        
        total_requests = len(recent_events)
        
        # Calculate percentages
        rule_based_count = tier_counts[ProcessingTier.RULE_BASED]
        generic_count = tier_counts[ProcessingTier.GENERIC_TEMPLATE]
        llm_count = tier_counts[ProcessingTier.LLM_FALLBACK]
        emergency_count = tier_counts[ProcessingTier.EMERGENCY_FALLBACK]
        
        # Performance metrics
        avg_processing_time = sum(processing_times) / len(processing_times)
        processing_times.sort()
        p95_time = processing_times[int(len(processing_times) * 0.95)]
        p99_time = processing_times[int(len(processing_times) * 0.99)]
        
        # Quality metrics
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Cost optimization score calculation
        rule_based_pct = (rule_based_count / total_requests) * 100
        llm_pct = (llm_count / total_requests) * 100
        
        # Cost optimization effectiveness (higher is better)
        cost_optimization_score = max(0.0, min(1.0, (rule_based_pct / 75.0) * 0.7 + ((100 - llm_pct) / 93.0) * 0.3))
        
        return TierUsageAnalytics(
            time_window_hours=window_hours,
            total_requests=total_requests,
            rule_based_count=rule_based_count,
            generic_template_count=generic_count,
            llm_fallback_count=llm_count,
            emergency_fallback_count=emergency_count,
            rule_based_percentage=rule_based_pct,
            generic_template_percentage=(generic_count / total_requests) * 100,
            llm_fallback_percentage=llm_pct,
            emergency_fallback_percentage=(emergency_count / total_requests) * 100,
            total_llm_tokens=total_llm_tokens,
            estimated_total_cost_usd=total_cost,
            cost_per_request_usd=total_cost / total_requests,
            average_processing_time_ms=avg_processing_time,
            p95_processing_time_ms=p95_time,
            p99_processing_time_ms=p99_time,
            average_quality_score=avg_quality,
            fallback_rate=(fallback_count / total_requests) * 100,
            error_rate=(error_count / total_requests) * 100,
            rule_based_variance=rule_based_pct - 75.0,  # vs 75% target
            llm_variance=llm_pct - 7.0,  # vs 7% target
            cost_optimization_score=cost_optimization_score
        )
    
    def _create_empty_analytics(self, window_hours: int) -> TierUsageAnalytics:
        """Create empty analytics for when no events exist"""
        
        return TierUsageAnalytics(
            time_window_hours=window_hours,
            total_requests=0,
            rule_based_count=0,
            generic_template_count=0,
            llm_fallback_count=0,
            emergency_fallback_count=0,
            rule_based_percentage=0.0,
            generic_template_percentage=0.0,
            llm_fallback_percentage=0.0,
            emergency_fallback_percentage=0.0,
            total_llm_tokens=0,
            estimated_total_cost_usd=0.0,
            cost_per_request_usd=0.0,
            average_processing_time_ms=0.0,
            p95_processing_time_ms=0.0,
            p99_processing_time_ms=0.0,
            average_quality_score=0.0,
            fallback_rate=0.0,
            error_rate=0.0,
            rule_based_variance=0.0,
            llm_variance=0.0,
            cost_optimization_score=1.0  # Perfect optimization when no LLM usage
        )
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get basic monitoring statistics"""
        
        total_events = len(self.events)
        uptime = datetime.now() - self.start_time
        
        tier_percentages = {}
        if total_events > 0:
            for tier, count in self.tier_counters.items():
                tier_percentages[tier.value] = (count / total_events) * 100
        
        return {
            "total_events": total_events,
            "uptime_seconds": uptime.total_seconds(),
            "tier_usage": dict(self.tier_counters),
            "tier_percentages": tier_percentages,
            "events_capacity": self.events.maxlen,
            "monitoring_version": "story-4.1-basic"
        }
    
    async def check_cost_thresholds(self) -> Dict[str, Any]:
        """Basic cost threshold checking (placeholder for Story 4.3)"""
        
        analytics = await self.get_tier_usage_analytics(window_hours=24)
        
        alerts = []
        
        # Check if LLM usage exceeds target
        if analytics.llm_fallback_percentage > 10.0:  # 10% threshold
            alerts.append({
                "type": "llm_usage_high",
                "severity": "warning" if analytics.llm_fallback_percentage < 15.0 else "critical",
                "message": f"LLM usage at {analytics.llm_fallback_percentage:.1f}% (target: <7%)",
                "current_value": analytics.llm_fallback_percentage,
                "threshold": 10.0
            })
        
        # Check if rule-based usage is below target
        if analytics.rule_based_percentage < 60.0:  # Below 60% is concerning
            alerts.append({
                "type": "rule_based_usage_low",
                "severity": "warning",
                "message": f"Rule-based usage at {analytics.rule_based_percentage:.1f}% (target: >70%)",
                "current_value": analytics.rule_based_percentage,
                "threshold": 70.0
            })
        
        return {
            "alerts": alerts,
            "cost_optimization_score": analytics.cost_optimization_score,
            "monitoring_timestamp": datetime.now().isoformat()
        }