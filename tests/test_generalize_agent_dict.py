from unittest.mock import MagicMock
from src.core.download import generalize_agent_dict

def make_agent(name):
    agent = MagicMock()
    agent.name = name
    return agent

def test_connected_agent_id_to_name():
    # agent_client returns agent name for id
    agent_client = MagicMock()
    agent_client.get_agent.return_value = make_agent("resolved-name")
    data = {
        "type": "connected_agent",
        "connected_agent": {"id": "agent-id"},
        "id": "should-remove",
        "created_at": "should-remove"
    }
    result = generalize_agent_dict(data, agent_client)
    assert "id" not in result
    assert "created_at" not in result
    assert result["connected_agent"]["name_from_id"] == "resolved-name"
    assert "id" not in result["connected_agent"]


def test_connected_agent_id_unknown():
    # agent_client returns None for id
    agent_client = MagicMock()
    agent_client.get_agent.return_value = None
    data = {
        "type": "connected_agent",
        "connected_agent": {"id": "agent-id"}
    }
    result = generalize_agent_dict(data, agent_client)
    assert result["connected_agent"]["name_from_id"] == "Unknown Agent"


def test_removes_id_and_created_at_recursively():
    agent_client = MagicMock()
    agent_client.get_agent.return_value = None
    data = {
        "id": "top-id",
        "created_at": "top-created",
        "foo": {
            "id": "nested-id",
            "created_at": "nested-created",
            "bar": [
                {"id": "list-id", "created_at": "list-created", "baz": 1},
                2,
            ]
        }
    }
    result = generalize_agent_dict(data, agent_client)
    assert "id" not in result
    assert "created_at" not in result
    assert "id" not in result["foo"]
    assert "created_at" not in result["foo"]
    assert "id" not in result["foo"]["bar"][0]
    assert "created_at" not in result["foo"]["bar"][0]
    assert result["foo"]["bar"][1] == 2

def test_handles_list_of_dicts():
    agent_client = MagicMock()
    agent_client.get_agent.return_value = None
    data = [
        {"id": "a", "created_at": "b", "foo": 1},
        {"type": "connected_agent", "connected_agent": {"id": "x"}},
        123
    ]
    result = generalize_agent_dict(data, agent_client)
    assert isinstance(result, list)
    assert "id" not in result[0]
    assert "created_at" not in result[0]
    assert result[2] == 123
    assert result[1]["connected_agent"]["name_from_id"] == "Unknown Agent"
