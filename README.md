# Azure AI Foundry Workflow Helpers

Utilities for exporting (downloading) and importing (creating/updating) Azure AI Foundry Agents along with dependency awareness, normalization, and consistent logging.

## 🚀 Quick Start

### 1. Set Environment Variables

```bash
export AZURE_TENANT_ID='your-tenant-id-here'
export PROJECT_ENDPOINT='your-ai-foundry-endpoint-here'
```

**Example:**

```bash
export AZURE_TENANT_ID='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
export PROJECT_ENDPOINT='https://your-resource.services.ai.azure.com/api/projects/your-project'
```

> **Note:** You can also provide these values via CLI parameters (`--azure-tenant-id` and `--project-endpoint`) which will take precedence over environment variables.

### 2. Install the Package

For development (editable install):

```bash
pip install -e .
```

Or for production:

```bash
pip install .
```

This will install all required dependencies automatically.

### 3. Using the CLI (Recommended)

The CLI is available as a console script after installation.

```bash
aif-workflow-helper --download-all-agents --agents-dir agents
```

Common examples:

```bash
# Download all agents with optional prefix/suffix filtering
aif-workflow-helper --download-all-agents --prefix dev- --suffix -v1

# Download a single agent
aif-workflow-helper --download-agent my_agent

# Upload all agents from JSON definitions in a directory
aif-workflow-helper --upload-all-agents --agents-dir agents

# Upload a single agent definition file
aif-workflow-helper --upload-agent my_agent --agents-dir agents

# Get the agent ID for a specific agent by name
aif-workflow-helper --get-agent-id my_agent

# Download agents in different formats
aif-workflow-helper --download-all-agents --format json     # Default
aif-workflow-helper --download-all-agents --format yaml     # YAML format
aif-workflow-helper --download-all-agents --format md       # Markdown with frontmatter

# Upload agents from different formats
aif-workflow-helper --upload-all-agents --format yaml
aif-workflow-helper --upload-agent my_agent --format md

# Change log level
aif-workflow-helper --download-all-agents --log-level DEBUG

# Override environment variables with CLI parameters
aif-workflow-helper --download-all-agents \
  --azure-tenant-id "your-tenant-id" \
  --project-endpoint "https://your-endpoint.services.ai.azure.com/api/projects/your-project"

# Mix CLI parameters with environment variables (CLI takes precedence)
export AZURE_TENANT_ID="env-tenant-id"
aif-workflow-helper --download-all-agents --azure-tenant-id "cli-tenant-id"  # Uses CLI value

# Get agent ID and use in scripts
AGENT_ID=$(aif-workflow-helper --get-agent-id my_agent)
echo "Agent ID: $AGENT_ID"
```

### 4. Direct Library Usage

You can import and compose the underlying functions directly:

```python
from aif_workflow_helper import (
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

`aif-workflow-helper` arguments:

```text
--agents-dir DIR                Directory for agent definition files (default: agents)
--download-all-agents           Download all existing agents
--download-agent NAME           Download a single agent by name
--upload-all-agents             Create/update all agents from definition files
--upload-agent NAME             Create/update a single agent from definition file
--get-agent-id NAME             Get the agent ID for a given agent name
--prefix TEXT                   Optional prefix applied during download/upload
--suffix TEXT                   Optional suffix applied during download/upload
--format FORMAT                 File format: json, yaml, or md (default: json)
--log-level LEVEL               Logging level (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET)
--azure-tenant-id TENANT_ID     Azure tenant ID (overrides AZURE_TENANT_ID environment variable)
--project-endpoint ENDPOINT     AI Foundry project endpoint URL (overrides PROJECT_ENDPOINT environment variable)
```

### Authentication Priority

1. **CLI Parameters** (highest priority): `--azure-tenant-id` and `--project-endpoint`
2. **Environment Variables** (fallback): `AZURE_TENANT_ID` and `PROJECT_ENDPOINT`

## � Agent Lookup

### Get Agent ID by Name

The `--get-agent-id` option allows you to retrieve the unique ID of an agent by its name. This is useful for scripting and automation scenarios where you need to reference an agent by its ID rather than its name.

**Usage:**

```bash
# Get agent ID
aif-workflow-helper --get-agent-id my-agent

