import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_19: Recessed Tray",
    "id": "prim_19_tray",
    "icon": "BOOL_INSET",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Geometry is volumetric
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": True,
    },
}


class MASSA_OT_PrimTray(Massa_OT_Base):
    bl_idname = "massa.gen_prim_19_tray"
    bl_label = "PRIM_19: Tray"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    size: FloatVectorProperty(name="Size (XY)", default=(1.0, 1.0, 0.1), min=0.01)
    hole_radius: FloatProperty(name="Recess Radius", default=0.35, min=0.01)
    depth: FloatProperty(name="Recess Depth", default=0.08, min=0.0)

    # --- 2. TOPOLOGY ---
    # Segments per quadrant (e.g., 3 = 12 total vertices)
    resolution: IntProperty(name="Corner Res", default=4, min=1, max=16)

    # --- 3. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Tray Surface", "uv": "BOX", "phys": "SYNTH_PLASTIC"},
            1: {
                "name": "Inner Recess",
                "uv": "BOX",
                "phys": "SYNTH_PLASTIC",
                "sock": True,
            },
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "size", index=0, text="X")
        row.prop(self, "size", index=1, text="Y")
        row.prop(self, "size", index=2, text="Z")

        col.separator()
        col.prop(self, "hole_radius")
        col.prop(self, "depth", text="Recess Z")

        layout.separator()
        layout.label(text="Topology", icon="MOD_WIREFRAME")
        layout.prop(self, "resolution")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, l, h = self.size
        safe_depth = min(self.depth, h - 0.001)

        # Clamp radius
        max_r = min(w, l) / 2.0
        r = min(self.hole_radius, max_r - 0.01)

        # Total vertices around the perimeter
        # 4 quadrants * resolution
        # We start at 45 degrees to align corners properly
        seg_quad = self.resolution
        total_verts = seg_quad * 4

        # ----------------------------------------------------------------------
        # 1. GENERATE LOOPS (Top Surface at Z=0)
        # ----------------------------------------------------------------------
        # We generate pairs of vertices: (Inner, Outer) for each angle step.

        verts_in_ring = []
        verts_out_ring = []

        for i in range(total_verts):
            # Angle: 0 to 2pi, rotated by 45deg (pi/4) so i=0 is a corner
            theta = (i / total_verts) * 2 * math.pi + (math.pi / 4)

            cos_t = math.cos(theta)
            sin_t = math.sin(theta)

            # Inner Point (Circle)
            xi = cos_t * r
            yi = sin_t * r
            v_in = bm.verts.new((xi, yi, 0))
            verts_in_ring.append(v_in)

            # Outer Point (Square Projection)
            # We project the vector (cos, sin) onto the box (w, l)
            # Distance to edge X: (w/2) / abs(cos)
            # Distance to edge Y: (l/2) / abs(sin)
            # Use the smaller distance to hit the box wall

            abs_cos = max(0.0001, abs(cos_t))
            abs_sin = max(0.0001, abs(sin_t))

            scale_x = (w / 2) / abs_cos
            scale_y = (l / 2) / abs_sin

            scale = min(scale_x, scale_y)

            xo = cos_t * scale
            yo = sin_t * scale
            v_out = bm.verts.new((xo, yo, 0))
            verts_out_ring.append(v_out)

        bm.verts.ensure_lookup_table()

        # ----------------------------------------------------------------------
        # 2. SKIN TOP SURFACE
        # ----------------------------------------------------------------------
        top_faces = []

        for i in range(total_verts):
            i_next = (i + 1) % total_verts

            # Quad: In_Cur -> Out_Cur -> Out_Next -> In_Next
            v1 = verts_in_ring[i]
            v2 = verts_out_ring[i]
            v3 = verts_out_ring[i_next]
            v4 = verts_in_ring[i_next]

            f = bm.faces.new((v1, v2, v3, v4))
            f.material_index = 0
            f.smooth = False  # Top is flat
            top_faces.append(f)

        # ----------------------------------------------------------------------
        # 3. EXTRUDE OUTER WALLS (Down)
        # ----------------------------------------------------------------------
        # Collect outer edges
        edges_out = []
        for i in range(total_verts):
            # The edge connects Out[i] and Out[i+1]
            v_a = verts_out_ring[i]
            v_b = verts_out_ring[(i + 1) % total_verts]
            # Find the edge connecting them
            for e in v_a.link_edges:
                if e.other_vert(v_a) == v_b:
                    edges_out.append(e)
                    break

        res_ext_out = bmesh.ops.extrude_edge_only(bm, edges=edges_out)
        verts_bot_rim = [
            v for v in res_ext_out["geom"] if isinstance(v, bmesh.types.BMVert)
        ]

        # Move down
        bmesh.ops.translate(bm, vec=(0, 0, -h), verts=verts_bot_rim)

        # Close Bottom (Cap)
        # Find the new bottom boundary loop
        edges_bot = [e for v in verts_bot_rim for e in v.link_edges if e.is_boundary]
        # set() to dedup not needed if logic is clean, but safe
        edges_bot = list(set(edges_bot))

        if edges_bot:
            bmesh.ops.contextual_create(bm, geom=edges_bot)

        # ----------------------------------------------------------------------
        # 4. EXTRUDE INNER RECESS (Down)
        # ----------------------------------------------------------------------
        edges_in = []
        for i in range(total_verts):
            v_a = verts_in_ring[i]
            v_b = verts_in_ring[(i + 1) % total_verts]
            for e in v_a.link_edges:
                if e.other_vert(v_a) == v_b:
                    edges_in.append(e)
                    break

        res_ext_in = bmesh.ops.extrude_edge_only(bm, edges=edges_in)
        verts_floor = [
            v for v in res_ext_in["geom"] if isinstance(v, bmesh.types.BMVert)
        ]
        faces_wall = [
            f for f in res_ext_in["geom"] if isinstance(f, bmesh.types.BMFace)
        ]

        # Move down
        bmesh.ops.translate(bm, vec=(0, 0, -safe_depth), verts=verts_floor)

        # Create Floor
        edges_floor = [e for v in verts_floor for e in v.link_edges if e.is_boundary]
        edges_floor = list(set(edges_floor))

        if edges_floor:
            res_floor = bmesh.ops.contextual_create(bm, geom=edges_floor)
            faces_floor = res_floor.get("faces", [])

            # Assign Recess Slot (1)
            for f in faces_wall + faces_floor:
                f.material_index = 1
                f.smooth = True

            # FIX NORMALS: Floor must point UP
            for f in faces_floor:
                f.normal_update()
                if f.normal.z < 0:
                    f.normal_flip()

        # ----------------------------------------------------------------------
        # 5. FINAL SLOT CLEANUP
        # ----------------------------------------------------------------------
        # Re-verify slots based on geometry position to catch any extrusion artifacts
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            cen = f.calc_center_median()

            # Top Surface (Z=0)
            if abs(cen.z) < 0.001:
                f.material_index = 0
            # Bottom Cap (Z=-h)
            elif abs(cen.z - (-h)) < 0.001:
                f.material_index = 0
            # Recess Floor (Z=-depth)
            elif abs(cen.z - (-safe_depth)) < 0.001:
                f.material_index = 1
            # Outer Walls (Radius > hole_radius)
            # Recess Walls (Radius <= hole_radius)
            else:
                dist_xy = math.hypot(cen.x, cen.y)
                # If further out than hole radius (plus tolerance), it's outer wall
                if dist_xy > (r + 0.01):
                    f.material_index = 0
                else:
                    f.material_index = 1

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # ----------------------------------------------------------------------
        # 6. UV MAPPING
        # ----------------------------------------------------------------------
        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale

        # Bounding box for FIT mode
        min_v = Vector((float("inf"),) * 3)
        max_v = Vector((float("-inf"),) * 3)
        if self.fit_uvs:
            for v in bm.verts:
                for i in range(3):
                    min_v[i] = min(min_v[i], v.co[i])
                    max_v[i] = max(max_v[i], v.co[i])
            dims = max_v - min_v
            for i in range(3):
                dims[i] = max(0.001, dims[i])

        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            for l in f.loops:
                co = l.vert.co
                u, v = 0.0, 0.0

                # Z-Dominant
                if nz > nx and nz > ny:
                    u, v = co.x, co.y
                    if self.fit_uvs:
                        u = (u - min_v.x) / dims.x
                        v = (v - min_v.y) / dims.y

                # X-Dominant
                elif nx > ny and nx > nz:
                    u, v = co.y, co.z
                    if self.fit_uvs:
                        u = (u - min_v.y) / dims.y
                        v = (v - min_v.z) / dims.z

                # Y-Dominant
                else:
                    u, v = co.x, co.z
                    if self.fit_uvs:
                        u = (u - min_v.x) / dims.x
                        v = (v - min_v.z) / dims.z

                if not self.fit_uvs:
                    u *= s
                    v *= s

                l[uv_layer].uv = (u, v)
