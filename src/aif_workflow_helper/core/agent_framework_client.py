"""Synchronous wrapper around the Agent Framework Azure AI client."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, List

from agent_framework_azure_ai import AzureAIAgentClient
from azure.ai.agents.models import Agent
from azure.identity.aio import DefaultAzureCredential


class AgentFrameworkAgentsClient:
    """Expose synchronous CRUD helpers backed by the Agent Framework SDK."""

    def __init__(
        self,
        *,
        project_endpoint: str,
        tenant_id: str,
        model_deployment_name: str,
        credential_factory: Callable[..., DefaultAzureCredential] | None = None,
    ) -> None:
        """Configure the synchronous wrapper with Azure project details."""
        self._project_endpoint = project_endpoint
        self._tenant_id = tenant_id
        self._model_deployment_name = model_deployment_name
        self._credential_factory = credential_factory or DefaultAzureCredential

        self._loop: asyncio.AbstractEventLoop | None = None
        self._credential: DefaultAzureCredential | None = None
        self._framework_client: AzureAIAgentClient | None = None
        self._agents_client: Any | None = None

    def _ensure_client(self) -> None:
        """Lazily create the async client and event loop."""
        if self._framework_client is not None:
            return

        self._loop = asyncio.new_event_loop()
        self._loop.run_until_complete(self._initialize_async())

    async def _initialize_async(self) -> None:
        """Instantiate the async credential and Agent Framework client."""
        self._credential = self._credential_factory(
            exclude_interactive_browser_credential=False,
            interactive_tenant_id=self._tenant_id,
        )
        self._framework_client = AzureAIAgentClient(
            project_endpoint=self._project_endpoint,
            model_deployment_name=self._model_deployment_name,
            async_credential=self._credential,
        )
        self._agents_client = self._framework_client.project_client.agents

    def _run(self, coro: Coroutine[Any, Any, Any]) -> Any:
        """Run a coroutine to completion on the internal loop."""
        self._ensure_client()
        assert self._loop is not None
        return self._loop.run_until_complete(coro)

    def list_agents(self) -> List[Agent]:
        """Return all agents registered in the project."""

        async def _impl() -> List[Agent]:
            assert self._agents_client is not None
            agents: List[Agent] = []
            async for agent in self._agents_client.list_agents():
                agents.append(agent)
            return agents

        return self._run(_impl())

    def create_agent(self, **kwargs: Any) -> Agent:
        """Create an agent using the Agent Framework SDK."""

        async def _impl() -> Agent:
            assert self._agents_client is not None
            return await self._agents_client.create_agent(**kwargs)

        return self._run(_impl())

    def update_agent(self, agent_id: str, **kwargs: Any) -> Agent:
        """Update an existing agent by ID."""

        async def _impl() -> Agent:
            assert self._agents_client is not None
            return await self._agents_client.update_agent(agent_id, **kwargs)

        return self._run(_impl())

    def get_agent(self, agent_id: str) -> Agent:
        """Fetch a single agent by ID."""

        async def _impl() -> Agent:
            assert self._agents_client is not None
            return await self._agents_client.get_agent(agent_id)

        return self._run(_impl())

    def delete_agent(self, agent_id: str) -> None:
        """Delete the specified agent."""

        async def _impl() -> None:
            assert self._agents_client is not None
            await self._agents_client.delete_agent(agent_id)

        self._run(_impl())

    def close(self) -> None:
        """Dispose the async client and tear down the event loop."""
        if self._loop is None:
            return

        try:
            if self._framework_client is not None:
                self._loop.run_until_complete(self._framework_client.close())
            if self._credential is not None:
                self._loop.run_until_complete(self._credential.close())
        finally:
            self._framework_client = None
            self._credential = None
            self._agents_client = None
            self._loop.close()
            self._loop = None

    def __enter__(self) -> "AgentFrameworkAgentsClient":
        """Support use of the client as a context manager."""
        self._ensure_client()
        return self

    def __exit__(self, exc_type: Any, exc: Any, exc_tb: Any) -> None:
        """Ensure resources are released when the context exits."""
        self.close()
