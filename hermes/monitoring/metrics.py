"""Prometheus metrics utilities for HERMES monitoring."""

from __future__ import annotations

import time
from typing import Iterable

from prometheus_client import Counter, Gauge, Histogram, generate_latest

APP_STARTED_AT = time.time()

REQUEST_LATENCY = Histogram(
    "hermes_request_latency_seconds",
    "Latency distribution for FastAPI HTTP requests.",
    labelnames=("method", "endpoint"),
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

REQUEST_COUNT = Counter(
    "hermes_requests_total",
    "Total number of HTTP requests served.",
    labelnames=("method", "endpoint", "status"),
)

VOICE_PROCESSING_LATENCY = Histogram(
    "hermes_voice_pipeline_latency_seconds",
    "End-to-end latency for voice pipeline interactions.",
    buckets=(0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 5.0),
)

SLA_UPTIME_TARGET = Gauge(
    "hermes_sla_uptime_target_percentage",
    "SLA uptime target percentage for dashboard usage.",
)

SLA_UPTIME_ACTUAL = Gauge(
    "hermes_sla_uptime_actual_percentage",
    "Rolling uptime percentage observed by health monitoring.",
)

ACTIVE_CONNECTIONS = Gauge(
    "hermes_active_voice_connections",
    "Number of active WebSocket voice connections.",
)

# Static SLA target derived from AGENTS.md (99.9% uptime SLA)
SLA_UPTIME_TARGET.set(99.9)


def record_request_metrics(method: str, endpoint: str, status_code: int, elapsed: float) -> None:
    """Record basic HTTP request metrics."""

    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)
    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status=str(status_code),
    ).inc()


def export_metrics() -> bytes:
    """Return Prometheus metrics in text exposition format."""

    return generate_latest()


def update_uptime_metrics(uptime_ratio: float) -> None:
    """Update uptime gauges with new ratio (0.0 - 1.0)."""

    SLA_UPTIME_ACTUAL.set(round(uptime_ratio * 100, 3))


def update_active_connections(count: int) -> None:
    """Update the active connection gauge."""

    ACTIVE_CONNECTIONS.set(count)


# Friendly helper for computing uptime after a successful health check.
def calculate_uptime_metrics(health_history: Iterable[bool]) -> float:
    """Compute uptime ratio based on recent health probe history."""

    history_list = list(health_history)
    if not history_list:
        return 1.0
    successes = sum(1 for status in history_list if status)
    return successes / len(history_list)
