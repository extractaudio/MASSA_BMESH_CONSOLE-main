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
            title="Select Massa Geometry",
            destructiveHint=True,
        )
    )
    def massa_select_geometry(
        object_name: str,
        select_by: str,
        domain: str = "FACE",
        indices: list[int] | None = None,
        slot: int = 0,
        material_index: int = 0,
        normal: list[float] | None = None,
        angle_tol: float = 15.0,
        action: str = "SET",
    ) -> dict[str, object]:
        """
        Programmatically select mesh geometry (enters Edit mode automatically).

        select_by:
          - INDEX     : select `indices` in `domain`
          - ALL/NONE/INVERT : whole-domain operations
          - EDGE_SLOT : edges whose MASSA_EDGE_SLOTS value == `slot` (domain=EDGE)
          - MATERIAL  : faces whose material_index == `material_index` (domain=FACE)
          - NORMAL    : faces whose normal is within `angle_tol` degrees of
                        `normal` (object space, domain=FACE)
          - SEAM/SHARP: edges marked seam / sharp (domain=EDGE)
        domain: VERT | EDGE | FACE (also sets the mesh select mode).
        action: SET (replace selection), ADD, or REMOVE.

        Returns the resulting selection count and indices (capped at 512).
        """
        from .massa_select_geometry_toolcode import Params

        params = Params(
            object_name=object_name,
            select_by=select_by,
            domain=domain,
            indices=indices or [],
            slot=slot,
            material_index=material_index,
            normal=normal or [0.0, 0.0, 1.0],
            angle_tol=angle_tol,
            action=action,
        )
        return send_code(toolcode_format_call(_TOOL_CALL, params), strict_json=True)
