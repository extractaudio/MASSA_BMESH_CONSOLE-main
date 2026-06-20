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
            title="Get Massa Slot Meta",
            readOnlyHint=True,
        )
    )
    def massa_get_slot_meta(
        cartridge_id: str = "",
        object_name: str = "",
    ) -> dict[str, object]:
        """
        Read a Massa cartridge's slot metadata (material/edge slot -> name, uv,
        phys, sock). Identify the cartridge either by `cartridge_id` (e.g.
        "prim_02_pipe") or by `object_name` (uses the object's stored
        massa_op_id). The `socket_slot` field reports which material slot is the
        socket slot (flagged sock:True) — use it before assigning socket faces.
        """
        from .massa_get_slot_meta_toolcode import Params

        params = Params(cartridge_id=cartridge_id, object_name=object_name)
        return send_code(toolcode_format_call(_TOOL_CALL, params), strict_json=True)
