"""Base types and registry for agent format transformers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, Optional

from aif_workflow_helper.utils.logging import logger


class AgentTransformer(ABC):
    """Abstract base class for converting agent definitions to/from files."""

    format_name: str
    extensions: tuple[str, ...]

    @abstractmethod
    def load(self, path: Path) -> dict:
        """Parse an agent definition from ``path`` and return a dictionary."""

    @abstractmethod
    def save(self, agent_dict: dict, path: Path) -> None:
        """Serialize ``agent_dict`` to ``path``."""


class TransformerRegistry:
    """Registry that maps format names and extensions to transformers."""

    def __init__(self) -> None:
        self._by_format: Dict[str, AgentTransformer] = {}
        self._by_extension: Dict[str, AgentTransformer] = {}

    def register(self, transformer: AgentTransformer) -> None:
        """Register a transformer instance."""
        format_name = transformer.format_name
        extensions = tuple(ext.lower() for ext in transformer.extensions)

        if not format_name:
            raise ValueError("Transformer must define a format_name")
        if not extensions:
            raise ValueError("Transformer must define at least one extension")
        if format_name in self._by_format:
            raise ValueError(
                f"Transformer for format '{format_name}' already registered"
            )

        self._by_format[format_name] = transformer
        for ext in extensions:
            if ext in self._by_extension:
                logger.warning(
                    "Extension '%s' already bound to another transformer", ext
                )
                continue
            self._by_extension[ext] = transformer

    def get_by_format(self, format_name: str) -> Optional[AgentTransformer]:
        return self._by_format.get(format_name)

    def get_by_extension(self, extension: str) -> Optional[AgentTransformer]:
        return self._by_extension.get(extension.lower())

    def list_formats(self) -> Iterable[str]:
        return self._by_format.keys()


registry = TransformerRegistry()


def register_transformer(transformer: AgentTransformer) -> None:
    """Helper for registering transformers from individual modules."""
    registry.register(transformer)
