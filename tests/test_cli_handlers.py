"""Comprehensive tests for CLI handler functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from argparse import Namespace
import pytest

from aif_workflow_helper.cli.main import (
    handle_download_agent_arg,
    handle_download_all_agents_arg,
    handle_upload_agent_arg,
    handle_upload_all_agents_arg,
    handle_get_agent_id_arg,
    handle_delete_agent_arg,
    handle_delete_all_agents_arg,
    confirm_deletion,
    process_args,
)


class TestDownloadAgentHandler:
    """Test the download agent handler function."""

    def test_download_agent_success(self, tmp_path, caplog, mock_cli_agent_client):
        """Test successful agent download."""
        args = Namespace(
            download_agent="test-agent",
            agents_dir=str(tmp_path),
            prefix="",
            suffix="",
            format="json"
        )

        with caplog.at_level("INFO"), \
             patch("aif_workflow_helper.cli.main.download_agent") as mock_download:
            handle_download_agent_arg(args, mock_cli_agent_client)

        mock_download.assert_called_once_with(
            agent_name="test-agent",
            agent_client=mock_cli_agent_client,
            file_path=str(tmp_path),
            prefix="",
            suffix="",
            format="json"
        )
        assert "Connecting..." in caplog.text
        assert "Downloading agent test-agent..." in caplog.text

    def test_download_agent_empty_name(self, tmp_path, caplog, mock_cli_agent_client):
        """Test download with empty agent name."""
        args = Namespace(
            download_agent="",
            agents_dir=str(tmp_path),
            prefix="",
            suffix="",
            format="json"
        )

        with caplog.at_level("INFO"):
            handle_download_agent_arg(args, mock_cli_agent_client)

        assert "Agent name not provided" in caplog.text

    def test_download_agent_exception(self, tmp_path, caplog, mock_cli_agent_client):
        """Test download agent with exception."""
        args = Namespace(
            download_agent="test-agent",
            agents_dir=str(tmp_path),
            prefix="",
            suffix="",
            format="json"
        )
        mock_cli_agent_client.list_agents.side_effect = Exception("Connection failed")

        handle_download_agent_arg(args, mock_cli_agent_client)

        assert "Unhandled error in downloading agent: Connection failed" in caplog.text


class TestDownloadAllAgentsHandler:
    """Test the download all agents handler function."""

    def test_download_all_agents_success(self, tmp_path, caplog, mock_cli_agent_client):
        """Test successful all agents download."""
        args = Namespace(
            agents_dir=str(tmp_path),
            prefix="test-",
            suffix="-v1",
            format="yaml"
        )

        with caplog.at_level("INFO"), \
             patch("aif_workflow_helper.cli.main.download_agents") as mock_download:
            handle_download_all_agents_arg(args, mock_cli_agent_client)

        mock_download.assert_called_once_with(
            mock_cli_agent_client,
            file_path=str(tmp_path),
            prefix="test-",
            suffix="-v1",
            format="yaml"
        )
        assert "Connected. Found 0 existing agents" in caplog.text

    def test_download_all_agents_exception(self, tmp_path, caplog, mock_cli_agent_client):
        """Test download all agents with exception."""
        args = Namespace(
            agents_dir=str(tmp_path),
            prefix="",
            suffix="",
            format="json"
        )
        mock_cli_agent_client.list_agents.side_effect = Exception("Network error")

        handle_download_all_agents_arg(args, mock_cli_agent_client)

        assert "Unhandled error in downloading agents: Network error" in caplog.text


class TestUploadAgentHandler:
    """Test the upload agent handler function."""

    def test_upload_agent_success(self, tmp_path, mock_cli_agent_client):
        """Test successful agent upload."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        
        args = Namespace(
            upload_agent="test-agent",
            agents_dir=str(agents_dir),
            prefix="dev-",
            suffix="-v1",
            format="json"
        )

        with patch("aif_workflow_helper.cli.main.create_or_update_agent_from_file") as mock_upload:
            handle_upload_agent_arg(args, mock_cli_agent_client)

        mock_upload.assert_called_once_with(
            agent_name="test-agent",
            path=str(agents_dir),
            agent_client=mock_cli_agent_client,
            prefix="dev-",
            suffix="-v1",
            format="json"
        )

    def test_upload_agent_missing_directory(self, tmp_path, caplog, mock_cli_agent_client):
        """Test upload agent with missing directory."""
        args = Namespace(
            upload_agent="test-agent",
            agents_dir=str(tmp_path / "nonexistent"),
            prefix="",
            suffix="",
            format="json"
        )

        with pytest.raises(SystemExit) as exc_info:
            handle_upload_agent_arg(args, mock_cli_agent_client)

        assert exc_info.value.code == 1
        assert "Agents directory not found" in caplog.text

    def test_upload_agent_exception(self, tmp_path, caplog, mock_cli_agent_client):
        """Test upload agent with exception."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        
        args = Namespace(
            upload_agent="test-agent",
            agents_dir=str(agents_dir),
            prefix="",
            suffix="",
            format="json"
        )

        with patch("aif_workflow_helper.cli.main.create_or_update_agent_from_file", 
                  side_effect=Exception("Upload failed")):
            handle_upload_agent_arg(args, mock_cli_agent_client)

        assert "Error uploading agent test-agent: Upload failed" in caplog.text


class TestUploadAllAgentsHandler:
    """Test the upload all agents handler function."""

    def test_upload_all_agents_success(self, tmp_path, mock_cli_agent_client):
        """Test successful all agents upload."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()
        
        args = Namespace(
            agents_dir=str(agents_dir),
            prefix="prod-",
            suffix="",
            format="yaml"
        )

        with patch("aif_workflow_helper.cli.main.create_or_update_agents_from_files") as mock_upload:
            handle_upload_all_agents_arg(args, mock_cli_agent_client)

        mock_upload.assert_called_once_with(
            path=str(agents_dir),
            agent_client=mock_cli_agent_client,
            prefix="prod-",
            suffix="",
            format="yaml"
        )

    def test_upload_all_agents_missing_directory(self, tmp_path, caplog, mock_cli_agent_client):
        """Test upload all agents with missing directory."""
        args = Namespace(
            agents_dir=str(tmp_path / "missing"),
            prefix="",
            suffix="",
            format="json"
        )

        with pytest.raises(SystemExit) as exc_info:
            handle_upload_all_agents_arg(args, mock_cli_agent_client)

        assert exc_info.value.code == 1
        assert "Agents directory not found" in caplog.text


