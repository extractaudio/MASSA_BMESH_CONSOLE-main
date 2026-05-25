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
from blmcp.tools.massa_assign_face_material_slot_to_selection_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Assign Material Slot to Selected Faces", destructiveHint=True))
    def massa_assign_face_material_slot_to_selection(
        slot_index: int,
        object_name: str = "",
    ) -> dict[str, object]:
        """
        Set material_index on every selected face. This is what drives
        Massa's slot manifest (UV strategy, physics material, socket flag)
        once the cartridge runs.

        Workflow:
          1. Enter Edit Mode and select faces.
          2. Ensure the target slot exists on the object (append a
             material slot first if needed; this tool fails otherwise).
          3. Call this tool.

        slot_index  — 0-based material slot index on the mesh
        object_name — target object; uses the active edit object when empty

        Returns the list of affected face indices and the material name
        currently assigned to that slot (if any).
        """
        if int(slot_index) < 0:
            return {"status": "error", "message": "slot_index must be >= 0"}

        p = Params(
            slot_index=int(slot_index),
            object_name=str(object_name),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
