"""YAML transformer for agent definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from aif_workflow_helper.core.formats import ALTERNATIVE_EXTENSIONS, EXTENSION_MAP
from aif_workflow_helper.core.transformers.base import AgentTransformer, register_transformer


class YamlAgentTransformer(AgentTransformer):
    """Handle serialization of agent definitions to and from YAML files."""

    format_name = "yaml"
    extensions = (EXTENSION_MAP["yaml"], *ALTERNATIVE_EXTENSIONS.get("yaml", []))

    def load(self, path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)

    def save(self, agent_dict: Dict[str, Any], path: Path) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            yaml.dump(agent_dict, handle, default_flow_style=False, allow_unicode=True)


register_transformer(YamlAgentTransformer())