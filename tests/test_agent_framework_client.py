"""Unit tests for the AgentFrameworkAgentsClient wrapper."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from aif_workflow_helper.core.agent_framework_client import AgentFrameworkAgentsClient


class DummyCredential:
    """Minimal async credential stub used to avoid real Azure auth."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class DummyAgents:
    """In-memory implementation of the async agents API."""

    def __init__(self) -> None:
        self._agents = [
            SimpleNamespace(id="agent-1", name="Agent One"),
            SimpleNamespace(id="agent-2", name="Agent Two"),
        ]
        self.created_kwargs: dict | None = None
        self.update_calls: list[tuple[str, dict]] = []
        self.get_calls: list[str] = []
        self.delete_calls: list[str] = []

    async def list_agents(self):
        for agent in self._agents:
            yield agent

    async def create_agent(self, **kwargs):
        self.created_kwargs = kwargs
        return SimpleNamespace(id="created", **kwargs)

    async def update_agent(self, agent_id: str, **kwargs):
        self.update_calls.append((agent_id, kwargs))
        return SimpleNamespace(id=agent_id, **kwargs)

    async def get_agent(self, agent_id: str):
        self.get_calls.append(agent_id)
        return SimpleNamespace(id=agent_id)

    async def delete_agent(self, agent_id: str):
        self.delete_calls.append(agent_id)


class DummyFrameworkClient:
    """Simplified Agent Framework client exposing the agents surface."""

    def __init__(self, agents: DummyAgents) -> None:
        self.project_client = SimpleNamespace(agents=agents)
        self.closed = False

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def client_fixture():
    """Provide a configured client and the associated test doubles."""

    dummy_agents = DummyAgents()
    credential_holder: dict[str, DummyCredential] = {}
    framework_holder: dict[str, DummyFrameworkClient] = {}

    def credential_factory(**kwargs):
        credential = DummyCredential(**kwargs)
        credential_holder["instance"] = credential
        return credential

    def fake_client(*, project_endpoint, model_deployment_name, async_credential):
        framework = DummyFrameworkClient(dummy_agents)
        framework_holder["instance"] = framework
        framework_holder["project_endpoint"] = project_endpoint
        framework_holder["model_deployment_name"] = model_deployment_name
        framework_holder["async_credential"] = async_credential
        return framework

    with patch(
        "aif_workflow_helper.core.agent_framework_client.AzureAIAgentClient",
        side_effect=fake_client,
    ) as mock_cls:
        client = AgentFrameworkAgentsClient(
            project_endpoint="https://example",
            tenant_id="tenant-id",
            model_deployment_name="model-name",
            credential_factory=credential_factory,
        )
        yield client, dummy_agents, credential_holder, framework_holder, mock_cls
        client.close()


def test_initialization_runs_once(client_fixture):
    """validate the client/credential are instantiated lazily."""

    client, _, credential_holder, framework_holder, mock_cls = client_fixture

    first = client.list_agents()
    second = client.list_agents()

    assert [agent.id for agent in first] == ["agent-1", "agent-2"]
    assert [agent.id for agent in second] == ["agent-1", "agent-2"]
    assert mock_cls.call_count == 1
    assert framework_holder["project_endpoint"] == "https://example"
    assert framework_holder["model_deployment_name"] == "model-name"
    assert credential_holder["instance"].kwargs["interactive_tenant_id"] == "tenant-id"


def test_create_agent_delegates_to_framework(client_fixture):
    """The wrapper should forward create requests to the agents API."""

    client, dummy_agents, _, _, _ = client_fixture

    result = client.create_agent(name="demo", instructions="hi")

    assert dummy_agents.created_kwargs == {"name": "demo", "instructions": "hi"}
    assert result.id == "created"
    assert result.name == "demo"


def test_update_agent_delegates_to_framework(client_fixture):
    """Updating an agent routes through the underlying async client."""

    client, dummy_agents, _, _, _ = client_fixture

    updated = client.update_agent("agent-1", description="new")

    assert dummy_agents.update_calls == [("agent-1", {"description": "new"})]
    assert updated.id == "agent-1"
    assert updated.description == "new"


def test_get_agent_delegates_to_framework(client_fixture):
    """Fetching an agent should use the internal agents client."""

    client, dummy_agents, _, _, _ = client_fixture

    fetched = client.get_agent("agent-2")

    assert dummy_agents.get_calls == ["agent-2"]
    assert fetched.id == "agent-2"


def test_delete_agent_delegates_to_framework(client_fixture):
    """Deleting an agent should call the underlying async API."""

    client, dummy_agents, _, _, _ = client_fixture

    client.delete_agent("agent-2")

    assert dummy_agents.delete_calls == ["agent-2"]


def test_close_releases_resources(client_fixture):
    """The close method should flush the event loop and async handles."""

    client, _, credential_holder, framework_holder, _ = client_fixture

    client.list_agents()
    client.close()

    assert framework_holder["instance"].closed is True
    assert credential_holder["instance"].closed is True


def test_context_manager_initializes_and_closes():
    """Using the wrapper as a context manager should manage lifecycle."""

    dummy_agents = DummyAgents()
    credential_holder: dict[str, DummyCredential] = {}
    framework_holder: dict[str, DummyFrameworkClient] = {}

    def credential_factory(**kwargs):
        credential = DummyCredential(**kwargs)
        credential_holder["instance"] = credential
        return credential

    def fake_client(*, project_endpoint, model_deployment_name, async_credential):
        framework = DummyFrameworkClient(dummy_agents)
        framework_holder["instance"] = framework
        framework_holder["async_credential"] = async_credential
        return framework

    with patch(
        "aif_workflow_helper.core.agent_framework_client.AzureAIAgentClient",
        side_effect=fake_client,
    ):
        with AgentFrameworkAgentsClient(
            project_endpoint="https://example",
            tenant_id="tenant-id",
            model_deployment_name="model-name",
            credential_factory=credential_factory,
        ) as client:
            assert client.list_agents()[0].id == "agent-1"

    assert framework_holder["instance"].closed is True
    assert credential_holder["instance"].closed is True
