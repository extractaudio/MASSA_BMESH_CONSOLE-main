# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from blmcp.tools_helpers.geonodes_paths import DEMOS_DIR
from blmcp.tools_helpers.geonodes_helpers import demo_info, error
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Geonodes List Demos", readOnlyHint=True))
    def geonodes_list_demos(filter_tag: str = "") -> dict[str, object]:
        """List vendored geonodes demos with descriptions and inferred tags."""
        if not DEMOS_DIR.is_dir():
            return error(f"Vendored geonodes demos were not found at {DEMOS_DIR}")
        wanted = filter_tag.strip().lower()
        demos = [demo_info(path) for path in sorted(DEMOS_DIR.glob("*.py")) if path.name != "__init__.py"]
        if wanted:
            demos = [demo for demo in demos if wanted in demo["tags"]]
        return {"status": "ok", "filter_tag": wanted or None, "count": len(demos), "demos": demos}
