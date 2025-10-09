# Azure AI Foundry Workflow Helpers

Utilities for exporting (downloading) and importing (creating/updating) Azure AI Foundry Agents along with dependency awareness, normalization, and consistent logging.

## 🚀 Quick Start

### 1. Set Environment Variables

```bash
export AZURE_TENANT_ID='your-tenant-id-here'
export AZURE_AI_PROJECT_ENDPOINT='your-ai-foundry-endpoint-here'
export AZURE_AI_MODEL_DEPLOYMENT_NAME='your-default-model-deployment'
```

**Example:**

```bash
export AZURE_TENANT_ID='aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
export AZURE_AI_PROJECT_ENDPOINT='https://your-resource.services.ai.azure.com/api/projects/your-project'
export AZURE_AI_MODEL_DEPLOYMENT_NAME='gpt-4o-preview'
```

> **Note:** You can also provide these values via CLI parameters (`--azure-tenant-id`, `--project-endpoint`, and `--model-deployment-name`) which take precedence over environment variables. The legacy `PROJECT_ENDPOINT` variable is still honored as a fallback when `AZURE_AI_PROJECT_ENDPOINT` is unset.

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

# Delete a single agent (with confirmation prompt)
aif-workflow-helper --delete-agent my_agent

# Delete a single agent without confirmation
aif-workflow-helper --delete-agent my_agent --force

# Delete all agents with prefix/suffix filtering (with confirmation)
aif-workflow-helper --delete-all-agents --prefix dev- --suffix -v1

# Delete all agents without confirmation (DANGEROUS!)
aif-workflow-helper --delete-all-agents --force

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
from aif_workflow_helper.core.agent_framework_client import AgentFrameworkAgentsClient

configure_logging()

client = AgentFrameworkAgentsClient(
  project_endpoint="your-endpoint",
  tenant_id="your-tenant-id",
  model_deployment_name="your-model-deployment",
)

# Bulk download
download_agents(client, file_path="./agents", prefix="", suffix="", format="json")

# Create/update from a directory (dependency ordered)
create_or_update_agents_from_files(path="./agents", agent_client=client, prefix="", suffix="", format="json")
```

### 5. Architecture & Client Abstraction

This project uses modern Python architecture patterns for maintainability and extensibility:

#### Protocol-Based Design

The codebase intentionally depends on a *structural protocol* (`SupportsAgents`) instead of the concrete Azure SDK `AgentsClient`. A lightweight synchronous wrapper `AgentFrameworkAgentsClient` adapts the Agent Framework (async) SDK to this protocol. This yields:

- **Decoupling**: Core upload/download/delete logic only relies on the handful of methods it needs (`list_agents`, `create_agent`, `update_agent`, `get_agent`, `delete_agent`).
- **Testability**: In-memory test doubles implement the protocol without inheriting from any SDK classes.
- **Forward Migration**: An eventual shift to native async (e.g. an `AsyncSupportsAgents` protocol) can happen without rewriting business logic.

If you want to provide your own backend, implement the same method names and return objects exposing `id`, `name`, and `as_dict()`.

#### Type Safety & Code Quality

- **Full Type Annotations**: All functions and methods include complete type hints for improved IDE support and error detection
- **Static Type Checking**: Configured with `mypy` for strict type checking (enforced in CI)
- **Modern Linting**: Uses `ruff` for fast, comprehensive code quality checks
- **Protocol Typing**: Leverages Python's structural subtyping for flexible yet type-safe interfaces

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
--delete-agent NAME             Delete a single agent by name
--delete-all-agents             Delete all agents (filtered by prefix/suffix if provided)
--force                         Skip confirmation prompts when deleting agents
--prefix TEXT                   Optional prefix applied during download/upload/delete
--suffix TEXT                   Optional suffix applied during download/upload/delete
--format FORMAT                 File format: json, yaml, or md (default: json)
--log-level LEVEL               Logging level (CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET)
--azure-tenant-id TENANT_ID     Azure tenant ID (overrides AZURE_TENANT_ID environment variable)
--project-endpoint ENDPOINT     AI Foundry project endpoint URL (overrides AZURE_AI_PROJECT_ENDPOINT/PROJECT_ENDPOINT)
--model-deployment-name NAME    Default model deployment name (overrides AZURE_AI_MODEL_DEPLOYMENT_NAME)
```

