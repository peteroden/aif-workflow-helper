import pytest
from aif_workflow_helper.core.upload import create_or_update_agent, create_or_update_agents


def test_upload_rejects_missing_model(agents_client_mock, caplog):
    agent_dict = {"name": "test-agent", "instructions": "Do things"}
    result = create_or_update_agent(agent_dict, agents_client_mock)
    assert result is None
    assert any("missing required 'model'" in m for m in caplog.messages)

def test_upload_rejects_missing_instructions(agents_client_mock, caplog):
    agent_dict = {"name": "test-agent", "model": "gpt-4"}
    result = create_or_update_agent(agent_dict, agents_client_mock)
    assert result is None
    assert any("missing required 'instructions'" in m for m in caplog.messages)

def test_unresolved_connected_agent_logs_warning(agents_client_mock, caplog):
    agent_dict = {
        "name": "parent",
        "model": "gpt-4",
        "instructions": "Parent",
        "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "child-agent"}}
        ]
    }
    create_or_update_agent(agent_dict, agents_client_mock)
    # Warning should appear because child not resolved
    assert any("Unable to resolve connected agent" in m for m in caplog.messages)

def test_circular_dependency_raises(agents_client_mock):
    # Two agents referencing each other via name_from_id
    agents = {
        "A": {
            "name": "A",
            "model": "gpt-4",
            "instructions": "Agent A",
            "tools": [
                {"type": "connected_agent", "connected_agent": {"name_from_id": "B"}}
            ]
        },
        "B": {
            "name": "B",
            "model": "gpt-4",
            "instructions": "Agent B",
            "tools": [
                {"type": "connected_agent", "connected_agent": {"name_from_id": "A"}}
            ]
        }
    }
    with pytest.raises(ValueError):
        create_or_update_agents(agents, agents_client_mock)
