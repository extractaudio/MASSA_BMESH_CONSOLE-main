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

        ret = bmesh.ops.inset_individual(
            self.bm,
            faces=self.active_faces,
            thickness=amount,
            depth=depth,
            use_relative=relative
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
            role_id (int): 1=Perimeter, 2=Contour, 3=Guide, 4=Detail, 5=Fold
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
    # 6. ANALYSIS & DEBUG
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

        return (
            f"--- Mesh Report ---\n"
            f"Verts: {v_count}, Edges: {e_count}, Faces: {f_count}\n"
            f"Volume: {vol:.4f}\n"
            f"Active Selection: {sel_faces} faces\n"
            f"-------------------"
        )
