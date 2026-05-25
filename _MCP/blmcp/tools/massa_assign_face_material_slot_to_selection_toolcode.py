# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

__all__ = (
    "Params",
    "Result",
    "main",
)

from typing import NamedTuple


class Params(NamedTuple):
    slot_index: int
    object_name: str


class Result(NamedTuple):
    status: str
    object: str | None = None
    slot_index: int | None = None
    material_name: str | None = None
    faces_affected: list[int] | None = None
    count: int | None = None
    message: str | None = None


def main(params: Params) -> Result:
    import bpy
    import bmesh

    obj_name = params.object_name
    slot_index = params.slot_index

    if obj_name:
        obj = bpy.data.objects.get(obj_name)
    else:
        obj = bpy.context.edit_object or bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        return Result(status="error", message="No mesh object available.")
    elif obj.mode != 'EDIT':
        return Result(status="error", message="Object '" + obj.name + "' must be in Edit Mode.")
    elif slot_index >= len(obj.material_slots):
        return Result(
            status="error",
            message="slot_index " + str(slot_index) + " is out of range; object has " + str(len(obj.material_slots)) + " material slot(s). Append a slot first.",
        )

    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    affected = []
    for f in bm.faces:
        if f.select:
            f.material_index = slot_index
            affected.append(f.index)

    bmesh.update_edit_mesh(obj.data)

    if not affected:
        return Result(
            status="error",
            message="No faces are selected. Switch to face-select mode and select faces.",
        )
    
    ms = obj.material_slots[slot_index]
    mat_name = ms.material.name if ms.material else None
    return Result(
        status="ok",
        object=obj.name,
        slot_index=slot_index,
        material_name=mat_name,
        faces_affected=affected,
        count=len(affected),
    )
