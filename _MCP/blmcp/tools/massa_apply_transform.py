# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from blmcp.tools_helpers import (
    toolcode_format_call,
    toolcode_load_from_filepath,
    toolcode_wrap_with_calling_convention,
)
from blmcp.tools_helpers.connection import send_code
from blmcp.tools.massa_apply_transform_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Massa Apply Transform", destructiveHint=True))
    def massa_apply_transform(
        object_name: str,
        location: bool = False,
        rotation: bool = True,
        scale: bool = True,
    ) -> dict[str, object]:
        """Apply object transforms using native Blender transform_apply."""
        p = Params(
            object_name=object_name,
            location=bool(location),
            rotation=bool(rotation),
            scale=bool(scale),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
