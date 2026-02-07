import bpy
import bmesh
from mathutils import Vector
import math

# ==================================================================================================
# UTILS
# ==================================================================================================


def _get_orientation_vector(mode):
    """Maps Enum to Vector."""
    if mode == "BACK":
        return Vector((0, -1, 0))
    if mode == "FRONT":
        return Vector((0, 1, 0))
    if mode == "LEFT":
        return Vector((-1, 0, 0))
    if mode == "RIGHT":
        return Vector((1, 0, 0))
    if mode == "BOTTOM":
        return Vector((0, 0, -1))
    return Vector((0, -1, 0))


def _get_islands(edges):
    visited = set()
    islands = []
    for e in edges:
        if e in visited:
            continue
        stack = [e]
        island = []
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            island.append(cur)
            for v in cur.verts:
                for next_e in v.link_edges:
                    if next_e in edges and next_e not in visited:
                        stack.append(next_e)
        if island:
            islands.append(island)
    return islands


# ==================================================================================================
# LAYER 1: DRIVERS (The Mandates)
# ==================================================================================================


def apply_base_drivers(
    bm,
    use_angle=True,
    angle_limit=60.0,
    use_slots=True,
    bias="BALANCED",
    # [ARCHITECT NEW]
    use_edges=False,
    edge_mask=(True, True, False, False, False),  # (Peri, Cont, Guide, Detail, Fold)
):
    """
    LAYER 1: The 'Obvious' Seams.
    Refactored to calculate geometry (Concavity) BEFORE making decisions.
    This ensures Bias affects Slot boundaries and Angles equally if needed.
    NOW INCLUDES: Edge Role processing with Protection Marking.
    """
    bm.edges.ensure_lookup_table()
    limit_rad = math.radians(angle_limit)
    epsilon = 0.0001

    # [ARCHITECT NEW] Retrieve Data Layers
    edge_slots_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
    force_seam_layer = bm.edges.layers.int.get("massa_force_seam")
    if not force_seam_layer:
        force_seam_layer = bm.edges.layers.int.new("massa_force_seam")

    for e in bm.edges:
        is_seam = False
        should_protect = False  # If True, protects from Enforcer

        is_concave = False
        is_slot_boundary = False

        # 1. GEOMETRY ANALYSIS (The Truth)
        # Calculate this for ALL manifold edges first to establish facts
        if e.is_manifold and len(e.link_faces) == 2:
            n1 = e.link_faces[0].normal
            c1 = e.link_faces[0].calc_center_median()
            c2 = e.link_faces[1].calc_center_median()

            # If vector between centers opposes normal -> Concave
            if (c2 - c1).dot(n1) < -0.001:
                is_concave = True

            # Check Slots
            if e.link_faces[0].material_index != e.link_faces[1].material_index:
                is_slot_boundary = True
        elif not e.is_manifold:
            is_slot_boundary = True  # Boundary edges are implicit slot breaks

        # 2. EDGE ROLE DRIVER (The New Logic)
        if use_edges and edge_slots_layer:
            slot_id = e[edge_slots_layer]
            # Slot IDs are 1-based (1,2,3,4,5)
            # Mask tuple is 0-based (0,1,2,3,4)
            if 1 <= slot_id <= 5:
                if edge_mask[slot_id - 1]:
                    is_seam = True
                    # CRITICAL: Edge Roles are manual decisions.
                    # We MUST protect them from the "Flat Seam Cleaner" (Enforcer).
                    should_protect = True

        # 3. SLOT DRIVER (Mandatory)
        if use_slots and is_slot_boundary:
            is_seam = True
            # We treat slot boundaries as critical structure.
            should_protect = True

        # 4. ANGLE DRIVER (Conditional)
        # Only check angle if we haven't already marked it (optimization)
        if use_angle and not is_seam:
            try:
                ang = e.calc_face_angle()
                if ang > (limit_rad - epsilon):
                    # Bias Logic
                    if bias == "BALANCED":
                        is_seam = True
                    elif bias == "CONVEX" and not is_concave:
                        is_seam = True
                    elif bias == "CONCAVE" and is_concave:
                        is_seam = True
            except ValueError:
                pass

        # 5. APPLY
        if is_seam:
            e.seam = True
            if should_protect:
                e[force_seam_layer] = 1


