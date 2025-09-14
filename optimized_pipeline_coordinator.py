#!/usr/bin/env python3
"""
Optimized Pipeline Coordinator - Phase 3 of 3-Tier Architecture Migration

This system coordinates the new streamlined 3-tier architecture:
- Tier 1: Enhanced MedSpaCy Clinical Intelligence
- Tier 2: Smart Regex Consolidation
- Tier 3: LLM Medical Safety Escalation

Design Philosophy:
- Performance-first pipeline coordination
- Intelligent caching and memoization
- Parallel processing where safe
- Comprehensive performance monitoring
- Graceful degradation and fallback handling
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Import our new 3-tier components
from smart_regex_consolidator import SmartRegexConsolidator
from simplified_escalation_engine import SimplifiedEscalationEngine, EscalationDecision

logger = logging.getLogger(__name__)

class ProcessingMode(Enum):
    """Pipeline processing modes for different performance requirements"""
    SPEED_OPTIMIZED = "speed_optimized"      # <500ms target
    BALANCED = "balanced"                    # <1000ms target
    QUALITY_OPTIMIZED = "quality_optimized" # <2000ms target

class TierStatus(Enum):
    """Status of individual tiers"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TierResult:
    """Result from individual tier processing"""
    tier_name: str
    status: TierStatus
    processing_time_ms: float
    entities: Dict[str, List]
    confidence: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PipelineResult:
    """Complete pipeline processing result"""
    request_id: str
    total_processing_time_ms: float
    processing_mode: ProcessingMode
    tier_results: List[TierResult]
    final_entities: Dict[str, List]
    escalation_decision: Optional[EscalationDecision]
    pipeline_confidence: float
    cache_hits: int = 0
    performance_warnings: List[str] = field(default_factory=list)
    quality_score: float = 0.0

