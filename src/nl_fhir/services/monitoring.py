"""
Monitoring and Health Check Service
HIPAA Compliant: No PHI in monitoring data
Production Ready: Comprehensive health and metrics endpoints
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..models.response import HealthResponse, MetricsResponse

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for health checks, metrics, and system monitoring"""
    
    def __init__(self):
        self.startup_time = datetime.now()
        self.request_count = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.max_response_times = 1000  # Keep last 1000 response times
        
    def record_request(self, success: bool, response_time_ms: float):
        """Record request metrics for monitoring"""
        self.request_count += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            
        # Store response times for average calculation
        self.response_times.append(response_time_ms)
        if len(self.response_times) > self.max_response_times:
            self.response_times.pop(0)  # Remove oldest
    
    async def get_health(self) -> HealthResponse:
        """
        Comprehensive health check endpoint
        Returns system health status and component checks
        """
        start_time = time.time()
        
        # Basic health indicators
        status = "healthy"
        components = {}
        dependencies = {}
        
        try:
            # Check system resources
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=0.1)
            disk_percent = psutil.disk_usage('/').percent
            
            # Component health checks
            components["memory"] = "healthy" if memory_percent < 90 else "warning" if memory_percent < 95 else "critical"
            components["cpu"] = "healthy" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
            components["disk"] = "healthy" if disk_percent < 85 else "warning" if disk_percent < 95 else "critical"
            
            # Application health
            components["application"] = "healthy"
            components["logging"] = "healthy"
            
            # Future dependency checks (Epic 2-3)
            dependencies["nlp_pipeline"] = "not_configured"  # Will be "healthy/unhealthy" in Epic 2
            dependencies["hapi_fhir"] = "not_configured"     # Will be "healthy/unhealthy" in Epic 3
            
            # Overall status determination
            if any(status == "critical" for status in components.values()):
                status = "critical"
            elif any(status == "warning" for status in components.values()):
                status = "warning"
                
        except Exception as e:
            logger.error(f"Health check error: {type(e).__name__}")
            status = "critical"
            components["system"] = "error"
        
        response_time = (time.time() - start_time) * 1000
        
        return HealthResponse(
            status=status,
            service="nl-fhir-converter",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            response_time_ms=response_time,
            components=components,
            dependencies=dependencies
        )
    
    async def get_metrics(self) -> MetricsResponse:
        """
        Application metrics endpoint
        Returns performance and usage statistics
        """
        uptime = (datetime.now() - self.startup_time).total_seconds()
        
        # Calculate average response time
        avg_response_time = (
            sum(self.response_times) / len(self.response_times) 
            if self.response_times else 0.0
        )
        
        # Calculate current load percentage
        success_rate = (
            self.successful_requests / self.request_count 
            if self.request_count > 0 else 1.0
        )
        current_load = min(100.0, (self.request_count / max(uptime / 60, 1)) * 5)  # Rough load estimate
        
        # Memory usage
        memory_usage = None
        try:
            memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        except Exception:
            pass
        
        return MetricsResponse(
            uptime_seconds=uptime,
            total_requests=self.request_count,
            successful_requests=self.successful_requests,
            failed_requests=self.failed_requests,
            average_response_time_ms=avg_response_time,
            current_load=current_load,
            memory_usage_mb=memory_usage
        )
    
    async def get_readiness(self) -> Dict[str, Any]:
        """
        Kubernetes/Railway readiness probe endpoint
        Checks if service is ready to receive traffic
        """
        ready = True
        checks = {}
        
        try:
            # Check if service can process requests
            checks["application"] = True
            checks["memory_available"] = psutil.virtual_memory().percent < 95
            checks["disk_space"] = psutil.disk_usage('/').percent < 95
            
            # Future Epic checks
            checks["nlp_models_loaded"] = True  # Will be actual check in Epic 2
            checks["fhir_server_connection"] = True  # Will be actual check in Epic 3
            
            ready = all(checks.values())
            
        except Exception as e:
            logger.error(f"Readiness check error: {type(e).__name__}")
            ready = False
            checks["system_error"] = False
        
        return {
            "ready": ready,
            "timestamp": datetime.now().isoformat(),
            "checks": checks
        }
    
    async def get_liveness(self) -> Dict[str, Any]:
        """
        Kubernetes/Railway liveness probe endpoint  
        Checks if service is alive and should not be restarted
        """
        alive = True
        
        try:
            # Basic liveness indicators
            uptime = (datetime.now() - self.startup_time).total_seconds()
            memory_percent = psutil.virtual_memory().percent
            
            # Service is alive if it's been running and not in critical memory state
            alive = uptime > 0 and memory_percent < 98
            
        except Exception as e:
            logger.error(f"Liveness check error: {type(e).__name__}")
            alive = False
        
        return {
            "alive": alive,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.startup_time).total_seconds()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary for Epic handoff
        Used for Epic 2 performance baseline establishment
        """
        if not self.response_times:
            return {
                "status": "no_data",
                "message": "No performance data available yet"
            }
        
        response_times = sorted(self.response_times)
        count = len(response_times)
        
        return {
            "total_requests": self.request_count,
            "success_rate": self.successful_requests / self.request_count,
            "response_time_stats": {
                "average_ms": sum(response_times) / count,
                "median_ms": response_times[count // 2],
                "p95_ms": response_times[int(count * 0.95)],
                "p99_ms": response_times[int(count * 0.99)],
                "min_ms": min(response_times),
                "max_ms": max(response_times)
            },
            "performance_notes": [
                "Baseline established for Epic 1 Input Layer",
                "Ready for Epic 2 NLP processing overhead assessment",
                "Target: <2s end-to-end response time including NLP"
            ]
        }