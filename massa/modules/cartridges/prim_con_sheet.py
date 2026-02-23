"""
Filename: modules/cartridges/prim_con_sheet.py
Content: Wave Function Sheet Generator (Corrugated, Trapezoidal, Drywall)
Status: PATCHED (KeyError Fix)
"""

import bpy
import bmesh
import math
from bpy.props import FloatProperty, EnumProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector

CARTRIDGE_META = {
    "name": "Con: Sheet/Cladding",
    "id": "prim_con_sheet",
    "icon": "MOD_WAVE",
    "scale_class": "MACRO",  #
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": True,
        "FIX_DEGENERATE": False,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_prim_con_sheet(Massa_OT_Base):
    """
    Wave Function Surface Generator.
    Fork of PRIM_03 (Sheet) Logic with PRIM_01 (Extrusion) Mechanics.
    """

    bl_idname = "massa.gen_prim_con_sheet"
    bl_label = "Construction Sheet"
    bl_description = "Corrugated, Trapezoidal, or Flat Cladding"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- DIMS ---
    width: FloatProperty(name="Width (X)", default=2.0, min=0.1, unit="LENGTH")
    length: FloatProperty(name="Length (Y)", default=2.0, min=0.1, unit="LENGTH")

    # --- PROFILE ---
    profile_type: EnumProperty(
        name="Profile",
        items=[
            ("SINE", "Sine Wave", "Corrugated Iron"),
            ("TRAPEZOID", "Trapezoidal", "Box Profile Roofing"),
            ("ZIGZAG", "Zig-Zag", "Sharp Creases"),
            ("FLAT", "Flat", "Drywall / Plywood"),
        ],
        default="SINE",
    )

    amplitude: FloatProperty(name="Wave Height", default=0.05, min=0.0, unit="LENGTH")
    frequency: FloatProperty(name="Wave Freq", default=10.0, min=0.1)

    thickness: FloatProperty(name="Thickness", default=0.005, min=0.001, unit="LENGTH")

    # --- RESOLUTION ---
    res_x: IntProperty(name="Resolution X", default=64, min=2)
    res_y: IntProperty(name="Resolution Y", default=2, min=1)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Dimensions", icon="MOD_BUILD")
        box.prop(self, "width")
        box.prop(self, "length")

        box = layout.box()
        box.label(text="Wave Profile", icon="FORCE_HARMONIC")
        box.prop(self, "profile_type")
        if self.profile_type != "FLAT":
            col = box.column(align=True)
            col.prop(self, "amplitude")
            col.prop(self, "frequency")
            col.prop(self, "res_x")

        box.prop(self, "thickness")

    def get_slot_meta(self):
        # Index 0 is King (Main Body)
        return {
            0: {"name": "Cladding_Ext", "uv": "TUBE_Y", "phys": "METAL_ALUMINUM"},
            1: {"name": "Cladding_Int", "uv": "TUBE_Y", "phys": "GENERIC"},
            2: {"name": "Rim", "uv": "BOX", "phys": "METAL_RUST"},
        }

    def build_shape(self, bm):
        # 1. SETUP
        w, l = self.width, self.length
        amp = self.amplitude
        freq = self.frequency

        # Edge Role Protocol
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 2. GENERATE PROFILE POINTS (X, Z)
        pts = []
        rx = self.res_x if self.profile_type != "FLAT" else 2

        # Arc Length Accumulator for UVs (Class A Logic)
        uv_x_list = []
        current_arc_len = 0.0

        for i in range(rx + 1):
            t = i / rx
            x = (t - 0.5) * w

            # Wave Function Math
            z = 0.0
            is_crease = False

            if self.profile_type == "SINE":
                z = math.sin(t * freq * math.pi * 2) * amp

            elif self.profile_type == "ZIGZAG":
                cycle = t * freq * 2
                local_t = cycle % 2.0
                val = (local_t - 1.0) if local_t > 1.0 else (1.0 - local_t)
                z = (val - 0.5) * 2 * amp
                # Detect peaks for sharpness
                if abs(abs(z) - amp) < 0.001:
                    is_crease = True

            elif self.profile_type == "TRAPEZOID":
                cycle = (t * freq) % 1.0
                val = 0.0
                if cycle < 0.2:
                    val = -1.0
                elif cycle < 0.3:
                    val = -1.0 + ((cycle - 0.2) * 10.0)  # Rise
                elif cycle < 0.7:
                    val = 1.0
                elif cycle < 0.8:
                    val = 1.0 - ((cycle - 0.7) * 10.0)  # Fall
                else:
                    val = -1.0

                z = val * amp
                # Detect corners
                if (
                    0.19 < cycle < 0.21
                    or 0.29 < cycle < 0.31
                    or 0.69 < cycle < 0.71
                    or 0.79 < cycle < 0.81
                ):
                    is_crease = True

            pts.append((Vector((x, 0, z)), is_crease))

            # UV Calc: Accumulate distance
            if i > 0:
                dist = (Vector((x, 0, z)) - pts[i - 1][0]).length
                current_arc_len += dist
            uv_x_list.append(current_arc_len)

        # Normalize UVs
        total_len = max(0.001, current_arc_len)
        uv_factors = [u / total_len for u in uv_x_list]

        # 3. EXTRUDE LENGTH (Y)
        verts_start = [bm.verts.new(p[0]) for p in pts]

        # OPERATOR SAFETY: Extrude Verts
        ret = bmesh.ops.extrude_vert_indiv(bm, verts=verts_start)
        # FIX: Use .get() to prevent KeyError if 'geom' is missing
        verts_end = [
            v for v in ret.get("geom", []) if isinstance(v, bmesh.types.BMVert)
        ]

        # Verify extrusion success before skinning
        if len(verts_end) != len(verts_start):
            print(
                f"MASSA_DEBUG: Extrusion mismatch. Start: {len(verts_start)}, End: {len(verts_end)}"
            )
            return  # Abort to prevent crash

        bmesh.ops.translate(bm, verts=verts_end, vec=(0, l, 0))

        faces_top = []

        # Manual Skinning (Quads)
        for i in range(len(verts_start) - 1):
            v1 = verts_start[i]
            v2 = verts_start[i + 1]
            v3 = verts_end[i + 1]
            v4 = verts_end[i]

            try:
                f = bm.faces.new((v1, v2, v3, v4))
            except ValueError:
                continue  # Skip if face already exists or is invalid

            f.material_index = 0
            faces_top.append(f)

            # Tag Crease Edges (Longitudinal)
            if pts[i][1]:
                # Locate Longitudinal Edge v1-v4 and v2-v3
                for e in v1.link_edges:
                    if e.other_vert(v1) == v4:
                        e[edge_slots] = 2  # CONTOUR

            # Manual UVs (Autonomy Protocol)
            uv_layer = bm.loops.layers.uv.verify()
            u1, u2 = uv_factors[i], uv_factors[i + 1]
            for loop in f.loops:
                v = loop.vert
                # Map U to profile length, V to physical length
                loop_u = u1 if (v == v1 or v == v4) else u2
                loop_v = 0.0 if (v == v1 or v == v2) else (l / w)
                loop[uv_layer].uv = (loop_u * (total_len / w), loop_v)

        # 4. SOLIDIFY
        # FIX: Ensure we have faces to solidify
        if self.thickness > 0.0001 and faces_top:
            bmesh.ops.recalc_face_normals(bm, faces=faces_top)

            # OPERATOR SAFETY: Solidify
            ret = bmesh.ops.solidify(bm, geom=faces_top, thickness=self.thickness)

            # FIX: Use .get("geom", []) to prevent KeyError: 'geom'
            new_geom = ret.get("geom", [])

            for f in new_geom:
                if isinstance(f, bmesh.types.BMFace):
                    if f not in faces_top:
                        # Detect Rim faces based on Normal Z
                        if abs(f.normal.z) < 0.2:
                            f.material_index = 2  # Rim Slot

        # 5. SEGMENTATION & CLEANUP
        # Optimization: Only bisect if necessary
        if self.res_y > 1:
            step = l / self.res_y
            for i in range(1, self.res_y):
                # Optimization: In a real scenario, we might limit geom to just the sheet
                # But for robustness, we slice everything.
                bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    plane_co=(0, i * step, 0),
                    plane_no=(0, 1, 0),
                )

        # Final Edge Marking (Perimeter Detection)
        for e in bm.edges:
            if e.is_boundary:
                e[edge_slots] = 1  # PERIMETER
            elif e[edge_slots] == 0 and e.calc_face_angle() > 0.5:
                e[edge_slots] = 2  # SHARP/CONTOUR

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
