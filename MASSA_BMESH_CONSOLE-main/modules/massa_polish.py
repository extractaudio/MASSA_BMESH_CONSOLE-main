import bpy
import bmesh
import math
import random
from mathutils import Vector, noise
from . import massa_nodes


# --- TRANSFORMS ---
def apply_transform_alignment(bm, mode):
    if mode == "ORIGIN" or not bm.verts:
        return
    inf = float("inf")
    min_v, max_v = Vector((inf, inf, inf)), Vector((-inf, -inf, -inf))
    for v in bm.verts:
        co = v.co
        min_v.x, min_v.y, min_v.z = (
            min(min_v.x, co.x),
            min(min_v.y, co.y),
            min(min_v.z, co.z),
        )
        max_v.x, max_v.y, max_v.z = (
            max(max_v.x, co.x),
            max(max_v.y, co.y),
            max(max_v.z, co.z),
        )
    center = (min_v + max_v) / 2
    offset = Vector((0, 0, 0))
    if mode == "Z_MIN":
        offset = Vector((-center.x, -center.y, -min_v.z))
    elif mode == "CENTER":
        offset = -center
    elif mode == "Z_MAX":
        offset = Vector((-center.x, -center.y, -max_v.z))
    if offset.length_squared > 0.000001:
        bmesh.ops.translate(bm, vec=offset, verts=bm.verts)


def apply_slot_inflation(bm, op):
    offset_map = {}
    for i in range(10):
        off = getattr(op, f"off_{i}", 0.0)
        if abs(off) > 0.00001:
            offset_map[i] = off * op.global_scale
    if not offset_map:
        return
    bm.verts.ensure_lookup_table()
    vert_offsets = {}
    for f in bm.faces:
        off = offset_map.get(f.material_index, 0.0)
        if abs(off) < 0.00001:
            continue
        for v in f.verts:
            if abs(off) > abs(vert_offsets.get(v, 0.0)):
                vert_offsets[v] = off
    for v, off in vert_offsets.items():
        v.co += v.normal * off


def apply_protection_mask(bm, manifest):
    if not bm.verts:
        return
    bm.verts.ensure_lookup_table()
    noise_layer = bm.verts.layers.float.get(
        "massa_noise_mask"
    ) or bm.verts.layers.float.new("massa_noise_mask")
    for v in bm.verts:
        v[noise_layer] = 1.0
    for f in bm.faces:
        if manifest.get(f.material_index, {}).get("prot", False):
            for v in f.verts:
                v[noise_layer] = 0.0


# --- MERGE / FUSE OPERATIONS ---


def apply_hard_merge(bm, mode="NONE", dist=0.001):
    """
    Handles geometric merging.
    WELD: Merges touching vertices.
    BOOLEAN: Intersects overlapping volumes (Creates Edges for Seams).
    """
    if mode == "NONE":
        return

    if mode == "WELD":
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)

    elif mode == "BOOLEAN":
        # Robust Boolean Strategy:
        # 1. Self-Intersect faces to create cut edges where meshes overlap
        # 2. Weld to fuse the geometry
        try:
            bmesh.ops.intersect_edges(bm, edges=bm.edges[:], use_self=True)
            # Cleanup resulting artifacts
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        except Exception as e:
            print(f"Massa Boolean Error: {e}")
            pass


def apply_sdf_fuse(obj, op):
    """Applies the SDF Fuse Modifier (Geometry Nodes)."""
    mod_name = "Massa_Fuse"
    mod = obj.modifiers.get(mod_name)
    if not mod:
        mod = obj.modifiers.new(mod_name, "NODES")
        mod.node_group = massa_nodes.get_or_create_sdf_fuse_tree()

    bevel_rad = max(0.001, op.pol_fuse_radius)
    res = int(8.0 / bevel_rad)
    res = max(64, min(res, 350))
    mod["Resolution"] = res


# --- POLISH STACK ---


def apply_decay(bm, manifest, strength, seed):
    if strength <= 0.0:
        return
    rng = random.Random(seed)
    faces_to_delete = []
    for f in bm.faces:
        if manifest.get(f.material_index, {}).get("prot", False):
            continue
        if rng.random() < strength:
            faces_to_delete.append(f)
    if faces_to_delete:
        bmesh.ops.delete(bm, geom=faces_to_delete, context="FACES")
        bmesh.ops.delete(
            bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS"
        )


