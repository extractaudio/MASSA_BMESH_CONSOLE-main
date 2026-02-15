import bmesh
import math
import random
import bpy
from mathutils import Vector, kdtree, noise
from mathutils.bvhtree import BVHTree
from ..utils import mat_utils


def gather_manifest(op):
    manifest = {}
    active_sockets = []
    slot_names = {}
    if hasattr(op, "get_slot_meta"):
        slot_names = {
            k: v.get("name", f"Slot_{k}") for k, v in op.get_slot_meta().items()
        }

    for i in range(10):
        manifest[i] = {
            "name": slot_names.get(i, f"Slot_{i}"),
            "uv": getattr(op, f"uv_mode_{i}", "SKIP"),
            "uv_scale": getattr(op, f"uv_scale_{i}", 1.0),
            "phys": getattr(op, f"phys_mat_{i}", "GENERIC"),
            "prot": getattr(op, f"prot_{i}", False),
        }
        if getattr(op, f"sock_{i}", False):
            active_sockets.append(i)
    return manifest, active_sockets


def calculate_physical_stats(bm, manifest):
    """
    Calculates Volume and Weighted Mass.
    Formula: Total_Volume * Sum((Slot_Area / Total_Area) * Slot_Density)
    """
    try:
        vol = bm.calc_volume(signed=True)
        vol = abs(vol)
    except:
        vol = 0.0

    if vol < 0.000001:
        return 0.0, 0.0

    total_area = 0.0
    slot_areas = {}

    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        a = f.calc_area()
        total_area += a
        idx = f.material_index
        slot_areas[idx] = slot_areas.get(idx, 0.0) + a

    total_mass = 0.0

    # Weighted Average Density Calculation
    if total_area > 0.000001:
        for idx, area in slot_areas.items():
            # Get Phys ID from manifest
            phys_id = manifest.get(idx, {}).get("phys", "GENERIC")
            dens = mat_utils.get_density(phys_id)

            # Ratio of this material on the surface
            ratio = area / total_area

            # Contribution to total mass
            total_mass += (vol * ratio) * dens

    return vol, total_mass


def assign_materials(obj, op):
    """
    Assigns final or debug materials.
    [ARCHITECT FIX]: Implements 'Law of the Hard 10'.
    Forces Object to have 10 materials. If user selected NONE, uses Debug Slot Color.
    """
    debug_v = getattr(op, "debug_view", "NONE")
    viz_mode = getattr(op, "viz_edge_mode", "NATIVE")
    override_mat = None

    # 1. Determine Global Override (Standard Debugs)
    if debug_v != "NONE":
        if debug_v == "UV":
            override_mat = mat_utils.create_debug_uv_material()
        elif debug_v == "WEAR":
            override_mat = mat_utils.create_debug_channel_material(0)
        elif debug_v == "THICK":
            override_mat = mat_utils.create_debug_channel_material(1)
        elif debug_v == "GRAV":
            override_mat = mat_utils.create_debug_channel_material(2)
        elif debug_v == "CAVITY":
            override_mat = mat_utils.create_debug_channel_material(3)
        elif debug_v == "PHYS":
            override_mat = mat_utils.create_debug_physics_material()
        elif debug_v == "PARTS":
            override_mat = mat_utils.create_debug_part_id_material()
        elif debug_v == "PROTECT":
            override_mat = mat_utils.create_debug_protect_material()
        elif debug_v == "SEAM":
            override_mat = mat_utils.create_debug_neutral_material()
    elif viz_mode == "SLOTS":
        # Do not override in SLOTS mode (let real mats show through wireframe)
        override_mat = None

    # 2. Apply to Object
    # We clear any existing, then forcefully pad to 10
    obj.data.materials.clear()
    
    # Ensure all debug mats exist
    mat_utils.ensure_default_library()

    for i in range(10):
        if override_mat:
            # Debug Mode: All slots use the debug shader, preserving index logic
            obj.data.materials.append(override_mat)
        else:
            # Final Mode: Load actual slot material or fallback to Debug Color
            mat_name = getattr(op, f"mat_{i}", "NONE")
            mat = mat_utils.load_material_smart(mat_name)
            
            if not mat:
                # If NONE or invalid, use the visual debug slot color (e.g. Red for 1)
                debug_name = mat_utils.get_debug_mat_name(i)
                mat = mat_utils.load_material_smart(debug_name)
            
            if mat:
                obj.data.materials.append(mat)
            else:
                # Last resort fallback to prevent index crash
                placeholder = mat_utils.get_or_create_placeholder_material()
                obj.data.materials.append(placeholder)


