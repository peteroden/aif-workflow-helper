"""Azure AI Foundry Agent Helper - Public API."""

# Core functionality
from src.core.upload import (
    create_or_update_agent,
    create_or_update_agents,
    create_or_update_agents_from_files,
    create_or_update_agent_from_file,
)
from src.core.download import (
    download_agent,
    download_agents,
)
from src.utils.logging import (
    configure_logging,
    logger,
)
from src.core.formats import (
    SUPPORTED_FORMATS,
    get_file_extension,
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
    "get_file_extension",
]