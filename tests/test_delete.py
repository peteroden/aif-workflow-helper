"""
Tests for the delete module functionality.
"""

import pytest
from unittest.mock import Mock, patch, call
from azure.ai.agents.models import Agent

from aif_workflow_helper.core.delete import (
    delete_agent_by_name,
    delete_agents,
    get_matching_agents
)


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = Mock(spec=Agent)
    agent.id = "agent-123"
    agent.name = "test-agent"
    return agent


@pytest.fixture
def mock_agent_with_prefix():
    """Create a mock agent with prefix for testing."""
    agent = Mock(spec=Agent)
    agent.id = "agent-456"
    agent.name = "dev-test-agent"
    return agent


@pytest.fixture
def mock_agent_with_prefix_suffix():
    """Create a mock agent with prefix and suffix for testing."""
    agent = Mock(spec=Agent)
    agent.id = "agent-789"
    agent.name = "dev-test-agent-v1"
    return agent


class TestDeleteAgentByName:
    """Tests for the delete_agent_by_name function."""
    
    @pytest.mark.asyncio
    async def test_delete_agent_by_name_success(self, mock_agent_client, mock_agent):
        """Test successful deletion."""
        with patch('aif_workflow_helper.core.delete.get_agent_by_name', return_value=mock_agent):
            result = await delete_agent_by_name(
                agent_name="test-agent",
                agent_client=mock_agent_client
            )
            assert result is True
            mock_agent_client.delete_agent.assert_called_once_with(mock_agent.id)
    
    @pytest.mark.asyncio
    async def test_delete_agent_by_name_not_found(self, mock_agent_client):
        """Test deletion when agent is not found."""
        with patch('aif_workflow_helper.core.delete.get_agent_by_name', return_value=None):
            result = await delete_agent_by_name(
                agent_name="missing-agent",
                agent_client=mock_agent_client
            )
            assert result is False
            mock_agent_client.delete_agent.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_agent_by_name_with_prefix(self, mock_agent_client, mock_agent_with_prefix):
        """Test deletion with prefix."""
        with patch('aif_workflow_helper.core.delete.get_agent_by_name', return_value=mock_agent_with_prefix):
            result = await delete_agent_by_name(
                agent_name="test-agent",
                agent_client=mock_agent_client,
                prefix="dev-"
            )
            assert result is True
            mock_agent_client.delete_agent.assert_called_once_with(mock_agent_with_prefix.id)
    
    @pytest.mark.asyncio
    async def test_delete_agent_by_name_with_suffix(self, mock_agent_client, mock_agent):
        """Test deletion with suffix."""
        mock_agent.name = "test-agent-v1"
        with patch('aif_workflow_helper.core.delete.get_agent_by_name', return_value=mock_agent):
            result = await delete_agent_by_name(
                agent_name="test-agent",
                agent_client=mock_agent_client,
                suffix="-v1"
            )
            assert result is True
            mock_agent_client.delete_agent.assert_called_once_with(mock_agent.id)
    
    @pytest.mark.asyncio
    async def test_delete_agent_by_name_with_prefix_and_suffix(self, mock_agent_client, mock_agent_with_prefix_suffix):
        """Test deletion with both prefix and suffix."""
        with patch('aif_workflow_helper.core.delete.get_agent_by_name', return_value=mock_agent_with_prefix_suffix):
            result = await delete_agent_by_name(
                agent_name="test-agent",
                agent_client=mock_agent_client,
                prefix="dev-",
                suffix="-v1"
            )
            assert result is True
            mock_agent_client.delete_agent.assert_called_once_with(mock_agent_with_prefix_suffix.id)
    
    @pytest.mark.asyncio
    async def test_delete_agent_by_name_api_error(self, mock_agent_client, mock_agent):
        """Test handling of API errors during deletion."""
        with patch('aif_workflow_helper.core.delete.get_agent_by_name', return_value=mock_agent):
            mock_agent_client.delete_agent.side_effect = Exception("API Error")
            result = await delete_agent_by_name(
                agent_name="test-agent",
                agent_client=mock_agent_client
            )
            assert result is False


