"""
Epic 4: Comprehensive Tests for Production Monitoring
Tests monitoring, analytics, and cost control functionality

Coverage:
- Event logging and storage
- Tier usage analytics calculation
- Time window filtering
- Performance metrics (avg, p95, p99)
- Quality score aggregation
- Cost calculation and optimization
- Threshold alerts and warnings
- Error and fallback tracking
- Edge cases and validation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from collections import deque

from src.nl_fhir.services.summarization.monitoring.production_monitoring import ProductionMonitoringMixin
from src.nl_fhir.services.summarization.models import (
    SummarizationEvent,
    TierUsageAnalytics,
    ProcessingTier
)


class TestProductionMonitoringInitialization:
    """Test monitoring mixin initialization"""

    def test_monitoring_initialization(self):
        """Test monitoring initializes with correct defaults"""
        monitoring = ProductionMonitoringMixin()

        assert isinstance(monitoring.events, deque)
        assert monitoring.events.maxlen == 1000
        assert isinstance(monitoring.tier_counters, dict)
        assert isinstance(monitoring.start_time, datetime)

    def test_monitoring_events_capacity(self):
        """Test events deque has correct capacity"""
        monitoring = ProductionMonitoringMixin()

        assert monitoring.events.maxlen == 1000


class TestEventLogging:
    """Test summarization event logging"""

    @pytest.fixture
    def monitoring(self):
        """Create monitoring instance"""
        return ProductionMonitoringMixin()

    def create_test_event(self, **kwargs) -> SummarizationEvent:
        """Helper to create test events"""
        defaults = {
            "timestamp": datetime.now(),
            "request_id": "test-request-123",
            "bundle_id": "test-bundle-123",
            "resource_types": ["Patient", "MedicationRequest"],
            "resource_count": 2,
            "bundle_complexity_score": 3.5,
            "has_rare_resources": False,
            "tier_selected": ProcessingTier.RULE_BASED,
            "analysis_time_ms": 15.0,
            "processing_time_ms": 45.0,
            "total_time_ms": 60.0,
            "server_instance": "test-server-1",
            "api_version": "4.1.0",
            "user_role": "physician"
        }
        defaults.update(kwargs)
        return SummarizationEvent(**defaults)

    @pytest.mark.asyncio
    async def test_log_basic_event(self, monitoring):
        """Test logging a basic summarization event"""
        event = self.create_test_event()

        await monitoring.log_summarization_event(event)

        assert len(monitoring.events) == 1
        assert monitoring.events[0] == event
        assert monitoring.tier_counters[ProcessingTier.RULE_BASED] == 1

    @pytest.mark.asyncio
    async def test_log_multiple_events(self, monitoring):
        """Test logging multiple events"""
        events = [
            self.create_test_event(request_id=f"req-{i}")
            for i in range(5)
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        assert len(monitoring.events) == 5
        assert monitoring.tier_counters[ProcessingTier.RULE_BASED] == 5

    @pytest.mark.asyncio
    async def test_log_different_tiers(self, monitoring):
        """Test logging events with different tiers"""
        events = [
            self.create_test_event(tier_selected=ProcessingTier.RULE_BASED),
            self.create_test_event(tier_selected=ProcessingTier.GENERIC_TEMPLATE),
            self.create_test_event(tier_selected=ProcessingTier.LLM_FALLBACK),
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        assert monitoring.tier_counters[ProcessingTier.RULE_BASED] == 1
        assert monitoring.tier_counters[ProcessingTier.GENERIC_TEMPLATE] == 1
        assert monitoring.tier_counters[ProcessingTier.LLM_FALLBACK] == 1

    @pytest.mark.asyncio
    async def test_log_llm_event_with_cost(self, monitoring, caplog):
        """Test logging LLM event includes cost warning"""
        event = self.create_test_event(
            tier_selected=ProcessingTier.LLM_FALLBACK,
            llm_tokens_used=1500,
            estimated_cost_usd=0.0225
        )

        with caplog.at_level("WARNING"):
            await monitoring.log_summarization_event(event)

        # Should log LLM usage warning
        assert any("LLM fallback used" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_log_fallback_event(self, monitoring, caplog):
        """Test logging tier fallback event"""
        event = self.create_test_event(
            tier_selected=ProcessingTier.GENERIC_TEMPLATE,
            tier_fallback_occurred=True,
            original_tier_attempted=ProcessingTier.RULE_BASED,
            fallback_reason="Missing summarizer for resource type"
        )

        with caplog.at_level("WARNING"):
            await monitoring.log_summarization_event(event)

        # Should log fallback warning
        assert any("Tier fallback occurred" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_log_error_event(self, monitoring, caplog):
        """Test logging error event"""
        event = self.create_test_event(
            error_occurred=True,
            error_type="ValidationError",
            error_message="Invalid FHIR resource"
        )

        with caplog.at_level("ERROR"):
            await monitoring.log_summarization_event(event)

        # Should log error
        assert any("Processing error" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_events_maxlen_enforcement(self, monitoring):
        """Test events deque enforces max length"""
        # Log more than max capacity
        for i in range(1100):
            event = self.create_test_event(request_id=f"req-{i}")
            await monitoring.log_summarization_event(event)

        # Should only keep last 1000
        assert len(monitoring.events) == 1000
        # Should have oldest events dropped
        assert monitoring.events[0].request_id == "req-100"


class TestTierUsageAnalytics:
    """Test tier usage analytics calculation"""

    @pytest.fixture
    def monitoring(self):
        """Create monitoring instance"""
        return ProductionMonitoringMixin()

    def create_test_event(self, **kwargs) -> SummarizationEvent:
        """Helper to create test events"""
        defaults = {
            "timestamp": datetime.now(),
            "request_id": "test-request",
            "bundle_id": "test-bundle",
            "resource_types": ["Patient"],
            "resource_count": 1,
            "bundle_complexity_score": 2.0,
            "has_rare_resources": False,
            "tier_selected": ProcessingTier.RULE_BASED,
            "analysis_time_ms": 10.0,
            "processing_time_ms": 30.0,
            "total_time_ms": 40.0,
            "output_quality_score": 0.95,
            "server_instance": "test-server",
            "api_version": "4.1.0",
            "user_role": "physician"
        }
        defaults.update(kwargs)
        return SummarizationEvent(**defaults)

    @pytest.mark.asyncio
    async def test_get_analytics_empty_events(self, monitoring):
        """Test analytics with no events"""
        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        assert analytics.total_requests == 0
        assert analytics.rule_based_count == 0
        assert analytics.llm_fallback_count == 0
        assert analytics.estimated_total_cost_usd == 0.0
        assert analytics.cost_optimization_score == 1.0  # Perfect when no LLM

    @pytest.mark.asyncio
    async def test_get_analytics_single_event(self, monitoring):
        """Test analytics with single event"""
        event = self.create_test_event(
            tier_selected=ProcessingTier.RULE_BASED,
            processing_time_ms=50.0,
            output_quality_score=0.95
        )

        await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        assert analytics.total_requests == 1
        assert analytics.rule_based_count == 1
        assert analytics.rule_based_percentage == 100.0
        assert analytics.average_processing_time_ms == 50.0
        assert analytics.average_quality_score == 0.95

    @pytest.mark.asyncio
    async def test_get_analytics_multiple_events(self, monitoring):
        """Test analytics with multiple events"""
        events = [
            self.create_test_event(tier_selected=ProcessingTier.RULE_BASED, processing_time_ms=30.0),
            self.create_test_event(tier_selected=ProcessingTier.RULE_BASED, processing_time_ms=40.0),
            self.create_test_event(tier_selected=ProcessingTier.GENERIC_TEMPLATE, processing_time_ms=50.0),
            self.create_test_event(tier_selected=ProcessingTier.LLM_FALLBACK, processing_time_ms=200.0,
                                 llm_tokens_used=1000, estimated_cost_usd=0.015)
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        assert analytics.total_requests == 4
        assert analytics.rule_based_count == 2
        assert analytics.generic_template_count == 1
        assert analytics.llm_fallback_count == 1
        assert analytics.rule_based_percentage == 50.0
        assert analytics.llm_fallback_percentage == 25.0

    @pytest.mark.asyncio
    async def test_analytics_time_window_filtering(self, monitoring):
        """Test analytics filters events by time window"""
        now = datetime.now()

        # Create events at different times
        old_event = self.create_test_event(
            timestamp=now - timedelta(hours=25),  # Outside 24hr window
            tier_selected=ProcessingTier.RULE_BASED
        )
        recent_event = self.create_test_event(
            timestamp=now - timedelta(hours=1),  # Within 24hr window
            tier_selected=ProcessingTier.RULE_BASED
        )

        await monitoring.log_summarization_event(old_event)
        await monitoring.log_summarization_event(recent_event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # Should only count recent event
        assert analytics.total_requests == 1

    @pytest.mark.asyncio
    async def test_analytics_cost_calculation(self, monitoring):
        """Test cost calculation in analytics"""
        events = [
            self.create_test_event(
                tier_selected=ProcessingTier.LLM_FALLBACK,
                llm_tokens_used=1000,
                estimated_cost_usd=0.015
            ),
            self.create_test_event(
                tier_selected=ProcessingTier.LLM_FALLBACK,
                llm_tokens_used=2000,
                estimated_cost_usd=0.030
            )
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        assert analytics.total_llm_tokens == 3000
        assert analytics.estimated_total_cost_usd == 0.045
        assert analytics.cost_per_request_usd == 0.0225

    @pytest.mark.asyncio
    async def test_analytics_performance_metrics(self, monitoring):
        """Test performance metrics calculation"""
        # Create events with varying processing times
        processing_times = [10.0, 20.0, 30.0, 40.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0]
        events = [
            self.create_test_event(processing_time_ms=time)
            for time in processing_times
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # Average should be mean of all values
        expected_avg = sum(processing_times) / len(processing_times)
        assert analytics.average_processing_time_ms == expected_avg

        # p95 should be approximately 95th percentile
        assert analytics.p95_processing_time_ms >= 200.0

        # p99 should be approximately 99th percentile
        assert analytics.p99_processing_time_ms >= 250.0

    @pytest.mark.asyncio
    async def test_analytics_quality_score_aggregation(self, monitoring):
        """Test quality score aggregation"""
        events = [
            self.create_test_event(output_quality_score=0.95),
            self.create_test_event(output_quality_score=0.90),
            self.create_test_event(output_quality_score=0.85),
            self.create_test_event(output_quality_score=None)  # No quality score
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # Should average non-None scores
        expected_avg = (0.95 + 0.90 + 0.85) / 3
        assert analytics.average_quality_score == pytest.approx(expected_avg, rel=0.01)

    @pytest.mark.asyncio
    async def test_analytics_error_rate(self, monitoring):
        """Test error rate calculation"""
        events = [
            self.create_test_event(error_occurred=False),
            self.create_test_event(error_occurred=False),
            self.create_test_event(error_occurred=True),
            self.create_test_event(error_occurred=False)
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # 1 error out of 4 events = 25%
        assert analytics.error_rate == 25.0

    @pytest.mark.asyncio
    async def test_analytics_fallback_rate(self, monitoring):
        """Test fallback rate calculation"""
        events = [
            self.create_test_event(tier_fallback_occurred=False),
            self.create_test_event(tier_fallback_occurred=True),
            self.create_test_event(tier_fallback_occurred=True),
            self.create_test_event(tier_fallback_occurred=False)
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # 2 fallbacks out of 4 events = 50%
        assert analytics.fallback_rate == 50.0

    @pytest.mark.asyncio
    async def test_analytics_cost_optimization_score(self, monitoring):
        """Test cost optimization score calculation"""
        # Scenario 1: Ideal distribution (75% rule-based, 7% LLM)
        events = []
        for _ in range(75):
            events.append(self.create_test_event(tier_selected=ProcessingTier.RULE_BASED))
        for _ in range(18):
            events.append(self.create_test_event(tier_selected=ProcessingTier.GENERIC_TEMPLATE))
        for _ in range(7):
            events.append(self.create_test_event(tier_selected=ProcessingTier.LLM_FALLBACK))

        for event in events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # Should have high optimization score
        assert analytics.cost_optimization_score > 0.9

    @pytest.mark.asyncio
    async def test_analytics_tier_variance(self, monitoring):
        """Test tier variance calculation"""
        # 80% rule-based (5% above target of 75%)
        events = []
        for _ in range(80):
            events.append(self.create_test_event(tier_selected=ProcessingTier.RULE_BASED))
        for _ in range(20):
            events.append(self.create_test_event(tier_selected=ProcessingTier.GENERIC_TEMPLATE))

        for event in events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # Variance from 75% target
        assert analytics.rule_based_variance == 5.0  # 80% - 75%

        # Variance from 7% target (0% LLM)
        assert analytics.llm_variance == -7.0  # 0% - 7%


class TestMonitoringStats:
    """Test monitoring statistics retrieval"""

    @pytest.fixture
    def monitoring(self):
        """Create monitoring instance"""
        return ProductionMonitoringMixin()

    def create_test_event(self, **kwargs) -> SummarizationEvent:
        """Helper to create test events"""
        defaults = {
            "timestamp": datetime.now(),
            "request_id": "test-request",
            "bundle_id": "test-bundle",
            "resource_types": ["Patient"],
            "resource_count": 1,
            "bundle_complexity_score": 2.0,
            "has_rare_resources": False,
            "tier_selected": ProcessingTier.RULE_BASED,
            "analysis_time_ms": 10.0,
            "processing_time_ms": 30.0,
            "total_time_ms": 40.0,
            "server_instance": "test-server",
            "api_version": "4.1.0",
            "user_role": "physician"
        }
        defaults.update(kwargs)
        return SummarizationEvent(**defaults)

    @pytest.mark.asyncio
    async def test_get_monitoring_stats_empty(self, monitoring):
        """Test getting stats with no events"""
        stats = monitoring.get_monitoring_stats()

        assert stats["total_events"] == 0
        assert "uptime_seconds" in stats
        assert stats["tier_percentages"] == {}
        assert stats["events_capacity"] == 1000

    @pytest.mark.asyncio
    async def test_get_monitoring_stats_with_events(self, monitoring):
        """Test getting stats with events"""
        events = [
            self.create_test_event(tier_selected=ProcessingTier.RULE_BASED),
            self.create_test_event(tier_selected=ProcessingTier.RULE_BASED),
            self.create_test_event(tier_selected=ProcessingTier.LLM_FALLBACK)
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        stats = monitoring.get_monitoring_stats()

        assert stats["total_events"] == 3
        assert stats["tier_percentages"]["rule_based"] == pytest.approx(66.67, rel=0.01)
        assert stats["tier_percentages"]["llm_fallback"] == pytest.approx(33.33, rel=0.01)

    def test_monitoring_stats_uptime(self, monitoring):
        """Test uptime tracking in stats"""
        stats = monitoring.get_monitoring_stats()

        assert stats["uptime_seconds"] > 0
        assert isinstance(stats["uptime_seconds"], float)


class TestCostThresholds:
    """Test cost threshold checking and alerts"""

    @pytest.fixture
    def monitoring(self):
        """Create monitoring instance"""
        return ProductionMonitoringMixin()

    def create_test_event(self, **kwargs) -> SummarizationEvent:
        """Helper to create test events"""
        defaults = {
            "timestamp": datetime.now(),
            "request_id": "test-request",
            "bundle_id": "test-bundle",
            "resource_types": ["Patient"],
            "resource_count": 1,
            "bundle_complexity_score": 2.0,
            "has_rare_resources": False,
            "tier_selected": ProcessingTier.RULE_BASED,
            "analysis_time_ms": 10.0,
            "processing_time_ms": 30.0,
            "total_time_ms": 40.0,
            "server_instance": "test-server",
            "api_version": "4.1.0",
            "user_role": "physician"
        }
        defaults.update(kwargs)
        return SummarizationEvent(**defaults)

    @pytest.mark.asyncio
    async def test_check_thresholds_no_alerts(self, monitoring):
        """Test threshold check with no alerts"""
        # 80% rule-based, 20% generic - optimal
        events = []
        for _ in range(80):
            events.append(self.create_test_event(tier_selected=ProcessingTier.RULE_BASED))
        for _ in range(20):
            events.append(self.create_test_event(tier_selected=ProcessingTier.GENERIC_TEMPLATE))

        for event in events:
            await monitoring.log_summarization_event(event)

        result = await monitoring.check_cost_thresholds()

        assert len(result["alerts"]) == 0
        assert result["cost_optimization_score"] > 0.8

    @pytest.mark.asyncio
    async def test_check_thresholds_llm_warning(self, monitoring):
        """Test LLM usage warning threshold"""
        # 12% LLM usage (above 10% threshold)
        events = []
        for _ in range(88):
            events.append(self.create_test_event(tier_selected=ProcessingTier.RULE_BASED))
        for _ in range(12):
            events.append(self.create_test_event(tier_selected=ProcessingTier.LLM_FALLBACK))

        for event in events:
            await monitoring.log_summarization_event(event)

        result = await monitoring.check_cost_thresholds()

        # Should have LLM usage warning
        assert len(result["alerts"]) > 0
        llm_alert = next((a for a in result["alerts"] if a["type"] == "llm_usage_high"), None)
        assert llm_alert is not None
        assert llm_alert["severity"] == "warning"
        assert llm_alert["current_value"] == 12.0

    @pytest.mark.asyncio
    async def test_check_thresholds_llm_critical(self, monitoring):
        """Test LLM usage critical threshold"""
        # 20% LLM usage (above 15% critical threshold)
        events = []
        for _ in range(80):
            events.append(self.create_test_event(tier_selected=ProcessingTier.RULE_BASED))
        for _ in range(20):
            events.append(self.create_test_event(tier_selected=ProcessingTier.LLM_FALLBACK))

        for event in events:
            await monitoring.log_summarization_event(event)

        result = await monitoring.check_cost_thresholds()

        # Should have critical alert
        llm_alert = next((a for a in result["alerts"] if a["type"] == "llm_usage_high"), None)
        assert llm_alert is not None
        assert llm_alert["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_check_thresholds_rule_based_low(self, monitoring):
        """Test rule-based usage low threshold"""
        # 50% rule-based (below 60% threshold)
        events = []
        for _ in range(50):
            events.append(self.create_test_event(tier_selected=ProcessingTier.RULE_BASED))
        for _ in range(50):
            events.append(self.create_test_event(tier_selected=ProcessingTier.GENERIC_TEMPLATE))

        for event in events:
            await monitoring.log_summarization_event(event)

        result = await monitoring.check_cost_thresholds()

        # Should have rule-based low warning
        rule_alert = next((a for a in result["alerts"] if a["type"] == "rule_based_usage_low"), None)
        assert rule_alert is not None
        assert rule_alert["severity"] == "warning"
        assert rule_alert["current_value"] == 50.0

    @pytest.mark.asyncio
    async def test_check_thresholds_multiple_alerts(self, monitoring):
        """Test multiple simultaneous alerts"""
        # 40% rule-based (low), 15% LLM (critical)
        events = []
        for _ in range(40):
            events.append(self.create_test_event(tier_selected=ProcessingTier.RULE_BASED))
        for _ in range(45):
            events.append(self.create_test_event(tier_selected=ProcessingTier.GENERIC_TEMPLATE))
        for _ in range(15):
            events.append(self.create_test_event(tier_selected=ProcessingTier.LLM_FALLBACK))

        for event in events:
            await monitoring.log_summarization_event(event)

        result = await monitoring.check_cost_thresholds()

        # Should have both alerts
        assert len(result["alerts"]) == 2

    @pytest.mark.asyncio
    async def test_check_thresholds_timestamp(self, monitoring):
        """Test threshold check includes timestamp"""
        result = await monitoring.check_cost_thresholds()

        assert "monitoring_timestamp" in result
        # Should be ISO format datetime
        datetime.fromisoformat(result["monitoring_timestamp"])


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def monitoring(self):
        """Create monitoring instance"""
        return ProductionMonitoringMixin()

    def create_test_event(self, **kwargs) -> SummarizationEvent:
        """Helper to create test events"""
        defaults = {
            "timestamp": datetime.now(),
            "request_id": "test-request",
            "bundle_id": "test-bundle",
            "resource_types": ["Patient"],
            "resource_count": 1,
            "bundle_complexity_score": 2.0,
            "has_rare_resources": False,
            "tier_selected": ProcessingTier.RULE_BASED,
            "analysis_time_ms": 10.0,
            "processing_time_ms": 30.0,
            "total_time_ms": 40.0,
            "server_instance": "test-server",
            "api_version": "4.1.0",
            "user_role": "physician"
        }
        defaults.update(kwargs)
        return SummarizationEvent(**defaults)

    @pytest.mark.asyncio
    async def test_analytics_with_all_old_events(self, monitoring):
        """Test analytics when all events are outside time window"""
        old_timestamp = datetime.now() - timedelta(hours=48)
        event = self.create_test_event(timestamp=old_timestamp)

        await monitoring.log_summarization_event(event)

        # Request 24-hour window analytics
        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # Should return empty analytics
        assert analytics.total_requests == 0

    @pytest.mark.asyncio
    async def test_analytics_with_mixed_timestamps(self, monitoring):
        """Test analytics filters correctly with mixed timestamps"""
        now = datetime.now()

        old_events = [
            self.create_test_event(timestamp=now - timedelta(hours=30), request_id=f"old-{i}")
            for i in range(5)
        ]
        recent_events = [
            self.create_test_event(timestamp=now - timedelta(hours=5), request_id=f"recent-{i}")
            for i in range(3)
        ]

        for event in old_events + recent_events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # Should only count 3 recent events
        assert analytics.total_requests == 3

    @pytest.mark.asyncio
    async def test_analytics_with_custom_window(self, monitoring):
        """Test analytics with custom time window"""
        now = datetime.now()

        # Event 10 hours ago
        event = self.create_test_event(timestamp=now - timedelta(hours=10))
        await monitoring.log_summarization_event(event)

        # 24-hour window should include it
        analytics_24h = await monitoring.get_tier_usage_analytics(window_hours=24)
        assert analytics_24h.total_requests == 1

        # 6-hour window should exclude it
        analytics_6h = await monitoring.get_tier_usage_analytics(window_hours=6)
        assert analytics_6h.total_requests == 0

    @pytest.mark.asyncio
    async def test_analytics_percentiles_single_value(self, monitoring):
        """Test percentile calculation with single value"""
        event = self.create_test_event(processing_time_ms=100.0)
        await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # With single value, all percentiles should be same
        assert analytics.average_processing_time_ms == 100.0
        assert analytics.p95_processing_time_ms == 100.0
        assert analytics.p99_processing_time_ms == 100.0

    @pytest.mark.asyncio
    async def test_analytics_with_none_quality_scores(self, monitoring):
        """Test analytics when all quality scores are None"""
        events = [
            self.create_test_event(output_quality_score=None)
            for _ in range(5)
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # Should handle gracefully
        assert analytics.average_quality_score == 0.0

    @pytest.mark.asyncio
    async def test_zero_cost_optimization_edge_case(self, monitoring):
        """Test cost optimization with 100% LLM usage"""
        events = [
            self.create_test_event(tier_selected=ProcessingTier.LLM_FALLBACK)
            for _ in range(10)
        ]

        for event in events:
            await monitoring.log_summarization_event(event)

        analytics = await monitoring.get_tier_usage_analytics(window_hours=24)

        # Cost optimization should be low (but not negative)
        assert analytics.cost_optimization_score >= 0.0
        assert analytics.cost_optimization_score <= 1.0