# ==================================================================================================
# LAYER 3: THE ENFORCER (Cleanup)
# ==================================================================================================


def cleanup_flat_seams(bm, threshold=5.0, keep_slots=True):
    """
    LAYER 3: The Enforcer.
    Removes seams on edges that are effectively flat (coplanar).
    Respects Slot boundaries AND Manual Edge Protection (massa_force_seam).
    """
    bm.edges.ensure_lookup_table()
    thresh_rad = math.radians(threshold)

    # [ARCHITECT NEW] Check for force layer (THE IMMUTABLE SEAL)
    force_layer = bm.edges.layers.int.get("massa_force_seam")

    for e in bm.edges:
        if not e.seam or not e.is_manifold:
            continue

        # 1. Protection: Manual Edge Slot override
        if force_layer and e[force_layer] == 1:
            continue

        # 2. Protect Slot Boundaries (Double check)
        if keep_slots and len(e.link_faces) == 2:
            if e.link_faces[0].material_index != e.link_faces[1].material_index:
                continue

        try:
            if e.calc_face_angle() < thresh_rad:
                e.seam = False
        except ValueError:
            pass


# ==================================================================================================
# LAYER 2: SOLVERS (The Intelligence)
# ==================================================================================================


def apply_seams_hard_surface(bm, tolerance_deg=15.0, strict_slots=True):
    """
    Planar Graph Clustering.
    Strict Slots: Prevents clusters from merging across material lines.
    """
    threshold = math.cos(math.radians(tolerance_deg))
    face_chart_map = {}
    visited = set()
    chart_id_counter = 0

    bm.faces.ensure_lookup_table()
    # Seed from largest faces to stabilize islands
    sorted_faces = sorted(bm.faces, key=lambda f: f.calc_area(), reverse=True)

    for seed in sorted_faces:
        if seed in visited:
            continue

        current_chart_id = chart_id_counter
        chart_id_counter += 1
        chart_normal = seed.normal.copy()
        seed_mat = seed.material_index

        stack = [seed]
        visited.add(seed)
        face_chart_map[seed] = current_chart_id

        while stack:
            f = stack.pop()
            for edge in f.edges:
                other = None
                for lf in edge.link_faces:
                    if lf != f:
                        other = lf
                        break

                if other and other not in visited:
                    # [COORD] Strict Slot Check
                    if strict_slots and other.material_index != seed_mat:
                        continue

                    if other.normal.dot(chart_normal) >= threshold:
                        visited.add(other)
                        face_chart_map[other] = current_chart_id
                        stack.append(other)

    bm.edges.ensure_lookup_table()
    for edge in bm.edges:
        if not edge.is_manifold:
            edge.seam = True
            continue
        if len(edge.link_faces) < 2:
            continue

        id_a = face_chart_map.get(edge.link_faces[0])
        id_b = face_chart_map.get(edge.link_faces[1])

        # If IDs differ, it's a chart boundary -> Seam
        if id_a is not None and id_b is not None:
            if id_a != id_b:
                edge.seam = True


