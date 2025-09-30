from typing import List, Tuple
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import Agent

from aif_workflow_helper.utils.logging import logger
from aif_workflow_helper.utils.validation import validate_agent_name
from aif_workflow_helper.core.download import get_agent_by_name


def delete_agent_by_name(
    agent_name: str,
    agent_client: AgentsClient,
    prefix: str = "",
    suffix: str = ""
) -> bool:
    """Delete a single agent by name.
    
    Args:
        agent_name: Agent name excluding optional prefix/suffix
        agent_client: Client used to retrieve and delete the agent
        prefix: Prefix applied to the stored agent name in the service
        suffix: Suffix applied to the stored agent name in the service
        
    Returns:
        True if the agent was deleted successfully; False otherwise
    """
    full_agent_name = f"{prefix}{agent_name}{suffix}"
    validate_agent_name(full_agent_name)
    
    try:
        agent = get_agent_by_name(full_agent_name, agent_client)
        
        if not agent:
            logger.warning(f"Agent with name '{full_agent_name}' not found.")
            return False
        
        # Delete the agent
        agent_client.delete_agent(agent.id)
        logger.info(f"Successfully deleted agent '{full_agent_name}' (ID: {agent.id})")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting agent '{full_agent_name}': {e}")
        return False


def get_matching_agents(
    agent_client: AgentsClient,
    prefix: str = "",
    suffix: str = ""
) -> List[Agent]:
    """Get all agents matching the prefix/suffix filter.
    
    Args:
        agent_client: Client used to list agents
        prefix: Only include agents whose names start with this value
        suffix: Only include agents whose names end with this value
        
    Returns:
        List of matching agent objects
    """
    agent_list = list(agent_client.list_agents())
    
    # Filter agents by prefix and suffix
    # Only apply filters if they are non-empty strings
    matching_agents = []
    for agent in agent_list:
        matches = True
        if prefix and not agent.name.startswith(prefix):
            matches = False
        if suffix and not agent.name.endswith(suffix):
            matches = False
        if matches:
            matching_agents.append(agent)
    
    return matching_agents


def delete_agents(
    agent_client: AgentsClient,
    agent_list: List[Agent]
) -> Tuple[bool, int]:
    """Delete a list of agents.
    
    Args:
        agent_client: Client used to delete agents
        agent_list: List of agent objects to delete
        
    Returns:
        Tuple of (success: bool, deleted_count: int)
    """
    if not agent_list:
        logger.info("No agents to delete.")
        return True, 0
    
    success = True
    deleted_count = 0
    
    for agent in agent_list:
        try:
            agent_client.delete_agent(agent.id)
            logger.info(f"Deleted agent '{agent.name}' (ID: {agent.id})")
            deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete agent '{agent.name}': {e}")
            success = False
    
    logger.info(f"Successfully deleted {deleted_count} of {len(agent_list)} agent(s)")
    return success, deleted_count
