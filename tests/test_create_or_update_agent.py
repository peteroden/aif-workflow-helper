import pytest
from unittest.mock import MagicMock

from aif_workflow_helper.core.upload import (
    create_or_update_agent,
    create_or_update_agents,
    create_or_update_agents_from_files,
)
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

@pytest.mark.asyncio
async def test_create_new_agent(agents_client_mock):
    agent_payload = {**test_consts.TEST_AGENT_DATA, "model": "gpt-4", "instructions": "hi"}
    result = await create_or_update_agent(agent_payload, agents_client_mock)
    assert result.name == test_consts.TEST_AGENT_DATA["name"]

@pytest.mark.asyncio
async def test_update_existing_agent(agents_client_mock):
    base = {**test_consts.TEST_AGENT_DATA, "model": "gpt-4", "instructions": "orig"}
    await create_or_update_agent(base, agents_client_mock)
    agent_data_update = base.copy()
    agent_data_update["instructions"] = "updated"
    result = await create_or_update_agent(agent_data_update, agents_client_mock)
    assert result.instructions == "updated"


@pytest.mark.asyncio
async def test_create_agent_drops_empty_tool_resources_and_object(agents_client_mock):
    agent_data = {
        "name": "agent",
        "tools": [],
        "tool_resources": {},
        "object": "agent",
        "model": "gpt-4",
        "instructions": "x",
    }

    result = await create_or_update_agent(agent_data, agents_client_mock)

    assert result.name == "agent"
    assert not hasattr(result, "tool_resources")
    assert "tool_resources" not in result._extra
    assert "object" not in result._extra


@pytest.mark.asyncio
async def test_create_agent_applies_prefix_and_suffix(agents_client_mock):
    agent_data = {"name": "core", "tools": [], "model": "gpt-4", "instructions": "x"}

    result = await create_or_update_agent(
        agent_data,
        agents_client_mock,
        prefix="pre-",
        suffix="-suf",
    )

    assert result.name == "pre-core-suf"


@pytest.mark.asyncio
async def test_create_agent_converts_connected_agent_names_with_prefix(agents_client_mock):
    child_data = {"name": "child", "tools": [], "model": "gpt-4", "instructions": "c"}
    child = await create_or_update_agent(child_data, agents_client_mock, prefix="pre-")

    parent_data = {
        "name": "parent",
        "tools": [
            {
                "type": "connected_agent",
                "connected_agent": {"name_from_id": "child"},
            }
        ],
        "model": "gpt-4",
        "instructions": "p",
    }

    parent = await create_or_update_agent(parent_data, agents_client_mock, prefix="pre-")

    tool_payload = parent.tools[0]["connected_agent"]
    assert "name_from_id" not in tool_payload
    assert tool_payload["id"] == child.id


@pytest.mark.asyncio
async def test_create_or_update_agent_requires_name(agents_client_mock, caplog):
    result = await create_or_update_agent({"tools": []}, agents_client_mock)

    assert result is None
    assert any("missing 'name'" in message for message in caplog.messages)


@pytest.mark.asyncio
async def test_create_or_update_agents_from_files_missing_directory(agents_client_mock):
    with pytest.raises(ValueError):
        await create_or_update_agents_from_files("/tmp/not-here", agents_client_mock)


@pytest.mark.asyncio
async def test_create_or_update_agents_detects_circular_dependencies(agents_client_mock):
    with pytest.raises(ValueError):
        await create_or_update_agents(
            test_consts.TEST_AGENT_DATA_CIRCULAR_DEPENDENCY,
            agents_client_mock,
        )
