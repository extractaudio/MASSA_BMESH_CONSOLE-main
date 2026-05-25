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
from blmcp.tools.massa_mesh_clean_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

CleanMode = Literal["ACTIVE", "SELECTED", "VISIBLE"]

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Massa Mesh Clean", destructiveHint=True))
    def massa_mesh_clean(
        object_names: list[str],
        mode: CleanMode = "SELECTED",
        merge_threshold: float = 0.0001,
        dissolve_angle_deg: float = 5.0,
        degenerate_iterations: int = 1,
        delete_interior: bool = False,
        force_native: bool = False,
    ) -> dict[str, object]:
        """
        Clean mesh topology on one or more objects.

        Uses HardOps clean_mesh when available and otherwise runs a native edit
        mode cleanup pass with merge-by-distance, limited dissolve, optional
        degenerate dissolve, and optional interior face deletion.
        """
        p = Params(
            object_names=object_names,
            mode=mode,
            merge_threshold=float(merge_threshold),
            dissolve_angle_deg=float(dissolve_angle_deg),
            degenerate_iterations=int(degenerate_iterations),
            delete_interior=bool(delete_interior),
            force_native=bool(force_native),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
