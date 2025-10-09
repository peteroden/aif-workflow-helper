"""Integration-style tests for upload and download helpers."""

from __future__ import annotations

import json
from aif_workflow_helper.core.download import download_agent
from aif_workflow_helper.core.upload import create_or_update_agents_from_files




def test_create_or_update_agents_from_files_resolves_dependencies(tmp_path, agents_client_mock):
    """Ensure upload resolves connected_agent references using newly created IDs."""

    child_path = tmp_path / "child.json"
    parent_path = tmp_path / "parent.json"

    child_payload = {"name": "child", "tools": [], "model": "gpt-4", "instructions": "c"}
    parent_payload = {
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

    child_path.write_text(json.dumps(child_payload), encoding="utf-8")
    parent_path.write_text(json.dumps(parent_payload), encoding="utf-8")

    create_or_update_agents_from_files(
        path=str(tmp_path),
        agent_client=agents_client_mock,
        prefix="",
        suffix="",
        format="json",
    )

    agents = {agent.name: agent for agent in agents_client_mock.list_agents()}

    assert set(agents.keys()) == {"child", "parent"}
    parent_tools = agents["parent"].tools
    assert parent_tools, "parent should retain its connected agent tool"
    connected_data = parent_tools[0]["connected_agent"]
    assert "name_from_id" not in connected_data
    assert connected_data["id"] == agents["child"].id


def test_download_agent_writes_generalized_payload(tmp_path, agents_client_mock):
    """Verify download normalizes names and connected agent references."""

    prefix = "prod-"
    suffix = "-v1"
    # Create child then parent with explicit IDs to mirror prior fixture structure
    child_agent = agents_client_mock.create_agent(
        id="child-id", name=f"{prefix}child{suffix}", tools=[], model="gpt-4", instructions="c"
    )
    agents_client_mock.create_agent(
        id="parent-id",
        name=f"{prefix}parent{suffix}",
        tools=[
            {
                "type": "connected_agent",
                "connected_agent": {"id": child_agent.id},
            }
        ],
        model="gpt-4",
        instructions="p",
    )

    output_dir = tmp_path / "exports"
    result = download_agent(
        agent_name="parent",
        agent_client=agents_client_mock,
        file_path=str(output_dir),
        prefix=prefix,
        suffix=suffix,
        format="json",
    )

    assert result is True
    output_file = output_dir / "parent.json"
    assert output_file.exists()

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["name"] == "parent"
    tool_payload = payload["tools"][0]["connected_agent"]
    assert tool_payload["name_from_id"] == "child"
    assert "id" not in tool_payload