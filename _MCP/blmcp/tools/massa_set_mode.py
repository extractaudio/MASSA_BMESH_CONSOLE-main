# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

# pylint: disable=C0114  # See tool doc-string.

__all__ = (
    "register",
)

from blmcp.tools_helpers import (
    toolcode_format_call,
    toolcode_load_from_filepath,
    toolcode_wrap_with_calling_convention,
)
from blmcp.tools_helpers.connection import send_code
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Set Massa Object Mode",
            destructiveHint=True,
        )
    )
    def massa_set_mode(
        object_name: str,
        mode: str = "EDIT",
        select_mode: list[str] | None = None,
    ) -> dict[str, object]:
        """
        Make an object active and set its mode; optionally set the mesh select
        mode in Edit mode. Call this before massa_select_geometry /
        massa_get_selected_geometry / slot-tagging tools.

        mode: OBJECT, EDIT, SCULPT, VERTEX_PAINT, WEIGHT_PAINT, TEXTURE_PAINT, PARTICLE_EDIT.
        select_mode: subset of ["VERT","EDGE","FACE"] (only applied in EDIT mode).
        """
        from .massa_set_mode_toolcode import Params

        params = Params(
            object_name=object_name,
            mode=mode,
            select_mode=select_mode or [],
        )
        return send_code(toolcode_format_call(_TOOL_CALL, params), strict_json=True)
