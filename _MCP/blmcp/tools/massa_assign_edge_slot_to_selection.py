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
from blmcp.tools.massa_assign_edge_slot_to_selection_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_EDGE_SLOT_ACTIONS = ("SEAM", "SHARP", "BOTH", "CREASE", "BEVEL", "IGNORE")
_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Assign Edge Slot to Selection", destructiveHint=True))
    def massa_assign_edge_slot_to_selection(
        slot: int,
        action: str = "SEAM",
        object_name: str = "",
    ) -> dict[str, object]:
        """
        Write a Massa edge-slot number to every currently selected edge,
        and optionally apply the geometric action immediately.

        The slot value is stored on the MASSA_EDGE_SLOTS bmesh int layer.
        On the next cartridge re-run, Massa's engine reads this layer and
        applies the edge_slot_N_action property defined on the operator.
        This tool can ALSO apply the action right now (live) so the user
        sees the result without rerunning.

        Workflow:
          1. Enter Edit Mode on the target mesh.
          2. Select edges (Alt+click for a loop, Ctrl+click for shortest
             path between two selected verts, etc.).
          3. Call get_selected_geometry to confirm.
          4. Call this tool.

        slot   — edge slot number (1-5); 0 clears the assignment
        action — one of:
                   SEAM   — mark UV seam (edge.seam = True)
                   SHARP  — mark sharp edge (edge.smooth = False)
                   BOTH   — apply SEAM and SHARP
                   CREASE — set full crease weight (1.0)
                   BEVEL  — set full bevel weight (1.0)
                   IGNORE — write the slot number only; do not touch
                            seam / sharp / crease / bevel attributes
        object_name — target object; uses the active edit object when empty

        Returns the list of affected edge indices.
        """
        if action not in _EDGE_SLOT_ACTIONS:
            return {
                "status": "error",
                "message": "action must be one of {}".format(list(_EDGE_SLOT_ACTIONS)),
            }
        if int(slot) < 0 or int(slot) > 5:
            return {"status": "error", "message": "slot must be in 0-5 (0 clears)"}

        p = Params(
            slot=int(slot),
            action=str(action),
            object_name=str(object_name),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