def write_identity_layers(bm, manifest, op):
    stats = {}
    if not bm.verts:
        return stats
    bm.faces.ensure_lookup_table()
    global_scale = getattr(op, "global_scale", 1.0)

    debug_view = getattr(op, "debug_view", "NONE")
    force_uv_preview = debug_view == "UV"

    # [ARCHITECT FIX] Explicit Layer Naming (Critical for Shaders)

    # 1. UV Map (Required for UV Debug)
    try:
        uv_layer = bm.loops.layers.uv.get("UVMap")
        if not uv_layer:
            uv_layer = bm.loops.layers.uv.new("UVMap")
    except:
        uv_layer = bm.loops.layers.uv.verify()  # Fallback
        uv_layer.name = "UVMap"

    # 2. Physics ID (Required for PHYS Debug)
    phys_layer = None
    if getattr(op, "phys_active", True):
        phys_layer = bm.faces.layers.int.get("massa_phys_id")
        if not phys_layer:
            phys_layer = bm.faces.layers.int.new("massa_phys_id")

    # 3. Part ID (Required for PARTS Debug)
    part_layer = None
    if getattr(op, "part_active", True):
        part_layer = bm.faces.layers.int.get("massa_part_id")
        if not part_layer:
            part_layer = bm.faces.layers.int.new("massa_part_id")

    # 4. Protection Mask (Required for PROTECT Debug)
    prot_layer = bm.faces.layers.float.get("massa_protect")
    if not prot_layer:
        prot_layer = bm.faces.layers.float.new("massa_protect")

    # Process Faces
    face_groups = {}
    for f in bm.faces:
        face_groups.setdefault(f.material_index, []).append(f)

    for idx, faces in face_groups.items():
        cfg = manifest.get(idx, {})
        c_phys = cfg.get("phys", "GENERIC")
        c_uv_mode = cfg.get("uv", "SKIP")
        c_uv_scl = cfg.get("uv_scale", 1.0)
        is_prot = cfg.get("prot", False)

        p_id = mat_utils.PHYS_ID_MAP.get(c_phys, 0)
        prot_val = 1.0 if is_prot else 0.0

        for f in faces:
            if phys_layer:
                f[phys_layer] = p_id
            if part_layer:
                f[part_layer] = idx
            f[prot_layer] = prot_val

        # Logic: If looking at UV Debug, we force a box map if the user set "SKIP"
        # Otherwise the UV map would be empty and the debugger would show nothing.
        mode_to_use = c_uv_mode
        if force_uv_preview and c_uv_mode == "SKIP":
            mode_to_use = "BOX"

        if mode_to_use != "SKIP":
            _apply_uv(faces, mode_to_use, uv_layer, global_scale * c_uv_scl)

        stats[idx] = _calc_uv_ratio(faces, uv_layer)

    return stats


def _apply_uv(faces, mode, uv_layer, scale):
    if mode == "UNWRAP":
        pass
    elif mode == "BOX":
        for f in faces:
            nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
            for l in f.loops:
                co = l.vert.co
                if nx > ny and nx > nz:
                    u, v = co.y, co.z
                elif ny > nx and ny > nz:
                    u, v = co.x, co.z
                else:
                    u, v = co.x, co.y
                l[uv_layer].uv = (u * scale, v * scale)
    elif "TUBE" in mode:
        for f in faces:
            for l in f.loops:
                co = l.vert.co
                if mode == "TUBE_X":
                    u, v = ((math.atan2(co.z, co.y) / 6.28) + 0.5, co.x * scale)
                elif mode == "TUBE_Y":
                    u, v = ((math.atan2(co.x, co.z) / 6.28) + 0.5, co.y * scale)
                else:
                    u, v = ((math.atan2(co.y, co.x) / 6.28) + 0.5, co.z * scale)
                l[uv_layer].uv = (u, v)
    elif "FIT" in mode:
        loops = [l for f in faces for l in f.loops]
        if loops:
            xs, ys = [l.vert.co.x for l in loops], [l.vert.co.y for l in loops]
            w, h = max(0.001, max(xs) - min(xs)), max(0.001, max(ys) - min(ys))
            min_x, min_y = min(xs), min(ys)
            for l in loops:
                l[uv_layer].uv = ((l.vert.co.x - min_x) / w, (l.vert.co.y - min_y) / h)