# Use in a script
AGENT_ID=$(aif-workflow-helper --get-agent-id my-agent)
echo "Agent ID: $AGENT_ID"

# With explicit authentication
aif-workflow-helper --get-agent-id my-agent \
  --azure-tenant-id "your-tenant-id" \
  --project-endpoint "your-endpoint"
```

**Output:**

- On success: Prints the agent ID to stdout (suitable for capturing in scripts)
- On failure: Logs an error message and exits with code 1

**Example Output:**

```text
========== Looking up agent: my-agent ==========
asst_abc123xyz456
========== Agent 'my-agent' has ID: asst_abc123xyz456 ==========
```

## �📄 Supported File Formats

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
├── pyproject.toml               # Package configuration and dependencies
├── requirements.txt             # Core runtime dependencies
├── README.md                    # Project documentation
├── agents/                      # Agent definition files
├── tests/                       # Test files
└── src/aif_workflow_helper/     # Main package source code
    ├── __init__.py              # Public exports
    ├── cli/
    │   └── main.py              # CLI entrypoint
    ├── core/
    │   ├── upload.py            # Upload + dependency logic
    │   ├── download.py          # Download + generalization logic
    │   └── formats.py           # Format handling utilities
    └── utils/
        ├── logging.py           # Shared logging configuration
        └── validation.py        # Agent name validation
```

## ⚠️ Important Notes

1. **Authentication**: Uses `DefaultAzureCredential` (interactive fallback enabled)
2. **Dependency Ordering**: Creates/updates in safe order via topological sort
3. **Name Safety**: Validation ensures only alphanumerics + hyphens (prefix/suffix applied consistently)
4. **Logging**: Centralized configurable logger (`configure_logging`)
5. **Efficiency**: Minimizes duplicate lookups by caching existing agents during batch operations
6. **Format Flexibility**: Supports JSON, YAML, and Markdown with frontmatter for different workflow preferences

## 🔍 Troubleshooting

### Installation Issues

```bash
# Install in development mode for local changes
pip install -e .

# Or install for production use
pip install .
```

### Authentication Errors

```bash
# Check environment variables
echo $AZURE_TENANT_ID
echo $PROJECT_ENDPOINT

# Or use CLI parameters (recommended for CI/CD or when environment variables conflict)
aif-workflow-helper --download-all-agents \
  --azure-tenant-id "your-tenant-id" \
  --project-endpoint "your-endpoint"

# Try interactive login
az login --tenant $AZURE_TENANT_ID
```

### Command Not Found Error

If `aif-workflow-helper` is not found after installation:

```bash
# Make sure you installed the package
pip install -e .

# Check if it's in your PATH
which aif-workflow-helper

# Or run directly with Python
python -m aif_workflow_helper.cli.main --help
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

## 🔄 CI/CD Pipeline

This project includes a comprehensive CI/CD pipeline using GitHub Actions that ensures code quality and functionality.

### Pipeline Features

- **Multi-Python Version Testing**: Tests on Python 3.10, 3.11, and 3.12
- **Automated Testing**: Runs all pytest tests with coverage reporting
- **Code Quality**: Includes linting with flake8
- **Package Testing**: Verifies the package can be built and installed correctly
- **CLI Testing**: Ensures the command-line interface works after installation

### Branch Protection

The main branch is protected with the following requirements:

- ✅ **Pull Request Required**: Direct pushes to main are not allowed
- ✅ **Tests Must Pass**: All CI checks must pass before merging
- ✅ **Code Review**: At least 1 approval required
- ✅ **Up-to-date Branch**: Branches must be current with main

### Running Tests Locally

Before submitting a PR, run tests locally to ensure they pass:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install with dev dependencies
pip install -e .[dev]

# Run tests
pytest tests/ -v --tb=short

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Check CLI functionality
aif-workflow-helper --help
```

### Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all tests pass locally
4. Submit a pull request
5. Wait for CI to pass and get code review approval
6. Merge when approved
