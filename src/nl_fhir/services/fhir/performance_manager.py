"""
FHIR Performance Manager for Production Optimization
Manages caching, connection pooling, and performance monitoring
HIPAA Compliant: Performance optimization without PHI exposure
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import deque, defaultdict
import hashlib
import json
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for FHIR operations"""
    operation_type: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    resource_count: int
    cache_hit: bool
    memory_usage_mb: float
    success: bool
    error_message: Optional[str] = None


class FHIRPerformanceManager:
    """Manages FHIR pipeline performance and optimization"""
    
    def __init__(self, cache_size: int = 1000, max_metrics_history: int = 10000):
        self.cache_size = cache_size
        self.max_metrics_history = max_metrics_history
        
        # Performance tracking
        self.metrics_history = deque(maxlen=max_metrics_history)
        self.operation_stats = defaultdict(list)
        self.performance_targets = {
            "validation_time_ms": 2000,
            "execution_time_ms": 2000,
            "total_pipeline_ms": 2000,
            "cache_hit_rate": 0.8,
            "success_rate": 0.95
        }
        
        # Caching system
        self.validation_cache = {}
        self.resource_cache = {}
        self.bundle_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
        # Connection pooling
        self.connection_pools = {}
        self.connection_stats = defaultdict(int)
        
        # Performance optimization settings
        self.optimization_settings = {
            "enable_validation_cache": True,
            "enable_resource_cache": True,
            "enable_bundle_cache": True,
            "cache_ttl_seconds": 3600,  # 1 hour
            "max_concurrent_requests": 10,
            "request_timeout_seconds": 30,
            "retry_attempts": 3,
            "retry_backoff_factor": 2.0
        }
        
        # Thread safety
        self._cache_lock = threading.RLock()
        self._metrics_lock = threading.RLock()
        
    def start_performance_tracking(self, operation_type: str, resource_count: int = 0) -> str:
        """Start tracking performance for an operation"""
        tracking_id = f"{operation_type}-{int(time.time() * 1000000)}"
        
        with self._metrics_lock:
            # Store start time and context
            self.operation_stats[tracking_id] = {
                "operation_type": operation_type,
                "start_time": datetime.now(timezone.utc),
                "resource_count": resource_count,
                "memory_start": self._get_memory_usage()
            }
        
        return tracking_id
    
    def end_performance_tracking(
        self, 
        tracking_id: str, 
        success: bool = True, 
        cache_hit: bool = False,
        error_message: Optional[str] = None
    ) -> PerformanceMetrics:
        """End tracking and record metrics"""
        
        end_time = datetime.now(timezone.utc)
        
        with self._metrics_lock:
            if tracking_id not in self.operation_stats:
                logger.warning(f"Unknown tracking ID: {tracking_id}")
                return None
            
            start_data = self.operation_stats[tracking_id]
            duration_ms = (end_time - start_data["start_time"]).total_seconds() * 1000
            
            metrics = PerformanceMetrics(
                operation_type=start_data["operation_type"],
                start_time=start_data["start_time"],
                end_time=end_time,
                duration_ms=duration_ms,
                resource_count=start_data["resource_count"],
                cache_hit=cache_hit,
                memory_usage_mb=self._get_memory_usage() - start_data["memory_start"],
                success=success,
                error_message=error_message
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Clean up tracking data
            del self.operation_stats[tracking_id]
            
            # Log performance issues
            if duration_ms > self.performance_targets.get(f"{metrics.operation_type}_time_ms", 2000):
                logger.warning(f"Performance target exceeded: {metrics.operation_type} took {duration_ms:.1f}ms")
            
            return metrics
    
    def cache_validation_result(self, bundle_hash: str, validation_result: Dict[str, Any]) -> None:
        """Cache validation result for reuse"""
        if not self.optimization_settings["enable_validation_cache"]:
            return
        
        with self._cache_lock:
            # Implement LRU eviction if cache is full
            if len(self.validation_cache) >= self.cache_size:
                self._evict_oldest_cache_entry("validation")
            
            self.validation_cache[bundle_hash] = {
                "result": validation_result,
                "timestamp": datetime.now(timezone.utc),
                "access_count": 0
            }
    
    def get_cached_validation_result(self, bundle_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached validation result"""
        if not self.optimization_settings["enable_validation_cache"]:
            return None
        
        with self._cache_lock:
            if bundle_hash in self.validation_cache:
                cache_entry = self.validation_cache[bundle_hash]
                
                # Check TTL
                age = (datetime.now(timezone.utc) - cache_entry["timestamp"]).total_seconds()
                if age > self.optimization_settings["cache_ttl_seconds"]:
                    del self.validation_cache[bundle_hash]
                    self.cache_stats["evictions"] += 1
                    return None
                
                # Update access statistics
                cache_entry["access_count"] += 1
                self.cache_stats["hits"] += 1
                
                return cache_entry["result"]
            
            self.cache_stats["misses"] += 1
            return None
    
    def cache_fhir_resource(self, resource_key: str, resource_data: Dict[str, Any]) -> None:
        """Cache FHIR resource for reuse"""
        if not self.optimization_settings["enable_resource_cache"]:
            return
        
        with self._cache_lock:
            if len(self.resource_cache) >= self.cache_size:
                self._evict_oldest_cache_entry("resource")
            
            self.resource_cache[resource_key] = {
                "resource": resource_data,
                "timestamp": datetime.now(timezone.utc),
                "access_count": 0
            }
    
    def get_cached_fhir_resource(self, resource_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached FHIR resource"""
        if not self.optimization_settings["enable_resource_cache"]:
            return None
        
        with self._cache_lock:
            if resource_key in self.resource_cache:
                cache_entry = self.resource_cache[resource_key]
                
                # Check TTL
                age = (datetime.now(timezone.utc) - cache_entry["timestamp"]).total_seconds()
                if age > self.optimization_settings["cache_ttl_seconds"]:
                    del self.resource_cache[resource_key]
                    return None
                
                cache_entry["access_count"] += 1
                return cache_entry["resource"]
            
            return None
    
    def generate_bundle_hash(self, bundle: Dict[str, Any]) -> str:
        """Generate hash for bundle caching (PHI-safe)"""
        try:
            # Create a PHI-safe representation for hashing
            safe_bundle = {
                "resourceType": bundle.get("resourceType"),
                "type": bundle.get("type"),
                "entry_count": len(bundle.get("entry", [])),
                "resource_types": []
            }
            
            # Add resource types and structure without PHI
            for entry in bundle.get("entry", []):
                if "resource" in entry:
                    resource = entry["resource"]
                    safe_bundle["resource_types"].append({
                        "resourceType": resource.get("resourceType"),
                        "field_count": len(resource.keys()),
                        "has_identifier": "identifier" in resource,
                        "has_reference": any("reference" in str(v) for v in resource.values() if isinstance(v, (str, dict)))
                    })
            
            # Generate hash
            bundle_json = json.dumps(safe_bundle, sort_keys=True)
            return hashlib.sha256(bundle_json.encode()).hexdigest()[:16]
            
        except Exception as e:
            logger.error(f"Failed to generate bundle hash: {e}")
            return f"hash-error-{int(time.time())}"
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        try:
            with self._metrics_lock:
                if not self.metrics_history:
                    return {"message": "No performance data available"}
                
                # Calculate overall statistics
                total_operations = len(self.metrics_history)
                successful_operations = sum(1 for m in self.metrics_history if m.success)
                success_rate = successful_operations / total_operations
                
                # Calculate average durations by operation type
                operation_averages = {}
                for metrics in self.metrics_history:
                    op_type = metrics.operation_type
                    if op_type not in operation_averages:
                        operation_averages[op_type] = []
                    operation_averages[op_type].append(metrics.duration_ms)
                
                for op_type in operation_averages:
                    durations = operation_averages[op_type]
                    operation_averages[op_type] = {
                        "average_ms": sum(durations) / len(durations),
                        "min_ms": min(durations),
                        "max_ms": max(durations),
                        "count": len(durations),
                        "target_met": sum(durations) / len(durations) < self.performance_targets.get(f"{op_type}_time_ms", 2000)
                    }
                
                # Cache statistics
                total_cache_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
                cache_hit_rate = self.cache_stats["hits"] / max(total_cache_requests, 1)
                
                # Recent performance (last 100 operations)
                recent_metrics = list(self.metrics_history)[-100:]
                recent_durations = [m.duration_ms for m in recent_metrics]
                recent_avg = sum(recent_durations) / len(recent_durations) if recent_durations else 0
                
                return {
                    "overall_statistics": {
                        "total_operations": total_operations,
                        "success_rate": success_rate,
                        "success_target_met": success_rate >= self.performance_targets["success_rate"],
                        "average_duration_ms": sum(m.duration_ms for m in self.metrics_history) / total_operations,
                        "recent_average_ms": recent_avg,
                        "performance_target_met": recent_avg < self.performance_targets["total_pipeline_ms"]
                    },
                    "operation_breakdown": operation_averages,
                    "cache_performance": {
                        "hit_rate": cache_hit_rate,
                        "hits": self.cache_stats["hits"],
                        "misses": self.cache_stats["misses"],
                        "evictions": self.cache_stats["evictions"],
                        "target_met": cache_hit_rate >= self.performance_targets["cache_hit_rate"],
                        "validation_cache_size": len(self.validation_cache),
                        "resource_cache_size": len(self.resource_cache),
                        "bundle_cache_size": len(self.bundle_cache)
                    },
                    "performance_targets": self.performance_targets,
                    "optimization_recommendations": self._generate_optimization_recommendations()
                }
        
        except Exception as e:
            logger.error(f"Failed to generate performance summary: {e}")
            return {"error": str(e)}
    
    def optimize_performance_settings(self) -> Dict[str, Any]:
        """Automatically optimize performance settings based on metrics"""
        try:
            recommendations = []
            
            # Analyze cache performance
            total_cache_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
            if total_cache_requests > 0:
                hit_rate = self.cache_stats["hits"] / total_cache_requests
                
                if hit_rate < 0.5:
                    # Increase cache TTL
                    old_ttl = self.optimization_settings["cache_ttl_seconds"]
                    self.optimization_settings["cache_ttl_seconds"] = min(old_ttl * 1.5, 7200)
                    recommendations.append(f"Increased cache TTL from {old_ttl}s to {self.optimization_settings['cache_ttl_seconds']}s")
                
                if hit_rate > 0.9 and self.cache_stats["evictions"] > 100:
                    # Increase cache size
                    old_size = self.cache_size
                    self.cache_size = min(old_size * 1.2, 5000)
                    recommendations.append(f"Increased cache size from {old_size} to {self.cache_size}")
            
            # Analyze operation performance
            with self._metrics_lock:
                if len(self.metrics_history) > 50:
                    recent_metrics = list(self.metrics_history)[-50:]
                    avg_duration = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)
                    
                    if avg_duration > self.performance_targets["total_pipeline_ms"]:
                        # Reduce timeout for faster failure detection
                        old_timeout = self.optimization_settings["request_timeout_seconds"]
                        self.optimization_settings["request_timeout_seconds"] = max(old_timeout * 0.8, 10)
                        recommendations.append(f"Reduced request timeout from {old_timeout}s to {self.optimization_settings['request_timeout_seconds']}s")
                        
                        # Increase concurrent requests if performance is poor
                        old_concurrent = self.optimization_settings["max_concurrent_requests"]
                        self.optimization_settings["max_concurrent_requests"] = min(old_concurrent + 2, 20)
                        recommendations.append(f"Increased max concurrent requests from {old_concurrent} to {self.optimization_settings['max_concurrent_requests']}")
            
            return {
                "optimizations_applied": len(recommendations),
                "recommendations": recommendations,
                "current_settings": self.optimization_settings.copy()
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize performance settings: {e}")
            return {"error": str(e)}
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics"""
        try:
            # Get metrics from last 5 minutes
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            
            with self._metrics_lock:
                recent_metrics = [
                    m for m in self.metrics_history 
                    if m.start_time >= cutoff_time
                ]
            
            if not recent_metrics:
                return {"message": "No recent metrics available"}
            
            # Calculate real-time statistics
            total_recent = len(recent_metrics)
            successful_recent = sum(1 for m in recent_metrics if m.success)
            avg_duration = sum(m.duration_ms for m in recent_metrics) / total_recent
            
            # Group by operation type
            operation_breakdown = defaultdict(list)
            for m in recent_metrics:
                operation_breakdown[m.operation_type].append(m.duration_ms)
            
            operation_stats = {}
            for op_type, durations in operation_breakdown.items():
                operation_stats[op_type] = {
                    "count": len(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "max_ms": max(durations),
                    "min_ms": min(durations)
                }
            
            return {
                "time_window": "5 minutes",
                "total_operations": total_recent,
                "success_rate": successful_recent / total_recent,
                "average_duration_ms": avg_duration,
                "performance_target_met": avg_duration < self.performance_targets["total_pipeline_ms"],
                "operation_breakdown": operation_stats,
                "active_connections": sum(self.connection_stats.values()),
                "cache_hit_rate_recent": self._calculate_recent_cache_hit_rate(),
                "memory_usage_mb": self._get_memory_usage()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            return {"error": str(e)}
    
    def clear_caches(self) -> Dict[str, int]:
        """Clear all caches and return cleared counts"""
        with self._cache_lock:
            validation_count = len(self.validation_cache)
            resource_count = len(self.resource_cache)
            bundle_count = len(self.bundle_cache)
            
            self.validation_cache.clear()
            self.resource_cache.clear()
            self.bundle_cache.clear()
            
            # Reset cache stats
            self.cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
            
            logger.info(f"Cleared caches: {validation_count} validation, {resource_count} resource, {bundle_count} bundle")
            
            return {
                "validation_entries_cleared": validation_count,
                "resource_entries_cleared": resource_count,
                "bundle_entries_cleared": bundle_count
            }
    
    def _evict_oldest_cache_entry(self, cache_type: str) -> None:
        """Evict oldest cache entry using LRU strategy"""
        try:
            if cache_type == "validation" and self.validation_cache:
                oldest_key = min(
                    self.validation_cache.keys(),
                    key=lambda k: self.validation_cache[k]["timestamp"]
                )
                del self.validation_cache[oldest_key]
                self.cache_stats["evictions"] += 1
                
            elif cache_type == "resource" and self.resource_cache:
                oldest_key = min(
                    self.resource_cache.keys(),
                    key=lambda k: self.resource_cache[k]["timestamp"]
                )
                del self.resource_cache[oldest_key]
                self.cache_stats["evictions"] += 1
                
        except Exception as e:
            logger.error(f"Failed to evict cache entry: {e}")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback if psutil not available
            return 0.0
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0
    
    def _calculate_recent_cache_hit_rate(self) -> float:
        """Calculate cache hit rate for recent operations"""
        # This is a simplified calculation - in a real implementation,
        # you might want to track cache stats over time windows
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        if total_requests == 0:
            return 0.0
        return self.cache_stats["hits"] / total_requests
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on performance data"""
        recommendations = []
        
        try:
            # Cache recommendations
            total_cache_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
            if total_cache_requests > 0:
                hit_rate = self.cache_stats["hits"] / total_cache_requests
                
                if hit_rate < 0.6:
                    recommendations.append("Consider increasing cache TTL or cache size for better hit rates")
                
                if self.cache_stats["evictions"] > self.cache_stats["hits"] * 0.1:
                    recommendations.append("High cache eviction rate - consider increasing cache size")
            
            # Performance recommendations
            with self._metrics_lock:
                if len(self.metrics_history) > 10:
                    recent_avg = sum(m.duration_ms for m in list(self.metrics_history)[-10:]) / 10
                    
                    if recent_avg > self.performance_targets["total_pipeline_ms"]:
                        recommendations.append("Average response time exceeds target - consider optimization")
                    
                    error_rate = sum(1 for m in self.metrics_history if not m.success) / len(self.metrics_history)
                    if error_rate > 0.05:  # 5% error rate
                        recommendations.append("High error rate detected - investigate error patterns")
            
            if not recommendations:
                recommendations.append("Performance is within targets - no immediate optimizations needed")
                
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            recommendations.append("Error generating recommendations - check logs")
        
        return recommendations


# Global performance manager instance
_performance_manager = None

def get_performance_manager() -> FHIRPerformanceManager:
    """Get performance manager instance"""
    global _performance_manager
    
    if _performance_manager is None:
        _performance_manager = FHIRPerformanceManager()
    
    return _performance_manager