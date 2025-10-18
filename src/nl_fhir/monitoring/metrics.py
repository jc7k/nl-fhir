"""
Prometheus Metrics for NL-FHIR Application

Provides production-ready metrics for monitoring:
- Request counts and latencies
- FHIR bundle creation and validation metrics
- System resource usage
- Business metrics (conversion success rates)

Metrics are created with safe re-registration handling for test compatibility.
"""

import time
from typing import Optional

import psutil
from prometheus_client import REGISTRY, Counter, Gauge, Histogram, Info

# Module-level registry to track created metrics and prevent duplicates
_metrics_registry = {}


def _get_or_create_metric(metric_class, name, documentation, **kwargs):
    """
    Safely get or create a Prometheus metric.
    Uses module-level registry to track created metrics and prevent duplicates.
    """
    global _metrics_registry

    # Check if metric already exists in our registry
    if name in _metrics_registry:
        return _metrics_registry[name]

    # Try to create the metric
    try:
        metric = metric_class(name, documentation, **kwargs)
        _metrics_registry[name] = metric
        return metric
    except ValueError:
        # Metric exists in Prometheus registry but not in our dict
        # This happens when module is reloaded during testing
        # Find and return the existing metric from REGISTRY
        for collector in list(REGISTRY._collector_to_names.keys()):
            collector_names = REGISTRY._collector_to_names.get(collector, set())
            # Check if this collector matches our metric name
            # Counter metrics have "_total" suffix added automatically
            if name in collector_names or f"{name}_total" in collector_names:
                _metrics_registry[name] = collector
                return collector
        # If we still can't find it, raise the original error
        raise


# Application Info
app_info = _get_or_create_metric(Info, "nl_fhir_app", "NL-FHIR Application Information")
if "nl_fhir_app" not in _metrics_registry or _metrics_registry["nl_fhir_app"] == app_info:
    try:
        app_info.info(
            {
                "version": "1.0.0",
                "name": "nl-fhir",
                "description": "Natural Language to FHIR R4 Bundle Converter",
            }
        )
    except (ValueError, AttributeError):
        # Info already set or in unexpected state, ignore
        pass

# HTTP Request Metrics
http_requests_total = _get_or_create_metric(
    Counter,
    "nl_fhir_http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "endpoint", "status"],
)

http_request_duration_seconds = _get_or_create_metric(
    Histogram,
    "nl_fhir_http_request_duration_seconds",
    "HTTP request latency",
    labelnames=["method", "endpoint"],
)

# FHIR Conversion Metrics
fhir_conversions_total = _get_or_create_metric(
    Counter,
    "nl_fhir_conversions_total",
    "Total FHIR bundle conversions",
    labelnames=["status"],  # success, failed
)

