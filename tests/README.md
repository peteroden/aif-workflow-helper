# Testing Guide

This directory contains comprehensive unit tests for the `aif_workflow_helpers` package, organized into multiple focused test files.

## Test Structure

The test suite is organized into the following files:

- **`conftest.py`**: Shared test fixtures and configuration
- **`test_agent_helpers.py`**: Tests for helper functions (`get_agent_name`, `get_agent_by_name`)
- **`test_data_processing.py`**: Tests for data processing functions (`generalize_agent_dict`, `read_agent_files`, `download_agents`, `download_agent`)
- **`test_dependencies.py`**: Tests for dependency management (`extract_dependencies`, `dependency_sort`)
- **`test_agent_operations.py`**: Tests for agent CRUD operations (`create_or_update_agent`, `create_or_update_agents`)
- **`test_main.py`**: Tests for the main function and end-to-end scenarios

## Prerequisites

Install the required testing dependencies:

```bash
pip install pytest pytest-cov pytest-mock
```

Or install all development dependencies:

```bash
pip install -e ".[dev]"
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
# Test only helper functions
pytest tests/test_agent_helpers.py

# Test only data processing
pytest tests/test_data_processing.py

# Test only dependency management
pytest tests/test_dependencies.py

# Test only agent operations
pytest tests/test_agent_operations.py

# Test only main function
pytest tests/test_main.py
```

### Run Specific Test Classes or Methods

```bash
# Run all tests in a specific class
pytest tests/test_agent_helpers.py::TestGetAgentName

# Run a specific test method
pytest tests/test_agent_helpers.py::TestGetAgentName::test_get_agent_name_success
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest --cov=aif_workflow_helpers --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html
```

### Run Tests with Different Verbosity Levels

```bash
# Verbose output
pytest -v

# Extra verbose output
pytest -vv

# Quiet output
pytest -q
```

## Test Fixtures

The `conftest.py` file provides shared fixtures used across multiple test files:

- **`mock_agent_client`**: Mock Azure Agents client
- **`sample_agent`**: Sample agent object for testing
- **`sample_agent_with_connected_agent`**: Agent with connected agent dependency
- **`sample_agent_data`**: Sample agent data dictionary
- **`sample_agent_data_with_dependency`**: Agent data with dependency
- **`agents_data_with_dependencies`**: Complex dependency graph for testing
- **`mock_environment_variables`**: Mock environment variables

## Test Categories

### Unit Tests

All tests are unit tests that mock external dependencies (Azure SDK, file system operations, etc.).

### Test Coverage Areas

1. **Helper Functions**:
   - Agent retrieval by ID and name
   - Error handling for API failures
   - Edge cases (missing agents, null values)

2. **Data Processing**:
   - Agent data generalization and cleanup
   - Connected agent reference resolution
   - File I/O operations
   - JSON parsing and validation

3. **Dependency Management**:
   - Dependency extraction from agent configurations
   - Topological sorting for creation order
   - Circular dependency detection
   - Complex dependency graphs

4. **Agent Operations**:
   - Agent creation and updates
   - Dependency resolution during creation
   - Error handling during CRUD operations
   - Batch operations

5. **Main Function**:
   - Environment variable validation
   - End-to-end workflow testing
   - Error scenarios and recovery

## Mocking Strategy

The tests use extensive mocking to isolate units of code and avoid dependencies on:

- Azure AI Agents API
- File system operations
- Environment variables
- Network calls

This ensures tests run quickly and reliably without external dependencies.

## Best Practices

1. **Isolated Tests**: Each test is independent and doesn't rely on other tests
2. **Clear Naming**: Test names clearly describe what they're testing
3. **Comprehensive Coverage**: Tests cover happy paths, error cases, and edge cases
4. **Mocked Dependencies**: External dependencies are mocked to ensure reliability
5. **Organized Structure**: Tests are organized by functionality for easy maintenance

## Adding New Tests

When adding new functionality to the main code:

1. Add tests to the appropriate test file based on functionality
2. Use existing fixtures from `conftest.py` when possible
3. Create new fixtures if needed for reusability
4. Follow the existing naming and organization patterns
5. Test both success and failure scenarios

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the package is installed in development mode: `pip install -e .`
2. **Missing Dependencies**: Install test dependencies: `pip install pytest pytest-cov pytest-mock`
3. **Path Issues**: Run tests from the project root directory
4. **Fixture Not Found**: Check that fixtures are properly defined in `conftest.py`

### Running Individual Test Modules

If you encounter issues running all tests, you can run individual modules:

```bash
python -m pytest tests/test_agent_helpers.py
python -m pytest tests/test_data_processing.py
python -m pytest tests/test_dependencies.py
python -m pytest tests/test_agent_operations.py
python -m pytest tests/test_main.py
```
