"""Fetch the vendored NodeToPython addon source."""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys
import os
import stat

REPO_URL = "https://github.com/BrendanParmer/NodeToPython.git"
TAG = "v4.1.0"


def _run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def _remove_readonly(func, path: str, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def main() -> int:
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    target = repo_root / "_MCP" / "vendor" / "NodeToPython"
    manifest = target / "NodeToPython" / "blender_manifest.toml"
    init_file = target / "NodeToPython" / "__init__.py"

    if target.exists():
        shutil.rmtree(target, onerror=_remove_readonly)
    target.parent.mkdir(parents=True, exist_ok=True)

    _run(["git", "clone", "--depth", "1", "--branch", TAG, REPO_URL, str(target)])
    nested_git = target / ".git"
    if nested_git.exists():
        shutil.rmtree(nested_git, onerror=_remove_readonly)

    if not init_file.exists():
        raise FileNotFoundError(f"Expected NodeToPython package at {init_file}")
    if not manifest.exists():
        raise FileNotFoundError(f"Expected Blender extension manifest at {manifest}")

    manifest_text = manifest.read_text(encoding="utf-8")
    version_match = re.search(r'^version\s*=\s*"([^"]+)"', manifest_text, re.MULTILINE)
    version = version_match.group(1) if version_match else "unknown"
    print(f"Vendored NodeToPython {version} from {TAG} into {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
