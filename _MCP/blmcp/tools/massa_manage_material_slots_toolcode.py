# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for inspecting / creating material slots on a Massa object.

massa_assign_face_material_slot_to_selection assumes the target slot already
exists; this tool lets an agent list slots and add/ensure enough slots first.
"""

__all__ = ("Params", "Result", "main")

from typing import NamedTuple, Any


class Params(NamedTuple):
    object_name: str
    action: str             # LIST | ADD | ENSURE
    count: int              # ENSURE: ensure at least this many slots
    names: list[str]        # ADD: material names to append (created if missing)


class Result(NamedTuple):
    status: str
    object: str | None = None
    action: str | None = None
    slot_count: int | None = None
    slots: list[dict[str, Any]] | None = None
    added: list[str] | None = None
    message: str | None = None


def _slot_list(obj):
    out = []
    for i, slot in enumerate(obj.material_slots):
        mat = slot.material
        out.append({
            "index": i,
            "material": mat.name if mat else None,
            "link": slot.link,
        })
    return out


def main(params: Params) -> Result:
    import bpy

    obj = bpy.data.objects.get(params.object_name) if params.object_name else bpy.context.active_object
    if obj is None:
        return Result(status="error", message="Object '{:s}' was not found.".format(params.object_name))
    if obj.type != "MESH":
        return Result(status="error", object=obj.name, message="Object is {:s}, expected MESH.".format(obj.type))

    action = (params.action or "LIST").upper()
    added: list[str] = []

    try:
        if bpy.context.view_layer.objects.active is not obj:
            bpy.context.view_layer.objects.active = obj
        if bpy.context.object and bpy.context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        if action == "ADD":
            for name in params.names:
                mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
                obj.data.materials.append(mat)
                added.append(mat.name)
        elif action == "ENSURE":
            while len(obj.data.materials) < params.count:
                obj.data.materials.append(None)
                added.append("(empty slot {:d})".format(len(obj.data.materials) - 1))
        elif action != "LIST":
            return Result(status="error", object=obj.name, message="Unknown action '{:s}'.".format(action))
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return Result(status="error", object=obj.name, action=action, message=str(exc))

    return Result(
        status="ok",
        object=obj.name,
        action=action,
        slot_count=len(obj.material_slots),
        slots=_slot_list(obj),
        added=added,
    )
