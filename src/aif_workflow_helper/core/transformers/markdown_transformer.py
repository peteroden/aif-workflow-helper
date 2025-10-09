"""Markdown transformer for agent definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import frontmatter

from aif_workflow_helper.core.formats import EXTENSION_MAP
from aif_workflow_helper.core.transformers.base import AgentTransformer, register_transformer


class MarkdownAgentTransformer(AgentTransformer):
    """Handle serialization of agent definitions to and from Markdown files."""

    format_name = "md"
    extensions = (EXTENSION_MAP["md"],)

    def load(self, path: Path) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as handle:
            raw_content = handle.read()

        post = frontmatter.loads(raw_content)
        metadata = post.metadata.copy()
        instructions = post.content or ""
        if raw_content.endswith("\n") and not instructions.endswith("\n"):
            instructions += "\n"
        metadata["instructions"] = instructions
        return metadata

    def save(self, agent_dict: Dict[str, Any], path: Path) -> None:
        metadata = agent_dict.copy()
        content = metadata.pop("instructions", "")
        # Ensure instructions always ends with a single trailing newline for roundtrip consistency
        if not content.endswith("\n"):
            content += "\n"
        post = frontmatter.Post(content, **metadata)
        markdown_content = frontmatter.dumps(post)
        # Guarantee file ends with a single trailing newline (Unix convention)
        if not markdown_content.endswith("\n"):
            markdown_content += "\n"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(markdown_content)


register_transformer(MarkdownAgentTransformer())