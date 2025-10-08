import io
import json
from unittest.mock import MagicMock, patch

import aif_workflow_helper.core.download as download_module
from aif_workflow_helper.core.download import download_agent, download_agents

def make_agent(name, as_dict=None):
    agent = MagicMock()
    agent.name = name
    agent.as_dict.return_value = as_dict or {"name": name, "tools": []}
    return agent

class DummyClient:
    def __init__(self, agent=None):
        self._agent = agent
    def list_agents(self):
        return [self._agent] if self._agent else []
    def get_agent(self, agent_id):
        return self._agent if self._agent and self._agent.name == agent_id else None
    def get_agent_by_name(self, name):
        return self._agent if self._agent and self._agent.name == name else None

@patch("builtins.open", new_callable=MagicMock)
def test_download_agent_success(mock_open):
    agent = make_agent("test-agent", {"name": "test-agent", "tools": []})
    client = DummyClient(agent)
    file_obj = io.StringIO()
    mock_open.return_value.__enter__.return_value = file_obj
    download_agent("test-agent", client)
    file_obj.seek(0)
    data = json.load(file_obj)
    assert data["name"] == "test-agent"
    assert "tools" in data

@patch("builtins.open", new_callable=MagicMock)
def test_download_agent_not_found(mock_open, caplog):
    client = DummyClient(None)
    download_agent("missing-agent", client)
    assert any("not found" in m for m in caplog.messages)
    mock_open.assert_not_called()

@patch("builtins.open", side_effect=OSError("fail"))
def test_download_agent_file_error(mock_open, caplog):
    agent = make_agent("fail-agent", {"name": "fail-agent", "tools": []})
    client = DummyClient(agent)
    download_agent("fail-agent", client)
    # Should log an error or warning, but not raise
    assert any("fail" in m for m in caplog.messages)


def test_download_agent_directory_creation_failure(monkeypatch):
    agent = make_agent("test-agent", {"name": "test-agent", "tools": []})
    client = DummyClient(agent)

    monkeypatch.setattr(
        download_module.os,
        "makedirs",
        MagicMock(side_effect=OSError("nope")),
    )

    result = download_agent("test-agent", client, file_path="/tmp/out")

    assert result is False


def test_download_agents_returns_false_when_save_fails(monkeypatch):
    agent = make_agent("test-agent", {"name": "test-agent", "tools": []})
    client = DummyClient(agent)

    monkeypatch.setattr(
        download_module,
        "save_agent_file",
        MagicMock(return_value=False),
    )

    result = download_agents(client, file_path="/tmp/out")

    assert result is False


def test_download_agent_returns_false_when_agent_missing(monkeypatch):
    client = DummyClient(None)

    monkeypatch.setattr(
        download_module.os,
        "makedirs",
        MagicMock(),
    )

    result = download_agent("unknown", client, file_path="/tmp/out")

    assert result is False
