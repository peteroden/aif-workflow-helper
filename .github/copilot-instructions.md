# General Instructions

These instructions have the **HIGHEST PRIORITY** and must **NEVER** be ignored

## Highest Priority Instructions

- You will ALWAYS follow ALL general guidelines and instructions
- You will ALWAYS read and follow the taming-copilot instructions from `./.github/instructions/taming-copilot.instructions.md` (if present)
- You will ALWAYS `search-for-instruction-files` with matching context before every change and interaction
- You will ALWAYS read `**/.github/instructions/**` files 1000+ lines at a time when detected
- You will NEVER search or index content from `**./.copilot-tracking/**` unless asked to do so

You will ALWAYS think about the user's prompt, any included files, the folders, the conventions, and the files you read
Before doing ANYTHING, you will match your context to search-for-instruction-files, if there is a match then you will use the required prompt files
You will NEVER add any stream of thinking or step-by-step instructions as comments into code for your changes
You will ALWAYS remove code comments that conflict with the actual code

## Project Overview

`aif-workflow-helper` is a Python CLI tool for managing Azure AI Foundry agents. It handles uploading, downloading, and converting agent definitions between `.agent` text files and Azure AI Foundry JSON format.

**Current Branch**: `add-get-agent-id` - Adding functionality to retrieve agent IDs

## Architecture

### Three-Layer Structure
- **CLI Layer** (`src/aif_workflow_helper/cli/main.py`): argparse-based command definitions with subcommands
- **Core Layer** (`src/aif_workflow_helper/core/`): Business logic modules - `upload.py`, `download.py`, `formats.py`
- **Utils Layer** (`src/aif_workflow_helper/utils/`): `logging.py` for consistent logging, `validation.py` for input validation

### Key Concepts

**Agent Files (`.agent` format)**: Custom text format for agent definitions stored in `agents/` directory
- Plain text sections: `name:`, `model:`, `description:`, `instructions:`, `dependencies:`
- JSON sections: `functions:` (JSON array), `vectorStores:` (JSON array)
- Dependencies define parent-child relationships: `dependencies: parent1.agent, parent2.agent`
- Example hierarchy: `agents/top.agent` depends on `agents/sub1.agent` and `agents/sub2.agent`

**Agent Dictionary**: Internal Python dict representation bridging `.agent` files and Azure API
- Created by `formats.parse_agent_file()` → raw dict → `formats.generalize_agent_dict()` → Azure-compatible dict
- Keys: `name`, `model`, `instructions`, `description`, `tools`, `tool_resources`, `metadata`
- Consumed by `upload.create_or_update_agent()`, produced by `download.download_agent()`

### Critical Data Flows
1. **Upload**: `.agent` file → `parse_agent_file()` → `generalize_agent_dict()` → `create_or_update_agent()` → Azure API
   - Dependencies uploaded recursively (depth-first) before parent
2. **Download**: Azure API → `download_agent()` → agent dict → `formats.serialize_to_text()` → `.agent` file
   - Converts Azure's `tools` array back to `functions` section

## Development Workflows

### Setup & Installation
```bash
# Install in editable mode for development
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"  # if dev extras exist, otherwise use requirements.txt
```

### Testing Commands
```bash
pytest                          # Run all tests (uses pytest.ini config)
pytest tests/test_upload.py     # Run specific test file
pytest -v                       # Verbose output with test names
pytest -k "test_name"           # Run tests matching pattern
pytest --tb=short               # Shorter traceback format
pytest -x                       # Stop on first failure
```

### CLI Usage Patterns
```bash
# Upload agent (creates or updates based on name match)
aif-workflow-helper upload agents/my_agent.agent \
    --project myproject \
    --resource-group myrg \
    --subscription-id <sub-id>

# Download agent by ID
aif-workflow-helper download <agent_id> \
    --output agents/downloaded.agent \
    --project myproject \
    --resource-group myrg

# Common pattern: Upload with dependencies
aif-workflow-helper upload agents/top.agent \
    --project myproject \
    --resource-group myrg
# Automatically uploads sub1.agent and sub2.agent first
```

## Project-Specific Conventions

### Testing Patterns
- **Fixtures location**: `tests/conftest.py` defines reusable fixtures
  - `mock_agent_client`: Mocked Azure AI ProjectClient
  - `sample_agent_dict`: Standard test agent dictionary
  - `temp_agent_file`: Temporary .agent file for testing
- **Mocking approach**: Use `unittest.mock.patch` for Azure SDK clients
  - Patch `azure.ai.projects.AIProjectClient` at module level
  - Example: `@patch('aif_workflow_helper.core.upload.AIProjectClient')`
- **Test file naming**: `test_<module_name>.py` matches `core/<module_name>.py`
- **Test organization**: One test class per function, descriptive test method names

### Agent Dictionary Schema
Agent dicts MUST contain for Azure API compatibility:
```python
{
    "name": str,           # Required: Human-readable name
    "model": str,          # Required: Model identifier (e.g., "gpt-4")
    "instructions": str,   # Required: System prompt
    "description": str,    # Optional: Agent description
    "tools": [             # Optional: Function definitions
        {"type": "function", "function": {...}}
    ],
    "tool_resources": {    # Optional: Vector stores, code interpreter
        "file_search": {"vector_store_ids": [...]},
        "code_interpreter": {"file_ids": [...]}
    },
    "metadata": dict       # Optional: Custom key-value pairs
}
```