def _calc_uv_ratio(faces, uv_layer):
    t3d, tuv = 0.0, 0.0
    for f in faces:
        a = f.calc_area()
        if a < 0.0001:
            continue
        uvs = [l[uv_layer].uv for l in f.loops]
        auv = 0.0
        if len(uvs) > 2:
            for i in range(len(uvs)):
                j = (i + 1) % len(uvs)
                auv += (uvs[i].x * uvs[j].y) - (uvs[j].x * uvs[i].y)
            auv = abs(auv) * 0.5
        t3d += a
        tuv += auv
    return math.sqrt(tuv / t3d) if t3d > 0.0001 else 0.0


def auto_detect_edge_slots(bm):
    """
    Populates MASSA_EDGE_SLOTS based on Material Boundaries.
    Slot ID = max(mat_index_A, mat_index_B)
    """
    print("MASSA DEBUG: auto_detect_edge_slots START")
    try:
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
    except:
        print("MASSA DEBUG: Failed to get/create MASSA_EDGE_SLOTS")
        return

    bm.edges.ensure_lookup_table()

    total_edges = 0
    total_boundaries = 0

    for e in bm.edges:
        total_edges += 1
        
        # [ARCHITECT CRITICAL] PRESERVATION OF INTENT
        # If the cartridge already assigned a slot (non-zero), DO NOT TOUCH IT.
        if e[edge_slots] != 0:
            continue

        # 1. PERIMETER DETECTION (Slot 1)
        # An edge is a perimeter if it has only 1 face (is_boundary)
        if e.is_boundary:
            e[edge_slots] = 1
            continue

        # 2. CONTOUR DETECTION (Slot 2)
        # An edge is a contour if it is sharp (angle based or manually sharp)
        # BUT we must respect seams. If it's a seam, it might be a Guide (3) or something else.
        # If it's just a sharp corner, it's a Contour.
        if not e.smooth and not e.seam:
             # Calculate angle to confirm it's actually sharp geometry
             # (Sometimes smooth=False is set but faces are coplanar)
             if len(e.link_faces) == 2:
                 ang = e.calc_face_angle_signed()
                 # If angle is significant (> 1 degree), treat as contour
                 if abs(ang) > 0.01:
                     e[edge_slots] = 2
                     # Note: We don't 'continue' here because it might ALSO be a material boundary

        # 3. MATERIAL BOUNDARY DETECTION (Slot 1-4)
        # Need at least 2 faces to be a boundary between regions
        if len(e.link_faces) < 2:
            continue
            
        boundary_found = False
        max_slot = 0
        
        # Check all unique material pairs
        checked_mats = set()
        for f in e.link_faces:
            checked_mats.add(f.material_index)
            
        if len(checked_mats) > 1:
            # Different materials found!
            # Slot ID = Max Material Index
            max_slot = max(checked_mats)
            boundary_found = True

        if boundary_found:
            total_boundaries += 1
            # Clamp to 4 (UI only supports 4 slots)
            if max_slot > 4:
                max_slot = 4
            elif max_slot < 0:
                max_slot = 0

            # [ARCHITECT LOGIC] Priority Resolution
            # If we detected a Material Boundary (max_slot > 0), overwrite any Contour (2).
            # If max_slot is 0 (no boundary), we KEEP the existing value (e.g. 2 from Contour).
            if max_slot > 0:
                e[edge_slots] = max_slot
            # print(f"MASSA DEBUG: Edge {e.index} -> Slot {max_slot} (Mats: {checked_mats})")

    print(f"MASSA DEBUG: auto_detect_edge_slots -> Edges: {total_edges}, Boundaries Found: {total_boundaries}")


