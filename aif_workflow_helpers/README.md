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

#### Option A: Using the CLI script (Recommended)

```bash
cd aif_workflow_helpers
source /workspaces/AIFoundry_CICD/.venv/bin/activate
PYTHONPATH=/workspaces/AIFoundry_CICD/aif_workflow_helpers python aif_helper.py
```

#### Option B: Direct module usage

You can import and use individual functions programmatically:

```python
from aif_workflow_helpers import (
    configure_logging,
    download_agents,
    download_agent,
    create_or_update_agents,
    create_or_update_agent
)

from azure.ai.agents import AgentsClient
from azure.identity import DefaultAzureCredential

configure_logging()

client = AgentsClient(
    credential=DefaultAzureCredential(
        exclude_interactive_browser_credential=False,
        interactive_tenant_id="your-tenant-id"
    ),
    endpoint="your-endpoint"
)

download_agents(client, file_path="./agents")
agents_data = read_agent_files("./agents")
create_or_update_agents(agents_data, client)
```

## 📁 What the Tooling Does

1. **Downloads all existing agents** from Azure AI Foundry to JSON files
2. **Reads agent JSON files** from the current directory
3. **Analyzes dependencies** between agents (connected_agent tools)
4. **Creates/updates agents** in dependency order to avoid reference errors

## 🔧 Core Functions

### Download Functions

- `download_agents(agent_client, file_path, prefix, suffix)` - Download all agents (filtered by optional prefix/suffix)
- `download_agent(agent_name, agent_client, file_path, prefix, suffix)` - Download a single agent
- `generalize_agent_dict(data, agent_client, prefix, suffix)` - Normalize agent JSON for portability

### Upload Functions  

- `read_agent_files(path)` / `read_agent_file(path)` - Read JSON definitions
- `create_or_update_agent(agent_data, agent_client, existing_agents, prefix, suffix)` - Upsert a single agent
- `create_or_update_agents(agents_data, agent_client, prefix, suffix)` - Upsert multiple agents (dependency ordered)
- `create_or_update_agent_from_file(agent_name, path, agent_client, prefix, suffix)` - Upsert a specific agent file
- `create_or_update_agents_from_files(path, agent_client, prefix, suffix)` - Convenience wrapper to load + upsert

### Dependency Management

- `extract_dependencies(agents_data)` - Infer connected-agent dependencies
- `dependency_sort(agents_data)` - Topological order respecting dependencies

### Lookup Helpers

- `get_agent_by_name(name, client)` - Fetch agent object by name
- `get_agent_name(agent_id, client)` - Resolve ID to name

## 🎯 CLI Usage

The CLI `aif_helper.py` supports the following flags:

```text
--agents-dir DIR              Directory for agent JSON files (default: agents)
--download-all-agents         Download all existing agents
--download-agent NAME         Download a single agent by name
--upload-all-agents           Create/update all agents from JSON files
--upload-agent NAME           Create/update a single agent from JSON file
--prefix TEXT                 Optional prefix applied during download/upload
--suffix TEXT                 Optional suffix applied during download/upload
--log-level LEVEL             Logging level (CRITICAL, ERROR, WARNING, INFO, DEBUG)
```

Examples:

```bash
# Download all agents whose names begin with 'dev-' and end with '-v1'
python aif_helper.py --download-all-agents --prefix dev- --suffix -v1

# Upload all local JSON definitions adding a prefix
python aif_helper.py --upload-all-agents --prefix staging-

# Download a single agent
python aif_helper.py --download-agent my_agent

# Upload a single agent file
python aif_helper.py --upload-agent my_agent
```

## 📋 File Structure

```text
aif_workflow_helpers/
├── aif_helper.py                 # CLI entrypoint
├── requirements.txt
├── README.md
└── aif_workflow_helpers/
    ├── __init__.py               # Re-exports helper functions
    ├── upload_agent_helpers.py   # Upload + dependency logic
    ├── download_agent_helpers.py # Download + generalization logic
    ├── logging_utils.py          # Shared logging setup
    ├── name_validation.py        # Agent name validation
    └── vscode_sdk_coversion_helpers.py
```

## ⚠️ Important Notes

1. **Authentication**: Uses Azure DefaultAzureCredential with interactive fallback
2. **Dependencies**: Automatically resolves agent dependencies using topological sort
3. **File Safety**: Agent names are sanitized for safe filesystem use
4. **Error Handling**: Comprehensive error handling with detailed logging
5. **Performance**: Minimizes API calls via cached existing agent list during batch operations

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
