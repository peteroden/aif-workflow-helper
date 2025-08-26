import logging
import pytest

from aif_workflow_helpers.upload_agent_helpers import (
    extract_dependencies,
    dependency_sort,
    configure_logging,
)

configure_logging(propagate=True)

def test_extract_no_dependencies():
    data = {
        "agent-a": {"name": "agent-a", "tools": []},
        "agent-b": {"name": "agent-b", "tools": [{"type": "other_tool", "config": {"setting": "value"}}]},
    }
    assert extract_dependencies(data) == {}


def test_extract_single_dependency():
    data = {
        "agent-a": {"name": "agent-a", "tools": []},
        "agent-b": {"name": "agent-b", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-a"}}
        ]},
    }
    assert extract_dependencies(data) == {"agent-b": {"agent-a"}}


def test_extract_multiple_dependencies():
    data = {
        "agent-c": {"name": "agent-c", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-a"}},
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-b"}},
        ]}
    }
    assert extract_dependencies(data) == {"agent-c": {"agent-a", "agent-b"}}


def test_extract_unknown_agent_ignored():
    data = {
        "agent-a": {"name": "agent-a", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "Unknown Agent"}}
        ]}
    }
    assert extract_dependencies(data) == {}


def test_extract_missing_name_from_id():
    data = {
        "agent-a": {"name": "agent-a", "tools": [
            {"type": "connected_agent", "connected_agent": {}}
        ]}
    }
    assert extract_dependencies(data) == {}


def test_extract_mixed_tool_types():
    data = {
        "agent-a": {"name": "agent-a", "tools": [
            {"type": "other_tool", "config": {"setting": "value"}},
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-b"}},
            {"type": "another_tool", "config": {"another": "setting"}},
        ]}
    }
    assert extract_dependencies(data) == {"agent-a": {"agent-b"}}


# --------- negative / malformed extract_dependencies inputs ---------

def test_extract_tools_not_list():
    data = {"agent-a": {"name": "agent-a", "tools": None}}
    assert extract_dependencies(data) == {}


def test_extract_tool_entry_not_dict():
    data = {"agent-a": {"name": "agent-a", "tools": ["not-a-dict"]}}
    assert extract_dependencies(data) == {}


def test_extract_connected_agent_not_dict():
    data = {"agent-a": {"name": "agent-a", "tools": [
        {"type": "connected_agent", "connected_agent": "not-a-dict"}
    ]}}
    assert extract_dependencies(data) == {}

def test_sort_no_dependencies():
    data = {
        "agent-a": {"name": "agent-a", "tools": []},
        "agent-b": {"name": "agent-b", "tools": []},
        "agent-c": {"name": "agent-c", "tools": []},
    }
    order = dependency_sort(data)
    assert set(order) == {"agent-a", "agent-b", "agent-c"}
    assert len(order) == 3


def test_sort_linear_chain():
    data = {
        "agent-a": {"name": "agent-a", "tools": []},
        "agent-b": {"name": "agent-b", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-a"}}
        ]},
        "agent-c": {"name": "agent-c", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-b"}}
        ]},
    }
    assert dependency_sort(data) == ["agent-a", "agent-b", "agent-c"]


def test_sort_complex_graph():
    data = {
        "agent-a": {"name": "agent-a", "tools": []},
        "agent-b": {"name": "agent-b", "tools": []},
        "agent-c": {"name": "agent-c", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-a"}},
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-b"}},
        ]},
        "agent-d": {"name": "agent-d", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-c"}},
        ]},
    }
    order = dependency_sort(data)
    assert order.index("agent-a") < order.index("agent-c")
    assert order.index("agent-b") < order.index("agent-c")
    assert order.index("agent-c") < order.index("agent-d")


def test_sort_independent_groups():
    data = {
        "group1-a": {"name": "group1-a", "tools": []},
        "group1-b": {"name": "group1-b", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "group1-a"}}
        ]},
        "group2-a": {"name": "group2-a", "tools": []},
        "group2-b": {"name": "group2-b", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "group2-a"}}
        ]},
    }
    order = dependency_sort(data)
    assert set(order) == {"group1-a", "group1-b", "group2-a", "group2-b"}
    assert order.index("group1-a") < order.index("group1-b")
    assert order.index("group2-a") < order.index("group2-b")


def test_sort_branching():
    data = {
        "a": {"name": "a", "tools": []},
        "b": {"name": "b", "tools": []},
        "c": {"name": "c", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "a"}},
            {"type": "connected_agent", "connected_agent": {"name_from_id": "b"}},
        ]},
    }
    order = dependency_sort(data)
    assert set(order) == {"a", "b", "c"}
    assert order.index("a") < order.index("c")
    assert order.index("b") < order.index("c")


def test_sort_empty():
    assert dependency_sort({}) == []


def test_sort_cycle(caplog: pytest.LogCaptureFixture):
    data = {
        "agent-a": {"name": "agent-a", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-b"}}
        ]},
        "agent-b": {"name": "agent-b", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-a"}}
        ]},
    }
    with caplog.at_level(logging.WARNING):
        order = dependency_sort(data)
    assert set(order) == {"agent-a", "agent-b"}
    assert any("Circular dependencies detected" in m for m in caplog.messages)


def test_sort_self_dependency():
    data = {
        "agent-a": {"name": "agent-a", "tools": [
            {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-a"}}
        ]}
    }
    assert dependency_sort(data) == ["agent-a"]

    def test_extract_dependencies_empty():
        assert extract_dependencies({}) == {}


    def test_extract_dependencies_simple():
        data = {
            "a": {"name": "a", "tools": []},
            "b": {"name": "b", "tools": [
                {"type": "connected_agent", "connected_agent": {"name_from_id": "a"}}
            ]}
        }
        deps = extract_dependencies(data)
        assert deps == {"b": {"a"}}


    def test_dependency_sort_no_deps():
        data = {"a": {"name": "a", "tools": []}, "b": {"name": "b", "tools": []}}
        order = dependency_sort(data)
        assert set(order) == {"a", "b"}
        # With no dependencies relative ordering is flexible; ensure stable subset property
        assert len(order) == 2


    def test_dependency_sort_linear():
        data = {
            "a": {"name": "a", "tools": []},
            "b": {"name": "b", "tools": [{"type": "connected_agent", "connected_agent": {"name_from_id": "a"}}]},
            "c": {"name": "c", "tools": [{"type": "connected_agent", "connected_agent": {"name_from_id": "b"}}]},
        }
        order = dependency_sort(data)
        assert order == ["a", "b", "c"]


    def test_dependency_sort_branching():
        data = {
            "a": {"name": "a", "tools": []},
            "b": {"name": "b", "tools": []},
            "c": {"name": "c", "tools": [
                {"type": "connected_agent", "connected_agent": {"name_from_id": "a"}},
                {"type": "connected_agent", "connected_agent": {"name_from_id": "b"}},
            ]},
        }
        order = dependency_sort(data)
        # a & b must appear before c
        assert set(order) == {"a", "b", "c"}
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("c")


    def test_dependency_sort_cycle():
        data = {
            "a": {"name": "a", "tools": [{"type": "connected_agent", "connected_agent": {"name_from_id": "b"}}]},
            "b": {"name": "b", "tools": [{"type": "connected_agent", "connected_agent": {"name_from_id": "a"}}]},
        }
        order = dependency_sort(data)
        assert set(order) == {"a", "b"}
        assert len(order) == 2