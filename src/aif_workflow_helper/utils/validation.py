"""Name validation utilities for agent names."""

import re
from aif_workflow_helper.utils.logging import logger

__all__ = ["validate_agent_name"]

def validate_agent_name(agent_name: str):
    """Validate an agent name.

    Ensures the provided `agent_name` consists only of ASCII letters (A-Z, a-z),
    digits (0-9), and hyphens (-). The empty string is permitted by the current
    pattern ("*" quantifier); callers should enforce non-emptiness upstream if
    required.

    Args:
        agent_name (str): The proposed agent name to validate.

    Raises:
        ValueError: If the name contains characters other than letters,
            digits, or hyphens.
    """
    if not re.match(r"^[a-zA-Z0-9-]*$", agent_name):
        logger.error(
            f"Invalid agent name '{agent_name}'; only letters, numbers, and hyphens are allowed."
        )
        raise ValueError(
            f"Invalid agent name '{agent_name}'; only letters, numbers and hyphens are allowed."
        )