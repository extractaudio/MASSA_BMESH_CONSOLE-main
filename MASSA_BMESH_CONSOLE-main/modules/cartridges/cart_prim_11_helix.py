import bpy
import bmesh
import math
from mathutils import Vector, Matrix, Quaternion
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_11: Helical Coil",
    "id": "prim_11_helix",
    "icon": "DRIVER_ROTATIONAL_DIFFERENCE",
    "scale_class": "MICRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Wire is a solid volume
        "USE_WELD": True,  # Merge start/end caps if they touch (rare)
        "FIX_DEGENERATE": True,  # Cleanup micro-geo
        "ALLOW_CHAMFER": False,  # Wire is usually too thin for bevels
        "LOCK_PIVOT": True,  # Pivot is strictly controlled (Base Center)
    },
}


class MASSA_OT_PrimHelix(Massa_OT_Base):
    bl_idname = "massa.gen_prim_11_helix"
    bl_label = "PRIM_11: Helix"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    radius: FloatProperty(name="Coil Radius", default=0.5, min=0.01)
    height: FloatProperty(name="Height", default=1.0, min=0.0)
    turns: FloatProperty(name="Turns", default=3.0, min=0.1)

    # --- 2. PROFILE ---
    wire_radius: FloatProperty(name="Wire Thickness", default=0.05, min=0.001)

    # --- 3. TOPOLOGY ---
    segments_radial: IntProperty(name="Wire Segs", default=12, min=3)
    segments_turn: IntProperty(name="Segs per Turn", default=16, min=3)

    # --- 4. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        V2 Standard: Defines 'TUBE_Y' for wire to follow length,
        but we calculate UVs manually for perfect twisting.
        """
        return {
            0: {"name": "Wire Surface", "uv": "SKIP", "phys": "METAL_STEEL"},
            1: {"name": "Cut Ends", "uv": "BOX", "phys": "METAL_IRON"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Coil Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "height")
        col.prop(self, "turns")

        layout.separator()
        layout.label(text="Wire Profile", icon="CURVE_PATH")
        col = layout.column(align=True)
        col.prop(self, "wire_radius")

        layout.separator()
        layout.label(text="Topology", icon="MOD_WIREFRAME")
        row = layout.row(align=True)
        row.prop(self, "segments_radial", text="Radial")
        row.prop(self, "segments_turn", text="Per Turn")



    def build_shape(self, bm: bmesh.types.BMesh):
        # 1. SETUP & MATH
        # ----------------------------------------------------------------------
        r_coil = self.radius
        r_wire = self.wire_radius
        h = self.height
        turns = self.turns

        seg_rad = self.segments_radial
        seg_turn = self.segments_turn

        total_steps = int(turns * seg_turn)
        if total_steps < 2:
            total_steps = 2

        angle_per_step = (2 * math.pi * turns) / total_steps
        z_per_step = h / total_steps

        # Calculate total arc length for accurate V-tiling
        # Helix Length L = sqrt( (2*pi*R*Turns)^2 + H^2 )
        c = 2 * math.pi * r_coil * turns
        total_len = math.sqrt(c * c + h * h)

        # UV Scale Factors
        perim_wire = 2 * math.pi * r_wire
        su = 1.0 if self.fit_uvs else (self.uv_scale * perim_wire)
        sv = 1.0 if self.fit_uvs else (self.uv_scale * total_len)

        uv_layer = bm.loops.layers.uv.verify()
        
        # Verify Edge Slots Layer
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 2. GENERATION LOOP (Construct Rings)
        # ----------------------------------------------------------------------
        # We build a list of rings, where each ring contains vertices and their metadata
        # Rings: List of [ (Vector_Pos, UV_U, UV_V) ]

        rings_data = []

        for i in range(total_steps + 1):
            t = i / total_steps  # 0.0 to 1.0 progress

            # Helix Spine Position
            angle = i * angle_per_step
            # Note: We negate angle for clockwise/standard screw direction if needed,
            # currently standard right-hand rule
            cx = math.cos(angle) * r_coil
            cy = math.sin(angle) * r_coil
            cz = i * z_per_step
            center_pos = Vector((cx, cy, cz))

            # Tangent Vector (Direction of wire)
            # Derivative of (Rcos(t), Rsin(t), ht) is (-Rsin(t), Rcos(t), h)
            # This creates the banking for the ring
            tx = -math.sin(angle)
            ty = math.cos(angle)
            tz = (
                h / (2 * math.pi * turns * r_coil) if r_coil > 0 else 1.0
            )  # Pitch ratio
            tangent = Vector((tx, ty, tz)).normalized()

            # Construct Rotation Matrix for Ring (Z-Axis -> Tangent)
            # We want the ring normal to point along the tangent
            quat = Vector((0, 0, 1)).rotation_difference(tangent)
            mat_rot = quat.to_matrix().to_4x4()
            mat_trans = Matrix.Translation(center_pos)
            mat_final = mat_trans @ mat_rot

            current_v_coord = t * sv  # V coordinate is progress along length

            ring_verts = []

            for j in range(seg_rad):
                # Radial Angle (U coordinate)
                theta = (j / seg_rad) * 2 * math.pi

                # Circle Point in Local Space (X/Y plane of the wire cross-section)
                lx = math.cos(theta) * r_wire
                ly = math.sin(theta) * r_wire
                local_p = Vector((lx, ly, 0.0))

                world_p = mat_final @ local_p

                # U Coordinate (0-1 around wire)
                u_coord = j / seg_rad

                # Store: (Position, U, V)
                ring_verts.append((world_p, u_coord, current_v_coord))

            rings_data.append(ring_verts)

        # 2a. Determine "Bottom" Seam Index
        # Find index j in the first ring with minimum Z coordinate
        # This aligns the longitudinal cut to the "bottom" of the wire coil
        j_bottom = 0
        if rings_data:
            min_z = rings_data[0][0][0].z  # rings_data[0][j][0] is Vector pos
            for j in range(len(rings_data[0])):
                z = rings_data[0][j][0].z
                if z < min_z:
                    min_z = z
                    j_bottom = j

        # 3. BUILD MESH FROM DATA
        # ----------------------------------------------------------------------
        # Create all BMesh Vertices first
        bm_ring_verts = []  # [ring_index][radial_index]

        for r_idx, r_data in enumerate(rings_data):
            current_ring = []
            for pos, u, v in r_data:
                vert = bm.verts.new(pos)
                current_ring.append(vert)
            bm_ring_verts.append(current_ring)

        bm.verts.ensure_lookup_table()

        # 4. SKIN FACES
        # ----------------------------------------------------------------------
        for r in range(len(bm_ring_verts) - 1):
            ring_curr = bm_ring_verts[r]
            ring_next = bm_ring_verts[r + 1]

            data_curr = rings_data[r]
            data_next = rings_data[r + 1]

            for j in range(seg_rad):
                j_next = (j + 1) % seg_rad

                # Quad Vertices
                v1 = ring_curr[j]
                v2 = ring_next[j]
                v3 = ring_next[j_next]
                v4 = ring_curr[j_next]

                try:
                    f = bm.faces.new((v1, v2, v3, v4))
                    f.material_index = 0  # Wire Surface
                    f.smooth = True

                    # UV Mapping
                    # Retrieve Pre-calculated UV data
                    # (Position, U, V) -> index 1 is U, 2 is V
                    uv1 = (data_curr[j][1], data_curr[j][2])
                    uv2 = (data_next[j][1], data_next[j][2])
                    uv3 = (data_next[j_next][1], data_next[j_next][2])
                    uv4 = (data_curr[j_next][1], data_curr[j_next][2])

                    # Handle U-Wrapping (Seam)
                    if j_next == 0:
                        uv3 = (1.0, uv3[1])
                        uv4 = (1.0, uv4[1])

                    # Apply
                    for l in f.loops:
                        if l.vert == v1:
                            l[uv_layer].uv = (uv1[0] * su, uv1[1])
                        elif l.vert == v2:
                            l[uv_layer].uv = (uv2[0] * su, uv2[1])
                        elif l.vert == v3:
                            l[uv_layer].uv = (uv3[0] * su, uv3[1])
                        elif l.vert == v4:
                            l[uv_layer].uv = (uv4[0] * su, uv4[1])

                    # --- EDGE SLOTS ---
                    # 1. Longitudinal Seam (Bottom)
                    # Edge connecting v1 -> v2 (along the wire length)
                    if j == j_bottom:
                         e_long = bm.edges.get([v1, v2])
                         if e_long:
                             e_long[edge_slots] = 3  # GUIDE
                             e_long.seam = True

                    # 2. Vertical Cuts (Rings) every 12 segments
                    # Edge connecting v1 -> v4 (radial ring)
                    # We cut the ring *before* the current segment if r % 12 == 0
                    if r > 0 and r % 12 == 0:
                        e_ring = bm.edges.get([v1, v4])
                        if e_ring:
                            e_ring[edge_slots] = 3  # GUIDE
                            e_ring.seam = True

                except ValueError:
                    pass  # Face already exists (rare)

        # 5. CAP ENDS
        # ----------------------------------------------------------------------
        def cap_ring(verts, reverse=False, uv_offset_v=0.0):
            try:
                # Create Face
                cap_f = (
                    bm.faces.new(verts)
                    if not reverse
                    else bm.faces.new(reversed(verts))
                )
                cap_f.material_index = 1  # Cut Ends
                cap_f.smooth = False

                # Box Map Cap
                for l in cap_f.loops:
                    # Project flat based on wire radius (local)
                    # Simple Planar mapping relative to cap center is sufficient for ends
                    l[uv_layer].uv = (
                        l.vert.co.x * self.uv_scale,
                        l.vert.co.y * self.uv_scale,
                    )
            except:
                pass

        # Start Cap
        cap_ring(bm_ring_verts[0], reverse=True, uv_offset_v=0.0)
        # End Cap
        cap_ring(bm_ring_verts[-1], reverse=False, uv_offset_v=total_len)

        # 6. MARK SEAMS
        # ----------------------------------------------------------------------
        for e in bm.edges:
            if len(e.link_faces) >= 2:
                # 1. Material Boundaries (Cut Ends vs Wire)
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True
                    e[edge_slots] = 1 # PERIMETER
            
            # 2. Existing Seams (from Cap generation?)
            # No, we rely on implicit U-wrapping seams.
            # But let's enforce the Cut End boundary strictly.

        # 7. FINAL CLEANUP
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # Ensure pivot is at Bottom-Center (0,0,0)
        # The generation logic starts at Z=0 and spirals up, so (0,0,0) is already
        # the center of the base. No translation needed if Pivot Mode is "ORIGIN".
