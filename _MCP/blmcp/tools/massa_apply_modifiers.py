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
from blmcp.tools.massa_apply_modifiers_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Massa Apply Modifiers", destructiveHint=True))
    def massa_apply_modifiers(
        object_name: str,
        modifier_names: list[str] | str = "ALL",
        keep_last_bevel_weighted_normal: bool = False,
        preserve_shape_keys: bool = False,
    ) -> dict[str, object]:
        """
        Apply modifiers on one object using native Blender operations.

        HardOps Smart Apply is event-driven, so this tool intentionally uses a
        deterministic native implementation. Set keep_last_bevel_weighted_normal
        to leave the final Bevel and Weighted Normal modifiers unapplied.
        """
        p = Params(
            object_name=object_name,
            modifier_names=modifier_names,
            keep_last_bevel_weighted_normal=bool(keep_last_bevel_weighted_normal),
            preserve_shape_keys=bool(preserve_shape_keys),
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
