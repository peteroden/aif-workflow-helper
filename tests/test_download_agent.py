import io
import json
import pytest
from unittest.mock import MagicMock, patch

import aif_workflow_helper.core.download as download_module
from aif_workflow_helper.core.download import download_agent, download_agents

def make_agent(name, as_dict=None):
    agent = MagicMock()
    agent.name = name
    agent.as_dict.return_value = as_dict or {"name": name, "tools": []}
    return agent



@pytest.mark.asyncio
@patch("builtins.open", new_callable=MagicMock)
async def test_download_agent_success(mock_open, agents_client_mock):
    agent = make_agent("test-agent", {"name": "test-agent", "tools": []})
    agents_client_mock._agents_by_id["test-agent"] = agent
    agents_client_mock._name_index["test-agent"] = "test-agent"
    file_obj = io.StringIO()
    mock_open.return_value.__enter__.return_value = file_obj
    await download_agent("test-agent", agents_client_mock)
    file_obj.seek(0)
    data = json.load(file_obj)
    assert data["name"] == "test-agent"
    assert "tools" in data

@pytest.mark.asyncio
@patch("builtins.open", new_callable=MagicMock)
async def test_download_agent_not_found(mock_open, caplog, agents_client_mock):
    await download_agent("missing-agent", agents_client_mock)
    assert any("not found" in m for m in caplog.messages)
    mock_open.assert_not_called()

@pytest.mark.asyncio
@patch("builtins.open", side_effect=OSError("fail"))
async def test_download_agent_file_error(mock_open, caplog, agents_client_mock):
    agent = make_agent("fail-agent", {"name": "fail-agent", "tools": []})
    agents_client_mock._agents_by_id["fail-agent"] = agent
    agents_client_mock._name_index["fail-agent"] = "fail-agent"
    await download_agent("fail-agent", agents_client_mock)
    # Should log an error or warning, but not raise
    assert any("fail" in m for m in caplog.messages)


@pytest.mark.asyncio
async def test_download_agent_directory_creation_failure(monkeypatch, agents_client_mock):
    agent = make_agent("test-agent", {"name": "test-agent", "tools": []})
    agents_client_mock._agents_by_id["test-agent"] = agent
    agents_client_mock._name_index["test-agent"] = "test-agent"

    monkeypatch.setattr(
        download_module.os,
        "makedirs",
        MagicMock(side_effect=OSError("nope")),
    )

    result = await download_agent("test-agent", agents_client_mock, file_path="/tmp/out")

    assert result is False


@pytest.mark.asyncio
async def test_download_agents_returns_false_when_save_fails(monkeypatch, agents_client_mock):
    agent = make_agent("test-agent", {"name": "test-agent", "tools": []})
    agents_client_mock._agents_by_id["test-agent"] = agent
    agents_client_mock._name_index["test-agent"] = "test-agent"

    monkeypatch.setattr(
        download_module,
        "save_agent_file",
        MagicMock(return_value=False),
    )

    result = await download_agents(agents_client_mock, file_path="/tmp/out")

    assert result is False


@pytest.mark.asyncio
async def test_download_agent_returns_false_when_agent_missing(monkeypatch, agents_client_mock):
    monkeypatch.setattr(
        download_module.os,
        "makedirs",
        MagicMock(),
    )

    result = await download_agent("unknown", agents_client_mock, file_path="/tmp/out")

    assert result is False
