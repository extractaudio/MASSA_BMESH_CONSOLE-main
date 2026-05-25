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
    socket_name: str
    object_name: str
    parent_to_mesh: bool
    align_to_normal: bool
    display_size: float


class Result(NamedTuple):
    status: str
    object: str | None = None
    sockets_created: list[dict[str, object]] | None = None
    count: int | None = None
    message: str | None = None


def main(params: Params) -> Result:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix

    obj_name = params.object_name
    socket_name = params.socket_name
    parent_to_mesh = params.parent_to_mesh
    align_to_normal = params.align_to_normal
    display_size = params.display_size

    if obj_name:
        obj = bpy.data.objects.get(obj_name)
    else:
        obj = bpy.context.edit_object or bpy.context.active_object

    if obj is None or obj.type != 'MESH':
        return Result(status="error", message="No mesh object available.")
    elif obj.mode != 'EDIT':
        return Result(
            status="error",
            message="Object '" + obj.name + "' must be in Edit Mode with face(s) selected.",
        )

    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    mw = obj.matrix_world
    mw_rs = mw.to_3x3()

    selected = [f for f in bm.faces if f.select]
    if not selected:
        return Result(status="error", message="No faces are selected. Switch to face-select mode.")
    
    created = []
    multi = (len(selected) > 1)
    for i, f in enumerate(selected):
        center_world = mw @ f.calc_center_median()

        if align_to_normal:
            z = (mw_rs @ f.normal)
            if z.length == 0:
                z = Vector((0.0, 0.0, 1.0))
            else:
                z = z.normalized()
            up = Vector((0.0, 0.0, 1.0)) if abs(z.z) < 0.95 else Vector((1.0, 0.0, 0.0))
            x = up.cross(z).normalized()
            y = z.cross(x).normalized()
            rot_mat = Matrix((x, y, z)).transposed().to_4x4()
        else:
            rot_mat = Matrix.Identity(4)

        name = (socket_name + ("_{:02d}".format(i + 1) if multi else ""))
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = 'ARROWS'
        empty.empty_display_size = display_size
        bpy.context.collection.objects.link(empty)

        world_mat = Matrix.Translation(center_world) @ rot_mat
        if parent_to_mesh:
            empty.parent = obj
            empty.matrix_world = world_mat
        else:
            empty.matrix_world = world_mat

        created.append({
            "name": empty.name,
            "face_index": f.index,
            "location_world": [round(c, 6) for c in empty.matrix_world.translation],
            "rotation_euler": [round(c, 6) for c in empty.rotation_euler],
            "parent": (obj.name if parent_to_mesh else None),
        })

    return Result(
        status="ok",
        object=obj.name,
        sockets_created=created,
        count=len(created),
    )
