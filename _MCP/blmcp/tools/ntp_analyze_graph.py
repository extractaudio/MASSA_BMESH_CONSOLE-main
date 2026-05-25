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
from blmcp.tools.ntp_analyze_graph_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="NTP Analyze Graph", readOnlyHint=True))
    def ntp_analyze_graph(
        graph_type: str,
        graph_name: str,
        coord_precision: int = 6,
    ) -> dict[str, object]:
        """
        Return structural stats, broken links, orphan/dead-end nodes, and group dependencies for one graph.
        """
        p = Params(
            graph_type=str(graph_type),
            graph_name=str(graph_name),
            coord_precision=int(coord_precision),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
