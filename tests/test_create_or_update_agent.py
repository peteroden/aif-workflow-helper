import pytest
from unittest.mock import MagicMock

from aif_workflow_helper.core.upload import (
    create_or_update_agent,
    create_or_update_agents,
    create_or_update_agents_from_files,
)
from . import test_consts
from .test_agent_client_mock import AgentsClientMock

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

def test_create_new_agent():
    client = AgentsClientMock()
    result = create_or_update_agent(test_consts.TEST_AGENT_DATA, client)
    assert result.name == test_consts.TEST_AGENT_DATA["name"]

def test_update_existing_agent():
    client = AgentsClientMock()
    create_or_update_agent(test_consts.TEST_AGENT_DATA, client)
    agent_data_update = test_consts.TEST_AGENT_DATA.copy()
    agent_data_update["instructions"] = "updated"
    result = create_or_update_agent(agent_data_update, client)
    assert result.instructions == "updated"


def test_create_agent_drops_empty_tool_resources_and_object():
    client = AgentsClientMock()
    agent_data = {
        "name": "agent",
        "tools": [],
        "tool_resources": {},
        "object": "agent",
    }

    result = create_or_update_agent(agent_data, client)

    assert result.name == "agent"
    assert not hasattr(result, "tool_resources")
    assert "tool_resources" not in result._extra
    assert "object" not in result._extra


def test_create_agent_applies_prefix_and_suffix():
    client = AgentsClientMock()
    agent_data = {"name": "core", "tools": []}

    result = create_or_update_agent(
        agent_data,
        client,
        prefix="pre-",
        suffix="-suf",
    )

    assert result.name == "pre-core-suf"


def test_create_agent_converts_connected_agent_names_with_prefix():
    client = AgentsClientMock()

    child_data = {"name": "child", "tools": []}
    child = create_or_update_agent(child_data, client, prefix="pre-")

    parent_data = {
        "name": "parent",
        "tools": [
            {
                "type": "connected_agent",
                "connected_agent": {"name_from_id": "child"},
            }
        ],
    }

    parent = create_or_update_agent(parent_data, client, prefix="pre-")

    tool_payload = parent.tools[0]["connected_agent"]
    assert "name_from_id" not in tool_payload
    assert tool_payload["id"] == child.id


def test_create_or_update_agent_requires_name(caplog):
    client = AgentsClientMock()

    result = create_or_update_agent({"tools": []}, client)

    assert result is None
    assert any("missing 'name'" in message for message in caplog.messages)


def test_create_or_update_agents_from_files_missing_directory():
    client = AgentsClientMock()

    with pytest.raises(ValueError):
        create_or_update_agents_from_files("/tmp/not-here", client)


def test_create_or_update_agents_detects_circular_dependencies():
    client = AgentsClientMock()

    with pytest.raises(ValueError):
        create_or_update_agents(
            test_consts.TEST_AGENT_DATA_CIRCULAR_DEPENDENCY,
            client,
        )
