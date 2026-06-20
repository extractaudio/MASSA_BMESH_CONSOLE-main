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
            title="Re-run Massa Cartridge",
            destructiveHint=True,
        )
    )
    def massa_rerun_cartridge(
        object_name: str,
        console_params: dict[str, object] | None = None,
        cartridge_params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """
        Live-edit an existing Massa cartridge object: restores its stored
        parameters, applies your overrides, and regenerates it in place
        (same location/rotation), deleting the old object. Use this to iterate
        on a spawned cartridge instead of deleting and re-spawning.

        object_name: the existing Massa-generated object to re-run.
        console_params / cartridge_params: parameter overrides to apply this run
        (cartridge_params take precedence). Use massa_get_cartridge_parameters to
        discover valid keys.
        """
        from .massa_rerun_cartridge_toolcode import Params

        params = Params(
            object_name=object_name,
            console_params=console_params or {},
            cartridge_params=cartridge_params or {},
        )
        return send_code(toolcode_format_call(_TOOL_CALL, params), strict_json=True)
