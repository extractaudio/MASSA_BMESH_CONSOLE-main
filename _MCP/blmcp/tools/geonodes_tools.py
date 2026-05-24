# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Reference and runtime tools for the vendored geonodes package."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from blmcp.tools_helpers.connection import send_code
from blmcp.tools_helpers.geonodes_paths import CORE_DIR, DEMOS_DIR, DOC_DIR, VENDOR_ROOT, find_demo, find_doc, iter_searchable_files
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

__all__ = ("register",)

_TAG_KEYWORDS = {
    "animation": ("animate", "animation", "frame", "motion"),
    "curve": ("curve", "spline", "bezier"),
    "field": ("field", "attribute"),
    "forest": ("forest", "tree", "foliage", "leaf"),
    "formula": ("formula", "math", "sin", "cos", "function"),
    "fractals": ("fractal", "mandelbrot", "julia"),
    "instances": ("instance", "instances", "points"),
    "mesh": ("mesh", "grid", "cube", "surface"),
    "physics": ("gravity", "physics", "collision"),
    "shader": ("shader", "material", "color", "texture"),
    "simulation": ("simulation", "sim", "rain", "particles"),
    "volume": ("volume", "volumetric"),
}

_TYPE_CATEGORIES = {
    "geometry": {"Mesh", "Curve", "Points", "Instances", "Geometry", "Volume", "Cloud"},
    "socket": {"Boolean", "Integer", "Float", "Vector", "Color", "String", "Material", "Texture", "Image", "Object", "Collection"},
    "domain": {"Vertex", "Face", "Edge", "Corner", "Spline", "ControlPoint", "CloudPoint", "Instance"},
    "control-flow": {"GeoNodes", "ShaderNodes", "Layout", "Panel", "Repeat", "Simulation", "MenuSwitch"},
}


def _error(message: str) -> dict[str, object]:
    return {"status": "error", "message": message}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _module_docstring(source: str) -> str:
    try:
        module = ast.parse(source)
    except SyntaxError:
        return ""
    return ast.get_docstring(module) or ""


def _one_line_description(source: str) -> str:
    docstring = _module_docstring(source)
    if docstring:
        return docstring.strip().splitlines()[0].strip()

    block: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped:
            if block:
                break
            continue
        if stripped.startswith("#"):
            block.append(stripped.lstrip("#").strip())
            continue
        break
    return " ".join(block).strip()


def _infer_tags(name: str, text: str) -> list[str]:
    haystack = f"{name} {text}".lower()
    tags = {tag for tag, words in _TAG_KEYWORDS.items() if any(word in haystack for word in words)}
    for token in re.split(r"[^a-z0-9]+", name.lower()):
        if token in _TAG_KEYWORDS:
            tags.add(token)
    return sorted(tags)


def _demo_info(path: Path) -> dict[str, object]:
    source = _read_text(path)
    description = _one_line_description(source)
    return {
        "name": path.stem,
        "file": _relative(path),
        "description": description,
        "size_bytes": path.stat().st_size,
        "line_count": len(source.splitlines()),
        "tags": _infer_tags(path.stem, f"{description}\n{source[:2000]}"),
    }


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(VENDOR_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _related_demos(tags: list[str], current: str, limit: int = 5) -> list[dict[str, object]]:
    tag_set = set(tags)
    related: list[tuple[int, dict[str, object]]] = []
    if not tag_set or not DEMOS_DIR.is_dir():
        return []
    for path in sorted(DEMOS_DIR.glob("*.py")):
        if path.stem == current:
            continue
        info = _demo_info(path)
        overlap = len(tag_set.intersection(info["tags"]))
        if overlap:
            related.append((overlap, info))
    related.sort(key=lambda item: (-item[0], item[1]["name"]))
    return [info for _overlap, info in related[:limit]]


def _literal_string_list(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.List, ast.Tuple)):
        return [elt.value for elt in node.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]
    return []


