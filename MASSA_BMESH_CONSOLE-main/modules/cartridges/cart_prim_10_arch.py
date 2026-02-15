import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_10: Simple Arch",
    "id": "prim_10_arch",
    "icon": "MOD_CURVE",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,  # Bricks are solid
        "USE_WELD": True,
        "ALLOW_FUSE": True,
    },
}


class MASSA_OT_PrimArch(Massa_OT_Base):
    bl_idname = "massa.gen_prim_10_arch"
    bl_label = "PRIM_10: Arch"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    radius: FloatProperty(name="Inner Radius", default=1.5, min=0.1)
    span: FloatProperty(name="Span (Deg)", default=180.0, min=10, max=360)
    count: IntProperty(name="Block Count", default=9, min=3)

    block_depth: FloatProperty(name="Depth (Y)", default=0.3, min=0.01)
    block_height: FloatProperty(name="Height (Z)", default=0.4, min=0.01)
    gap: FloatProperty(name="Mortar Gap", default=0.02, min=0.0)

    # --- 2. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        V2 Standard: UV set to 'SKIP' to preserve custom continuous mapping.
        """
        return {
            0: {"name": "Bricks", "uv": "SKIP", "phys": "STONE_MARBLE"},
            1: {"name": "Keystone", "uv": "SKIP", "phys": "STONE_MARBLE"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "span")
        col.prop(self, "count")

        layout.separator()
        layout.label(text="Block Profile", icon="MESH_CUBE")
        col = layout.column(align=True)
        col.prop(self, "block_depth")
        col.prop(self, "block_height")
        col.prop(self, "gap")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        # 1. ARCH MATH
        r_inner = self.radius
        r_outer = self.radius + self.block_height
        r_mid = r_inner + (self.block_height / 2)

        rad_span = math.radians(self.span)
        angle_per_unit = rad_span / self.count

        # Calculate Arc Lengths for UV accumulation
        # Arc = theta * r
        # We use the MID radius for the primary U-coordinate to minimize distortion
        arc_len_per_block = angle_per_unit * r_mid
        total_arc_len = arc_len_per_block * self.count

        keystone_idx = -1
        if self.count % 2 != 0:
            keystone_idx = int(self.count / 2)

        # Center span around 90 deg (Top)
        start_angle = (math.pi / 2) + (rad_span / 2)

        uv_layer = bm.loops.layers.uv.verify()

        # Scale Factors
        su = 1.0 / total_arc_len if self.fit_uvs else self.uv_scale
        sv_depth = 1.0 / self.block_depth if self.fit_uvs else self.uv_scale
        sv_height = 1.0 / self.block_height if self.fit_uvs else self.uv_scale

        # 2. GENERATION LOOP
        for i in range(self.count):
            # --- A. BLOCK GEOMETRY ---
            # Calculate wedge widths
            w_inner = (r_inner * angle_per_unit) - self.gap
            w_outer = (r_outer * angle_per_unit) - self.gap
            w_inner = max(0.001, w_inner)
            w_outer = max(0.001, w_outer)

            # Block Dimensions
            hw_i = w_inner / 2
            hw_o = w_outer / 2
            hd = self.block_depth / 2
            hh = self.block_height / 2

            # Local Vertices (Trapezoid Prism)
            v_coords = [
                Vector((-hw_i, -hd, -hh)),
                Vector((hw_i, -hd, -hh)),  # Bottom Front
                Vector((hw_i, hd, -hh)),
                Vector((-hw_i, hd, -hh)),  # Bottom Back
                Vector((-hw_o, -hd, hh)),
                Vector((hw_o, -hd, hh)),  # Top Front
                Vector((hw_o, hd, hh)),
                Vector((-hw_o, hd, hh)),  # Top Back
            ]
            new_verts = [bm.verts.new(c) for c in v_coords]

            # Faces
            f_bot = bm.faces.new(
                [new_verts[3], new_verts[2], new_verts[1], new_verts[0]]
            )
            f_top = bm.faces.new(
                [new_verts[4], new_verts[5], new_verts[6], new_verts[7]]
            )
            f_front = bm.faces.new(
                [new_verts[0], new_verts[1], new_verts[5], new_verts[4]]
            )
            f_right = bm.faces.new(
                [new_verts[1], new_verts[2], new_verts[6], new_verts[5]]
            )
            f_back = bm.faces.new(
                [new_verts[2], new_verts[3], new_verts[7], new_verts[6]]
            )
            f_left = bm.faces.new(
                [new_verts[3], new_verts[0], new_verts[4], new_verts[7]]
            )

            all_faces = [f_bot, f_top, f_front, f_right, f_back, f_left]

            # Material
            mat_idx = 1 if i == keystone_idx else 0
            for f in all_faces:
                f.material_index = mat_idx
                f.smooth = False

            # --- B. CONTINUOUS UV MAPPING ---
            # We offset the U coordinate by the arc distance accumulated so far
            u_offset = i * arc_len_per_block

            for f in all_faces:
                n = f.normal

                # 1. TOP/BOTTOM (Curved Surfaces)
                # Map U along Arc, V along Depth
                if abs(n.z) > 0.9:
                    for l in f.loops:
                        # Local X is width (Arc direction), Local Y is Depth
                        local_u = l.vert.co.x

                        # Normalize local width to 0..BlockWidth?
                        # No, keep real world scale. Center is 0.
                        # U = GlobalOffset + LocalPos
                        u = u_offset + (
                            local_u + (w_outer / 2)
                        )  # Shift so block starts at offset
                        v = l.vert.co.y

                        l[uv_layer].uv = (u * su, v * sv_depth)

                # 2. FRONT/BACK (Face Profile)
                # Map U along Arc, V along Radial Height
                elif abs(n.y) > 0.9:
                    for l in f.loops:
                        local_u = l.vert.co.x
                        u = u_offset + (local_u + (w_outer / 2))
                        v = l.vert.co.z  # Height

                        l[uv_layer].uv = (u * su, v * sv_height)

                # 3. SIDES (Caps/Mortar Interface)
                # These are the cuts. Standard Box map.
                else:
                    for l in f.loops:
                        u = l.vert.co.y  # Depth
                        v = l.vert.co.z  # Height
                        l[uv_layer].uv = (u * sv_depth, v * sv_height)

            # --- C. TRANSFORM ---
            theta = start_angle - (i * angle_per_unit) - (angle_per_unit / 2)
            px = r_mid * math.cos(theta)
            pz = r_mid * math.sin(theta)
            rot_y = theta - (math.pi / 2)

            mat_trans = Matrix.Translation((px, 0, pz))
            mat_rot = Matrix.Rotation(-rot_y, 4, "Y")

            bmesh.ops.transform(bm, matrix=mat_trans @ mat_rot, verts=new_verts)

        # 3. MARK SEAMS
        # ----------------------------------------------------------------------
        for e in bm.edges:
            if len(e.link_faces) >= 2:
                # 1. Material Boundaries
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True
                    continue

        # 4. GLOBAL CLEANUP
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
