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
from blmcp.tools_helpers.geonodes_paths import VENDOR_ROOT
from blmcp.tools.geonodes_execute_script_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Geonodes Execute Script", destructiveHint=True))
    def geonodes_execute_script(script: str, target_object: str = "") -> dict[str, object]:
        """Execute a geonodes Python script inside Blender, report created node data, and optionally attach it to an object."""
        vendor_parent = str(VENDOR_ROOT.parent)
        p = Params(
            vendor_parent=str(vendor_parent),
            script=str(script),
            target_object=str(target_object),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
