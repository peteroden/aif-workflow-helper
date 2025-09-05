import pytest

from src.core.upload import (
    extract_dependencies,
    dependency_sort,
)
from src.utils.logging import configure_logging
from . import test_consts

configure_logging(propagate=True)


def test_extract_no_dependencies():
    assert extract_dependencies(test_consts.TEST_AGENT_DATA_GOOD_NO_DEPENDENCIES) == {}


def test_extract_single_dependency():
    assert extract_dependencies(test_consts.TEST_AGENT_DATA_GOOD_SINGLE_DEPENDENCY) == {"agent-b": {"agent-a"}}


def test_extract_multiple_dependencies():
    assert extract_dependencies(test_consts.TEST_AGENT_DATA_GOOD_MULTIPLE_DEPENDENCIES) == {"agent-g": {"agent-e", "agent-f"}}


def test_extract_unknown_agent_ignored():
    assert extract_dependencies(test_consts.TEST_AGENT_DATA_UNKNOWN_AGENT) == {}


def test_extract_missing_name_from_id():
    assert extract_dependencies(test_consts.TEST_AGENT_DATA_MISSING_NAME_FROM_ID) == {}


def test_extract_mixed_tool_types():
    assert extract_dependencies(test_consts.TEST_AGENT_DATA_MIXED_TOOLS) == {"agent-a": {"agent-b"}}


def test_extract_tools_not_list():
    assert extract_dependencies(test_consts.TEST_AGENT_DATA_NO_TOOLS) == {}


def test_extract_tool_entry_not_dict():
    assert extract_dependencies(test_consts.TEST_AGENT_DATA_MALFORMED_TOOLS) == {}


def test_extract_connected_agent_not_dict():
    assert extract_dependencies(test_consts.TEST_AGENT_DATA_MALFORMED_CONNECTED_AGENT) == {}


def test_extract_dependencies_empty():
    assert extract_dependencies({}) == {}


def test_extract_dependencies_simple():
    deps = extract_dependencies(test_consts.TEST_AGENT_DATA_GOOD_SINGLE_DEPENDENCY)
    assert deps == {'agent-b': {'agent-a'}}

def test_sort_no_dependencies():
    order = dependency_sort(test_consts.TEST_AGENT_DATA_GOOD_MULTIPLE_NO_DEPENDENCIES)
    assert set(order) == {"agent-a", "agent-b", "agent-c"}
    assert len(order) == 3


def test_sort_linear_chain():
    assert dependency_sort(test_consts.TEST_AGENT_DATA_GOOD_LINEAR_CHAIN) == ["agent-a", "agent-b", "agent-c"]


def test_sort_complex_graph():
    order = dependency_sort(test_consts.TEST_AGENT_DATA_GOOD_COMPLEX_DEPENDENCIES)
    assert set(order) == {"agent-a", "agent-b", "agent-c", "agent-d"}


def test_sort_independent_groups():
    order = dependency_sort({**test_consts.TEST_AGENT_DATA_GOOD_SINGLE_DEPENDENCY, **test_consts.TEST_AGENT_DATA_GOOD_MULTIPLE_DEPENDENCIES})
    assert set(order) == {"agent-a", "agent-b", "agent-e", "agent-f", "agent-g"}


def test_sort_empty():
    assert dependency_sort({}) == []


def test_sort_self_dependency():

    with pytest.raises(ValueError, match="Circular dependencies detected for"):
        dependency_sort(test_consts.TEST_AGENT_DATA_SELF_DEPENDENCY)


def test_dependency_sort_no_deps():
    order = dependency_sort(test_consts.TEST_AGENT_DATA_GOOD_MULTIPLE_NO_DEPENDENCIES)
    assert len(order) == 3
    assert "agent-a" in order
    assert "agent-b" in order
    assert "agent-c" in order


def test_dependency_sort_branching():
    order = dependency_sort(test_consts.TEST_AGENT_DATA_GOOD_MULTIPLE_DEPENDENCIES)
    assert order.index("agent-e") < order.index("agent-g")
    assert order.index("agent-f") < order.index("agent-g")


def test_dependency_sort_circular_dependencies():
    with pytest.raises(ValueError, match="Circular dependencies detected for"):
        dependency_sort(test_consts.TEST_AGENT_DATA_CIRCULAR_DEPENDENCY)
