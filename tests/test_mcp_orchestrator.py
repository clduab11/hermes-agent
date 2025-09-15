import os

import pytest

from hermes.mcp.orchestrator import MCPOrchestrator


@pytest.fixture(autouse=True)
def configure_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "supabase-test-token")
    monkeypatch.setenv("GITHUB_TOKEN", "github-test-token")
    monkeypatch.setenv("MEM0_API_KEY", "mem0-test-token")
    yield


def test_orchestrator_loads_servers_from_config():
    orchestrator = MCPOrchestrator()

    assert "redis" in orchestrator.servers
    assert orchestrator.servers["redis"].url.startswith("redis://")

    assert "supabase" in orchestrator.servers
    assert orchestrator.servers["supabase"].auth_token == "supabase-test-token"

    assert "github" in orchestrator.servers
    assert orchestrator.servers["github"].auth_token == "github-test-token"

    assert "sequential-thinking" in orchestrator.servers
    assert (
        orchestrator.servers["sequential-thinking"].server_type.value
        == "sequential_thinking"
    )
