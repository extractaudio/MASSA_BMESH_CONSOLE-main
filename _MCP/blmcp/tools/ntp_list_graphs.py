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
from blmcp.tools.ntp_list_graphs_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="NTP List Graphs", readOnlyHint=True))
    def ntp_list_graphs(filter_by_type: str = "") -> dict[str, object]:
        """
        List material, geometry-node, shader, compositor, world, light, and line-style node graphs.
        """
        p = Params(
            filter_by_type=str(filter_by_type),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
