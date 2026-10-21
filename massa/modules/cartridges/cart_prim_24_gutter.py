import bpy
import bmesh
import math
from bpy.props import FloatProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_24: Gutter (K-Style)",
    "id": "prim_24_gutter",
    "icon": "MOD_FLUID",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
    },
}


class MASSA_OT_PrimGutter(Massa_OT_Base):
    bl_idname = "massa.gen_prim_24_gutter"
    bl_label = "PRIM_24: Gutter"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # AXIS STANDARD: Y-AXIS IS LENGTH
    width: FloatProperty(name="Width (X)", default=0.12, min=0.05)
    height: FloatProperty(name="Height (Z)", default=0.10, min=0.05)
    length: FloatProperty(name="Length (Y)", default=2.0, min=0.1)
    thickness: FloatProperty(name="Thickness", default=0.006, min=0.001)

    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Gutter Metal", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="PROFILE (XZ Plane)", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "thickness")

        layout.separator()
        layout.label(text="EXTRUSION (Y+)", icon="AXIS_SIDE")
        layout.prop(self, "length")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, h = self.width, self.height
        # Clamp thickness so the inner walls can never cross the outer ones.
        t = min(self.thickness, w * 0.4, h * 0.4)
        hw = w / 2.0

        # ----------------------------------------------------------------------
        # 1. PROFILE DEFINITION (XZ Plane) — closed U-channel outline.
        # ----------------------------------------------------------------------
        # Outer boundary up the back, across the bottom, up the front; then the
        # inner boundary back down. Open at the top (the two short top edges are
        # just the wall thickness), so the polygon is simple — no self-intersection.
        pts = [
            (-hw, h),          # 0 back  top    outer
            (-hw, 0.0),        # 1 back  bottom outer
            (hw, 0.0),         # 2 front bottom outer
            (hw, h),           # 3 front top    outer
            (hw - t, h),       # 4 front top    inner
            (hw - t, t),       # 5 front bottom inner
            (-hw + t, t),      # 6 back  bottom inner
            (-hw + t, h),      # 7 back  top    inner
        ]

        # ----------------------------------------------------------------------
        # 2. SETUP LAYERS
        # ----------------------------------------------------------------------
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = (bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
                      or bm.edges.layers.int.new("MASSA_EDGE_SLOTS"))

        # ----------------------------------------------------------------------
        # 3. CREATE BASE GEOMETRY (Clean Extrusion — Beam idiom)
        # ----------------------------------------------------------------------
        base_verts = [bm.verts.new((p[0], 0.0, p[1])) for p in pts]
        bm.verts.ensure_lookup_table()
        try:
            start_cap = bm.faces.new(base_verts)
        except ValueError:
            return

        res_ext = bmesh.ops.extrude_face_region(bm, geom=[start_cap])
        verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=verts_ext, vec=(0.0, self.length, 0.0))

        # ----------------------------------------------------------------------
        # 4. CATEGORIZE FACES + FORCE CAP NORMALS
        # ----------------------------------------------------------------------
        start_caps, end_caps, walls = [], [], []
        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            cy = f.calc_center_median().y
            if abs(cy) < 0.01:
                start_caps.append(f)
            elif abs(cy - self.length) < 0.01:
                end_caps.append(f)
            else:
                walls.append(f)

        for f in start_caps:
            f.normal_update()
            if f.normal.y > 0:
                f.normal_flip()
        for f in end_caps:
            f.normal_update()
            if f.normal.y < 0:
                f.normal_flip()
        bm.normal_update()
        if walls:
            bmesh.ops.recalc_face_normals(bm, faces=walls)

        # ----------------------------------------------------------------------
        # 5. ASSIGN SLOT (single material)
        # ----------------------------------------------------------------------
        for f in bm.faces:
            f.material_index = 0

        # ----------------------------------------------------------------------
        # 6. SEAMS & EDGE SLOTS
        # ----------------------------------------------------------------------
        # Cap perimeters -> seam (auto-detect owns Slot 1 Perimeter). One
        # longitudinal Guide (Slot 3) along the back-bottom-outer corner pts[1].
        for f in start_caps + end_caps:
            for e in f.edges:
                e.seam = True

        seam_x, seam_z = pts[1]
        bm.edges.ensure_lookup_table()
        for e in bm.edges:
            v1, v2 = e.verts
            on1 = abs(v1.co.x - seam_x) < 0.005 and abs(v1.co.z - seam_z) < 0.005
            on2 = abs(v2.co.x - seam_x) < 0.005 and abs(v2.co.z - seam_z) < 0.005
            if on1 and on2:
                e.seam = True
                e[edge_slots] = 3  # Guide

        # ----------------------------------------------------------------------
        # 7. UV MAPPING — walls: arc-length(U) x length(V); caps: box(XZ).
        # ----------------------------------------------------------------------
        perim = sum(
            math.hypot(pts[(i + 1) % len(pts)][0] - pts[i][0],
                       pts[(i + 1) % len(pts)][1] - pts[i][1])
            for i in range(len(pts))
        )
        su_w = (1.0 / perim) if (self.fit_uvs and perim > 0) else self.uv_scale
        sv_w = (1.0 / self.length) if self.fit_uvs else self.uv_scale
        su_c = (1.0 / w) if self.fit_uvs else self.uv_scale
        sv_c = (1.0 / h) if self.fit_uvs else self.uv_scale

        def get_u(x, z):
            cu = 0.0
            for i in range(len(pts)):
                p1 = pts[i]
                if math.hypot(p1[0] - x, p1[1] - z) < 0.002:
                    return cu
                pn = pts[(i + 1) % len(pts)]
                cu += math.hypot(pn[0] - p1[0], pn[1] - p1[1])
            return 0.0

        start_set = set(start_caps)
        end_set = set(end_caps)
        for f in bm.faces:
            if not f.is_valid:
                continue
            if f in start_set or f in end_set:  # CAPS — analytic XZ
                for l in f.loops:
                    u = (l.vert.co.x + hw) * su_c
                    v = l.vert.co.z * sv_c
                    l[uv_layer].uv = (u, v)
            else:  # WALLS — arc-length + wrapping fix on the closing face
                loop_uvs = []
                for l in f.loops:
                    ua = get_u(l.vert.co.x, l.vert.co.z)
                    va = l.vert.co.y
                    loop_uvs.append([l, ua, va])

                us = [item[1] for item in loop_uvs]
                if (max(us) - min(us)) > (perim * 0.5):
                    for item in loop_uvs:
                        if item[1] < (perim * 0.5):
                            item[1] += perim

                for l, u, v in loop_uvs:
                    l[uv_layer].uv = (u * su_w, v * sv_w)
