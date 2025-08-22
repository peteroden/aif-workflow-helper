import json

from .name_validation import validate_agent_name
from glob import glob
from collections import defaultdict
from pathlib import Path
from azure.ai.agents import AgentsClient, models
from .logging_utils import logger, configure_logging  # re-exported for backward compatibility
_configure_logging_ref = configure_logging


def read_agent_file(file_path: str) -> dict | None:
    """Read a single agent JSON file.

    Args:
        file_path: Path to the agent JSON file
    Returns:
        Parsed dict or None if error
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            logger.info(f"Successfully read agent file: {file_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
    except FileNotFoundError:
        logger.error(f"Agent file not found: {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
    return None

def read_agent_files(path: str = ".") -> dict:
    """Read all agent JSON files in the specified directory

    Args:
        path: Directory path to search for agent JSON files.
    """
    agent_files = glob(f"{path}/*.json")
    agents_data = {}
    for file in agent_files:
        agent_data = read_agent_file(file)
        if agent_data:
            agents_data[agent_data["name"]] = agent_data    
    return agents_data

def extract_dependencies(agents_data: dict) -> defaultdict:
    """Extract dependencies from connected agents"""
    dependencies = defaultdict(set)
    
    for agent_name, agent_data in agents_data.items():
        tools = agent_data.get('tools', [])
        if not isinstance(tools, list):
            logger.debug(f"Agent '{agent_name}' has non-list 'tools' field; skipping")
            continue
        for tool in tools:
            if not isinstance(tool, dict):
                logger.debug(f"Agent '{agent_name}' tool entry not a dict; skipping: {tool}")
                continue
            if tool.get('type') == 'connected_agent':
                connected_agent_data = tool.get('connected_agent')
                if not isinstance(connected_agent_data, dict):
                    logger.debug(f"Agent '{agent_name}' connected_agent not a dict; skipping")
                    continue
                dependency_name = connected_agent_data.get('name_from_id')
                if dependency_name and dependency_name != "Unknown Agent":
                    dependencies[agent_name].add(dependency_name)
                    logger.debug(f"{agent_name} depends on {dependency_name}")
    
    return dependencies

def dependency_sort(agents_data: dict) -> list:
    """Perform sort to determine creation order based on dependencies"""
    
    agents = set(agents_data.keys())
    dependencies = extract_dependencies(agents_data)
    sorted_order = []
    unsorted = agents.copy()
    logger.info("Extracting dependencies...")
    while unsorted:
        ready = [a for a in unsorted if dependencies.get(a, set()).issubset(sorted_order)]
        if not ready:
            logger.warning(f"Circular dependencies detected for: {sorted(unsorted)}")
            sorted_order.extend(sorted(unsorted))
            break
        for a in ready:
            sorted_order.append(a)
            unsorted.remove(a)
    return sorted_order

def create_or_update_agent(agent_data: dict, agent_client: AgentsClient, existing_agents: list[models.Agent] = None, prefix: str = "", suffix: str = "") -> models.Agent:
    """Create or update an agent in the system
    
    Args:
        agent_data: Dictionary containing agent configuration
        agent_client: Azure AI Agents client
        existing_agents: Optional list of existing agents (fetched if None)
        prefix: Prefix to add to agent names
        suffix: Suffix to add to agent names
    """

    # Prepare agent data for creation (resolve connected agent references and any name changes)
    clean_data = agent_data.copy()

    if prefix != "" or suffix != "":
            full_agent_name = prefix + agent_data['name'] + suffix
            validate_agent_name(full_agent_name)
            clean_data['name'] = full_agent_name
    
    if existing_agents is None:
        existing_agents = list(agent_client.list_agents())
        logger.info(f"Found {len(existing_agents)} existing agents in the system")

    try:
        # Find existing agent by name
        existing_agent = None
        
        # Create a lookup dict for agent names to IDs
        agent_names_to_ids = {agent.name: agent.id for agent in existing_agents}
        
        for agent in existing_agents:
            if agent.name == clean_data['name']:
                existing_agent = agent
                break
        
        # Resolve connected agent name_from_id fields back to actual IDs
        if 'tools' in clean_data:
            for tool in clean_data['tools']:
                if tool.get('type') == 'connected_agent' and 'connected_agent' in tool:
                    connected_agent_data = tool['connected_agent']
                    
                    # If we have a name_from_id field, resolve it to actual ID
                    if 'name_from_id' in connected_agent_data:
                        agent_name_ref = prefix + connected_agent_data['name_from_id'] + suffix
                        
                        # Look up the actual agent ID
                        if agent_name_ref in agent_names_to_ids:
                            connected_agent_data['id'] = agent_names_to_ids[agent_name_ref]
                            logger.debug(f"Resolved '{agent_name_ref}' to ID: {agent_names_to_ids[agent_name_ref]}")
                        else:
                            logger.warning(f"Could not resolve agent name '{agent_name_ref}' to ID")
                        
                        # Remove our custom name_from_id field
                        del connected_agent_data['name_from_id']
        
        if existing_agent:
            logger.info(f"Updating existing agent: {clean_data['name']}")
            # Update existing agent
            updated_agent = agent_client.update_agent(
                agent_id=existing_agent.id,
                name=clean_data['name'],
                description=clean_data.get('description'),
                instructions=clean_data.get('instructions', ''),
                model=clean_data.get('model', 'gpt-4'),
                tools=clean_data.get('tools', []),
                temperature=clean_data.get('temperature', 1.0),
                top_p=clean_data.get('top_p', 1.0),
                metadata=clean_data.get('metadata', {})
            )
            return updated_agent
        else:
            logger.info(f"Creating new agent: {clean_data['name']}")
            # Create new agent
            new_agent = agent_client.create_agent(
                name=clean_data['name'],
                description=clean_data.get('description'),
                instructions=clean_data.get('instructions', ''),
                model=clean_data.get('model', 'gpt-4'),
                tools=clean_data.get('tools', []),
                temperature=clean_data.get('temperature', 1.0),
                top_p=clean_data.get('top_p', 1.0),
                metadata=clean_data.get('metadata', {})
            )
            return new_agent
            
    except Exception as e:
        logger.exception(f"Error creating/updating agent {clean_data['name']}: {e}")
        return None

def create_or_update_agents(agents_data: dict, agent_client: AgentsClient, prefix: str="", suffix: str="") -> None:
    """Create or update multiple agents in the system
    
    Args:
        agents_data: Dictionary containing agent configurations
        agent_client: Azure AI Agents client
        prefix: Prefix to add to agent names
        suffix: Suffix to add to agent names
    """
    logger.info("Sort agents to create in dependency order...")
    creation_ordered_agents = dependency_sort(agents_data)
    logger.info(f"Creating/updating agents in dependency order... {creation_ordered_agents}")

    existing_agents = list(agent_client.list_agents())
    logger.info(f"Found {len(existing_agents)} existing agents in the system")
    
    created_agents = []

    for agent_name in creation_ordered_agents:
        if agent_name in agents_data:
            logger.info(f"Processing: {agent_name}")
            agent = create_or_update_agent(agents_data[agent_name], agent_client, existing_agents, prefix, suffix)
            if agent:
                created_agents.append(agent)
                logger.info(f"✓ Successfully processed {agent_name}")
            else:
                logger.error(f"✗ Failed to process {agent_name}")

    logger.info(f"Completed! Processed {len(created_agents)} agents successfully.")



def create_or_update_agents_from_files(path: str, agent_client: AgentsClient, prefix: str="", suffix: str="") -> None:
    """Create or update multiple agents from a JSON file.

    Args:
        file_path: Path to the JSON file containing agent configurations
        agent_client: Azure AI Agents client
        prefix: Prefix to add to agent names
        suffix: Suffix to add to agent names
    """

    agents_dir = Path(path)
    if not agents_dir.exists() or not agents_dir.is_dir():
        logger.error(f"ERROR: Agents directory not found: {agents_dir}")
        raise ValueError(f"ERROR: Agents directory not found: {agents_dir}")

    try:
        print("Reading agent files...")
        agents_data = read_agent_files(agents_dir)
        logger.info(f"Found {len(agents_data)} agents")
        
        if agents_data:
            logger.info("Creating/updating agents...")
            create_or_update_agents(agents_data, agent_client, prefix, suffix)
        else:
            logger.info("No agent files found to process")

    except Exception as e:
        logger.error(f"Error uploading agent files: {e}")
        raise ValueError(f"Error uploading agent files: {e}")

def create_or_update_agent_from_file(agent_name: str, path: str, agent_client: AgentsClient, prefix: str="", suffix: str="") -> None:
    agent_dict = read_agent_file(f"{path}/{agent_name}.json")
    if agent_dict:
        create_or_update_agent(agent_data=agent_dict, agent_client=agent_client, prefix=prefix, suffix=suffix)