def apply_plating(bm, manifest, thickness, depth):
    if thickness <= 0.0001:
        return
    targets = [
        f for f in bm.faces if not manifest.get(f.material_index, {}).get("prot", False)
    ]
    if targets:
        try:
            bmesh.ops.inset_individual(
                bm,
                faces=targets,
                thickness=thickness,
                depth=depth,
                use_even_offset=True,
            )
            bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=True, faces=True)
        except:
            pass


def apply_taper(bm, taper_x, taper_y, curve=1.0, mirror=False, invert=False):
    if abs(taper_x) < 0.001 and abs(taper_y) < 0.001:
        return
    verts = [v for v in bm.verts if v.is_valid]
    if not verts:
        return
    min_z = min([v.co.z for v in verts])
    max_z = max([v.co.z for v in verts])
    height = max_z - min_z
    if height < 0.0001:
        return

    for v in verts:
        h_fac = (v.co.z - min_z) / height

        if mirror:
            h_fac = 1.0 - abs(h_fac - 0.5) * 2.0

        if invert:
            h_fac = 1.0 - h_fac

        if curve != 1.0 and h_fac > 0.0:
            h_fac = pow(h_fac, curve)

        v.co.x *= 1.0 - (h_fac * taper_x)
        v.co.y *= 1.0 - (h_fac * taper_y)


def apply_bend(bm, angle, axis="X"):
    if abs(angle) < 0.001 or not bm.verts:
        return

    verts = [v for v in bm.verts if v.is_valid]
    if not verts:
        return

    min_z = min([v.co.z for v in verts])
    max_z = max([v.co.z for v in verts])
    height = max_z - min_z
    if height < 0.001:
        return

    if axis == "Z":
        # Twist logic
        for v in verts:
            theta = ((v.co.z - min_z) / height) * angle
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            x = v.co.x
            y = v.co.y
            v.co.x = x * cos_t - y * sin_t
            v.co.y = x * sin_t + y * cos_t
        return

    # Bend logic (X or Y)
    radius = height / angle

    for v in verts:
        z_norm = (v.co.z - min_z)
        theta = (z_norm / height) * angle

        if axis == "X":
            r_cur = radius - v.co.x
            v.co.x = radius - r_cur * math.cos(theta)
            v.co.z = min_z + r_cur * math.sin(theta)

        elif axis == "Y":
            r_cur = radius - v.co.y
            v.co.y = radius - r_cur * math.cos(theta)
            v.co.z = min_z + r_cur * math.sin(theta)


def apply_noise(bm, strength, scale, seed, global_scale):
    if strength <= 0.0001:
        return
    ns = scale / (global_scale * 0.2) if global_scale > 0 else 10.0
    off = Vector((seed * 13.0, seed * 47.0, seed * 19.0))
    bm.verts.ensure_lookup_table()
    noise_layer = bm.verts.layers.float.get("massa_noise_mask")
    for v in bm.verts:
        mult = v[noise_layer] if noise_layer else 1.0
        if mult < 0.01:
            continue
        val = noise.noise((v.co + off) * ns)
        v.co += v.normal * ((val - 0.2) * strength * mult)


def apply_smooth(bm, iterations, factor):
    if iterations < 1:
        return
    bmesh.ops.smooth_vert(
        bm,
        verts=bm.verts[:],
        factor=factor,
        use_axis_x=True,
        use_axis_y=True,
        use_axis_z=True,
    )


def apply_chamfer(bm, width, segments, is_square=False, angle_limit=0.05):
    if width <= 0.00001:
        return
    bm.edges.ensure_lookup_table()
    targets = []
    for e in bm.edges:
        if e.is_manifold:
            try:
                if e.calc_face_angle_signed() > angle_limit:
                    targets.append(e)
            except ValueError:
                continue
    if targets:
        prof = 1.0 if is_square else 0.5
        try:
            bmesh.ops.bevel(
                bm,
                geom=targets,
                offset=width,
                segments=int(segments),
                profile=prof,
                clamp_overlap=True,
                loop_slide=True,
                material=-1,
            )
        except:
            pass


def apply_concave_bevel(bm, width, segments, is_square=False):
    if width <= 0.00001:
        return
    bm.edges.ensure_lookup_table()
    concave = []
    for e in bm.edges:
        if e.is_manifold:
            try:
                if e.calc_face_angle_signed() < math.radians(-1.0):
                    concave.append(e)
            except ValueError:
                continue
    if concave:
        prof = 1.0 if is_square else 0.5
        try:
            bmesh.ops.bevel(
                bm,
                geom=concave,
                offset=width,
                segments=int(segments),
                profile=prof,
                clamp_overlap=False,
                loop_slide=True,
                material=-1,
            )
        except:
            pass


