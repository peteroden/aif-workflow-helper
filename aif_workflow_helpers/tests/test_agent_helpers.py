"""
Tests for helper functions in upload_download_agents_helpers.py
"""

from unittest.mock import Mock, patch

from aif_workflow_helpers.upload_download_agents_helpers import (
    get_agent_name,
    get_agent_by_name
)


class TestGetAgentName:
    """Test cases for get_agent_name function."""

    def test_get_agent_name_success(self, mock_agent_client, sample_agent):
        """Test successful agent name retrieval."""
        mock_agent_client.get_agent.return_value = sample_agent
        
        result = get_agent_name("agent-123", mock_agent_client)
        
        assert result == "test-agent"
        mock_agent_client.get_agent.assert_called_once_with("agent-123")

    def test_get_agent_name_not_found(self, mock_agent_client):
        """Test agent name retrieval when agent is not found."""
        mock_agent_client.get_agent.return_value = None
        
        result = get_agent_name("nonexistent-agent", mock_agent_client)
        
        assert result is None
        mock_agent_client.get_agent.assert_called_once_with("nonexistent-agent")

    def test_get_agent_name_exception(self, mock_agent_client):
        """Test agent name retrieval when an exception occurs."""
        mock_agent_client.get_agent.side_effect = Exception("API Error")
        
        with patch('builtins.print') as mock_print:
            result = get_agent_name("agent-123", mock_agent_client)
        
        assert result is None
        mock_print.assert_called_once_with("Error getting agent name for ID agent-123: API Error")

    def test_get_agent_name_agent_without_name(self, mock_agent_client):
        """Test agent name retrieval when agent has no name attribute."""
        mock_agent = Mock()
        mock_agent.name = None
        mock_agent_client.get_agent.return_value = mock_agent
        
        result = get_agent_name("agent-123", mock_agent_client)
        
        assert result is None


class TestGetAgentByName:
    """Test cases for get_agent_by_name function."""

    def test_get_agent_by_name_success(self, mock_agent_client, sample_agent):
        """Test successful agent retrieval by name."""
        mock_agent_client.list_agents.return_value = [sample_agent]
        
        result = get_agent_by_name("test-agent", mock_agent_client)
        
        assert result == sample_agent
        mock_agent_client.list_agents.assert_called_once()

    def test_get_agent_by_name_not_found(self, mock_agent_client, sample_agent):
        """Test agent retrieval when agent name is not found."""
        sample_agent.name = "different-agent"
        mock_agent_client.list_agents.return_value = [sample_agent]
        
        result = get_agent_by_name("nonexistent-agent", mock_agent_client)
        
        assert result is None
        mock_agent_client.list_agents.assert_called_once()

    def test_get_agent_by_name_empty_list(self, mock_agent_client):
        """Test agent retrieval when no agents exist."""
        mock_agent_client.list_agents.return_value = []
        
        result = get_agent_by_name("test-agent", mock_agent_client)
        
        assert result is None
        mock_agent_client.list_agents.assert_called_once()

    def test_get_agent_by_name_multiple_agents(self, mock_agent_client):
        """Test agent retrieval with multiple agents in the system."""
        agent1 = Mock()
        agent1.name = "agent-1"
        agent2 = Mock()
        agent2.name = "target-agent"
        agent3 = Mock()
        agent3.name = "agent-3"
        
        mock_agent_client.list_agents.return_value = [agent1, agent2, agent3]
        
        result = get_agent_by_name("target-agent", mock_agent_client)
        
        assert result == agent2
        mock_agent_client.list_agents.assert_called_once()

    def test_get_agent_by_name_exception(self, mock_agent_client):
        """Test agent retrieval when an exception occurs."""
        mock_agent_client.list_agents.side_effect = Exception("API Error")
        
        with patch('builtins.print') as mock_print:
            result = get_agent_by_name("test-agent", mock_agent_client)
        
        assert result is None
        mock_print.assert_called_once_with("Error getting agent by name 'test-agent': API Error")

    def test_get_agent_by_name_case_sensitive(self, mock_agent_client, sample_agent):
        """Test that agent name matching is case sensitive."""
        sample_agent.name = "Test-Agent"
        mock_agent_client.list_agents.return_value = [sample_agent]
        
        # Test exact match
        result = get_agent_by_name("Test-Agent", mock_agent_client)
        assert result == sample_agent
        
        # Test case mismatch
        result = get_agent_by_name("test-agent", mock_agent_client)
        assert result is None