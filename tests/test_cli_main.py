"""Tests for the CLI entry point in `cli.main`."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

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


def test_main_exits_when_tenant_missing(monkeypatch, caplog):
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://endpoint")
    monkeypatch.setenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "model")
    monkeypatch.setattr(sys, "argv", ["prog", "--download-agent", "agent"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "tenant ID is required" in caplog.text


def test_main_exits_when_endpoint_missing(monkeypatch, caplog):
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "model")
    monkeypatch.setattr(sys, "argv", ["prog", "--download-agent", "agent"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "Project endpoint is required" in caplog.text


def test_main_exits_when_model_missing(monkeypatch, caplog):
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant")
    monkeypatch.setenv("AZURE_AI_PROJECT_ENDPOINT", "https://endpoint")
    monkeypatch.setattr(sys, "argv", ["prog", "--download-agent", "agent"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    assert "Model deployment name is required" in caplog.text


def test_main_invokes_handler_and_closes(monkeypatch):
    _set_base_env(monkeypatch)

    fake_client = MagicMock()
    fake_client.close = MagicMock()

    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "--download-agent", "agent"],
    )

    with patch(
        "aif_workflow_helper.cli.main.AgentFrameworkAgentsClient",
        return_value=fake_client,
    ) as mock_client_cls, patch(
        "aif_workflow_helper.cli.main.handle_download_agent_arg"
    ) as mock_handler:
        main()

    mock_client_cls.assert_called_once()
    mock_handler.assert_called_once()
    fake_client.close.assert_called_once()


def test_main_closes_client_when_handler_raises(monkeypatch):
    _set_base_env(monkeypatch)

    fake_client = MagicMock()
    fake_client.close = MagicMock()

    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "--download-agent", "agent"],
    )

    with patch(
        "aif_workflow_helper.cli.main.AgentFrameworkAgentsClient",
        return_value=fake_client,
    ), patch(
        "aif_workflow_helper.cli.main.handle_download_agent_arg",
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(RuntimeError):
            main()

    fake_client.close.assert_called_once()
