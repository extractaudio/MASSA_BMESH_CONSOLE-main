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
    object_name: str
    include_world_coords: bool
    coord_precision: int


class Result(NamedTuple):
    status: str
    object: str | None = None
    mode: str | None = None
    in_edit_mode: bool | None = None
    select_mode: list[str] | None = None
    active_element: dict[str, object] | None = None
    world_matrix: list[list[float]] | None = None
    selected: dict[str, list[dict[str, object]]] | None = None
    stats: dict[str, object] | None = None
    message: str | None = None


def main(params: Params) -> Result:
    import bpy
    import bmesh

    obj_name = params.object_name
    include_world = params.include_world_coords
    prec = params.coord_precision

    if obj_name:
        obj = bpy.data.objects.get(obj_name)
    elif bpy.context.edit_object is not None:
        obj = bpy.context.edit_object
    else:
        obj = bpy.context.active_object

    if obj is None:
        return Result(status="error", message="No object specified or active.")
    elif obj.type != 'MESH':
        return Result(status="error", message="Object '" + obj.name + "' is type " + obj.type + ", expected MESH.")

    in_edit = (bpy.context.edit_object is obj) or (obj.mode == 'EDIT')

    bm = None
    owns_bm = False
    try:
        if in_edit:
            bm = bmesh.from_edit_mesh(obj.data)
        else:
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            owns_bm = True

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        slot_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        bevel_layer = bm.edges.layers.float.get("bevel_weight_edge")
        crease_layer = bm.edges.layers.float.get("crease_edge")

        mw = obj.matrix_world
        mw_rs = mw.to_3x3()

        def r(v):
            return round(float(v), prec)

        def vec_l(c):
            return [r(c.x), r(c.y), r(c.z)]

        def vec_w(c):
            w = mw @ c
            return [r(w.x), r(w.y), r(w.z)]

        def nrm_w(n):
            wn = (mw_rs @ n)
            if wn.length > 0:
                wn = wn.normalized()
            return [r(wn.x), r(wn.y), r(wn.z)]

        sel_verts = []
        for v in bm.verts:
            if not v.select:
                continue
            entry = {
                "index": v.index,
                "co_local": vec_l(v.co),
                "is_boundary": v.is_boundary,
                "edge_count": len(v.link_edges),
            }
            if include_world:
                entry["co_world"] = vec_w(v.co)
            sel_verts.append(entry)

        sel_edges = []
        for e in bm.edges:
            if not e.select:
                continue
            va, vb = e.verts
            mid = (va.co + vb.co) * 0.5
            entry = {
                "index": e.index,
                "vert_indices": [va.index, vb.index],
                "v_co_local": [vec_l(va.co), vec_l(vb.co)],
                "midpoint_local": vec_l(mid),
                "length": r(e.calc_length()),
                "is_seam": bool(e.seam),
                "is_sharp": (not bool(e.smooth)),
                "is_boundary": e.is_boundary,
                "current_edge_slot": (e[slot_layer] if slot_layer is not None else 0),
                "face_count": len(e.link_faces),
            }
            if include_world:
                entry["v_co_world"] = [vec_w(va.co), vec_w(vb.co)]
                entry["midpoint_world"] = vec_w(mid)
            if bevel_layer is not None:
                entry["bevel_weight"] = r(e[bevel_layer])
            if crease_layer is not None:
                entry["crease"] = r(e[crease_layer])
            sel_edges.append(entry)

        sel_faces = []
        for f in bm.faces:
            if not f.select:
                continue
            center = f.calc_center_median()
            entry = {
                "index": f.index,
                "vert_indices": [v.index for v in f.verts],
                "loop_count": len(f.verts),
                "center_local": vec_l(center),
                "normal_local": vec_l(f.normal),
                "area": r(f.calc_area()),
                "material_index": f.material_index,
                "is_smooth": bool(f.smooth),
            }
            if include_world:
                entry["center_world"] = vec_w(center)
                entry["normal_world"] = nrm_w(f.normal)
            sel_faces.append(entry)

        active = None
        if in_edit and len(bm.select_history) > 0:
            ah = bm.select_history[-1]
            if isinstance(ah, bmesh.types.BMVert):
                active = {"type": "VERT", "index": ah.index}
            elif isinstance(ah, bmesh.types.BMEdge):
                active = {"type": "EDGE", "index": ah.index}
            elif isinstance(ah, bmesh.types.BMFace):
                active = {"type": "FACE", "index": ah.index}

        if in_edit:
            sm_tuple = bm.select_mode
            select_mode_names = []
            if 'VERT' in sm_tuple: select_mode_names.append('VERT')
            if 'EDGE' in sm_tuple: select_mode_names.append('EDGE')
            if 'FACE' in sm_tuple: select_mode_names.append('FACE')
        else:
            select_mode_names = []

        world_matrix = None
        if include_world:
            world_matrix = [[r(x) for x in row] for row in mw]

        return Result(
            status="ok",
            object=obj.name,
            mode=bpy.context.mode,
            in_edit_mode=in_edit,
            select_mode=select_mode_names,
            active_element=active,
            world_matrix=world_matrix,
            selected={
                "verts": sel_verts,
                "edges": sel_edges,
                "faces": sel_faces,
            },
            stats={
                "selected_vert_count": len(sel_verts),
                "selected_edge_count": len(sel_edges),
                "selected_face_count": len(sel_faces),
                "total_verts": len(bm.verts),
                "total_edges": len(bm.edges),
                "total_faces": len(bm.faces),
                "massa_edge_slot_layer_present": (slot_layer is not None),
            },
        )
    finally:
        if owns_bm and bm is not None:
            bm.free()
