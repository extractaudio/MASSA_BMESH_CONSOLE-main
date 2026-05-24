"""Fetch the vendored geonodes source tree."""

from __future__ import annotations

import os
import pathlib
import shutil
import stat
import subprocess
import sys

REPO_URL = "https://github.com/al1brn/geonodes.git"
BRANCH = "main"
LICENSE_TEXT = """geonodes

SPDX-License-Identifier: GPL-3.0-only

This vendored snapshot is recorded as GPL-3.0 in the Massa MCP vendor policy.
The upstream repository did not include a root LICENSE file at the pinned
commit when this vendor script was authored, so this file preserves the SPDX
license identifier expected by the package manifest.
"""


def _run(args: list[str], cwd: pathlib.Path | None = None) -> str:
    completed = subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)
    return completed.stdout.strip()


def _remove_readonly(func, path: str, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    target = repo_root / "_MCP" / "vendor" / "geonodes"
    init_file = target / "__init__.py"
    demos_dir = target / "demos"
    doc_dir = target / "doc"
    license_file = target / "LICENSE"
    commit_file = target / ".vendored_commit"

    if target.exists():
        shutil.rmtree(target, onerror=_remove_readonly)
    target.parent.mkdir(parents=True, exist_ok=True)

    _run(["git", "clone", "--depth", "1", "--branch", BRANCH, REPO_URL, str(target)])
    commit = _run(["git", "rev-parse", "HEAD"], cwd=target)

    nested_git = target / ".git"
    if nested_git.exists():
        shutil.rmtree(nested_git, onerror=_remove_readonly)

    if not init_file.exists():
        raise FileNotFoundError(f"Expected geonodes package at {init_file}")
    if not demos_dir.is_dir():
        raise FileNotFoundError(f"Expected geonodes demos at {demos_dir}")
    if not doc_dir.is_dir():
        raise FileNotFoundError(f"Expected geonodes docs at {doc_dir}")

    if not license_file.exists():
        license_file.write_text(LICENSE_TEXT, encoding="utf-8")
    commit_file.write_text(commit + "\n", encoding="utf-8")
    print(f"Vendored geonodes {commit[:12]} from {BRANCH} into {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