### Authentication Priority

1. **CLI Parameters** (highest priority): `--azure-tenant-id`, `--project-endpoint`, and `--model-deployment-name`
2. **Environment Variables** (fallback): `AZURE_TENANT_ID`, `AZURE_AI_PROJECT_ENDPOINT` (or legacy `PROJECT_ENDPOINT`), and `AZURE_AI_MODEL_DEPLOYMENT_NAME`

## 🧠 Per-Agent Models & Retry Behavior

### Model Resolution Order

When creating or updating an agent the model deployment used follows this precedence:

1. Explicit model defined inside the agent definition file (JSON/YAML/Markdown) under `model`
2. CLI parameter `--model-deployment-name`
3. Environment variable `AZURE_AI_MODEL_DEPLOYMENT_NAME`
4. Fallback placeholder value `default` (a warning is logged – you almost always want to supply a real deployment)

This means you can mix strategies: set a global default via env/CLI and override only specific agents that require a specialized deployment.

### Why Per-Agent Models Matter

- Different capability tiers (e.g. reasoning vs standard) for different agents
- Cost optimization – lightweight model for routing agents, larger model for planners
- Incremental migration – trial a new deployment on a subset of agents before broad rollout

### Retry & Resilience

Transient Azure/network failures are automatically retried with exponential backoff. You can tune this without code changes:

Environment variables:

- `AIF_RETRY_ATTEMPTS` – Total retry attempts (default: 3)
- `AIF_RETRY_BASE_DELAY` – Initial delay in seconds before first retry (default: 0.5)

Backoff strategy roughly: `delay = base * (2 ** (attempt - 1)) + jitter`.

Example tuning for slower environments:

```bash
export AIF_RETRY_ATTEMPTS=5
export AIF_RETRY_BASE_DELAY=1.0
```

You will see INFO/WARNING logs indicating retry attempts and final failure if exhausted.

### Recommended Practices

- Always set a real model deployment globally (env or CLI)
- Use per-agent overrides sparingly and document why the override exists
- Monitor logs for the placeholder `default` warning – that usually signals a configuration gap

## 🧩 Connected Agent Alias Normalization

Agents may reference other agents via connected agent tools (dependencies). The service enforces an identifier-style pattern for alias names. To keep uploads resilient the tool automatically normalizes aliases:

Normalization rules:

- Any character not matching `[A-Za-z0-9_]` is replaced with `_`
- Aliases are trimmed (no leading/trailing whitespace)
- Multiple consecutive invalid characters collapse to single `_`
- A leading digit is prefixed with `_` to satisfy identifier constraints

Example transformations:

| Original Alias        | Normalized Alias |
|-----------------------|------------------|
| `pricing-api`         | `pricing_api`    |
| `customer-support`    | `customer_support` |
| `orchestration@root`  | `orchestration_root` |
| `123planner`          | `_123planner`    |
| `chat/assist+core`    | `chat_assist_core` |

### Resolution & Warnings

During upload the tool attempts to resolve connected agents **by name (post prefix/suffix application)**. If an agent reference cannot be resolved:

- A WARNING is logged: unresolved connected agent name
- The unresolved reference is skipped (not fatal – allows partial graph deployment)

To enforce strictness you can add a CI policy that fails on the presence of these warnings (future enhancement could introduce a `--strict-dependencies` flag).

### Practical Tips

- Keep aliases simple and service-friendly from the start to avoid renames
- Use consistent naming conventions (e.g. snake_case) across your team
- After a bulk download → modify → re-upload cycle, expect aliases to already appear normalized

### Troubleshooting Unresolved Dependencies

Common causes:

- Misspelled agent name in the referencing agent file
- Missing prefix/suffix when running upload compared to how agents were originally created
- Upload order manipulated manually (let the bulk upload handle ordering)

Fix strategy:

1. Verify the target agent file exists in the directory
2. Confirm the final computed name (prefix + base + suffix) matches what the reference expects
3. Re-run with `--log-level DEBUG` to see raw dependency resolution steps

