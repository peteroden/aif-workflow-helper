
import os
import json
import logging
from glob import glob
from collections import defaultdict
from azure.ai.agents import AgentsClient, models

logger = logging.getLogger(__name__)

def configure_logging(level: int = logging.INFO):
    """Configure basic logging for the helpers.

    Idempotent: calling multiple times will not duplicate handlers.
    """
    if logger.handlers:
        # Already configured
        return
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

def get_agent_name(agent_id, agent_client):
    """Get agent name by ID, return None if not found"""
    try:
        agent = agent_client.get_agent(agent_id)
        return agent.name if agent else None
    except Exception as e:
        logger.warning(f"Error getting agent name for ID {agent_id}: {e}")
        return None

def get_agent_by_name(agent_name, agent_client):
    """Get an agent by name from the system"""
    try:
        agent_list = agent_client.list_agents()
        for agent in agent_list:
            if agent.name == agent_name:
                return agent
        return None
    except Exception as e:
        logger.warning(f"Error getting agent by name '{agent_name}': {e}")
        return None

def generalize_agent_dict(data, agent_client):
    """Remove 'id' and 'created_at' properties from a dictionary or nested structure"""
    if isinstance(data, dict):
        # Special handling for connected_agent type
        if data.get('type') == 'connected_agent':
            # The ID is nested in the connected_agent object
            connected_agent_data = data.get('connected_agent', {})
            agent_id = connected_agent_data.get('id')
            
            # Get agent name for the connected agent
            agent_name = None
            if agent_id is not None:
                agent_name = get_agent_name(agent_id, agent_client)
            
            # Create new dict without 'id' and 'created_at' keys and recursively process values
            result = {}
            for k, v in data.items():
                if k not in ['id', 'created_at']:
                    if k == 'connected_agent':
                        # Process the connected_agent object and add id_name to it
                        processed_connected_agent = generalize_agent_dict(v, agent_client)
                        if agent_name:
                            processed_connected_agent['name_from_id'] = agent_name
                        else:
                            processed_connected_agent['name_from_id'] = "Unknown Agent"
                        result[k] = processed_connected_agent
                    else:
                        result[k] = generalize_agent_dict(v, agent_client)
            
            return result
        else:
            # Create new dict without 'id' and 'created_at' keys and recursively process values
            result = {}
            for k, v in data.items():
                if k not in ['id', 'created_at']:
                    result[k] = generalize_agent_dict(v, agent_client)
            
            return result
    elif isinstance(data, list):
        # Process each item in the list
        return [generalize_agent_dict(item, agent_client) for item in data]
    else:
        # Return primitive values as-is
        return data

