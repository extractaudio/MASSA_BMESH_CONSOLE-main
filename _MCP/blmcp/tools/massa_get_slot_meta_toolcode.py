# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for reading a Massa cartridge's slot metadata (``get_slot_meta``).

Resolves the cartridge by id, or by an existing object's stored ``massa_op_id``.
Returns the slot -> {name, uv, phys, sock} map and the resolved socket slot
(the slot flagged ``sock: True``), which downstream tools use instead of
hard-coding a slot index.
"""

__all__ = ("Params", "Result", "main")

from typing import NamedTuple, Any


class Params(NamedTuple):
    cartridge_id: str
    object_name: str


class Result(NamedTuple):
    status: str
    cartridge_id: str | None = None
    bl_idname: str | None = None
    slots: dict[str, Any] | None = None
    socket_slot: int | None = None
    error: str | None = None


class _PermissiveSelf:
    """Stand-in ``self`` so ``get_slot_meta`` (an instance method) can be called
    without a live operator instance. Attribute reads return a neutral value so
    any internal branching falls through to a default slot map."""

    def __getattr__(self, _name):
        return 0


def _resolve_class(cartridge_id, object_name):
    import bpy
    from massa.modules.cartridges import CLASSES

    bl_target = None
    if object_name:
        obj = bpy.data.objects.get(object_name)
        if obj is not None and "massa_op_id" in obj:
            bl_target = obj["massa_op_id"]  # e.g. "massa.gen_prim_02_pipe"

    if bl_target is None and cartridge_id:
        norm = cartridge_id
        for pre in ("massa.gen_", "massa.", "gen_"):
            if norm.startswith(pre):
                norm = norm[len(pre):]
                break
        bl_target = "gen_" + norm

    for cls in CLASSES:
        bl = getattr(cls, "bl_idname", "")
        if bl == bl_target or bl.split(".")[-1] == bl_target or bl.split(".")[-1] == bl_target.split(".")[-1]:
            return cls
    return None


def main(params: Params) -> Result:
    try:
        target = _resolve_class(params.cartridge_id, params.object_name)
    except ImportError as exc:
        return Result(status="error", error=str(exc))

    if target is None:
        return Result(
            status="error",
            cartridge_id=params.cartridge_id,
            error="Could not resolve cartridge from id '{:s}' / object '{:s}'.".format(
                params.cartridge_id, params.object_name
            ),
        )

    try:
        meta = target.get_slot_meta(_PermissiveSelf())
    except Exception as exc:
        return Result(
            status="error",
            bl_idname=getattr(target, "bl_idname", None),
            error="get_slot_meta() failed: {:s}".format(str(exc)),
        )

    slots: dict[str, Any] = {}
    socket_slot = None
    for idx, data in meta.items():
        slots[str(idx)] = dict(data)
        if isinstance(data, dict) and data.get("sock"):
            socket_slot = int(idx)

    return Result(
        status="ok",
        cartridge_id=params.cartridge_id or None,
        bl_idname=getattr(target, "bl_idname", None),
        slots=slots,
        socket_slot=socket_slot,
    )
