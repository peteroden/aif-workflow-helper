"""
Mock implementation of azure.ai.agents.AgentsClient for test isolation.

Covers the subset of behavior required by this project:
- create_agent(**kwargs)
- update_agent(**kwargs)
- list_agents()
- get_agent(agent_id)

Agent objects expose attributes: id, name, tools (list) and any extra kwargs.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

@dataclass
class MockAgent:
    id: str
    name: str
    description: Optional[str] = None
    instructions: str = ""
    model: str = "gpt-4"
    temperature: float = 1.0
    top_p: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    tools: List[dict] = field(default_factory=list)
    _extra: Dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, item: str) -> Any:
        if item in self._extra:
            return self._extra[item]
        raise AttributeError(item)

    def to_dict(self) -> Dict[str, Any]:
        base = {
            "id": self.id,
            "name": self.name,
            "tools": [t.copy() for t in self.tools],
        }
        base.update(self._extra)
        return base


class AgentsClientMock:
    """
    In-memory mock of AgentsClient.

    Usage:
        client = AgentsClientMock()
        agent = client.create_agent(name="agent-a", tools=[...])
        for a in client.list_agents(): ...
    """

    def __init__(self):
        self._agents_by_id: Dict[str, MockAgent] = {}
        self._name_index: Dict[str, str] = {}
        self._counter = 0

    # ---- internal utilities ----
    def _generate_id(self) -> str:
        self._counter += 1
        return f"mock-{self._counter}"

    def _register(self, agent: MockAgent) -> MockAgent:
        self._agents_by_id[agent.id] = agent
        self._name_index[agent.name] = agent.id
        return agent

    def _ensure_unique_name(self, name: str) -> None:
        if name in self._name_index:
            raise ValueError(f"Agent with name '{name}' already exists")

    # ---- public mock API ----
    def list_agents(self) -> Iterable[MockAgent]:
        # Return a list copy to avoid mutation side-effects
        return list(self._agents_by_id.values())

    def get_agent(self, agent_id: str) -> Optional[MockAgent]:
        return self._agents_by_id.get(agent_id)

    def create_agent(self, **kwargs) -> MockAgent:
        name = kwargs.get("name")
        if not name:
            raise ValueError("create_agent requires 'name'")
        self._ensure_unique_name(name)
        tools = kwargs.get("tools") or []
        agent_id = kwargs.get("id") or self._generate_id()
        description = kwargs.get("description", None)
        instructions = kwargs.get("instructions", "")
        model = kwargs.get("model", "gpt-4")
        temperature = kwargs.get("temperature", 1.0)
        top_p = kwargs.get("top_p", 1.0)
        metadata = kwargs.get("metadata", {})
        
        # Extract recognized keys; everything else into _extra
        extra = {
            k: v
            for k, v in kwargs.items()
            if k not in {"id", "name", "tools", "description", "instructions", "model", "temperature", "top_p", "metadata"}
        }
        agent = MockAgent(id=agent_id, name=name, description=description, instructions=instructions, model=model, temperature=temperature, top_p=top_p, metadata=metadata, tools=[t.copy() for t in tools], _extra=extra)
        return self._register(agent)

    def update_agent(self, agent_id: str, body=None, **kwargs) -> MockAgent:
        """
        Update existing agent.
        """
        target: Optional[MockAgent] = None
        if agent_id:
            target = self._agents_by_id.get(agent_id)
        else:
            raise ValueError("update_agent target not found (need existing id)")

        # If body is provided, merge its contents with kwargs
        if body and isinstance(body, dict):
            kwargs.update(body)

        # Update name (and index) if changed
        new_name = kwargs.get("name")
        if new_name and new_name != target.name:
            if new_name in self._name_index and self._name_index[new_name] != target.id:
                raise ValueError(f"Agent with name '{new_name}' already exists")
            # Update index
            del self._name_index[target.name]
            target.name = new_name
            self._name_index[target.name] = target.id
        target.description = kwargs.get("description", target.description)
        target.instructions = kwargs.get("instructions", target.instructions)
        target.model = kwargs.get("model", target.model)
        target.temperature = kwargs.get("temperature", target.temperature)
        target.top_p = kwargs.get("top_p", target.top_p)
        target.metadata = kwargs.get("metadata", target.metadata)

        if "tools" in kwargs and kwargs["tools"] is not None:
            target.tools = [t.copy() for t in kwargs["tools"]]

        # Update arbitrary extra fields
        for k, v in kwargs.items():
            if k not in {"id", "name", "tools", "description", "instructions", "model", "temperature", "top_p", "metadata"}:
                target._extra[k] = v

        return target

    # Optional convenience for tests
    def reset(self):
        self._agents_by_id.clear()
        self._name_index.clear()
        self._counter = 0