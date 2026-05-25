# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared python helpers for geonodes MCP tools."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from blmcp.tools_helpers.geonodes_paths import CORE_DIR, DEMOS_DIR, DOC_DIR, VENDOR_ROOT

__all__ = (
    "error",
    "read_text",
    "module_docstring",
    "one_line_description",
    "infer_tags",
    "demo_info",
    "relative",
    "related_demos",
    "iter_public_type_names",
    "class_docstrings",
    "category_for_type",
    "related_docs",
    "enclosing_def",
    "rank_line",
)

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


def error(message: str) -> dict[str, object]:
    return {"status": "error", "message": message}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def module_docstring(source: str) -> str:
    try:
        module = ast.parse(source)
    except SyntaxError:
        return ""
    return ast.get_docstring(module) or ""


def one_line_description(source: str) -> str:
    docstring = module_docstring(source)
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


def infer_tags(name: str, text: str) -> list[str]:
    haystack = f"{name} {text}".lower()
    tags = {tag for tag, words in _TAG_KEYWORDS.items() if any(word in haystack for word in words)}
    for token in re.split(r"[^a-z0-9]+", name.lower()):
        if token in _TAG_KEYWORDS:
            tags.add(token)
    return sorted(tags)


def demo_info(path: Path) -> dict[str, object]:
    source = read_text(path)
    description = one_line_description(source)
    return {
        "name": path.stem,
        "file": relative(path),
        "description": description,
        "size_bytes": path.stat().st_size,
        "line_count": len(source.splitlines()),
        "tags": infer_tags(path.stem, f"{description}\n{source[:2000]}"),
    }


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(VENDOR_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def related_demos(tags: list[str], current: str, limit: int = 5) -> list[dict[str, object]]:
    tag_set = set(tags)
    related: list[tuple[int, dict[str, object]]] = []
    if not tag_set or not DEMOS_DIR.is_dir():
        return []
    for path in sorted(DEMOS_DIR.glob("*.py")):
        if path.stem == current:
            continue
        info = demo_info(path)
        overlap = len(tag_set.intersection(info["tags"]))
        if overlap:
            related.append((overlap, info))
    related.sort(key=lambda item: (-item[0], item[1]["name"]))
    return [info for _overlap, info in related[:limit]]


def _literal_string_list(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.List, ast.Tuple)):
        return [elt.value for elt in node.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)]
    return []


def iter_public_type_names() -> list[str]:
    names: list[str] = []
    init_file = VENDOR_ROOT / "__init__.py"
    if init_file.exists():
        try:
            module = ast.parse(read_text(init_file))
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
                module = ast.parse(read_text(path))
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


def class_docstrings() -> dict[str, str]:
    docs: dict[str, str] = {}
    for root in (CORE_DIR, VENDOR_ROOT / "shadernodes"):
        if not root.is_dir():
            continue
        for path in root.rglob("*.py"):
            try:
                module = ast.parse(read_text(path))
            except SyntaxError:
                continue
            for node in module.body:
                if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                    doc = ast.get_docstring(node) or ""
                    docs[node.name] = doc.strip().splitlines()[0].strip() if doc.strip() else ""
    return docs


def category_for_type(name: str) -> str:
    for category, names in _TYPE_CATEGORIES.items():
        if name in names:
            return category
    lowered = name.lower()
    if lowered.endswith(("vertex", "face", "edge", "spline", "point")):
        return "domain"
    if lowered in {"geonodes", "shadernodes"} or "layout" in lowered:
        return "control-flow"
    return "socket" if name[:1].isupper() else "other"


def related_docs(path: Path, limit: int = 8) -> list[str]:
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
            scored.append((overlap, relative(candidate)))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [name for _score, name in scored[:limit]]


def enclosing_def(lines: list[str], line_index: int) -> str | None:
    for index in range(line_index, -1, -1):
        stripped = lines[index].lstrip()
        if stripped.startswith(("def ", "class ")):
            return stripped.split(":", 1)[0]
    return None


def rank_line(query: str, line: str) -> int:
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
