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


def assign_materials(obj, op, bm=None):
    """
    Assigns final or debug materials.
    [ARCHITECT FIX]: Now implements Smart Slotting.
    Only generates material slots that are actually used by the geometry.
    Returns a mapping: {old_slot_index: new_slot_index}
    """
    debug_v = getattr(op, "debug_view", "NONE")
    viz_mode = getattr(op, "viz_edge_mode", "NATIVE")
    override_mat = None

    # 1. Determine Global Override (Standard Debugs)
    if debug_v != "NONE":
        if debug_v == "UV":
            override_mat = mat_utils.create_debug_uv_material()
        elif debug_v == "DATA_SET_1":
            override_mat = mat_utils.create_debug_set1_material()
        elif debug_v == "DATA_SET_2":
            override_mat = mat_utils.create_debug_set2_material()
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

    # 2. Determine Used Slots
    slot_map = {} # old_idx -> new_idx
    slots_to_create = [] # List of old indices to create

    if bm:
        bm.faces.ensure_lookup_table()
        used_indices = set()
        for f in bm.faces:
            used_indices.add(f.material_index)

        # Sort so that Slot 0 comes before Slot 5 (Predictable order)
        sorted_used = sorted(list(used_indices))

        for new_idx, old_idx in enumerate(sorted_used):
            slot_map[old_idx] = new_idx
            slots_to_create.append(old_idx)

        # Remap Faces
        for f in bm.faces:
            if f.material_index in slot_map:
                f.material_index = slot_map[f.material_index]
            else:
                # Should not happen if we scanned correctly
                f.material_index = 0
    else:
        # Fallback: Create all 10 slots (Old Behavior)
        slots_to_create = list(range(10))
        for i in range(10):
            slot_map[i] = i

    # 3. Apply to Object
    # We clear any existing, then forcefully pad to 10
    obj.data.materials.clear()
    
    # Ensure all debug mats exist
    mat_utils.ensure_default_library()

    for old_i in slots_to_create:
        if override_mat:
            # Debug Mode: All slots use the debug shader, preserving index logic
            obj.data.materials.append(override_mat)
        else:
            # Final Mode: Load actual slot material or fallback to Debug Color
            mat_name = getattr(op, f"mat_{old_i}", "NONE")
            mat = mat_utils.load_material_smart(mat_name)
            
            if not mat:
                # If NONE or invalid, use the visual debug slot color (e.g. Red for 1)
                debug_name = mat_utils.get_debug_mat_name(old_i)
                mat = mat_utils.load_material_smart(debug_name)
            
            if mat:
                obj.data.materials.append(mat)
            else:
                # Last resort fallback to prevent index crash
                placeholder = mat_utils.get_or_create_placeholder_material()
                obj.data.materials.append(placeholder)

    return slot_map


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
    Populates MASSA_EDGE_SLOTS using Intelligent Geometry Analysis.

    Strategy:
    1. Identify 'End Caps' vs 'Walls' based on dominant axis alignment.
    2. Mark edges between Caps and Walls as Slot 1 (Perimeter).
    3. Find a continuous path connecting End Caps along the Wall as Slot 3 (Guide).
    4. Mark remaining sharp edges as Slot 2 (Contour).
    5. Handle Material Boundaries as Slot 1-4 based on Max Material Index.

    Respects existing manual assignments (non-zero).
    """
    try:
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
    except:
        return

    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Ensure Normals are valid before classification
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    # [STEP 0] Geometry Analysis
    # Determine Dominant Axis
    min_v = Vector((float('inf'), float('inf'), float('inf')))
    max_v = Vector((float('-inf'), float('-inf'), float('-inf')))

    for v in bm.verts:
        min_v.x = min(min_v.x, v.co.x)
        min_v.y = min(min_v.y, v.co.y)
        min_v.z = min(min_v.z, v.co.z)
        max_v.x = max(max_v.x, v.co.x)
        max_v.y = max(max_v.y, v.co.y)
        max_v.z = max(max_v.z, v.co.z)
        
    dim = max_v - min_v
    dom_axis = 2 # Z default

    # [ARCHITECT REFINED] Default to Z for cubes/equidistant objects.
    # Only switch if X or Y is STRICTLY greater than Z by a margin.
    # Otherwise, for architectural elements, Z (Up) is usually the "Cap" axis.

    if dim.x > dim.z * 1.1 and dim.x >= dim.y:
        dom_axis = 0 # X
    elif dim.y > dim.z * 1.1 and dim.y >= dim.x:
        dom_axis = 1 # Y

    dom_vec = Vector((0,0,0))
    dom_vec[dom_axis] = 1.0

    # Classify Faces: Cap vs Wall
    caps = set()
    walls = set()

    # [ARCHITECT DEBUG] If ALL faces are caps (e.g. flat plane), or ALL walls, we need fallback.
    # But usually procedural objects have volume.

    for f in bm.faces:
        # Dot product of normal with dominant axis
        alignment = abs(f.normal.dot(dom_vec))
        if alignment > 0.8: # Mostly aligned with axis -> Cap
            caps.add(f)
        else: # Mostly perpendicular -> Wall
            walls.add(f)

    # Fallback for Cylinder Cap Detection:
    # If a face is a polygon with > 4 verts at the extreme ends of the bounding box, it is likely a cap
    # even if normal is slightly off? No, normals are reliable.

    # [STEP 1] Edge Classification Loop
    for e in bm.edges:
        # [ARCHITECT CRITICAL] Preservation of Intent
        if e[edge_slots] != 0:
            continue

        # A. Open Mesh Boundary -> Slot 1 (Perimeter) always
        if e.is_boundary:
            e[edge_slots] = 1
            continue

        if len(e.link_faces) < 2:
            continue
            
        f1 = e.link_faces[0]
        f2 = e.link_faces[1]

        # B. Cap-Wall Interface -> Slot 1 (Perimeter Loop)
        # Using index lookup for reliability if sets fail? No, sets are object hashes.
        is_cap1 = f1 in caps
        is_cap2 = f2 in caps

        # Determine if we are on a Rim
        if is_cap1 != is_cap2:
            # One cap, one wall -> This is the rim
            e[edge_slots] = 1
            continue

        # [ARCHITECT DEBUG] Closed Cylinder Special Case
        # If both faces are walls, but the angle is sharp (e.g. box corner), it is Slot 2.
        # If both faces are caps (e.g. stacked planes), it is Slot 2?
        # What if we have a cylinder cap made of multiple faces (grid fill)?
        # Then the boundary between grid faces is flat (smooth).
        # But boundary between grid and side is Cap-Wall.

        # What if the Cap is a single N-gon?
        # The edge connecting Cap to Wall is Cap-Wall.
        # This logic holds.
        
        # Why did Closed Cylinder fail in test?
        # "Slots: {2: 12}" -> All edges became Slot 2.
        # This means NO edges were detected as Cap-Wall.
        # Means either NO faces were Caps, or ALL faces were Caps?
        # Cylinder Top/Bottom normals are (0,0,1). Dom axis is Z (2). Dot is 1.0. Caps.
        # Side faces normals are (1,0,0), etc. Dot is 0. Walls.
        # So caps set has Top/Bottom faces. Walls set has Side faces.
        # Edges between Top and Side connect f1(Cap) and f2(Wall).
        # So is_cap1 != is_cap2 should be True.

        # Unless... link_faces order? No.
        # Unless create_cone result normals are messed up?
        # bmesh.ops.recalc_face_normals(bm, faces=bm.faces) might be needed at start.

        # C. Material Boundaries -> Max ID (Override)
        if f1.material_index != f2.material_index:
            max_id = max(f1.material_index, f2.material_index)
            if max_id > 0:
                e[edge_slots] = min(max_id, 4) # Clamp to 4
                continue

        # D. Sharp Edges -> Slot 2 (Contour)
        # Check angle or smoothness
        if not e.smooth:
            ang = e.calc_face_angle_signed()
            if abs(ang) > 0.01:
                e[edge_slots] = 2

    # [STEP 2] Slot 3: The Guide Cut (Seam)
    # Re-evaluate walls if no guide found
    has_guide = False
    for e in bm.edges:
        if e[edge_slots] == 3:
            has_guide = True
            break
            
    if not has_guide and walls:
        # Find candidate start edge
        candidates = []
        for e in bm.edges:
            # Must be available (0) or Contour (2) - we can override contour for a seam
            if e[edge_slots] not in {0, 2}: continue

            # Check alignment
            v_vec = (e.verts[1].co - e.verts[0].co).normalized()
            align = abs(v_vec.dot(dom_vec))

            if align > 0.9: # Highly aligned
                # Check if it touches a Slot 1 edge
                score = 0
                for v in e.verts:
                    for le in v.link_edges:
                        if le[edge_slots] == 1:
                            score += 1

                # Boost if it connects two Slot 1 loops (score 2)
                candidates.append((e, score))

        candidates.sort(key=lambda x: x[1], reverse=True)

        if candidates:
            start_edge = candidates[0][0]
            start_edge[edge_slots] = 3 # Mark start immediately

            # Walk Only ONE Direction if score is 2 (connected at both ends)
            # But simplistic walker: just mark it.

            # If we just mark the start edge, for a simple cylinder, that IS the seam.
            # But for segmented cylinders, we need to walk.

            # Walker
            curr = start_edge

            # Determine Axis Vector for guidance
            guide_vec = (curr.verts[1].co - curr.verts[0].co).normalized()
            if guide_vec.dot(dom_vec) < 0:
                guide_vec = -guide_vec

            # Walk "Forward" (Up) and "Backward" (Down) relative to guide_vec
            for direction in [-1, 1]:
                # Pick a vertex based on direction approximation
                # v1 - v0 is edge vector.
                # if direction is 1, go to v1.
                v_start = curr.verts[1] if direction == 1 else curr.verts[0]

                walker = v_start
                last_edge = curr

                steps = 0
                while steps < 1000:
                    # Find best next edge connected to walker
                    best_next = None
                    best_align = 0.9 # High threshold

                    for ne in walker.link_edges:
                        if ne == last_edge: continue
                        if ne[edge_slots] == 1: # Hit Cap
                            best_next = None
                            break

                        # Check alignment
                        ne_vec = (ne.verts[1].co - ne.verts[0].co).normalized()
                        align = abs(ne_vec.dot(guide_vec))

                        if align > best_align:
                            best_align = align
                            best_next = ne

                    if best_next:
                        # Overwrite Slot 2 if needed
                        best_next[edge_slots] = 3
                        last_edge = best_next
                        walker = best_next.other_vert(walker)
                        steps += 1
                    else:
                        break

    # [STEP 2] Slot 3: The Guide Cut (Seam)
    # We need to find a path along the WALLS that connects two End Caps (or loops back).
    # Heuristic: Pick a Wall edge aligned with dominant axis and walk it.


def auto_detect_sharp_edges(bm, op):
    """
    Additive pass to detect sharp edges based on angle and convexity.
    Skipps edges with existing Slot Data.
    """

    use_cvx = getattr(op, "edge_sharp_convex_active", False)
    use_cnv = getattr(op, "edge_sharp_concave_active", False)

    if not (use_cvx or use_cnv):
        return

    ang_cvx = getattr(op, "edge_sharp_convex_angle", 0.52)
    ang_cnv = getattr(op, "edge_sharp_concave_angle", 0.52)

    try:
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
    except:
        edge_slots = None

    bm.edges.ensure_lookup_table()

    count = 0

    for e in bm.edges:
        # 1. Skip if already processed (Slot Data)
        if edge_slots and e[edge_slots] != 0:
            continue

        # 2. Skip if already sharp (Additive only)
        if not e.smooth:
            continue

        # 3. Geometry Check
        if not e.is_manifold or len(e.link_faces) != 2:
            continue

        # Calculate Angle (Unsigned)
        # 0 = Flat, PI = Folded back
        angle = e.calc_face_angle()

        # Optimization: Early exit if angle is tiny
        if angle < 0.001:
            continue

        # Determine Concavity
        is_concave = False
        f0 = e.link_faces[0]
        f1 = e.link_faces[1]

        # Use simple dot product of face center vector vs normal
        # Vector from F0 center to F1 center
        c0 = f0.calc_center_median()
        c1 = f1.calc_center_median()
        vec = c1 - c0

        # Convex (Ridge) = Neighbor center is below plane (Negative Dot)
        # Concave (Valley) = Neighbor center is above plane (Positive Dot)
        if vec.dot(f0.normal) > 0.0001:
            is_concave = True

        marked = False

        if is_concave:
            if use_cnv and angle >= ang_cnv:
                marked = True
        else: # Convex
            if use_cvx and angle >= ang_cvx:
                marked = True

        if marked:
            e.smooth = False
            count += 1

    # print(f"MASSA DEBUG: Auto-Detect Sharp -> Marked {count} edges.")


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
    # viz_counts = {}
    # for e in bm.edges:
    #     val = e[viz_layer]
    #     if val > 0:
    #         viz_counts[val] = viz_counts.get(val, 0) + 1
    # print(f"MASSA DEBUG: tag_structure_edges -> Counts: {viz_counts}")

    return cvx, cnv


def generate_surface_maps(bm, op, convex, concave):
    """
    Calculates Wear, Thickness, etc. and writes to "Data_Colors_1" and "Data_Colors_2".
    """
    debug_view = getattr(op, "debug_view", "NONE")

    # --- SET 1 LOGIC (RGBW) ---
    thick_enabled = getattr(op, "thick_active", True)
    thick_mode = getattr(op, "data_green_mode", "THICKNESS") == "THICKNESS"
    thick_on = thick_mode and thick_enabled
    flow_on = getattr(op, "data_green_mode", "THICKNESS") == "FLOW"

    if debug_view in {"DATA_SET_1", "DATA_SET_2"}:
        # Force calculate if debugging combined layers
        # Optimization: Only calculate active ones, but for now we trust the "active" flags
        pass

    grav_on = getattr(op, "grav_active", False)
    cavity_on = getattr(op, "cavity_active", False)

    # --- SET 2 LOGIC (O/B/P/B) ---
    wear2_on = getattr(op, "wear2_active", False)
    flow2_on = getattr(op, "flow2_active", False)
    cover_on = getattr(op, "cover_active", False)
    peak_on = getattr(op, "peak_active", False)

    need_bvh = (thick_on or grav_on or cavity_on or cover_on or peak_on)
    bvh = BVHTree.FromBMesh(bm) if need_bvh else None

    # Maps: 1 = R, G, B, A; 2 = R, G, B, A
    m1_r, m1_g, m1_b, m1_a = {}, {}, {}, {}
    m2_r, m2_g, m2_b, m2_a = {}, {}, {}, {}

    gs = getattr(op, "global_scale", 1.0)

    # --- SET 1 CALCULATION ---

    # 1. Wear (R)
    if getattr(op, "wear_active", False):
        scl = getattr(op, "wear_scale", 1.0)
        er = (0.05 / max(0.1, scl)) * gs
        me = _calc_prox(bm, convex, er)
        rough = getattr(op, "wear_rough", 0.5)
        amt = getattr(op, "wear_amount", 0.5)
        for v in bm.verts:
            b = me.get(v, 0.0)
            if b > 0.01:
                val = b * (1.0 - (rough * noise.noise(v.co * scl * 5) * 0.8)) * amt * 2
                m1_r[v] = min(1.0, val)

    # 2. Thick/Flow (G)
    if thick_on and bvh:
        m1_g = _calculate_mesh_thickness(
            bm,
            bvh,
            getattr(op, "thick_dist", 0.2) * gs,
            getattr(op, "thick_amount", 1.0),
            getattr(op, "thick_contrast", 1.0),
        )
    elif flow_on:
        m1_g = _calculate_hydraulic_flow(
            bm,
            iterations=getattr(op, "flow_steps", 1),
            rain=getattr(op, "flow_rain", 0.5),
            streak=getattr(op, "flow_streak", 0.9),
        )

    # 3. Gravity (B)
    if grav_on and bvh:
        m1_g_res = _calculate_gravity_flow(
            bm, bvh, 8, 5.0 * gs, getattr(op, "grav_amount", 0.5)
        )
        m1_b = m1_g_res # Rename to match slot B

    # 4. Cavity (A)
    if cavity_on and bvh:
        m1_a = _calculate_cavity_ao(
            bm,
            bvh,
            getattr(op, "cavity_dist", 0.1) * gs,
            getattr(op, "cavity_samples", 16),
            getattr(op, "cavity_contrast", 1.0),
        )

    # --- SET 2 CALCULATION ---

    # 1. Edge Wear (R)
    if wear2_on:
        # Re-use prox on convex but simplified logic
        er = 0.02 * gs
        me = _calc_prox(bm, convex, er)
        amt = getattr(op, "wear2_amount", 1.0)
        contr = getattr(op, "wear2_contrast", 2.0)
        for v in bm.verts:
            b = me.get(v, 0.0)
            if b > 0.001:
                m2_r[v] = min(1.0, pow(b, contr) * amt)

    # 2. Flow 2 (Wind) (G)
    if flow2_on:
        m2_g = _calculate_directional_flow(
            bm,
            iterations=4,
            rain=getattr(op, "flow2_rain", 0.8),
            wind=Vector(getattr(op, "flow2_wind_dir", (1,0,0))).normalized()
        )

    # 3. Cover (Snow) (B)
    if cover_on and bvh:
        m2_b = _calculate_covering(
            bm, bvh,
            getattr(op, "cover_amount", 1.0),
            getattr(op, "cover_contrast", 1.0)
        )

    # 4. Peaks (Inv Cavity) (A)
    if peak_on and bvh:
        m2_a = _calculate_peaks(
            bm, bvh,
            getattr(op, "peak_dist", 0.1) * gs,
            getattr(op, "peak_contrast", 1.0)
        )

    # --- WRITE LAYERS ---

    # Layer 1
    try:
        cl1 = bm.loops.layers.float_color.get("Data_Colors_1")
        if not cl1: cl1 = bm.loops.layers.float_color.new("Data_Colors_1")
    except:
        cl1 = bm.loops.layers.color.get("Data_Colors_1") or bm.loops.layers.color.new("Data_Colors_1")

    # Layer 2
    try:
        cl2 = bm.loops.layers.float_color.get("Data_Colors_2")
        if not cl2: cl2 = bm.loops.layers.float_color.new("Data_Colors_2")
    except:
        cl2 = bm.loops.layers.color.get("Data_Colors_2") or bm.loops.layers.color.new("Data_Colors_2")

    # Delete old "Massa_Surface" if it exists to avoid confusion
    old_l = bm.loops.layers.float_color.get("Massa_Surface")
    if old_l: bm.loops.layers.float_color.remove(old_l)

    for f in bm.faces:
        for l in f.loops:
            v = l.vert
            l[cl1] = (
                m1_r.get(v, 0.0),
                m1_g.get(v, 0.0),
                m1_b.get(v, 0.0),
                m1_a.get(v, 0.0)
            )
            l[cl2] = (
                m2_r.get(v, 0.0),
                m2_g.get(v, 0.0),
                m2_b.get(v, 0.0),
                m2_a.get(v, 0.0)
            )


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


def _calculate_directional_flow(bm, iterations, rain, wind):
    """
    Hydraulic flow but gravity is skewed by wind direction.
    """
    water = {}
    # Upness is alignment with wind (rain coming FROM wind direction)
    # Actually rain usually falls down (-Z) but wind pushes it.
    # Let's say effective "Gravity" is (0,0,-1) + Wind.
    # So "Down" is (0,0,-1) + WindDir * Strength?
    # No, let's keep it simple. User sets "Wind Dir".
    # We treat Wind Dir as the "Rain Source".

    source_dir = -wind

    for v in bm.verts:
        # Exposure to source
        exposure = max(0.0, v.normal.dot(source_dir))
        water[v] = exposure * rain

    # Sort by projection along wind
    sorted_verts = sorted(bm.verts, key=lambda v: v.co.dot(source_dir), reverse=True)

    # Flow direction is roughly Down (-Z) + Wind
    # But for hydraulic algo, we just need to know "Downhill".
    # Downhill is along the "Gravity" vector.
    # Let's assume standard gravity (-Z) for flow, but initial deposit is wind-based.

    for _ in range(iterations):
        for v in sorted_verts:
            current_water = water[v]
            if current_water < 0.01: continue

            lower_neighbors = []
            total_drop = 0.0
            for e in v.link_edges:
                other = e.other_vert(v)
                # Standard Gravity Flow logic
                if other.co.z < v.co.z:
                    drop = v.co.z - other.co.z
                    lower_neighbors.append((other, drop))
                    total_drop += drop

            if lower_neighbors and total_drop > 0:
                moving_water = current_water * 0.9
                for neighbor, drop in lower_neighbors:
                    ratio = drop / total_drop
                    water[neighbor] += moving_water * ratio
                water[v] = current_water * 0.1
            else:
                water[v] = min(2.0, current_water)

    result = {}
    for v, val in water.items():
        result[v] = min(1.0, val)
    return result


def _calculate_covering(bm, bvh, amount, contrast):
    """
    Simulates Snow/Dust (Up-facing + Occlusion).
    """
    data, eps = {}, 0.01
    up = Vector((0, 0, 1))

    for v in bm.verts:
        # 1. Normal alignment
        dot = v.normal.dot(up)
        if dot <= 0.0:
            data[v] = 0.0
            continue

        # 2. Occlusion check (Raycast UP)
        start = v.co + (v.normal * eps)
        # Check if something is above
        if bvh.ray_cast(start, up, 100.0)[0]:
            # Occluded (Under roof)
            data[v] = 0.0
        else:
            # Exposed
            val = dot # Base on flatness
            if contrast != 1.0:
                 val = pow(val, contrast)
            data[v] = min(1.0, val * amount)

    return data


def _calculate_peaks(bm, bvh, dist, contrast):
    """
    Inverse Cavity / Peaks.
    Rays cast OUTWARD. If they hit nothing, it's a peak.
    If they hit something immediately, it's a valley/crevice.
    """
    data, eps = {}, 0.002

    for v in bm.verts:
        start = v.co + (v.normal * eps)
        # Raycast in normal direction
        hit_loc, _, _, _ = bvh.ray_cast(start, v.normal, dist)

        if hit_loc:
            # Hit something: Enclosed/Concave
            # Measure distance
            d = (hit_loc - start).length
            val = d / dist # 0.0 (Close hit) to 1.0 (Far hit)
        else:
            # Hit nothing: Open/Convex
            val = 1.0

        if contrast != 1.0:
            val = pow(val, contrast)

        data[v] = min(1.0, val)

    return data


def bake_strain_map(bm, op):
    """
    [Phase 3 Protocol] Strain Maps (phys_bake_strain)
    Creates 'MASSA_YieldMap' Color Attribute for Chaos Destruction.
    Iterates vertices.
    - Slot 1 (Perimeter) -> (1.0, 1.0, 1.0, 1.0) * Strength
    - Slot 4 (Detail) -> (0.1, 0.1, 0.1, 1.0) * Strength
    """
    if not getattr(op, "phys_bake_strain", False):
        return

    # Create/Verify Layer (Float Color on Loops)
    # BMesh uses loops for color attributes (Corner Domain)
    try:
        # Try Float Color
        layer = bm.loops.layers.float_color.get("MASSA_YieldMap")
        if not layer:
            layer = bm.loops.layers.float_color.new("MASSA_YieldMap")
    except:
        # Fallback to Byte Color if needed (though Float is standard now)
        try:
            layer = bm.loops.layers.color.get("MASSA_YieldMap")
            if not layer:
                layer = bm.loops.layers.color.new("MASSA_YieldMap")
        except:
            print("MASSA ERROR: Could not create Strain Map layer.")
            return

    try:
        edge_slots_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
    except:
         edge_slots_layer = None

    if not edge_slots_layer:
        # If no slots, just return (or create empty map)
        return

    strength = getattr(op, "phys_yield_strength", 1.0)
    
    # Pre-calculate Vertex Constraints
    # We map Vert -> Max Constraint Value
    # 0.0 = Default
    # 0.1 * Strength = Detail (Slot 4)
    # 1.0 * Strength = Indestructible (Slot 1)
    
    vert_vals = {}
    
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    
    for v in bm.verts:
        max_val = 0.0
        for e in v.link_edges:
            slot_id = e[edge_slots_layer]
            
            val = 0.0
            if slot_id == 1: # Perimeter
                val = 1.0
            elif slot_id == 4: # Detail
                val = 0.1
            
            if val > max_val:
                max_val = val
                
        vert_vals[v] = max_val * strength
        
    # Apply to Loops
    for f in bm.faces:
        for l in f.loops:
            v = l.vert
            val = vert_vals.get(v, 0.0)
            # RGBA: (val, val, val, 1.0)
            l[layer] = (val, val, val, 1.0)


def bake_kinematic_anchors(obj, bm, op):
    """
    [Phase 3 Protocol] Kinematic Anchors (phys_kinematic_pin)
    Creates 'MASSA_Kinematic' Vertex Group.
    - Slot 1 Verts -> 1.0 (Anchor)
    - 1-Ring Neighbors -> 0.5 (Falloff)
    """
    if not getattr(op, "phys_kinematic_pin", False):
        return
        
    # 1. Create VG on Object
    vg = obj.vertex_groups.get("MASSA_Kinematic")
    if not vg:
        vg = obj.vertex_groups.new(name="MASSA_Kinematic")
    
    vg_index = vg.index
    
    # 2. Get Deform Layer on BMesh
    deform_layer = bm.verts.layers.deform.verify()
    
    try:
        edge_slots_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
    except:
        edge_slots_layer = None

    if not edge_slots_layer:
        return
        
    # 3. Identify Anchors
    anchors = set()
    supports = set()
    
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        is_anchor = False
        for e in v.link_edges:
            if e[edge_slots_layer] == 1:
                is_anchor = True
                break
        
        if is_anchor:
            anchors.add(v)
            
    # 4. Identify Supports (1-Ring from Anchors)
    for v in anchors:
        for e in v.link_edges:
            other = e.other_vert(v)
            if other not in anchors:
                supports.add(other)
                
    # 5. Apply Weights
    for v in anchors:
        dvert = v[deform_layer]
        dvert[vg_index] = 1.0
        
    for v in supports:
        dvert = v[deform_layer]
        # Only set if not already set (though logic above ensures disjoint)
        dvert[vg_index] = 0.5