def apply_safety_decimate(bm, target_count=1000000):
    if len(bm.verts) <= target_count:
        return
    try:
        bmesh.ops.dissolve_limit(
            bm,
            angle_limit=math.radians(1.0),
            use_dissolve_boundaries=False,
            verts=bm.verts[:],
        )
    except:
        pass


def apply_solidify(bm, thickness):
    if abs(thickness) < 0.0001 or not bm.faces:
        return
    try:
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thickness)
    except:
        pass


def apply_triangulate(bm, method="BEAUTY"):
    try:
        bmesh.ops.triangulate(
            bm, faces=bm.faces[:], quad_method=method, ngon_method=method
        )
    except:
        pass


def apply_fill_holes(bm, sides=4):
    try:
        bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=sides)
    except:
        pass


def apply_symmetrize(bm, direction="POS_X", offset=0.0):
    dirs = {"POS_X": 0, "POS_Y": 1, "POS_Z": 2, "NEG_X": 3, "NEG_Y": 4, "NEG_Z": 5}
    dir_idx = dirs.get(direction, 0)

    # Calculate offset vector
    off_vec = Vector((0,0,0))
    if dir_idx in {0, 3}: # X axis
        off_vec.x = -offset
    elif dir_idx in {1, 4}: # Y axis
        off_vec.y = -offset
    elif dir_idx in {2, 5}: # Z axis
        off_vec.z = -offset

    if off_vec.length_squared > 0.000001:
        bmesh.ops.translate(bm, vec=off_vec, verts=bm.verts[:])

    try:
        bmesh.ops.symmetrize(
            bm,
            input=bm.verts[:] + bm.edges[:] + bm.faces[:],
            direction=dir_idx,
            dist=0.005,
        )
    except Exception as e:
        print(f"Massa Symmetrize Error: {e}")

    # Restore position
    if off_vec.length_squared > 0.000001:
        bmesh.ops.translate(bm, vec=-off_vec, verts=bm.verts[:])


def apply_bridge_loops(bm):
    edges = [e for e in bm.edges if e.is_boundary]
    if edges:
        try:
            bmesh.ops.bridge_loops(bm, edges=edges, use_pairs=True, use_merge=True)
        except:
            pass


# --- SEPARATION LOGIC ---
def handle_separation(obj, op, manifest, context):
    final_sel = [obj]

    # [ARCHITECT FIX] Ensure Fuse is baked before separation logic
    if op.pol_fuse_active and "Massa_Fuse" in obj.modifiers:
         if any(getattr(op, f"sep_{i}", False) for i in range(10)):
             try:
                 context.view_layer.objects.active = obj
                 bpy.ops.object.modifier_apply(modifier="Massa_Fuse")
             except:
                 pass

    for i in range(10):
        if not getattr(op, f"sep_{i}", False):
            continue

        bpy.ops.object.select_all(action="DESELECT")
        context.view_layer.objects.active = obj
        obj.select_set(True)
        if not obj.data.vertices:
            break

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bm = bmesh.from_edit_mesh(obj.data)
        found = False
        for f in bm.faces:
            if f.material_index == i:
                f.select = True
                found = True
        bmesh.update_edit_mesh(obj.data)

        if found:
            try:
                bpy.ops.mesh.separate(type="SELECTED")
            except Exception:
                pass
            bpy.ops.object.mode_set(mode="OBJECT")
            new_parts = [o for o in context.selected_objects if o != obj]
            if new_parts:
                p = new_parts[0]
                safe = "".join(
                    c for c in manifest[i]["name"] if c.isalnum() or c in (" ", "_")
                ).strip()
                p.name = f"{op.bl_label}_{safe}"
                
                # [ARCHITECT FIX] Parent to Main Object for Cleaner Outliner & Redo Support
                p.parent = obj
                p.matrix_parent_inverse = obj.matrix_world.inverted()
                
                final_sel.append(p)
        else:
            bpy.ops.object.mode_set(mode="OBJECT")

    bpy.ops.object.select_all(action="DESELECT")
    for o in final_sel:
        o.select_set(True)
    if final_sel:
        context.view_layer.objects.active = final_sel[0]