def _iter_public_type_names() -> list[str]:
    names: list[str] = []
    init_file = VENDOR_ROOT / "__init__.py"
    if init_file.exists():
        try:
            module = ast.parse(_read_text(init_file))
        except SyntaxError:
            module = ast.Module(body=[], type_ignores=[])
        for node in module.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        names.extend(_literal_string_list(node.value))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    names.append(alias.asname or alias.name.split(".")[0])

    for root in (CORE_DIR, VENDOR_ROOT / "shadernodes"):
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            try:
                module = ast.parse(_read_text(path))
            except SyntaxError:
                continue
            for node in module.body:
                if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    names.append(node.name)

    seen: set[str] = set()
    result = []
    for name in names:
        if name and not name.startswith("_") and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def _class_docstrings() -> dict[str, str]:
    docs: dict[str, str] = {}
    for root in (CORE_DIR, VENDOR_ROOT / "shadernodes"):
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            try:
                module = ast.parse(_read_text(path))
            except SyntaxError:
                continue
            for node in module.body:
                if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    doc = ast.get_docstring(node) or ""
                    docs[node.name] = doc.strip().splitlines()[0].strip() if doc.strip() else ""
    return docs


def _category_for_type(name: str) -> str:
    for category, names in _TYPE_CATEGORIES.items():
        if name in names:
            return category
    lowered = name.lower()
    if lowered.endswith(("vertex", "face", "edge", "spline", "point")):
        return "domain"
    if lowered in {"geonodes", "shadernodes"} or "layout" in lowered:
        return "control-flow"
    return "socket" if name[:1].isupper() else "other"


def _related_docs(path: Path, limit: int = 8) -> list[str]:
    if not DOC_DIR.is_dir():
        return []
    base_tokens = set(re.split(r"[-_\W]+", path.stem.lower())) - {""}
    scored: list[tuple[int, str]] = []
    for candidate in DOC_DIR.rglob("*.md"):
        if candidate == path:
            continue
        tokens = set(re.split(r"[-_\W]+", candidate.stem.lower())) - {""}
        overlap = len(base_tokens.intersection(tokens))
        if overlap:
            scored.append((overlap, _relative(candidate)))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [name for _score, name in scored[:limit]]


def _enclosing_def(lines: list[str], line_index: int) -> str | None:
    for index in range(line_index, -1, -1):
        stripped = lines[index].lstrip()
        if stripped.startswith(("def ", "class ")):
            return stripped.split(":", 1)[0]
    return None


def _rank_line(query: str, line: str) -> int:
    query_lower = query.lower()
    line_lower = line.lower()
    rank = 0
    if re.search(rf"\b{re.escape(query_lower)}\b", line_lower):
        rank += 100
    if query_lower in line_lower:
        rank += 60
    if line_lower.strip().startswith(query_lower):
        rank += 30
    if line.lstrip().startswith(("class ", "def ")):
        rank += 25
    return rank


