import json

from .name_validation import validate_agent_name
from glob import glob
from collections import defaultdict
from pathlib import Path
from azure.ai.agents import AgentsClient, models
from .logging_utils import logger

def read_agent_file(file_path: str) -> dict | None:
    """Read a single agent JSON file.

    Args:
        file_path: Path to the agent JSON file.

    Returns:
        Parsed dictionary if successful; otherwise None on error.
    """
    data: dict | None = None
    try:
        with open(file_path, 'r') as f:
            loaded = json.load(f)
            logger.info(f"Successfully read agent file: {file_path}")
            data = loaded
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
    except FileNotFoundError:
        logger.error(f"Agent file not found: {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
    return data

def read_agent_files(path: str = ".") -> dict:
    """Load all agent JSON files in a directory.

    Args:
        path: Directory path to search for agent JSON files (default current directory).

    Returns:
        Mapping of agent name to raw agent definition dictionaries.
    """
    agent_files = glob(f"{path}/*.json")
    agents_data = {}
    for file in agent_files:
        agent_data = read_agent_file(file)
        if agent_data:
            agents_data[agent_data["name"]] = agent_data    
    return agents_data

def extract_dependencies(agents_data: dict) -> defaultdict:
    """Extract connected-agent dependencies.

    Scans each agent's `tools` list for entries of type `connected_agent` and
    records name-based dependencies.

    Args:
        agents_data: Mapping of agent name to its configuration dictionary.

    Returns:
        A defaultdict(set) mapping agent name to the set of dependency names.
    """
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
    """Order agents so dependencies are created first.

    Performs a topological-like sort; if cycles are detected, remaining agents
    are appended in arbitrary order with a warning.

    Args:
        agents_data: Mapping of agent name to configuration.

    Returns:
        List of agent names in creation order.
    """
    
    agents = set(agents_data.keys())
    dependencies = extract_dependencies(agents_data)
    sorted_order = []
    unsorted = agents.copy()
    logger.info("Extracting dependencies...")
    while unsorted:
        ready = [a for a in unsorted if dependencies.get(a, set()).issubset(sorted_order)]
        if not ready:
            logger.error(f"Circular dependencies detected for: {sorted(unsorted)}")
            raise ValueError(f"Circular dependencies detected for {sorted(unsorted)}")
        for a in ready:
            sorted_order.append(a)
            unsorted.remove(a)
    return sorted_order

def create_or_update_agent(agent_data: dict, agent_client: AgentsClient, existing_agents: list[models.Agent] = None, prefix: str = "", suffix: str = "") -> models.Agent | None:
    """Create or update a single agent definition.

    Resolves any connected-agent references using the provided existing agent
    list (fetching if necessary) and applies an optional prefix/suffix to the
    agent's name for namespacing.

    Args:
        agent_data: Agent configuration dictionary.
        agent_client: Azure AI Agents client.
        existing_agents: Optional pre-fetched list of agent objects.
        prefix: Prefix applied to the agent name.
        suffix: Suffix applied to the agent name.

    Returns:
        The created or updated agent instance, or None on failure.
    """
    result: models.Agent | None = None

    clean_data = agent_data.copy()
    if prefix or suffix:
        full_agent_name = prefix + agent_data['name'] + suffix
        validate_agent_name(full_agent_name)
        clean_data['name'] = full_agent_name

    if existing_agents is None:
        existing_agents = list(agent_client.list_agents())
        logger.info(f"Found {len(existing_agents)} existing agents in the system")

    try:
        existing_agent = None
        agent_names_to_ids = {agent.name: agent.id for agent in existing_agents}
        for agent in existing_agents:
            if agent.name == clean_data['name']:
                existing_agent = agent
                break

        if 'tools' in clean_data:
            for tool in clean_data['tools']:
                if tool.get('type') == 'connected_agent' and 'connected_agent' in tool:
                    connected_agent_data = tool['connected_agent']
                    if 'name_from_id' in connected_agent_data:
                        agent_name_ref = prefix + connected_agent_data['name_from_id'] + suffix
                        if agent_name_ref in agent_names_to_ids:
                            connected_agent_data['id'] = agent_names_to_ids[agent_name_ref]
                            logger.debug(f"Resolved '{agent_name_ref}' to ID: {agent_names_to_ids[agent_name_ref]}")
                        else:
                            logger.warning(f"Could not resolve agent name '{agent_name_ref}' to ID")
                        del connected_agent_data['name_from_id']

        if existing_agent:
            logger.info(f"Updating existing agent: {clean_data['name']}")
            result = agent_client.update_agent(
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
        else:
            logger.info(f"Creating new agent: {clean_data['name']}")
            result = agent_client.create_agent(
                name=clean_data['name'],
                description=clean_data.get('description'),
                instructions=clean_data.get('instructions', ''),
                model=clean_data.get('model', 'gpt-4'),
                tools=clean_data.get('tools', []),
                temperature=clean_data.get('temperature', 1.0),
                top_p=clean_data.get('top_p', 1.0),
                metadata=clean_data.get('metadata', {})
            )
    except Exception as e:  # pragma: no cover (already logged via exception)
        logger.exception(f"Error creating/updating agent {clean_data['name']}: {e}")
        result = None

    return result

def create_or_update_agents(agents_data: dict, agent_client: AgentsClient, prefix: str="", suffix: str="") -> None:
    """Create or update multiple agents honoring dependencies.

    Args:
        agents_data: Mapping of agent name to configuration dictionaries.
        agent_client: Azure AI Agents client.
        prefix: Prefix applied to each agent name during creation/update.
        suffix: Suffix applied to each agent name during creation/update.
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
    """Load agent files from a directory and create/update them.

    Args:
        path: Directory containing `*.json` agent definition files.
        agent_client: Azure AI Agents client.
        prefix: Prefix applied to agent names.
        suffix: Suffix applied to agent names.
    """

    agents_dir = Path(path)
    if not agents_dir.exists() or not agents_dir.is_dir():
        logger.error(f"ERROR: Agents directory not found: {agents_dir}")
        raise ValueError(f"ERROR: Agents directory not found: {agents_dir}")

    try:
        logger.info("Reading agent files...")
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
    """Create or update a single agent from a JSON file.

    Args:
        agent_name: Base name (without .json) of the agent definition file.
        path: Directory containing the agent file.
        agent_client: Azure AI Agents client.
        prefix: Prefix applied to agent name.
        suffix: Suffix applied to agent name.
    """
    agent_dict = read_agent_file(Path(f"{path}/{agent_name}.json"))
    if agent_dict:
        create_or_update_agent(agent_data=agent_dict, agent_client=agent_client, prefix=prefix, suffix=suffix)