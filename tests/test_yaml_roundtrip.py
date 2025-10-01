"""Tests for YAML format roundtrip consistency."""
import tempfile
from pathlib import Path
from aif_workflow_helper.core.download import save_agent_file
from aif_workflow_helper.core.upload import read_agent_file


class TestYAMLRoundtrip:
    """Test that YAML files maintain consistency through upload/download cycles."""
    
    def test_basic_agent_roundtrip(self):
        """Test basic agent data roundtrips correctly."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "You are a helpful assistant.",
            "description": "Test description",
            "tools": []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            
            # Write (download)
            success = save_agent_file(agent_dict, file_path, format="yaml")
            assert success
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            assert read_dict is not None
            
            # Should match exactly
            assert read_dict == agent_dict
    
    def test_yml_extension_roundtrip(self):
        """Test that .yml extension works correctly."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "You are helpful."
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yml"
            
            # Write (download)
            success = save_agent_file(agent_dict, file_path, format="yaml")
            assert success
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            assert read_dict is not None
            
            # Should match exactly
            assert read_dict == agent_dict
    
    def test_multiline_strings_roundtrip(self):
        """Test that multiline strings are preserved."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "You are a helpful assistant.\n\nProvide clear responses.\nBe concise.",
            "description": "This is a test description\nwith multiple lines\n\nand blank lines"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            
            # Write (download)
            save_agent_file(agent_dict, file_path, format="yaml")
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            
            # Multiline strings should be preserved
            assert read_dict == agent_dict
            assert "\n\n" in read_dict["instructions"]
            assert "\n\n" in read_dict["description"]
    
    def test_agent_with_tools_roundtrip(self):
        """Test agent with tools roundtrips correctly."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "You are helpful.",
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get current weather",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string"}
                            },
                            "required": ["location"]
                        }
                    }
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            
            # Write (download)
            save_agent_file(agent_dict, file_path, format="yaml")
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            
            # Should match exactly including nested tool structure
            assert read_dict == agent_dict
            assert len(read_dict["tools"]) == 1
            assert read_dict["tools"][0]["type"] == "function"
            assert read_dict["tools"][0]["function"]["name"] == "get_weather"
    
    def test_agent_with_tool_resources_roundtrip(self):
        """Test agent with tool_resources roundtrips correctly."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "You are helpful.",
            "tools": [{"type": "file_search"}],
            "tool_resources": {
                "file_search": {
                    "vector_store_ids": ["vs_123", "vs_456"]
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            
            # Write (download)
            save_agent_file(agent_dict, file_path, format="yaml")
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            
            # Should match exactly including tool_resources
            assert read_dict == agent_dict
            assert "tool_resources" in read_dict
            assert read_dict["tool_resources"]["file_search"]["vector_store_ids"] == ["vs_123", "vs_456"]
    
    def test_multiple_roundtrips_consistent(self):
        """Test that multiple roundtrips produce identical results."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "description": "Test description",
            "instructions": "You are a helpful assistant.\n\nProvide clear responses.",
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "search",
                        "description": "Search for information"
                    }
                }
            ],
            "metadata": {
                "version": "1.0",
                "author": "test"
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            
            # First roundtrip
            save_agent_file(agent_dict, file_path, format="yaml")
            read_dict1 = read_agent_file(str(file_path))
            
            # Second roundtrip (using the read dict)
            save_agent_file(read_dict1, file_path, format="yaml")
            read_dict2 = read_agent_file(str(file_path))
            
            # Third roundtrip
            save_agent_file(read_dict2, file_path, format="yaml")
            read_dict3 = read_agent_file(str(file_path))
            
            # All should be identical
            assert read_dict1 == read_dict2
            assert read_dict2 == read_dict3
            assert read_dict1 == agent_dict
    
    def test_unicode_characters_roundtrip(self):
        """Test that unicode characters are preserved."""
        agent_dict = {
            "name": "test-agent-émoji-🤖",
            "model": "gpt-4",
            "instructions": "You are helpful. 你好 мир 🌍",
            "description": "Test with émojis 🎉 and unicode ñ ü ö"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            
            # Write (download)
            save_agent_file(agent_dict, file_path, format="yaml")
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            
            # Unicode should be preserved
            assert read_dict == agent_dict
            assert "🤖" in read_dict["name"]
            assert "🌍" in read_dict["instructions"]
            assert "🎉" in read_dict["description"]
    
    def test_empty_and_null_values_roundtrip(self):
        """Test that empty strings and None values are preserved."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "",
            "description": None,
            "tools": [],
            "metadata": {}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            
            # Write (download)
            save_agent_file(agent_dict, file_path, format="yaml")
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            
            # Empty values should be preserved
            assert read_dict == agent_dict
            assert read_dict["instructions"] == ""
            assert read_dict["description"] is None
            assert read_dict["tools"] == []
            assert read_dict["metadata"] == {}
    
    def test_nested_metadata_roundtrip(self):
        """Test that deeply nested metadata structures are preserved."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "You are helpful.",
            "metadata": {
                "level1": {
                    "level2": {
                        "level3": {
                            "value": "deep",
                            "list": [1, 2, 3],
                            "nested_list": [{"a": 1}, {"b": 2}]
                        }
                    }
                },
                "array": [1, "two", 3.0, True, None]
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            
            # Write (download)
            save_agent_file(agent_dict, file_path, format="yaml")
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            
            # Complex nested structure should be preserved
            assert read_dict == agent_dict
            assert read_dict["metadata"]["level1"]["level2"]["level3"]["value"] == "deep"
            assert read_dict["metadata"]["array"] == [1, "two", 3.0, True, None]
    
    def test_special_yaml_characters_roundtrip(self):
        """Test that strings with special YAML characters are handled correctly."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "Use these symbols: : @ # - * & | > < [ ] { } ! %",
            "description": "Test with colon: value and - dash"
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            
            # Write (download)
            save_agent_file(agent_dict, file_path, format="yaml")
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            
            # Special characters should be preserved
            assert read_dict == agent_dict
            assert ":" in read_dict["instructions"]
            assert "-" in read_dict["instructions"]
    
    def test_boolean_and_numeric_values_roundtrip(self):
        """Test that boolean and numeric values in metadata are preserved with correct types."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "You are helpful.",
            "metadata": {
                "enabled": True,
                "disabled": False,
                "count": 42,
                "ratio": 3.14,
                "negative": -10,
                "zero": 0
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.yaml"
            
            # Write (download)
            save_agent_file(agent_dict, file_path, format="yaml")
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            
            # Types should be preserved
            assert read_dict == agent_dict
            assert read_dict["metadata"]["enabled"] is True
            assert read_dict["metadata"]["disabled"] is False
            assert isinstance(read_dict["metadata"]["count"], int)
            assert isinstance(read_dict["metadata"]["ratio"], float)