If still unresolved, download existing agents and compare normalized names to your references.

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
  --project-endpoint "your-endpoint" \
  --model-deployment-name "your-model-deployment"
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

## 🗑️ Deleting Agents

### Delete a Single Agent

Delete an agent by name with an interactive confirmation prompt:

```bash
# Delete with confirmation prompt
aif-workflow-helper --delete-agent my-agent

# Skip confirmation prompt with --force flag
aif-workflow-helper --delete-agent my-agent --force

# Delete agent with prefix/suffix
aif-workflow-helper --delete-agent my-agent --prefix dev- --suffix -v1
```

**Interactive Confirmation Example:**

```text
The following agents will be deleted:
  - my-agent

Total: 1 agent(s)

Are you sure you want to delete these agents? (yes/no): yes
========== Successfully deleted agent 'my-agent' (ID: asst_abc123xyz) ==========
```

### Delete Multiple Agents

Delete all agents matching a prefix/suffix pattern:

```bash
# Delete all agents starting with "dev-" (with confirmation)
aif-workflow-helper --delete-all-agents --prefix dev-

# Delete all agents ending with "-v1" (with confirmation)
aif-workflow-helper --delete-all-agents --suffix -v1

# Delete all agents with both prefix and suffix (with confirmation)
aif-workflow-helper --delete-all-agents --prefix staging- --suffix -test

# Delete all agents without confirmation (DANGEROUS!)
aif-workflow-helper --delete-all-agents --force

# Delete all matching agents without confirmation
aif-workflow-helper --delete-all-agents --prefix dev- --suffix -v1 --force
```

**Interactive Confirmation Example:**

```text
The following agents will be deleted:
  - dev-agent-1-v1
  - dev-agent-2-v1
  - dev-worker-v1

Total: 3 agent(s)

Are you sure you want to delete these agents? (yes/no): yes
========== Deleted agent 'dev-agent-1-v1' (ID: asst_abc123) ==========
========== Deleted agent 'dev-agent-2-v1' (ID: asst_def456) ==========
========== Deleted agent 'dev-worker-v1' (ID: asst_ghi789) ==========
========== Successfully deleted 3 of 3 agent(s) ==========
```

**Safety Features:**

- **Confirmation Prompt**: By default, you'll be asked to confirm before any deletion
- **--force Flag**: Skip confirmation for automated scripts (use with caution!)
- **Prefix/Suffix Filtering**: Target specific agents by name pattern
- **Detailed Logging**: See exactly which agents will be deleted before confirming

**⚠️ Warning:** Deletion is permanent and cannot be undone. Always double-check the agent names before confirming deletion.

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

**Markdown Format Behavior:**

- **Trailing Newlines**: The markdown format preserves trailing newlines in the instructions content to maintain exact formatting across upload/download cycles. All markdown files end with a newline character following Unix text file conventions.
- **Frontmatter Library**: The tool uses the `python-frontmatter` library, which strips trailing newlines from content when reading. The tool automatically detects and restores these newlines to ensure perfect roundtrip consistency.
- **Multi-line Fields**: YAML frontmatter fields (like `description`) can use multi-line string syntax for better readability.

**File Extensions:**

- JSON: `.json`
- YAML: `.yaml` or `.yml`
- Markdown: `.md`

## 📋 File Structure

```text
├── pyproject.toml               # Project configuration & dependencies (uv managed)
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
7. **Roundtrip Consistency**: All formats support perfect roundtrip consistency - downloading and re-uploading an agent produces identical results. This includes:
   - Preserving trailing newlines in markdown format
   - Maintaining exact data types (numbers, booleans, nulls) in JSON/YAML
   - Preserving complex nested structures and metadata
   - Handling unicode characters and emojis correctly

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
echo $AZURE_AI_PROJECT_ENDPOINT
echo $AZURE_AI_MODEL_DEPLOYMENT_NAME

# Or use CLI parameters (recommended for CI/CD or when environment variables conflict)
aif-workflow-helper --download-all-agents \
  --azure-tenant-id "your-tenant-id" \
  --project-endpoint "your-endpoint" \
  --model-deployment-name "your-model-deployment"

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
- **Code Quality**: Includes linting with `ruff` and type checking with `mypy`
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

# Run type checking
mypy src/

# Run linting
ruff check .

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
