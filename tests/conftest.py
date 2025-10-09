

import pytest
from unittest.mock import Mock
from azure.ai.agents import models
from .test_agent_client_mock import AgentsClientMock

@pytest.fixture
def agents_client_mock():
    """Fixture providing a fresh AgentsClientMock for each test."""
    return AgentsClientMock()


@pytest.fixture
def mock_agent_client():
    """Create a mock AgentsClient for testing."""
    client = Mock()
    client.list_agents = Mock()
    client.get_agent = Mock()
    client.create_agent = Mock()
    client.update_agent = Mock()
    return client


@pytest.fixture
def sample_agent():
    """Create a sample agent object for testing."""
    agent = Mock(spec=models.Agent)
    agent.id = "agent-123"
    agent.name = "test-agent"
    agent.description = "Test agent description"
    agent.instructions = "Test instructions"
    agent.model = "gpt-4"
    agent.tools = []
    agent.temperature = 1.0
    agent.top_p = 1.0
    agent.metadata = {}
    agent.as_dict.return_value = {
        "id": "agent-123",
        "name": "test-agent",
        "description": "Test agent description",
        "instructions": "Test instructions",
        "model": "gpt-4",
        "tools": [],
        "temperature": 1.0,
        "top_p": 1.0,
        "metadata": {},
        "created_at": "2023-01-01T00:00:00Z"
    }
    return agent


@pytest.fixture
def sample_agent_with_connected_agent():
    """Create a sample agent with connected agent tool for testing."""
    agent = Mock(spec=models.Agent)
    agent.id = "parent-agent-123"
    agent.name = "parent-agent"
    agent.description = "Parent agent with connected agent"
    agent.instructions = "Parent agent instructions"
    agent.model = "gpt-4"
    agent.tools = [
        {
            "type": "connected_agent",
            "connected_agent": {
                "id": "child-agent-456",
                "name": "child-agent"
            }
        }
    ]
    agent.temperature = 1.0
    agent.top_p = 1.0
    agent.metadata = {}
    agent.as_dict.return_value = {
        "id": "parent-agent-123",
        "name": "parent-agent",
        "description": "Parent agent with connected agent",
        "instructions": "Parent agent instructions",
        "model": "gpt-4",
        "tools": [
            {
                "type": "connected_agent",
                "connected_agent": {
                    "id": "child-agent-456",
                    "name": "child-agent"
                }
            }
        ],
        "temperature": 1.0,
        "top_p": 1.0,
        "metadata": {},
        "created_at": "2023-01-01T00:00:00Z"
    }
    return agent


@pytest.fixture
def sample_agent_data():
    """Create sample agent data dictionary for testing."""
    return {
        "name": "test-agent",
        "description": "Test agent description",
        "instructions": "Test instructions",
        "model": "gpt-4",
        "tools": [],
        "temperature": 1.0,
        "top_p": 1.0,
        "metadata": {}
    }


@pytest.fixture
def sample_agent_data_with_dependency():
    """Create sample agent data with connected agent dependency."""
    return {
        "name": "parent-agent",
        "description": "Parent agent with dependency",
        "instructions": "Parent agent instructions",
        "model": "gpt-4",
        "tools": [
            {
                "type": "connected_agent",
                "connected_agent": {
                    "name_from_id": "child-agent"
                }
            }
        ],
        "temperature": 1.0,
        "top_p": 1.0,
        "metadata": {}
    }


@pytest.fixture
def agents_data_with_dependencies():
    """Create sample agents data with complex dependencies for testing."""
    return {
        "agent-a": {
            "name": "agent-a",
            "description": "Agent A (no dependencies)",
            "instructions": "Agent A instructions",
            "model": "gpt-4",
            "tools": [],
            "temperature": 1.0,
            "top_p": 1.0,
            "metadata": {}
        },
        "agent-b": {
            "name": "agent-b",
            "description": "Agent B (depends on A)",
            "instructions": "Agent B instructions",
            "model": "gpt-4",
            "tools": [
                {
                    "type": "connected_agent",
                    "connected_agent": {
                        "name_from_id": "agent-a"
                    }
                }
            ],
            "temperature": 1.0,
            "top_p": 1.0,
            "metadata": {}
        },
        "agent-c": {
            "name": "agent-c",
            "description": "Agent C (depends on B)",
            "instructions": "Agent C instructions",
            "model": "gpt-4",
            "tools": [
                {
                    "type": "connected_agent",
                    "connected_agent": {
                        "name_from_id": "agent-b"
                    }
                }
            ],
            "temperature": 1.0,
            "top_p": 1.0,
            "metadata": {}
        }
    }


@pytest.fixture
def mock_cli_agent_client():
    """Create a unified mock AgentFrameworkAgentsClient for CLI handler testing.
    
    This fixture provides a pre-configured mock client that covers all the
    common CLI handler scenarios. Tests can override specific behaviors
    by modifying the returned mock or its methods.
    """
    client = Mock()
    
    # Mock common methods used by CLI handlers
    client.list_agents = Mock(return_value=[])
    client.get_agent = Mock(return_value=None)
    client.create_agent = Mock()
    client.update_agent = Mock()
    client.delete_agent = Mock()
    client.close = Mock()
    
    # Create sample agents for testing scenarios
    sample_agent = Mock()
    sample_agent.id = "asst_test123"
    sample_agent.name = "test-agent"
    
    sample_agent_with_prefix = Mock()
    sample_agent_with_prefix.id = "asst_test456"
    sample_agent_with_prefix.name = "dev-test-agent-v1"
    
    # Configure client to return sample data when needed
    client._sample_agent = sample_agent
    client._sample_agent_with_prefix = sample_agent_with_prefix
    
    # Add helper method to easily configure list_agents response
    def set_agents_list(agents):
        """Helper to set the list of agents returned by list_agents()."""
        client.list_agents.return_value = agents
    
    client.set_agents_list = set_agents_list
    
    return client


@pytest.fixture
def mock_environment_variables(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("AZURE_TENANT_ID", "test-tenant-id")
    monkeypatch.setenv("PROJECT_ENDPOINT", "https://test-endpoint.services.ai.azure.com/api/projects/test-project")