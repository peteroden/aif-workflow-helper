"""Azure AI Foundry Agent Helper - Public API."""

# Core functionality
from aif_workflow_helper.core.upload import (
    create_or_update_agent,
    create_or_update_agents,
    create_or_update_agents_from_files,
    create_or_update_agent_from_file,
)
from aif_workflow_helper.core.download import (
    download_agent,
    download_agents,
)
from aif_workflow_helper.utils.logging import (
    configure_logging,
    logger,
)
from aif_workflow_helper.core.formats import (
    SUPPORTED_FORMATS,
    get_file_extension,
)

__version__ = "0.2.0"

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