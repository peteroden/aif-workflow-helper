TEST_AGENT_DATA = {"name": "agent", "tools": []}

TEST_AGENT_DATA_GOOD_NO_DEPENDENCIES = {
    "agent-a": {"name": "agent-a", "tools": []},
    "agent-b": {"name": "agent-b", "tools": [{"type": "other_tool", "config": {"setting": "value"}}]},
}

TEST_AGENT_DATA_GOOD_SINGLE_DEPENDENCY = {
    "agent-a": {"name": "agent-a",   "instructions": "instructions", "tools": []},
    "agent-b": {"name": "agent-b", "tools": [
        {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-a"}}
    ]},
}

TEST_AGENT_DATA_GOOD_MULTIPLE_NO_DEPENDENCIES = {
    "agent-a": {"name": "agent-a", "tools": []},
    "agent-b": {"name": "agent-b", "tools": []},
    "agent-c": {"name": "agent-c", "tools": []},
}

TEST_AGENT_DATA_GOOD_MULTIPLE_DEPENDENCIES = {
    "agent-e": {"name": "agent-e", "tools": []},
    "agent-f": {"name": "agent-f", "tools": []},
    "agent-g": {"name": "agent-g", "tools": [
        {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-e"}},
        {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-f"}},
    ]}
}

TEST_AGENT_DATA_UNKNOWN_AGENT = {
    "agent-a": {"name": "agent-a", "tools": [
        {"type": "connected_agent", "connected_agent": {"name_from_id": "Unknown Agent"}}
    ]}
}

TEST_AGENT_DATA_MISSING_NAME_FROM_ID = {
    "agent-a": {"name": "agent-a", "tools": [
        {"type": "connected_agent", "connected_agent": {}}
    ]}
}

TEST_AGENT_DATA_MIXED_TOOLS = {
    "agent-a": {"name": "agent-a", "tools": [
        {"type": "other_tool", "config": {"setting": "value"}},
        {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-b"}},
        {"type": "another_tool", "config": {"another": "setting"}},
    ]}
}

TEST_AGENT_DATA_NO_TOOLS = {
    "agent-a": {"name": "agent-a"}
}

TEST_AGENT_DATA_MALFORMED_TOOLS = {
    "agent-a": {"name": "agent-a", "tools": ""}
}

TEST_AGENT_DATA_MALFORMED_CONNECTED_AGENT = {
    "agent-a": {"name": "agent-a", "tools": [
        {"type": "connected_agent", "connected_agent": "not-a-dict"}
    ]}
}

TEST_AGENT_DATA_GOOD_LINEAR_CHAIN = {
    "agent-a": {"name": "agent-a", "tools": []},
    "agent-b": {"name": "agent-b", "tools": [
        {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-a"}}
    ]},
    "agent-c": {"name": "agent-c", "tools": [
        {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-b"}}
    ]},
}

TEST_AGENT_DATA_GOOD_COMPLEX_DEPENDENCIES = {
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

TEST_AGENT_DATA_SELF_DEPENDENCY = {
    "agent-a": {"name": "agent-a", "tools": [
        {"type": "connected_agent", "connected_agent": {"name_from_id": "agent-a"}}
    ]}
}

TEST_AGENT_DATA_CIRCULAR_DEPENDENCY = {
    "agent-a": {"name": "agent-a", "tools": [{"type": "connected_agent", "connected_agent": {"name_from_id": "agent-b"}}]},
    "agent-b": {"name": "agent-b", "tools": [{"type": "connected_agent", "connected_agent": {"name_from_id": "agent-a"}}]},
}
