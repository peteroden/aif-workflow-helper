

from aif_workflow_helper.core.download import generalize_agent_dict



def test_connected_agent_id_to_name(agents_client_mock):
    # Add agent with id 'agent-id' and name 'resolved-name'
    class Dummy:
        pass
    agent = Dummy()
    agent.name = "resolved-name"
    agents_client_mock._agents_by_id["agent-id"] = agent
    data = {
        "type": "connected_agent",
        "connected_agent": {"id": "agent-id"},
        "id": "should-remove",
        "created_at": "should-remove"
    }
    result = generalize_agent_dict(data, agents_client_mock)
    assert "id" not in result
    assert "created_at" not in result
    assert result["connected_agent"]["name_from_id"] == "resolved-name"
    assert "id" not in result["connected_agent"]


def test_connected_agent_id_unknown(agents_client_mock):
    # No agent with id 'agent-id' in mock
    data = {
        "type": "connected_agent",
        "connected_agent": {"id": "agent-id"}
    }
    result = generalize_agent_dict(data, agents_client_mock)
    assert result["connected_agent"]["name_from_id"] == "Unknown Agent"


def test_removes_id_and_created_at_recursively(agents_client_mock):
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
    result = generalize_agent_dict(data, agents_client_mock)
    assert "id" not in result
    assert "created_at" not in result
    assert "id" not in result["foo"]
    assert "created_at" not in result["foo"]
    assert "id" not in result["foo"]["bar"][0]
    assert "created_at" not in result["foo"]["bar"][0]
    assert result["foo"]["bar"][1] == 2

def test_handles_list_of_dicts(agents_client_mock):
    data = [
        {"id": "a", "created_at": "b", "foo": 1},
        {"type": "connected_agent", "connected_agent": {"id": "x"}},
        123
    ]
    result = generalize_agent_dict(data, agents_client_mock)
    assert isinstance(result, list)
    assert "id" not in result[0]
    assert "created_at" not in result[0]
    assert result[2] == 123
    assert result[1]["connected_agent"]["name_from_id"] == "Unknown Agent"
