__all__ = ("Params", "Result", "main",)
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
    cartridge_snippet: str | None = None
    message: str | None = None

def main(params: Params) -> Result:
    import bpy
    import bmesh
    import textwrap

    obj_name = params.object_name
    slot_index = params.slot_index

    obj = bpy.data.objects.get(obj_name) if obj_name else (bpy.context.edit_object or bpy.context.active_object)

    if obj is None or obj.type != 'MESH' or obj.mode != 'EDIT':
        return Result(status="error", message="No valid mesh object in Edit Mode.")
    if slot_index >= len(obj.material_slots):
        return Result(status="error", message=f"slot_index {slot_index} out of range.")

    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    affected = []
    target_centers = []

    for f in bm.faces:
        if f.select:
            f.material_index = slot_index
            affected.append(f.index)
            c = f.calc_center_median()
            target_centers.append([round(c.x, 5), round(c.y, 5), round(c.z, 5)])

    bmesh.update_edit_mesh(obj.data)

    if not affected:
        return Result(status="error", message="No faces selected.")

    snippet = textwrap.dedent(f"""\
        # --- PROCEDURAL FACE MATERIAL ASSIGNMENT (SLOT {slot_index}) ---
        import mathutils
        target_centers = {target_centers}
        
        for f in bm.faces:
            c = f.calc_center_median()
            for tc in target_centers:
                if (c - mathutils.Vector(tc)).length_squared < 0.000001:
                    f.material_index = {slot_index}
                    break
        # -----------------------------------------------------------
    """)

    ms = obj.material_slots[slot_index]
    return Result(
        status="ok", object=obj.name, slot_index=slot_index, 
        material_name=ms.material.name if ms.material else None,
        faces_affected=affected, count=len(affected), cartridge_snippet=snippet
    )