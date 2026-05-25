# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from blmcp.tools_helpers.geonodes_paths import find_doc
from blmcp.tools_helpers.geonodes_helpers import error, read_text, related_docs, relative
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Geonodes Get Type Doc", readOnlyHint=True))
    def geonodes_get_type_doc(type_name: str) -> dict[str, object]:
        """Return the markdown reference for a geonodes type."""
        path = find_doc(type_name)
        if path is None:
            return error(f"Geonodes documentation for '{type_name}' was not found.")
        content = read_text(path)
        return {
            "status": "ok",
            "type_name": type_name,
            "file": relative(path),
            "content": content,
            "related_docs": related_docs(path),
        }
