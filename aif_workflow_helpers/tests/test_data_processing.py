"""
Tests for data processing functions in upload_download_agents_helpers.py
"""

import json
import tempfile
import os
from unittest.mock import Mock, patch, mock_open

from aif_workflow_helpers.upload_download_agents_helpers import (
    generalize_agent_dict,
    read_agent_files,
    download_agents,
    download_agent
)


class TestGeneralizeAgentDict:
    """Test cases for generalize_agent_dict function."""

    def test_generalize_simple_dict(self, mock_agent_client):
        """Test generalization of simple dictionary without nested structures."""
        data = {
            "id": "agent-123",
            "name": "test-agent",
            "description": "Test description",
            "created_at": "2023-01-01T00:00:00Z",
            "model": "gpt-4"
        }
        
        result = generalize_agent_dict(data, mock_agent_client)
        
        expected = {
            "name": "test-agent",
            "description": "Test description",
            "model": "gpt-4"
        }
        assert result == expected

    def test_generalize_connected_agent_dict(self, mock_agent_client):
        """Test generalization of dictionary with connected_agent type."""
        mock_agent_client.get_agent.return_value = Mock(name="child-agent")
        
        data = {
            "type": "connected_agent",
            "connected_agent": {
                "id": "child-123",
                "name": "child-agent",
                "created_at": "2023-01-01T00:00:00Z"
            }
        }
        
        result = generalize_agent_dict(data, mock_agent_client)
        
        expected = {
            "type": "connected_agent",
            "connected_agent": {
                "name": "child-agent",
                "name_from_id": "child-agent"
            }
        }
        assert result == expected
        mock_agent_client.get_agent.assert_called_once_with("child-123")

    def test_generalize_connected_agent_unknown(self, mock_agent_client):
        """Test generalization when connected agent name cannot be resolved."""
        mock_agent_client.get_agent.return_value = None
        
        data = {
            "type": "connected_agent",
            "connected_agent": {
                "id": "unknown-123",
                "created_at": "2023-01-01T00:00:00Z"
            }
        }
        
        result = generalize_agent_dict(data, mock_agent_client)
        
        expected = {
            "type": "connected_agent",
            "connected_agent": {
                "name_from_id": "Unknown Agent"
            }
        }
        assert result == expected

    def test_generalize_nested_list(self, mock_agent_client):
        """Test generalization of nested list structures."""
        data = [
            {
                "id": "item-1",
                "name": "Item 1",
                "created_at": "2023-01-01T00:00:00Z"
            },
            {
                "id": "item-2",
                "name": "Item 2",
                "created_at": "2023-01-01T00:00:00Z"
            }
        ]
        
        result = generalize_agent_dict(data, mock_agent_client)
        
        expected = [
            {"name": "Item 1"},
            {"name": "Item 2"}
        ]
        assert result == expected

    def test_generalize_primitive_values(self, mock_agent_client):
        """Test that primitive values are returned as-is."""
        assert generalize_agent_dict("string", mock_agent_client) == "string"
        assert generalize_agent_dict(123, mock_agent_client) == 123
        assert generalize_agent_dict(True, mock_agent_client) is True
        assert generalize_agent_dict(None, mock_agent_client) is None

    def test_generalize_complex_nested_structure(self, mock_agent_client):
        """Test generalization of complex nested structures."""
        mock_agent_client.get_agent.return_value = Mock(name="dependency-agent")
        
        data = {
            "id": "main-agent",
            "name": "Main Agent",
            "tools": [
                {
                    "type": "connected_agent",
                    "connected_agent": {
                        "id": "dep-123",
                        "name": "dependency",
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                },
                {
                    "type": "other_tool",
                    "config": {
                        "id": "config-123",
                        "setting": "value",
                        "created_at": "2023-01-01T00:00:00Z"
                    }
                }
            ],
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        result = generalize_agent_dict(data, mock_agent_client)
        
        expected = {
            "name": "Main Agent",
            "tools": [
                {
                    "type": "connected_agent",
                    "connected_agent": {
                        "name": "dependency",
                        "name_from_id": "dependency-agent"
                    }
                },
                {
                    "type": "other_tool",
                    "config": {
                        "setting": "value"
                    }
                }
            ]
        }
        assert result == expected


class TestReadAgentFiles:
    """Test cases for read_agent_files function."""

    def test_read_agent_files_success(self):
        """Test successful reading of agent JSON files."""
        agent_data = {
            "name": "test-agent",
            "description": "Test agent"
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test JSON file
            agent_file = os.path.join(temp_dir, "test-agent.json")
            with open(agent_file, 'w') as f:
                json.dump(agent_data, f)
            
            with patch('builtins.print') as mock_print:
                result = read_agent_files(temp_dir)
            
            assert "test-agent" in result
            assert result["test-agent"] == agent_data
            mock_print.assert_called_with("Loaded agent: test-agent")

    def test_read_agent_files_no_files(self):
        """Test reading when no JSON files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = read_agent_files(temp_dir)
            assert result == {}

    def test_read_agent_files_no_name(self):
        """Test reading agent file without name field."""
        agent_data = {
            "description": "Agent without name"
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            agent_file = os.path.join(temp_dir, "unnamed-agent.json")
            with open(agent_file, 'w') as f:
                json.dump(agent_data, f)
            
            result = read_agent_files(temp_dir)
            assert result == {}

    def test_read_agent_files_multiple_files(self):
        """Test reading multiple agent files."""
        agent1_data = {"name": "agent-1", "description": "First agent"}
        agent2_data = {"name": "agent-2", "description": "Second agent"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test files
            with open(os.path.join(temp_dir, "agent-1.json"), 'w') as f:
                json.dump(agent1_data, f)
            with open(os.path.join(temp_dir, "agent-2.json"), 'w') as f:
                json.dump(agent2_data, f)
            
            result = read_agent_files(temp_dir)
            
            assert len(result) == 2
            assert result["agent-1"] == agent1_data
            assert result["agent-2"] == agent2_data

    def test_read_agent_files_invalid_json(self):
        """Test handling of invalid JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid JSON file
            invalid_file = os.path.join(temp_dir, "invalid.json")
            with open(invalid_file, 'w') as f:
                f.write("invalid json content")
            
            # Should not raise exception but continue processing
            result = read_agent_files(temp_dir)
            assert result == {}


class TestDownloadAgents:
    """Test cases for download_agents function."""

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_download_agents_success(self, mock_json_dump, mock_file, mock_agent_client, sample_agent):
        """Test successful downloading of agents."""
        mock_agent_client.list_agents.return_value = [sample_agent]
        
        with patch('builtins.print') as mock_print:
            download_agents(mock_agent_client)
        
        mock_file.assert_called_once_with("test-agent.json", 'w')
        mock_json_dump.assert_called_once()
        mock_print.assert_any_call("Saved agent 'test-agent' to test-agent.json")

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_download_agents_empty_list(self, mock_json_dump, mock_file, mock_agent_client):
        """Test downloading when no agents exist."""
        mock_agent_client.list_agents.return_value = []
        
        download_agents(mock_agent_client)
        
        mock_file.assert_not_called()
        mock_json_dump.assert_not_called()

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_download_agents_multiple(self, mock_json_dump, mock_file, mock_agent_client):
        """Test downloading multiple agents."""
        agent1 = Mock()
        agent1.name = "agent-1"
        agent1.as_dict.return_value = {"name": "agent-1", "id": "1", "created_at": "2023-01-01"}
        
        agent2 = Mock()
        agent2.name = "agent-2"
        agent2.as_dict.return_value = {"name": "agent-2", "id": "2", "created_at": "2023-01-01"}
        
        mock_agent_client.list_agents.return_value = [agent1, agent2]
        
        download_agents(mock_agent_client)
        
        assert mock_file.call_count == 2
        assert mock_json_dump.call_count == 2


class TestDownloadAgent:
    """Test cases for download_agent function."""

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_download_agent_success(self, mock_json_dump, mock_file, mock_agent_client, sample_agent):
        """Test successful downloading of specific agent."""
        mock_agent_client.list_agents.return_value = [sample_agent]
        
        with patch('builtins.print') as mock_print:
            download_agent("test-agent", mock_agent_client)
        
        mock_file.assert_called_once_with("test-agent.json", 'w')
        mock_json_dump.assert_called_once()
        mock_print.assert_any_call("Saved agent 'test-agent' to test-agent.json")

    def test_download_agent_not_found(self, mock_agent_client, sample_agent):
        """Test downloading non-existent agent."""
        sample_agent.name = "different-agent"
        mock_agent_client.list_agents.return_value = [sample_agent]
        
        with patch('builtins.print') as mock_print:
            download_agent("nonexistent-agent", mock_agent_client)
        
        mock_print.assert_called_with("Agent with name nonexistent-agent not found.")