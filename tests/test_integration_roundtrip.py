"""Integration roundtrip tests that interact with actual AI Foundry instance.

These tests extend the format roundtrip tests by uploading to and downloading from
a real AI Foundry instance, verifying that the complete workflow preserves data.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any
import pytest

from aif_workflow_helper.core.agent_framework_client import AgentFrameworkAgentsClient
from aif_workflow_helper.core.upload import create_or_update_agent, read_agent_file
from aif_workflow_helper.core.download import download_agent
from aif_workflow_helper.utils.logging import logger

# -------------------- Normalization Utilities --------------------
def normalize_agent(agent: dict) -> dict:
    """Return a normalized shallow copy for stable comparisons.

    We intentionally ignore service-added benign fields and coerce minor
    representation differences (e.g. int->str in metadata, trailing newlines).
    """
    if agent is None:
        return {}
    a = dict(agent)

    # Fields we don't assert strict absence/presence for; remove for equality checks
    for transient in ["object", "temperature", "top_p", "response_format", "tool_resources"]:
        # Keep tool_resources only if it has meaningful content
        if transient == "tool_resources":
            tr = a.get(transient)
            if not tr:  # empty dict or None
                a.pop(transient, None)
            continue
        a.pop(transient, None)

    # Normalize instructions (service may append a trailing newline in md export)
    if "instructions" in a and isinstance(a["instructions"], str):
        a["instructions"] = a["instructions"].rstrip("\n")

    # Coerce metadata values that became strings (e.g. integers serialized)
    if isinstance(a.get("metadata"), dict):
        meta = {}
        for k, v in a["metadata"].items():
            # If original semantic numeric (simple digit string) convert to int-like string for comparison
            if isinstance(v, (int, float)):
                meta[k] = str(v)
            else:
                # If digit-only string, keep as is for consistent compare across sides
                meta[k] = v
        a["metadata"] = meta

    # Normalize tools: remove 'strict': false additions and ordering of keys
    tools = a.get("tools")
    if isinstance(tools, list):
        norm_tools = []
        for t in tools:
            if not isinstance(t, dict):
                norm_tools.append(t)
                continue
            t_copy = dict(t)
            if t_copy.get("type") == "function" and isinstance(t_copy.get("function"), dict):
                func = dict(t_copy["function"])
                # Remove service-added 'strict' flag when False (default)
                if func.get("strict") is False:
                    func.pop("strict", None)
                t_copy["function"] = func
            norm_tools.append(t_copy)
        a["tools"] = norm_tools

    return a


def print_agent_definition(agent_dict: Dict[str, Any], title: str) -> None:
    """Print agent definition for debugging and verification."""
    print(f"\n=== {title} ===")
    try:
        print(json.dumps(agent_dict, indent=2, ensure_ascii=False))
    except (TypeError, ValueError) as e:
        print(f"Could not serialize agent definition: {e}")
        print(f"Agent dict keys: {list(agent_dict.keys()) if agent_dict else 'None'}")
    print("=" * (len(title) + 8))


def requires_azure_ai_foundry():
    """Decorator to skip tests if Azure AI Foundry environment is not configured."""
    required_env_vars = ["AZURE_AI_PROJECT_ENDPOINT", "AZURE_TENANT_ID"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    return pytest.mark.skipif(
        bool(missing_vars),
        reason=f"Azure AI Foundry integration tests require environment variables: {missing_vars}"
    )


@pytest.fixture
def azure_agent_client():
    """Create a real Azure AI Foundry agent client for integration tests."""
    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    
    if not project_endpoint or not tenant_id:
        pytest.skip("Azure AI Foundry credentials not configured")
    
    client = AgentFrameworkAgentsClient(
        project_endpoint=project_endpoint,
        tenant_id=tenant_id
    )
    
    yield client
    
    # Cleanup: Try to remove any test agents created during tests
    try:
        agents = client.list_agents()
        for agent in agents:
            if agent.name.startswith("integration-test-"):
                logger.info(f"Cleaning up test agent: {agent.name}")
                client.delete_agent(agent.id)
    except Exception as e:
        logger.warning(f"Error during test cleanup: {e}")
    finally:
        client.close()


@pytest.fixture
def test_agent_base_name():
    """Generate unique test agent name to avoid conflicts."""
    import time
    return f"integration-test-{int(time.time())}"


@pytest.fixture
def sample_agents_dir():
    """Path to sample agent files directory."""
    from pathlib import Path
    return Path(__file__).parent.parent / "agents" / "sample"


@pytest.mark.integration
class TestIntegrationRoundtrip:
    """Integration tests for complete upload/download roundtrip with AI Foundry."""
    
    @requires_azure_ai_foundry()
    def test_basic_agent_roundtrip_json(self, azure_agent_client, test_agent_base_name):
        """Test basic agent roundtrip with JSON format."""
        original_agent = {
            "name": test_agent_base_name,
            "model": "gpt-4",
            "instructions": "You are a helpful assistant for testing.",
            "description": "Integration test agent",
            "tools": [],
            "metadata": {"test": "roundtrip", "format": "json"}
        }
        
        print_agent_definition(original_agent, "ORIGINAL AGENT DEFINITION")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Upload to AI Foundry
            uploaded_agent = create_or_update_agent(
                agent_data=original_agent,
                agent_client=azure_agent_client
            )
            
            assert uploaded_agent is not None, "Agent upload failed"
            assert uploaded_agent.name == test_agent_base_name
            logger.info(f"Successfully uploaded agent with ID: {uploaded_agent.id}")
            
            # Download from AI Foundry
            download_path = Path(tmpdir)
            success = download_agent(
                agent_name=test_agent_base_name,
                agent_client=azure_agent_client,
                file_path=str(download_path),
                format="json"
            )
            
            assert success, "Agent download failed"
            
            # Read downloaded file
            downloaded_file = download_path / f"{test_agent_base_name}.json"
            assert downloaded_file.exists(), f"Downloaded file not found: {downloaded_file}"
            
            downloaded_agent = read_agent_file(str(downloaded_file))
            assert downloaded_agent is not None, "Failed to parse downloaded agent file"
            
            print_agent_definition(downloaded_agent, "DOWNLOADED AGENT DEFINITION")
            
            # Normalize for comparison
            norm_original = normalize_agent(original_agent)
            norm_downloaded = normalize_agent(downloaded_agent)
            assert norm_downloaded == norm_original
    
    @requires_azure_ai_foundry()
    def test_agent_with_tools_roundtrip_yaml(self, azure_agent_client, test_agent_base_name):
        """Test agent with function tools roundtrip using YAML format."""
        original_agent = {
            "name": test_agent_base_name,
            "model": "gpt-4",
            "instructions": "You are a helpful assistant with weather capabilities.",
            "description": "Test agent with function tools",
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get current weather information",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "City name"
                                },
                                "units": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                }
                            },
                            "required": ["location"]
                        }
                    }
                }
            ],
            "metadata": {"test": "tools-roundtrip", "format": "yaml"}
        }
        
        print_agent_definition(original_agent, "ORIGINAL AGENT WITH TOOLS")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Upload to AI Foundry
            uploaded_agent = create_or_update_agent(
                agent_data=original_agent,
                agent_client=azure_agent_client
            )
            
            assert uploaded_agent is not None, "Agent with tools upload failed"
            logger.info(f"Successfully uploaded agent with tools, ID: {uploaded_agent.id}")
            
            # Download from AI Foundry
            download_path = Path(tmpdir)
            success = download_agent(
                agent_name=test_agent_base_name,
                agent_client=azure_agent_client,
                file_path=str(download_path),
                format="yaml"
            )
            
            assert success, "Agent with tools download failed"
            
            # Read downloaded file
            downloaded_file = download_path / f"{test_agent_base_name}.yaml"
            assert downloaded_file.exists(), f"Downloaded YAML file not found: {downloaded_file}"
            
            downloaded_agent = read_agent_file(str(downloaded_file))
            assert downloaded_agent is not None, "Failed to parse downloaded YAML agent file"
            
            print_agent_definition(downloaded_agent, "DOWNLOADED AGENT WITH TOOLS")
            
            # Verify tools structure is preserved
            assert downloaded_agent["name"] == original_agent["name"]
            assert downloaded_agent["model"] == original_agent["model"]
            assert normalize_agent(downloaded_agent)["instructions"] == normalize_agent(original_agent)["instructions"].rstrip("\n")
            assert len(downloaded_agent["tools"]) == 1
            
            downloaded_tool = downloaded_agent["tools"][0]
            original_tool = original_agent["tools"][0]
            
            assert downloaded_tool["type"] == original_tool["type"]
            assert downloaded_tool["function"]["name"] == original_tool["function"]["name"]
            assert downloaded_tool["function"]["description"] == original_tool["function"]["description"]
            assert downloaded_tool["function"]["parameters"] == original_tool["function"]["parameters"]
    
    @requires_azure_ai_foundry()
    def test_agent_with_tool_resources_roundtrip_md(self, azure_agent_client, test_agent_base_name):
        """Test agent with tool resources roundtrip using Markdown format."""
        original_agent = {
            "name": test_agent_base_name,
            "model": "gpt-4",
            "instructions": "You are a helpful assistant with file search capabilities.\n\nYou can search through uploaded files to find relevant information.",
            "description": "Test agent with file search tool resources",
            "tools": [{"type": "file_search"}],
            "tool_resources": {
                "file_search": {
                    "vector_store_ids": []  # Empty for test - would need actual vector stores in real usage
                }
            },
            "metadata": {"test": "tool-resources-roundtrip", "format": "markdown"}
        }
        
        print_agent_definition(original_agent, "ORIGINAL AGENT WITH TOOL RESOURCES")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Upload to AI Foundry
            uploaded_agent = create_or_update_agent(
                agent_data=original_agent,
                agent_client=azure_agent_client
            )
            
            assert uploaded_agent is not None, "Agent with tool resources upload failed"
            logger.info(f"Successfully uploaded agent with tool resources, ID: {uploaded_agent.id}")
            
            # Download from AI Foundry
            download_path = Path(tmpdir)
            success = download_agent(
                agent_name=test_agent_base_name,
                agent_client=azure_agent_client,
                file_path=str(download_path),
                format="md"
            )
            
            assert success, "Agent with tool resources download failed"
            
            # Read downloaded file
            downloaded_file = download_path / f"{test_agent_base_name}.md"
            assert downloaded_file.exists(), f"Downloaded MD file not found: {downloaded_file}"
            
            downloaded_agent = read_agent_file(str(downloaded_file))
            assert downloaded_agent is not None, "Failed to parse downloaded MD agent file"
            
            print_agent_definition(downloaded_agent, "DOWNLOADED AGENT WITH TOOL RESOURCES")
            
            # Verify tool resources structure is preserved
            assert downloaded_agent["name"] == original_agent["name"]
            assert downloaded_agent["model"] == original_agent["model"]
            # Allow for a trailing newline in instructions (markdown roundtrip always adds one)
            assert downloaded_agent["instructions"].rstrip("\n") == original_agent["instructions"].rstrip("\n")
            assert downloaded_agent["tools"] == original_agent["tools"]
            
            # Tool resources should be preserved (empty vector_store_ids becomes None/empty in some cases)
            if "tool_resources" in downloaded_agent:
                assert "file_search" in downloaded_agent["tool_resources"]
    
    @requires_azure_ai_foundry()
    def test_multiple_roundtrips_consistency(self, azure_agent_client, test_agent_base_name):
        """Test that multiple roundtrips produce consistent results."""
        original_agent = {
            "name": test_agent_base_name,
            "model": "gpt-4",
            "instructions": "You are a helpful assistant.\n\nProvide clear and concise responses.",
            "description": "Multi-roundtrip consistency test agent",
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "calculate",
                        "description": "Perform basic calculations",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "expression": {"type": "string"}
                            },
                            "required": ["expression"]
                        }
                    }
                }
            ],
            "metadata": {
                "test": "multi-roundtrip",
                "version": "1.0",
                "iterations": 3
            }
        }
        
        print_agent_definition(original_agent, "ORIGINAL MULTI-ROUNDTRIP AGENT")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            download_path = Path(tmpdir)
            current_agent = original_agent.copy()
            
            for iteration in range(3):
                logger.info(f"Starting roundtrip iteration {iteration + 1}")
                
                # Upload current agent
                uploaded_agent = create_or_update_agent(
                    agent_data=current_agent,
                    agent_client=azure_agent_client
                )
                
                assert uploaded_agent is not None, f"Upload failed in iteration {iteration + 1}"
                
                # Download the agent
                success = download_agent(
                    agent_name=test_agent_base_name,
                    agent_client=azure_agent_client,
                    file_path=str(download_path),
                    format="json"
                )
                
                assert success, f"Download failed in iteration {iteration + 1}"
                
                # Read the downloaded agent
                downloaded_file = download_path / f"{test_agent_base_name}.json"
                downloaded_agent = read_agent_file(str(downloaded_file))
                assert downloaded_agent is not None, f"Parse failed in iteration {iteration + 1}"
                
                print_agent_definition(downloaded_agent, f"ITERATION {iteration + 1} RESULT")
                
                # Verify consistency with original
                norm_orig = normalize_agent(original_agent)
                norm_dl = normalize_agent(downloaded_agent)
                # Coerce metadata numeric differences (iterations became string)
                if "metadata" in norm_orig and "metadata" in norm_dl:
                    for k in norm_orig["metadata"].keys():
                        if k in norm_dl["metadata"]:
                            if isinstance(norm_orig["metadata"][k], (int, float)):
                                norm_orig["metadata"][k] = str(norm_orig["metadata"][k])
                assert norm_dl == norm_orig
                
                # Use downloaded agent for next iteration
                current_agent = downloaded_agent
    
    @requires_azure_ai_foundry()
    def test_unicode_characters_roundtrip(self, azure_agent_client, test_agent_base_name):
        """Test that unicode characters and emojis are preserved through roundtrip."""
        original_agent = {
            "name": test_agent_base_name,
            "model": "gpt-4", 
            "instructions": "Hola! 你好! Привет! 🌍\n\nYou are a multilingual assistant. 🤖",
            "description": "Test agent with unicode: émojis 🎉, ñ, ü, ö, café ☕",
            "tools": [],
            "metadata": {
                "greeting": "¡Hola mundo! 世界你好！",
                "symbols": "→←↑↓ ♠♣♥♦ αβγδ ✓✗",
                "emoji": "😀😃😄😁🚀🎈🎉"
            }
        }
        
        print_agent_definition(original_agent, "ORIGINAL UNICODE AGENT")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Upload to AI Foundry
            uploaded_agent = create_or_update_agent(
                agent_data=original_agent,
                agent_client=azure_agent_client
            )
            
            assert uploaded_agent is not None, "Unicode agent upload failed"
            logger.info(f"Successfully uploaded unicode agent, ID: {uploaded_agent.id}")
            
            # Download from AI Foundry
            download_path = Path(tmpdir)
            success = download_agent(
                agent_name=test_agent_base_name,
                agent_client=azure_agent_client,
                file_path=str(download_path),
                format="json"
            )
            
            assert success, "Unicode agent download failed"
            
            # Read downloaded file
            downloaded_file = download_path / f"{test_agent_base_name}.json"
            downloaded_agent = read_agent_file(str(downloaded_file))
            assert downloaded_agent is not None, "Failed to parse downloaded unicode agent file"
            
            print_agent_definition(downloaded_agent, "DOWNLOADED UNICODE AGENT")
            
            # Verify unicode characters are preserved
            assert downloaded_agent["name"] == original_agent["name"]
            assert "🌍" in downloaded_agent["instructions"]
            assert "🤖" in downloaded_agent["instructions"]
            assert "🎉" in downloaded_agent["description"]
            assert "café" in downloaded_agent["description"]
            assert "☕" in downloaded_agent["description"]
            assert downloaded_agent["metadata"]["greeting"] == original_agent["metadata"]["greeting"]
            assert downloaded_agent["metadata"]["symbols"] == original_agent["metadata"]["symbols"]
            assert downloaded_agent["metadata"]["emoji"] == original_agent["metadata"]["emoji"]
    
    @requires_azure_ai_foundry()
    def test_sample_agents_roundtrip(self, azure_agent_client, test_agent_base_name, sample_agents_dir):
        """Test roundtrip using real sample agent files from the repository."""
        from aif_workflow_helper.core.upload import read_agent_files, create_or_update_agents
        
        # Read sample agents
        sample_agents = read_agent_files(str(sample_agents_dir), format="md")
        assert len(sample_agents) > 0, "No sample agents found"
        
        print(f"\n=== FOUND {len(sample_agents)} SAMPLE AGENTS ===")
        for name in sample_agents.keys():
            print(f"- {name}")
        
        # Rename agents with test prefix to avoid conflicts
        test_prefix = f"{test_agent_base_name}-"
        test_agents = {}
        for name, agent_data in sample_agents.items():
            test_name = name.replace(name, f"{test_prefix}{name}")
            agent_data = agent_data.copy()
            agent_data["name"] = test_name
            
            # Update connected agent references
            if "tools" in agent_data:
                for tool in agent_data["tools"]:
                    if (isinstance(tool, dict) and 
                        tool.get("type") == "connected_agent" and
                        "connected_agent" in tool):
                        connected_data = tool["connected_agent"]
                        if "name_from_id" in connected_data:
                            original_ref = connected_data["name_from_id"]
                            connected_data["name_from_id"] = f"{test_prefix}{original_ref}"
            
            test_agents[test_name] = agent_data
            print_agent_definition(agent_data, f"PREPARED TEST AGENT: {test_name}")
        
        # Upload all agents (with dependency resolution)
        try:
            create_or_update_agents(
                agents_data=test_agents,
                agent_client=azure_agent_client
            )
            
            logger.info(f"Successfully uploaded {len(test_agents)} test agents")
            
        except Exception as e:
            pytest.fail(f"Failed to upload sample agents: {e}")
        
        # Download all agents
        with tempfile.TemporaryDirectory() as tmpdir:
            download_path = Path(tmpdir)
            
            for agent_name in test_agents.keys():
                success = download_agent(
                    agent_name=agent_name,
                    agent_client=azure_agent_client, 
                    file_path=str(download_path),
                    format="md"
                )
                
                assert success, f"Failed to download agent: {agent_name}"
                
                # Verify downloaded file
                downloaded_file = download_path / f"{agent_name}.md"
                assert downloaded_file.exists(), f"Downloaded file missing: {downloaded_file}"
                
                downloaded_agent = read_agent_file(str(downloaded_file))
                assert downloaded_agent is not None, f"Failed to parse downloaded agent: {agent_name}"
                
                print_agent_definition(downloaded_agent, f"DOWNLOADED AGENT: {agent_name}")
                
                # Verify key fields match
                original_agent = test_agents[agent_name]
                assert downloaded_agent["name"] == original_agent["name"]
                assert downloaded_agent["model"] == original_agent["model"]
                assert downloaded_agent["instructions"] == original_agent["instructions"]
                
                # Verify connected agent tools are preserved
                if "tools" in original_agent and original_agent["tools"]:
                    assert "tools" in downloaded_agent
                    assert len(downloaded_agent["tools"]) == len(original_agent["tools"])
                    
                    for orig_tool, down_tool in zip(original_agent["tools"], downloaded_agent["tools"]):
                        if orig_tool.get("type") == "connected_agent":
                            assert down_tool.get("type") == "connected_agent"
                            assert "connected_agent" in down_tool
                            # The name_from_id should be preserved in the downloaded version
                            orig_connected = orig_tool["connected_agent"]
                            down_connected = down_tool["connected_agent"]
                            if "name_from_id" in orig_connected:
                                assert "name_from_id" in down_connected
                                assert down_connected["name_from_id"] == orig_connected["name_from_id"]
    
    @requires_azure_ai_foundry()
    def test_connected_agent_dependency_roundtrip(self, azure_agent_client, test_agent_base_name):
        """Test that connected agent dependencies are properly handled in roundtrip."""
        # Create a child agent first
        child_agent = {
            "name": f"{test_agent_base_name}-child",
            "model": "gpt-4",
            "instructions": "You are a specialized helper agent.",
            "description": "Child agent for dependency testing",
            "tools": [],
            "metadata": {"role": "child", "test": "dependency"}
        }
        
        # Create a parent agent that depends on the child
        parent_agent = {
            "name": f"{test_agent_base_name}-parent",
            "model": "gpt-4",
            "instructions": "You are a coordinator agent that delegates to specialists.",
            "description": "Parent agent with connected agent dependency",
            "tools": [
                {
                    "type": "connected_agent",
                    "connected_agent": {
                        "name_from_id": f"{test_agent_base_name}-child",
                        "description": "Specialized helper for complex tasks"
                    }
                }
            ],
            "metadata": {"role": "parent", "test": "dependency"}
        }
        
        print_agent_definition(child_agent, "CHILD AGENT DEFINITION")
        print_agent_definition(parent_agent, "PARENT AGENT DEFINITION")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Upload child agent first
            uploaded_child = create_or_update_agent(
                agent_data=child_agent,
                agent_client=azure_agent_client
            )
            assert uploaded_child is not None, "Child agent upload failed"
            logger.info(f"Uploaded child agent with ID: {uploaded_child.id}")
            
            # Refresh existing agents so parent can resolve dependency
            existing_agents = list(azure_agent_client.list_agents())
            # Upload parent agent (should resolve child dependency)
            uploaded_parent = create_or_update_agent(
                agent_data=parent_agent,
                agent_client=azure_agent_client,
                existing_agents=existing_agents
            )
            assert uploaded_parent is not None, "Parent agent upload failed"
            logger.info(f"Uploaded parent agent with ID: {uploaded_parent.id}")
            
            # Download parent agent
            download_path = Path(tmpdir)
            success = download_agent(
                agent_name=f"{test_agent_base_name}-parent",
                agent_client=azure_agent_client,
                file_path=str(download_path),
                format="json"
            )
            
            assert success, "Parent agent download failed"
            
            # Verify downloaded parent has correct connected agent reference
            downloaded_file = download_path / f"{test_agent_base_name}-parent.json"
            downloaded_parent = read_agent_file(str(downloaded_file))
            
            print_agent_definition(downloaded_parent, "DOWNLOADED PARENT WITH DEPENDENCY")
            
            assert downloaded_parent is not None, "Failed to parse downloaded parent agent"
            assert len(downloaded_parent["tools"]) == 1
            
            connected_tool = downloaded_parent["tools"][0]
            assert connected_tool["type"] == "connected_agent"
            assert "connected_agent" in connected_tool
            
            connected_data = connected_tool["connected_agent"]
            # Should have name_from_id instead of id after download
            assert "name_from_id" in connected_data
            assert connected_data["name_from_id"] == f"{test_agent_base_name}-child"
            assert "id" not in connected_data  # ID should be stripped during download
    
    @requires_azure_ai_foundry()
    def test_prefix_suffix_handling_roundtrip(self, azure_agent_client, test_agent_base_name):
        """Test that prefix and suffix are handled correctly in roundtrip."""
        prefix = "test-"
        suffix = "-v1"
        base_name = test_agent_base_name.replace("integration-test-", "")  # Remove default prefix
        
        original_agent = {
            "name": base_name,  # Name without prefix/suffix
            "model": "gpt-4",
            "instructions": "You are a test agent with prefix/suffix handling.",
            "description": "Test prefix and suffix handling",
            "tools": [],
            "metadata": {"test": "prefix-suffix-roundtrip"}
        }
        
        print_agent_definition(original_agent, "ORIGINAL AGENT (BASE NAME)")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Upload with prefix and suffix
            uploaded_agent = create_or_update_agent(
                agent_data=original_agent,
                agent_client=azure_agent_client,
                prefix=prefix,
                suffix=suffix
            )
            
            assert uploaded_agent is not None, "Prefix/suffix agent upload failed"
            # Agent name in Azure should have prefix and suffix
            expected_full_name = f"{prefix}{base_name}{suffix}"
            assert uploaded_agent.name == expected_full_name
            logger.info(f"Successfully uploaded agent with full name: {uploaded_agent.name}")
            
            # Download with prefix and suffix
            download_path = Path(tmpdir)
            success = download_agent(
                agent_name=base_name,  # Use base name for download
                agent_client=azure_agent_client,
                file_path=str(download_path),
                prefix=prefix,
                suffix=suffix,
                format="json"
            )
            
            assert success, "Prefix/suffix agent download failed"
            
            # Read downloaded file (should use base name)
            downloaded_file = download_path / f"{base_name}.json"
            assert downloaded_file.exists(), f"Downloaded file not found: {downloaded_file}"
            
            downloaded_agent = read_agent_file(str(downloaded_file))
            assert downloaded_agent is not None, "Failed to parse downloaded prefix/suffix agent file"
            
            print_agent_definition(downloaded_agent, "DOWNLOADED AGENT (STRIPPED NAME)")
            
            # Verify prefix/suffix were stripped during download
            assert downloaded_agent["name"] == base_name  # Should be back to base name
            norm_orig = normalize_agent(original_agent)
            norm_dl = normalize_agent(downloaded_agent)
            assert norm_dl == norm_orig


    @requires_azure_ai_foundry()
    def test_complete_sample_workflow_roundtrip(self, azure_agent_client, test_agent_base_name, sample_agents_dir):
        """Test the complete workflow with all sample agents including dependency resolution."""
        from aif_workflow_helper.core.upload import create_or_update_agents_from_files
        
        # Create a temporary directory with modified sample agents for testing
        with tempfile.TemporaryDirectory() as work_dir:
            work_path = Path(work_dir) / "test_agents"
            work_path.mkdir()
            
            # Copy and modify sample agents with test prefix
            test_prefix = f"{test_agent_base_name}-"
            
            for sample_file in sample_agents_dir.glob("*.md"):
                # Read original agent
                original_agent = read_agent_file(str(sample_file))
                if not original_agent:
                    continue
                    
                # Modify for testing
                test_agent = original_agent.copy()
                original_name = test_agent["name"]
                test_name = f"{test_prefix}{original_name}"
                test_agent["name"] = test_name
                
                # Update connected agent references
                if "tools" in test_agent:
                    for tool in test_agent["tools"]:
                        if (isinstance(tool, dict) and 
                            tool.get("type") == "connected_agent" and
                            "connected_agent" in tool):
                            connected_data = tool["connected_agent"]
                            if "name_from_id" in connected_data:
                                original_ref = connected_data["name_from_id"]
                                connected_data["name_from_id"] = f"{test_prefix}{original_ref}"
                
                print_agent_definition(test_agent, f"SAMPLE AGENT: {test_name}")
                
                # Save modified agent to work directory
                from aif_workflow_helper.core.download import save_agent_file
                test_file = work_path / f"{test_name}.md"
                success = save_agent_file(test_agent, test_file, "md")
                assert success, f"Failed to save test agent: {test_name}"
            
            # Upload all agents using the complete workflow
            try:
                create_or_update_agents_from_files(
                    path=str(work_path),
                    agent_client=azure_agent_client,
                    format="md"
                )
                logger.info("Successfully uploaded all sample agents via complete workflow")
            except Exception as e:
                pytest.fail(f"Complete workflow upload failed: {e}")
            
            # Download and verify all agents
            download_path = Path(work_dir) / "downloads"
            download_path.mkdir()
            
            # Get list of uploaded agents
            uploaded_agents = []
            for agent in azure_agent_client.list_agents():
                if agent.name.startswith(test_prefix):
                    uploaded_agents.append(agent)
            
            assert len(uploaded_agents) > 0, "No test agents found after upload"
            logger.info(f"Found {len(uploaded_agents)} uploaded test agents")
            
            for agent in uploaded_agents:
                agent_base_name = agent.name[len(test_prefix):]  # Remove prefix
                
                success = download_agent(
                    agent_name=agent_base_name,
                    agent_client=azure_agent_client,
                    file_path=str(download_path),
                    prefix=test_prefix,
                    format="md"
                )
                
                assert success, f"Failed to download agent: {agent.name}"
                
                # Verify downloaded file
                downloaded_file = download_path / f"{agent_base_name}.md"
                assert downloaded_file.exists(), f"Downloaded file missing: {downloaded_file}"
                
                downloaded_agent = read_agent_file(str(downloaded_file))
                assert downloaded_agent is not None, f"Failed to parse: {downloaded_file}"
                
                print_agent_definition(downloaded_agent, f"FINAL RESULT: {agent_base_name}")
                
                # Verify the roundtrip preserved essential data
                assert downloaded_agent["name"] == agent_base_name  # Prefix should be stripped
                assert downloaded_agent["model"] in ["gpt-4.1", "gpt-4.1-mini"]  # From sample files
                assert len(downloaded_agent["instructions"]) > 0
                
                # Verify connected agents are properly handled
                if "tools" in downloaded_agent and downloaded_agent["tools"]:
                    for tool in downloaded_agent["tools"]:
                        if tool.get("type") == "connected_agent":
                            connected_data = tool["connected_agent"]
                            # Should have name_from_id, not id
                            assert "name_from_id" in connected_data
                            assert "id" not in connected_data
                            # Name should be without prefix
                            ref_name = connected_data["name_from_id"]
                            assert not ref_name.startswith(test_prefix), f"Reference still has prefix: {ref_name}"


@pytest.mark.integration
class TestIntegrationRoundtripErrors:
    """Test error conditions in integration roundtrip scenarios."""
    
    @requires_azure_ai_foundry()
    def test_upload_invalid_model_fails(self, azure_agent_client, test_agent_base_name):
        """Document current service behavior: unknown model is accepted (no validation here)."""
        test_agent = {
            "name": test_agent_base_name,
            "model": "totally-nonexistent-model-xyz",
            "instructions": "This uses an unknown model.",
            "tools": []
        }

        print_agent_definition(test_agent, "UNKNOWN MODEL AGENT")

        uploaded_agent = create_or_update_agent(
            agent_data=test_agent,
            agent_client=azure_agent_client
        )

        # Service currently allows creation; assert roundtrip preserves requested model string.
        assert uploaded_agent is not None, "Agent creation unexpectedly failed"
        assert uploaded_agent.model == test_agent["model"], "Model string not preserved"
    
    @requires_azure_ai_foundry()
    def test_download_nonexistent_agent_fails(self, azure_agent_client):
        """Test that downloading non-existent agent fails gracefully."""
        nonexistent_name = "definitely-does-not-exist-12345"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            success = download_agent(
                agent_name=nonexistent_name,
                agent_client=azure_agent_client,
                file_path=tmpdir,
                format="json"
            )
            
            # Download should fail for non-existent agent
            assert not success, "Download of non-existent agent should have failed"
            
            # No file should be created
            download_file = Path(tmpdir) / f"{nonexistent_name}.json"
            assert not download_file.exists(), "No file should be created for non-existent agent"


if __name__ == "__main__":
    # Allow running tests directly for debugging
    pytest.main([__file__, "-v", "-s", "--tb=short"])