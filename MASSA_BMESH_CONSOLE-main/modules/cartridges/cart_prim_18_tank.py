import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_18: Spherified Tank",
    "id": "prim_18_tank",
    "icon": "MESH_UVSPHERE",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Tank is a closed volume
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": False,
    },
}


class MASSA_OT_PrimTank(Massa_OT_Base):
    bl_idname = "massa.gen_prim_18_tank"
    bl_label = "PRIM_18: Tank"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    radius: FloatProperty(name="Radius", default=0.5, min=0.1)
    length: FloatProperty(name="Total Length", default=2.0, min=0.2)

    # --- 2. TOPOLOGY ---
    subdivisions: IntProperty(name="Sphere Res", default=3, min=1, max=5)
    body_segs: IntProperty(name="Body Loops", default=4, min=1)

    # --- 3. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        V2 Standard:
        Slot 0 (Body) -> SKIP (We apply TUBE_Y).
        Slot 1 (Caps) -> SKIP (We apply BOX).
        """
        return {
            0: {"name": "Tank Body", "uv": "SKIP", "phys": "METAL_STEEL"},
            1: {"name": "End Caps", "uv": "SKIP", "phys": "METAL_STEEL"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "length")

        layout.separator()
        layout.label(text="Topology", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "subdivisions")
        col.prop(self, "body_segs")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        # 1. GENERATE QUAD SPHERE (The Caps)
        # ----------------------------------------------------------------------
        # Start with Cube sized 2.0 (Radius 1.0 approx)
        bmesh.ops.create_cube(bm, size=2.0)

        # Subdivide (Catmull-Clark) to create sphere topology
        bmesh.ops.subdivide_edges(
            bm,
            edges=bm.edges[:],
            cuts=self.subdivisions,
            use_grid_fill=True,
            smooth=1.0,
        )

        # Spherify (Normalize vertices to Radius)
        bm.verts.ensure_lookup_table()
        for v in bm.verts:
            v.co = v.co.normalized() * self.radius

        # Assign ALL initial faces to Slot 1 (Caps)
        for f in bm.faces:
            f.material_index = 1
            f.smooth = True

        # 2. ELONGATE (Bisect & Bridge)
        # ----------------------------------------------------------------------
        # Calculate cylinder length required
        cyl_len = max(0.0, self.length - (2 * self.radius))
        offset = cyl_len / 2

        if offset > 0.001:
            # A. FIND EQUATOR
            # We look for edges lying exactly on Y=0 plane
            bm.edges.ensure_lookup_table()
            equator_edges = []
            for e in bm.edges:
                v1, v2 = e.verts
                if abs(v1.co.y) < 0.001 and abs(v2.co.y) < 0.001:
                    equator_edges.append(e)

            # B. SPLIT EQUATOR
            # This duplicates the vertices along the ring
            if equator_edges:
                bmesh.ops.split_edges(bm, edges=equator_edges)

            # C. TRANSLATE HALVES
            # Now we must decide which vertices go Left (-Y) and which go Right (+Y)
            bm.verts.ensure_lookup_table()

            verts_right = []
            verts_left = []

            for v in bm.verts:
                y = v.co.y
                if y > 0.001:
                    verts_right.append(v)
                elif y < -0.001:
                    verts_left.append(v)
                else:
                    # On the seam. Check neighbors to determine allegiance.
                    is_right = False
                    for e in v.link_edges:
                        ov = e.other_vert(v)
                        if ov.co.y > 0.001:
                            is_right = True
                            break

                    if is_right:
                        verts_right.append(v)
                    else:
                        verts_left.append(v)

            # Move them
            bmesh.ops.translate(bm, vec=(0, offset, 0), verts=verts_right)
            bmesh.ops.translate(bm, vec=(0, -offset, 0), verts=verts_left)

            # D. BRIDGE GAP
            # Find open boundary edges created by the split
            bm.edges.ensure_lookup_table()
            boundary_edges = [e for e in bm.edges if e.is_boundary]

            if boundary_edges:
                ret_bridge = bmesh.ops.bridge_loops(bm, edges=boundary_edges)
                bridge_faces = ret_bridge["faces"]

                # E. SUBDIVIDE BODY
                # To maintain quad density, we cut the long bridge faces
                if self.body_segs > 1:
                    # Get edges that run lengthwise (connecting the two loops)
                    bridge_edges = list({e for f in bridge_faces for e in f.edges})

                    # Filter: Lengthwise edges span roughly 'cyl_len' distance in Y
                    long_edges = []
                    for e in bridge_edges:
                        v1, v2 = e.verts
                        dist_y = abs(v1.co.y - v2.co.y)
                        if dist_y > (cyl_len * 0.9):
                            long_edges.append(e)

                    if long_edges:
                        bmesh.ops.subdivide_edges(
                            bm,
                            edges=long_edges,
                            cuts=(self.body_segs - 1),
                            use_grid_fill=True,
                        )

                # F. ROBUST MATERIAL ASSIGNMENT
                # Use GEOMETRIC POSITION to identify body faces.
                # Body faces are strictly between -offset and +offset.
                # Cap faces are outside this range.
                # We use a slight epsilon to avoid floating point jitter at the seam.

                limit = offset - 0.001

                bm.faces.ensure_lookup_table()
                for f in bm.faces:
                    cen_y = f.calc_center_median().y
                    if abs(cen_y) < limit:
                        f.material_index = 0  # Body
                    else:
                        f.material_index = 1  # Caps

        # 3. UV MAPPING (Split Strategy)
        # ----------------------------------------------------------------------
        uv_layer = bm.loops.layers.uv.verify()

        # Scale Factors
        perim = 2 * math.pi * self.radius
        s_u = 1.0 if self.fit_uvs else (self.uv_scale * perim)
        s_box = self.uv_scale  # For caps

        # Bounding box for FIT mode on caps
        if self.fit_uvs:
            min_v = Vector((float("inf"),) * 3)
            max_v = Vector((float("-inf"),) * 3)
            for v in bm.verts:
                for i in range(3):
                    min_v[i] = min(min_v[i], v.co[i])
                    max_v[i] = max(max_v[i], v.co[i])
            dims = max_v - min_v
            for i in range(3):
                dims[i] = max(0.001, dims[i])

        for f in bm.faces:
            # --- SLOT 0: BODY (Tube Mapping) ---
            if f.material_index == 0:
                for l in f.loops:
                    co = l.vert.co
                    # U: Radial Angle
                    angle = math.atan2(co.z, co.x)
                    u = (angle / (2 * math.pi)) + 0.5

                    # V: Linear Y
                    # Normalize V relative to total length for consistency
                    v = (co.y + (self.length / 2)) / self.length

                    if not self.fit_uvs:
                        u *= s_u
                        v = co.y * self.uv_scale

                    l[uv_layer].uv = (u, v)

                # Seam Fix (Wrap 0.99 -> 0.01)
                us = [l[uv_layer].uv.x for l in f.loops]
                if max(us) - min(us) > 0.5:
                    for l in f.loops:
                        if l[uv_layer].uv.x < 0.5:
                            l[uv_layer].uv.x += 1.0

            # --- SLOT 1: CAPS (Box Mapping) ---
            else:
                n = f.normal
                nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

                for l in f.loops:
                    co = l.vert.co
                    u, v = 0.0, 0.0

                    # Y-Dominant (Ends) -> Project XZ
                    if ny > nx and ny > nz:
                        u, v = co.x, co.z
                        if self.fit_uvs:
                            u = (u - min_v.x) / dims.x
                            v = (v - min_v.z) / dims.z

                    # Z-Dominant -> Project XY
                    elif nz > nx and nz > ny:
                        u, v = co.x, co.y
                        if self.fit_uvs:
                            u = (u - min_v.x) / dims.x
                            v = (v - min_v.y) / dims.y

                    # X-Dominant -> Project YZ
                    else:
                        u, v = co.y, co.z
                        if self.fit_uvs:
                            u = (u - min_v.y) / dims.y
                            v = (v - min_v.z) / dims.z

                    if not self.fit_uvs:
                        u *= s_box
                        v *= s_box

                    l[uv_layer].uv = (u, v)

        # 5. MARK SEAMS
        # ----------------------------------------------------------------------
        for e in bm.edges:
            if len(e.link_faces) >= 2:
                # Material Boundaries (Caps vs Body)
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True
                    continue

        # 6. PIVOT CORRECTION & CLEANUP
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        # Move pivot to Bottom (Sit on Grid)
        bmesh.ops.translate(bm, vec=(0, 0, self.radius), verts=bm.verts)