def download_agents(agent_client, file_path: str | None = None):
    """Download all agents and save them to JSON files.

    Args:
        agent_client: Azure AI Agents client
        file_path: Optional directory path to save agent JSON files. Defaults to current working directory.
    """
    agent_list = agent_client.list_agents()

    base_dir = file_path or "."
    # Create directory if custom path provided and doesn't exist
    if base_dir and base_dir != ".":
        try:
            os.makedirs(base_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Could not create directory '{base_dir}': {e}")
            return

    for agent in agent_list:
        agent_dict = agent.as_dict()
        clean_dict = generalize_agent_dict(agent_dict, agent_client)

        filename = f"{agent.name}.json"
        full_path = f"{base_dir}/{filename}"
        try:
            with open(full_path, 'w') as f:
                json.dump(clean_dict, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving agent '{agent.name}' to {full_path}: {e}")
            return

        logger.info(f"Saved agent '{agent.name}' to {full_path}")
        logger.debug(json.dumps(clean_dict, indent=2))

def download_agent(agent_name, agent_client, file_path: str | None = None):
    """Download a specific agent by name and save it to a JSON file.

    Args:
        agent_name: Name of the agent to download
        agent_client: Azure AI Agents client
        file_path: Optional directory path to save the agent JSON file. Defaults to current working directory.
    """
    agent = get_agent_by_name(agent_name, agent_client)

    base_dir = file_path or "."
    if base_dir and base_dir != ".":
        try:
            os.makedirs(base_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Could not create directory '{base_dir}': {e}")
            return

    if agent:
        agent_dict = agent.as_dict()
        clean_dict = generalize_agent_dict(agent_dict, agent_client)

        filename = f"{agent.name}.json"
        full_path = f"{base_dir}/{filename}"
        try:
            with open(full_path, 'w') as f:
                json.dump(clean_dict, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving agent '{agent.name}' to {full_path}: {e}")
            return

        logger.info(f"Saved agent '{agent.name}' to {full_path}")
        logger.debug(json.dumps(clean_dict, indent=2))
    else:
        logger.warning(f"Agent with name {agent_name} not found.")

def read_agent_files(path: str = ".") -> dict:
    """Read all agent JSON files in the specified directory"""
    agent_files = glob(f"{path}/*.json")
    agents_data = {}
    
    for file in agent_files:
        try:
            with open(file, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON file '{file}': {e}")
                    continue
                agent_name = data.get('name')
                if agent_name:
                    agents_data[agent_name] = data
                    logger.info(f"Loaded agent: {agent_name}")
                else:
                    logger.debug(f"File '{file}' missing 'name' field; skipping")
        except OSError as e:
            logger.warning(f"Could not read file '{file}': {e}")
    
    return agents_data

def extract_dependencies(agents_data: dict):
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

def dependency_sort(agents_data: dict):
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

def create_or_update_agent(agent_data: dict, agent_client: AgentsClient, existing_agents: list[models.Agent] = None) -> models.Agent:
    """Create or update an agent in the system
    
    Args:
        agent_data: Dictionary containing agent configuration
        agent_client: Azure AI Agents client
        existing_agents: Optional list of existing agents (fetched if None)
    """
    
    agent_name = agent_data['name']
    
    if existing_agents is None:
        existing_agents = list(agent_client.list_agents())
        logger.info(f"Found {len(existing_agents)} existing agents in the system")

    try:
        # Find existing agent by name
        existing_agent = None
        
        # Create a lookup dict for agent names to IDs
        agent_name_to_id = {agent.name: agent.id for agent in existing_agents}
        
        for agent in existing_agents:
            if agent.name == agent_name:
                existing_agent = agent
                break
        
        # Prepare agent data for creation (resolve connected agent references)
        clean_data = agent_data.copy()
        
        # Resolve connected agent name_from_id fields back to actual IDs
        if 'tools' in clean_data:
            for tool in clean_data['tools']:
                if tool.get('type') == 'connected_agent' and 'connected_agent' in tool:
                    connected_agent_data = tool['connected_agent']
                    
                    # If we have a name_from_id field, resolve it to actual ID
                    if 'name_from_id' in connected_agent_data:
                        agent_name_ref = connected_agent_data['name_from_id']
                        
                        # Look up the actual agent ID
                        if agent_name_ref in agent_name_to_id:
                            connected_agent_data['id'] = agent_name_to_id[agent_name_ref]
                            logger.debug(f"Resolved '{agent_name_ref}' to ID: {agent_name_to_id[agent_name_ref]}")
                        else:
                            logger.warning(f"Could not resolve agent name '{agent_name_ref}' to ID")
                        
                        # Remove our custom name_from_id field
                        del connected_agent_data['name_from_id']
        
        if existing_agent:
            logger.info(f"Updating existing agent: {agent_name}")
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
            logger.info(f"Creating new agent: {agent_name}")
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
        logger.error(f"Error creating/updating agent {agent_name}: {str(e)}")
        return None

def create_or_update_agents(agents_data: dict, agent_client: AgentsClient) -> None:
    """Create or update multiple agents in the system
    
    Args:
        agents_data: Dictionary containing agent configurations
        agent_client: Azure AI Agents client
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
            agent = create_or_update_agent(agents_data[agent_name], agent_client, existing_agents)
            if agent:
                created_agents.append(agent)
                logger.info(f"✓ Successfully processed {agent_name}")
            else:
                logger.error(f"✗ Failed to process {agent_name}")

    logger.info(f"Completed! Processed {len(created_agents)} agents successfully.")
