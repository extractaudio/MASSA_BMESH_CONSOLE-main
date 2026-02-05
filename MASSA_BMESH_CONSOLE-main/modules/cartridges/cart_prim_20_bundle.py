import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, Quaternion
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_20: Cable Bundle",
    "id": "prim_20_bundle",
    "icon": "HAIR",
    "scale_class": "MICRO",
    "flags": {
        "USE_WELD": False,  # CRITICAL: Strands must stay separate
        "ALLOW_SOLIDIFY": False,
        "ALLOW_FUSE": False,
        "PROTECT_NORMALS": True,  # Keep custom normals
        "FIX_DEGENERATE": True,
    },
}


class MASSA_OT_PrimBundle(Massa_OT_Base):
    bl_idname = "massa.gen_prim_20_bundle"
    bl_label = "PRIM_20: Bundle"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    length: FloatProperty(name="Length", default=2.0, min=0.1)
    bundle_radius: FloatProperty(name="Bundle Radius", default=0.1, min=0.01)

    # --- 2. STRANDS ---
    strand_count: IntProperty(name="Strand Count", default=6, min=2, max=50)
    wire_radius: FloatProperty(name="Wire Radius", default=0.03, min=0.001)
    twist: FloatProperty(
        name="Twist Rate", default=1.0, description="Full rotations per length"
    )

    # --- 3. VARIATION ---
    seed: IntProperty(name="Color Seed", default=99)

    # --- 4. TOPOLOGY ---
    seg_radial: IntProperty(name="Wire Segs", default=8, min=3)
    seg_length: IntProperty(name="Length Segs", default=32, min=2)

    # --- 5. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        V2 Standard:
        Slot 0 (Insulation) -> SKIP. We generate local helical UVs.
        Slot 1 (Copper Core) -> BOX. Caps.
        """
        return {
            0: {"name": "Insulation", "uv": "SKIP", "phys": "SYNTH_RUBBER"},
            1: {"name": "Cut Ends", "uv": "BOX", "phys": "METAL_COPPER"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Bundle Profile", icon="FIXED_SIZE")
        layout.prop(self, "length")
        layout.prop(self, "bundle_radius")

        layout.separator()
        layout.label(text="Strand Config", icon="CURVE_PATH")
        layout.prop(self, "strand_count")
        layout.prop(self, "wire_radius")
        layout.prop(self, "twist")
        layout.prop(self, "seed")

        layout.separator()
        layout.label(text="Topology", icon="MOD_WIREFRAME")
        layout.prop(self, "seg_radial")
        layout.prop(self, "seg_length")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        rng = random.Random(self.seed)

        # 1. SETUP LAYERS
        # ----------------------------------------------------------------------
        uv_layer = bm.loops.layers.uv.verify()

        # Color layer for material variation (e.g. multi-colored wires)
        try:
            col_layer = bm.loops.layers.color.verify()
        except:
            col_layer = bm.loops.layers.color.new("Massa_Variation")

        # 2. CALC CONSTANTS
        # ----------------------------------------------------------------------
        L = self.length
        R_bundle = self.bundle_radius
        R_wire = self.wire_radius

        steps = self.seg_length
        seg_rad = self.seg_radial

        total_twist_angle = self.twist * 2 * math.pi
        angle_per_step = total_twist_angle / steps
        z_step = L / steps

        # Arc Length Calculation (Helix Length)
        # Helix circumference = 2 * pi * R_bundle * Twist
        C = 2 * math.pi * R_bundle * self.twist
        helix_len = math.sqrt(C**2 + L**2)

        # UV Scaling
        perim_wire = 2 * math.pi * R_wire
        s_u = 1.0 if self.fit_uvs else (self.uv_scale * perim_wire)
        s_v = 1.0 if self.fit_uvs else (self.uv_scale * helix_len)

        # 3. GENERATION LOOP (Per Strand)
        # ----------------------------------------------------------------------
        base_angle_step = (2 * math.pi) / self.strand_count

        for s_idx in range(self.strand_count):
            # A. Strand Color (Random RGBA)
            # We use grayscale value in Alpha or RGB for variation
            val = rng.uniform(0.2, 1.0)
            strand_color = (val, val, val, 1.0)  # Grayscale ID

            # B. Strand Offset Angle
            start_angle = s_idx * base_angle_step

            # C. Generate Rings
            # We store rings as list of (Vert, U_coord, V_coord)
            rings = []

            for i in range(steps + 1):
                t = i / steps

                # Current Helix Position (Center of wire)
                current_twist = i * angle_per_step
                theta = start_angle + current_twist

                cx = math.cos(theta) * R_bundle
                cy = math.sin(theta) * R_bundle
                cz = (i * z_step) - (L / 2)  # Centered on Z

                center_pos = Vector((cx, cy, cz))

                # Tangent Calculation (For Ring Rotation)
                # Tangent of helix: (-sin, cos, pitch)
                # Pitch = h / (2*pi*r*turns) relative to rotation speed
                # Simplified: Z is constant speed, XY rotates.

                # Tangent Vector:
                # dx/dt = -R * sin(theta) * d_theta
                # dy/dt = R * cos(theta) * d_theta
                # dz/dt = z_step
                # We just need the direction

                tx = -math.sin(theta)
                ty = math.cos(theta)
                # Pitch factor (heuristic for visual banking)
                # If twist is 0, tz is 1, tx/ty are 0.
                if abs(self.twist) < 0.001:
                    tangent = Vector((0, 0, 1))
                else:
                    # Scaling tangent components to match aspect ratio
                    # This approximation is sufficient for wire banking
                    tangent = Vector((tx, ty, L / (C if C > 0 else 1.0))).normalized()

                # Rotation Matrix (Align Z to Tangent)
                rot_quat = Vector((0, 0, 1)).rotation_difference(tangent)
                mat_rot = rot_quat.to_matrix().to_4x4()
                mat_trans = Matrix.Translation(center_pos)
                mat_final = mat_trans @ mat_rot

                current_ring = []

                # Generate Circle Verts
                for r in range(seg_rad):
                    phi = (r / seg_rad) * 2 * math.pi

                    # Local Circle Point
                    lx = math.cos(phi) * R_wire
                    ly = math.sin(phi) * R_wire

                    world_pos = mat_final @ Vector((lx, ly, 0))

                    v = bm.verts.new(world_pos)

                    u_uv = r / seg_rad
                    v_uv = t  # 0 to 1 along length

                    current_ring.append((v, u_uv, v_uv))

                rings.append(current_ring)

            # D. Skin Strands
            bm.verts.ensure_lookup_table()

            for i in range(len(rings) - 1):
                r1 = rings[i]
                r2 = rings[i + 1]

                for j in range(seg_rad):
                    j_next = (j + 1) % seg_rad

                    # Verts
                    v1, u1, v_coord1 = r1[j]
                    v2, u2, v_coord2 = r2[j]
                    v3, u3, v_coord3 = r2[j_next]
                    v4, u4, v_coord4 = r1[j_next]

                    # Seam handling for U
                    if j_next == 0:
                        u3 += 1.0
                        u4 += 1.0

                    f = bm.faces.new((v1, v2, v3, v4))
                    f.material_index = 0
                    f.smooth = True

                    # Assign Data
                    for loop in f.loops:
                        # Color
                        loop[col_layer] = strand_color

                        # UVs
                        if loop.vert == v1:
                            loop[uv_layer].uv = (u1 * s_u, v_coord1 * s_v)
                        elif loop.vert == v2:
                            loop[uv_layer].uv = (u2 * s_u, v_coord2 * s_v)
                        elif loop.vert == v3:
                            loop[uv_layer].uv = (u3 * s_u, v_coord3 * s_v)
                        elif loop.vert == v4:
                            loop[uv_layer].uv = (u4 * s_u, v_coord4 * s_v)

            # E. Cap Ends
            # Start Cap
            verts_start = [d[0] for d in rings[0]]
            f_start = bm.faces.new(reversed(verts_start))  # Flip normal out
            f_start.material_index = 1
            f_start.smooth = False

            # End Cap
            verts_end = [d[0] for d in rings[-1]]
            f_end = bm.faces.new(verts_end)
            f_end.material_index = 1
            f_end.smooth = False

            # Box Map Caps
            for f_cap in [f_start, f_end]:
                for l in f_cap.loops:
                    l[col_layer] = strand_color
                    l[uv_layer].uv = (
                        l.vert.co.x * self.uv_scale,
                        l.vert.co.y * self.uv_scale,
                    )

        # 4. FINAL CLEANUP
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # Add Central Core Wire? (Optional)
        # Usually bundles wrap around a core.
        # If user wants a core, they can instantiate a separate single cylinder.
