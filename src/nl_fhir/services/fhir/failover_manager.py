"""
HAPI FHIR Failover Manager for Story 3.3
Manages multiple HAPI FHIR endpoints with automatic failover and health monitoring
HIPAA Compliant: Secure endpoint management with no PHI exposure
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class EndpointStatus(Enum):
    """HAPI FHIR endpoint status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class HAPIEndpoint:
    """HAPI FHIR endpoint configuration"""
    name: str
    url: str
    priority: int  # Lower number = higher priority
    timeout: int = 30
    max_retries: int = 3
    health_check_interval: int = 60  # seconds
    
    # Runtime state
    status: EndpointStatus = EndpointStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    average_response_time: float = 0.0
    last_error: Optional[str] = None


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failures detected, stop requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for endpoint protection"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
    
    def can_execute(self) -> bool:
        """Check if requests can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            # Check if enough time has passed to try recovery
            if (self.last_failure_time and 
                datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)):
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful request"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class HAPIFailoverManager:
    """Manager for HAPI FHIR endpoint failover and health monitoring"""
    
    def __init__(self):
        self.endpoints: List[HAPIEndpoint] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.current_primary: Optional[str] = None
        self.health_check_task: Optional[asyncio.Task] = None
        self.initialized = False
        
        # Failover metrics
        self.failover_events = []
        self.total_failovers = 0
        
        # Default endpoints
        self._setup_default_endpoints()
    
    def _setup_default_endpoints(self):
        """Setup default HAPI FHIR endpoints"""
        
        default_endpoints = [
            {
                "name": "local_docker",
                "url": "http://localhost:8080/fhir",
                "priority": 1,
                "timeout": 10
            },
            {
                "name": "cloud_primary", 
                "url": "https://hapi.fhir.org/baseR4",
                "priority": 2,
                "timeout": 30
            },
            {
                "name": "cloud_fallback",
                "url": "https://server.fire.ly/r4", 
                "priority": 3,
                "timeout": 30
            }
        ]
        
        for endpoint_config in default_endpoints:
            self.add_endpoint(**endpoint_config)
    
    def add_endpoint(self, name: str, url: str, priority: int, timeout: int = 30, 
                    max_retries: int = 3, health_check_interval: int = 60):
        """Add HAPI FHIR endpoint to failover pool"""
        
        endpoint = HAPIEndpoint(
            name=name,
            url=url,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            health_check_interval=health_check_interval
        )
        
        self.endpoints.append(endpoint)
        self.circuit_breakers[name] = CircuitBreaker()
        
        # Sort by priority (lower number = higher priority)
        self.endpoints.sort(key=lambda x: x.priority)
        
        logger.info(f"Added HAPI endpoint: {name} ({url}) with priority {priority}")
    
    def remove_endpoint(self, name: str):
        """Remove endpoint from failover pool"""
        
        self.endpoints = [ep for ep in self.endpoints if ep.name != name]
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
        
        if self.current_primary == name:
            self.current_primary = None
        
        logger.info(f"Removed HAPI endpoint: {name}")
    
    async def initialize(self) -> bool:
        """Initialize failover manager and start health monitoring"""
        
        try:
            # Perform initial health checks
            await self._initial_health_check()
            
            # Start continuous health monitoring
            self.health_check_task = asyncio.create_task(self._health_monitoring_loop())
            
            self.initialized = True
            logger.info("HAPI Failover Manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize failover manager: {e}")
            return False
    
    async def get_healthy_endpoint(self, operation_type: str = "validation") -> Optional[HAPIEndpoint]:
        """Get the best available healthy endpoint"""
        
        if not self.initialized:
            await self.initialize()
        
        # Try current primary first if available and healthy
        if self.current_primary:
            primary_endpoint = self._get_endpoint_by_name(self.current_primary)
            if primary_endpoint and self._is_endpoint_available(primary_endpoint):
                return primary_endpoint
        
        # Find best available endpoint by priority
        for endpoint in self.endpoints:
            if self._is_endpoint_available(endpoint):
                # Update current primary if it changed
                if self.current_primary != endpoint.name:
                    self._record_failover_event(self.current_primary, endpoint.name, operation_type)
                    self.current_primary = endpoint.name
                
                return endpoint
        
        # No healthy endpoints available
        logger.error("No healthy HAPI FHIR endpoints available")
        return None
    
    async def execute_with_failover(self, operation: Callable, *args, **kwargs) -> Optional[Any]:
        """Execute operation with automatic failover on failure"""
        
        attempt_count = 0
        last_error = None
        
        while attempt_count < len(self.endpoints):
            endpoint = await self.get_healthy_endpoint(kwargs.get('operation_type', 'unknown'))
            
            if not endpoint:
                break
            
            circuit_breaker = self.circuit_breakers[endpoint.name]
            
            if not circuit_breaker.can_execute():
                # Mark endpoint as failed and try next
                endpoint.status = EndpointStatus.FAILED
                attempt_count += 1
                continue
            
            try:
                # Update endpoint URL in client if needed
                if hasattr(operation, '__self__') and hasattr(operation.__self__, 'base_url'):
                    operation.__self__.base_url = endpoint.url.rstrip('/')
                
                # Execute operation
                start_time = time.time()
                result = await operation(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Record success
                self._record_success(endpoint, execution_time)
                circuit_breaker.record_success()
                
                return result
                
            except Exception as e:
                last_error = str(e)
                
                # Record failure
                self._record_failure(endpoint, last_error)
                circuit_breaker.record_failure()
                
                logger.warning(f"Operation failed on endpoint {endpoint.name}: {e}")
                attempt_count += 1
                
                # Try next endpoint
                continue
        
        # All endpoints failed
        logger.error(f"All HAPI endpoints failed. Last error: {last_error}")
        return None
    
    async def _initial_health_check(self):
        """Perform initial health check on all endpoints"""
        
        logger.info("Performing initial HAPI endpoint health checks")
        
        health_check_tasks = []
        for endpoint in self.endpoints:
            task = asyncio.create_task(self._check_endpoint_health(endpoint))
            health_check_tasks.append(task)
        
        # Wait for all health checks to complete
        await asyncio.gather(*health_check_tasks, return_exceptions=True)
        
        # Set initial primary endpoint
        healthy_endpoints = [ep for ep in self.endpoints if ep.status == EndpointStatus.HEALTHY]
        if healthy_endpoints:
            self.current_primary = healthy_endpoints[0].name
            logger.info(f"Initial primary endpoint: {self.current_primary}")
    
    async def _health_monitoring_loop(self):
        """Continuous health monitoring background task"""
        
        while self.initialized:
            try:
                # Check all endpoints
                for endpoint in self.endpoints:
                    if (not endpoint.last_health_check or 
                        datetime.now() - endpoint.last_health_check > timedelta(seconds=endpoint.health_check_interval)):
                        
                        await self._check_endpoint_health(endpoint)
                
                # Sleep between monitoring cycles
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _check_endpoint_health(self, endpoint: HAPIEndpoint):
        """Check health of a specific endpoint"""
        
        try:
            import requests
            
            # Simple metadata endpoint check
            health_url = f"{endpoint.url.rstrip('/')}/metadata"
            
            start_time = time.time()
            response = requests.get(health_url, timeout=5)
            response_time = time.time() - start_time
            
            endpoint.last_health_check = datetime.now()
            
            if response.status_code == 200:
                # Update endpoint metrics
                endpoint.average_response_time = (
                    (endpoint.average_response_time * endpoint.total_requests + response_time) /
                    (endpoint.total_requests + 1)
                )
                endpoint.total_requests += 1
                endpoint.successful_requests += 1
                endpoint.consecutive_failures = 0
                endpoint.last_error = None
                
                # Determine status based on response time
                if response_time < 2.0:
                    endpoint.status = EndpointStatus.HEALTHY
                else:
                    endpoint.status = EndpointStatus.DEGRADED
                
                logger.debug(f"Endpoint {endpoint.name} health check: {endpoint.status.value} ({response_time:.3f}s)")
            else:
                self._mark_endpoint_unhealthy(endpoint, f"HTTP {response.status_code}")
                
        except Exception as e:
            self._mark_endpoint_unhealthy(endpoint, str(e))
    
    def _mark_endpoint_unhealthy(self, endpoint: HAPIEndpoint, error: str):
        """Mark endpoint as unhealthy"""
        
        endpoint.status = EndpointStatus.FAILED
        endpoint.consecutive_failures += 1
        endpoint.last_error = error
        endpoint.last_health_check = datetime.now()
        
        logger.warning(f"Endpoint {endpoint.name} marked unhealthy: {error}")
    
    def _is_endpoint_available(self, endpoint: HAPIEndpoint) -> bool:
        """Check if endpoint is available for requests"""
        
        if endpoint.status == EndpointStatus.FAILED:
            return False
        
        circuit_breaker = self.circuit_breakers[endpoint.name]
        return circuit_breaker.can_execute()
    
    def _get_endpoint_by_name(self, name: str) -> Optional[HAPIEndpoint]:
        """Get endpoint by name"""
        return next((ep for ep in self.endpoints if ep.name == name), None)
    
    def _record_success(self, endpoint: HAPIEndpoint, execution_time: float):
        """Record successful operation"""
        
        endpoint.total_requests += 1
        endpoint.successful_requests += 1
        endpoint.consecutive_failures = 0
        
        # Update average response time
        endpoint.average_response_time = (
            (endpoint.average_response_time * (endpoint.total_requests - 1) + execution_time) /
            endpoint.total_requests
        )
    
    def _record_failure(self, endpoint: HAPIEndpoint, error: str):
        """Record failed operation"""
        
        endpoint.total_requests += 1
        endpoint.consecutive_failures += 1
        endpoint.last_error = error
        
        # Mark as degraded or failed based on consecutive failures
        if endpoint.consecutive_failures >= 3:
            endpoint.status = EndpointStatus.FAILED
        else:
            endpoint.status = EndpointStatus.DEGRADED
    
    def _record_failover_event(self, from_endpoint: Optional[str], to_endpoint: str, operation_type: str):
        """Record failover event for monitoring"""
        
        self.total_failovers += 1
        
        failover_event = {
            "timestamp": datetime.now().isoformat(),
            "from_endpoint": from_endpoint,
            "to_endpoint": to_endpoint,
            "operation_type": operation_type,
            "failover_count": self.total_failovers
        }
        
        self.failover_events.append(failover_event)
        
        # Keep only last 100 events
        if len(self.failover_events) > 100:
            self.failover_events.pop(0)
        
        logger.info(f"[FAILOVER] {from_endpoint} → {to_endpoint} for {operation_type}")
    
    def get_endpoint_status(self) -> Dict[str, Any]:
        """Get current status of all endpoints"""
        
        endpoint_statuses = []
        
        for endpoint in self.endpoints:
            success_rate = (
                (endpoint.successful_requests / endpoint.total_requests * 100) 
                if endpoint.total_requests > 0 else 0
            )
            
            endpoint_statuses.append({
                "name": endpoint.name,
                "url": endpoint.url,
                "priority": endpoint.priority,
                "status": endpoint.status.value,
                "is_primary": endpoint.name == self.current_primary,
                "total_requests": endpoint.total_requests,
                "successful_requests": endpoint.successful_requests,
                "success_rate_percentage": round(success_rate, 2),
                "average_response_time": round(endpoint.average_response_time, 3),
                "consecutive_failures": endpoint.consecutive_failures,
                "last_health_check": endpoint.last_health_check.isoformat() if endpoint.last_health_check else None,
                "last_error": endpoint.last_error,
                "circuit_breaker_state": self.circuit_breakers[endpoint.name].state.value
            })
        
        return {
            "endpoints": endpoint_statuses,
            "total_failovers": self.total_failovers,
            "recent_failovers": self.failover_events[-10:],  # Last 10 failover events
            "primary_endpoint": self.current_primary,
            "health_monitoring_active": self.health_check_task is not None and not self.health_check_task.done()
        }
    
    def get_failover_metrics(self) -> Dict[str, Any]:
        """Get failover-specific metrics"""
        
        healthy_count = len([ep for ep in self.endpoints if ep.status == EndpointStatus.HEALTHY])
        total_count = len(self.endpoints)
        
        return {
            "total_endpoints": total_count,
            "healthy_endpoints": healthy_count,
            "degraded_endpoints": len([ep for ep in self.endpoints if ep.status == EndpointStatus.DEGRADED]),
            "failed_endpoints": len([ep for ep in self.endpoints if ep.status == EndpointStatus.FAILED]),
            "availability_percentage": round((healthy_count / total_count * 100) if total_count > 0 else 0, 2),
            "total_failover_events": self.total_failovers,
            "meets_availability_target": (healthy_count / total_count) >= 0.999 if total_count > 0 else False,
            "primary_endpoint": self.current_primary
        }
    
    async def shutdown(self):
        """Shutdown failover manager"""
        
        self.initialized = False
        
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("HAPI Failover Manager shutdown complete")


# Global failover manager instance
_failover_manager = None

async def get_failover_manager() -> HAPIFailoverManager:
    """Get initialized failover manager instance"""
    global _failover_manager
    
    if _failover_manager is None:
        _failover_manager = HAPIFailoverManager()
        await _failover_manager.initialize()
    
    return _failover_manager