class TestGetMatchingAgents:
    """Tests for the get_matching_agents function."""
    
    @pytest.mark.asyncio
    async def test_get_matching_agents_no_filter(self, mock_agent_client):
        """Test getting all agents when no filter is provided."""
        agents = [
            Mock(id="agent-1", name="agent-1"),
            Mock(id="agent-2", name="agent-2"),
            Mock(id="agent-3", name="agent-3")
        ]
        mock_agent_client.list_agents.return_value = agents
        
        result = await get_matching_agents(agent_client=mock_agent_client)
        
        assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_get_matching_agents_with_prefix(self, mock_agent_client):
        """Test filtering agents by prefix."""
        agent1 = Mock()
        agent1.id = "agent-1"
        agent1.name = "dev-agent-1"
        agent2 = Mock()
        agent2.id = "agent-2"
        agent2.name = "dev-agent-2"
        agent3 = Mock()
        agent3.id = "agent-3"
        agent3.name = "prod-agent-3"
        agents = [agent1, agent2, agent3]
        mock_agent_client.list_agents.return_value = agents
        
        result = await get_matching_agents(
            agent_client=mock_agent_client,
            prefix="dev-"
        )
        
        assert len(result) == 2
        assert all(a.name.startswith("dev-") for a in result)
    
    @pytest.mark.asyncio
    async def test_get_matching_agents_with_suffix(self, mock_agent_client):
        """Test filtering agents by suffix."""
        agent1 = Mock()
        agent1.id = "agent-1"
        agent1.name = "agent-1-v1"
        agent2 = Mock()
        agent2.id = "agent-2"
        agent2.name = "agent-2-v1"
        agent3 = Mock()
        agent3.id = "agent-3"
        agent3.name = "agent-3-v2"
        agents = [agent1, agent2, agent3]
        mock_agent_client.list_agents.return_value = agents
        
        result = await get_matching_agents(
            agent_client=mock_agent_client,
            suffix="-v1"
        )
        
        assert len(result) == 2
        assert all(a.name.endswith("-v1") for a in result)
    
    @pytest.mark.asyncio
    async def test_get_matching_agents_with_prefix_and_suffix(self, mock_agent_client):
        """Test filtering agents by both prefix and suffix."""
        agent1 = Mock()
        agent1.id = "agent-1"
        agent1.name = "dev-agent-1-v1"
        agent2 = Mock()
        agent2.id = "agent-2"
        agent2.name = "dev-agent-2-v1"
        agent3 = Mock()
        agent3.id = "agent-3"
        agent3.name = "dev-agent-3-v2"
        agent4 = Mock()
        agent4.id = "agent-4"
        agent4.name = "prod-agent-4-v1"
        agents = [agent1, agent2, agent3, agent4]
        mock_agent_client.list_agents.return_value = agents
        
        result = await get_matching_agents(
            agent_client=mock_agent_client,
            prefix="dev-",
            suffix="-v1"
        )
        
        assert len(result) == 2
        assert all(a.name.startswith("dev-") and a.name.endswith("-v1") for a in result)
    
    @pytest.mark.asyncio
    async def test_get_matching_agents_no_matches(self, mock_agent_client):
        """Test when no agents match the filter."""
        agent1 = Mock()
        agent1.id = "agent-1"
        agent1.name = "test-agent-1"
        agent2 = Mock()
        agent2.id = "agent-2"
        agent2.name = "test-agent-2"
        agents = [agent1, agent2]
        mock_agent_client.list_agents.return_value = agents
        
        result = await get_matching_agents(
            agent_client=mock_agent_client,
            prefix="nonexistent-"
        )
        
        assert len(result) == 0


class TestDeleteAgents:
    """Tests for the delete_agents function (bulk deletion)."""
    
    @pytest.mark.asyncio
    async def test_delete_agents_success(self, mock_agent_client):
        """Test successful bulk deletion."""
        agents = [
            Mock(id="agent-1", name="test-agent-1"),
            Mock(id="agent-2", name="test-agent-2"),
            Mock(id="agent-3", name="test-agent-3")
        ]
        
        success, count = await delete_agents(agent_client=mock_agent_client, agent_list=agents)
        
        assert success is True
        assert count == 3
        assert mock_agent_client.delete_agent.call_count == 3
        mock_agent_client.delete_agent.assert_has_calls([
            call("agent-1"),
            call("agent-2"),
            call("agent-3")
        ], any_order=True)
    
    @pytest.mark.asyncio
    async def test_delete_agents_empty_list(self, mock_agent_client):
        """Test bulk deletion when agent list is empty."""
        success, count = await delete_agents(agent_client=mock_agent_client, agent_list=[])
        
        assert success is True
        assert count == 0
        mock_agent_client.delete_agent.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_agents_partial_failure(self, mock_agent_client):
        """Test bulk deletion with partial failures."""
        agents = [
            Mock(id="agent-1", name="test-agent-1"),
            Mock(id="agent-2", name="test-agent-2"),
            Mock(id="agent-3", name="test-agent-3")
        ]
        
        # Make the second deletion fail
        def delete_side_effect(agent_id):
            if agent_id == "agent-2":
                raise Exception("API Error")
        
        mock_agent_client.delete_agent.side_effect = delete_side_effect
        
        success, count = await delete_agents(agent_client=mock_agent_client, agent_list=agents)
        
        assert success is False
        assert count == 2  # Two succeeded despite one failure
        assert mock_agent_client.delete_agent.call_count == 3


