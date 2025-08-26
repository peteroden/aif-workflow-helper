
import os
import json
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import Agent

from .logging_utils import logger
from .name_validation import validate_agent_name

def trim_agent_name(agent_name: str, prefix: str = "", suffix: str = "") -> str:
    if prefix and agent_name.startswith(prefix):
        agent_name = agent_name[len(prefix):]
    if suffix and agent_name.endswith(suffix):
        agent_name = agent_name[:-len(suffix)]
    return agent_name

def get_agent_name(agent_id: str, agent_client: AgentsClient) -> str | None:
    """Get agent name by ID, return None if not found"""
    try:
        agent = agent_client.get_agent(agent_id)
        return agent.name if agent else None
    except Exception as e:
        logger.warning(f"Error getting agent name for ID {agent_id}: {e}")
        return None

def get_agent_by_name(agent_name: str, agent_client: AgentsClient) -> Agent | None:
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

def generalize_agent_dict(data: dict, agent_client: AgentsClient, prefix: str = "", suffix: str = "") -> dict:
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
                        processed_connected_agent = generalize_agent_dict(v, agent_client, prefix, suffix)
                        if agent_name:
                            processed_connected_agent['name_from_id'] = trim_agent_name(agent_name, prefix, suffix)
                        else:
                            processed_connected_agent['name_from_id'] = "Unknown Agent"
                        result[k] = processed_connected_agent
                    else:
                        result[k] = generalize_agent_dict(v, agent_client, prefix, suffix)
            
            return result
        else:
            # Create new dict without 'id' and 'created_at' keys and recursively process values
            result = {}
            for k, v in data.items():
                if k == 'name':
                    result[k] = trim_agent_name(v, prefix, suffix)
                elif k not in ['id', 'created_at']:
                    result[k] = generalize_agent_dict(v, agent_client, prefix, suffix)
            
            return result
    elif isinstance(data, list):
        # Process each item in the list
        return [generalize_agent_dict(item, agent_client, prefix, suffix) for item in data]
    else:
        # Return primitive values as-is
        return data

def download_agents(agent_client: AgentsClient, file_path: str | None = None, prefix: str = "", suffix: str = "") -> None:
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
        if agent.name.startswith(prefix) and agent.name.endswith(suffix):
            agent_dict = agent.as_dict()

            clean_dict = generalize_agent_dict(agent_dict, agent_client, prefix, suffix)

            # remove prefix from beginning and suffix from end of agent.name
            agent_name = agent.name[len(prefix):] if prefix else agent.name
            agent_name = agent_name[:-len(suffix)] if suffix else agent_name
            filename = f"{agent_name}.json"
            full_path = f"{base_dir}/{filename}"
            try:
                with open(full_path, 'w') as f:
                    json.dump(clean_dict, f, indent=2)

            except Exception as e:
                logger.error(f"Error saving agent '{agent.name}' to {full_path}: {e}")
                return

            logger.info(f"Saved agent '{agent.name}' to {full_path}")
            logger.debug(json.dumps(clean_dict, indent=2))

def download_agent(agent_name: str, agent_client: AgentsClient, file_path: str | None = None, prefix: str = "", suffix: str = "") -> None:
    """Download a specific agent by name and save it to a JSON file.

    Args:
        agent_name: Name of the agent to download
        agent_client: Azure AI Agents client
        file_path: Optional directory path to save the agent JSON file. Defaults to current working directory.
        prefix: Optional prefix for the Agent name. Defaults to an empty string.
        suffix: Optional suffix for the Agent name. Defaults to an empty string.
    """

    # add a check to make sure the prefix and suffix only contains letters and/or -
    full_agent_name = f"{prefix}{agent_name}{suffix}"
    validate_agent_name(full_agent_name)
    agent = get_agent_by_name(full_agent_name, agent_client)

    base_dir = file_path or "."
    if base_dir and base_dir != ".":
        try:
            os.makedirs(base_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Could not create directory '{base_dir}': {e}")
            return

    if agent:
        agent_dict = agent.as_dict()
        clean_dict = generalize_agent_dict(agent_dict, agent_client, prefix, suffix)

        filename = f"{agent_name}.json"
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
        logger.warning(f"Agent with name {full_agent_name} not found.")


