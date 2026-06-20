# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

# pylint: disable=C0114  # See tool doc-string.

__all__ = (
    "register",
)

from blmcp.tools_helpers.connection import ping
from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error,no-name-in-module
from mcp.types import ToolAnnotations  # pylint: disable=import-error,no-name-in-module


def register(mcp: FastMCP) -> None:
    @mcp.tool(
        annotations=ToolAnnotations(
            title="Ping Blender Bridge",
            readOnlyHint=True,
        )
    )
    def blender_ping() -> dict[str, object]:
        """
        Check whether the Blender-side MCP bridge is reachable.

        Returns ``{"reachable": True, ...}`` with Blender version and whether the
        MASSA addon is loaded, or ``{"reachable": False, "message": ...}`` when
        the bridge is down — without raising. Call this first to confirm the
        connection before running heavier tools.
        """
        try:
            response = ping()
        except ConnectionError as ex:
            return {"reachable": False, "message": str(ex)}

        result = response.get("result") if isinstance(response, dict) else None
        if not isinstance(result, dict):
            return {"reachable": True, "raw": response}
        return {
            "reachable": True,
            "blender_version": result.get("blender_version"),
            "massa_loaded": result.get("massa_loaded"),
        }
