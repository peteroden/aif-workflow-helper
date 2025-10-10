"""Tests for the CLI entry point in `cli.main`."""

from __future__ import annotations

import sys
from unittest.mock import patch, AsyncMock

import pytest

from aif_workflow_helper.cli.main import main


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    """Ensure env vars do not leak between tests."""

    for key in [
        "AZURE_TENANT_ID",
        "AZURE_AI_PROJECT_ENDPOINT",
        "PROJECT_ENDPOINT",
        "AZURE_AI_MODEL_DEPLOYMENT_NAME",
    ]:
        monkeypatch.delenv(key, raising=False)


def _set_base_env(monkeypatch):
    """Populate the minimal environment expected by the CLI."""

    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://endpoint")
    monkeypatch.setenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "model")


@pytest.mark.asyncio
async def test_main_exits_when_tenant_missing(monkeypatch, caplog):
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://endpoint")
    monkeypatch.setenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "model")
    monkeypatch.setattr(sys, "argv", ["prog", "--download-agent", "agent"])

    with pytest.raises(SystemExit) as exc_info:
        await main()

    assert exc_info.value.code == 1
    assert "tenant ID is required" in caplog.text


@pytest.mark.asyncio
async def test_main_exits_when_endpoint_missing(monkeypatch, caplog):
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "model")
    monkeypatch.setattr(sys, "argv", ["prog", "--download-agent", "agent"])

    with pytest.raises(SystemExit) as exc_info:
        await main()

    assert exc_info.value.code == 1
    assert "Project endpoint is required" in caplog.text


@pytest.mark.asyncio
async def test_main_works_without_model_deployment_name(monkeypatch, mock_cli_agent_client):
    """Test that CLI works without global model deployment name (uses per-agent models)."""
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://endpoint")
    monkeypatch.setattr(sys, "argv", ["prog", "--download-agent", "agent"])

    with patch(
        "aif_workflow_helper.cli.main.AsyncAgentClient",
        return_value=mock_cli_agent_client,
    ) as mock_client_cls, patch(
        "aif_workflow_helper.cli.main.handle_download_agent_arg", new_callable=AsyncMock
    ) as mock_handler:
        await main()

    # Verify client was created with None for model_deployment_name
    mock_client_cls.assert_called_once_with(
        project_endpoint="https://endpoint",
        tenant_id="tenant", 
        model_deployment_name=None,
    )
    mock_handler.assert_called_once()
    mock_cli_agent_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_main_invokes_handler_and_closes(monkeypatch, mock_cli_agent_client):
    _set_base_env(monkeypatch)

    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "--download-agent", "agent"],
    )

    with patch(
        "aif_workflow_helper.cli.main.AsyncAgentClient",
        return_value=mock_cli_agent_client,
    ) as mock_client_cls, patch(
        "aif_workflow_helper.cli.main.handle_download_agent_arg", new_callable=AsyncMock
    ) as mock_handler:
        await main()

    mock_client_cls.assert_called_once()
    mock_handler.assert_called_once()
    mock_cli_agent_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_main_closes_client_when_handler_raises(monkeypatch, mock_cli_agent_client):
    _set_base_env(monkeypatch)

    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "--download-agent", "agent"],
    )

    with patch(
        "aif_workflow_helper.cli.main.AsyncAgentClient",
        return_value=mock_cli_agent_client,
    ), patch(
        "aif_workflow_helper.cli.main.handle_download_agent_arg",
        new_callable=AsyncMock, side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(RuntimeError):
            await main()

    mock_cli_agent_client.close.assert_called_once()
