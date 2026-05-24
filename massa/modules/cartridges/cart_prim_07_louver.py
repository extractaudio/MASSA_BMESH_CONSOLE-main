import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, FloatVectorProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_07: Louver Vent",
    "id": "prim_07_louver",
    "icon": "MOD_ARRAY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Geometry is already volumetric
        "USE_WELD": True,         # Merge frame/backing vertices
        "FIX_DEGENERATE": True,   # Clean up potential bevel artifacts
        "ALLOW_CHAMFER": True,    # Frame edges need highlights
        "ALLOW_FUSE": False,      # Keep blades distinct for cleanliness
    },
}


class MASSA_OT_PrimLouver(Massa_OT_Base):
    bl_idname = "massa.gen_prim_07_louver"
    bl_label = "PRIM_07: Louver"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    size: FloatVectorProperty(name="Size", default=(1.0, 1.0, 0.1), min=0.01)

    frame_width: FloatProperty(name="Frame Width", default=0.1, min=0.01)
    frame_depth: FloatProperty(name="Frame Depth", default=0.1, min=0.01)

    # --- 2. LOUVERS ---
    blade_count: IntProperty(name="Blade Count", default=8, min=1)
    blade_angle: FloatProperty(name="Blade Angle", default=35.0, min=-90.0, max=90.0)
    blade_overlap: FloatProperty(name="Overlap", default=0.02)
    blade_thick: FloatProperty(name="Blade Thick", default=0.01, min=0.001)

    # --- 3. EXTRAS ---
    add_screen: BoolProperty(name="Add Backing Screen", default=True)

    # --- 4. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame",  "uv": "BOX", "phys": "METAL_ALUMINUM"},
            1: {"name": "Blades", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            2: {"name": "Screen", "uv": "BOX", "phys": "METAL_IRON"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)

        row = col.row(align=True)
        row.prop(self, "size", index=0, text="X")
        row.prop(self, "size", index=1, text="Y")
        row.prop(self, "size", index=2, text="Z")

        col.prop(self, "frame_width")
        col.prop(self, "frame_depth")

        layout.separator()
        layout.label(text="Louvers", icon="ALIGN_JUSTIFY")
        col = layout.column(align=True)
        col.prop(self, "blade_count")
        col.prop(self, "blade_angle")
        col.prop(self, "blade_overlap")
        col.prop(self, "blade_thick")
        layout.prop(self, "add_screen")

    def build_shape(self, bm: bmesh.types.BMesh):
        # Safe unpack — FloatVectorProperty returns a 3-tuple in normal use,
        # but the fuzz auditor can inject a scalar float directly.
        try:
            sx, sy, sz = self.size
        except (TypeError, ValueError):
            sx = sy = sz = float(self.size)
        fw = min(self.frame_width, sx / 2.1, sy / 2.1)  # Safety clamp
        fd = self.frame_depth

        # ----------------------------------------------------------------------
        # LAYER SETUP — must come first so mark_edge is available at geometry birth
        # ----------------------------------------------------------------------
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        force_seam = bm.edges.layers.int.get("massa_force_seam")
        if not force_seam:
            force_seam = bm.edges.layers.int.new("massa_force_seam")

        def mark_edge(e, slot=None, seam=False, sharp=False, protect=False):
            if slot is not None:
                e[edge_slots] = slot
            if seam:
                e.seam = True
            if sharp:
                e.smooth = False
            if protect:
                e[force_seam] = 1

        # ----------------------------------------------------------------------
        # 1. BUILD FRAME (Bridge Loops Method)
        # ----------------------------------------------------------------------

        # A. Outer loop (z=0)
        res_out = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
        verts_out = res_out["verts"]
        faces_out = list({f for v in verts_out for f in v.link_faces})
        bmesh.ops.delete(bm, geom=faces_out, context="FACES_ONLY")
        bmesh.ops.scale(bm, vec=(sx, sy, 1.0), verts=verts_out)

        # B. Inner loop (z=0)
        res_in = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
        verts_in = res_in["verts"]
        faces_in = list({f for v in verts_in for f in v.link_faces})
        bmesh.ops.delete(bm, geom=faces_in, context="FACES_ONLY")
        bmesh.ops.scale(bm, vec=(sx - (fw * 2), sy - (fw * 2), 1.0), verts=verts_in)

        # C. Bridge → frame ring faces
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        edges_before_bridge = bm.edges[:]
        res_bridge = bmesh.ops.bridge_loops(bm, edges=edges_before_bridge, use_pairs=True)
        faces_front = res_bridge["faces"]

        # D. Extrude frame backwards (depth)
        res_ext = bmesh.ops.extrude_face_region(bm, geom=faces_front)
        verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]
        faces_side = [f for f in res_ext["geom"] if isinstance(f, bmesh.types.BMFace)]
        bmesh.ops.translate(bm, vec=(0, 0, -fd), verts=verts_ext)

        for f in faces_front + faces_side:
            f.material_index = 0

        # --- Mark frame seams at birth — UV_PRIM_SHEET / BOX_DETAIL ---
        # Archetype: frame is a rectangular box with a hollow opening.
        # Orientation: axis-aligned, z=0 is front face, z=-fd is back face.
        # Slot 1 (perimeter/seam+sharp):   front horizontal loops and back horizontal loops.
        # Slot 2 (contour/sharp only):     depth edges connecting front to back (not UV cuts).
        frame_all_edges = {e for f in faces_front + faces_side for e in f.edges}
        for e in frame_all_edges:
            v1, v2 = e.verts
            dz = abs(v1.co.z - v2.co.z)
            z_avg = (v1.co.z + v2.co.z) * 0.5
            is_flat = dz < 0.001
            is_front_loop = is_flat and abs(z_avg) < 0.001          # z ≈ 0
            is_back_loop  = is_flat and abs(z_avg + fd) < 0.001     # z ≈ -fd
            if is_front_loop:
                # Outer and inner perimeter — seam + sharp so ring can isolate as UV island
                mark_edge(e, slot=1, seam=True, sharp=True, protect=True)
            elif is_back_loop:
                # Back rim — seam + protect (sharp optional, back face rarely visible)
                mark_edge(e, slot=1, seam=True, protect=True)
            else:
                # Depth (vertical) edges — hard contour, not UV seams
                mark_edge(e, slot=2, sharp=True)

        # Derived inner dimensions for blades
        inner_w = sx - (fw * 2)
        inner_h = sy - (fw * 2)

        # ----------------------------------------------------------------------
        # 2. BUILD BLADES — UV_PRIM_PLANK per blade
        # ----------------------------------------------------------------------
        # Archetype: each blade is a thin box rotated around X.
        # Local long axis = global X  (rotation is around X, so X direction is unchanged).
        # Cap faces:  normals ≈ ±X  → slot 1, seam + sharp + protect.
        # Zipper:     long edge with lowest average Z after rotation → slot 3, seam + protect.
        # Remaining long edges: slot 2 (contour/sharp).
        # Seams are marked after rotate (correct normals) but before translate (blade-local Z).

        long_axis = Vector((1.0, 0.0, 0.0))

        if self.blade_count > 0:
            step_y   = inner_h / self.blade_count
            blade_h  = step_y + self.blade_overlap
            start_y  = (inner_h / 2) - (step_y / 2)
            rot_mat  = Matrix.Rotation(math.radians(self.blade_angle), 4, "X")

            for i in range(self.blade_count):
                y_pos = start_y - (i * step_y)

                res_blade = bmesh.ops.create_cube(bm, size=1.0)
                verts_b   = res_blade["verts"]
                faces_b   = list({f for v in verts_b for f in v.link_faces})

                # Scale then rotate — normals now reflect post-rotation orientation
                bmesh.ops.scale(
                    bm, vec=(inner_w, blade_h, self.blade_thick), verts=verts_b
                )
                bmesh.ops.rotate(
                    bm, cent=(0, 0, 0), matrix=rot_mat, verts=verts_b
                )

                # -- Mark blade seams at birth (before translate) --
                # Cap faces: normal ≈ ±X (X-axis rotation leaves X normals unchanged)
                cap_faces = [f for f in faces_b if abs(f.normal.dot(long_axis)) > 0.7]
                cap_edges = set()
                for f in cap_faces:
                    for e in f.edges:
                        cap_edges.add(e)
                        mark_edge(e, slot=1, seam=True, sharp=True, protect=True)

                all_blade_edges = {e for f in faces_b for e in f.edges}

                # Long edges: aligned with X, not part of cap loops
                long_edges = [
                    e for e in all_blade_edges - cap_edges
                    if abs(
                        (e.verts[1].co - e.verts[0].co).normalized().dot(long_axis)
                    ) > 0.7
                ]

                # Zipper: the long edge with the lowest average Z in blade-local space.
                # After X-axis rotation, this sits on the underside (most hidden by adjacent
                # blades and typical louver viewing angles).
                if long_edges:
                    zipper = min(
                        long_edges,
                        key=lambda e: (e.verts[0].co.z + e.verts[1].co.z) * 0.5,
                    )
                    mark_edge(zipper, slot=3, seam=True, protect=True)
                    for e in long_edges:
                        if e is not zipper:
                            mark_edge(e, slot=2)

                # Remaining non-long, non-cap edges (short width/depth edges) → contour
                other_edges = all_blade_edges - cap_edges - set(long_edges)
                for e in other_edges:
                    mark_edge(e, slot=2, sharp=True)

                # Translate to final position (after seam marking)
                bmesh.ops.translate(bm, vec=(0, y_pos, -fd / 2), verts=verts_b)

                for f in faces_b:
                    f.material_index = 1

        # ----------------------------------------------------------------------
        # 3. BUILD SCREEN — UV_PRIM_SHEET
        # ----------------------------------------------------------------------
        if self.add_screen:
            res_screen = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
            verts_s = res_screen["verts"]
            faces_s = list({f for v in verts_s for f in v.link_faces})

            # Exact fit — no extra slop.  The fw*0.1 oversize caused the screen
            # corners to extend past the inner frame edge at z=-fd, creating
            # coplanar overlapping faces with the frame back-ring (ghost geometry
            # that doubled the back plate and corrupted the UV unwrap).
            screen_w = inner_w
            screen_h = inner_h
            bmesh.ops.scale(bm, vec=(screen_w, screen_h, 1.0), verts=verts_s)
            bmesh.ops.translate(bm, vec=(0, 0, -fd), verts=verts_s)

            for v in verts_s:
                for f in v.link_faces:
                    f.material_index = 2

            # Mark screen seams at birth — UV_PRIM_SHEET perimeter isolation
            # The screen is a single flat quad; all its edges are boundary at birth.
            for e in {e for f in faces_s for e in f.edges}:
                mark_edge(e, slot=1, seam=True, sharp=True, protect=True)

        # ----------------------------------------------------------------------
        # 4. CLEANUP & PIVOT
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # Pivot: raise so z-min sits at world origin
        min_z = min(v.co.z for v in bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, -min_z), verts=bm.verts)

        # After pivot: z=0 is back face, z=fd is front face of frame.

        # ----------------------------------------------------------------------
        # 5. UV MAPPING (Box Projection)
        # ----------------------------------------------------------------------
        # Projection uses post-pivot coordinates.
        # fit_uvs: z-depth mapped as z/fd (back=0, front=1) — min_z must NOT be
        # subtracted again here; it has already been applied by the translate above.
        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale
        safe_fd = max(fd, 0.0001)

        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            if nz >= nx and nz >= ny:
                # Z-dominant (front/back faces) → project XY
                for lp in f.loops:
                    if self.fit_uvs:
                        u = (lp.vert.co.x + sx * 0.5) / sx
                        v = (lp.vert.co.y + sy * 0.5) / sy
                    else:
                        u = lp.vert.co.x * s
                        v = lp.vert.co.y * s
                    lp[uv_layer].uv = (u, v)

            elif nx >= ny:
                # X-dominant (left/right walls) → project YZ
                for lp in f.loops:
                    if self.fit_uvs:
                        u = (lp.vert.co.y + sy * 0.5) / sy
                        v = lp.vert.co.z / safe_fd   # 0 = back, 1 = front
                    else:
                        u = lp.vert.co.y * s
                        v = lp.vert.co.z * s
                    lp[uv_layer].uv = (u, v)

            else:
                # Y-dominant (top/bottom walls and blade faces) → project XZ
                for lp in f.loops:
                    if self.fit_uvs:
                        u = (lp.vert.co.x + sx * 0.5) / sx
                        v = lp.vert.co.z / safe_fd   # 0 = back, 1 = front
                    else:
                        u = lp.vert.co.x * s
                        v = lp.vert.co.z * s
                    lp[uv_layer].uv = (u, v)

    def add_sockets(self, bm):
        """
        Standard Socket Definitions.
        """
        sockets = []
        sx, sy, sz = self.size

        # Top Edge (+Y)
        sockets.append({
            "name": "Link_Top",
            "type": "SOCKET_A",
            "loc": (0, sy / 2, self.frame_depth / 2),
            "rot": (math.radians(-90), 0, 0),
        })

        # Bottom Edge (-Y)
        sockets.append({
            "name": "Link_Bottom",
            "type": "SOCKET_B",
            "loc": (0, -sy / 2, self.frame_depth / 2),
            "rot": (math.radians(90), 0, 0),
        })

        return sockets
