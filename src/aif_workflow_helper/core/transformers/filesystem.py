"""Utilities for loading and saving agent definitions from the filesystem.

This module centralizes translation between on-disk agent formats and the
in-memory dictionary representation consumed by the rest of the application.
By consolidating format-specific logic here, higher-level upload and download
flows remain agnostic to individual serialization details.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

import yaml

from aif_workflow_helper.core.formats import (
    ALTERNATIVE_EXTENSIONS,
    EXTENSION_MAP,
    SUPPORTED_FORMATS,
    get_glob_pattern,
)
from aif_workflow_helper.utils.logging import logger
from aif_workflow_helper.core.transformers.base import registry

# Ensure transformer registration side effects run.
import aif_workflow_helper.core.transformers.markdown_transformer  # noqa: F401
import aif_workflow_helper.core.transformers.json_transformer  # noqa: F401
import aif_workflow_helper.core.transformers.yaml_transformer  # noqa: F401

# Internal mapping of format name -> loader/saver callables and supported extensions.
_FORMAT_EXTENSIONS: Dict[str, tuple[str, ...]] = {
    format_name: tuple({EXTENSION_MAP[format_name], *ALTERNATIVE_EXTENSIONS.get(format_name, [])})
    for format_name in SUPPORTED_FORMATS
}
_FORMAT_LOADERS: Dict[str, object] = {}

_FORMAT_SAVERS: Dict[str, object] = {}


def _resolve_format_from_extension(extension: str) -> Optional[str]:
    lowered = extension.lower()
    for format_name, extensions in _FORMAT_EXTENSIONS.items():
        if lowered in extensions:
            return format_name
    return None


def _get_loader(format_name: str):
    loader = _FORMAT_LOADERS.get(format_name)
    if loader is None and registry.get_by_format(format_name) is None:
        logger.error(
            "Unsupported format '%s'. Supported formats: %s",
            format_name,
            sorted(_FORMAT_LOADERS.keys()),
        )
    return loader


def _get_saver(format_name: str):
    saver = _FORMAT_SAVERS.get(format_name)
    if saver is None and registry.get_by_format(format_name) is None:
        logger.error(
            "Unsupported format '%s'. Supported formats: %s",
            format_name,
            sorted(_FORMAT_SAVERS.keys()),
        )
    return saver


def _get_transformer(format_name: str):
    transformer = registry.get_by_format(format_name)
    if transformer is None:
        logger.error("No transformer registered for format '%s'", format_name)
    return transformer


def load_agent_from_file(file_path: Path, format_name: str | None = None) -> Optional[dict]:
    """Load a single agent definition from disk.

    The format can be provided explicitly or inferred from the file extension.

    Args:
        file_path: Path to the agent file.
        format_name: Optional format identifier (``json``, ``yaml``, ``md``).

    Returns:
        Parsed agent dictionary on success, ``None`` if loading fails.
    """
    try:
        actual_format = format_name or _resolve_format_from_extension(file_path.suffix)
        if not actual_format:
            logger.error("Unsupported file extension for '%s'", file_path)
            return None

        loader = _get_loader(actual_format)
        if loader is not None:
            data = loader(file_path)
        else:
            transformer = _get_transformer(actual_format)
            if transformer is None:
                return None
            data = transformer.load(file_path)
        logger.info("Successfully read agent file: %s", file_path)
        return data
    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s", file_path, exc)
    except yaml.YAMLError as exc:
        logger.error("Invalid YAML in %s: %s", file_path, exc)
    except FileNotFoundError:
        logger.error("Agent file not found: %s", file_path)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error("Unexpected error reading %s: %s", file_path, exc)
    return None


def load_agents_from_directory(directory: Path | str, format_name: str) -> Dict[str, dict]:
    """Load all agent definitions of a given format within a directory."""
    directory_path = Path(directory)
    pattern = get_glob_pattern(format_name)
    files = list(directory_path.glob(pattern))

    # Include additional extensions (e.g., .yml) if configured.
    for extension in _FORMAT_EXTENSIONS.get(format_name, ()):  # type: ignore[arg-type]
        if extension == EXTENSION_MAP.get(format_name):
            continue
        files.extend(directory_path.glob(f"*{extension}"))

    agents: Dict[str, dict] = {}
    for file_path in files:
        agent_dict = load_agent_from_file(file_path, format_name=format_name)
        if agent_dict and agent_dict.get("name"):
            agents[agent_dict["name"]] = agent_dict
    return agents


def save_agent_to_file(agent_dict: dict, file_path: Path, format_name: str = "json") -> bool:
    """Persist an agent definition to disk in the requested format."""
    try:
        saver = _get_saver(format_name)
        if saver is not None:
            saver(agent_dict, file_path)
        else:
            transformer = _get_transformer(format_name)
            if transformer is None:
                return False
            transformer.save(agent_dict, file_path)
        logger.info("Saved agent '%s' to %s", agent_dict.get("name"), file_path)
        return True
    except Exception as exc:
        logger.error("Error saving file %s: %s", file_path, exc)
        return False