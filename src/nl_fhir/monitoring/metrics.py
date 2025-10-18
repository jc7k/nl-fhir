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

import psutil
from prometheus_client import REGISTRY, Counter, Gauge, Histogram, Info


def _get_or_create_info(name: str, documentation: str, **kwargs):
    """Safely get or create an Info metric"""
    try:
        return Info(name, documentation)
    except ValueError:
        # Metric already exists, retrieve it from registry
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, "_name") and collector._name == name:
                return collector
        raise


def _get_or_create_counter(name: str, documentation: str, labelnames: list = None):
    """Safely get or create a Counter metric"""
    try:
        return Counter(name, documentation, labelnames or [])
    except ValueError:
        # Metric already exists, retrieve it from registry
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, "_name") and collector._name == name:
                return collector
        raise


def _get_or_create_histogram(name: str, documentation: str, labelnames: list = None, buckets=None):
    """Safely get or create a Histogram metric"""
    try:
        if buckets:
            return Histogram(name, documentation, labelnames or [], buckets=buckets)
        return Histogram(name, documentation, labelnames or [])
    except ValueError:
        # Metric already exists, retrieve it from registry
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, "_name") and collector._name == name:
                return collector
        raise


def _get_or_create_gauge(name: str, documentation: str, labelnames: list = None):
    """Safely get or create a Gauge metric"""
    try:
        return Gauge(name, documentation, labelnames or [])
    except ValueError:
        # Metric already exists, retrieve it from registry
        for collector in list(REGISTRY._collector_to_names.keys()):
            if hasattr(collector, "_name") and collector._name == name:
                return collector
        raise


# Application Info
app_info = _get_or_create_info("nl_fhir_app", "NL-FHIR Application Information")
try:
    app_info.info(
        {
            "version": "1.0.0",
            "name": "nl-fhir",
            "description": "Natural Language to FHIR R4 Bundle Converter",
        }
    )
except ValueError:
    # Info already set, ignore
    pass

# HTTP Request Metrics
http_requests_total = _get_or_create_counter(
    "nl_fhir_http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = _get_or_create_histogram(
    "nl_fhir_http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"]
)

# FHIR Conversion Metrics
fhir_conversions_total = _get_or_create_counter(
    "nl_fhir_conversions_total",
    "Total FHIR bundle conversions",
    ["status"],  # success, failed
)

fhir_conversion_duration_seconds = _get_or_create_histogram(
    "nl_fhir_conversion_duration_seconds",
    "FHIR bundle conversion duration",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

fhir_resources_created_total = _get_or_create_counter(
    "nl_fhir_resources_created_total", "Total FHIR resources created", ["resource_type"]
)

# FHIR Validation Metrics
fhir_validations_total = _get_or_create_counter(
    "nl_fhir_validations_total",
    "Total FHIR bundle validations",
    ["status", "validator"],  # success/failed, local/hapi
)

fhir_validation_duration_seconds = _get_or_create_histogram(
    "nl_fhir_validation_duration_seconds",
    "FHIR bundle validation duration",
    ["validator"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0),
)

# NLP Processing Metrics
nlp_extractions_total = _get_or_create_counter(
    "nl_fhir_nlp_extractions_total",
    "Total NLP entity extractions",
    ["entity_type"],  # medication, condition, procedure, etc.
)

nlp_processing_duration_seconds = _get_or_create_histogram(
    "nl_fhir_nlp_processing_duration_seconds",
    "NLP processing duration",
    buckets=(0.1, 0.5, 1.0, 2.0),
)

# System Resource Metrics
system_cpu_usage_percent = _get_or_create_gauge(
    "nl_fhir_system_cpu_usage_percent", "System CPU usage percentage"
)

system_memory_usage_bytes = _get_or_create_gauge(
    "nl_fhir_system_memory_usage_bytes", "System memory usage in bytes"
)

system_memory_available_bytes = _get_or_create_gauge(
    "nl_fhir_system_memory_available_bytes", "System memory available in bytes"
)

# Application Health Metrics
app_healthy = _get_or_create_gauge(
    "nl_fhir_app_healthy", "Application health status (1=healthy, 0=unhealthy)"
)

hapi_server_available = _get_or_create_gauge(
    "nl_fhir_hapi_server_available", "HAPI FHIR server availability (1=available, 0=unavailable)"
)

# Cache Metrics
cache_hits_total = _get_or_create_counter(
    "nl_fhir_cache_hits_total", "Total cache hits", ["cache_type"]
)

cache_misses_total = _get_or_create_counter(
    "nl_fhir_cache_misses_total", "Total cache misses", ["cache_type"]
)

# Error Metrics
errors_total = _get_or_create_counter(
    "nl_fhir_errors_total", "Total errors", ["error_type", "severity"]
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
