

import json
from glob import glob
from collections import defaultdict
from azure.ai.agents import AgentsClient, models
from azure.identity import DefaultAzureCredential

def get_agent_name(agent_id, agent_client):
    """Get agent name by ID, return None if not found"""
    try:
        agent = agent_client.get_agent(agent_id)
        return agent.name if agent else None
    except Exception as e:
        print(f"Error getting agent name for ID {agent_id}: {e}")
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
        print(f"Error getting agent by name '{agent_name}': {e}")
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

def download_agents(agent_client: AgentsClient):
    """Download all agents and save them to JSON files

    Args:
        agent_client: Azure AI Agents client
    """
    agent_list = agent_client.list_agents()

    for agent in agent_list:
        agent_dict = agent.as_dict()
        clean_dict = generalize_agent_dict(agent_dict, agent_client)
        
        # Create filename from agent name
        filename = f"{agent.name}.json"
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(clean_dict, f, indent=2)
        
        print(f"Saved agent '{agent.name}' to {filename}")
        print(json.dumps(clean_dict, indent=2))
        print()  # Add blank line between agents

def download_agent(agent_name, agent_client):
    """Download a specific agent by name and save it to a JSON file"""
    agent = get_agent_by_name(agent_name, agent_client)
    
    if agent:
        agent_dict = agent.as_dict()
        clean_dict = generalize_agent_dict(agent_dict, agent_client)
        
        # Create filename from agent name
        filename = f"{agent.name}.json"
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(clean_dict, f, indent=2)
        
        print(f"Saved agent '{agent.name}' to {filename}")
        print(json.dumps(clean_dict, indent=2))
    else:
        print(f"Agent with name {agent_name} not found.")

def read_agent_files(path: str = ".") -> dict:
    """Read all agent JSON files in the specified directory"""
    agent_files = glob(f"{path}/*.json")
    agents_data = {}
    
    for file in agent_files:
        with open(file, 'r') as f:
            data = json.load(f)
            agent_name = data.get('name')
            if agent_name:
                agents_data[agent_name] = data
                print(f"Loaded agent: {agent_name}")
    
    return agents_data

def extract_dependencies(agents_data: dict):
    """Extract dependencies from connected agents"""
    dependencies = defaultdict(set)
    
    for agent_name, agent_data in agents_data.items():
        tools = agent_data.get('tools', [])
        for tool in tools:
            if tool.get('type') == 'connected_agent':
                connected_agent_data = tool.get('connected_agent', {})
                dependency_name = connected_agent_data.get('name_from_id')
                if dependency_name and dependency_name != "Unknown Agent":
                    dependencies[agent_name].add(dependency_name)
                    print(f"  {agent_name} depends on {dependency_name}")
    
    return dependencies

def dependency_sort(agents_data: dict):
    """Perform sort to determine creation order based on dependencies"""
    all_agents = set(agents_data.keys())
    sorted_order = []
    remaining = all_agents.copy()

    print("\nExtracting dependencies...")
    dependencies = extract_dependencies(agents_data)

    # Keep processing until all agents are sorted
    while remaining:
        # Find agents with no unresolved dependencies
        ready = []
        for agent in remaining:
            agent_deps = dependencies.get(agent, set())
            # Check if all dependencies are already in sorted_order
            if agent_deps.issubset(set(sorted_order)):
                ready.append(agent)
        
        if not ready:
            # Circular dependency - just add remaining agents
            print(f"Warning: Circular dependencies detected for: {remaining}")
            sorted_order.extend(remaining)
            break
        
        # Add ready agents to sorted order
        for agent in ready:
            sorted_order.append(agent)
            remaining.remove(agent)
    
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
        print(f"Found {len(existing_agents)} existing agents in the system")

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
                            print(f"  Resolved '{agent_name_ref}' to ID: {agent_name_to_id[agent_name_ref]}")
                        else:
                            print(f"  Warning: Could not resolve agent name '{agent_name_ref}' to ID")
                        
                        # Remove our custom name_from_id field
                        del connected_agent_data['name_from_id']
        
        if existing_agent:
            print(f"Updating existing agent: {agent_name}")
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
            print(f"Creating new agent: {agent_name}")
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
        print(f"Error creating/updating agent {agent_name}: {str(e)}")
        return None

def create_or_update_agents(agents_data: dict, agent_client: AgentsClient) -> None:
    """Create or update multiple agents in the system
    
    Args:
        agents_data: Dictionary containing agent configurations
        agent_client: Azure AI Agents client
    """

    print("\nSort agents to create in dependency order...")
    creation_ordered_agents = dependency_sort(agents_data)
    print(f"\nCreating/updating agents in dependency order... {creation_ordered_agents}")

    existing_agents = list(agent_client.list_agents())
    print(f"Found {len(existing_agents)} existing agents in the system")
    
    created_agents = []

    for agent_name in creation_ordered_agents:
        if agent_name in agents_data:
            print(f"\nProcessing: {agent_name}")
            agent = create_or_update_agent(agents_data[agent_name], agent_client, existing_agents)
            if agent:
                created_agents.append(agent)
                print(f"✓ Successfully processed {agent_name}")
            else:
                print(f"✗ Failed to process {agent_name}")

    print(f"\nCompleted! Processed {len(created_agents)} agents successfully.")


def main():
    """Main execution function"""
    import os
    
    # Configuration - get from environment variables
    tenant_id = os.getenv("AZURE_TENANT_ID", "your-tenant-id-here")
    endpoint = os.getenv("AIF_ENDPOINT", "https://your-endpoint-here.services.ai.azure.com/api/projects/your-project")
    
    if tenant_id == "your-tenant-id-here" or endpoint == "https://your-endpoint-here.services.ai.azure.com/api/projects/your-project":
        print("❌ Please set AZURE_TENANT_ID and AIF_ENDPOINT environment variables")
        print("   export AZURE_TENANT_ID='your-tenant-id'")
        print("   export AIF_ENDPOINT='your-ai-foundry-endpoint'")
        return
    
    # Create agent client
    agent_client = AgentsClient(
        credential=DefaultAzureCredential(
            exclude_interactive_browser_credential=False, 
            interactive_tenant_id=tenant_id
        ),
        endpoint=endpoint
    )
    
    try:
        # Test connection
        print("🔌 Testing connection...")
        agents = list(agent_client.list_agents())
        print(f"✅ Connected! Found {len(agents)} existing agents")
        
        # Download all agents
        print("\n📥 Downloading agents...")
        download_agents(agent_client)
        
        # Read agent files and create/update
        print("\n📂 Reading agent files...")
        agents_data = read_agent_files()
        print(f"Found {len(agents_data)} agents")
        
        if agents_data:
            print("\n🚀 Creating/updating agents...")
            create_or_update_agents(agents_data, agent_client)
        else:
            print("No agent files found to process")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