class OptimizedPipelineCoordinator:
    """
    High-performance coordinator for the new 3-tier NLP architecture

    Manages optimal flow through:
    1. Enhanced MedSpaCy → 2. Smart Regex Consolidation → 3. LLM Safety Escalation
    """

    def __init__(self, enable_caching: bool = True, enable_parallel: bool = True):
        # Initialize tier components
        self.consolidator = SmartRegexConsolidator()
        self.escalation_engine = SimplifiedEscalationEngine()

        # Performance optimization settings
        self.enable_caching = enable_caching
        self.enable_parallel = enable_parallel

        # Result caching for repeated inputs
        self.result_cache = {}  # text_hash -> cached_result
        self.cache_ttl = timedelta(hours=1)  # Cache results for 1 hour

        # Performance monitoring
        self.performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "avg_processing_time_ms": 0.0,
            "tier_performance": {
                "tier1_avg_ms": 0.0,
                "tier2_avg_ms": 0.0,
                "tier3_avg_ms": 0.0
            },
            "escalation_rate": 0.0,
            "quality_scores": []
        }

        # Thread pool for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=3) if enable_parallel else None

        # Performance thresholds
        self.performance_targets = {
            ProcessingMode.SPEED_OPTIMIZED: 500,    # 500ms
            ProcessingMode.BALANCED: 1000,          # 1000ms
            ProcessingMode.QUALITY_OPTIMIZED: 2000  # 2000ms
        }

    async def process_clinical_text(
        self,
        text: str,
        request_id: Optional[str] = None,
        processing_mode: ProcessingMode = ProcessingMode.BALANCED,
        use_cache: bool = True
    ) -> PipelineResult:
        """
        Main pipeline processing method

        Args:
            text: Clinical text to process
            request_id: Optional request identifier
            processing_mode: Performance/quality trade-off mode
            use_cache: Whether to use result caching

        Returns:
            Complete pipeline result with performance metrics
        """

        start_time = time.time()

        if not request_id:
            request_id = f"pipeline_{int(time.time()*1000)}"

        self.performance_stats["total_requests"] += 1

        logger.info(f"[{request_id}] Starting 3-tier pipeline processing - {len(text)} chars, mode: {processing_mode.value}")

        # Check cache if enabled
        cache_key = None
        if self.enable_caching and use_cache:
            cache_key = self._generate_cache_key(text, processing_mode)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.performance_stats["cache_hits"] += 1
                logger.info(f"[{request_id}] Cache hit - returning cached result")
                cached_result.request_id = request_id  # Update request ID
                cached_result.cache_hits = 1
                return cached_result

        # Initialize result tracking
        tier_results = []
        performance_warnings = []

        try:
            # TIER 1: Enhanced MedSpaCy Clinical Intelligence
            tier1_result = await self._process_tier1_medspacy(
                text, request_id, processing_mode
            )
            tier_results.append(tier1_result)

            if tier1_result.status == TierStatus.FAILED:
                # Critical failure - cannot continue
                return self._create_failure_result(
                    request_id, start_time, processing_mode, tier_results,
                    "Tier 1 (MedSpaCy) processing failed"
                )

            # TIER 2: Smart Regex Consolidation
            tier2_result = await self._process_tier2_consolidation(
                text, tier1_result.entities, request_id, processing_mode
            )
            tier_results.append(tier2_result)

            # Performance checkpoint
            elapsed_ms = (time.time() - start_time) * 1000
            target_ms = self.performance_targets[processing_mode]

            if elapsed_ms > target_ms * 0.7:  # 70% of budget used
                performance_warnings.append(f"Approaching time budget: {elapsed_ms:.1f}ms/{target_ms}ms")
                logger.warning(f"[{request_id}] Performance warning: {elapsed_ms:.1f}ms elapsed")

            # TIER 3: LLM Medical Safety Escalation (Conditional)
            escalation_decision = None
            tier3_result = None

            if processing_mode != ProcessingMode.SPEED_OPTIMIZED or tier2_result.confidence < 0.8:
                # Always escalate unless in speed mode with high confidence
                tier3_result = await self._process_tier3_escalation(
                    text, tier1_result.entities, tier2_result.entities,
                    request_id, processing_mode
                )
                tier_results.append(tier3_result)
                escalation_decision = tier3_result.metadata.get("escalation_decision")

            # Finalize results
            final_entities = tier2_result.entities  # Tier 2 provides final entities
            pipeline_confidence = self._calculate_pipeline_confidence(tier_results)
            quality_score = self._calculate_quality_score(text, final_entities, tier_results)

            total_time_ms = (time.time() - start_time) * 1000

            # Performance validation
            if total_time_ms > target_ms:
                performance_warnings.append(f"Exceeded time budget: {total_time_ms:.1f}ms > {target_ms}ms")

            # Create final result
            pipeline_result = PipelineResult(
                request_id=request_id,
                total_processing_time_ms=total_time_ms,
                processing_mode=processing_mode,
                tier_results=tier_results,
                final_entities=final_entities,
                escalation_decision=escalation_decision,
                pipeline_confidence=pipeline_confidence,
                performance_warnings=performance_warnings,
                quality_score=quality_score
            )

            # Cache result if appropriate
            if self.enable_caching and cache_key and total_time_ms < target_ms:
                self._cache_result(cache_key, pipeline_result)

            # Update performance statistics
            self._update_performance_stats(pipeline_result)

            logger.info(f"[{request_id}] Pipeline completed: {total_time_ms:.1f}ms, confidence: {pipeline_confidence:.2f}")
            return pipeline_result

        except Exception as e:
            logger.error(f"[{request_id}] Pipeline error: {e}")
            return self._create_failure_result(
                request_id, start_time, processing_mode, tier_results,
                f"Pipeline error: {str(e)}"
            )

    async def _process_tier1_medspacy(
        self,
        text: str,
        request_id: str,
        processing_mode: ProcessingMode
    ) -> TierResult:
        """Process Tier 1: Enhanced MedSpaCy Clinical Intelligence"""

        start_time = time.time()

        try:
            # Simulate MedSpaCy processing (replace with actual MedSpaCy call)
            # For now, using basic entity extraction as placeholder
            from src.nl_fhir.services.conversion import ConversionService

            conversion_service = ConversionService()
            result = await conversion_service._basic_text_analysis(text, request_id)

            entities = result.get("extracted_entities", {})
            confidence = result.get("confidence_score", 0.8)

            processing_time = (time.time() - start_time) * 1000

            logger.info(f"[{request_id}] Tier 1 completed: {processing_time:.1f}ms, {len(entities.get('medications', []))} meds")

            return TierResult(
                tier_name="Enhanced MedSpaCy",
                status=TierStatus.SUCCESS,
                processing_time_ms=processing_time,
                entities=entities,
                confidence=confidence,
                metadata={
                    "entity_counts": {k: len(v) for k, v in entities.items() if isinstance(v, list)},
                    "processing_method": "medspacy_enhanced"
                }
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"[{request_id}] Tier 1 failed: {e}")

            return TierResult(
                tier_name="Enhanced MedSpaCy",
                status=TierStatus.FAILED,
                processing_time_ms=processing_time,
                entities={},
                confidence=0.0,
                error_message=str(e)
            )

    async def _process_tier2_consolidation(
        self,
        text: str,
        tier1_entities: Dict,
        request_id: str,
        processing_mode: ProcessingMode
    ) -> TierResult:
        """Process Tier 2: Smart Regex Consolidation"""

        start_time = time.time()

        try:
            # Apply Smart Regex Consolidation
            consolidated_entities = self.consolidator.extract_with_smart_consolidation(
                text, tier1_entities
            )

            processing_time = (time.time() - start_time) * 1000

            # Calculate confidence based on entity enhancement
            tier1_count = sum(len(entities) for entities in tier1_entities.values() if isinstance(entities, list))
            tier2_count = sum(len(entities) for entities in consolidated_entities.values() if isinstance(entities, list))

            enhancement_ratio = tier2_count / max(tier1_count, 1)
            confidence = min(0.9, 0.7 + (enhancement_ratio * 0.2))

            logger.info(f"[{request_id}] Tier 2 completed: {processing_time:.1f}ms, enhanced {tier1_count} → {tier2_count} entities")

            return TierResult(
                tier_name="Smart Regex Consolidation",
                status=TierStatus.SUCCESS,
                processing_time_ms=processing_time,
                entities=consolidated_entities,
                confidence=confidence,
                metadata={
                    "tier1_entity_count": tier1_count,
                    "tier2_entity_count": tier2_count,
                    "enhancement_ratio": enhancement_ratio,
                    "consolidation_method": "smart_regex"
                }
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"[{request_id}] Tier 2 failed: {e}")

            # Fallback to Tier 1 results
            return TierResult(
                tier_name="Smart Regex Consolidation",
                status=TierStatus.PARTIAL,
                processing_time_ms=processing_time,
                entities=tier1_entities,  # Fallback to Tier 1
                confidence=0.6,
                error_message=str(e),
                metadata={"fallback_used": True}
            )

    async def _process_tier3_escalation(
        self,
        text: str,
        tier1_entities: Dict,
        tier2_entities: Dict,
        request_id: str,
        processing_mode: ProcessingMode
    ) -> TierResult:
        """Process Tier 3: LLM Medical Safety Escalation"""

        start_time = time.time()

        try:
            # Evaluate escalation need
            escalation_decision = self.escalation_engine.evaluate_escalation_need(
                text, tier1_entities, tier2_entities, request_id
            )

            processing_time = (time.time() - start_time) * 1000

            # Tier 3 doesn't modify entities, just provides safety validation
            entities = tier2_entities.copy()
            confidence = escalation_decision.confidence

            status = TierStatus.SUCCESS
            if escalation_decision.should_escalate and processing_mode == ProcessingMode.SPEED_OPTIMIZED:
                # In speed mode, flag but don't actually escalate to LLM
                status = TierStatus.PARTIAL

            logger.info(f"[{request_id}] Tier 3 completed: {processing_time:.1f}ms, escalate: {escalation_decision.should_escalate}")

            return TierResult(
                tier_name="LLM Medical Safety Escalation",
                status=status,
                processing_time_ms=processing_time,
                entities=entities,
                confidence=confidence,
                metadata={
                    "escalation_decision": escalation_decision,
                    "should_escalate": escalation_decision.should_escalate,
                    "trigger": escalation_decision.trigger.value if escalation_decision.trigger else None,
                    "safety_flags": len(escalation_decision.safety_flags)
                }
            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"[{request_id}] Tier 3 failed: {e}")

            return TierResult(
                tier_name="LLM Medical Safety Escalation",
                status=TierStatus.FAILED,
                processing_time_ms=processing_time,
                entities=tier2_entities,  # Fallback to Tier 2
                confidence=0.7,
                error_message=str(e),
                metadata={"escalation_skipped": True}
            )

    def _calculate_pipeline_confidence(self, tier_results: List[TierResult]) -> float:
        """Calculate overall pipeline confidence"""

        if not tier_results:
            return 0.0

        # Weight confidence by tier importance
        weights = [0.4, 0.4, 0.2]  # Tier 1, 2, 3 weights
        weighted_confidence = 0.0
        total_weight = 0.0

        for i, tier_result in enumerate(tier_results):
            if i < len(weights) and tier_result.status != TierStatus.FAILED:
                weight = weights[i]
                weighted_confidence += tier_result.confidence * weight
                total_weight += weight

        return weighted_confidence / max(total_weight, 0.1)

    def _calculate_quality_score(
        self,
        text: str,
        entities: Dict,
        tier_results: List[TierResult]
    ) -> float:
        """Calculate overall quality score for the extraction"""

        quality = 0.0

        # Entity completeness (40% of score)
        total_entities = sum(len(entity_list) for entity_list in entities.values() if isinstance(entity_list, list))
        expected_entities = len(text.split()) / 20  # Rough heuristic
        completeness = min(total_entities / max(expected_entities, 1), 1.0)
        quality += completeness * 0.4

        # Processing success (30% of score)
        successful_tiers = sum(1 for tier in tier_results if tier.status == TierStatus.SUCCESS)
        success_rate = successful_tiers / max(len(tier_results), 1)
        quality += success_rate * 0.3

        # Confidence score (30% of score)
        avg_confidence = sum(tier.confidence for tier in tier_results) / max(len(tier_results), 1)
        quality += avg_confidence * 0.3

        return min(quality, 1.0)

    def _generate_cache_key(self, text: str, processing_mode: ProcessingMode) -> str:
        """Generate cache key for text and processing mode"""

        content = f"{text}|{processing_mode.value}".encode('utf-8')
        return hashlib.md5(content).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[PipelineResult]:
        """Get cached result if available and not expired"""

        if cache_key not in self.result_cache:
            return None

        cached_entry = self.result_cache[cache_key]
        cache_time = cached_entry.get("timestamp")

        if cache_time and datetime.now() - cache_time < self.cache_ttl:
            return cached_entry.get("result")
        else:
            # Remove expired entry
            del self.result_cache[cache_key]
            return None

    def _cache_result(self, cache_key: str, result: PipelineResult) -> None:
        """Cache pipeline result"""

        # Simple cache size management
        if len(self.result_cache) > 100:
            # Remove oldest entries
            oldest_key = min(self.result_cache.keys(),
                           key=lambda k: self.result_cache[k]["timestamp"])
            del self.result_cache[oldest_key]

        self.result_cache[cache_key] = {
            "timestamp": datetime.now(),
            "result": result
        }

    def _create_failure_result(
        self,
        request_id: str,
        start_time: float,
        processing_mode: ProcessingMode,
        tier_results: List[TierResult],
        error_message: str
    ) -> PipelineResult:
        """Create failure result"""

        total_time_ms = (time.time() - start_time) * 1000

        return PipelineResult(
            request_id=request_id,
            total_processing_time_ms=total_time_ms,
            processing_mode=processing_mode,
            tier_results=tier_results,
            final_entities={},
            escalation_decision=None,
            pipeline_confidence=0.0,
            performance_warnings=[error_message],
            quality_score=0.0
        )

    def _update_performance_stats(self, result: PipelineResult) -> None:
        """Update running performance statistics"""

        total_requests = self.performance_stats["total_requests"]

        # Update average processing time
        current_avg = self.performance_stats["avg_processing_time_ms"]
        new_avg = ((current_avg * (total_requests - 1)) + result.total_processing_time_ms) / total_requests
        self.performance_stats["avg_processing_time_ms"] = new_avg

        # Update tier performance
        for tier_result in result.tier_results:
            tier_key = f"tier{len([t for t in result.tier_results if t == tier_result or result.tier_results.index(t) < result.tier_results.index(tier_result)]+[tier_result])}_avg_ms"
            if tier_key in self.performance_stats["tier_performance"]:
                current_tier_avg = self.performance_stats["tier_performance"][tier_key]
                new_tier_avg = ((current_tier_avg * (total_requests - 1)) + tier_result.processing_time_ms) / total_requests
                self.performance_stats["tier_performance"][tier_key] = new_tier_avg

        # Update escalation rate
        escalations = sum(1 for r in [result] if r.escalation_decision and r.escalation_decision.should_escalate)
        self.performance_stats["escalation_rate"] = (escalations / total_requests) * 100

        # Track quality scores
        self.performance_stats["quality_scores"].append(result.quality_score)
        if len(self.performance_stats["quality_scores"]) > 100:
            self.performance_stats["quality_scores"] = self.performance_stats["quality_scores"][-100:]

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""

        quality_scores = self.performance_stats["quality_scores"]
        avg_quality = sum(quality_scores) / max(len(quality_scores), 1)

        return {
            "pipeline_overview": {
                "architecture": "3-Tier Optimized",
                "tiers": [
                    "Enhanced MedSpaCy Clinical Intelligence",
                    "Smart Regex Consolidation",
                    "LLM Medical Safety Escalation"
                ],
                "optimization_features": [
                    "Result caching",
                    "Performance monitoring",
                    "Graceful degradation",
                    "Processing mode adaptation"
                ]
            },
            "performance_metrics": {
                "total_requests": self.performance_stats["total_requests"],
                "cache_hit_rate": (self.performance_stats["cache_hits"] / max(self.performance_stats["total_requests"], 1)) * 100,
                "avg_processing_time_ms": self.performance_stats["avg_processing_time_ms"],
                "escalation_rate_percent": self.performance_stats["escalation_rate"],
                "avg_quality_score": avg_quality,
                "tier_performance": self.performance_stats["tier_performance"]
            },
            "performance_targets": {
                "speed_optimized": f"{self.performance_targets[ProcessingMode.SPEED_OPTIMIZED]}ms",
                "balanced": f"{self.performance_targets[ProcessingMode.BALANCED]}ms",
                "quality_optimized": f"{self.performance_targets[ProcessingMode.QUALITY_OPTIMIZED]}ms"
            }
        }

