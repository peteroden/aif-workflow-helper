"""
Tests for dependency management functions in upload_download_agents_helpers.py
"""

from unittest.mock import patch

from aif_workflow_helpers.upload_download_agents_helpers import (
    extract_dependencies,
    dependency_sort
)


class TestExtractDependencies:
    """Test cases for extract_dependencies function."""

    def test_extract_dependencies_no_dependencies(self):
        """Test extraction when no dependencies exist."""
        agents_data = {
            "agent-a": {
                "name": "agent-a",
                "tools": []
            },
            "agent-b": {
                "name": "agent-b",
                "tools": [
                    {
                        "type": "other_tool",
                        "config": {"setting": "value"}
                    }
                ]
            }
        }
        
        with patch('builtins.print'):
            result = extract_dependencies(agents_data)
        
        assert len(result) == 0

    def test_extract_dependencies_simple(self):
        """Test extraction of simple dependencies."""
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
        
        with patch('builtins.print') as mock_print:
            result = extract_dependencies(agents_data)
        
        assert "agent-b" in result
        assert "agent-a" in result["agent-b"]
        mock_print.assert_called_with("  agent-b depends on agent-a")

    def test_extract_dependencies_multiple_per_agent(self):
        """Test extraction when agent has multiple dependencies."""
        agents_data = {
            "agent-c": {
                "name": "agent-c",
                "tools": [
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "agent-a"
                        }
                    },
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "agent-b"
                        }
                    }
                ]
            }
        }
        
        with patch('builtins.print'):
            result = extract_dependencies(agents_data)
        
        assert "agent-c" in result
        assert "agent-a" in result["agent-c"]
        assert "agent-b" in result["agent-c"]
        assert len(result["agent-c"]) == 2

    def test_extract_dependencies_unknown_agent(self):
        """Test extraction when dependency name is 'Unknown Agent'."""
        agents_data = {
            "agent-a": {
                "name": "agent-a",
                "tools": [
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "Unknown Agent"
                        }
                    }
                ]
            }
        }
        
        with patch('builtins.print'):
            result = extract_dependencies(agents_data)
        
        assert len(result) == 0

    def test_extract_dependencies_missing_name_from_id(self):
        """Test extraction when name_from_id is missing."""
        agents_data = {
            "agent-a": {
                "name": "agent-a",
                "tools": [
                    {
                        "type": "connected_agent",
                        "connected_agent": {}
                    }
                ]
            }
        }
        
        with patch('builtins.print'):
            result = extract_dependencies(agents_data)
        
        assert len(result) == 0

    def test_extract_dependencies_mixed_tools(self):
        """Test extraction with mixed tool types."""
        agents_data = {
            "agent-a": {
                "name": "agent-a",
                "tools": [
                    {
                        "type": "other_tool",
                        "config": {"setting": "value"}
                    },
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "agent-b"
                        }
                    },
                    {
                        "type": "another_tool",
                        "config": {"another": "setting"}
                    }
                ]
            }
        }
        
        with patch('builtins.print'):
            result = extract_dependencies(agents_data)
        
        assert "agent-a" in result
        assert "agent-b" in result["agent-a"]
        assert len(result["agent-a"]) == 1


class TestDependencySort:
    """Test cases for dependency_sort function."""

    def test_dependency_sort_no_dependencies(self):
        """Test sorting when no dependencies exist."""
        agents_data = {
            "agent-a": {"name": "agent-a", "tools": []},
            "agent-b": {"name": "agent-b", "tools": []},
            "agent-c": {"name": "agent-c", "tools": []}
        }
        
        with patch('builtins.print'):
            result = dependency_sort(agents_data)
        
        # All agents should be included
        assert len(result) == 3
        assert set(result) == {"agent-a", "agent-b", "agent-c"}

    def test_dependency_sort_linear_chain(self, agents_data_with_dependencies):
        """Test sorting with linear dependency chain."""
        with patch('builtins.print'):
            result = dependency_sort(agents_data_with_dependencies)
        
        # Should be sorted in dependency order: a -> b -> c
        assert result == ["agent-a", "agent-b", "agent-c"]

    def test_dependency_sort_complex_dependencies(self):
        """Test sorting with complex dependency graph."""
        agents_data = {
            "agent-a": {
                "name": "agent-a",
                "tools": []
            },
            "agent-b": {
                "name": "agent-b",
                "tools": []
            },
            "agent-c": {
                "name": "agent-c",
                "tools": [
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "agent-a"
                        }
                    },
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "agent-b"
                        }
                    }
                ]
            },
            "agent-d": {
                "name": "agent-d",
                "tools": [
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "agent-c"
                        }
                    }
                ]
            }
        }
        
        with patch('builtins.print'):
            result = dependency_sort(agents_data)
        
        # Verify dependency constraints are satisfied
        a_index = result.index("agent-a")
        b_index = result.index("agent-b")
        c_index = result.index("agent-c")
        d_index = result.index("agent-d")
        
        assert a_index < c_index  # a before c
        assert b_index < c_index  # b before c
        assert c_index < d_index  # c before d

    def test_dependency_sort_circular_dependencies(self):
        """Test sorting with circular dependencies."""
        agents_data = {
            "agent-a": {
                "name": "agent-a",
                "tools": [
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "agent-b"
                        }
                    }
                ]
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
        
        with patch('builtins.print') as mock_print:
            result = dependency_sort(agents_data)
        
        # Should handle circular dependencies and include all agents
        assert len(result) == 2
        assert set(result) == {"agent-a", "agent-b"}
        
        # Should print warning about circular dependencies
        mock_print.assert_any_call("Warning: Circular dependencies detected for: {'agent-a', 'agent-b'}")

    def test_dependency_sort_self_dependency(self):
        """Test sorting when agent depends on itself."""
        agents_data = {
            "agent-a": {
                "name": "agent-a",
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
        
        with patch('builtins.print'):
            result = dependency_sort(agents_data)
        
        # Should handle self-dependency gracefully
        assert result == ["agent-a"]

    def test_dependency_sort_independent_groups(self):
        """Test sorting with independent groups of agents."""
        agents_data = {
            "group1-a": {"name": "group1-a", "tools": []},
            "group1-b": {
                "name": "group1-b",
                "tools": [
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "group1-a"
                        }
                    }
                ]
            },
            "group2-a": {"name": "group2-a", "tools": []},
            "group2-b": {
                "name": "group2-b",
                "tools": [
                    {
                        "type": "connected_agent",
                        "connected_agent": {
                            "name_from_id": "group2-a"
                        }
                    }
                ]
            }
        }
        
        with patch('builtins.print'):
            result = dependency_sort(agents_data)
        
        # All agents should be included
        assert len(result) == 4
        assert set(result) == {"group1-a", "group1-b", "group2-a", "group2-b"}
        
        # Dependency constraints within each group should be satisfied
        g1a_index = result.index("group1-a")
        g1b_index = result.index("group1-b")
        g2a_index = result.index("group2-a")
        g2b_index = result.index("group2-b")
        
        assert g1a_index < g1b_index
        assert g2a_index < g2b_index