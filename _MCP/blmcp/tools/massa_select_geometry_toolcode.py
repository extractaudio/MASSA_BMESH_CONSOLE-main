# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tool-code for programmatic geometry selection inside a Massa mesh.

Selects verts/edges/faces by index list, all/none/invert, MASSA_EDGE_SLOTS edge
slot value, face material_index, face normal direction (with tolerance), or
seam/sharp edges. Pairs with massa_get_selected_geometry and the slot-tagging
tools so an agent never has to hand-write bmesh selection via execute_blender_code.
"""

__all__ = ("Params", "Result", "main")

from typing import NamedTuple


class Params(NamedTuple):
    object_name: str
    select_by: str          # INDEX | ALL | NONE | INVERT | EDGE_SLOT | MATERIAL | NORMAL | SEAM | SHARP
    domain: str             # VERT | EDGE | FACE
    indices: list[int]
    slot: int
    material_index: int
    normal: list[float]
    angle_tol: float        # degrees
    action: str             # SET | ADD | REMOVE


class Result(NamedTuple):
    status: str
    object: str | None = None
    domain: str | None = None
    selected_count: int | None = None
    selected_indices: list[int] | None = None
    truncated: bool | None = None
    message: str | None = None


_MAX_RETURN = 512


def main(params: Params) -> Result:
    import bpy
    import bmesh
    import math
    from mathutils import Vector

    obj = bpy.data.objects.get(params.object_name) if params.object_name else bpy.context.active_object
    if obj is None:
        return Result(status="error", message="Object '{:s}' was not found.".format(params.object_name))
    if obj.type != "MESH":
        return Result(status="error", object=obj.name, message="Object is {:s}, expected MESH.".format(obj.type))

    domain = (params.domain or "FACE").upper()
    if domain not in {"VERT", "EDGE", "FACE"}:
        return Result(status="error", object=obj.name, message="Invalid domain '{:s}'.".format(domain))
    by = (params.select_by or "INDEX").upper()
    action = (params.action or "SET").upper()

    try:
        if bpy.context.view_layer.objects.active is not obj:
            bpy.context.view_layer.objects.active = obj
        obj.hide_set(False)
        obj.select_set(True)
        if bpy.context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
        bpy.context.tool_settings.mesh_select_mode = (domain == "VERT", domain == "EDGE", domain == "FACE")

        bm = bmesh.from_edit_mesh(obj.data)
        seq = {"VERT": bm.verts, "EDGE": bm.edges, "FACE": bm.faces}[domain]
        seq.ensure_lookup_table()

        if action == "SET":
            for el in seq:
                el.select = False

        def _set(elements, value):
            for el in elements:
                el.select = value

        target_value = action != "REMOVE"

        if by == "ALL":
            _set(seq, target_value)
        elif by == "NONE":
            _set(seq, False)
        elif by == "INVERT":
            for el in seq:
                el.select = not el.select
        elif by == "INDEX":
            idx_set = set(params.indices)
            _set((el for el in seq if el.index in idx_set), target_value)
        elif by == "MATERIAL":
            if domain != "FACE":
                return Result(status="error", object=obj.name, message="MATERIAL selection requires domain=FACE.")
            _set((f for f in bm.faces if f.material_index == params.material_index), target_value)
        elif by == "EDGE_SLOT":
            if domain != "EDGE":
                return Result(status="error", object=obj.name, message="EDGE_SLOT selection requires domain=EDGE.")
            layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
            if layer is None:
                return Result(status="error", object=obj.name, message="Mesh has no MASSA_EDGE_SLOTS layer.")
            _set((e for e in bm.edges if e[layer] == params.slot), target_value)
        elif by == "SEAM":
            if domain != "EDGE":
                return Result(status="error", object=obj.name, message="SEAM selection requires domain=EDGE.")
            _set((e for e in bm.edges if e.seam), target_value)
        elif by == "SHARP":
            if domain != "EDGE":
                return Result(status="error", object=obj.name, message="SHARP selection requires domain=EDGE.")
            _set((e for e in bm.edges if not e.smooth), target_value)
        elif by == "NORMAL":
            if domain != "FACE":
                return Result(status="error", object=obj.name, message="NORMAL selection requires domain=FACE.")
            if len(params.normal) != 3:
                return Result(status="error", object=obj.name, message="normal must be 3 floats.")
            ref = Vector(params.normal)
            if ref.length == 0.0:
                return Result(status="error", object=obj.name, message="normal vector must be non-zero.")
            ref.normalize()
            cos_tol = math.cos(math.radians(params.angle_tol))
            _set((f for f in bm.faces if f.normal.normalized().dot(ref) >= cos_tol), target_value)
        else:
            return Result(status="error", object=obj.name, message="Unknown select_by '{:s}'.".format(by))

        bm.select_flush_mode()
        bmesh.update_edit_mesh(obj.data)

        selected = [el.index for el in seq if el.select]
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return Result(status="error", object=obj.name, message=str(exc))

    truncated = len(selected) > _MAX_RETURN
    return Result(
        status="ok",
        object=obj.name,
        domain=domain,
        selected_count=len(selected),
        selected_indices=selected[:_MAX_RETURN],
        truncated=truncated,
    )
