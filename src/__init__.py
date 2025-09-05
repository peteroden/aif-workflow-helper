"""Azure AI Foundry Workflow Helpers.

A Python package for managing Azure AI Foundry agents with support for 
download, upload, and multi-format agent definitions.
"""

from core.upload import (
    create_or_update_agent,
    create_or_update_agents,
    create_or_update_agent_from_file,
    create_or_update_agents_from_files,
)

from core.download import (
    download_agents,
    download_agent,
)

from utils.logging import (
    configure_logging,
    logger
)

from core.formats import (
    SUPPORTED_FORMATS,
    EXTENSION_MAP,
    GLOB_PATTERN_MAP,
    get_file_extension,
    get_glob_pattern,
    get_alternative_extensions,
    is_supported_format
)

__version__ = "0.1.0"

__all__ = [
    "configure_logging",
    "logger",
    "download_agents",
    "download_agent",
    "create_or_update_agent",
    "create_or_update_agents",
    "create_or_update_agent_from_file",
    "create_or_update_agents_from_files",
    "SUPPORTED_FORMATS",
    "EXTENSION_MAP", 
    "GLOB_PATTERN_MAP",
    "get_file_extension",
    "get_glob_pattern",
    "get_alternative_extensions",
    "is_supported_format"
]