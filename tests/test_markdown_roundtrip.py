"""Tests for markdown format roundtrip consistency."""
import tempfile
from pathlib import Path
from aif_workflow_helper.core.download import save_agent_file
from aif_workflow_helper.core.upload import read_agent_file


class TestMarkdownRoundtrip:
    """Test that markdown files maintain consistency through upload/download cycles."""
    
    def test_instructions_trailing_newline_preserved(self):
        """Test that trailing newlines in instructions are preserved."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "You are a helpful assistant.\n\nProvide clear responses.\n",
            "tools": []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            
            # Write (download)
            success = save_agent_file(agent_dict, file_path, format="md")
            assert success
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            assert read_dict is not None
            
            # Instructions should match exactly (trailing newline preserved)
            assert read_dict["instructions"] == agent_dict["instructions"]
            
            # Other fields should match
            assert read_dict["name"] == agent_dict["name"]
            assert read_dict["model"] == agent_dict["model"]
    
    def test_description_trailing_newline_preserved(self):
        """Test that trailing newlines in description are preserved."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "description": "Test description\n",
            "instructions": "You are helpful.",
            "tools": []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            
            # Write (download)
            success = save_agent_file(agent_dict, file_path, format="md")
            assert success
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            assert read_dict is not None
            
            # Description should match exactly (trailing newline preserved)
            assert read_dict["description"] == agent_dict["description"]
    
    def test_multiple_roundtrips_consistent(self):
        """Test that multiple roundtrips produce consistent results."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "description": "Test description\n",
            "instructions": "You are a helpful assistant.\n\nProvide clear responses.\n",
            "tools": []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            
            # First roundtrip
            save_agent_file(agent_dict, file_path, format="md")
            read_dict1 = read_agent_file(str(file_path))
            
            # Second roundtrip (using the read dict)
            save_agent_file(read_dict1, file_path, format="md")
            read_dict2 = read_agent_file(str(file_path))
            
            # Third roundtrip
            save_agent_file(read_dict2, file_path, format="md")
            read_dict3 = read_agent_file(str(file_path))
            
            # All should be identical
            assert read_dict1 == read_dict2
            assert read_dict2 == read_dict3
    
    def test_no_trailing_newlines_gets_one_added(self):
        """Test that content without trailing newlines gets one added (file ends with newline)."""
        agent_dict = {
            "name": "test-agent",
            "model": "gpt-4",
            "instructions": "You are a helpful assistant.",
            "description": "Test description",
            "tools": []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            
            # Write (download)
            save_agent_file(agent_dict, file_path, format="md")
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            
            # Instructions gets trailing newline (file ends with newline by convention)
            assert read_dict["instructions"] == agent_dict["instructions"] + "\n"
            # Description stays as-is (metadata field)
            assert read_dict["description"] == agent_dict["description"]
    
    def test_metadata_fields_with_newlines(self):
        """Test that metadata fields preserve values as-is, instructions preserves trailing newline."""
        agent_dict = {
            "name": "test-agent\n",
            "model": "gpt-4\n",
            "description": "Test description\n",
            "instructions": "You are helpful.\n",
            "custom_field": "custom value\n",
            "tools": []
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            
            # Write (download)
            save_agent_file(agent_dict, file_path, format="md")
            
            # Read (upload)
            read_dict = read_agent_file(str(file_path))
            
            # YAML metadata fields preserve their values exactly
            assert read_dict["name"] == agent_dict["name"]
            assert read_dict["model"] == agent_dict["model"]
            assert read_dict["description"] == agent_dict["description"]
            assert read_dict["custom_field"] == agent_dict["custom_field"]
            # Instructions (content) preserves trailing newline
            assert read_dict["instructions"] == agent_dict["instructions"]
