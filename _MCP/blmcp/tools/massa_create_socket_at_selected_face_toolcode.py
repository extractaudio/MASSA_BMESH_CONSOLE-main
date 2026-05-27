__all__ = ("Params", "Result", "main",)
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
    cartridge_snippet: str | None = None
    message: str | None = None

def main(params: Params) -> Result:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix
    import textwrap

    obj_name = params.object_name
    obj = bpy.data.objects.get(obj_name) if obj_name else (bpy.context.edit_object or bpy.context.active_object)
    
    if not obj or obj.mode != 'EDIT':
        return Result(status="error", message="Object must be in Edit mode.")

    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    
    target_centers = []
    created_sockets = []

    bpy.ops.object.mode_set(mode='OBJECT')

    for f in bm.faces:
        if f.select:
            c = f.calc_center_median()
            n = f.normal
            target_centers.append([round(c.x, 5), round(c.y, 5), round(c.z, 5)])
            
            empty = bpy.data.objects.new(f"SOCKET_{params.socket_name}", None)
            empty.empty_display_size = params.display_size
            empty.empty_display_type = 'ARROWS'
            bpy.context.collection.objects.link(empty)
            
            world_loc = obj.matrix_world @ c
            empty.location = world_loc
            
            if params.align_to_normal:
                z_axis = (obj.matrix_world.to_3x3() @ n).normalized()
                up = Vector((0, 0, 1)) if abs(z_axis.z) < 0.99 else Vector((0, 1, 0))
                x_axis = up.cross(z_axis).normalized()
                y_axis = z_axis.cross(x_axis).normalized()
                rot_mat = Matrix((x_axis, y_axis, z_axis)).transposed()
                empty.rotation_euler = rot_mat.to_euler()

            if params.parent_to_mesh:
                empty.parent = obj
                empty.matrix_parent_inverse = obj.matrix_world.inverted()
                
            created_sockets.append({"name": empty.name, "location": list(empty.location)})

    bpy.ops.object.mode_set(mode='EDIT')

    if not target_centers:
        return Result(status="error", message="No faces selected for socket creation.")

    snippet = textwrap.dedent(f"""\
        # --- PROCEDURAL SOCKET TAGGING ({params.socket_name}) ---
        # Note: Set socket_slot_index to the designated 'sock': True slot
        import mathutils
        socket_target_centers = {target_centers}
        socket_slot_index = 3 
        
        for f in bm.faces:
            c = f.calc_center_median()
            for tc in socket_target_centers:
                if (c - mathutils.Vector(tc)).length_squared < 0.000001:
                    f.material_index = socket_slot_index
                    break
        # --------------------------------------------------------
    """)

    return Result(
        status="ok", object=obj.name, sockets_created=created_sockets,
        count=len(target_centers), cartridge_snippet=snippet
    )