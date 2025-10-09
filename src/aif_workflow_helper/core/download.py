import os
import json
from pathlib import Path 

from aif_workflow_helper.core.types import AgentLike

from aif_workflow_helper.utils.logging import logger
from aif_workflow_helper.utils.validation import validate_agent_name
from aif_workflow_helper.core.formats import get_file_extension
from aif_workflow_helper.core.types import SupportsAgents
from aif_workflow_helper.core.transformers.filesystem import save_agent_to_file as filesystem_save_agent

from typing import Optional, Union

def save_agent_file(agent_dict: dict, file_path: Union[str, Path], format: str = "json") -> bool:
    """Save agent data to file in the specified format.
    
    Args:
        agent_dict: Agent data dictionary
        file_path: Path where to save the file
        format: Format to save in (json, yaml, md)
        
    Returns:
        True if successful, False otherwise
    """
    return filesystem_save_agent(agent_dict, Path(file_path), format)

def trim_agent_name(agent_name: str, prefix: str = "", suffix: str = "") -> str:
    """Remove provided prefix and suffix from an agent name if present.

    Args:
        agent_name: Original agent name.
        prefix: Prefix to strip when found at the start.
        suffix: Suffix to strip when found at the end.

    Returns:
        The normalized agent name without the given prefix/suffix.
    """
    if prefix and agent_name.startswith(prefix):
        agent_name = agent_name[len(prefix):]
    if suffix and agent_name.endswith(suffix):
        agent_name = agent_name[:-len(suffix)]
    return agent_name

def get_agent_name(agent_id: str, agent_client: SupportsAgents) -> Optional[str]:
    """Retrieve an agent's name by its ID.

    Args:
        agent_id: Unique identifier of the agent.
        agent_client: Client used to fetch the agent.

    Returns:
        The agent name if found; otherwise None.
    """
    name: str | None = None
    try:
        agent = agent_client.get_agent(agent_id)
        if agent:
            name = agent.name
    except Exception as e:
        logger.warning(f"Error getting agent name for ID {agent_id}: {e}")
    return name

def get_agent_by_name(agent_name: str, agent_client: SupportsAgents) -> Optional[AgentLike]:
    """Fetch an agent object by its name.

    Args:
        agent_name: Name of the agent to retrieve.
        agent_client: Client used to list and search agents.

    Returns:
        The matching Agent instance if found; otherwise None.
    """
    found: AgentLike | None = None
    try:
        agent_list = agent_client.list_agents()
        for agent in agent_list:
            if agent.name == agent_name:
                found = agent
                break
    except Exception as e:
        logger.warning(f"Error getting agent by name '{agent_name}': {e}")
    return found

def generalize_agent_dict(data: dict, agent_client: SupportsAgents, prefix: str = "", suffix: str = "") -> dict:
    """Normalize an agent-derived structure for export.

    Removes transient keys (``id``, ``created_at``), converts connected agent
    IDs to a ``name_from_id`` field, and trims any provided prefix/suffix from
    agent names recursively.

    Args:
        data: Arbitrary nested structure (dict/list/primitives) from an agent.
        agent_client: Client used to resolve connected agent names.
        prefix: Optional prefix to remove from name fields.
        suffix: Optional suffix to remove from name fields.

    Returns:
        A new structure with IDs removed and names normalized.
    """
    result: dict | list | str | int | float | bool | None = None

    if isinstance(data, dict):
        if data.get('type') == 'connected_agent':
            connected_agent_data = data.get('connected_agent', {})
            agent_id = connected_agent_data.get('id')
            agent_name = get_agent_name(agent_id, agent_client) if agent_id is not None else None

            processed_connected: dict = {}
            for k, v in data.items():
                if k in ['id', 'created_at']:
                    continue
                if k == 'connected_agent':
                    nested = generalize_agent_dict(v, agent_client, prefix, suffix)
                    if isinstance(nested, dict):
                        nested['name_from_id'] = trim_agent_name(agent_name, prefix, suffix) if agent_name else "Unknown Agent"
                    processed_connected[k] = nested
                else:
                    processed_connected[k] = generalize_agent_dict(v, agent_client, prefix, suffix)
            result = processed_connected
        else:
            processed: dict = {}
            for k, v in data.items():
                if k in ['id', 'created_at']:
                    continue
                if k == 'name':
                    processed[k] = trim_agent_name(v, prefix, suffix)
                else:
                    processed[k] = generalize_agent_dict(v, agent_client, prefix, suffix)
            result = processed
    elif isinstance(data, list):
        result = [generalize_agent_dict(item, agent_client, prefix, suffix) for item in data]
    else:
        result = data

    return result