def tag_structure_edges(bm, op):
    """
    Writes edge data to 'Massa_Viz_ID' (Edge Int Layer) for GN Visualization.
    [ARCHITECT FIX] Maps Seams to ID 5.
    """
    bm.edges.ensure_lookup_table()
    cvx, cnv = [], []
    viz_mode = getattr(op, "viz_edge_mode", "NATIVE")

    try:
        viz_layer = bm.edges.layers.int.get("Massa_Viz_ID")
        if not viz_layer:
            viz_layer = bm.edges.layers.int.new("Massa_Viz_ID")
    except:
        viz_layer = bm.edges.layers.int.new("Massa_Viz_ID")

    try:
        edge_slots_layer = bm.edges.layers.int["MASSA_EDGE_SLOTS"]
    except KeyError:
        edge_slots_layer = None

    for e in bm.edges:
        e[viz_layer] = 0

    total_viz_assignments = 0
    viz_counts = {}

    for e in bm.edges:
        is_concave_geo = False
        if not e.is_manifold:
            pass
        elif len(e.link_faces) == 2:
            c1 = e.link_faces[0].calc_center_median()
            c2 = e.link_faces[1].calc_center_median()
            n1 = e.link_faces[0].normal
            if (c2 - c1).dot(n1) < -0.001:
                is_concave_geo = True

        if is_concave_geo:
            cnv.append(e)
        else:
            cvx.append(e)

        if viz_mode == "SLOTS":
            # 1. Read Slot
            if edge_slots_layer:
                slot_id = e[edge_slots_layer]
                if 1 <= slot_id <= 4:
                    e[viz_layer] = slot_id
            
            # 2. Check Seam (Override)
            # This ensures we see seams even if they aren't standard slots
            # 2. Check Seam (Backend Override)
            # [ARCHITECT FIX] Only visualize Seams as geometry if explicitly debugging Seams
            # This prevents "Ghost Edges" from appearing in standard Slot/Wireframe views
            debug_view = getattr(op, "debug_view", "NONE")
            if e.seam and e[viz_layer] == 0:
                if debug_view == "SEAM":
                    e[viz_layer] = 5

    
    # [ARCHITECT DEBUG]
    viz_counts = {}
    for e in bm.edges:
        val = e[viz_layer]
        if val > 0:
            viz_counts[val] = viz_counts.get(val, 0) + 1
    print(f"MASSA DEBUG: tag_structure_edges -> Counts: {viz_counts}")

    return cvx, cnv


def generate_surface_maps(bm, op, convex, concave):
    """
    Calculates Wear, Thickness, etc. and writes to "Massa_Surface".
    """
    debug_view = getattr(op, "debug_view", "NONE")

    thick_enabled = getattr(op, "thick_active", True)
    if debug_view == "THICK":
        thick_enabled = True

    thick_mode = getattr(op, "data_green_mode", "THICKNESS") == "THICKNESS"
    thick_on = thick_mode and thick_enabled
    flow_on = getattr(op, "data_green_mode", "THICKNESS") == "FLOW"

    if debug_view == "THICK" and not thick_mode:
        flow_on = True

    grav_on = getattr(op, "grav_active", False)
    if debug_view == "GRAV":
        grav_on = True

    cavity_on = getattr(op, "cavity_active", False)
    if debug_view == "CAVITY":
        cavity_on = True

    bvh = BVHTree.FromBMesh(bm) if (thick_on or grav_on or cavity_on) else None

    mw, mt, mg, mc = {}, {}, {}, {}
    gs = getattr(op, "global_scale", 1.0)

    wear_active = getattr(op, "wear_active", False)
    if debug_view == "WEAR":
        wear_active = True

    if wear_active:
        scl = getattr(op, "wear_scale", 1.0)
        er = (0.05 / max(0.1, scl)) * gs
        me = _calc_prox(bm, convex, er)
        rough = getattr(op, "wear_rough", 0.5)
        amt = getattr(op, "wear_amount", 0.5)
        for v in bm.verts:
            b = me.get(v, 0.0)
            if b > 0.01:
                mw[v] = min(
                    1.0,
                    b * (1.0 - (rough * noise.noise(v.co * scl * 5) * 0.8)) * amt * 2,
                )

    if thick_on and bvh:
        mt = _calculate_mesh_thickness(
            bm,
            bvh,
            getattr(op, "thick_dist", 0.2) * gs,
            getattr(op, "thick_amount", 1.0),
            getattr(op, "thick_contrast", 1.0),
        )
    elif flow_on:
        mt = _calculate_hydraulic_flow(
            bm,
            iterations=getattr(op, "flow_steps", 1),
            rain=getattr(op, "flow_rain", 0.5),
            streak=getattr(op, "flow_streak", 0.9),
        )

    if grav_on and bvh:
        mg = _calculate_gravity_flow(
            bm, bvh, 8, 5.0 * gs, getattr(op, "grav_amount", 0.5)
        )

    if cavity_on and bvh:
        mc = _calculate_cavity_ao(
            bm,
            bvh,
            getattr(op, "cavity_dist", 0.1) * gs,
            getattr(op, "cavity_samples", 16),
            getattr(op, "cavity_contrast", 1.0),
        )

    try:
        cl = bm.loops.layers.float_color.get("Massa_Surface")
        if not cl:
            cl = bm.loops.layers.float_color.new("Massa_Surface")
    except:
        cl = bm.loops.layers.color.get("Massa_Surface") or bm.loops.layers.color.new(
            "Massa_Surface"
        )

    for f in bm.faces:
        for l in f.loops:
            v = l.vert
            l[cl] = (mw.get(v, 0.0), mt.get(v, 0.0), mg.get(v, 0.0), mc.get(v, 0.0))


