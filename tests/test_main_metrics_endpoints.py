import os
import sys
import types
from collections import deque
from types import SimpleNamespace

import pytest

# Provide lightweight stubs for optional dependencies before importing the app
sys.modules.setdefault("asyncpg", types.SimpleNamespace(Connection=object))
sys.modules.setdefault("whisper", types.SimpleNamespace(load_model=lambda *args, **kwargs: None))

# Provide router stubs for optional routers
from fastapi import APIRouter

router_stub = APIRouter()
sys.modules.setdefault("hermes.api.analytics_endpoints", SimpleNamespace(router=router_stub))
sys.modules.setdefault("hermes.api.billing_endpoints", SimpleNamespace(router=router_stub))
sys.modules.setdefault("hermes.api.clio_endpoints", SimpleNamespace(router=router_stub))
sys.modules.setdefault("hermes.audit.api", SimpleNamespace(router=router_stub))

# Ensure FastAPI settings default to debug for tests before importing app
os.environ.setdefault("DEBUG", "true")

import hermes.main as main


@pytest.fixture(autouse=True)
def reset_app_state():
    main.health_history = deque(maxlen=100)
    main.health_history.extend([True, True, False])

    main.app.state.request_metrics = {"count": 2, "total": 0.15}

    main.voice_pipeline = SimpleNamespace(
        get_performance_metrics=lambda: {
            "average_latency_seconds": 0.08,
            "interactions_processed": 42,
        }
    )
    main.websocket_handler = SimpleNamespace(get_connection_count=lambda: 3)
    yield


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_prometheus():
    response = await main.metrics_endpoint()
    assert response.media_type.startswith("text/plain")
    body = response.body.decode("utf-8")
    assert "hermes_request_latency_seconds" in body


@pytest.mark.asyncio
async def test_sla_endpoint_returns_expected_payload():
    payload = await main.sla_overview()
    assert payload["uptime"]["target_percent"] == 99.9
    assert payload["voice_pipeline"]["interactions_processed"] == 42
    assert payload["latency"]["voice_pipeline_average_ms"] == pytest.approx(80.0)
    assert payload["active_connections"] == 3
