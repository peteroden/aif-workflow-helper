# General Instructions

These instructions have the **HIGHEST PRIORITY** and must **NEVER** be ignored

## Highest Priority Instructions

- You will ALWAYS follow ALL general guidelines and instructions
- You will ALWAYS `search-for-copilot-files` with matching context before every change and interaction
- You will ALWAYS read `**/copilot/**` files 1000+ lines at a time when detected
- You will NEVER search or index content from `**./.copilot-tracking/**` unless asked to do so

You will ALWAYS think about the user's prompt, any included files, the folders, the conventions, and the files you read
Before doing ANYTHING, you will match your context to search-for-copilot-files, if there is a match then you will use the required prompt files
You will NEVER add any stream of thinking or step-by-step instructions as comments into code for your changes
You will ALWAYS remove code comments that conflict with the actual code

<!-- <search-for-copilot-files> -->
## Copilot Files Search Process

When working with specific types of files or contexts, you must:

1. Detect patterns and contexts that match the predefined rules
2. Search for and read the corresponding copilot files
3. Read all the lines from these files before proceeding with any changes

### Matching Patterns and Files for Prompts

| Pattern/Context                   | Required Copilot Files                        |
|-----------------------------------|-----------------------------------------------|
| Any deployment-related context    | `./.github/prompts/deploy.prompt.md`          |
| Any getting started/help context  | `./.github/prompts/getting-started.prompt.md` |
| Any pull request creation context | `./.github/prompts/pull-request.prompt.md`    |

### Matching Patterns and Files for Changes or Implementation

| Pattern/Context                        | Required Copilot Files        |
|----------------------------------------|-------------------------------|
| `**/terraform/**` or terraform context | `**/copilot/terraform/**`     |
| `**/bicep/**` or bicep context         | `**/copilot/bicep/**`         |
| `**/bash/**` or bash context           | `**/copilot/bash/**`          |
| `**/*.py` or Python context            | `**/copilot/python-script.md` |

### Internal Modules

- Template: `{component}/modules/{internal_module}`
- Internal modules can be files or folders depending on the framework
- Rules for internal modules:
  - Internal modules are ONLY referenced from their component
  - Internal modules are NEVER referenced outside their component
- Examples:
  - `**/terraform/modules/identity`
  - `**/bicep/modules/identity.bicep`

### Conventions

- Always follow existing patterns for a component when working within a component directory
- Reference existing components when needed:
  - `**/src/000-cloud/010-security-identity`
  - `**/src/100-edge/110-iot-ops`

## Markdown Formatting Requirements

NEVER follow this section for ANY `.copilot-tracking/` files.

- Before any edits you will read required linting rules from #file:../.mega-linter.yml in the workspace root
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
