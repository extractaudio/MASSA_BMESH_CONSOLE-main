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
    ) -> str:
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

        Returns a formatted status string including the procedural cartridge snippet.
        """
        if int(slot_index) < 0:
            return "Error: slot_index must be >= 0"

        p = Params(
            slot_index=int(slot_index),
            object_name=str(object_name),
        )
        
        # 1. Execute the tool code in Blender
        code = toolcode_format_call(_TOOL_CALL, p)
        result = send_code(code, strict_json=True)
        
        # 2. Validate response
        if not isinstance(result, dict):
            return f"Error: Unexpected response format from Blender: {result}"
            
        if result.get("status") == "error":
            return f"Error executing in Blender: {result.get('message', 'Unknown error')}"

        # 3. Format standard output
        faces_affected = result.get("faces_affected") or []
        count = result.get("count") if result.get("count") is not None else len(faces_affected)
        material_name = result.get("material_name")
        mat_info = f" (Material: '{material_name}')" if material_name else ""
        
        response_text = (
            f"Successfully assigned {count} faces "
            f"to Material Slot {result.get('slot_index')}{mat_info}."
        )

        # 4. Inject the Procedural Cartridge Snippet for the Agent
        snippet = result.get("cartridge_snippet")
        if snippet:
            response_text += f"\n\n=== PROCEDURAL CARTRIDGE SNIPPET ===\n```python\n{snippet}\n```\n"
            response_text += "\nAgent Instruction: You may now inject this snippet into the cartridge's build_shape(bm) function to proceduralize this action."

        return response_text