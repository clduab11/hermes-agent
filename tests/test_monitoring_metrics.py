import re

import pytest
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

from hermes.monitoring import metrics


@pytest.fixture(autouse=True)
def isolated_metrics(monkeypatch):
    registry = CollectorRegistry()

    request_latency = Histogram(
        "hermes_request_latency_seconds",
        "Latency distribution for FastAPI HTTP requests.",
        labelnames=("method", "endpoint"),
        buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        registry=registry,
    )
    request_count = Counter(
        "hermes_requests_total",
        "Total number of HTTP requests served.",
        labelnames=("method", "endpoint", "status"),
        registry=registry,
    )
    voice_latency = Histogram(
        "hermes_voice_pipeline_latency_seconds",
        "End-to-end latency for voice pipeline interactions.",
        buckets=(0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 5.0),
        registry=registry,
    )
    uptime_target = Gauge(
        "hermes_sla_uptime_target_percentage",
        "SLA uptime target percentage for dashboard usage.",
        registry=registry,
    )
    uptime_actual = Gauge(
        "hermes_sla_uptime_actual_percentage",
        "Rolling uptime percentage observed by health monitoring.",
        registry=registry,
    )
    active_connections = Gauge(
        "hermes_active_voice_connections",
        "Number of active WebSocket voice connections.",
        registry=registry,
    )

    uptime_target.set(99.9)

    monkeypatch.setattr(metrics, "REQUEST_LATENCY", request_latency)
    monkeypatch.setattr(metrics, "REQUEST_COUNT", request_count)
    monkeypatch.setattr(metrics, "VOICE_PROCESSING_LATENCY", voice_latency)
    monkeypatch.setattr(metrics, "SLA_UPTIME_TARGET", uptime_target)
    monkeypatch.setattr(metrics, "SLA_UPTIME_ACTUAL", uptime_actual)
    monkeypatch.setattr(metrics, "ACTIVE_CONNECTIONS", active_connections)
    monkeypatch.setattr(metrics, "generate_latest", lambda: generate_latest(registry))

    yield


def test_record_request_metrics_updates_histogram():
    metrics.record_request_metrics("GET", "/test", 200, 0.12)
    output = metrics.export_metrics().decode("utf-8")
    assert 'hermes_request_latency_seconds_count{endpoint="/test",method="GET"}' in output
    assert 'hermes_requests_total{endpoint="/test",method="GET",status="200"} 1.0' in output


def test_record_metrics_rejects_invalid_input():
    with pytest.raises(ValueError):
        metrics.record_request_metrics("", "/test", 200, 0.1)
    with pytest.raises(ValueError):
        metrics.record_request_metrics("GET", "/test", 99, 0.1)
    with pytest.raises(ValueError):
        metrics.record_request_metrics("GET", "/test", 200, -1.0)


def test_calculate_and_update_uptime_metrics():
    ratio = metrics.calculate_uptime_metrics([True, False, True, True])
    assert ratio == 0.75
    metrics.update_uptime_metrics(ratio)
    output = metrics.export_metrics().decode("utf-8")
    assert 'hermes_sla_uptime_actual_percentage' in output


def test_update_uptime_metrics_bounds():
    with pytest.raises(ValueError):
        metrics.update_uptime_metrics(-0.1)
    with pytest.raises(ValueError):
        metrics.update_uptime_metrics(1.5)


def test_active_connections_gauge_updates():
    metrics.update_active_connections(5)
    output = metrics.export_metrics().decode("utf-8")
    match = re.search(r'hermes_active_voice_connections\s+(\d+)', output)
    assert match and int(match.group(1)) == 5


def test_active_connections_rejects_negative_values():
    with pytest.raises(ValueError):
        metrics.update_active_connections(-1)
