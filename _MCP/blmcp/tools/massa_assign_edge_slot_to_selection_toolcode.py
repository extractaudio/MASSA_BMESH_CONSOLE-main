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
    slot: int
    action: str
    object_name: str


class Result(NamedTuple):
    status: str
    object: str | None = None
    slot: int | None = None
    action: str | None = None
    edges_affected: list[int] | None = None
    count: int | None = None
    message: str | None = None


def main(params: Params) -> Result:
    import bpy
    import bmesh

    obj_name = params.object_name
    slot = params.slot
    action = params.action

    if obj_name:
        obj = bpy.data.objects.get(obj_name)
    else:
        obj = bpy.context.edit_object or bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        return Result(status="error", message="No mesh object available.")
    elif obj.mode != 'EDIT':
        return Result(
            status="error",
            message="Object '" + obj.name + "' must be in Edit Mode. Enter Edit Mode and select edges first."
        )

    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()

    slot_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
    if slot_layer is None:
        slot_layer = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

    bevel_layer = None
    crease_layer = None
    if action == "CREASE":
        crease_layer = bm.edges.layers.float.get("crease_edge")
        if crease_layer is None:
            crease_layer = bm.edges.layers.float.new("crease_edge")
    if action == "BEVEL":
        bevel_layer = bm.edges.layers.float.get("bevel_weight_edge")
        if bevel_layer is None:
            bevel_layer = bm.edges.layers.float.new("bevel_weight_edge")

    affected = []
    for e in bm.edges:
        if not e.select:
            continue
        e[slot_layer] = slot
        if action == "SEAM" or action == "BOTH":
            e.seam = True
        if action == "SHARP" or action == "BOTH":
            e.smooth = False
        if action == "CREASE":
            e[crease_layer] = 1.0
        if action == "BEVEL":
            e[bevel_layer] = 1.0
        # IGNORE: write slot only, leave edge attrs alone
        affected.append(e.index)

    bmesh.update_edit_mesh(obj.data)

    if not affected:
        return Result(status="error", message="No edges are selected. Select edges in Edit Mode first.")
    
    return Result(
        status="ok",
        object=obj.name,
        slot=slot,
        action=action,
        edges_affected=affected,
        count=len(affected),
    )
