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
            title="Spawn Massa Cartridge",
            destructiveHint=True,
        )
    )
    def massa_spawn_cartridge(
        cartridge_id: str,
        location: list[float] | None = None,
        rotation: list[float] | None = None,
        console_params: dict[str, object] | None = None,
        cartridge_params: dict[str, object] | None = None
    ) -> dict[str, object]:
        """
        Spawn a procedural geometry using the Massa add-on.
        
        cartridge_id: The ID of the cartridge, e.g. "prim_02_pipe" or "massa.gen_prim_02_pipe".
        location: A list of 3 floats for xyz position.
        rotation: A list of 3 floats for euler rotation.
        console_params: A dictionary of parameters to temporarily override on bpy.context.scene.massa_console (e.g. {"pol_solidify_active": True}).
        cartridge_params: A dictionary of shape parameters to pass directly to the operator (e.g. {"radius": 1.5}).
        """
        from .massa_spawn_cartridge_toolcode import Params
        
        params = Params(
            cartridge_id=cartridge_id,
            location=location or [0.0, 0.0, 0.0],
            rotation=rotation or [0.0, 0.0, 0.0],
            console_params=console_params or {},
            cartridge_params=cartridge_params or {}
        )
        return send_code(toolcode_format_call(_TOOL_CALL, params), strict_json=True)
