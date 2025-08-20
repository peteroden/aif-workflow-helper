"""
Tests for agent CRUD operations in upload_download_agents_helpers.py
"""

from unittest.mock import Mock, patch
from azure.ai.agents import models

from aif_workflow_helpers.upload_download_agents_helpers import (
    create_or_update_agent,
    create_or_update_agents
)


class TestCreateOrUpdateAgent:
    """Test cases for create_or_update_agent function."""

    def test_create_new_agent_success(self, mock_agent_client, sample_agent_data):
        """Test successful creation of new agent."""
        mock_agent_client.list_agents.return_value = []
        mock_new_agent = Mock(spec=models.Agent)
        mock_new_agent.id = "new-agent-123"
        mock_new_agent.name = "test-agent"
        mock_agent_client.create_agent.return_value = mock_new_agent
        
        with patch('builtins.print') as mock_print:
            result = create_or_update_agent(sample_agent_data, mock_agent_client)
        
        assert result == mock_new_agent
        mock_agent_client.create_agent.assert_called_once()
        mock_print.assert_any_call("Found 0 existing agents in the system")
        mock_print.assert_any_call("Creating new agent: test-agent")

    def test_update_existing_agent_success(self, mock_agent_client, sample_agent_data, sample_agent):
        """Test successful update of existing agent."""
        mock_agent_client.list_agents.return_value = [sample_agent]
        mock_updated_agent = Mock(spec=models.Agent)
        mock_updated_agent.id = "agent-123"
        mock_updated_agent.name = "test-agent"
        mock_agent_client.update_agent.return_value = mock_updated_agent
        
        with patch('builtins.print') as mock_print:
            result = create_or_update_agent(sample_agent_data, mock_agent_client)
        
        assert result == mock_updated_agent
        mock_agent_client.update_agent.assert_called_once_with(
            agent_id="agent-123",
            name="test-agent",
            description="Test agent description",
            instructions="Test instructions",
            model="gpt-4",
            tools=[],
            temperature=1.0,
            top_p=1.0,
            metadata={}
        )
        mock_print.assert_any_call("Updating existing agent: test-agent")

    def test_create_agent_with_dependency(self, mock_agent_client, sample_agent_data_with_dependency):
        """Test creating agent with connected agent dependency."""
        # Setup existing agents for dependency resolution
        dependency_agent = Mock()
        dependency_agent.name = "child-agent"
        dependency_agent.id = "child-agent-456"
        
        mock_agent_client.list_agents.return_value = [dependency_agent]
        mock_new_agent = Mock(spec=models.Agent)
        mock_agent_client.create_agent.return_value = mock_new_agent
        
        with patch('builtins.print') as mock_print:
            create_or_update_agent(sample_agent_data_with_dependency, mock_agent_client)
        
        # Verify dependency was resolved
        create_call_args = mock_agent_client.create_agent.call_args
        tools = create_call_args.kwargs['tools']
        connected_agent_tool = tools[0]
        
        assert connected_agent_tool['connected_agent']['id'] == "child-agent-456"
        assert 'name_from_id' not in connected_agent_tool['connected_agent']
        mock_print.assert_any_call("  Resolved 'child-agent' to ID: child-agent-456")

    def test_create_agent_unresolved_dependency(self, mock_agent_client, sample_agent_data_with_dependency):
        """Test creating agent with unresolved dependency."""
        mock_agent_client.list_agents.return_value = []  # No existing agents
        mock_new_agent = Mock(spec=models.Agent)
        mock_agent_client.create_agent.return_value = mock_new_agent
        
        with patch('builtins.print') as mock_print:
            create_or_update_agent(sample_agent_data_with_dependency, mock_agent_client)
        
        # Should still create agent but warn about unresolved dependency
        mock_print.assert_any_call("  Warning: Could not resolve agent name 'child-agent' to ID")

    def test_create_agent_with_existing_agents_list(self, mock_agent_client, sample_agent_data, sample_agent):
        """Test creating agent when existing_agents list is provided."""
        existing_agents = [sample_agent]
        mock_updated_agent = Mock(spec=models.Agent)
        mock_agent_client.update_agent.return_value = mock_updated_agent
        
        # Should not call list_agents when existing_agents is provided
        result = create_or_update_agent(sample_agent_data, mock_agent_client, existing_agents)
        
        assert result == mock_updated_agent
        mock_agent_client.list_agents.assert_not_called()

    def test_create_agent_exception_handling(self, mock_agent_client, sample_agent_data):
        """Test exception handling during agent creation."""
        mock_agent_client.list_agents.return_value = []
        mock_agent_client.create_agent.side_effect = Exception("API Error")
        
        with patch('builtins.print') as mock_print:
            result = create_or_update_agent(sample_agent_data, mock_agent_client)
        
        assert result is None
        mock_print.assert_any_call("Error creating/updating agent test-agent: API Error")

    def test_update_agent_exception_handling(self, mock_agent_client, sample_agent_data, sample_agent):
        """Test exception handling during agent update."""
        mock_agent_client.list_agents.return_value = [sample_agent]
        mock_agent_client.update_agent.side_effect = Exception("Update failed")
        
        with patch('builtins.print') as mock_print:
            result = create_or_update_agent(sample_agent_data, mock_agent_client)
        
        assert result is None
        mock_print.assert_any_call("Error creating/updating agent test-agent: Update failed")

    def test_create_agent_minimal_data(self, mock_agent_client):
        """Test creating agent with minimal required data."""
        minimal_data = {"name": "minimal-agent"}
        mock_agent_client.list_agents.return_value = []
        mock_new_agent = Mock(spec=models.Agent)
        mock_agent_client.create_agent.return_value = mock_new_agent
        
        result = create_or_update_agent(minimal_data, mock_agent_client)
        
        assert result == mock_new_agent
        create_call = mock_agent_client.create_agent.call_args
        assert create_call.kwargs['name'] == "minimal-agent"
        assert create_call.kwargs['description'] is None
        assert create_call.kwargs['instructions'] == ""
        assert create_call.kwargs['model'] == "gpt-4"


