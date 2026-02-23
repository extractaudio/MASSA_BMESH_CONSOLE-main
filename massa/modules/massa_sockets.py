import bpy
import bmesh
from mathutils import Vector, Euler, Matrix


def calculate_transforms(bm, target_slots):
    """
    Scans the mesh for faces belonging to 'target_slots'.
    Groups them by island, finds the dominant face, and calculates a robust transform matrix.
    """
    sockets = {}
    if not target_slots:
        return sockets
    bm.faces.ensure_lookup_table()

    # 1. Group Faces by Connectivity (Islands)
    visited = set()
    islands = []
    relevant = [f for f in bm.faces if f.material_index in target_slots]

    for f in relevant:
        if f in visited:
            continue
        stack = [f]
        current_island = []
        visited.add(f)
        while stack:
            curr = stack.pop()
            current_island.append(curr)
            for e in curr.edges:
                for lf in e.link_faces:
                    if lf.material_index == curr.material_index and lf not in visited:
                        visited.add(lf)
                        stack.append(lf)
        if current_island:
            islands.append(current_island)

    # 2. Calculate Robust Transforms per Island
    for island in islands:
        if not island:
            continue

        mat_idx = island[0].material_index

        # A. Find Dominant Face (Largest Area)
        # We use this instead of averaging to prevent "Diagonal" normals on cubes
        dominant_face = max(island, key=lambda f: f.calc_area())

        # B. Calculate Center (Geometric Center of the Island)
        center = Vector((0, 0, 0))
        total_a = 0.0
        for f in island:
            a = f.calc_area()
            center += f.calc_center_median() * a
            total_a += a

        if total_a < 0.0001:
            final_center = dominant_face.calc_center_median()
        else:
            final_center = center / total_a

        # C. Calculate Robust Orientation (Tangent aligned)
        # Normal Z = Face Normal
        vec_z = dominant_face.normal.normalized()

        # Tangent Y = Try to align with Global Z (Up), else Global Y
        # This prevents the socket from rotating randomly around its normal
        global_up = Vector((0, 0, 1))

        # If normal is pointing roughly Up/Down, we can't use Up as tangent.
        if abs(vec_z.dot(global_up)) > 0.95:
            # Use Global Y as the reference "Up" for the socket
            ref_vec = Vector((0, 1, 0))
        else:
            ref_vec = global_up

        # Calculate X (Right)
        vec_x = ref_vec.cross(vec_z).normalized()
        # Recalculate Y (Up) to ensure orthogonality
        vec_y = vec_z.cross(vec_x).normalized()

        # Construct Rotation Matrix
        rot_mat = Matrix((vec_x, vec_y, vec_z)).transposed()  # 3x3 Rotation

        sockets.setdefault(mat_idx, []).append((final_center, rot_mat))

    return sockets


def spawn_socket_objects(
    parent_obj, socket_data, manifest, global_scale, use_rot, rotation
):
    """
    Spawns Empty objects based on the calculated matrices.
    """
    for s_idx, data_list in socket_data.items():
        name = manifest[s_idx]["name"]
        safe = "".join(c for c in name if c.isalnum() or c in (" ", "_", "-")).strip()

        for i, (loc, rot_mat) in enumerate(data_list):
            sock_name = f"SOCKET_{safe}_{i}"
            sock = bpy.data.objects.new(sock_name, None)

            # Setup Visuals
            sock.empty_display_type = "SINGLE_ARROW"
            sock.empty_display_size = 0.2 * global_scale

            # 1. Apply Local Transform
            # Convert 3x3 Rot Matrix to 4x4 for placement
            local_mat = rot_mat.to_4x4()
            local_mat.translation = loc

            sock.matrix_world = local_mat

            # 2. Apply Global Rotation (if user rotated the main object)
            if use_rot:
                # If the parent is rotated, we must rotate the socket's location AND rotation
                global_rot = Euler(rotation, "XYZ").to_matrix().to_4x4()

                # New Location = Rot @ Old Location
                new_loc = global_rot @ sock.location
                sock.location = new_loc

                # New Rotation = Rot @ Old Rotation
                sock.rotation_euler = (global_rot @ sock.matrix_world).to_euler()

            # Link and Parent
            bpy.context.collection.objects.link(sock)
            sock.parent = parent_obj
