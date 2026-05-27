# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for listing available Massa procedural geometry cartridges.
"""

__all__ = (
    "Result",
    "main",
)

from typing import NamedTuple


class Result(NamedTuple):
    status: str
    cartridges: list[dict]
    error: str | None = None


def main(params: None) -> Result:
    del params
    import bpy  # pylint: disable=import-error,no-name-in-module

    try:
        from massa.modules.cartridges import MODULES
    except ImportError as e:
        return Result(status="error", cartridges=[], error=str(e))
    
    carts = []
    for mod in MODULES:
        meta = getattr(mod, "CARTRIDGE_META", {})
        carts.append({
            "id": meta.get("id"),
            "name": meta.get("name"),
            "icon": meta.get("icon"),
            "flags": meta.get("flags", {})
        })
        
    return Result(status="ok", cartridges=carts)
