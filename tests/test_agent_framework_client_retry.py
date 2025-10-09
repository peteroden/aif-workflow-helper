import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from aif_workflow_helper.core.agent_framework_client import AgentFrameworkAgentsClient

class DummyErr(Exception):
    pass

@pytest.mark.parametrize("failures", [1,2])
def test_retry_transient_failures(monkeypatch, failures):
    client = AgentFrameworkAgentsClient(project_endpoint="https://example", tenant_id="tenant", model_deployment_name="model")

    async def failing_then_success():
        if failing_then_success.calls < failures:
            failing_then_success.calls += 1
            from azure.core.exceptions import ServiceRequestError
            raise ServiceRequestError("boom")
        return "ok"
    failing_then_success.calls = 0

    monkeypatch.setenv("AIF_RETRY_ATTEMPTS", "5")
    monkeypatch.setenv("AIF_RETRY_BASE_DELAY", "0.0")

    # Patch internal ensure + loop to avoid real network
    # Provide a real loop and bypass initialization
    client._loop = asyncio.new_event_loop()
    try:
        with patch.object(client, '_ensure_client', return_value=None):
            result = client._run(failing_then_success)
            assert result == "ok"
            assert failing_then_success.calls == failures
    finally:
        client._loop.close()


def test_retry_exhaust(monkeypatch):
    client = AgentFrameworkAgentsClient(project_endpoint="https://example", tenant_id="tenant", model_deployment_name="model")

    async def always_fail():
        from azure.core.exceptions import ServiceRequestError
        raise ServiceRequestError("nope")

    monkeypatch.setenv("AIF_RETRY_ATTEMPTS", "3")
    monkeypatch.setenv("AIF_RETRY_BASE_DELAY", "0.0")

    client._loop = asyncio.new_event_loop()
    try:
        with patch.object(client, '_ensure_client', return_value=None):
            with pytest.raises(Exception):
                client._run(always_fail)
    finally:
        client._loop.close()


class _FakeCredential:
    async def close(self) -> None:
        return None


class _FakeFrameworkClient:
    def __init__(self) -> None:
        self.project_client = SimpleNamespace(agents=object())

    async def close(self) -> None:
        return None


async def _fake_initialize(self: AgentFrameworkAgentsClient) -> None:
    self._credential = _FakeCredential()
    self._framework_client = _FakeFrameworkClient()
    self._agents_client = object()


def test_close_restores_previous_event_loop(monkeypatch):
    try:
        prior_loop = asyncio.get_running_loop()
    except RuntimeError:
        prior_loop = None

    original_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(original_loop)

    monkeypatch.setattr(
        AgentFrameworkAgentsClient,
        "_initialize_async",
        _fake_initialize,
        raising=False,
    )

    client = AgentFrameworkAgentsClient(project_endpoint="https://example", tenant_id="tenant", model_deployment_name="model")
    try:
        client._ensure_client()

        assert asyncio.get_event_loop() is client._loop

        client.close()

        try:
            restored_loop = asyncio.get_event_loop()
        except RuntimeError:
            restored_loop = None

        assert restored_loop is original_loop
    finally:
        asyncio.set_event_loop(prior_loop)
        original_loop.close()


async def _failing_initialize(self: AgentFrameworkAgentsClient) -> None:
    raise RuntimeError("boom")


def test_failed_initialize_restores_loop(monkeypatch):
    try:
        prior_loop = asyncio.get_running_loop()
    except RuntimeError:
        prior_loop = None

    original_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(original_loop)

    monkeypatch.setattr(
        AgentFrameworkAgentsClient,
        "_initialize_async",
        _failing_initialize,
        raising=False,
    )

    client = AgentFrameworkAgentsClient(project_endpoint="https://example", tenant_id="tenant", model_deployment_name="model")
    try:
        with pytest.raises(RuntimeError, match="boom"):
            client._ensure_client()

        assert client._loop is None

        try:
            restored_loop = asyncio.get_event_loop()
        except RuntimeError:
            restored_loop = None

        assert restored_loop is original_loop
    finally:
        asyncio.set_event_loop(prior_loop)
        original_loop.close()
