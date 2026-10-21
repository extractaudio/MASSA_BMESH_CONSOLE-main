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


def _import_massa_cartridges():
    """Return MASSA's ``modules.cartridges`` package from whichever install is
    loaded: an extension (``bl_ext.<repo>.massa_mesh_gen``) or a legacy ``massa`` add-on."""
    import importlib
    import sys

    loaded = sorted(
        n for n in sys.modules
        if "massa" in n and n.count(".") == (2 if n.startswith("bl_ext.") else 0)
    )
    for root in loaded + ["massa"]:
        try:
            return importlib.import_module(root + ".modules.cartridges")
        except ImportError:
            continue
    raise ImportError("MASSA add-on is not loaded (no 'massa' or bl_ext.*.massa* package)")


def main(params: None) -> Result:
    del params
    import bpy  # pylint: disable=import-error,no-name-in-module

    try:
        MODULES = _import_massa_cartridges().MODULES
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