class TestGetAgentIdHandler:
    """Test the get agent ID handler function."""

    def test_get_agent_id_success(self, caplog, capsys, mock_cli_agent_client):
        """Test successful agent ID retrieval."""
        args = Namespace(get_agent_id="test-agent")
        mock_agent = MagicMock()
        mock_agent.id = "asst_123456"

        with caplog.at_level("INFO"), \
             patch("aif_workflow_helper.cli.main.get_agent_by_name", return_value=mock_agent):
            handle_get_agent_id_arg(args, mock_cli_agent_client)

        captured = capsys.readouterr()
        assert "asst_123456" in captured.out
        assert "Agent 'test-agent' has ID: asst_123456" in caplog.text

    def test_get_agent_id_not_found(self, caplog, mock_cli_agent_client):
        """Test agent ID retrieval when agent not found."""
        args = Namespace(get_agent_id="missing-agent")

        with patch("aif_workflow_helper.cli.main.get_agent_by_name", return_value=None):
            with pytest.raises(SystemExit) as exc_info:
                handle_get_agent_id_arg(args, mock_cli_agent_client)

        assert exc_info.value.code == 1
        assert "Agent 'missing-agent' not found" in caplog.text

    def test_get_agent_id_empty_name(self, caplog, mock_cli_agent_client):
        """Test get agent ID with empty name."""
        args = Namespace(get_agent_id="")

        with pytest.raises(SystemExit) as exc_info:
            handle_get_agent_id_arg(args, mock_cli_agent_client)

        assert exc_info.value.code == 1
        assert "Agent name is required for --get-agent-id" in caplog.text

    def test_get_agent_id_exception(self, caplog, mock_cli_agent_client):
        """Test get agent ID with exception."""
        args = Namespace(get_agent_id="test-agent")

        with patch("aif_workflow_helper.cli.main.get_agent_by_name", 
                  side_effect=Exception("Lookup failed")):
            with pytest.raises(SystemExit) as exc_info:
                handle_get_agent_id_arg(args, mock_cli_agent_client)

        assert exc_info.value.code == 1
        assert "Error getting agent ID for 'test-agent': Lookup failed" in caplog.text