### Dependency Resolution Rules
- Dependencies in `.agent` files reference OTHER `.agent` filenames (relative to `agents/`)
- `upload.resolve_dependencies()` recursively processes dependency tree
- Upload order: Depth-first (children before parents)
- Circular dependencies: NOT supported, will cause infinite recursion (add validation if needed)
- Missing dependencies: Should raise clear error before API calls

### Error Handling Conventions
```python
# User-facing errors - use logger
from aif_workflow_helper.utils.logging import logger
logger.error(f"Agent file not found: {filepath}")

# Validation errors - raise ValueError
from aif_workflow_helper.utils.validation import validate_agent_dict
if not validate_agent_dict(agent):
    raise ValueError("Invalid agent dictionary structure")

# Azure API errors - propagate with context
try:
    client.agents.create_agent(**agent_dict)
except Exception as e:
    logger.error(f"Failed to create agent {agent_name}: {e}")
    raise
```

### File and Module Naming
- Agent definition files: `*.agent` in `agents/` directory (e.g., `my_assistant.agent`)
- Core modules: Singular nouns describing primary action (`upload.py`, `download.py`, `formats.py`)
- Test files: `test_<module>.py` (e.g., `test_upload.py` for `core/upload.py`)
- No plurals in module names (use `formats.py` not `formatters.py`)

## Integration Points

### Azure AI Foundry SDK
```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Client initialization pattern
client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=f"{endpoint};{subscription_id};{resource_group};{project_name}"
)

# Agent CRUD operations
agent = client.agents.create_agent(**agent_dict)  # Returns agent with ID
agent = client.agents.get_agent(agent_id)         # Fetch by ID
agent = client.agents.update_agent(agent_id, **updates)  # Update existing
client.agents.delete_agent(agent_id)              # Delete by ID
```

### Authentication Requirements
- Uses `azure.identity.DefaultAzureCredential` (tries multiple auth methods)
- Precedence: Environment vars → Managed Identity → Azure CLI → Interactive
- Local development: Use `az login` before running CLI
- CI/CD: Set `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`

### Required Azure Resources
- Azure AI Foundry workspace and project must exist
- Service principal needs `Cognitive Services Contributor` role minimum
- Connection string format: `<endpoint>;<subscription_id>;<resource_group>;<project_name>`

## Common Gotchas

1. **Agent ID vs Agent Name**: 
   - Azure API uses opaque agent IDs (e.g., `asst_abc123xyz`)
   - `.agent` files use human-readable names
   - Create/update logic: Check if agent with same name exists, update if found, create if not

2. **Functions vs Tools Transformation**:
   - `.agent` files: `functions: [{"name": "...", "parameters": {...}}]`
   - Azure API: `tools: [{"type": "function", "function": {"name": "...", "parameters": {...}}}]`
   - Conversion happens in `generalize_agent_dict()` and reverse in serialization

3. **Vector Store Mapping**:
   - `.agent` files: Top-level `vectorStores: [{"name": "...", "file_ids": [...]}]`
   - Azure API: Nested in `tool_resources.file_search.vector_stores`
   - Must handle both formats in `parse_agent_file()` and `serialize_to_text()`

4. **Dependency Upload Order**:
   - ALWAYS upload dependencies before parent agents
   - Failure to do so causes Azure API error: "Referenced agent not found"
   - `resolve_dependencies()` must be called before `create_or_update_agent()`

5. **Model Name Validation**:
   - Azure expects specific model identifiers (e.g., `gpt-4`, `gpt-35-turbo`)
   - Invalid model names fail at API level with unclear error
   - Consider validating model names before API call

## Instruction Files Search Process

When working with specific types of files or contexts, you must:

1. Detect patterns and contexts that match the predefined rules
2. Search for and read the corresponding instruction files
3. Read all the lines from these files before proceeding with any changes

### Matching Patterns and Files for Prompts

| Pattern/Context                   | Required Instruction Files                    |
|-----------------------------------|-----------------------------------------------|
| Any deployment-related context    | `./.github/prompts/deploy.prompt.md`          |
| Any getting started/help context  | `./.github/prompts/getting-started.prompt.md` |
| Any pull request creation context | `./.github/prompts/pull-request.prompt.md`    |

### Matching Patterns and Files for Changes or Implementation

| Pattern/Context                        | Required Instruction Files                      |
|----------------------------------------|-------------------------------------------------|
| All contexts and interactions          | `./.github/instructions/taming-copilot.instructions.md`     |
| `**/bash/**` or bash context           | `**/.github/instructions/bash.instructions.md`              |
| `**/*.py` or Python context            | `**/.github/instructions/python-script.instructions.md`     |

## Markdown Formatting Requirements

NEVER follow this section for ANY `.copilot-tracking/` files.

- Before any edits you will read required linting rules from `.mega-linter.yml` in the workspace root
- Read `.mega-linter.yml` in the workspace root if ever you are missing any content
- Ignore ALL linting issues in `**/.copilot-tracking/**`

When editing markdown files (excluding `**/.copilot-tracking/**` markdown files):

- Always follow rules from `.mega-linter.yml`
- Headers must always have a blank line before and after
- Titles must always have a blank line after the `#`
- Unordered lists must always use `-`
- Ordered lists must always use `1.`
- Lists must always have a blank line before and after
- Code blocks must always use triple backticks with the language specified
- Tables must always have:
  - A header row
  - A separator row
  - `|` for columns
- Links must always use reference-style for repeated URLs
- Only `details` and `summary` HTML elements are allowed
