# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from blmcp.tools_helpers.geonodes_paths import VENDOR_ROOT
from blmcp.tools_helpers.geonodes_helpers import category_for_type, class_docstrings, error, iter_public_type_names
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Geonodes List Types", readOnlyHint=True))
    def geonodes_list_types() -> dict[str, object]:
        """List public geonodes classes grouped by broad category."""
        if not VENDOR_ROOT.exists():
            return error(f"Vendored geonodes package was not found at {VENDOR_ROOT}")
        docs = class_docstrings()
        grouped: dict[str, list[dict[str, object]]] = {}
        for name in iter_public_type_names():
            category = category_for_type(name)
            grouped.setdefault(category, []).append({"name": name, "summary": docs.get(name, "")})
        for entries in grouped.values():
            entries.sort(key=lambda item: item["name"])
        count = sum(len(entries) for entries in grouped.values())
        return {"status": "ok", "count": count, "categories": dict(sorted(grouped.items()))}
