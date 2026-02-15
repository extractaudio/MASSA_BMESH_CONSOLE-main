import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_08: Hex Bolt",
    "id": "prim_08_bolt",
    "icon": "BOLT",
    "scale_class": "MICRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Solid volume
        "USE_WELD": True,  # Merge parts
        "FIX_DEGENERATE": True,  # Micro clean
        "ALLOW_CHAMFER": True,  # Essential for Hex edges
        "LOCK_PIVOT": True,  # Pivot at Neck (Z=0)
    },
}


class MASSA_OT_PrimBolt(Massa_OT_Base):
    bl_idname = "massa.gen_prim_08_bolt"
    bl_label = "PRIM_08: Bolt"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    head_radius: FloatProperty(name="Head Radius", default=0.08, min=0.01)
    head_height: FloatProperty(name="Head Height", default=0.05, min=0.005)

    shank_radius: FloatProperty(name="Shank Radius", default=0.04, min=0.005)
    shank_length: FloatProperty(name="Shank Length", default=0.15, min=0.0)

    # --- 2. WASHER ---
    use_washer: BoolProperty(name="Add Washer", default=True)
    washer_thick: FloatProperty(name="Washer Thick", default=0.01, min=0.001)

    # --- 3. TOPOLOGY ---
    segments_radial: IntProperty(name="Shank Segs", default=12, min=6, max=32)

    # --- 4. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        # UPDATED: All slots use BOX mapping for stability on Micro assets
        return {
            0: {"name": "Hex Head", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Shank/Thread", "uv": "BOX", "phys": "METAL_IRON"},
            2: {"name": "Washer", "uv": "BOX", "phys": "METAL_ALUMINUM"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        col.prop(self, "head_radius")
        col.prop(self, "head_height")
        col.separator()
        col.prop(self, "shank_radius")
        col.prop(self, "shank_length")

        layout.separator()
        layout.label(text="Accessories", icon="MOD_SCREW")
        row = layout.row(align=True)
        row.prop(self, "use_washer", toggle=True)
        if self.use_washer:
            row.prop(self, "washer_thick", text="Thick")

        layout.separator()
        layout.label(text="Topology", icon="MOD_WIREFRAME")
        layout.prop(self, "segments_radial")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        # ----------------------------------------------------------------------
        # 1. BUILD SHANK (Slot 1) - Extends Down (-Z)
        # ----------------------------------------------------------------------
        if self.shank_length > 0.001:
            mat_shank = Matrix.Translation((0, 0, -self.shank_length / 2))

            res_shank = bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                cap_tris=True,
                segments=self.segments_radial,
                radius1=self.shank_radius,
                radius2=self.shank_radius,
                depth=self.shank_length,
                matrix=mat_shank,
            )

            # Identify Faces via Verts (Safe Mode)
            new_verts = res_shank["verts"]
            shank_faces = list({f for v in new_verts for f in v.link_faces})

            faces_to_nuke = []
            for f in shank_faces:
                f.material_index = 1
                f.smooth = True
                # Delete Top Cap (Normal Up, Center at Z=0)
                if f.normal.z > 0.9 and abs(f.calc_center_median().z) < 0.001:
                    faces_to_nuke.append(f)

            bmesh.ops.delete(bm, geom=faces_to_nuke, context="FACES")

        # ----------------------------------------------------------------------
        # 2. BUILD WASHER (Slot 2) - Sits at Z=0
        # ----------------------------------------------------------------------
        z_head_start = 0.0

        if self.use_washer:
            w_rad = self.head_radius * 1.3
            w_th = self.washer_thick
            mat_wash = Matrix.Translation((0, 0, w_th / 2))

            res_washer = bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                cap_tris=False,
                segments=self.segments_radial,
                radius1=w_rad,
                radius2=w_rad,
                depth=w_th,
                matrix=mat_wash,
            )

            wash_verts = res_washer["verts"]
            washer_faces = list({f for v in wash_verts for f in v.link_faces})

            for f in washer_faces:
                f.material_index = 2
                f.smooth = True

            z_head_start = w_th

        # ----------------------------------------------------------------------
        # 3. BUILD HEX HEAD (Slot 0) - Sits on top
        # ----------------------------------------------------------------------
        h_rad = self.head_radius
        h_h = self.head_height

        mat_head = Matrix.Translation((0, 0, z_head_start + (h_h / 2)))

        res_head = bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=6,  # HEXAGON FIXED
            radius1=h_rad,
            radius2=h_rad,
            depth=h_h,
            matrix=mat_head,
        )

        head_verts = res_head["verts"]
        head_faces = list({f for v in head_verts for f in v.link_faces})

        for f in head_faces:
            f.material_index = 0
            f.smooth = False  # Hard edges for Hex

        # ----------------------------------------------------------------------
        # 4. CLEANUP & UVs
        # ----------------------------------------------------------------------
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # ----------------------------------------------------------------------
        # 5. MARK SEAMS
        # ----------------------------------------------------------------------
        for e in bm.edges:
            # 1. Material Boundaries
            if len(e.link_faces) >= 2:
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True
                    continue
                
                # 2. Sharp Edges (Hex Head corners)
                if all(m >= 0 for m in mats):
                    n1 = e.link_faces[0].normal
                    n2 = e.link_faces[1].normal
                    if n1.dot(n2) < 0.5:  # 60 degrees
                        e.seam = True

        uv_layer = bm.loops.layers.uv.verify()
        s = self.uv_scale

        # UNIFIED BOX MAPPING (Stable for Micro Assets)
        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            for l in f.loops:
                co = l.vert.co
                # Tri-Planar Projection
                if nz > nx and nz > ny:
                    u, v = co.x, co.y
                elif nx > ny and nx > nz:
                    u, v = co.y, co.z
                else:
                    u, v = co.x, co.z

                if not self.fit_uvs:
                    u *= s
                    v *= s

                l[uv_layer].uv = (u, v)
