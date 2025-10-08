"""Integration-style tests for upload and download helpers."""

from __future__ import annotations

import json
from aif_workflow_helper.core.download import download_agent
from aif_workflow_helper.core.upload import create_or_update_agents_from_files

from .test_agent_client_mock import AgentsClientMock


class SimpleAgent:
    """Minimal agent stand-in exposing the attributes used by download code."""

    def __init__(self, agent_id: str, name: str, payload: dict) -> None:
        self.id = agent_id
        self.name = name
        self._payload = payload

    def as_dict(self) -> dict:
        """Return the stored payload in Azure SDK compatible form."""
        return self._payload


class DownloadClientStub:
    """Synchronous client stub implementing the subset used by downloads."""

    def __init__(self, agents: list[SimpleAgent]) -> None:
        self._agents = agents
        self._by_id = {agent.id: agent for agent in agents}

    def list_agents(self) -> list[SimpleAgent]:
        """Return the full agent listing."""
        return self._agents

    def get_agent(self, agent_id: str) -> SimpleAgent | None:
        """Fetch a single agent by ID."""
        return self._by_id.get(agent_id)


def test_create_or_update_agents_from_files_resolves_dependencies(tmp_path):
    """Ensure upload resolves connected_agent references using newly created IDs."""

    child_path = tmp_path / "child.json"
    parent_path = tmp_path / "parent.json"

    child_payload = {"name": "child", "tools": []}
    parent_payload = {
        "name": "parent",
        "tools": [
            {
                "type": "connected_agent",
                "connected_agent": {"name_from_id": "child"},
            }
        ],
    }

    child_path.write_text(json.dumps(child_payload), encoding="utf-8")
    parent_path.write_text(json.dumps(parent_payload), encoding="utf-8")

    client = AgentsClientMock()

    create_or_update_agents_from_files(
        path=str(tmp_path),
        agent_client=client,
        prefix="",
        suffix="",
        format="json",
    )

    agents = {agent.name: agent for agent in client.list_agents()}

    assert set(agents.keys()) == {"child", "parent"}
    parent_tools = agents["parent"].tools
    assert parent_tools, "parent should retain its connected agent tool"
    connected_data = parent_tools[0]["connected_agent"]
    assert "name_from_id" not in connected_data
    assert connected_data["id"] == agents["child"].id


def test_download_agent_writes_generalized_payload(tmp_path):
    """Verify download normalizes names and connected agent references."""

    prefix = "prod-"
    suffix = "-v1"
    child_payload = {
        "id": "child-id",
        "name": f"{prefix}child{suffix}",
        "tools": [],
    }
    parent_payload = {
        "id": "parent-id",
        "name": f"{prefix}parent{suffix}",
        "tools": [
            {
                "type": "connected_agent",
                "connected_agent": {"id": "child-id"},
            }
        ],
    }

    child_agent = SimpleAgent("child-id", child_payload["name"], child_payload)
    parent_agent = SimpleAgent("parent-id", parent_payload["name"], parent_payload)
    client = DownloadClientStub([parent_agent, child_agent])

    output_dir = tmp_path / "exports"
    result = download_agent(
        agent_name="parent",
        agent_client=client,
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