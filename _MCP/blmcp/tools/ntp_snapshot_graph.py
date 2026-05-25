# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
from pathlib import Path

from blmcp.tools_helpers import (
    toolcode_format_call,
    toolcode_load_from_filepath,
    toolcode_wrap_with_calling_convention,
)
from blmcp.tools_helpers.connection import send_code
from blmcp.tools.ntp_snapshot_graph_toolcode import Params
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_TOOL_CALL = toolcode_wrap_with_calling_convention(toolcode_load_from_filepath(__file__))


def _vendor_paths() -> tuple[str, str]:
    """Return package-layout and legacy repo-layout vendor roots."""
    tool_path = Path(__file__).resolve()
    mcp_root = tool_path.parents[2]
    package_root = tool_path.parents[1]
    return (
        str(package_root / "vendor" / "NodeToPython"),
        str(mcp_root / "vendor" / "NodeToPython"),
    )


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="NTP Snapshot Graph", readOnlyHint=True))
    def ntp_snapshot_graph(
        graph_type: str,
        graph_name: str,
        include_imports: bool = True,
        set_defaults: bool = True,
    ) -> dict[str, object]:
        """
        Export one node graph as NodeToPython Python code without changing the graph.
        """
        package_vendor_path, repo_vendor_path = _vendor_paths()
        p = Params(
            graph_type=str(graph_type),
            graph_name=str(graph_name),
            include_imports=bool(include_imports),
            set_defaults=bool(set_defaults),
            package_vendor_path=package_vendor_path,
            repo_vendor_path=repo_vendor_path,
        )
        code = toolcode_format_call(_TOOL_CALL, p)
        return send_code(code, strict_json=True)
