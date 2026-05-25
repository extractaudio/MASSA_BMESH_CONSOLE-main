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
    ) -> dict[str, object]:
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

        Returns one entry per socket with its name, source face index,
        world location, and rotation.
        """
        p = Params(
            socket_name=str(socket_name),
            object_name=str(object_name),
            parent_to_mesh=bool(parent_to_mesh),
            align_to_normal=bool(align_to_normal),
            display_size=float(display_size),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
