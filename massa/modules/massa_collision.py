import bpy
import bmesh
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix
import math
from bpy.app.handlers import persistent

# --- CACHE ---
# structure: { obj_name: { slot_id: { "shape": "BOX", "lines": [...], "timestamp": 12345 } } }
_collision_cache = {}

def get_slot_geometry_lines(obj, slot_id, shape_type):
    """
    Returns a list of line segments (start, end, start, end...) for the given slot.
    """
    # 1. Check Cache
    if obj.name in _collision_cache:
        slot_cache = _collision_cache[obj.name].get(slot_id)
        if slot_cache and slot_cache["shape"] == shape_type:
            return slot_cache["lines"]

    # 2. Calculate
    lines = _calculate_lines(obj, slot_id, shape_type)

    # 3. Store
    if obj.name not in _collision_cache:
        _collision_cache[obj.name] = {}
    _collision_cache[obj.name][slot_id] = {"shape": shape_type, "lines": lines}

    return lines

def _calculate_lines(obj, slot_id, shape_type):
    # This is heavy, so we do it carefully.
    mesh = obj.data
    if not mesh: return []

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()

    part_layer = bm.faces.layers.int.get("massa_part_id")
    if not part_layer:
        bm.free()
        return []

    # Collect vertices for this slot
    verts = set()
    edges = set()
    for f in bm.faces:
        if f[part_layer] == slot_id:
            for v in f.verts:
                verts.add(v)
            if shape_type == "MESH":
                for e in f.edges:
                    edges.add(e)

    if not verts:
        bm.free()
        return []

    points = [v.co.copy() for v in verts]
    # Keep BM alive for MESH processing if needed, else free now?
    # Actually we can copy edge data now
    mesh_lines = []
    if shape_type == "MESH":
        for e in edges:
            mesh_lines.append(e.verts[0].co.copy())
            mesh_lines.append(e.verts[1].co.copy())

    bm.free()  # Done with BMesh

    if not points:
        return []

    lines = []

    if shape_type == "MESH":
        lines = mesh_lines

    elif shape_type == "BOX":
        # AABB
        min_v = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
        max_v = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))

        # 12 edges of a box
        # Bottom
        p0 = Vector((min_v.x, min_v.y, min_v.z))
        p1 = Vector((max_v.x, min_v.y, min_v.z))
        p2 = Vector((max_v.x, max_v.y, min_v.z))
        p3 = Vector((min_v.x, max_v.y, min_v.z))
        # Top
        p4 = Vector((min_v.x, min_v.y, max_v.z))
        p5 = Vector((max_v.x, min_v.y, max_v.z))
        p6 = Vector((max_v.x, max_v.y, max_v.z))
        p7 = Vector((min_v.x, max_v.y, max_v.z))

        lines = [
            p0, p1, p1, p2, p2, p3, p3, p0, # Bottom Loop
            p4, p5, p5, p6, p6, p7, p7, p4, # Top Loop
            p0, p4, p1, p5, p2, p6, p3, p7  # Pillars
        ]

    elif shape_type == "HULL":
        # Convex Hull
        bm_hull = bmesh.new()
        for p in points:
            bm_hull.verts.new(p)

        try:
            bmesh.ops.convex_hull(bm_hull, input=bm_hull.verts)
            bm_hull.edges.ensure_lookup_table()
            for e in bm_hull.edges:
                lines.append(e.verts[0].co.copy())
                lines.append(e.verts[1].co.copy())
        except Exception:
            pass
        bm_hull.free()

    elif shape_type == "SPHERE":
        # Bounding Sphere (Center + Radius)
        min_v = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
        max_v = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
        center = (min_v + max_v) * 0.5
        radius = 0.0
        for p in points:
            d = (p - center).length
            if d > radius: radius = d

        segments = 16
        for axis in range(3):
            for i in range(segments):
                angle1 = (i / segments) * 2 * math.pi
                angle2 = ((i + 1) / segments) * 2 * math.pi

                v1 = Vector((0,0,0))
                v2 = Vector((0,0,0))

                if axis == 0: # XY
                    v1.x, v1.y = math.cos(angle1) * radius, math.sin(angle1) * radius
                    v2.x, v2.y = math.cos(angle2) * radius, math.sin(angle2) * radius
                elif axis == 1: # XZ
                    v1.x, v1.z = math.cos(angle1) * radius, math.sin(angle1) * radius
                    v2.x, v2.z = math.cos(angle2) * radius, math.sin(angle2) * radius
                else: # YZ
                    v1.y, v1.z = math.cos(angle1) * radius, math.sin(angle1) * radius
                    v2.y, v2.z = math.cos(angle2) * radius, math.sin(angle2) * radius

                lines.append(center + v1)
                lines.append(center + v2)

    elif shape_type == "CAPSULE":
        # Vertical Capsule (Z-Axis)
        min_z = min(p.z for p in points)
        max_z = max(p.z for p in points)

        # Radius in XY plane
        center_xy = Vector(((min(p.x for p in points) + max(p.x for p in points))*0.5, (min(p.y for p in points) + max(p.y for p in points))*0.5, 0))
        radius = 0.0
        for p in points:
            d = (Vector((p.x, p.y, 0)) - center_xy).length
            if d > radius: radius = d

        base_z = min_z
        top_z = max_z
        center = Vector((center_xy.x, center_xy.y, base_z))

        for z in [base_z, top_z]:
            c = Vector((center_xy.x, center_xy.y, z))
            for i in range(segments):
                angle1 = (i / segments) * 2 * math.pi
                angle2 = ((i + 1) / segments) * 2 * math.pi
                v1 = Vector((math.cos(angle1) * radius, math.sin(angle1) * radius, 0))
                v2 = Vector((math.cos(angle2) * radius, math.sin(angle2) * radius, 0))
                lines.append(c + v1)
                lines.append(c + v2)

        for i in range(4):
            angle = (i/4) * 2 * math.pi
            v = Vector((math.cos(angle) * radius, math.sin(angle) * radius, 0))
            lines.append(Vector((center.x + v.x, center.y + v.y, base_z)))
            lines.append(Vector((center.x + v.x, center.y + v.y, top_z)))

    return lines