fhir_conversion_duration_seconds = _get_or_create_metric(
    Histogram,
    "nl_fhir_conversion_duration_seconds",
    "FHIR bundle conversion duration",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

fhir_resources_created_total = _get_or_create_metric(
    Counter,
    "nl_fhir_resources_created_total",
    "Total FHIR resources created",
    labelnames=["resource_type"],
)

# FHIR Validation Metrics
fhir_validations_total = _get_or_create_metric(
    Counter,
    "nl_fhir_validations_total",
    "Total FHIR bundle validations",
    labelnames=["status", "validator"],  # success/failed, local/hapi
)

fhir_validation_duration_seconds = _get_or_create_metric(
    Histogram,
    "nl_fhir_validation_duration_seconds",
    "FHIR bundle validation duration",
    labelnames=["validator"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0),
)

# NLP Processing Metrics
nlp_extractions_total = _get_or_create_metric(
    Counter,
    "nl_fhir_nlp_extractions_total",
    "Total NLP entity extractions",
    labelnames=["entity_type"],  # medication, condition, procedure, etc.
)

nlp_processing_duration_seconds = _get_or_create_metric(
    Histogram,
    "nl_fhir_nlp_processing_duration_seconds",
    "NLP processing duration",
    buckets=(0.1, 0.5, 1.0, 2.0),
)

# System Resource Metrics
system_cpu_usage_percent = _get_or_create_metric(
    Gauge, "nl_fhir_system_cpu_usage_percent", "System CPU usage percentage"
)

system_memory_usage_bytes = _get_or_create_metric(
    Gauge, "nl_fhir_system_memory_usage_bytes", "System memory usage in bytes"
)

system_memory_available_bytes = _get_or_create_metric(
    Gauge, "nl_fhir_system_memory_available_bytes", "System memory available in bytes"
)

# Application Health Metrics
app_healthy = _get_or_create_metric(
    Gauge, "nl_fhir_app_healthy", "Application health status (1=healthy, 0=unhealthy)"
)

hapi_server_available = _get_or_create_metric(
    Gauge,
    "nl_fhir_hapi_server_available",
    "HAPI FHIR server availability (1=available, 0=unavailable)",
)

# Cache Metrics
cache_hits_total = _get_or_create_metric(
    Counter, "nl_fhir_cache_hits_total", "Total cache hits", labelnames=["cache_type"]
)

cache_misses_total = _get_or_create_metric(
    Counter, "nl_fhir_cache_misses_total", "Total cache misses", labelnames=["cache_type"]
)

# Error Metrics
errors_total = _get_or_create_metric(
    Counter, "nl_fhir_errors_total", "Total errors", labelnames=["error_type", "severity"]
)


class MetricsCollector:
    """Helper class for collecting application metrics"""

    @staticmethod
    def update_system_metrics():
        """Update system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            system_cpu_usage_percent.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            system_memory_usage_bytes.set(memory.used)
            system_memory_available_bytes.set(memory.available)
        except Exception:
            errors_total.labels(error_type="metrics_collection", severity="low").inc()

    @staticmethod
    def record_http_request(method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

    @staticmethod
    def record_conversion(success: bool, duration: float, resource_types: list | None = None):
        """Record FHIR conversion metrics"""
        status = "success" if success else "failed"
        fhir_conversions_total.labels(status=status).inc()
        fhir_conversion_duration_seconds.observe(duration)

        if resource_types:
            for resource_type in resource_types:
                fhir_resources_created_total.labels(resource_type=resource_type).inc()

    @staticmethod
    def record_validation(success: bool, duration: float, validator: str = "local"):
        """Record FHIR validation metrics"""
        status = "success" if success else "failed"
        fhir_validations_total.labels(status=status, validator=validator).inc()
        fhir_validation_duration_seconds.labels(validator=validator).observe(duration)

    @staticmethod
    def record_nlp_extraction(entity_type: str, duration: float | None = None):
        """Record NLP extraction metrics"""
        nlp_extractions_total.labels(entity_type=entity_type).inc()
        if duration is not None:
            nlp_processing_duration_seconds.observe(duration)

    @staticmethod
    def record_cache_access(hit: bool, cache_type: str = "default"):
        """Record cache access metrics"""
        if hit:
            cache_hits_total.labels(cache_type=cache_type).inc()
        else:
            cache_misses_total.labels(cache_type=cache_type).inc()

    @staticmethod
    def record_error(error_type: str, severity: str = "medium"):
        """Record error metrics"""
        errors_total.labels(error_type=error_type, severity=severity).inc()

    @staticmethod
    def set_health_status(healthy: bool):
        """Set application health status"""
        app_healthy.set(1 if healthy else 0)

    @staticmethod
    def set_hapi_status(available: bool):
        """Set HAPI FHIR server availability status"""
        hapi_server_available.set(1 if available else 0)


# Context manager for timing operations
class metrics_timer:
    """Context manager for timing operations and recording metrics"""

    def __init__(self, metric_histogram, **labels):
        self.histogram = metric_histogram
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if self.labels:
            self.histogram.labels(**self.labels).observe(duration)
        else:
            self.histogram.observe(duration)
        return False
