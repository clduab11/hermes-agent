import re

from hermes.monitoring import metrics


def test_record_request_metrics_updates_histogram():
    metrics.record_request_metrics("GET", "/test", 200, 0.12)
    output = metrics.export_metrics().decode("utf-8")
    assert 'hermes_request_latency_seconds_count{endpoint="/test",method="GET"}' in output
    assert 'hermes_requests_total{endpoint="/test",method="GET",status="200"} 1.0' in output


def test_calculate_and_update_uptime_metrics():
    ratio = metrics.calculate_uptime_metrics([True, False, True, True])
    assert ratio == 0.75
    metrics.update_uptime_metrics(ratio)
    output = metrics.export_metrics().decode("utf-8")
    assert 'hermes_sla_uptime_actual_percentage' in output


def test_active_connections_gauge_updates():
    metrics.update_active_connections(5)
    output = metrics.export_metrics().decode("utf-8")
    match = re.search(r'hermes_active_voice_connections\s+(\d+)', output)
    assert match and int(match.group(1)) == 5
