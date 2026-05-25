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
from blmcp.tools.massa_get_selected_geometry_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Get Selected Geometry", readOnlyHint=True))
    def massa_get_selected_geometry(
        object_name: str = "",
        include_world_coords: bool = True,
        coord_precision: int = 6,
    ) -> dict[str, object]:
        """
        Return precise geometry data for every selected element on a mesh.

        Reads the live edit-mesh while in Edit Mode (the recommended path);
        falls back to the persisted selection on the mesh data when in
        Object Mode.

        For each selected vertex, edge, and face this returns:
          - index in the mesh
          - co_local  — object-space coordinates
          - co_world  — world-space coordinates (matrix_world applied)
          - topology  — edges: vertex indices; faces: vertex loop
          - geometry  — edge length, face area, face normal (local + world)
          - midpoint  — for edges
          - current_edge_slot — value of the MASSA_EDGE_SLOTS int layer
          - is_seam / is_sharp / bevel_weight / crease — current edge marks
          - material_index — for faces

        Also returns:
          - mode, in_edit_mode, select_mode  — Blender's current state
          - active_element — last-picked element ({type, index}) for
            "this exact one" intent
          - world_matrix — object's matrix_world (4x4 row list)
          - stats — selected counts + total mesh counts

        Use this BEFORE calling any of the assignment tools, so the agent
        can confirm what is highlighted. If nothing is selected, all
        arrays are empty and stats reflect zero.

        object_name           — target object; uses the active edit object
                                when empty, falling back to the active object
        include_world_coords  — set False to skip world-space transforms
                                (faster, smaller payload)
        coord_precision       — decimal places to round coordinates to
        """
        p = Params(
            object_name=object_name,
            include_world_coords=bool(include_world_coords),
            coord_precision=int(coord_precision),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
