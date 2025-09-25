"""
Epic 4 Production Monitoring for FHIR Bundle Summarization
Monitoring and analytics mixin for tracking summarization performance
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

from .models import SummarizationEvent, ProcessingTier, TierUsageAnalytics

logger = logging.getLogger(__name__)


class ProductionMonitoringMixin:
    """
    Production monitoring capabilities for Epic 4 summarization services
    Tracks performance, costs, and quality metrics
    """

    def __init__(self):
        # In-memory event store (in production, this would be a database)
        self._events: deque = deque(maxlen=1000)  # Keep last 1000 events
        self._tier_costs = {
            ProcessingTier.TEMPLATE: 0.001,  # $0.001 per request
            ProcessingTier.GENERIC: 0.010,   # $0.01 per request
            ProcessingTier.LLM: 0.050        # $0.05 per request
        }

    def record_event(self, event: SummarizationEvent) -> None:
        """Record a summarization processing event"""
        self._events.append(event)

        # Log key metrics
        logger.info(
            f"Summarization event: {event.request_id} | "
            f"Tier: {event.tier_used.value} | "
            f"Time: {event.processing_time_ms:.1f}ms | "
            f"Success: {event.success}"
        )

        # Log warnings for performance issues
        if event.processing_time_ms > 5000:  # 5 second threshold
            logger.warning(
                f"Slow summarization: {event.request_id} took {event.processing_time_ms:.1f}ms"
            )

        if not event.success:
            logger.error(
                f"Summarization failed: {event.request_id} - {event.error_message}"
            )

    def get_recent_analytics(self, hours: int = 24) -> TierUsageAnalytics:
        """Get analytics for recent events"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [
            event for event in self._events
            if event.timestamp >= cutoff_time
        ]

        if not recent_events:
            return TierUsageAnalytics(
                total_requests=0,
                tier_distribution={},
                avg_processing_time={},
                success_rates={},
                cost_analysis={}
            )

        # Calculate tier distribution
        tier_counts = defaultdict(int)
        tier_times = defaultdict(list)
        tier_successes = defaultdict(list)

        for event in recent_events:
            tier_counts[event.tier_used] += 1
            tier_times[event.tier_used].append(event.processing_time_ms)
            tier_successes[event.tier_used].append(event.success)

        # Calculate averages and rates
        avg_processing_time = {}
        success_rates = {}
        total_cost = 0.0

        for tier, count in tier_counts.items():
            avg_processing_time[tier] = sum(tier_times[tier]) / len(tier_times[tier])
            success_rates[tier] = sum(tier_successes[tier]) / len(tier_successes[tier])
            total_cost += count * self._tier_costs[tier]

        # Cost breakdown
        cost_analysis = {
            "total_cost_usd": total_cost,
            "cost_per_request_usd": total_cost / len(recent_events) if recent_events else 0,
            "tier_costs": {
                tier.value: count * self._tier_costs[tier]
                for tier, count in tier_counts.items()
            }
        }

        return TierUsageAnalytics(
            total_requests=len(recent_events),
            tier_distribution=tier_counts,
            avg_processing_time=avg_processing_time,
            success_rates=success_rates,
            cost_analysis=cost_analysis
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the last 24 hours"""
        analytics = self.get_recent_analytics(24)

        if analytics.total_requests == 0:
            return {
                "status": "no_data",
                "message": "No requests in the last 24 hours"
            }

        # Calculate overall metrics
        total_success = sum(
            count * analytics.success_rates.get(tier, 0)
            for tier, count in analytics.tier_distribution.items()
        )
        overall_success_rate = total_success / analytics.total_requests

        total_time = sum(
            count * analytics.avg_processing_time.get(tier, 0)
            for tier, count in analytics.tier_distribution.items()
        )
        overall_avg_time = total_time / analytics.total_requests

        return {
            "status": "healthy" if overall_success_rate > 0.95 else "degraded",
            "total_requests": analytics.total_requests,
            "success_rate": overall_success_rate,
            "avg_response_time_ms": overall_avg_time,
            "cost_per_request_usd": analytics.cost_analysis.get("cost_per_request_usd", 0),
            "tier_usage": {
                tier.value: count for tier, count in analytics.tier_distribution.items()
            },
            "most_used_tier": max(analytics.tier_distribution.items(), key=lambda x: x[1])[0].value if analytics.tier_distribution else "none"
        }

    def should_scale_tier(self, tier: ProcessingTier, load_threshold: float = 0.8) -> bool:
        """Determine if a processing tier should be scaled"""
        analytics = self.get_recent_analytics(1)  # Last hour

        if analytics.total_requests < 10:  # Not enough data
            return False

        tier_usage_ratio = analytics.tier_distribution.get(tier, 0) / analytics.total_requests
        return tier_usage_ratio > load_threshold

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status for monitoring systems"""
        try:
            performance = self.get_performance_summary()

            if performance.get("status") == "no_data":
                return {"status": "unknown", "details": performance}

            health_score = performance["success_rate"] * 0.6 + (
                1.0 - min(performance["avg_response_time_ms"] / 10000, 1.0)
            ) * 0.4

            status = "healthy"
            if health_score < 0.7:
                status = "unhealthy"
            elif health_score < 0.9:
                status = "degraded"

            return {
                "status": status,
                "health_score": health_score,
                "details": performance,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }