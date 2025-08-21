# Azure AI Agents Workflow Helpers

This package provides utilities for managing Azure AI Agents, including downloading, uploading, and dependency management.

## 🚀 Quick Start

### 1. Set Environment Variables

```bash
export AZURE_TENANT_ID='your-tenant-id-here'
export AIF_ENDPOINT='your-ai-foundry-endpoint-here'
```

**Example:**

```bash
export AZURE_TENANT_ID='16b3c013-d300-468d-ac64-7eda0820b6d3'
export AIF_ENDPOINT='https://peroden-2927-resource.services.ai.azure.com/api/projects/peroden-2927'
```

### 2. Install Dependencies

```bash
cd aif_workflow_helpers
pip install -r requirements.txt
```

### 3. Run the Script

#### Option A: Direct Python execution (Recommended)

```bash
cd aif_workflow_helpers
source /workspaces/AIFoundry_CICD/.venv/bin/activate
PYTHONPATH=/workspaces/AIFoundry_CICD/aif_workflow_helpers python -c "from aif_workflow_helpers.upload_download_agents_helpers import main; main()"
```

#### Option B: Using the CLI script

```bash
cd aif_workflow_helpers
source /workspaces/AIFoundry_CICD/.venv/bin/activate
PYTHONPATH=/workspaces/AIFoundry_CICD/aif_workflow_helpers python aif_helper.py
```

#### Option C: Run directly as module

```bash
cd aif_workflow_helpers
source /workspaces/AIFoundry_CICD/.venv/bin/activate
python -m aif_workflow_helpers.upload_download_agents_helpers
```

## 📁 What the Script Does

1. **Downloads all existing agents** from Azure AI Foundry to JSON files
2. **Reads agent JSON files** from the current directory
3. **Analyzes dependencies** between agents (connected_agent tools)
4. **Creates/updates agents** in dependency order to avoid reference errors

## 🔧 Core Functions

### Agent Download Functions

- `download_agents(agent_client)` - Download all agents to JSON files
- `download_agent(agent_name, agent_client)` - Download specific agent
- `generalize_agent_dict(data, agent_client)` - Clean agent data for export

### Agent Upload Functions  

- `read_agent_files(path)` - Read JSON files from directory
- `create_or_update_agent(agent_data, client, existing_agents)` - Process single agent
- `create_or_update_agents(agents_data, client)` - Process multiple agents

### Dependency Management

- `extract_dependencies(agents_data)` - Find agent dependencies
- `dependency_sort(agents_data)` - Topological sort for creation order

### Helper Functions

- `get_agent_by_name(name, client)` - Find agent by name
- `get_agent_name(agent_id, client)` - Get agent name from ID

## 🎯 Usage as a Library

```python
from aif_workflow_helpers import (
    download_agents, 
    read_agent_files, 
    create_or_update_agents
)
from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

# Create client
client = AgentsClient(
    credential=DefaultAzureCredential(
        exclude_interactive_browser_credential=False,
        interactive_tenant_id="your-tenant-id"
    ),
    endpoint="your-endpoint"
)

# Download all agents
download_agents(client)

# Read and upload agents
agents_data = read_agent_files("./agents")
create_or_update_agents(agents_data, client)
```

## 📋 File Structure

```text
aif_workflow_helpers/
├── aif_workflow_helpers/
│   ├── __init__.py
│   └── upload_download_agents_helpers.py
├── requirements.txt
├── aif_helper.py
└── README.md
```

## ⚠️ Important Notes

1. **Authentication**: Uses Azure DefaultAzureCredential with interactive fallback
2. **Dependencies**: Automatically resolves agent dependencies using topological sort
3. **File Safety**: Agent names are sanitized for safe filesystem use
4. **Error Handling**: Comprehensive error handling with detailed logging
5. **Performance**: Optimized to minimize API calls using agent list caching

## 🔍 Troubleshooting

### "No module named 'azure'" Error

```bash
# Make sure you're in the virtual environment
source /workspaces/AIFoundry_CICD/.venv/bin/activate
# And set the Python path
export PYTHONPATH=/workspaces/AIFoundry_CICD/aif_workflow_helpers
```

### Authentication Errors

```bash
# Make sure environment variables are set
echo $AZURE_TENANT_ID
echo $AIF_ENDPOINT

# Try interactive login
az login --tenant $AZURE_TENANT_ID
```

### Import Errors

```bash
# Run from the correct directory
cd /workspaces/AIFoundry_CICD/aif_workflow_helpers
# Set Python path correctly
export PYTHONPATH=$(pwd)
```

## 🎉 Success Output

When running successfully, you should see:

```text
🔌 Testing connection...
✅ Connected! Found X existing agents

📥 Downloading agents...
Saved agent 'agent-name' to agent-name.json

📂 Reading agent files...
Found X agents

🚀 Creating/updating agents...
Processing 1/X: agent-name
✅ Successfully processed agent-name
```