async def main():
    """Test the Optimized Pipeline Coordinator"""

    print("⚡ OPTIMIZED PIPELINE COORDINATOR - Testing")
    print("=" * 55)

    coordinator = OptimizedPipelineCoordinator()

    # Test cases with different complexity levels
    test_cases = [
        {
            "name": "Simple Medication Order",
            "text": "Acetaminophen 650mg for headache",
            "mode": ProcessingMode.SPEED_OPTIMIZED
        },
        {
            "name": "High-Risk Medication",
            "text": "Start warfarin 5mg daily for atrial fibrillation, monitor INR",
            "mode": ProcessingMode.BALANCED
        },
        {
            "name": "Complex Multi-Drug Order",
            "text": "Continue warfarin 2mg daily, start aspirin 81mg daily for cardioprotection, lisinopril 10mg for hypertension",
            "mode": ProcessingMode.QUALITY_OPTIMIZED
        },
        {
            "name": "Critical Emergency",
            "text": "Patient with acute myocardial infarction - give aspirin 325mg STAT, start heparin protocol",
            "mode": ProcessingMode.BALANCED
        }
    ]

    print(f"Testing {len(test_cases)} pipeline scenarios...\n")

    for i, case in enumerate(test_cases, 1):
        print(f"🧪 Test Case {i}: {case['name']}")
        print(f"   Text: {case['text']}")
        print(f"   Mode: {case['mode'].value}")

        result = await coordinator.process_clinical_text(
            case["text"],
            f"test_{i}",
            case["mode"]
        )

        print(f"   ⏱️  Total Time: {result.total_processing_time_ms:.1f}ms")
        print(f"   🎯 Confidence: {result.pipeline_confidence:.2f}")
        print(f"   🏆 Quality: {result.quality_score:.2f}")
        print(f"   🔧 Tiers: {len(result.tier_results)} processed")

        # Show tier breakdown
        for tier in result.tier_results:
            status_emoji = "✅" if tier.status == TierStatus.SUCCESS else "⚠️" if tier.status == TierStatus.PARTIAL else "❌"
            print(f"      {status_emoji} {tier.tier_name}: {tier.processing_time_ms:.1f}ms")

        # Show escalation if applicable
        if result.escalation_decision:
            escalate_emoji = "🚨" if result.escalation_decision.should_escalate else "✅"
            print(f"   {escalate_emoji} Escalation: {'YES' if result.escalation_decision.should_escalate else 'NO'}")

        # Show performance warnings
        if result.performance_warnings:
            print(f"   ⚠️  Warnings: {len(result.performance_warnings)}")

        print()

    # Test caching performance
    print("🔄 Testing Cache Performance...")

    # Process same request twice
    cache_test_text = "Amoxicillin 500mg TID for pneumonia"

    start = time.time()
    result1 = await coordinator.process_clinical_text(cache_test_text, "cache_test_1")
    first_time = (time.time() - start) * 1000

    start = time.time()
    result2 = await coordinator.process_clinical_text(cache_test_text, "cache_test_2")
    second_time = (time.time() - start) * 1000

    print(f"   First request: {first_time:.1f}ms")
    print(f"   Second request: {second_time:.1f}ms")
    print(f"   Cache hits: {result2.cache_hits}")
    print(f"   Speed improvement: {((first_time - second_time) / first_time * 100):.1f}%")
    print()

    # Display comprehensive performance report
    report = coordinator.get_performance_report()
    print("📊 Performance Report:")
    print(f"   Total Requests: {report['performance_metrics']['total_requests']}")
    print(f"   Avg Processing Time: {report['performance_metrics']['avg_processing_time_ms']:.1f}ms")
    print(f"   Cache Hit Rate: {report['performance_metrics']['cache_hit_rate']:.1f}%")
    print(f"   Escalation Rate: {report['performance_metrics']['escalation_rate_percent']:.1f}%")
    print(f"   Avg Quality Score: {report['performance_metrics']['avg_quality_score']:.2f}")
    print()
    print("🎯 Architecture Summary:")
    print(f"   Design: {report['pipeline_overview']['architecture']}")
    print(f"   Tiers: {len(report['pipeline_overview']['tiers'])}")
    for tier in report['pipeline_overview']['tiers']:
        print(f"      • {tier}")

if __name__ == "__main__":
    asyncio.run(main())