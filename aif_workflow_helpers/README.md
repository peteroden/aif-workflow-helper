# Azure AI Agents Workflow Helpers

Utilities for exporting (downloading) and importing (creating/updating) Azure AI Agents along with dependency awareness, normalization, and consistent logging.

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

### 3. Using the CLI (Recommended)

The CLI wraps the helper functions and enforces environment validation.

```bash
cd aif_workflow_helpers
python aif_helper.py --download-all-agents --agents-dir agents
```

Common examples:

```bash
# Download all agents with optional prefix/suffix filtering
python aif_helper.py --download-all-agents --prefix dev- --suffix -v1

# Download a single agent
python aif_helper.py --download-agent my_agent

# Upload all agents from JSON definitions in a directory
python aif_helper.py --upload-all-agents --agents-dir agents

# Upload a single agent definition file
python aif_helper.py --upload-agent my_agent --agents-dir agents

# Download agents in different formats
python aif_helper.py --download-all-agents --format json     # Default
python aif_helper.py --download-all-agents --format yaml     # YAML format
python aif_helper.py --download-all-agents --format md       # Markdown with frontmatter

# Upload agents from different formats
python aif_helper.py --upload-all-agents --format yaml
python aif_helper.py --upload-agent my_agent --format md

# Change log level
python aif_helper.py --download-all-agents --log-level DEBUG
```

### 4. Direct Library Usage

You can import and compose the underlying functions directly:

```python
from aif_workflow_helpers import (
    configure_logging,
    download_agents,
    download_agent,
    create_or_update_agents,
    create_or_update_agent,
    create_or_update_agent_from_file,
    create_or_update_agents_from_files,
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

# Bulk download
download_agents(client, file_path="./agents", prefix="", suffix="", format="json")

# Create/update from a directory (dependency ordered)
create_or_update_agents_from_files(path="./agents", agent_client=client, prefix="", suffix="", format="json")
```

## 📁 What the Tooling Does

1. Downloads existing agents to normalized files (JSON, YAML, or Markdown with frontmatter)
2. Normalizes (generalizes) definitions for portability (removes resource-specific fields)
3. Infers and resolves inter-agent dependencies (connected agent tools)
4. Creates or updates agents in dependency-safe order
5. Applies optional prefix/suffix for environment namespacing
6. Supports multiple file formats for flexible workflow integration

## 🔧 Core Functions

### Download Functions

- `download_agents(agent_client, file_path, prefix, suffix, format)` – Download and generalize all agents (optional prefix/suffix filters, format selection)
- `download_agent(agent_name, agent_client, file_path, prefix, suffix, format)` – Download and generalize a single agent
- `generalize_agent_dict(data, agent_client, prefix, suffix)` – Normalize agent JSON for portability

### Upload Functions

- `create_or_update_agent(agent_data, agent_client, existing_agents, prefix, suffix)` – Upsert a single agent object
- `create_or_update_agents(agents_data, agent_client, prefix, suffix)` – Upsert multiple agents with dependency ordering
- `create_or_update_agent_from_file(agent_name, path, agent_client, prefix, suffix, format)` – Upsert from a specific file
- `create_or_update_agents_from_files(path, agent_client, prefix, suffix, format)` – Bulk load and upsert directory

### Internal Helpers (Not all re-exported)

- `read_agent_file(path)` / `read_agent_files(path, format)` – Load definitions in any supported format (used internally by *from_files* wrappers)
- `extract_dependencies(agents_data)` – Build dependency graph
- `dependency_sort(agents_data)` – Topological sort of agents
- `get_agent_by_name(name, client)` – Lookup agent object
- `get_agent_name(agent_id, client)` – Reverse lookup by ID

## 🎯 CLI Reference

`aif_helper.py` arguments:

```text
--agents-dir DIR        Directory for agent definition files (default: agents)
--download-all-agents   Download all existing agents
--download-agent NAME   Download a single agent by name
--upload-all-agents     Create/update all agents from definition files
--upload-agent NAME     Create/update a single agent from definition file
--prefix TEXT           Optional prefix applied during download/upload
--suffix TEXT           Optional suffix applied during download/upload
--format FORMAT         File format: json, yaml, or md (default: json)
--log-level LEVEL       Logging level (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET)
```

## 📄 Supported File Formats

The tool supports three file formats for agent definitions:

### JSON Format (Default)

Standard JSON format with all agent properties in a single object:

```json
{
  "name": "my-agent",
  "model": "gpt-4",
  "instructions": "You are a helpful AI assistant...",
  "tools": [],
  "temperature": 0.7,
  "top_p": 1.0
}
```

### YAML Format

Clean YAML format for better readability:

```yaml
name: my-agent
model: gpt-4
instructions: |
  You are a helpful AI assistant.
  Please provide clear and concise responses.
tools: []
temperature: 0.7
top_p: 1.0
```

### Markdown with Frontmatter

Markdown format where the `instructions` field becomes the content and all other properties go into YAML frontmatter:

```markdown
---
name: my-agent
model: gpt-4
tools: []
temperature: 0.7
top_p: 1.0
---
You are a helpful AI assistant.

Please provide clear and concise responses to user questions.
```

**File Extensions:**

- JSON: `.json`
- YAML: `.yaml` or `.yml`
- Markdown: `.md`

## 📋 File Structure

```text
aif_workflow_helpers/
├── aif_helper.py                 # CLI entrypoint
├── requirements.txt
├── README.md
└── aif_workflow_helpers/
    ├── __init__.py               # Public exports (upload/download/logging)
    ├── upload_agent_helpers.py   # Upload + dependency logic
    ├── download_agent_helpers.py # Download + generalization logic
    ├── logging_utils.py          # Shared logging configuration
    ├── name_validation.py        # Agent name validation
```

## ⚠️ Important Notes

1. **Authentication**: Uses `DefaultAzureCredential` (interactive fallback enabled)
2. **Dependency Ordering**: Creates/updates in safe order via topological sort
3. **Name Safety**: Validation ensures only alphanumerics + hyphens (prefix/suffix applied consistently)
4. **Logging**: Centralized configurable logger (`configure_logging`)
5. **Efficiency**: Minimizes duplicate lookups by caching existing agents during batch operations
6. **Format Flexibility**: Supports JSON, YAML, and Markdown with frontmatter for different workflow preferences

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

Typical successful run output (truncated example):

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