class TestCreateOrUpdateAgents:
    """Test cases for create_or_update_agents function."""

    def test_create_agents_in_dependency_order(self, mock_agent_client, agents_data_with_dependencies):
        """Test creating multiple agents in dependency order."""
        mock_agent_client.list_agents.return_value = []
        
        # Mock successful agent creation
        created_agents = []
        for i, name in enumerate(["agent-a", "agent-b", "agent-c"]):
            mock_agent = Mock(spec=models.Agent)
            mock_agent.id = f"id-{i+1}"
            mock_agent.name = name
            created_agents.append(mock_agent)
        
        mock_agent_client.create_agent.side_effect = created_agents
        
        with patch('builtins.print') as mock_print:
            create_or_update_agents(agents_data_with_dependencies, mock_agent_client)
        
        # Verify agents were created in correct order
        assert mock_agent_client.create_agent.call_count == 3
        
        # Check the order of creation calls
        create_calls = mock_agent_client.create_agent.call_args_list
        assert create_calls[0].kwargs['name'] == "agent-a"
        assert create_calls[1].kwargs['name'] == "agent-b"
        assert create_calls[2].kwargs['name'] == "agent-c"
        
        mock_print.assert_any_call("Creating/updating agents in dependency order... ['agent-a', 'agent-b', 'agent-c']")

    def test_create_agents_with_existing_agents(self, mock_agent_client, agents_data_with_dependencies):
        """Test creating agents when some already exist."""
        # Mock existing agent
        existing_agent = Mock()
        existing_agent.name = "agent-a"
        existing_agent.id = "existing-agent-a"
        
        mock_agent_client.list_agents.return_value = [existing_agent]
        
        # Mock agent creation/update
        mock_updated_agent = Mock(spec=models.Agent)
        mock_agent_client.update_agent.return_value = mock_updated_agent
        
        mock_new_agents = []
        for name in ["agent-b", "agent-c"]:
            mock_agent = Mock(spec=models.Agent)
            mock_agent.name = name
            mock_new_agents.append(mock_agent)
        
        mock_agent_client.create_agent.side_effect = mock_new_agents
        
        with patch('builtins.print') as mock_print:
            create_or_update_agents(agents_data_with_dependencies, mock_agent_client)
        
        # Should update existing agent and create new ones
        mock_agent_client.update_agent.assert_called_once()
        assert mock_agent_client.create_agent.call_count == 2
        mock_print.assert_any_call("Completed! Processed 3 agents successfully.")

    def test_create_agents_with_failures(self, mock_agent_client, agents_data_with_dependencies):
        """Test handling agent creation failures."""
        mock_agent_client.list_agents.return_value = []
        
        # Mock first agent success, second failure, third success
        mock_success_agent = Mock(spec=models.Agent)
        mock_agent_client.create_agent.side_effect = [
            mock_success_agent,  # agent-a succeeds
            Exception("Creation failed"),  # agent-b fails
            mock_success_agent   # agent-c succeeds
        ]
        
        with patch('builtins.print') as mock_print:
            create_or_update_agents(agents_data_with_dependencies, mock_agent_client)
        
        # Should attempt to create all agents despite failure
        assert mock_agent_client.create_agent.call_count == 3
        mock_print.assert_any_call("✓ Successfully processed agent-a")
        mock_print.assert_any_call("✗ Failed to process agent-b")
        mock_print.assert_any_call("✓ Successfully processed agent-c")
        mock_print.assert_any_call("Completed! Processed 2 agents successfully.")

    def test_create_agents_empty_data(self, mock_agent_client):
        """Test creating agents with empty data."""
        mock_agent_client.list_agents.return_value = []
        
        with patch('builtins.print') as mock_print:
            create_or_update_agents({}, mock_agent_client)
        
        mock_agent_client.create_agent.assert_not_called()
        mock_print.assert_any_call("Completed! Processed 0 agents successfully.")

    def test_create_agents_dependency_resolution(self, mock_agent_client):
        """Test dependency resolution during agent creation."""
        # Create agents data where agent-b depends on agent-a
        agents_data = {
            "agent-a": {
                "name": "agent-a",
                "tools": []
            },
            "agent-b": {
                "name": "agent-b",
                "tools": [
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "agent-a"
                        }
                    }
                ]
            }
        }
        
        mock_agent_client.list_agents.return_value = []
        
        # Mock agent creation - agent-a first, then agent-b
        agent_a = Mock(spec=models.Agent)
        agent_a.name = "agent-a"
        agent_a.id = "agent-a-id"
        
        agent_b = Mock(spec=models.Agent)
        agent_b.name = "agent-b"
        agent_b.id = "agent-b-id"
        
        mock_agent_client.create_agent.side_effect = [agent_a, agent_b]
        
        with patch('builtins.print'):
            create_or_update_agents(agents_data, mock_agent_client)
        
        # Verify agent-b was created with resolved dependency
        create_calls = mock_agent_client.create_agent.call_args_list
        agent_b_call = create_calls[1]
        tools = agent_b_call.kwargs['tools']
        
        # The dependency should be resolved to the actual ID
        connected_agent_tool = tools[0]
        assert connected_agent_tool['connected_agent']['id'] == "agent-a-id"