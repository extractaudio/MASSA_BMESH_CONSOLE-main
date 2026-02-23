import bmesh
import math
from mathutils import Vector, Matrix

class MassaBuilder:
    """
    A high-level wrapper around Blender's BMesh API designed to simplify procedural geometry generation.
    It provides a fluent interface for creation, selection, modification, and tagging of geometry.

    Usage Example:
        builder = MassaBuilder(bm)
        builder.create_box(1, 1, 1) \
               .select_facing(Vector((0, 0, 1))) \
               .extrude(0.5) \
               .tag_slot(1)
    """

    def __init__(self, bm: bmesh.types.BMesh):
        self.bm = bm
        self.active_faces = []
        self.active_edges = []
        self.active_verts = []

        # Ensure lookup tables are current
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()

    def _update(self):
        """Internal: Refreshes BMesh lookup tables. Call after geometry changes."""
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()
        return self

    # =========================================================================
    # 1. CREATION METHODS
    # =========================================================================

    def create_box(self, width=1.0, depth=1.0, height=1.0, center=None):
        """
        Creates a box at the specified center.

        Args:
            width (float): Size in X.
            depth (float): Size in Y.
            height (float): Size in Z.
            center (Vector): Location of the box center (default: 0,0,0).

        Returns:
            self
        """
        if center is None:
            center = Vector((0, 0, 0))

        ret = bmesh.ops.create_cube(self.bm, size=1.0)
        verts = ret['verts']
        bmesh.ops.scale(self.bm, vec=(width, depth, height), verts=verts)
        bmesh.ops.translate(self.bm, vec=center, verts=verts)

        self.active_verts = verts
        # Capture faces reliably
        self.bm.verts.ensure_lookup_table()
        if 'faces' in ret:
            self.active_faces = [f for f in ret['faces'] if isinstance(f, bmesh.types.BMFace)]
        else:
            self.active_faces = list(set(f for v in verts for f in v.link_faces))

        self._update()
        return self

    def create_grid(self, x_segments=1, y_segments=1, size=1.0, center=None):
        """
        Creates a grid (plane) on the XY plane.

        Args:
            x_segments (int): Number of subdivisions in X.
            y_segments (int): Number of subdivisions in Y.
            size (float): Overall size (Diameter).
            center (Vector): Location (default: 0,0,0).

        Returns:
            self
        """
        if center is None:
            center = Vector((0, 0, 0))

        ret = bmesh.ops.create_grid(
            self.bm,
            x_segments=x_segments,
            y_segments=y_segments,
            size=size  # Fix: create_grid uses diameter/width
        )
        verts = ret['verts']
        bmesh.ops.translate(self.bm, vec=center, verts=verts)

        self.active_verts = verts
        self.bm.verts.ensure_lookup_table()
        if 'faces' in ret:
            self.active_faces = [f for f in ret['faces'] if isinstance(f, bmesh.types.BMFace)]
        else:
            self.active_faces = list(set(f for v in verts for f in v.link_faces))

        self._update()
        return self

    def create_cylinder(self, radius=1.0, depth=2.0, segments=16, cap_ends=True, center=None):
        """
        Creates a cylinder aligned with the Z axis.

        Args:
            radius (float): Radius of the cylinder.
            depth (float): Height (Z) of the cylinder.
            segments (int): Number of radial segments.
            cap_ends (bool): Whether to close the top and bottom.
            center (Vector): Location (default: 0,0,0).

        Returns:
            self
        """
        if center is None:
            center = Vector((0, 0, 0))

        ret = bmesh.ops.create_cone(
            self.bm,
            cap_ends=cap_ends,
            cap_tris=False,
            segments=segments,
            radius1=radius,
            radius2=radius,
            depth=depth
        )
        verts = ret['verts']
        bmesh.ops.translate(self.bm, vec=center, verts=verts)

        self.active_verts = verts
        self.bm.verts.ensure_lookup_table()
        if 'faces' in ret: # Sometimes in 'geom'
            self.active_faces = [f for f in ret['faces'] if isinstance(f, bmesh.types.BMFace)]
        elif 'geom' in ret:
            self.active_faces = [f for f in ret['geom'] if isinstance(f, bmesh.types.BMFace)]
        else:
            self.active_faces = list(set(f for v in verts for f in v.link_faces))

        self._update()
        return self

    def create_cone(self, radius_bottom=1.0, radius_top=0.0, depth=2.0, segments=16, cap_ends=True, center=None):
        """
        Creates a cone or truncated cone aligned with the Z axis.

        Args:
            radius_bottom (float): Radius at the base (Z-).
            radius_top (float): Radius at the top (Z+).
            depth (float): Height (Z).
            segments (int): Radial segments.
            cap_ends (bool): Cap top/bottom.
            center (Vector): Location (default: 0,0,0).

        Returns:
            self
        """
        if center is None:
            center = Vector((0, 0, 0))

        ret = bmesh.ops.create_cone(
            self.bm,
            cap_ends=cap_ends,
            cap_tris=False,
            segments=segments,
            radius1=radius_bottom,
            radius2=radius_top,
            depth=depth
        )
        verts = ret['verts']
        bmesh.ops.translate(self.bm, vec=center, verts=verts)

        self.active_verts = verts
        self.bm.verts.ensure_lookup_table()
        if 'faces' in ret:
            self.active_faces = [f for f in ret['faces'] if isinstance(f, bmesh.types.BMFace)]
        elif 'geom' in ret:
            self.active_faces = [f for f in ret['geom'] if isinstance(f, bmesh.types.BMFace)]
        else:
            self.active_faces = list(set(f for v in verts for f in v.link_faces))

        self._update()
        return self

    # =========================================================================
    # 2. SELECTION METHODS
    # =========================================================================

    def select_all_faces(self):
        """Selects all faces in the mesh."""
        self.active_faces = [f for f in self.bm.faces]
        return self

    def select_faces_by_normal(self, direction: Vector, tolerance=0.1):
        """
        Selects faces whose normal aligns with the given direction.

        Args:
            direction (Vector): The target direction (e.g., Vector((0,0,1)) for Up).
            tolerance (float): Dot product tolerance (1.0 = exact match, 0.9 = within ~25 deg).
        """
        direction = direction.normalized()
        self.active_faces = [
            f for f in self.bm.faces
            if f.normal.dot(direction) >= (1.0 - tolerance)
        ]
        return self

    def select_faces_by_height(self, min_z=-float('inf'), max_z=float('inf')):
        """
        Selects faces based on their center Z coordinate.
        """
        self.active_faces = [
            f for f in self.bm.faces
            if min_z <= f.calc_center_median().z <= max_z
        ]
        return self

    def select_faces_by_slot(self, slot_index: int):
        """Selects faces that are assigned to a specific material slot index."""
        self.active_faces = [
            f for f in self.bm.faces
            if f.material_index == slot_index
        ]
        return self

    def select_boundary(self):
        """
        Selects boundary edges of the current face selection.
        If no faces selected, selects mesh boundary.
        Updates active_edges.
        """
        if self.active_faces:
            candidates = set()
            for f in self.active_faces:
                for e in f.edges:
                    candidates.add(e)
            # Boundary edge = edge used by only 1 SELECTED face
            # Or edge on mesh boundary if no adjacent faces exist

            # Simple approach: An edge is a boundary of the selection if it belongs
            # to a selected face but not to another selected face.
            sel_faces = set(self.active_faces)
            boundary = []
            for e in candidates:
                linked_sel = [f for f in e.link_faces if f in sel_faces]
                if len(linked_sel) == 1:
                    boundary.append(e)
            self.active_edges = boundary
        else:
            # Mesh boundary
            self.active_edges = [e for e in self.bm.edges if e.is_boundary]

        return self

    def grow_selection(self, steps=1):
        """Expands the current face selection by adjacency."""
        if not self.active_faces:
            return self

        current = set(self.active_faces)
        for _ in range(steps):
            new_faces = set()
            for f in current:
                for e in f.edges:
                    for linked in e.link_faces:
                        new_faces.add(linked)
            current.update(new_faces)

        self.active_faces = list(current)
        return self

    def shrink_selection(self, steps=1):
        """Shrinks the current face selection."""
        if not self.active_faces:
            return self

        current = set(self.active_faces)
        for _ in range(steps):
            # Find boundary faces of the selection
            boundary_faces = set()
            for f in current:
                is_boundary = False
                for e in f.edges:
                    # If any edge connects to a non-selected face, this face is boundary
                    linked_sel = [lf for lf in e.link_faces if lf in current]
                    # If edge has neighbor not in current, or is open boundary
                    if len(linked_sel) < len(e.link_faces) or e.is_boundary:
                        is_boundary = True
                        break
                if is_boundary:
                    boundary_faces.add(f)

            current.difference_update(boundary_faces)
            if not current:
                break

        self.active_faces = list(current)
        return self

    def clear_selection(self):
        """Clears active selection lists."""
        self.active_faces = []
        self.active_edges = []
        self.active_verts = []
        return self

    # =========================================================================
    # 3. MODIFICATION METHODS
    # =========================================================================

    def extrude(self, distance: float, axis: Vector = None):
        """
        Extrudes currently selected faces.

        Args:
            distance (float): Distance to extrude.
            axis (Vector): If None, extrudes along face normals (Region Extrude).
                           If set, translates along this global axis.
        """
        if not self.active_faces:
            return self

        ret = bmesh.ops.extrude_face_region(self.bm, geom=self.active_faces)

        extruded_faces = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMFace)]
        extruded_verts = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]

        # Calculate Translation
        if axis:
            vec = axis.normalized() * distance
            bmesh.ops.translate(self.bm, vec=vec, verts=extruded_verts)
        else:
            # Fix: Avoid crash on opposing normals (zero sum)
            avg_normal = Vector((0,0,0))
            for f in self.active_faces:
                avg_normal += f.normal

            # Check length before normalizing
            if avg_normal.length_squared > 0.0001:
                avg_normal = avg_normal.normalized()
                bmesh.ops.translate(self.bm, vec=avg_normal * distance, verts=extruded_verts)
            else:
                # If opposing normals, do not translate (or default to Z?)
                # Usually region extrude without translate creates zero-volume geometry,
                # but with opposing faces it might expand outwards?
                # Actually, standard region extrude behavior without translate is to leave faces in place.
                # If users selected opposing faces, they likely wanted 'extrude individual along normal'
                # but extrude_face_region treats them as a group.
                # We'll just skip translation to be safe.
                pass

        # Update Selection to the new faces
        self.active_faces = extruded_faces
        self._update()
        return self

    def inset(self, amount: float, depth: float = 0.0, relative=False):
        """
        Insets selected faces.

        Args:
            amount (float): Inset distance.
            depth (float): Depth offset (negative for groove, positive for protrusion).
            relative (bool): Use relative scaling instead of absolute distance.
        """
        if not self.active_faces:
            return self

        # Fixed: use_relative not supported by inset_individual in this API version
        ret = bmesh.ops.inset_individual(
            self.bm,
            faces=self.active_faces,
            thickness=amount,
            depth=depth
        )

        # Selection usually remains valid faces or new faces?
        # inset_individual modifies existing faces or replaces them.
        # We should update active_faces to be the result.
        self.active_faces = [f for f in ret['faces'] if f.is_valid]
        self._update()
        return self

    def transform(self, matrix: Matrix):
        """
        Applies a generic 4x4 transform matrix to active selection (or all if none selected).
        """
        target_verts = []
        if self.active_faces:
            for f in self.active_faces: target_verts.extend(f.verts)
        elif self.active_verts:
            target_verts = self.active_verts
        else:
            target_verts = self.bm.verts[:]

        target_verts = list(set(target_verts)) # Unique
        bmesh.ops.transform(self.bm, matrix=matrix, verts=target_verts)
        self._update()
        return self

    def translate(self, x=0.0, y=0.0, z=0.0):
        return self.transform(Matrix.Translation((x, y, z)))

    def rotate(self, angle_degrees, axis='Z'):
        """Rotates selection around center (0,0,0). For local rotation, use advanced transform."""
        rad = math.radians(angle_degrees)
        rot_mat = Matrix.Rotation(rad, 4, axis)
        return self.transform(rot_mat)

    def scale(self, x=1.0, y=1.0, z=1.0):
        scale_mat = Matrix.Scale(x, 4, (1,0,0)) @ Matrix.Scale(y, 4, (0,1,0)) @ Matrix.Scale(z, 4, (0,0,1))
        return self.transform(scale_mat)

    # =========================================================================
    # 4. TAGGING & SLOTS
    # =========================================================================

    def tag_slot(self, slot_index: int):
        """
        Assigns the specified material slot index to currently selected faces.
        """
        if not self.active_faces:
            return self

        for f in self.active_faces:
            f.material_index = slot_index
        return self

    def tag_edge_role(self, role_id: int):
        """
        Assigns the 'MASSA_EDGE_SLOTS' layer value to edges of selected faces.

        Args:
            role_id (int):
                1 = Perimeter (Seam + Sharp). Used for End Caps.
                2 = Contour (Sharp). Used for sharp turns.
                3 = Guide (Seam Only). Used for cutting tubes/cylinders.
                4 = Detail (Bevel). Small details.
                5 = Fold (Crease). Soft body pinning.
        """
        layer = self.bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not layer:
            layer = self.bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        target_edges = set()
        if self.active_faces:
            for f in self.active_faces:
                for e in f.edges:
                    target_edges.add(e)
        elif self.active_edges:
            target_edges = set(self.active_edges)

        for e in target_edges:
            e[layer] = role_id

        return self

    def tag_socket(self, socket_id: int):
        """
        Tags selected faces as Socket Locations using 'MASSA_SOCKETS' layer.
        """
        layer = self.bm.faces.layers.int.get("MASSA_SOCKETS")
        if not layer:
            layer = self.bm.faces.layers.int.new("MASSA_SOCKETS")

        if self.active_faces:
            for f in self.active_faces:
                f[layer] = socket_id
        return self

    def tag_uvs(self, scale=1.0, projection='BOX', axis='Z'):
        """
        Projects UVs onto selected faces.
        Supports: 'BOX' (Tri-planar), 'VIEW' (Planar Z), 'CYLINDER' (Basic polar).
        """
        uv_layer = self.bm.loops.layers.uv.verify()
        target_faces = self.active_faces if self.active_faces else self.bm.faces

        for f in target_faces:
            n = f.normal
            for l in f.loops:
                v = l.vert.co
                u, v_coord = 0.0, 0.0

                if projection == 'BOX':
                    # Tri-planar projection based on normal
                    if abs(n.z) >= 0.5: # Top/Bottom
                        u, v_coord = v.x, v.y
                    elif abs(n.x) >= 0.5: # Left/Right
                        u, v_coord = v.y, v.z
                    else: # Front/Back
                        u, v_coord = v.x, v.z

                elif projection == 'VIEW':
                    # Planar Z projection
                    u, v_coord = v.x, v.y

                elif projection == 'CYLINDER':
                    # Polar projection
                    if axis == 'Z':
                        angle = math.atan2(v.y, v.x)
                        v_coord = v.z
                    elif axis == 'X':
                        # Along X. Circle in YZ.
                        angle = math.atan2(v.z, v.y)
                        v_coord = v.x
                    elif axis == 'Y':
                        # Along Y. Circle in XZ.
                        angle = math.atan2(v.x, v.z)
                        v_coord = v.y
                    else: # Default Z
                        angle = math.atan2(v.y, v.x)
                        v_coord = v.z

                    u = angle / (2 * math.pi)

                elif projection == 'FIT':
                    # Per-face normalization (0..1)
                    # Requires 2 passes per face
                    pass

                if projection != 'FIT':
                    l[uv_layer].uv = (u * scale, v_coord * scale)

            if projection == 'FIT':
                # Handle FIT separately per face
                u_vals, v_vals, loop_data = [], [], []
                plane = 'XZ'
                if abs(n.z) >= 0.5: plane = 'XY'
                elif abs(n.x) >= 0.5: plane = 'YZ'

                for l in f.loops:
                    vv = l.vert.co
                    if plane == 'XY': uu, vv_c = vv.x, vv.y
                    elif plane == 'YZ': uu, vv_c = vv.y, vv.z
                    else: uu, vv_c = vv.x, vv.z
                    u_vals.append(uu)
                    v_vals.append(vv_c)
                    loop_data.append((l, uu, vv_c))

                if not u_vals: continue
                min_u, max_u = min(u_vals), max(u_vals)
                min_v, max_v = min(v_vals), max(v_vals)
                w, h = max_u - min_u, max_v - min_v

                for l, uu, vv_c in loop_data:
                    nu = (uu - min_u) / w if w > 0.0001 else 0.5
                    nv = (vv_c - min_v) / h if h > 0.0001 else 0.5
                    l[uv_layer].uv = (nu, nv)

        return self

    # =========================================================================
    # 5. CLEANUP & FINISH
    # =========================================================================

    def clean(self):
        """Runs remove_doubles and recalc_normals."""
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts[:], dist=0.0001)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        self._update()
        return self

    # =========================================================================
    # 6. SPATIAL ANALYSIS (The "Eyes")
    # =========================================================================

    def get_active_bounds(self):
        """
        Returns (min_vec, max_vec, center_vec) of the current selection.
        If no selection, returns world bounds of mesh.
        """
        verts = []
        if self.active_faces:
            for f in self.active_faces: verts.extend(f.verts)
        elif self.active_verts:
            verts = self.active_verts
        else:
            verts = self.bm.verts

        if not verts:
            return Vector((0,0,0)), Vector((0,0,0)), Vector((0,0,0))

        min_v = Vector((float('inf'), float('inf'), float('inf')))
        max_v = Vector((float('-inf'), float('-inf'), float('-inf')))

        for v in verts:
            min_v.x = min(min_v.x, v.co.x)
            min_v.y = min(min_v.y, v.co.y)
            min_v.z = min(min_v.z, v.co.z)
            max_v.x = max(max_v.x, v.co.x)
            max_v.y = max(max_v.y, v.co.y)
            max_v.z = max(max_v.z, v.co.z)

        center = (min_v + max_v) / 2.0
        return min_v, max_v, center

    def get_active_dimensions(self):
        """Returns Vector(width, depth, height) of selection."""
        min_v, max_v, _ = self.get_active_bounds()
        return max_v - min_v

    def get_active_center(self):
        """Returns the median center of the selection."""
        _, _, center = self.get_active_bounds()
        return center

    def get_active_normal(self):
        """Returns the average normal of selected faces."""
        if not self.active_faces:
            return Vector((0,0,1))

        avg = Vector((0,0,0))
        for f in self.active_faces:
            avg += f.normal

        if avg.length_squared > 0:
            return avg.normalized()
        return Vector((0,0,1))

    def measure_distance(self, target: Vector):
        """Returns Euclidean distance from selection center to target vector."""
        center = self.get_active_center()
        return (target - center).length

    # =========================================================================
    # 7. TOPOLOGY TOOLS (The "Muscle")
    # =========================================================================

    def bridge_selection(self, cuts=0, twist=0):
        """
        Bridges two selected edge loops or face regions.
        Use 'select_boundary' before calling if you have faces selected.
        """
        # If faces are selected, convert to boundary edges implicitly?
        # Or let user do it? Let's try to be smart.
        target_edges = []
        if self.active_edges:
            target_edges = self.active_edges
        elif self.active_faces:
            # Auto-detect boundary
            candidates = set()
            sel_faces = set(self.active_faces)
            for f in self.active_faces:
                for e in f.edges:
                    linked_sel = [lf for lf in e.link_faces if lf in sel_faces]
                    if len(linked_sel) == 1:
                        candidates.add(e)
            target_edges = list(candidates)

        if not target_edges:
            return self

        ret = bmesh.ops.bridge_loops(
            self.bm,
            edges=target_edges,
            use_pairs=True,
            use_cyclic=False
        )

        # New faces are in ret['faces']
        self.active_faces = ret['faces']
        self._update()
        return self

    def fill_grid(self, span=0, offset=0):
        """
        Fills a closed edge loop with a grid.
        Requires active edges to form a valid loop.
        """
        if not self.active_edges:
            return self

        try:
            # span/offset not supported in bmesh.ops.grid_fill in this API version
            ret = bmesh.ops.grid_fill(
                self.bm,
                edges=self.active_edges
            )
            self.active_faces = ret['faces']
        except RuntimeError:
            # Grid fill is finicky, requires even edge count
            pass

        self._update()
        return self

    def bevel(self, offset=0.1, segments=1, profile=0.5, clamp_overlap=True):
        """Bevels selected edges or faces."""
        # Prioritize edges if explicitly selected, otherwise faces
        geom = []
        if self.active_edges:
            geom = self.active_edges
        elif self.active_faces:
            geom = self.active_faces # Beveling faces bevels their edges

        if not geom:
            return self

        ret = bmesh.ops.bevel(
            self.bm,
            geom=geom,
            offset=offset,
            offset_type='OFFSET',
            segments=segments,
            profile=profile,
            vertex_only=False,
            clamp_overlap=clamp_overlap
        )

        # Update selection to new faces
        self.active_faces = [f for f in ret['faces'] if isinstance(f, bmesh.types.BMFace)]
        self._update()
        return self

    def subdivide(self, cuts=1, fractal=0.0, smooth=0.0):
        """Subdivides selected edges/faces."""
        geom = []
        if self.active_faces:
            geom.extend(self.active_faces)
            # Also include inner edges
            edges = set()
            for f in self.active_faces:
                for e in f.edges:
                    edges.add(e)
            geom.extend(list(edges))
        elif self.active_edges:
            geom.extend(self.active_edges)

        if not geom:
            return self

        ret = bmesh.ops.subdivide_edges(
            self.bm,
            edges=[e for e in geom if isinstance(e, bmesh.types.BMEdge)],
            cuts=cuts,
            fractal=fractal,
            smooth=smooth,
            use_grid_fill=True
        )

        # Capture new geometry
        self.active_faces = [f for f in ret['geom_inner'] if isinstance(f, bmesh.types.BMFace)]
        # Add original split faces
        split = [f for f in ret['geom_split'] if isinstance(f, bmesh.types.BMFace)]
        self.active_faces.extend(split)

        self._update()
        return self

    def relax_verts(self, iterations=3, factor=0.5):
        """
        Smooths active vertices (Laplacian smooth).
        Useful for organic shapes or fixing jagged extrusions.
        """
        verts = []
        if self.active_verts:
            verts = self.active_verts
        elif self.active_faces:
            unique = set()
            for f in self.active_faces:
                for v in f.verts: unique.add(v)
            verts = list(unique)

        if not verts:
            return self

        for _ in range(iterations):
            bmesh.ops.smooth_vert(
                self.bm,
                verts=verts,
                factor=factor,
                use_axis_x=True,
                use_axis_y=True,
                use_axis_z=True
            )

        self._update()
        return self

    # =========================================================================
    # 8. PRECISION TRANSFORMS (The "Hands")
    # =========================================================================

    def align_normal_to_vector(self, target_vector: Vector):
        """
        Rotates the selection so its average normal matches the target vector.
        """
        current_normal = self.get_active_normal()
        if current_normal.length_squared < 0.001:
            return self

        target_vector = target_vector.normalized()
        rot_quat = current_normal.rotation_difference(target_vector)

        center = self.get_active_center()

        # Translate to origin, rotate, translate back
        t_mat_inv = Matrix.Translation(-center)
        r_mat = rot_quat.to_matrix().to_4x4()
        t_mat = Matrix.Translation(center)

        final_mat = t_mat @ r_mat @ t_mat_inv

        self.transform(final_mat)
        return self

    def move_center_to(self, target_location: Vector):
        """Moves the center of the selection to the target location."""
        current_center = self.get_active_center()
        diff = target_location - current_center
        return self.translate(diff.x, diff.y, diff.z)

    def fit_to_bounds(self, min_v: Vector, max_v: Vector):
        """Scales the selection to fit exactly within the given bounds."""
        curr_min, curr_max, curr_cen = self.get_active_bounds()
        curr_size = curr_max - curr_min

        target_size = max_v - min_v
        target_center = (min_v + max_v) / 2.0

        scale_x = target_size.x / curr_size.x if curr_size.x > 0.001 else 1.0
        scale_y = target_size.y / curr_size.y if curr_size.y > 0.001 else 1.0
        scale_z = target_size.z / curr_size.z if curr_size.z > 0.001 else 1.0

        # Move to origin
        self.translate(-curr_cen.x, -curr_cen.y, -curr_cen.z)
        # Scale
        self.scale(scale_x, scale_y, scale_z)
        # Move to target center
        self.translate(target_center.x, target_center.y, target_center.z)

        return self

    def flatten(self, axis='Z'):
        """Flattens the selection along the specified global axis."""
        # Just scale to 0 on that axis
        scale_vec = Vector((1,1,1))
        if axis == 'X': scale_vec.x = 0.0
        elif axis == 'Y': scale_vec.y = 0.0
        elif axis == 'Z': scale_vec.z = 0.0

        # We need to flatten relative to the center, otherwise it snaps to 0 coordinate
        center = self.get_active_center()
        self.translate(-center.x, -center.y, -center.z)
        self.scale(scale_vec.x, scale_vec.y, scale_vec.z)
        self.translate(center.x, center.y, center.z)

        return self

    # =========================================================================
    # 9. REPORTING
    # =========================================================================

    def report(self):
        """
        Returns a string summary of the mesh state.
        Useful for agents to verify their actions.
        """
        v_count = len(self.bm.verts)
        e_count = len(self.bm.edges)
        f_count = len(self.bm.faces)

        vol = 0.0
        try:
            vol = self.bm.calc_volume()
        except:
            pass # Non-manifold or open

        sel_faces = len(self.active_faces)

        # New: Spatial Info
        min_v, max_v, center = self.get_active_bounds()
        dim = max_v - min_v

        return (
            f"--- Mesh Report ---\n"
            f"Verts: {v_count}, Edges: {e_count}, Faces: {f_count}\n"
            f"Volume: {vol:.4f}\n"
            f"Active Selection: {sel_faces} faces\n"
            f"Selection Bounds: {dim.x:.2f} x {dim.y:.2f} x {dim.z:.2f}\n"
            f"Selection Center: {center}\n"
            f"-------------------"
        )
