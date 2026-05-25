# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from blmcp.tools_helpers.geonodes_paths import iter_searchable_files
from blmcp.tools_helpers.geonodes_helpers import enclosing_def, error, rank_line, read_text, relative
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Geonodes Search", readOnlyHint=True))
    def geonodes_search(query: str, scope: str = "all", max_results: int = 20, context_lines: int = 2) -> dict[str, object]:
        """Search vendored geonodes demos, docs, and core source."""
        clean_query = query.strip()
        if not clean_query:
            return error("query must be non-empty.")
        try:
            files = list(iter_searchable_files(scope))
        except ValueError as ex:
            return error(str(ex))

        max_results = max(1, min(int(max_results), 100))
        context_lines = max(0, min(int(context_lines), 8))
        hits: list[dict[str, object]] = []
        query_lower = clean_query.lower()

        for path in files:
            lines = read_text(path).splitlines()
            for index, line in enumerate(lines):
                if query_lower not in line.lower():
                    continue
                start = max(0, index - context_lines)
                end = min(len(lines), index + context_lines + 1)
                rank = rank_line(clean_query, line)
                hits.append(
                    {
                        "rank": rank,
                        "file": relative(path),
                        "line_no": index + 1,
                        "line": line[:240],
                        "surrounding": [{"line_no": offset + 1, "line": lines[offset][:240]} for offset in range(start, end)],
                        "enclosing_def": enclosing_def(lines, index),
                    }
                )

        hits.sort(key=lambda hit: (-int(hit["rank"]), str(hit["file"]), int(hit["line_no"])))
        for hit in hits:
            hit.pop("rank", None)
        return {"status": "ok", "query": clean_query, "scope": scope, "count": len(hits), "hits": hits[:max_results]}
