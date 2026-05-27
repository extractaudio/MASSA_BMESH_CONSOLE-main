# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from blmcp.tools_helpers.geonodes_paths import find_demo
from blmcp.tools_helpers.geonodes_helpers import demo_info, error, module_docstring, read_text, related_demos
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)


from typing import cast

def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Geonodes Get Demo", readOnlyHint=True))
    def geonodes_get_demo(demo_name: str) -> dict[str, object]:
        """Return one vendored geonodes demo source file and related demos."""
        path = find_demo(demo_name)
        if path is None:
            return error(f"Geonodes demo '{demo_name}' was not found.")
        source = read_text(path)
        info = demo_info(path)
        tags = cast(list[str], info.get("tags", []))
        return {
            "status": "ok",
            "demo": info,
            "module_docstring": module_docstring(source),
            "source": source,
            "related_demos": related_demos(tags, path.stem),
        }
