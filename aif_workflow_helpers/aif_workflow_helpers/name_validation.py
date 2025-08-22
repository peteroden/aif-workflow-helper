import re
from .logging_utils import logger

__all__ = ["validate_agent_name"]

def validate_agent_name(agent_name: str):
    """Validate that an agent name contains only alphanumerics and hyphens.

    Raises ValueError if invalid.
    """
    if not re.match(r"^[a-zA-Z0-9-]*$", agent_name):
        logger.exception(
            f"Invalid agent name '{agent_name}'; only letters, numbers, and hyphens are allowed."
        )
        raise ValueError(
            f"Invalid agent name '{agent_name}'; only letters, numbers and hyphens are allowed."
        )