def register(mcp: FastMCP) -> None:
    @mcp.tool(annotations=ToolAnnotations(title="Geonodes List Demos", readOnlyHint=True))
    def geonodes_list_demos(filter_tag: str = "") -> dict[str, object]:
        """List vendored geonodes demos with descriptions and inferred tags."""
        if not DEMOS_DIR.is_dir():
            return _error(f"Vendored geonodes demos were not found at {DEMOS_DIR}")
        wanted = filter_tag.strip().lower()
        demos = [_demo_info(path) for path in sorted(DEMOS_DIR.glob("*.py")) if path.name != "__init__.py"]
        if wanted:
            demos = [demo for demo in demos if wanted in demo["tags"]]
        return {"status": "ok", "filter_tag": wanted or None, "count": len(demos), "demos": demos}

    @mcp.tool(annotations=ToolAnnotations(title="Geonodes Get Demo", readOnlyHint=True))
    def geonodes_get_demo(demo_name: str) -> dict[str, object]:
        """Return one vendored geonodes demo source file and related demos."""
        path = find_demo(demo_name)
        if path is None:
            return _error(f"Geonodes demo '{demo_name}' was not found.")
        source = _read_text(path)
        info = _demo_info(path)
        return {
            "status": "ok",
            "demo": info,
            "module_docstring": _module_docstring(source),
            "source": source,
            "related_demos": _related_demos(info["tags"], path.stem),
        }

    @mcp.tool(annotations=ToolAnnotations(title="Geonodes List Types", readOnlyHint=True))
    def geonodes_list_types() -> dict[str, object]:
        """List public geonodes classes grouped by broad category."""
        if not VENDOR_ROOT.exists():
            return _error(f"Vendored geonodes package was not found at {VENDOR_ROOT}")
        docs = _class_docstrings()
        grouped: dict[str, list[dict[str, object]]] = {}
        for name in _iter_public_type_names():
            category = _category_for_type(name)
            grouped.setdefault(category, []).append({"name": name, "summary": docs.get(name, "")})
        for entries in grouped.values():
            entries.sort(key=lambda item: item["name"])
        count = sum(len(entries) for entries in grouped.values())
        return {"status": "ok", "count": count, "categories": dict(sorted(grouped.items()))}

    @mcp.tool(annotations=ToolAnnotations(title="Geonodes Get Type Doc", readOnlyHint=True))
    def geonodes_get_type_doc(type_name: str) -> dict[str, object]:
        """Return the markdown reference for a geonodes type."""
        path = find_doc(type_name)
        if path is None:
            return _error(f"Geonodes documentation for '{type_name}' was not found.")
        content = _read_text(path)
        return {
            "status": "ok",
            "type_name": type_name,
            "file": _relative(path),
            "content": content,
            "related_docs": _related_docs(path),
        }

    @mcp.tool(annotations=ToolAnnotations(title="Geonodes Search", readOnlyHint=True))
    def geonodes_search(query: str, scope: str = "all", max_results: int = 20, context_lines: int = 2) -> dict[str, object]:
        """Search vendored geonodes demos, docs, and core source."""
        clean_query = query.strip()
        if not clean_query:
            return _error("query must be non-empty.")
        try:
            files = list(iter_searchable_files(scope))
        except ValueError as ex:
            return _error(str(ex))

        max_results = max(1, min(int(max_results), 100))
        context_lines = max(0, min(int(context_lines), 8))
        hits: list[dict[str, object]] = []
        query_lower = clean_query.lower()

        for path in files:
            lines = _read_text(path).splitlines()
            for index, line in enumerate(lines):
                if query_lower not in line.lower():
                    continue
                start = max(0, index - context_lines)
                end = min(len(lines), index + context_lines + 1)
                rank = _rank_line(clean_query, line)
                hits.append(
                    {
                        "rank": rank,
                        "file": _relative(path),
                        "line_no": index + 1,
                        "line": line[:240],
                        "surrounding": [{"line_no": offset + 1, "line": lines[offset][:240]} for offset in range(start, end)],
                        "enclosing_def": _enclosing_def(lines, index),
                    }
                )

        hits.sort(key=lambda hit: (-int(hit["rank"]), str(hit["file"]), int(hit["line_no"])))
        for hit in hits:
            hit.pop("rank", None)
        return {"status": "ok", "query": clean_query, "scope": scope, "count": len(hits), "hits": hits[:max_results]}

    @mcp.tool(annotations=ToolAnnotations(title="Geonodes Execute Script", destructiveHint=True))
    def geonodes_execute_script(script: str) -> dict[str, object]:
        """Execute a geonodes Python script inside Blender and report created node data."""
        vendor_parent = str(VENDOR_ROOT.parent)
        code = """
import contextlib
import io
import sys
import traceback

import bpy

vendor_parent = __VENDOR_PARENT__
user_script = __SCRIPT__

if vendor_parent not in sys.path:
    sys.path.insert(0, vendor_parent)

before_groups = set(bpy.data.node_groups.keys())
before_materials = set(bpy.data.materials.keys())
stdout = io.StringIO()
trace = None

try:
    with contextlib.redirect_stdout(stdout):
        exec(compile(user_script, "<geonodes_execute_script>", "exec"), {"__name__": "__main__"})
except Exception:
    trace = traceback.format_exc()

created_node_groups = sorted(name for name in bpy.data.node_groups.keys() if name not in before_groups)
created_materials = sorted(name for name in bpy.data.materials.keys() if name not in before_materials)

result = {
    "status": "error" if trace else "ok",
    "message": "geonodes script failed; see traceback." if trace else "geonodes script executed.",
    "created_node_groups": created_node_groups,
    "created_materials": created_materials,
    "stdout": stdout.getvalue(),
    "traceback": trace,
}
"""
        code = code.replace("__VENDOR_PARENT__", repr(vendor_parent)).replace("__SCRIPT__", repr(script))
        return send_code(code, strict_json=True)
