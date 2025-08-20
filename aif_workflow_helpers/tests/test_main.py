"""
Tests for the main function in upload_download_agents_helpers.py
"""

import os
from unittest.mock import Mock, patch

from aif_workflow_helpers.upload_download_agents_helpers import main


class TestMain:
    """Test cases for main function."""

    def test_main_missing_environment_variables(self, capsys):
        """Test main function when environment variables are not set."""
        with patch.dict(os.environ, {}, clear=True):
            main()
        
        captured = capsys.readouterr()
        assert "❌ Please set AZURE_TENANT_ID and AIF_ENDPOINT environment variables" in captured.out
        assert "export AZURE_TENANT_ID='your-tenant-id'" in captured.out
        assert "export AIF_ENDPOINT='your-ai-foundry-endpoint'" in captured.out

    def test_main_partial_environment_variables(self, capsys):
        """Test main function when only some environment variables are set."""
        with patch.dict(os.environ, {"AZURE_TENANT_ID": "test-tenant"}, clear=True):
            main()
        
        captured = capsys.readouterr()
        assert "❌ Please set AZURE_TENANT_ID and AIF_ENDPOINT environment variables" in captured.out

    @patch('aif_workflow_helpers.upload_download_agents_helpers.create_or_update_agents')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.read_agent_files')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.download_agents')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.AgentsClient')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.DefaultAzureCredential')
    def test_main_successful_execution(
        self,
        mock_credential,
        mock_agents_client_class,
        mock_download_agents,
        mock_read_agent_files,
        mock_create_or_update_agents,
        mock_environment_variables,
        capsys
    ):
        """Test successful execution of main function."""
        # Setup mocks
        mock_credential_instance = Mock()
        mock_credential.return_value = mock_credential_instance
        
        mock_client = Mock()
        mock_agents_client_class.return_value = mock_client
        
        # Mock agent list for connection test
        mock_agents = [Mock(), Mock()]
        mock_client.list_agents.return_value = mock_agents
        
        # Mock agent files
        mock_agents_data = {
            "agent-1": {"name": "agent-1"},
            "agent-2": {"name": "agent-2"}
        }
        mock_read_agent_files.return_value = mock_agents_data
        
        main()
        
        captured = capsys.readouterr()
        
        # Verify connection test
        assert "🔌 Testing connection..." in captured.out
        assert "✅ Connected! Found 2 existing agents" in captured.out
        
        # Verify download phase
        assert "📥 Downloading agents..." in captured.out
        mock_download_agents.assert_called_once_with(mock_client)
        
        # Verify reading phase
        assert "📂 Reading agent files..." in captured.out
        assert "Found 2 agents" in captured.out
        mock_read_agent_files.assert_called_once()
        
        # Verify creation phase
        assert "🚀 Creating/updating agents..." in captured.out
        mock_create_or_update_agents.assert_called_once_with(mock_agents_data, mock_client)
        
        # Verify credential creation
        mock_credential.assert_called_once_with(
            exclude_interactive_browser_credential=False,
            interactive_tenant_id="test-tenant-id"
        )
        
        # Verify client creation
        mock_agents_client_class.assert_called_once_with(
            credential=mock_credential_instance,
            endpoint="https://test-endpoint.services.ai.azure.com/api/projects/test-project"
        )

    @patch('aif_workflow_helpers.upload_download_agents_helpers.read_agent_files')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.download_agents')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.AgentsClient')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.DefaultAzureCredential')
    def test_main_no_agent_files(
        self,
        mock_credential,
        mock_agents_client_class,
        mock_download_agents,
        mock_read_agent_files,
        mock_environment_variables,
        capsys
    ):
        """Test main function when no agent files are found."""
        # Setup mocks
        mock_client = Mock()
        mock_agents_client_class.return_value = mock_client
        mock_client.list_agents.return_value = []
        mock_read_agent_files.return_value = {}
        
        main()
        
        captured = capsys.readouterr()
        
        assert "Found 0 agents" in captured.out
        assert "No agent files found to process" in captured.out

    @patch('aif_workflow_helpers.upload_download_agents_helpers.AgentsClient')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.DefaultAzureCredential')
    def test_main_connection_error(
        self,
        mock_credential,
        mock_agents_client_class,
        mock_environment_variables,
        capsys
    ):
        """Test main function when connection to Azure fails."""
        mock_client = Mock()
        mock_agents_client_class.return_value = mock_client
        mock_client.list_agents.side_effect = Exception("Connection failed")
        
        main()
        
        captured = capsys.readouterr()
        
        assert "🔌 Testing connection..." in captured.out
        assert "❌ Error: Connection failed" in captured.out

    @patch('aif_workflow_helpers.upload_download_agents_helpers.create_or_update_agents')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.read_agent_files')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.download_agents')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.AgentsClient')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.DefaultAzureCredential')
    def test_main_download_error(
        self,
        mock_credential,
        mock_agents_client_class,
        mock_download_agents,
        mock_read_agent_files,
        mock_create_or_update_agents,
        mock_environment_variables,
        capsys
    ):
        """Test main function when download fails."""
        mock_client = Mock()
        mock_agents_client_class.return_value = mock_client
        mock_client.list_agents.return_value = []
        mock_download_agents.side_effect = Exception("Download failed")
        
        main()
        
        captured = capsys.readouterr()
        
        assert "❌ Error: Download failed" in captured.out

    @patch('aif_workflow_helpers.upload_download_agents_helpers.create_or_update_agents')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.read_agent_files')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.download_agents')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.AgentsClient')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.DefaultAzureCredential')
    def test_main_read_files_error(
        self,
        mock_credential,
        mock_agents_client_class,
        mock_download_agents,
        mock_read_agent_files,
        mock_create_or_update_agents,
        mock_environment_variables,
        capsys
    ):
        """Test main function when reading agent files fails."""
        mock_client = Mock()
        mock_agents_client_class.return_value = mock_client
        mock_client.list_agents.return_value = []
        mock_read_agent_files.side_effect = Exception("Read failed")
        
        main()
        
        captured = capsys.readouterr()
        
        assert "❌ Error: Read failed" in captured.out

    @patch('aif_workflow_helpers.upload_download_agents_helpers.create_or_update_agents')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.read_agent_files')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.download_agents')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.AgentsClient')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.DefaultAzureCredential')
    def test_main_create_agents_error(
        self,
        mock_credential,
        mock_agents_client_class,
        mock_download_agents,
        mock_read_agent_files,
        mock_create_or_update_agents,
        mock_environment_variables,
        capsys
    ):
        """Test main function when creating/updating agents fails."""
        mock_client = Mock()
        mock_agents_client_class.return_value = mock_client
        mock_client.list_agents.return_value = []
        mock_read_agent_files.return_value = {"agent-1": {"name": "agent-1"}}
        mock_create_or_update_agents.side_effect = Exception("Create failed")
        
        main()
        
        captured = capsys.readouterr()
        
        assert "❌ Error: Create failed" in captured.out

    @patch('aif_workflow_helpers.upload_download_agents_helpers.AgentsClient')
    @patch('aif_workflow_helpers.upload_download_agents_helpers.DefaultAzureCredential')
    def test_main_environment_variable_handling(
        self,
        mock_credential,
        mock_agents_client_class,
        capsys
    ):
        """Test main function with various environment variable scenarios."""
        # Test with default values
        with patch.dict(os.environ, {
            "AZURE_TENANT_ID": "your-tenant-id-here",
            "AIF_ENDPOINT": "https://your-endpoint-here.services.ai.azure.com/api/projects/your-project"
        }, clear=True):
            main()
        
        captured = capsys.readouterr()
        assert "❌ Please set AZURE_TENANT_ID and AIF_ENDPOINT environment variables" in captured.out
        
        # Test with one default and one valid
        with patch.dict(os.environ, {
            "AZURE_TENANT_ID": "valid-tenant",
            "AIF_ENDPOINT": "https://your-endpoint-here.services.ai.azure.com/api/projects/your-project"
        }, clear=True):
            main()
        
        captured = capsys.readouterr()
        assert "❌ Please set AZURE_TENANT_ID and AIF_ENDPOINT environment variables" in captured.out