def apply_seams_organic(
    bm, hide_vector_enum="BACK", straightness=2.0, strict_slots=True
):
    """
    Cylinder Detective / Tree Cut.
    Strict Slots: Prevents the 'zipper' from crossing materials.
    """
    hide_vector = _get_orientation_vector(hide_vector_enum)
    edge_costs = {}

    # 1. Cost Analysis
    for edge in bm.edges:
        if not edge.is_manifold:
            edge_costs[edge] = 9999.0
            continue
        if len(edge.link_faces) < 2:
            continue

        n1 = edge.link_faces[0].normal
        n2 = edge.link_faces[1].normal
        edge_normal = (n1 + n2).normalized()

        vis_align = edge_normal.dot(hide_vector)
        vis_cost = 1.0 - vis_align
        angle = edge.calc_face_angle_signed()
        concavity_cost = -2.0 if angle < -0.01 else 0.0

        final_cost = 5.0 + (vis_cost * 5.0) + concavity_cost
        edge_costs[edge] = max(0.1, final_cost)

    # Use existing seams as boundaries for the pathfinder
    boundaries = [e for e in bm.edges if not e.is_manifold or e.seam]

    if not boundaries:
        # Fallback for closed shapes (sphere): Pick a random start if no seams exist
        return

    # 2. Path Finding
    start_candidates = [e for e in boundaries]
    visited_edges = set()

    for start_edge in start_candidates:
        if start_edge in visited_edges:
            continue

        path = []
        # Determine starting material to enforce strictness
        start_mat = -1
        if start_edge.link_faces:
            start_mat = start_edge.link_faces[0].material_index

        current_vert = start_edge.verts[0]

        # Traverse
        while True:
            candidates = []
            for e in current_vert.link_edges:
                if e in visited_edges or e in path:
                    continue

                # [COORD] Strict Slot Check
                if strict_slots and e.link_faces:
                    # If edge lies between two DIFFERENT materials, it's a boundary, not a path.
                    if len(e.link_faces) == 2:
                        if (
                            e.link_faces[0].material_index
                            != e.link_faces[1].material_index
                        ):
                            continue  # Don't walk along the border
                        if e.link_faces[0].material_index != start_mat:
                            continue  # Don't walk into another material

                cost = edge_costs.get(e, 100.0)

                # Straightness Bias
                if path:
                    prev_e = path[-1]
                    v_prev = (prev_e.verts[1].co - prev_e.verts[0].co).normalized()
                    v_curr = (e.verts[1].co - e.verts[0].co).normalized()
                    dot_turn = abs(v_prev.dot(v_curr))
                    turn_penalty = (1.0 - dot_turn) * 10.0 * straightness
                    cost += turn_penalty

                is_boundary = not e.is_manifold or e.seam
                candidates.append((e, cost, is_boundary))

            if not candidates:
                break

            best_edge = min(candidates, key=lambda x: x[1])
            edge, cost, is_boundary = best_edge

            path.append(edge)
            visited_edges.add(edge)
            current_vert = edge.other_vert(current_vert)

            if is_boundary:
                break
            if len(path) > 500:  # Safety break
                break

        for edge in path:
            edge.seam = True

        # Ensure boundaries remain seams (reinforce Layer 1)
        for e in boundaries:
            e.seam = True


def apply_seams_strip_follow(bm):
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    rungs = set()
    rails = set()

    for f in bm.faces:
        if len(f.verts) != 4:
            continue
        loops = list(f.loops)
        edge_pairs = [(loops[0].edge, loops[2].edge), (loops[1].edge, loops[3].edge)]
        len_a = _measure_strip_len(f, edge_pairs[0])
        len_b = _measure_strip_len(f, edge_pairs[1])

        winning_pair = edge_pairs[0] if len_a > len_b else edge_pairs[1]
        losing_pair = edge_pairs[1] if len_a > len_b else edge_pairs[0]

        rungs.add(winning_pair[0])
        rungs.add(winning_pair[1])
        rails.add(losing_pair[0])
        rails.add(losing_pair[1])

    for e in rails:
        e.seam = True
    for e in rungs:
        e.seam = False


def _measure_strip_len(start_face, start_edge_pair):
    length = 1
    for edge in start_edge_pair:
        curr_e = edge
        curr_f = start_face
        for _ in range(50):
            if len(curr_e.link_faces) != 2:
                break
            next_f = None
            for lf in curr_e.link_faces:
                if lf != curr_f:
                    next_f = lf
                    break
            if not next_f:
                break
            if len(next_f.verts) != 4:
                break
            found_next = False
            for e_next in next_f.edges:
                if e_next == curr_e:
                    continue
                if not (
                    e_next.verts[0] in curr_e.verts or e_next.verts[1] in curr_e.verts
                ):
                    curr_e = e_next
                    curr_f = next_f
                    length += 1
                    found_next = True
                    break
            if not found_next:
                break
    return length


