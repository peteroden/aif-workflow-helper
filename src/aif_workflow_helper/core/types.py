"""Structural typing protocols for agent client interactions.

These protocols decouple core logic from any specific SDK implementation
(legacy Azure AgentsClient vs. Agent Framework wrapper). They describe only
the methods actually consumed by upload/download/delete flows, enabling
flexible substitution in tests or future backends.
"""

from __future__ import annotations

from typing import Protocol, Iterable, runtime_checkable, Any


@runtime_checkable
class AgentLike(Protocol):  # pragma: no cover - structural container
    """Minimal shape required for agent objects returned by clients."""

    id: str
    name: str

    def as_dict(self) -> dict:  # noqa: D401 - simple protocol method
        """Return a dictionary representation of the agent."""


@runtime_checkable
class SupportsAgents(Protocol):  # pragma: no cover - structural typing only
    """Protocol capturing the asynchronous agent operations used internally."""

    async def list_agents(self) -> Iterable[AgentLike]: ...  # noqa: D401,E701
    async def create_agent(self, **kwargs: Any) -> AgentLike: ...  # noqa: D401,E701
    async def update_agent(self, agent_id: str, **kwargs: Any) -> AgentLike: ...  # noqa: D401,E701
    async def get_agent(self, agent_id: str) -> AgentLike | None: ...  # noqa: D401,E701
    async def delete_agent(self, agent_id: str) -> None: ...  # noqa: D401,E701
    async def close(self) -> None: ...  # noqa: D401,E701
