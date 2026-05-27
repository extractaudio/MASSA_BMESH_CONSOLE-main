__all__ = ("Params", "Result", "main",)
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
    cartridge_snippet: str | None = None
    message: str | None = None

def main(params: Params) -> Result:
    import bpy
    import bmesh
    import textwrap

    obj_name = params.object_name
    slot = params.slot
    action = params.action.upper()

    obj = bpy.data.objects.get(obj_name) if obj_name else (bpy.context.edit_object or bpy.context.active_object)

    if obj is None or obj.type != 'MESH' or obj.mode != 'EDIT':
        return Result(status="error", message="No valid mesh object in Edit Mode.")

    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()

    slot_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
    bevel_layer = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
    crease_layer = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")

    affected = []
    target_midpoints = []

    for e in bm.edges:
        if e.select:
            e[slot_layer] = slot
            if action in ("SEAM", "BOTH"): e.seam = True
            if action in ("SHARP", "BOTH"): e.smooth = False
            if action == "CREASE": e[crease_layer] = 1.0
            if action == "BEVEL": e[bevel_layer] = 1.0
            
            affected.append(e.index)
            mid = e.calc_center_median()
            target_midpoints.append([round(mid.x, 5), round(mid.y, 5), round(mid.z, 5)])

    bmesh.update_edit_mesh(obj.data)

    if not affected:
        return Result(status="error", message="No edges selected.")

    b_seam = action in ("SEAM", "BOTH")
    b_sharp = action in ("SHARP", "BOTH")
    b_crease = action == "CREASE"
    b_bevel = action == "BEVEL"

    actions = [f"e[edge_layer] = {slot}"]
    if b_seam: actions.append("e.seam = True")
    if b_sharp: actions.append("e.smooth = False")
    if b_crease: actions.append("e[crease_layer] = 1.0")
    if b_bevel: actions.append("e[bevel_layer] = 1.0")
    action_block = "\n                    ".join(actions)

    snippet = textwrap.dedent(f"""\
        # --- PROCEDURAL EDGE ASSIGNMENT (SLOT {slot} | {action}) ---
        import mathutils
        edge_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS") or bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
        crease_layer = bm.edges.layers.float.get("crease_edge") or bm.edges.layers.float.new("crease_edge")
        bevel_layer = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
        
        target_mids = {target_midpoints}
        
        for e in bm.edges:
            mid = e.calc_center_median()
            for t_mid in target_mids:
                if (mid - mathutils.Vector(t_mid)).length_squared < 0.000001:
                    {action_block}
                    break
        # -----------------------------------------------------------
    """)

    return Result(
        status="ok", object=obj.name, slot=slot, action=action, 
        edges_affected=affected, count=len(affected), cartridge_snippet=snippet
    )