def apply_seams_smart_tube(bm, hide_vector_enum="BACK", strict_slots=True):
    """
    1-Cut Unroll (Zipper).
    """
    orient_enum = hide_vector_enum
    hide_vector = _get_orientation_vector(orient_enum)

    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    walls = []
    caps = []
    up_vec = Vector((0, 0, 1))

    for f in bm.faces:
        if abs(f.normal.dot(up_vec)) > 0.8:
            caps.append(f)
        else:
            walls.append(f)

    wall_set = set(walls)
    vertical_edges = []

    for e in bm.edges:
        if not e.is_manifold:
            continue

        # [COORD] Strict Slot Check
        if strict_slots and len(e.link_faces) == 2:
            if e.link_faces[0].material_index != e.link_faces[1].material_index:
                # This is a material boundary, treat it as a hard cut, not a vertical candidate
                continue

        f1, f2 = e.link_faces[0], e.link_faces[1]
        is_f1_wall = f1 in wall_set
        is_f2_wall = f2 in wall_set

        if is_f1_wall and is_f2_wall:
            vertical_edges.append(e)
            e.seam = (
                False  # Reset potential vertical seams in favor of the zipper logic
            )
        elif is_f1_wall != is_f2_wall:
            e.seam = True  # Cap boundary -> Seam

    if not vertical_edges:
        return

    islands = _get_islands(vertical_edges)

    for island_edges in islands:
        scored_edges = []
        for e in island_edges:
            score = 0.0
            cent = (e.verts[0].co + e.verts[1].co) / 2
            norm_cent = cent.normalized()

            pos_score = norm_cent.dot(hide_vector)
            score += pos_score * 10.0

            angle = e.calc_face_angle_signed()
            n1 = e.link_faces[0].normal
            c1 = e.link_faces[0].calc_center_median()
            c2 = e.link_faces[1].calc_center_median()
            dir_12 = (c2 - c1).normalized()

            if dir_12.dot(n1) < -0.01:
                score += 20.0  # Prefer concave (hidden) corners
            elif abs(angle) < 0.01:
                score += 5.0  # Prefer flat
            else:
                score -= 10.0  # Avoid sharp convex

            scored_edges.append((e, score))

        scored_edges.sort(key=lambda x: x[1], reverse=True)

        if scored_edges:
            best_start = scored_edges[0][0]
            stack = [best_start]
            visited = set()
            while stack:
                e = stack.pop()
                if e in visited:
                    continue
                visited.add(e)
                e.seam = True

                # Flood fill to find the vertical strip
                for v in e.verts:
                    for next_e in v.link_edges:
                        if next_e in island_edges and next_e not in visited:
                            stack.append(next_e)


# ==================================================================================================
# DISPATCHER
# ==================================================================================================


def solve_seams(bm, mode="AUTO", **kwargs):
    strict = kwargs.get("strict_slots", True)

    if mode == "HARD_SURFACE":
        tol = kwargs.get("cluster_tol", 5.0)
        apply_seams_hard_surface(bm, tolerance_deg=tol, strict_slots=strict)

    elif mode == "ORGANIC":
        orient = kwargs.get("orient", "BACK")
        straight = kwargs.get("straightness", 1.0)
        apply_seams_organic(
            bm, hide_vector_enum=orient, straightness=straight, strict_slots=strict
        )

    elif mode == "STRIP":
        apply_seams_strip_follow(bm)

    elif mode == "SMART_TUBE":
        orient = kwargs.get("orient", "BACK")
        apply_seams_smart_tube(bm, hide_vector_enum=orient, strict_slots=strict)

    elif mode == "BOX_STRIP":
        orient = kwargs.get("orient", "BACK")
        apply_seams_smart_tube(bm, hide_vector_enum=orient, strict_slots=strict)

    elif mode == "AUTO":
        tol = kwargs.get("cluster_tol", 5.0)
        apply_seams_hard_surface(bm, tolerance_deg=tol, strict_slots=strict)
