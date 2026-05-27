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
from blmcp.tools.massa_create_socket_at_selected_face_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Create Socket Empty at Selected Face", destructiveHint=True))
    def massa_create_socket_at_selected_face(
        socket_name: str = "socket",
        object_name: str = "",
        parent_to_mesh: bool = True,
        align_to_normal: bool = True,
        display_size: float = 0.2,
    ) -> str:
        """
        Create a Blender Empty at the centre of every selected face,
        oriented so its local +Z follows the face normal, and (by default)
        parented to the source mesh. This is the canonical Massa socket
        pattern — face-aligned empties used as mount points.

        Workflow:
          1. Enter Edit Mode and select one or more faces.
          2. Call this tool.

        socket_name      — base name; suffixed _01, _02, ... when multiple
                           faces are selected
        object_name      — target object; uses the active edit object when empty
        parent_to_mesh   — parent each Empty to the source mesh so it
                           follows the mesh through transforms
        align_to_normal  — rotate the Empty so its local +Z aligns with
                           the world-space face normal
        display_size     — Empty arrow display size in Blender units

        Returns a formatted status string including the procedural cartridge snippet.
        """
        p = Params(
            socket_name=str(socket_name),
            object_name=str(object_name),
            parent_to_mesh=bool(parent_to_mesh),
            align_to_normal=bool(align_to_normal),
            display_size=float(display_size),
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
        count = result.get("count", 0)
        
        response_text = (
            f"Successfully created {count} live visual sockets "
            f"named '{socket_name}'."
        )

        # 4. Inject the Procedural Cartridge Snippet for the Agent
        snippet = result.get("cartridge_snippet")
        if snippet:
            response_text += f"\n\n=== PROCEDURAL CARTRIDGE SNIPPET ===\n```python\n{snippet}\n```\n"
            response_text += "\nAgent Instruction: Insert this snippet to ensure the engine dynamically spawns these sockets upon cartridge load. Remember to verify the target slot has 'sock': True in CARTRIDGE_META."

        return response_text