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
            title="Get Massa Cartridge Parameters",
            readOnlyHint=True,
        )
    )
    def massa_get_cartridge_parameters(cartridge_id: str) -> dict[str, object]:
        """
        Introspect a Massa cartridge's operator parameter schema.

        Returns every settable parameter with its type, default, min/max ranges,
        enum options, and description — so you can call massa_spawn_cartridge or
        massa_rerun_cartridge with valid values instead of guessing. Use the
        `cartridge_specific_params` list to see the parameters unique to this
        cartridge (vs. shared console/material/UV settings).

        cartridge_id: e.g. "prim_02_pipe" or "massa.gen_prim_02_pipe".
        """
        from .massa_get_cartridge_parameters_toolcode import Params

        params = Params(cartridge_id=cartridge_id)
        return send_code(toolcode_format_call(_TOOL_CALL, params), strict_json=True)