# --- DRAW HANDLER ---
_handler = None
_shader = gpu.shader.from_builtin('UNIFORM_COLOR')

def draw():
    context = bpy.context
    if not context.scene: return
    console = getattr(context.scene, "massa_console", None)
    if not console: return

    # Check if we are in Collision Tab
    if console.ui_tab != "COLLISION": return

    obj = context.active_object
    if not obj or obj.type != 'MESH': return

    # Check Toggles
    slots_to_draw = []
    for i in range(10):
        if getattr(console, f"show_coll_{i}", False):
            shape = getattr(console, f"collision_shape_{i}", "BOX")
            slots_to_draw.append((i, shape))

    if not slots_to_draw: return

    # Draw
    matrix = obj.matrix_world

    _shader.bind()
    gpu.state.line_width_set(2)
    # X-Ray view for Wireframe Helper
    gpu.state.depth_test_set('NONE')

    for i, shape in slots_to_draw:
        lines = get_slot_geometry_lines(obj, i, shape)
        if lines:
            world_lines = [matrix @ p for p in lines]

            # Distinct Colors for Slots
            colors = [
                (1, 0, 0, 1), # 0 Red
                (1, 1, 0, 1), # 1 Yellow
                (0, 0.5, 1, 1), # 2 Blue
                (0, 1, 0, 1), # 3 Green
                (0, 1, 1, 1), # 4 Cyan
                (1, 0, 1, 1), # 5 Magenta
                (1, 0.5, 0, 1), # 6 Orange
                (0.5, 0, 1, 1), # 7 Purple
                (0.5, 1, 0, 1), # 8 Lime
                (1, 1, 1, 1) # 9 White
            ]

            _shader.uniform_float("color", colors[i % 10])
            batch = batch_for_shader(_shader, 'LINES', {"pos": world_lines})
            batch.draw(_shader)

    gpu.state.depth_test_set('LESS_EQUAL')


# --- UPDATE HANDLER ---

@persistent
def depsgraph_update_post(scene, depsgraph):
    for update in depsgraph.updates:
        if update.id.name in _collision_cache:
            if update.is_updated_geometry:
                 del _collision_cache[update.id.name]

def register():
    global _handler
    if _handler is None:
        _handler = bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

    if depsgraph_update_post not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post)

def unregister():
    global _handler
    if _handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handler, 'WINDOW')
        _handler = None

    if depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post)
