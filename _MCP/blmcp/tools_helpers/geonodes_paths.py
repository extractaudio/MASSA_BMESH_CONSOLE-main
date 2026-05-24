# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Path helpers for the vendored geonodes package."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

_HELPER_PATH = Path(__file__).resolve()
_PACKAGE_ROOT = _HELPER_PATH.parents[1]
_MCP_ROOT = _HELPER_PATH.parents[2]

_REPO_VENDOR_ROOT = _MCP_ROOT / "vendor" / "geonodes"
_PACKAGE_VENDOR_ROOT = _PACKAGE_ROOT / "vendor" / "geonodes"

VENDOR_ROOT: Path = _REPO_VENDOR_ROOT if _REPO_VENDOR_ROOT.exists() else _PACKAGE_VENDOR_ROOT
DEMOS_DIR: Path = VENDOR_ROOT / "demos"
DOC_DIR: Path = VENDOR_ROOT / "doc"
CORE_DIR: Path = VENDOR_ROOT / "core"

_SEARCH_SCOPES = {
    "demos": (DEMOS_DIR,),
    "docs": (DOC_DIR,),
    "core": (CORE_DIR, VENDOR_ROOT / "shadernodes"),
    "all": (DEMOS_DIR, DOC_DIR, CORE_DIR, VENDOR_ROOT / "shadernodes", VENDOR_ROOT / "macros.py"),
}


def find_demo(name: str) -> Path | None:
    """Resolve a demo by stem, filename, or path-ish name."""
    if not DEMOS_DIR.is_dir():
        return None

    clean_name = Path(name.strip()).name
    candidates = [clean_name]
    if not clean_name.endswith(".py"):
        candidates.append(f"{clean_name}.py")

    lower_candidates = {candidate.lower() for candidate in candidates}
    for path in sorted(DEMOS_DIR.glob("*.py")):
        if path.name.lower() in lower_candidates or path.stem.lower() in lower_candidates:
            return path
    return None


def find_doc(type_name: str) -> Path | None:
    """Resolve a geonodes markdown doc by type name."""
    if not DOC_DIR.is_dir():
        return None

    clean_name = Path(type_name.strip()).stem
    if not clean_name:
        return None

    docs = sorted(DOC_DIR.rglob("*.md"))
    lower = clean_name.lower()

    exact_names = {lower, f"{lower}.md"}
    for path in docs:
        if path.stem.lower() == lower or path.name.lower() in exact_names:
            return path

    generated_name = f"core-gener-{lower}"
    for path in docs:
        if path.stem.lower() == generated_name:
            return path

    for path in docs:
        stem = path.stem.lower()
        if stem.endswith(f"-{lower}") or lower in stem.split("-"):
            return path
    return None


def iter_searchable_files(scope: str = "all") -> Iterator[Path]:
    """Yield searchable vendored files for a scope."""
    selected = _SEARCH_SCOPES.get(scope.lower())
    if selected is None:
        raise ValueError("scope must be one of demos, docs, core, all")

    seen: set[Path] = set()
    for root in selected:
        if root.is_file():
            paths = [root]
        elif root.is_dir():
            paths = sorted(path for path in root.rglob("*") if path.suffix.lower() in {".py", ".md"})
        else:
            paths = []
        for path in paths:
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield path
