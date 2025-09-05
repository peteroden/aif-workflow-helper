import json
import yaml
import frontmatter

from glob import glob
from collections import defaultdict
from pathlib import Path
from azure.ai.agents import AgentsClient, models
from aif_workflow_helper.utils.validation import validate_agent_name
from aif_workflow_helper.core.formats import get_glob_pattern, get_file_extension, get_alternative_extensions
from aif_workflow_helper.utils.logging import logger

def read_agent_file(file_path: str) -> dict | None:
    """Read a single agent file in any supported format.

    Args:
        file_path: Path to the agent file (json, yaml, or md).

    Returns:
        Parsed dictionary if successful; otherwise None on error.
    """
    data: dict | None = None
    try:
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()
        
        with open(file_path, 'r') as f:
            if extension == '.json':
                loaded = json.load(f)
            elif extension in ['.yaml', '.yml']:
                loaded = yaml.safe_load(f)
            elif extension == '.md':
                # For markdown with frontmatter
                post = frontmatter.load(f)
                loaded = post.metadata.copy()
                loaded['instructions'] = post.content
            else:
                logger.error(f"Unsupported file format: {extension}")
                return None
                
        logger.info(f"Successfully read agent file: {file_path}")
        data = loaded
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {file_path}: {e}")
    except FileNotFoundError:
        logger.error(f"Agent file not found: {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
    return data

def read_agent_files(path: str = ".", format: str = "json") -> dict:
    """Load all agent files in a directory for the specified format.

    Args:
        path: Directory path to search for agent files (default current directory).
        format: Format to look for (json, yaml, md).

    Returns:
        Mapping of agent name to raw agent definition dictionaries.
    """
    # Get the glob pattern for the format
    pattern = get_glob_pattern(format)
    agent_files = glob(f"{path}/{pattern}")
    
    # Also check for alternative extensions if available
    for alt_ext in get_alternative_extensions(format):
        alt_pattern = f"*{alt_ext}"
        agent_files.extend(glob(f"{path}/{alt_pattern}"))
    
    agents_data = {}
    for file in agent_files:
        agent_data = read_agent_file(file)
        if agent_data:
            agents_data[agent_data["name"]] = agent_data    
    return agents_data

def extract_dependencies(agents_data: dict) -> defaultdict:
    """Extract inter-agent dependencies from agent definitions.

    Args:
        agents_data: Dictionary of agent name -> agent definition.

    Returns:
        defaultdict mapping agent names to sets of their dependencies.
    """
    dependencies = defaultdict(set)

    for agent_name, agent_data in agents_data.items():
        tools = agent_data.get("tools", [])
        for tool in tools:
            if isinstance(tool, dict) and tool.get("type") == "connected_agent":
                connected_agent_data = tool.get("connected_agent", {})
                if not isinstance(connected_agent_data, dict):
                    logger.debug(f"Agent '{agent_name}' connected_agent not a dict; skipping")
                    continue
                dependency_name = connected_agent_data.get('name_from_id')
                if dependency_name and dependency_name != "Unknown Agent":
                    dependencies[agent_name].add(dependency_name)
                    logger.debug(f"{agent_name} depends on {dependency_name}")
    
    return dependencies

def dependency_sort(agents_data: dict) -> list:
    """Topologically sort agents based on their dependencies.

    Args:
        agents_data: Dictionary of agent name -> agent definition.

    Returns:
        List of agent names in dependency-safe order.

    Raises:
        ValueError: If circular dependencies are detected.
    """
    dependencies = extract_dependencies(agents_data)
    
    # Kahn's algorithm for topological sorting
    in_degree = {agent: 0 for agent in agents_data.keys()}
    
    # Calculate in-degrees
    # If agent B depends on agent A, then A→B, so B has an incoming edge
    for agent in dependencies:
        for dep in dependencies[agent]:
            if dep in in_degree:
                in_degree[agent] += 1
    
    # Find nodes with no incoming edges
    queue = [agent for agent, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        current = queue.pop(0)
        result.append(current)
        
        # Remove current node and update in-degrees
        # For each agent that depends on current, decrement their in-degree
        for agent in dependencies:
            if current in dependencies[agent]:
                in_degree[agent] -= 1
                if in_degree[agent] == 0:
                    queue.append(agent)
    
    # Check for circular dependencies
    if len(result) != len(agents_data):
        remaining_agents = [agent for agent in agents_data.keys() if agent not in result]
        logger.error(f"Circular dependencies detected for agents: {remaining_agents}")
        raise ValueError(f"Circular dependencies detected for agents: {remaining_agents}")
    
    return result

def _prepare_agent_data_for_azure(agent_data: dict, existing_agents: list, prefix: str = "", suffix: str = "") -> dict:
    """Prepare agent data for Azure API calls by converting connected agents and cleaning fields.
    
    Args:
        agent_data: Raw agent definition dictionary.
        existing_agents: List of existing agents to resolve connected agent IDs.
        prefix: Optional prefix for agent names.
        suffix: Optional suffix for agent names.
        
    Returns:
        Cleaned agent data ready for Azure API calls.
    """
    # Make a copy to avoid modifying the original
    cleaned_data = agent_data.copy()
    
    # Convert connected agent tools to use IDs instead of names
    if "tools" in cleaned_data:
        for tool in cleaned_data["tools"]:
            if isinstance(tool, dict) and tool.get("type") == "connected_agent":
                connected_data = tool.get("connected_agent", {})
                if "name_from_id" in connected_data:
                    # Find the agent ID by name
                    dep_name = connected_data["name_from_id"]
                    # Apply prefix/suffix to find the actual agent name
                    dep_full_name = f"{prefix}{dep_name}{suffix}"
                    for existing in existing_agents:
                        if existing.name == dep_full_name:
                            connected_data["id"] = existing.id
                            del connected_data["name_from_id"]
                            break
    
    # Remove empty tool_resources - Azure expects None or proper ToolResources object
    if "tool_resources" in cleaned_data and not cleaned_data["tool_resources"]:
        del cleaned_data["tool_resources"]
    
    # Remove fields that shouldn't be sent to Azure APIs
    fields_to_remove = ["object"]  # 'object' is read-only
    for field in fields_to_remove:
        if field in cleaned_data:
            del cleaned_data[field]
    
    return cleaned_data

def create_or_update_agent(agent_data: dict, agent_client: AgentsClient, existing_agents: list[models.Agent] = None, prefix: str = "", suffix: str = "") -> models.Agent | None:
    """Create or update a single agent in Azure AI Foundry.

    Args:
        agent_data: Agent definition dictionary.
        agent_client: Azure AI Agents client.
        existing_agents: Optional list of existing agents to check against.
        prefix: Optional prefix to add to agent name.
        suffix: Optional suffix to add to agent name.

    Returns:
        Created or updated Agent instance, or None on failure.
    """
    agent: models.Agent | None = None
    
    try:
        agent_name = agent_data.get("name")
        if not agent_name:
            logger.error("Agent data missing 'name' field")
            return agent

        # Apply prefix/suffix to the name
        full_name = f"{prefix}{agent_name}{suffix}"
        validate_agent_name(full_name)
        
        # Update the agent data with the full name
        agent_data = agent_data.copy()
        agent_data["name"] = full_name

        # Check if agent exists
        existing_agent = None
        if existing_agents is None:
            # Fetch existing agents if not provided
            existing_agents = list(agent_client.list_agents())
        
        for existing in existing_agents:
            if existing.name == full_name:
                existing_agent = existing
                break

        if existing_agent:
            logger.info(f"Updating existing agent: {full_name}")
            cleaned_agent_data = _prepare_agent_data_for_azure(agent_data, existing_agents, prefix, suffix)
            agent = agent_client.update_agent(existing_agent.id, **cleaned_agent_data)
        else:
            logger.info(f"Creating new agent: {full_name}")
            cleaned_agent_data = _prepare_agent_data_for_azure(agent_data, existing_agents, prefix, suffix)
            agent = agent_client.create_agent(**cleaned_agent_data)
        
        logger.debug(f"Agent operation successful for {full_name}")

    except Exception as e:
        logger.error(f"Error creating/updating agent {agent_data.get('name', 'Unknown')}: {e}")
    
    return agent

def create_or_update_agents(agents_data: dict, agent_client: AgentsClient, prefix: str="", suffix: str="") -> None:
    """Create or update multiple agents with dependency-aware ordering.

    Args:
        agents_data: Dictionary of agent name -> agent definition.
        agent_client: Azure AI Agents client.
        prefix: Optional prefix to add to agent names.
        suffix: Optional suffix to add to agent names.
    """
    if not agents_data:
        logger.info("No agents to process")
        return

    logger.info(f"Processing {len(agents_data)} agents with dependency resolution...")
    
    # Sort agents by dependencies
    sorted_agent_names = dependency_sort(agents_data)
    
    # Get existing agents once for efficiency
    existing_agents = list(agent_client.list_agents())
    created_agents = []

    for i, agent_name in enumerate(sorted_agent_names, 1):
        logger.info(f"Processing {i}/{len(sorted_agent_names)}: {agent_name}")
        agent_data = agents_data[agent_name]
        
        agent = create_or_update_agent(
            agent_data=agent_data,
            agent_client=agent_client,
            existing_agents=existing_agents,
            prefix=prefix,
            suffix=suffix
        )
        
        if agent:
            created_agents.append(agent)
            existing_agents.append(agent)  # Add to list for future dependency resolution
            logger.info(f"✓ Successfully processed {agent_name}")
        else:
            logger.error(f"✗ Failed to process {agent_name}")

    logger.info(f"Completed! Processed {len(created_agents)} agents successfully.")

def create_or_update_agents_from_files(path: str, agent_client: AgentsClient, prefix: str="", suffix: str="", format: str="json") -> None:
    """Load agent files from a directory and create/update them.

    Args:
        path: Directory containing agent definition files.
        agent_client: Azure AI Agents client.
        prefix: Prefix applied to agent names.
        suffix: Suffix applied to agent names.
        format: Format of the files to read (json, yaml, md).
    """

    agents_dir = Path(path)
    if not agents_dir.exists() or not agents_dir.is_dir():
        logger.error(f"ERROR: Agents directory not found: {agents_dir}")
        raise ValueError(f"ERROR: Agents directory not found: {agents_dir}")

    try:
        logger.info("Reading agent files...")
        agents_data = read_agent_files(agents_dir, format)
        logger.info(f"Found {len(agents_data)} agents")
        
        if agents_data:
            logger.info("Creating/updating agents...")
            create_or_update_agents(agents_data, agent_client, prefix, suffix)
        else:
            logger.info("No agent files found to process")
            
    except Exception as e:
        logger.error(f"Error uploading agent files: {e}")
        raise ValueError(f"Error uploading agent files: {e}")

def create_or_update_agent_from_file(agent_name: str, path: str, agent_client: AgentsClient, prefix: str="", suffix: str="", format: str="json") -> None:
    """Create or update a single agent from a file.

    Args:
        agent_name: Base name (without extension) of the agent definition file.
        path: Directory containing the agent file.
        agent_client: Azure AI Agents client.
        prefix: Prefix applied to agent name.
        suffix: Suffix applied to agent name.
        format: Format of the file to read (json, yaml, md).
    """
    # Get the file extension for the format
    extension = get_file_extension(format)
    file_path = Path(f"{path}/{agent_name}{extension}")
    
    # Try alternative extensions if the primary one doesn't exist
    if not file_path.exists():
        for alt_ext in get_alternative_extensions(format):
            alt_file_path = Path(f"{path}/{agent_name}{alt_ext}")
            if alt_file_path.exists():
                file_path = alt_file_path
                break
    
    agent_dict = read_agent_file(str(file_path))
    if agent_dict:
        create_or_update_agent(agent_data=agent_dict, agent_client=agent_client, prefix=prefix, suffix=suffix)