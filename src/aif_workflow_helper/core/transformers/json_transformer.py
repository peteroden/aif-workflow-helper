"""JSON transformer for agent definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from aif_workflow_helper.core.formats import EXTENSION_MAP
from aif_workflow_helper.core.transformers.base import AgentTransformer, register_transformer


class JsonAgentTransformer(AgentTransformer):
    """Handle serialization of agent definitions to and from JSON files."""

    format_name = "json"
    extensions = (EXTENSION_MAP["json"],)

    def load(self, path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def save(self, agent_dict: Dict[str, Any], path: Path) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(agent_dict, handle, indent=2)
            handle.write("\n")


register_transformer(JsonAgentTransformer())
