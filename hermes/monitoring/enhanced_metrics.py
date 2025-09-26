"""
Enhanced Prometheus metrics for enterprise-grade monitoring and observability.
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager

from prometheus_client import (
    Counter, Gauge, Histogram, Summary, Info, Enum,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from prometheus_client.multiprocess import MultiProcessCollector

from ..config import settings
from ..database.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)

# Custom registry for better control
HERMES_REGISTRY = CollectorRegistry()

# === Core Application Metrics ===

# Request metrics with enhanced labels
REQUEST_COUNT = Counter(
    'hermes_http_requests_total',
    'Total HTTP requests served',
    ['method', 'endpoint', 'status_code', 'tenant_id'],
    registry=HERMES_REGISTRY
)

REQUEST_DURATION = Histogram(
    'hermes_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'tenant_id'],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=HERMES_REGISTRY
)

REQUEST_SIZE = Summary(
    'hermes_http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    registry=HERMES_REGISTRY
)

RESPONSE_SIZE = Summary(
    'hermes_http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint', 'status_code'],
    registry=HERMES_REGISTRY
)

# === Database Metrics ===

DATABASE_CONNECTIONS_ACTIVE = Gauge(
    'hermes_database_connections_active',
    'Active database connections',
    ['tenant_id'],
    registry=HERMES_REGISTRY
)

DATABASE_CONNECTIONS_IDLE = Gauge(
    'hermes_database_connections_idle',
    'Idle database connections',
    ['tenant_id'],
    registry=HERMES_REGISTRY
)

DATABASE_QUERY_DURATION = Histogram(
    'hermes_database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type', 'tenant_id', 'table'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
    registry=HERMES_REGISTRY
)

DATABASE_QUERIES_TOTAL = Counter(
    'hermes_database_queries_total',
    'Total database queries executed',
    ['query_type', 'tenant_id', 'status'],
    registry=HERMES_REGISTRY
)

DATABASE_POOL_SIZE = Gauge(
    'hermes_database_pool_size',
    'Database connection pool size',
    registry=HERMES_REGISTRY
)

DATABASE_POOL_OVERFLOW = Gauge(
    'hermes_database_pool_overflow',
    'Database connection pool overflow',
    registry=HERMES_REGISTRY
)

# === Cache Metrics ===

CACHE_OPERATIONS_TOTAL = Counter(
    'hermes_cache_operations_total',
    'Total cache operations',
    ['operation', 'cache_type', 'tenant_id', 'status'],
    registry=HERMES_REGISTRY
)

CACHE_HIT_RATIO = Gauge(
    'hermes_cache_hit_ratio',
    'Cache hit ratio by tenant',
    ['cache_type', 'tenant_id'],
    registry=HERMES_REGISTRY
)

CACHE_ITEMS_COUNT = Gauge(
    'hermes_cache_items_count',
    'Number of items in cache',
    ['cache_type', 'tenant_id'],
    registry=HERMES_REGISTRY
)

CACHE_MEMORY_USAGE_BYTES = Gauge(
    'hermes_cache_memory_usage_bytes',
    'Cache memory usage in bytes',
    ['cache_type'],
    registry=HERMES_REGISTRY
)

CACHE_OPERATION_DURATION = Histogram(
    'hermes_cache_operation_duration_seconds',
    'Cache operation duration in seconds',
    ['operation', 'cache_type'],
    buckets=(0.0001, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
    registry=HERMES_REGISTRY
)

# === Voice Pipeline Metrics ===

VOICE_SESSIONS_ACTIVE = Gauge(
    'hermes_voice_sessions_active',
    'Active voice sessions',
    ['tenant_id'],
    registry=HERMES_REGISTRY
)

VOICE_PROCESSING_DURATION = Histogram(
    'hermes_voice_processing_duration_seconds',
    'Voice processing pipeline duration',
    ['stage', 'tenant_id'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
    registry=HERMES_REGISTRY
)

VOICE_AUDIO_QUALITY = Gauge(
    'hermes_voice_audio_quality_score',
    'Audio quality score (0-1)',
    ['tenant_id'],
    registry=HERMES_REGISTRY
)

VOICE_TRANSCRIPTION_ACCURACY = Gauge(
    'hermes_voice_transcription_accuracy',
    'Transcription accuracy score (0-1)',
    ['model', 'tenant_id'],
    registry=HERMES_REGISTRY
)

VOICE_WEBSOCKET_CONNECTIONS = Gauge(
    'hermes_voice_websocket_connections',
    'Active voice WebSocket connections',
    registry=HERMES_REGISTRY
)

# === Tenant-specific Metrics ===

TENANT_API_USAGE = Counter(
    'hermes_tenant_api_usage_total',
    'API usage by tenant',
    ['tenant_id', 'endpoint', 'plan_type'],
    registry=HERMES_REGISTRY
)

TENANT_ACTIVE_USERS = Gauge(
    'hermes_tenant_active_users',
    'Active users per tenant',
    ['tenant_id'],
    registry=HERMES_REGISTRY
)

TENANT_STORAGE_USAGE_BYTES = Gauge(
    'hermes_tenant_storage_usage_bytes',
    'Storage usage by tenant in bytes',
    ['tenant_id', 'storage_type'],
    registry=HERMES_REGISTRY
)

TENANT_BILLING_EVENTS = Counter(
    'hermes_tenant_billing_events_total',
    'Billing events by tenant',
    ['tenant_id', 'event_type'],
    registry=HERMES_REGISTRY
)

# === System Resource Metrics ===

SYSTEM_CPU_USAGE = Gauge(
    'hermes_system_cpu_usage_percent',
    'System CPU usage percentage',
    registry=HERMES_REGISTRY
)

SYSTEM_MEMORY_USAGE = Gauge(
    'hermes_system_memory_usage_bytes',
    'System memory usage in bytes',
    ['type'],  # total, available, used
    registry=HERMES_REGISTRY
)

SYSTEM_DISK_USAGE = Gauge(
    'hermes_system_disk_usage_bytes',
    'System disk usage in bytes',
    ['path', 'type'],  # total, used, free
    registry=HERMES_REGISTRY
)

SYSTEM_NETWORK_IO = Counter(
    'hermes_system_network_io_bytes_total',
    'System network I/O in bytes',
    ['direction'],  # sent, received
    registry=HERMES_REGISTRY
)

# === Application Health Metrics ===

APPLICATION_INFO = Info(
    'hermes_application_info',
    'Application information',
    registry=HERMES_REGISTRY
)

APPLICATION_STATUS = Enum(
    'hermes_application_status',
    'Application status',
    states=['starting', 'healthy', 'degraded', 'unhealthy'],
    registry=HERMES_REGISTRY
)

UPTIME_SECONDS = Gauge(
    'hermes_uptime_seconds',
    'Application uptime in seconds',
    registry=HERMES_REGISTRY
)

HEALTH_CHECK_DURATION = Histogram(
    'hermes_health_check_duration_seconds',
    'Health check duration',
    ['check_type'],
    registry=HERMES_REGISTRY
)

SLA_UPTIME_TARGET = Gauge(
    'hermes_sla_uptime_target_percentage',
    'SLA uptime target percentage',
    registry=HERMES_REGISTRY
)

SLA_UPTIME_ACTUAL = Gauge(
    'hermes_sla_uptime_actual_percentage',
    'Actual uptime percentage',
    registry=HERMES_REGISTRY
)

# === Error Tracking Metrics ===

ERROR_RATE = Gauge(
    'hermes_error_rate',
    'Application error rate',
    ['error_type', 'tenant_id'],
    registry=HERMES_REGISTRY
)

EXCEPTIONS_TOTAL = Counter(
    'hermes_exceptions_total',
    'Total exceptions raised',
    ['exception_type', 'module', 'tenant_id'],
    registry=HERMES_REGISTRY
)

# === Business Metrics ===

BUSINESS_CONVERSIONS = Counter(
    'hermes_business_conversions_total',
    'Business conversion events',
    ['tenant_id', 'conversion_type'],
    registry=HERMES_REGISTRY
)

BUSINESS_REVENUE = Gauge(
    'hermes_business_revenue_total',
    'Business revenue metrics',
    ['tenant_id', 'revenue_type', 'currency'],
    registry=HERMES_REGISTRY
)

@dataclass
class MetricsCollector:
    """Enhanced metrics collector with automatic tenant context."""

    start_time: float = field(default_factory=time.time)
    resource_monitor_task: Optional[asyncio.Task] = None

    def __post_init__(self):
        # Set application info
        APPLICATION_INFO.info({
            'version': '1.0.0',
            'environment': 'production' if not settings.debug else 'development',
            'debug': str(settings.debug).lower()
        })

        # Set SLA target
        SLA_UPTIME_TARGET.set(99.9)

        # Set initial application status
        APPLICATION_STATUS.state('starting')

    async def start_monitoring(self):
        """Start background monitoring tasks."""
        self.resource_monitor_task = asyncio.create_task(self._monitor_system_resources())
        APPLICATION_STATUS.state('healthy')
        logger.info("Enhanced metrics monitoring started")

    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        if self.resource_monitor_task:
            self.resource_monitor_task.cancel()
            try:
                await self.resource_monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Enhanced metrics monitoring stopped")

    @contextmanager
    def time_request(self, method: str, endpoint: str):
        """Context manager to time HTTP requests."""
        tenant_id = get_current_tenant() or "unknown"
        start_time = time.perf_counter()

        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            REQUEST_DURATION.labels(
                method=method.upper(),
                endpoint=endpoint,
                tenant_id=tenant_id
            ).observe(duration)

    def record_request(self, method: str, endpoint: str, status_code: int,
                      request_size: int = 0, response_size: int = 0):
        """Record HTTP request metrics."""
        tenant_id = get_current_tenant() or "unknown"

        REQUEST_COUNT.labels(
            method=method.upper(),
            endpoint=endpoint,
            status_code=str(status_code),
            tenant_id=tenant_id
        ).inc()

        if request_size > 0:
            REQUEST_SIZE.labels(
                method=method.upper(),
                endpoint=endpoint
            ).observe(request_size)

        if response_size > 0:
            RESPONSE_SIZE.labels(
                method=method.upper(),
                endpoint=endpoint,
                status_code=str(status_code)
            ).observe(response_size)

    @contextmanager
    def time_database_query(self, query_type: str, table: str = "unknown"):
        """Context manager to time database queries."""
        tenant_id = get_current_tenant() or "unknown"
        start_time = time.perf_counter()

        try:
            yield
            # Query successful
            DATABASE_QUERIES_TOTAL.labels(
                query_type=query_type,
                tenant_id=tenant_id,
                status="success"
            ).inc()

        except Exception as e:
            # Query failed
            DATABASE_QUERIES_TOTAL.labels(
                query_type=query_type,
                tenant_id=tenant_id,
                status="error"
            ).inc()
            raise

        finally:
            duration = time.perf_counter() - start_time
            DATABASE_QUERY_DURATION.labels(
                query_type=query_type,
                tenant_id=tenant_id,
                table=table
            ).observe(duration)

    def update_database_pool_metrics(self, active: int, idle: int, size: int, overflow: int):
        """Update database connection pool metrics."""
        DATABASE_POOL_SIZE.set(size)
        DATABASE_POOL_OVERFLOW.set(overflow)

        tenant_id = get_current_tenant() or "global"
        DATABASE_CONNECTIONS_ACTIVE.labels(tenant_id=tenant_id).set(active)
        DATABASE_CONNECTIONS_IDLE.labels(tenant_id=tenant_id).set(idle)

    @contextmanager
    def time_cache_operation(self, operation: str, cache_type: str = "redis"):
        """Context manager to time cache operations."""
        tenant_id = get_current_tenant() or "unknown"
        start_time = time.perf_counter()

        try:
            yield
            # Operation successful
            CACHE_OPERATIONS_TOTAL.labels(
                operation=operation,
                cache_type=cache_type,
                tenant_id=tenant_id,
                status="hit" if operation == "get" else "success"
            ).inc()

        except Exception as e:
            # Operation failed
            CACHE_OPERATIONS_TOTAL.labels(
                operation=operation,
                cache_type=cache_type,
                tenant_id=tenant_id,
                status="error"
            ).inc()
            raise

        finally:
            duration = time.perf_counter() - start_time
            CACHE_OPERATION_DURATION.labels(
                operation=operation,
                cache_type=cache_type
            ).observe(duration)

    def update_cache_metrics(self, cache_type: str, hit_ratio: float,
                           items_count: int, memory_usage: int):
        """Update cache performance metrics."""
        tenant_id = get_current_tenant() or "global"

        CACHE_HIT_RATIO.labels(
            cache_type=cache_type,
            tenant_id=tenant_id
        ).set(hit_ratio)

        CACHE_ITEMS_COUNT.labels(
            cache_type=cache_type,
            tenant_id=tenant_id
        ).set(items_count)

        CACHE_MEMORY_USAGE_BYTES.labels(
            cache_type=cache_type
        ).set(memory_usage)

    @contextmanager
    def time_voice_processing(self, stage: str):
        """Context manager to time voice processing stages."""
        tenant_id = get_current_tenant() or "unknown"
        start_time = time.perf_counter()

        try:
            yield
        finally:
            duration = time.perf_counter() - start_time
            VOICE_PROCESSING_DURATION.labels(
                stage=stage,
                tenant_id=tenant_id
            ).observe(duration)

    def update_voice_metrics(self, active_sessions: int, audio_quality: float,
                           transcription_accuracy: float, model: str = "whisper"):
        """Update voice processing metrics."""
        tenant_id = get_current_tenant() or "global"

        VOICE_SESSIONS_ACTIVE.labels(tenant_id=tenant_id).set(active_sessions)
        VOICE_AUDIO_QUALITY.labels(tenant_id=tenant_id).set(audio_quality)
        VOICE_TRANSCRIPTION_ACCURACY.labels(
            model=model,
            tenant_id=tenant_id
        ).set(transcription_accuracy)

    def update_websocket_connections(self, count: int):
        """Update WebSocket connection count."""
        VOICE_WEBSOCKET_CONNECTIONS.set(count)

    def record_tenant_api_usage(self, endpoint: str, plan_type: str = "free"):
        """Record tenant API usage."""
        tenant_id = get_current_tenant() or "unknown"

        TENANT_API_USAGE.labels(
            tenant_id=tenant_id,
            endpoint=endpoint,
            plan_type=plan_type
        ).inc()

    def update_tenant_metrics(self, tenant_id: str, active_users: int,
                            storage_usage: Dict[str, int]):
        """Update tenant-specific metrics."""
        TENANT_ACTIVE_USERS.labels(tenant_id=tenant_id).set(active_users)

        for storage_type, usage in storage_usage.items():
            TENANT_STORAGE_USAGE_BYTES.labels(
                tenant_id=tenant_id,
                storage_type=storage_type
            ).set(usage)

    def record_billing_event(self, event_type: str):
        """Record billing events."""
        tenant_id = get_current_tenant() or "unknown"

        TENANT_BILLING_EVENTS.labels(
            tenant_id=tenant_id,
            event_type=event_type
        ).inc()

    def record_exception(self, exception_type: str, module: str):
        """Record application exceptions."""
        tenant_id = get_current_tenant() or "unknown"

        EXCEPTIONS_TOTAL.labels(
            exception_type=exception_type,
            module=module,
            tenant_id=tenant_id
        ).inc()

    def update_error_rate(self, error_type: str, rate: float):
        """Update error rate metrics."""
        tenant_id = get_current_tenant() or "unknown"

        ERROR_RATE.labels(
            error_type=error_type,
            tenant_id=tenant_id
        ).set(rate)

    def record_business_conversion(self, conversion_type: str):
        """Record business conversion events."""
        tenant_id = get_current_tenant() or "unknown"

        BUSINESS_CONVERSIONS.labels(
            tenant_id=tenant_id,
            conversion_type=conversion_type
        ).inc()

    def update_uptime_metrics(self):
        """Update application uptime metrics."""
        uptime = time.time() - self.start_time
        UPTIME_SECONDS.set(uptime)

        # Calculate uptime percentage (assuming 99.9% SLA)
        uptime_hours = uptime / 3600
        if uptime_hours > 0:
            # Simple uptime calculation - in production, this would be more sophisticated
            uptime_percentage = min(99.9, (uptime_hours / (uptime_hours + 0.001)) * 100)
            SLA_UPTIME_ACTUAL.set(uptime_percentage)

    async def _monitor_system_resources(self):
        """Background task to monitor system resources."""
        import psutil

        while True:
            try:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                SYSTEM_CPU_USAGE.set(cpu_percent)

                # Memory metrics
                memory = psutil.virtual_memory()
                SYSTEM_MEMORY_USAGE.labels(type="total").set(memory.total)
                SYSTEM_MEMORY_USAGE.labels(type="available").set(memory.available)
                SYSTEM_MEMORY_USAGE.labels(type="used").set(memory.used)

                # Disk metrics
                disk = psutil.disk_usage('/')
                SYSTEM_DISK_USAGE.labels(path="/", type="total").set(disk.total)
                SYSTEM_DISK_USAGE.labels(path="/", type="used").set(disk.used)
                SYSTEM_DISK_USAGE.labels(path="/", type="free").set(disk.free)

                # Network metrics
                network = psutil.net_io_counters()
                SYSTEM_NETWORK_IO.labels(direction="sent").inc(network.bytes_sent)
                SYSTEM_NETWORK_IO.labels(direction="received").inc(network.bytes_recv)

                # Update uptime
                self.update_uptime_metrics()

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(60)

# Global metrics collector instance
metrics_collector = MetricsCollector()

def get_metrics_output() -> str:
    """Generate Prometheus metrics output."""
    return generate_latest(HERMES_REGISTRY).decode('utf-8')

def get_metrics_content_type() -> str:
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST

async def initialize_enhanced_metrics():
    """Initialize enhanced metrics system."""
    await metrics_collector.start_monitoring()
    logger.info("Enhanced metrics system initialized")

async def cleanup_enhanced_metrics():
    """Clean up enhanced metrics system."""
    await metrics_collector.stop_monitoring()
    logger.info("Enhanced metrics system cleaned up")

# Backward compatibility
def record_request_metrics(method: str, endpoint: str, status_code: int, elapsed: float):
    """Legacy function for backward compatibility."""
    metrics_collector.record_request(method, endpoint, status_code)

def export_metrics() -> bytes:
    """Legacy function for backward compatibility."""
    return get_metrics_output().encode('utf-8')

def calculate_uptime_metrics(health_history) -> float:
    """Legacy function for backward compatibility."""
    if not health_history:
        return 1.0
    successes = sum(1 for status in health_history if status)
    return successes / len(health_history)

def update_uptime_metrics(uptime_ratio: float):
    """Legacy function for backward compatibility."""
    SLA_UPTIME_ACTUAL.set(uptime_ratio * 100)

def update_active_connections(count: int):
    """Legacy function for backward compatibility."""
    metrics_collector.update_websocket_connections(count)