def _calc_prox(bm, edges, radius, resolution=0.05):
    data = {}
    if not edges:
        return data
    pts = []
    for e in edges:
        v1, v2 = e.verts[0].co, e.verts[1].co
        pts.extend([v1, v2])
        l = e.calc_length()
        if l > resolution:
            for i in range(1, int(l / resolution)):
                pts.append(v1.lerp(v2, i / int(l / resolution)))
    kt = kdtree.KDTree(len(pts))
    for i, p in enumerate(pts):
        kt.insert(p, i)
    kt.balance()
    for v in bm.verts:
        _, _, d = kt.find(v.co)
        if d < radius:
            data[v] = (1.0 - (d / radius)) ** 2
    return data


def _calculate_mesh_thickness(bm, bvh, max_dist, amount, contrast):
    data, eps = {}, 0.002
    for v in bm.verts:
        start = v.co + (-v.normal * eps)
        loc, _, _, _ = bvh.ray_cast(start, -v.normal, max_dist)
        val = max(0.0, 1.0 - ((loc - start).length / max_dist)) if loc else 0.0
        data[v] = min(1.0, pow(val, max(0.1, contrast)) * amount)
    return data


def _calculate_gravity_flow(bm, bvh, samples, dist, amount):
    rng, data, eps = random.Random(77), {}, 0.01
    dirs = [Vector((0, 0, 1))]
    for _ in range(samples - 1):
        dirs.append(
            Vector((rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 1.0)).normalized()
        )
    for v in bm.verts:
        dz = v.normal.dot(Vector((0, 0, 1)))
        if dz < -0.4:
            data[v] = 0.0
            continue
        hits, start = 0, v.co + (v.normal * eps)
        for d in dirs:
            if bvh.ray_cast(start, d, dist)[0]:
                hits += 1
        val = (1.0 - (hits / len(dirs))) * ((1.0 - abs(dz)) + 0.2)
        data[v] = min(1.0, val * (0.6 + 0.4 * noise.noise(v.co * 2)) * amount)
    return data


def _calculate_cavity_ao(bm, bvh, max_dist, samples, contrast):
    rng, data, eps = random.Random(42), {}, 0.002
    base_dirs = []
    for _ in range(samples):
        v = Vector(
            (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))
        ).normalized()
        base_dirs.append(v)
    for v in bm.verts:
        start = v.co + (v.normal * eps)
        hits = 0
        for d in base_dirs:
            ray_dir = d
            if ray_dir.dot(v.normal) < 0:
                ray_dir = -ray_dir
            if bvh.ray_cast(start, ray_dir, max_dist)[0]:
                hits += 1
        occ = hits / samples
        if contrast != 1.0:
            occ = pow(occ, max(0.1, 1.0 / contrast))
        data[v] = min(1.0, occ)
    return data


def _calculate_hydraulic_flow(bm, iterations, rain, streak):
    water = {}
    up = Vector((0, 0, 1))
    for v in bm.verts:
        upness = max(0.0, v.normal.dot(up))
        water[v] = upness * rain
    sorted_verts = sorted(bm.verts, key=lambda v: v.co.z, reverse=True)
    for _ in range(iterations):
        for v in sorted_verts:
            current_water = water[v]
            if current_water < 0.01:
                continue
            lower_neighbors = []
            total_drop = 0.0
            for e in v.link_edges:
                other = e.other_vert(v)
                if other.co.z < v.co.z:
                    drop = v.co.z - other.co.z
                    lower_neighbors.append((other, drop))
                    total_drop += drop
            if lower_neighbors and total_drop > 0:
                moving_water = current_water * 0.9
                for neighbor, drop in lower_neighbors:
                    ratio = drop / total_drop
                    water[neighbor] += moving_water * ratio
                water[v] = current_water * (1.0 - streak)
            else:
                water[v] = min(2.0, current_water)
    result = {}
    for v, val in water.items():
        result[v] = min(1.0, val)
    return result