"""Async Azure AI Agent Framework client with retry capabilities.

This module provides a direct async interface to the Azure AI Agent Framework SDK,
eliminating the synchronous wrapper layer for better performance and cleaner architecture.
"""

from __future__ import annotations

import os
import asyncio
from typing import Any, Callable, List, Type

from azure.core.exceptions import ServiceRequestError, ServiceResponseError, HttpResponseError
from aif_workflow_helper.utils.logging import logger

from agent_framework_azure_ai import AzureAIAgentClient
from azure.ai.agents.models import Agent
from azure.identity.aio import DefaultAzureCredential


class AsyncAgentClient:
    """Direct async interface to Azure AI Agent Framework with retry capabilities."""

    def __init__(
        self,
        *,
        project_endpoint: str,
        tenant_id: str,
        model_deployment_name: str | None = None,
        credential_factory: Callable[..., DefaultAzureCredential] | None = None,
    ) -> None:
        """Configure the async client with Azure project details."""
        self._project_endpoint = project_endpoint
        self._tenant_id = tenant_id
        self._model_deployment_name = model_deployment_name
        self._credential_factory = credential_factory or DefaultAzureCredential

        self._credential: DefaultAzureCredential | None = None
        self._framework_client: AzureAIAgentClient | None = None
        self._agents_client: Any | None = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Lazily initialize the async client."""
        if self._initialized:
            return

        self._credential = self._credential_factory(
            exclude_interactive_browser_credential=False,
            interactive_tenant_id=self._tenant_id,
        )
        
        if self._model_deployment_name:
            # Use global model deployment if provided
            self._framework_client = AzureAIAgentClient(
                project_endpoint=self._project_endpoint,
                model_deployment_name=self._model_deployment_name,
                async_credential=self._credential,
            )
        else:
            # Use a default model deployment for client initialization
            # Per-agent models will be handled in create/update methods
            self._framework_client = AzureAIAgentClient(
                project_endpoint=self._project_endpoint,
                model_deployment_name="default",  # Placeholder - will be overridden per agent
                async_credential=self._credential,
            )
            logger.warning(
                "No global model deployment configured. Using placeholder 'default'. "
                "Ensure each created agent specifies an explicit 'model' field or set --model-deployment-name."
            )
        
        self._agents_client = self._framework_client.project_client.agents
        self._initialized = True

    async def _run_with_retry(self, coro_factory: Callable[[], Any]) -> Any:
        """Run a coroutine with retry/backoff for transient failures.

        Args:
            coro_factory: Zero-argument function that returns a fresh coroutine

        Environment overrides:
          AIF_RETRY_ATTEMPTS (int, default 3)
          AIF_RETRY_BASE_DELAY (float seconds, default 0.5)
        """
        await self._ensure_initialized()

        attempts = max(1, int(os.getenv("AIF_RETRY_ATTEMPTS", "3")))
        base_delay = float(os.getenv("AIF_RETRY_BASE_DELAY", "0.5"))
        retry_exceptions: tuple[Type[BaseException], ...] = (
            ServiceRequestError,
            ServiceResponseError,
            HttpResponseError,
            asyncio.TimeoutError,
        )

        last_exc: BaseException | None = None
        for attempt in range(1, attempts + 1):
            try:
                coro = coro_factory()
                return await coro
            except retry_exceptions as exc:  # pragma: no cover - network conditions vary
                last_exc = exc
                if attempt == attempts:
                    break
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "Transient error (%s) attempt %d/%d; retrying in %.2fs",
                    exc.__class__.__name__, attempt, attempts, delay,
                )
                await asyncio.sleep(delay)
            except Exception:
                # Non-transient → re-raise immediately
                raise
        
        assert last_exc is not None
        raise last_exc

    async def list_agents(self) -> List[Agent]:
        """Return all agents registered in the project."""
        async def _impl() -> List[Agent]:
            assert self._agents_client is not None
            agents: List[Agent] = []
            async for agent in self._agents_client.list_agents():
                agents.append(agent)
            return agents
        
        return await self._run_with_retry(_impl)

    async def create_agent(self, **kwargs: Any) -> Agent:
        """Create an agent using the Agent Framework SDK."""
        async def _impl() -> Agent:
            assert self._agents_client is not None
            return await self._agents_client.create_agent(**kwargs)
        
        return await self._run_with_retry(_impl)

    async def update_agent(self, agent_id: str, **kwargs: Any) -> Agent:
        """Update an existing agent by ID."""
        async def _impl() -> Agent:
            assert self._agents_client is not None
            return await self._agents_client.update_agent(agent_id, **kwargs)
        
        return await self._run_with_retry(_impl)

    async def get_agent(self, agent_id: str) -> Agent:
        """Fetch a single agent by ID."""
        async def _impl() -> Agent:
            assert self._agents_client is not None
            return await self._agents_client.get_agent(agent_id)
        
        return await self._run_with_retry(_impl)

    async def delete_agent(self, agent_id: str) -> None:
        """Delete the specified agent."""
        async def _impl() -> None:
            assert self._agents_client is not None
            await self._agents_client.delete_agent(agent_id)
        
        await self._run_with_retry(_impl)

    async def close(self) -> None:
        """Dispose the async client and clean up resources."""
        if not self._initialized:
            return

        try:
            if self._framework_client is not None:
                await self._framework_client.close()
            if self._credential is not None:
                await self._credential.close()
        finally:
            self._framework_client = None
            self._credential = None
            self._agents_client = None
            self._initialized = False

    async def __aenter__(self) -> "AsyncAgentClient":
        """Support use of the client as an async context manager."""
        await self._ensure_initialized()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, exc_tb: Any) -> None:
        """Ensure resources are released when the async context exits."""
        await self.close()