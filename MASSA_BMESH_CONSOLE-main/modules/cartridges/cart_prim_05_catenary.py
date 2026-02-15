import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Quaternion
from bpy.props import FloatProperty, FloatVectorProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_05: Catenary Wire",
    "id": "prim_05_catenary",
    "icon": "CURVE_PATH",
    "scale_class": "MICRO",
    "flags": {
        "LOCK_PIVOT": True,  # Keeps Origin at Start Point for easy snapping
        "ALLOW_SOLIDIFY": False,  # Wire is solid
        "USE_WELD": True,
        "PROTECT_NORMALS": False,  # Cylindrical smoothing handles this
    },
}


class MASSA_OT_PrimCatenary(Massa_OT_Base):
    bl_idname = "massa.gen_prim_05_catenary"
    bl_label = "PRIM_05: Catenary"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- INPUTS ---
    start_point: FloatVectorProperty(name="Start (A)", default=(0.0, 0.0, 0.0))
    end_point: FloatVectorProperty(name="End (B)", default=(3.0, 0.0, 0.0))

    sag: FloatProperty(name="Sag Amount", default=0.5)
    radius: FloatProperty(name="Wire Radius", default=0.02, min=0.001)

    # --- TOPOLOGY ---
    segments_len: IntProperty(name="Length Segs", default=24, min=4)
    segments_rad: IntProperty(name="Radial Segs", default=8, min=3)

    # --- UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        FIXED: 'METAL_COPPER' replaced with 'METAL_GOLD' to match MASTER_MAT_DB registry.
        """
        return {
            0: {
                "name": "Insulation",
                "uv": "SKIP",
                "phys": "SYNTH_RUBBER",
            },  # UVs calc'd in script
            1: {"name": "Caps", "uv": "BOX", "phys": "METAL_GOLD"},
            2: {"name": "Guide Edge", "uv": "SKIP", "phys": "GENERIC"},
        }

    def invoke(self, context, event):
        """
        Smart Invoke: Captures selected objects to auto-bridge them.
        """
        sel = context.selected_objects
        # 1. Bridge 2 Objects
        if len(sel) >= 2:
            p1 = sel[0].location.copy()
            p2 = sel[1].location.copy()
            self.start_point = p1
            self.end_point = p2
            self.report({"INFO"}, f"Massa: Bridging {sel[0].name} -> {sel[1].name}")
        # 2. Bridge Cursor -> Object
        elif len(sel) == 1:
            self.start_point = context.scene.cursor.location.copy()
            self.end_point = sel[0].location.copy()

        return super().invoke(context, event)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Anchor Points (World)", icon="EMPTY_AXIS")

        # UI FIX: Using row() forces X/Y/Z to align horizontally
        row = box.row()
        row.prop(self, "start_point")

        row = box.row()
        row.prop(self, "end_point")

        layout.separator()
        layout.label(text="Profile", icon="MESH_DATA")
        layout.prop(self, "sag")
        layout.prop(self, "radius")

        layout.separator()
        layout.label(text="Topology", icon="MOD_WIREFRAME")
        row = layout.row(align=True)
        row.prop(self, "segments_rad", text="Radial")
        row.prop(self, "segments_len", text="Length")



    def build_shape(self, bm: bmesh.types.BMesh):
        # 1. Calculate Local Vector Logic
        v_start_world = Vector(self.start_point)
        v_end_world = Vector(self.end_point)

        vec_delta = v_end_world - v_start_world
        length_linear = vec_delta.length

        if length_linear < 0.001:
            bmesh.ops.create_icosphere(bm, radius=self.radius)
            return

        # --- ARC LENGTH CALCULATION (Fixes Stretching) ---
        # We approximate the parabolic arc length to scale UVs correctly.
        # Parabola: z = 4 * sag * (x/L) * (1 - x/L)
        # Exact integration is complex, numerical approximation is sufficient for UVs.
        arc_length = 0.0
        steps = 10
        prev_p = Vector((0, 0))
        for i in range(1, steps + 1):
            t = i / steps
            x = t * length_linear
            z = 4 * self.sag * t * (1.0 - t)
            curr_p = Vector((x, z))
            arc_length += (curr_p - prev_p).length
            prev_p = curr_p

        # If sagging is 0, arc_length equals linear length
        if arc_length < length_linear:
            arc_length = length_linear

        # 2. Create Straight Cylinder
        res_cone = bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=True,
            segments=self.segments_rad,
            radius1=self.radius,
            radius2=self.radius,
            depth=length_linear,
            matrix=Matrix.Translation((0, 0, length_linear / 2)),
        )

        # 3. Subdivide Length
        edges_long = []
        for e in bm.edges:
            v1, v2 = e.verts
            diff = v1.co - v2.co
            if abs(diff.z) > (length_linear * 0.9):
                edges_long.append(e)

        if self.segments_len > 1:
            bmesh.ops.subdivide_edges(
                bm, edges=edges_long, cuts=(self.segments_len - 1), use_grid_fill=True
            )

        # 3. ASSIGN MATERIALS (Before Seam Logic)
        for f in bm.faces:
            n = f.normal
            if abs(n.z) > 0.9:
                f.material_index = 1  # Caps
            else:
                f.material_index = 0  # Insulation
                f.smooth = True

        # 4. MARK SEAMS & EDGE SLOTS
        edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for e in bm.edges:
            # 1. Material Boundary (Caps vs Insulation)
            if len(e.link_faces) >= 2:
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True
                    e[edge_slots] = 1 # Perimeter

        # 3. SLOT 3: GUIDE EDGE (Zipper at -X)
        # Mark edges that are longitudinal and at angle roughly Pi (x < 0, y ~ 0)
        # matches the UV wap point: u = (phi + math.pi) / ...

        vertical_edges = []
        for e in bm.edges:
            # Filter for Insulation Body
            if not all(f.material_index == 0 for f in e.link_faces):
                continue
            
            # Filter for Vertical Alignment (before bending)
            v1, v2 = e.verts
            is_vertical = abs(v1.co.x - v2.co.x) < 0.001 and abs(v1.co.y - v2.co.y) < 0.001
            if is_vertical:
                vertical_edges.append(e)

        if vertical_edges:
            # Find the column closest to angle PI (-X axis)
            def get_edge_dist_to_pi(edge):
                mid = (edge.verts[0].co + edge.verts[1].co) * 0.5
                ang = math.atan2(mid.y, mid.x)
                return abs(abs(ang) - math.pi)

            # Analyze all vertical edges
            scored_edges = [(get_edge_dist_to_pi(e), e) for e in vertical_edges]
            
            # Find best score
            min_dist = min(s[0] for s in scored_edges)
            
            # Mark all edges in that column (tolerance for float errors)
            for dist, e in scored_edges:
                if dist < (min_dist + 0.001):
                    e.seam = True
                    e[edge_slots] = 3 # Guide Edge


        # 2. TRANSVERSE RINGS (Every 8 segments)
        # Fixes UV warping on long wires by breaking strips
        if self.segments_len >= 16:
            seg_step = length_linear / self.segments_len
            for e in bm.edges:
                if e.seam:
                    continue

                # Check Transverse (Flat Z)
                dz = abs(e.verts[0].co.z - e.verts[1].co.z)
                if dz < 0.001:
                    z_check = (e.verts[0].co.z + e.verts[1].co.z) * 0.5
                    idx = int(round(z_check / seg_step))

                    # Mark every 8th, avoiding caps (0 and max)
                    # We check idx > 0 to avoid the cap itself
                    if idx > 0 and idx < self.segments_len:
                        if idx % 8 == 0:
                            e.seam = True

        # 5. UV MAPPING (Seam-Aware & Arc-Compensated)
        uv_layer = bm.loops.layers.uv.verify()
        perim = 2 * math.pi * self.radius

        # Use ARC LENGTH for V-Scale
        s_u = (1.0) if self.fit_uvs else (self.uv_scale * perim * 4.0)
        s_v = (1.0) if self.fit_uvs else (self.uv_scale * arc_length)

        for f in bm.faces:
            n = f.normal
            if abs(n.z) > 0.9:
                # Box Map Caps
                for l in f.loops:
                    l[uv_layer].uv = (
                        l.vert.co.x * self.uv_scale,
                        l.vert.co.y * self.uv_scale,
                    )
            else:
                # --- ROBUST SEAM LOGIC (Fixes Smashed UVs) ---
                loop_uvs = []
                for l in f.loops:
                    co = l.vert.co
                    # U Calculation (0-1 radial)
                    phi = math.atan2(co.y, co.x)
                    u = (phi + math.pi) / (2 * math.pi)

                    # V Calculation (Linear Z ratio)
                    v = co.z / length_linear
                    loop_uvs.append([l, u, v])

                # Check for Seam Wrapping
                # If a face has U values near 0.0 AND 1.0 (e.g., 0.01 and 0.99)
                us = [item[1] for item in loop_uvs]
                if not us:
                    continue
                min_u, max_u = min(us), max(us)

                if (max_u - min_u) > 0.5:
                    # Unwrap: Shift the small values up by 1.0
                    for item in loop_uvs:
                        if item[1] < 0.5:
                            item[1] += 1.0

                # Apply final scaled UVs
                for l, u, v in loop_uvs:
                    l[uv_layer].uv = (u * s_u, v * s_v)

        # 5. ROTATE TO ALIGNMENT
        vec_norm = vec_delta.normalized()
        z_axis = Vector((0, 0, 1))
        rot_quat = z_axis.rotation_difference(vec_norm)

        bmesh.ops.rotate(
            bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot_quat.to_matrix()
        )

        # 6. APPLY SAG
        bm.verts.ensure_lookup_table()
        for v in bm.verts:
            proj = v.co.dot(vec_norm)
            t = proj / length_linear
            t = max(0.0, min(1.0, t))

            drop_mag = 4 * self.sag * t * (1.0 - t)
            v.co.z -= drop_mag

        # 7. MANAGE PIVOT
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
