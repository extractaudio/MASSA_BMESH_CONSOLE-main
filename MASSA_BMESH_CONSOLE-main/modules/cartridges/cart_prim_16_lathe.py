import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_16: Lathed Vessel",
    "id": "prim_16_lathe",
    "icon": "MOD_SCREW",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Geometry is fully closed and thickened internally
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
    },
}


class MASSA_OT_PrimLathe(Massa_OT_Base):
    bl_idname = "massa.gen_prim_16_lathe"
    bl_label = "PRIM_16: Lathe"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    height: FloatProperty(name="Height", default=0.8, min=0.1)
    r_base: FloatProperty(name="Base Radius", default=0.25, min=0.01)
    r_mid: FloatProperty(name="Mid Radius", default=0.45, min=0.01)
    r_rim: FloatProperty(name="Rim Radius", default=0.35, min=0.01)

    mid_pos: FloatProperty(name="Mid Height %", default=0.6, min=0.1, max=0.9)
    thickness: FloatProperty(name="Wall Thickness", default=0.03, min=0.001)

    # --- 2. TOPOLOGY ---
    segments: IntProperty(name="Radial Segs", default=32, min=3)
    smooth_shade: BoolProperty(name="Smooth Shading", default=True)

    # --- 3. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        V2 Standard:
        Slot 0: Main Surface (Continuous UVs).
        Slot 1: Base Anchor (Bottom Faces) -> flagged as 'sock': True for easy instancing.
        """
        return {
            0: {"name": "Ceramic Surface", "uv": "SKIP", "phys": "STONE_MARBLE"},
            1: {"name": "Base Anchor", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Profile Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        col.prop(self, "height")
        col.prop(self, "thickness")

        layout.separator()
        layout.label(text="Radii Profile", icon="CURVE_PATH")
        col = layout.column(align=True)
        col.prop(self, "r_rim", text="Top (Rim)")
        col.prop(self, "r_mid", text="Middle")
        col.prop(self, "mid_pos", slider=True, text="Mid Position")
        col.prop(self, "r_base", text="Bottom")

        layout.separator()
        layout.label(text="Topology", icon="MOD_WIREFRAME")
        layout.prop(self, "segments")
        layout.prop(self, "smooth_shade")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        # 1. SETUP PROFILE POINTS (XZ Plane)
        # ----------------------------------------------------------------------
        h = self.height
        rb, rm, rr = self.r_base, self.r_mid, self.r_rim
        hm = h * self.mid_pos
        t = self.thickness

        # Safety: Ensure thickness doesn't invert the mesh
        min_r = min(rb, rm, rr)
        safe_t = min(t, min_r * 0.9)

        # Profile Nodes: (Radius, Height)
        # Outer Wall (Bottom -> Up)
        nodes = [
            Vector((rb, 0.0, 0.0)),  # 0: Base Outer
            Vector((rm, 0.0, hm)),  # 1: Mid Outer
            Vector((rr, 0.0, h)),  # 2: Rim Outer
            Vector((rr - safe_t, 0.0, h)),  # 3: Rim Inner
            Vector((rm - safe_t, 0.0, hm)),  # 4: Mid Inner
            Vector((rb - safe_t, 0.0, safe_t)),  # 5: Base Inner (Floor)
        ]

        # 2. CALCULATE V-COORDINATES (Arc Length)
        # ----------------------------------------------------------------------
        d_center_to_base = rb

        profile_data = []  # List of (Vector, Accumulated_V)
        current_v = d_center_to_base

        prev_p = nodes[0]
        profile_data.append((nodes[0], current_v))

        for i in range(1, len(nodes)):
            p = nodes[i]
            dist = (p - prev_p).length
            current_v += dist
            profile_data.append((p, current_v))
            prev_p = p

        # Add distance to inner center
        d_base_inner_to_center = rb - safe_t
        total_len = current_v + d_base_inner_to_center

        # UV Scale Factors
        avg_r = (rb + rm + rr) / 3.0
        circumference = 2 * math.pi * avg_r

        s_u = 1.0 if self.fit_uvs else (self.uv_scale * circumference)
        s_v = 1.0 if self.fit_uvs else (self.uv_scale * total_len)

        # 3. SPIN GENERATION (Manual Rings)
        # ----------------------------------------------------------------------
        segs = self.segments
        angle_step = (2 * math.pi) / segs

        ring_verts = []
        uv_layer = bm.loops.layers.uv.verify()

        # A. Create Rings
        for p_vec, p_v_coord in profile_data:
            current_ring = []
            r = p_vec.x
            z = p_vec.z

            for i in range(segs + 1):
                if i == segs:
                    current_ring.append(current_ring[0])
                    continue

                theta = i * angle_step
                x = math.cos(theta) * r
                y = math.sin(theta) * r

                v = bm.verts.new((x, y, z))
                current_ring.append(v)

            ring_verts.append(current_ring)

        bm.verts.ensure_lookup_table()

        # B. Skin Profile Walls (Quads)
        for r_idx in range(len(ring_verts) - 1):
            ring_bot = ring_verts[r_idx]
            ring_top = ring_verts[r_idx + 1]

            v_bot = profile_data[r_idx][1]
            v_top = profile_data[r_idx + 1][1]

            for s in range(segs):
                v1 = ring_bot[s]
                v2 = ring_bot[s + 1]
                v3 = ring_top[s + 1]
                v4 = ring_top[s]

                try:
                    f = bm.faces.new((v1, v2, v3, v4))
                    f.material_index = 0  # Main Ceramic Surface
                    f.smooth = self.smooth_shade

                    u1 = s / segs
                    u2 = (s + 1) / segs

                    for l in f.loops:
                        if l.vert == v1:
                            l[uv_layer].uv = (u1 * s_u, v_bot * s_v)
                        elif l.vert == v2:
                            l[uv_layer].uv = (u2 * s_u, v_bot * s_v)
                        elif l.vert == v3:
                            l[uv_layer].uv = (u2 * s_u, v_top * s_v)
                        elif l.vert == v4:
                            l[uv_layer].uv = (u1 * s_u, v_top * s_v)
                except:
                    pass

        # 4. CAP CENTERS (Triangle Fans)
        # ----------------------------------------------------------------------
        v_center_bot = bm.verts.new((0, 0, 0))  # Bottom Cap Center
        v_center_top = bm.verts.new((0, 0, safe_t))  # Inner Floor Center

        last_ring_idx = len(ring_verts) - 1

        for s in range(segs):
            u1 = s / segs
            u2 = (s + 1) / segs
            u_mid = (u1 + u2) / 2

            # --- Bottom Cap (Outer) ---
            # Normal points DOWN. This is the "Base Anchor".
            v1 = ring_verts[0][s]
            v2 = ring_verts[0][s + 1]

            try:
                f = bm.faces.new((v_center_bot, v2, v1))
                f.material_index = 1  # SLOT 1: Base Anchor
                f.smooth = self.smooth_shade

                v_outer = profile_data[0][1]  # Radius of base

                # UVs: Center is 0, Edge matches wall start
                for l in f.loops:
                    if l.vert == v_center_bot:
                        l[uv_layer].uv = (u_mid * s_u, 0.0)
                    elif l.vert == v2:
                        l[uv_layer].uv = (u2 * s_u, v_outer * s_v)
                    elif l.vert == v1:
                        l[uv_layer].uv = (u1 * s_u, v_outer * s_v)
            except:
                pass

            # --- Top Cap (Inner Floor) ---
            # Normal points UP. This is just the inside surface.
            v1 = ring_verts[last_ring_idx][s]
            v2 = ring_verts[last_ring_idx][s + 1]

            try:
                f = bm.faces.new((v_center_top, v1, v2))
                f.material_index = 0  # Main Ceramic Surface
                f.smooth = self.smooth_shade

                v_ring = profile_data[-1][1]
                v_center = total_len

                for l in f.loops:
                    if l.vert == v_center_top:
                        l[uv_layer].uv = (u_mid * s_u, v_center * s_v)
                    elif l.vert == v1:
                        l[uv_layer].uv = (u1 * s_u, v_ring * s_v)
                    elif l.vert == v2:
                        l[uv_layer].uv = (u2 * s_u, v_ring * s_v)
            except:
                pass

        # 5. MARK SEAMS
        # ----------------------------------------------------------------------
        for e in bm.edges:
            if len(e.link_faces) >= 2:
                # 1. Material Boundaries (Base Anchor vs Surface)
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True

        # 6. FINAL CLEANUP
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