class TestDeleteAgentHandler:
    """Test the delete agent handler function."""

    def test_delete_agent_success_with_force(self, caplog, mock_cli_agent_client):
        """Test successful agent deletion with force flag."""
        args = Namespace(
            delete_agent="test-agent",
            prefix="dev-",
            suffix="-v1",
            force=True
        )

        with patch("aif_workflow_helper.cli.main.delete_agent_by_name", return_value=True):
            handle_delete_agent_arg(args, mock_cli_agent_client)

        # Should not show confirmation since force=True

    def test_delete_agent_success_with_confirmation(self, caplog, mock_cli_agent_client):
        """Test successful agent deletion with user confirmation."""
        args = Namespace(
            delete_agent="test-agent",
            prefix="",
            suffix="",
            force=False
        )

        with patch("aif_workflow_helper.cli.main.confirm_deletion", return_value=True), \
             patch("aif_workflow_helper.cli.main.delete_agent_by_name", return_value=True):
            handle_delete_agent_arg(args, mock_cli_agent_client)

    def test_delete_agent_cancelled_by_user(self, caplog, mock_cli_agent_client):
        """Test agent deletion cancelled by user."""
        args = Namespace(
            delete_agent="test-agent",
            prefix="",
            suffix="",
            force=False
        )

        with caplog.at_level("INFO"), \
             patch("aif_workflow_helper.cli.main.confirm_deletion", return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                handle_delete_agent_arg(args, mock_cli_agent_client)

        assert exc_info.value.code == 0
        assert "Deletion cancelled by user" in caplog.text

    def test_delete_agent_empty_name(self, caplog, mock_cli_agent_client):
        """Test delete agent with empty name."""
        args = Namespace(delete_agent="", prefix="", suffix="", force=True)

        with pytest.raises(SystemExit) as exc_info:
            handle_delete_agent_arg(args, mock_cli_agent_client)

        assert exc_info.value.code == 1
        assert "Agent name is required for --delete-agent" in caplog.text

    def test_delete_agent_failure(self, mock_cli_agent_client):
        """Test agent deletion failure."""
        args = Namespace(
            delete_agent="test-agent",
            prefix="",
            suffix="",
            force=True
        )

        with patch("aif_workflow_helper.cli.main.delete_agent_by_name", return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                handle_delete_agent_arg(args, mock_cli_agent_client)

        assert exc_info.value.code == 1


class TestDeleteAllAgentsHandler:
    """Test the delete all agents handler function."""

    def test_delete_all_agents_success(self, caplog, mock_cli_agent_client):
        """Test successful bulk agent deletion."""
        args = Namespace(
            prefix="test-",
            suffix="-v1",
            force=True
        )
        # Example of using the unified mock's helper methods
        mock_agents = [MagicMock(), MagicMock()]
        mock_agents[0].name = "test-agent1-v1"
        mock_agents[1].name = "test-agent2-v1"
        mock_cli_agent_client.set_agents_list(mock_agents)

        with patch("aif_workflow_helper.cli.main.get_matching_agents", return_value=mock_agents), \
             patch("aif_workflow_helper.cli.main.delete_agents", return_value=(True, 2)):
            handle_delete_all_agents_arg(args, mock_cli_agent_client)

    def test_delete_all_agents_no_matches(self, caplog, mock_cli_agent_client):
        """Test bulk deletion with no matching agents."""
        args = Namespace(prefix="nonexistent-", suffix="", force=True)

        with caplog.at_level("INFO"), \
             patch("aif_workflow_helper.cli.main.get_matching_agents", return_value=[]):
            handle_delete_all_agents_arg(args, mock_cli_agent_client)

        assert "No agents found matching the specified criteria" in caplog.text

    def test_delete_all_agents_cancelled(self, caplog, mock_cli_agent_client):
        """Test bulk deletion cancelled by user."""
        args = Namespace(prefix="", suffix="", force=False)
        mock_agents = [MagicMock()]
        mock_agents[0].name = "test-agent"

        with caplog.at_level("INFO"), \
             patch("aif_workflow_helper.cli.main.get_matching_agents", return_value=mock_agents), \
             patch("aif_workflow_helper.cli.main.confirm_deletion", return_value=False):
            handle_delete_all_agents_arg(args, mock_cli_agent_client)

        assert "Deletion cancelled by user" in caplog.text


class TestConfirmDeletion:
    """Test the deletion confirmation function."""

    def test_confirm_deletion_yes(self):
        """Test deletion confirmation with 'yes' response."""
        with patch("builtins.input", return_value="yes"):
            result = confirm_deletion(["agent1", "agent2"])
        assert result is True

    def test_confirm_deletion_y(self):
        """Test deletion confirmation with 'y' response."""
        with patch("builtins.input", return_value="y"):
            result = confirm_deletion(["agent1"])
        assert result is True

    def test_confirm_deletion_no(self):
        """Test deletion confirmation with 'no' response."""
        with patch("builtins.input", return_value="no"):
            result = confirm_deletion(["agent1"])
        assert result is False

    def test_confirm_deletion_empty_list(self):
        """Test deletion confirmation with empty agent list."""
        result = confirm_deletion([])
        assert result is False

    def test_confirm_deletion_keyboard_interrupt(self):
        """Test deletion confirmation with keyboard interrupt."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = confirm_deletion(["agent1"])
        assert result is False

    def test_confirm_deletion_eof_error(self):
        """Test deletion confirmation with EOF error."""
        with patch("builtins.input", side_effect=EOFError):
            result = confirm_deletion(["agent1"])
        assert result is False


class TestProcessArgs:
    """Test argument processing function."""

    def test_process_args_defaults(self):
        """Test argument processing with defaults."""
        with patch("sys.argv", ["prog"]):
            args = process_args()
        
        assert args.agents_dir == "agents"
        assert args.download_all_agents is False
        assert args.download_agent == ""
        assert args.format == "json"
        assert args.log_level == "INFO"
        assert args.prefix == ""
        assert args.suffix == ""

    def test_process_args_custom_values(self):
        """Test argument processing with custom values."""
        with patch("sys.argv", [
            "prog",
            "--agents-dir", "custom_agents",
            "--download-all-agents",
            "--format", "yaml",
            "--log-level", "DEBUG"
        ]):
            args = process_args()
        
        assert args.agents_dir == "custom_agents"
        assert args.download_all_agents is True
        assert args.format == "yaml"
        assert args.log_level == "DEBUG"