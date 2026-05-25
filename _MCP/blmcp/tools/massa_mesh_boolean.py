# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from typing import Literal

from blmcp.tools_helpers import (
    toolcode_format_call,
    toolcode_load_from_filepath,
    toolcode_wrap_with_calling_convention,
)
from blmcp.tools_helpers.connection import send_code
from blmcp.tools.massa_mesh_boolean_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

BooleanOperation = Literal["DIFFERENCE", "UNION", "INTERSECT", "SLASH", "INSET", "KNIFE"]
BooleanSolver = Literal["FAST", "EXACT"]

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Massa Mesh Boolean", destructiveHint=True))
    def massa_mesh_boolean(
        target_object: str,
        cutter_objects: list[str],
        operation: BooleanOperation,
        solver: BooleanSolver = "EXACT",
        inset_thickness: float = 0.5,
        inset_outset: bool = False,
        force_native: bool = False,
    ) -> dict[str, object]:
        """
        Add a boolean-style operation to a target mesh.

        Uses HardOps object-mode operators when they are registered in the live
        Blender instance, then falls back to native Boolean modifiers for
        DIFFERENCE/UNION/INTERSECT.
        """
        p = Params(
            target_object=target_object,
            cutter_objects=cutter_objects,
            operation=operation,
            solver=solver,
            inset_thickness=float(inset_thickness),
            inset_outset=bool(inset_outset),
            force_native=bool(force_native),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