class TestConfirmDeletion:
    """Tests for the CLI confirmation prompt function."""
    
    def test_confirm_deletion_with_yes(self):
        """Test that 'yes' input returns True."""
        from aif_workflow_helper.cli.main import confirm_deletion
        with patch('builtins.input', return_value='yes'):
            result = confirm_deletion(['agent-1', 'agent-2'])
            assert result is True
    
    def test_confirm_deletion_with_y(self):
        """Test that 'y' input returns True."""
        from aif_workflow_helper.cli.main import confirm_deletion
        with patch('builtins.input', return_value='y'):
            result = confirm_deletion(['agent-1'])
            assert result is True
    
    def test_confirm_deletion_with_no(self):
        """Test that 'no' input returns False."""
        from aif_workflow_helper.cli.main import confirm_deletion
        with patch('builtins.input', return_value='no'):
            result = confirm_deletion(['agent-1'])
            assert result is False
    
    def test_confirm_deletion_with_n(self):
        """Test that 'n' input returns False."""
        from aif_workflow_helper.cli.main import confirm_deletion
        with patch('builtins.input', return_value='n'):
            result = confirm_deletion(['agent-1'])
            assert result is False
    
    def test_confirm_deletion_with_invalid_input(self):
        """Test that invalid input returns False."""
        from aif_workflow_helper.cli.main import confirm_deletion
        with patch('builtins.input', return_value='maybe'):
            result = confirm_deletion(['agent-1'])
            assert result is False
    
    def test_confirm_deletion_with_empty_list(self):
        """Test that empty list returns False."""
        from aif_workflow_helper.cli.main import confirm_deletion
        result = confirm_deletion([])
        assert result is False
    
    def test_confirm_deletion_with_eof_error(self):
        """Test that EOFError returns False."""
        from aif_workflow_helper.cli.main import confirm_deletion
        with patch('builtins.input', side_effect=EOFError):
            result = confirm_deletion(['agent-1'])
            assert result is False
    
    def test_confirm_deletion_with_keyboard_interrupt(self):
        """Test that KeyboardInterrupt returns False."""
        from aif_workflow_helper.cli.main import confirm_deletion
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            result = confirm_deletion(['agent-1'])
            assert result is False
    
    def test_confirm_deletion_case_insensitive(self):
        """Test that confirmation is case-insensitive."""
        from aif_workflow_helper.cli.main import confirm_deletion
        with patch('builtins.input', return_value='YES'):
            result = confirm_deletion(['agent-1'])
            assert result is True
        
        with patch('builtins.input', return_value='Y'):
            result = confirm_deletion(['agent-1'])
            assert result is True
    
    def test_confirm_deletion_with_whitespace(self):
        """Test that whitespace is stripped from input."""
        from aif_workflow_helper.cli.main import confirm_deletion
        with patch('builtins.input', return_value='  yes  '):
            result = confirm_deletion(['agent-1'])
            assert result is True
    
    def test_confirm_deletion_displays_agent_list(self, capsys):
        """Test that agent names are displayed to user."""
        from aif_workflow_helper.cli.main import confirm_deletion
        with patch('builtins.input', return_value='no'):
            confirm_deletion(['agent-1', 'agent-2', 'agent-3'])
            captured = capsys.readouterr()
            assert 'agent-1' in captured.out
            assert 'agent-2' in captured.out
            assert 'agent-3' in captured.out
            assert 'Total: 3 agent(s)' in captured.out
