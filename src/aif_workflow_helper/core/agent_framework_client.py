"""Synchronous wrapper around the Agent Framework Azure AI client.

Enhancements added in refactor:
 - Optional global model deployment (per-agent model allowed)
 - Lightweight retry with exponential backoff for transient failures
 - Warning when falling back to placeholder model deployment
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any, Callable, Coroutine, List, Type

from azure.core.exceptions import ServiceRequestError, ServiceResponseError, HttpResponseError
from aif_workflow_helper.utils.logging import logger

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
        model_deployment_name: str | None = None,
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
        self._previous_loop: asyncio.AbstractEventLoop | None = None

    def _ensure_client(self) -> None:
        """Lazily create the async client and event loop."""
        if self._framework_client is not None:
            return

        try:
            self._previous_loop = asyncio.get_event_loop()
        except RuntimeError:
            self._previous_loop = None

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._initialize_async())
        except Exception:
            # Clean up the partially created state and restore the prior loop
            if self._framework_client is not None:
                try:
                    self._loop.run_until_complete(self._framework_client.close())
                except Exception:  # pragma: no cover - defensive
                    pass
            if self._credential is not None:
                try:
                    self._loop.run_until_complete(self._credential.close())
                except Exception:  # pragma: no cover - defensive
                    pass
            self._framework_client = None
            self._credential = None
            self._agents_client = None
            if self._loop is not None:
                self._loop.close()
            self._loop = None
            self._restore_previous_loop()
            raise

    async def _initialize_async(self) -> None:
        """Instantiate the async credential and Agent Framework client."""
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

    def _run(self, task: Any) -> Any:
        """Run an awaitable with retry/backoff for transient failures.

        Supports either a zero-argument coroutine factory (preferred for
        retries) or a single coroutine object when only one attempt is needed.

        Environment overrides:
          AIF_RETRY_ATTEMPTS (int, default 3)
          AIF_RETRY_BASE_DELAY (float seconds, default 0.5)
        """
        self._ensure_client()
        assert self._loop is not None

        attempts = max(1, int(os.getenv("AIF_RETRY_ATTEMPTS", "3")))
        base_delay = float(os.getenv("AIF_RETRY_BASE_DELAY", "0.5"))
        retry_exceptions: tuple[Type[BaseException], ...] = (
            ServiceRequestError,
            ServiceResponseError,
            HttpResponseError,
            asyncio.TimeoutError,
        )

        reusable_factory = False

        if asyncio.iscoroutine(task):
            attempts = 1

            def coroutine_factory() -> Coroutine[Any, Any, Any]:
                return task  # type: ignore[return-value]

        elif callable(task):
            reusable_factory = True

            def coroutine_factory() -> Coroutine[Any, Any, Any]:
                produced = task()
                if not asyncio.iscoroutine(produced):  # pragma: no cover - defensive
                    raise TypeError("_run task factory must return a coroutine")
                return produced
        else:
            raise TypeError("_run expects coroutine or zero-arg coroutine factory")

        last_exc: BaseException | None = None
        for attempt in range(1, attempts + 1):
            try:
                coro_instance = coroutine_factory()
                return self._loop.run_until_complete(coro_instance)
            except retry_exceptions as exc:  # pragma: no cover - network conditions vary
                last_exc = exc
                if attempt == attempts or not reusable_factory:
                    break
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(
                    "Transient error (%s) attempt %d/%d; retrying in %.2fs",
                    exc.__class__.__name__, attempt, attempts, delay,
                )
                time.sleep(delay)
            except Exception:
                # Non-transient → re-raise immediately
                raise
        assert last_exc is not None
        raise last_exc

    def _restore_previous_loop(self) -> None:
        """Restore the thread's default loop to its prior value."""

        try:
            asyncio.set_event_loop(self._previous_loop)
        except Exception:  # pragma: no cover - defensive safeguard
            pass
        finally:
            self._previous_loop = None

    def list_agents(self) -> List[Agent]:
        """Return all agents registered in the project."""

        async def _impl() -> List[Agent]:
            assert self._agents_client is not None
            agents: List[Agent] = []
            async for agent in self._agents_client.list_agents():
                agents.append(agent)
            return agents
        return self._run(_impl)

    def create_agent(self, **kwargs: Any) -> Agent:
        """Create an agent using the Agent Framework SDK."""

        async def _impl() -> Agent:
            assert self._agents_client is not None
            return await self._agents_client.create_agent(**kwargs)
        return self._run(_impl)

    def update_agent(self, agent_id: str, **kwargs: Any) -> Agent:
        """Update an existing agent by ID."""

        async def _impl() -> Agent:
            assert self._agents_client is not None
            return await self._agents_client.update_agent(agent_id, **kwargs)
        return self._run(_impl)

    def get_agent(self, agent_id: str) -> Agent:
        """Fetch a single agent by ID."""

        async def _impl() -> Agent:
            assert self._agents_client is not None
            return await self._agents_client.get_agent(agent_id)
        return self._run(_impl)

    def delete_agent(self, agent_id: str) -> None:
        """Delete the specified agent."""

        async def _impl() -> None:
            assert self._agents_client is not None
            await self._agents_client.delete_agent(agent_id)
        self._run(_impl)

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
            self._restore_previous_loop()

    def __enter__(self) -> "AgentFrameworkAgentsClient":
        """Support use of the client as a context manager."""
        self._ensure_client()
        return self

    def __exit__(self, exc_type: Any, exc: Any, exc_tb: Any) -> None:
        """Ensure resources are released when the context exits."""
        self.close()
