from unittest.mock import MagicMock
import pytest
from aif_workflow_helpers.upload_agent_helpers import create_or_update_agent
from . import test_consts

def make_agent(name, id="id1"):
    agent = MagicMock()
    agent.name = name
    agent.id = id
    return agent

class DummyClient:
    def __init__(self, agents=None):
        self._agents = agents or []
        self.create_agent = MagicMock(return_value=make_agent("created", "newid"))
        self.update_agent = MagicMock(return_value=make_agent("updated", "upid"))
        self.list_agents = MagicMock(return_value=self._agents)

@pytest.mark.usefixtures("caplog")
def test_create_new_agent():
    client = DummyClient([])
    agent_data = test_consts.TEST_AGENT_DATA
    result = create_or_update_agent(agent_data, client)
    client.create_agent.assert_called_once()
    assert result.name == "created"

@pytest.mark.usefixtures("caplog")
def test_update_existing_agent():
    existing = make_agent("agent", "exid")
    client = DummyClient([existing])
    result = create_or_update_agent(test_consts.TEST_AGENT_DATA, client)
    client.update_agent.assert_called_once()
    assert result.name == "updated"

@pytest.mark.usefixtures("caplog")
def test_resolve_name_from_id():
    # Should resolve name_from_id to id for connected_agent
    existing = make_agent("agent", "dep-id")
    client = DummyClient([existing])
    agent_data = {
        "name": "main-agent",
        "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "dep-agent"}}
        ]
    }
    result = create_or_update_agent(agent_data, client)  # noqa: F841
    args, kwargs = client.create_agent.call_args
    found = False
    for tool in kwargs.get("tools", []):
        if tool.get("type") == "connected_agent":
            assert tool["connected_agent"]["id"] == "dep-id"
            found = True
    assert found

@pytest.mark.usefixtures("caplog")
def test_unresolved_name_from_id_warns(caplog):
    client = DummyClient([])
    agent_data = {
        "name": "main-agent",
        "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "missing-agent"}}
        ]
    }
    result = create_or_update_agent(agent_data, client)  # noqa: F841
    assert any("Could not resolve agent name" in m for m in caplog.messages)

@pytest.mark.usefixtures("caplog")
def test_create_or_update_agent_exception(caplog):
    client = DummyClient([])
    client.create_agent.side_effect = Exception("fail-create")
    agent_data = {"name": "fail-agent", "tools": []}
    result = create_or_update_agent(agent_data, client)
    assert result is None
    assert any("Error creating/updating agent" in m for m in caplog.messages)
