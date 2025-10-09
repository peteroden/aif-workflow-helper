# Code Review Prompt for aif-workflow-helper

## Project Context

This CLI tool manages Azure AI Foundry agents with support for uploading, downloading, and converting agent definitions between `.agent` text files and Azure AI Foundry JSON format. The architecture follows a three-layer pattern: CLI → Core Business Logic → Utilities.

## Review Checklist

### 🏗️ Architecture & Design

- [ ] Follows three-layer architecture (CLI → Core → Utils)
- [ ] Modules placed correctly (`cli/`, `core/`, `utils/`)
- [ ] Separation of concerns preserved (formats vs business logic)
- [ ] Azure interactions abstracted via `SupportsAgents`
- [ ] Backward compatibility of CLI preserved unless documented

### 🔒 Agent Framework Integration

- [ ] Async SDK usage properly wrapped in sync layer
- [ ] Event loop handling safe (no nested loop misuse)
- [ ] `DefaultAzureCredential` used without leaking secrets
- [ ] Resources (client, credential, loop) closed reliably
- [ ] Connected agent alias + ID resolution correct

### 📁 File Format Handling

- [ ] New formats use transformer registry (`core/transformers`)
- [ ] Roundtrip consistency (JSON/YAML/Markdown) maintained
- [ ] Markdown trailing newline preserved (Unix convention)
- [ ] Data types (bool, int, null) preserved in YAML/JSON
- [ ] Unicode + emoji content survives save/load

### 🔗 Connected Agents & Dependencies

- [ ] Alias matches pattern `^[a-zA-Z_]+$`
- [ ] Dependency extraction & topo sort correct
- [ ] `name_from_id` stripped before API submission
- [ ] Child agents created before parents
- [ ] Existing agents list refreshed when needed

### 🧪 Testing

- [ ] Unit tests cover new logic branches
- [ ] Integration tests updated (real service scenarios)
- [ ] Error cases (missing model, invalid name, bad dependency) tested
- [ ] Roundtrip tests extended if format logic changed
- [ ] Edge cases: empty lists, empty instructions, unicode, deep metadata

### 📝 Code Quality

#### Simplicity & Readability
- [ ] Single responsibility functions
- [ ] Descriptive names (no ambiguous abbreviations)
- [ ] No unnecessary abstraction layers
- [ ] Early returns reduce nesting
- [ ] No dead or commented-out code

#### Error Handling
- [ ] User-facing errors logged with context
- [ ] Validation uses `ValueError` with clear messages
- [ ] Azure SDK exceptions wrapped or re-raised meaningfully
- [ ] No blanket `except Exception` without re-raise/log
- [ ] Cleanup executed in finally/ctx managers

#### Performance & Efficiency
- [ ] Avoids redundant list_agents() calls in loops
- [ ] Large file ops efficient (no unnecessary copies)
- [ ] No quadratic behavior in dependency handling
- [ ] Avoids premature optimization

### 🔍 Patterns to Verify

#### Agent Dictionary Schema
```python
{
    "name": str,
    "model": str,
    "instructions": str,
    "description": str | optional,
    "tools": list | optional,
    "tool_resources": dict | optional,
    "metadata": dict | optional
}
```

#### Connected Agent Tool
```python
{
  "type": "connected_agent",
  "connected_agent": {
     "name": "valid_alias",  # ^[A-Za-z_]+$
     "id": "asst_xxx",       # resolved
     "description": "..."     # optional
  }
}
```

#### Error Logging Pattern
```python
try:
    do_thing()
except SpecificError as e:
    logger.error("Failed doing thing %s: %s", ref, e)
    raise
```

### 🚫 Anti-Patterns

- Hardcoded endpoints or deployment names
- Direct mutation of shared dicts without copy
- Mixed formatting logic in core upload/download modules
- Silent exception swallowing
- Long functions (>60 lines) without necessity
- Recomputing dependency graphs per item
- Using placeholder model values without validation path

### 📋 Documentation

- [ ] New CLI flags documented with help text
- [ ] README updated if behavior or usage changes
- [ ] Migration notes updated for breaking shifts
- [ ] Docstrings include Args / Returns / Raises where non-trivial
- [ ] Complex transformations explained inline

### 🏷️ Naming Conventions

- snake_case: functions/variables
- PascalCase: classes
- UPPER_SNAKE_CASE: constants
- Filenames: lowercase, no spaces
- Transformers: <format>_transformer.py

### ⚡ Performance Considerations

- Batching when practical
- No excessive per-file re-parsing
- Only resolves agent IDs once per batch when possible

### 🔐 Security

- [ ] No secrets logged
- [ ] Environment access guarded (fallbacks explicit)
- [ ] File paths not user-injected without validation
- [ ] No exposure of internal Azure IDs unless required

### Final Reviewer Questions

1. Is there a simpler implementation?  
2. Are responsibilities clearly owned?  
3. Are failure modes predictable and logged?  
4. Does this introduce tech debt that needs an issue?  
5. Do tests demonstrate correctness or only happy paths?

### Approval Gate

All must be true:
- ✅ All relevant checklist items satisfied
- ✅ Tests (unit + integration) pass locally/CI
- ✅ No silent behavioral changes undocumented
- ✅ Public surface stays stable or changes are documented
- ✅ Code is clear enough to modify in 6 months without archeology