def download_agents(
    agent_client: SupportsAgents,
    file_path: Optional[str] = None,
    prefix: str = "",
    suffix: str = "",
    format: str = "json"
) -> bool:
    """Download all (optionally filtered) agents to files.

    Agents are filtered by prefix and suffix (both must match if provided) and
    each definition is normalized before being written.

    Args:
        agent_client: Client used to list agents.
        file_path: Directory where files are saved (defaults to current dir).
        prefix: Only include agents whose names start with this value.
        suffix: Only include agents whose names end with this value.
        format: Output format (json, yaml, md).

    Returns:
        True if all selected agents were written successfully; False otherwise.
    """
    success = True
    agent_list = agent_client.list_agents()
    base_dir = file_path or "."

    if base_dir and base_dir != ".":
        try:
            os.makedirs(base_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Could not create directory '{base_dir}': {e}")
            success = False

    if success:
        file_extension = get_file_extension(format)
        for agent in agent_list:
            try:
                logger.debug(f"Processing agent: {agent.name}")
                if not (agent.name.startswith(prefix) and agent.name.endswith(suffix)):
                    logger.debug(f"Skipping agent '{agent.name}' - doesn't match prefix/suffix filter")
                    continue
                
                logger.debug(f"Converting agent '{agent.name}' to dict...")
                agent_dict = agent.as_dict()
                logger.debug(f"Agent dict keys: {list(agent_dict.keys()) if agent_dict else 'None'}")
                
                logger.debug(f"Generalizing agent dict for '{agent.name}'...")
                clean_dict = generalize_agent_dict(agent_dict, agent_client, prefix, suffix)
                
                agent_name = agent.name[len(prefix):] if prefix else agent.name
                agent_name = agent_name[:-len(suffix)] if suffix else agent_name
                full_path = Path(f"{base_dir}/{agent_name}{file_extension}")
                
                if save_agent_file(clean_dict, full_path, format):
                    logger.info(f"Saved agent '{agent.name}' to {full_path}")
                    # Only try to serialize for debug if it's safe
                    try:
                        logger.debug(json.dumps(clean_dict, indent=2))
                    except (TypeError, ValueError) as json_error:
                        logger.debug(f"Could not serialize clean_dict for debug: {json_error}")
                else:
                    success = False
                    break
            except Exception as e:
                logger.error(f"Error processing agent '{agent.name}': {e}")
                success = False
                break

    return success

def download_agent(
    agent_name: str,
    agent_client: SupportsAgents,
    file_path: Optional[str] = None,
    prefix: str = "",
    suffix: str = "",
    format: str = "json"
) -> bool:
    """Download a single agent definition to a file.

    Args:
        agent_name: Agent name excluding optional prefix/suffix.
        agent_client: Client used to retrieve the agent.
        file_path: Directory where the file is saved (defaults to current dir).
        prefix: Prefix applied to the stored agent name in the service.
        suffix: Suffix applied to the stored agent name in the service.
        format: Output format (json, yaml, md).

    Returns:
        True if the agent definition was saved successfully; False otherwise.
    """
    success = True
    full_agent_name = f"{prefix}{agent_name}{suffix}"
    validate_agent_name(full_agent_name)
    agent = get_agent_by_name(full_agent_name, agent_client)

    base_dir = file_path or "."
    if base_dir and base_dir != ".":
        try:
            os.makedirs(base_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Could not create directory '{base_dir}': {e}")
            success = False

    if success and agent:
        agent_dict = agent.as_dict()
        clean_dict = generalize_agent_dict(agent_dict, agent_client, prefix, suffix)
        file_extension = get_file_extension(format)
        full_path = Path(f"{base_dir}/{agent_name}{file_extension}")
        
        if save_agent_file(clean_dict, full_path, format):
            logger.info(f"Saved agent '{agent.name}' to {full_path}")
            logger.debug(json.dumps(clean_dict, indent=2))
        else:
            success = False
    elif success and not agent:
        logger.warning(f"Agent with name {full_agent_name} not found.")
        success = False

    return success
