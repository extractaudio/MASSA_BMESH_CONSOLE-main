import bpy
import bmesh
import random
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, FloatVectorProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_15: Offset Scale",
    "id": "prim_15_scale",
    "icon": "MOD_GRID",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": False,  # Tiles must remain separate objects
        "ALLOW_SOLIDIFY": False,  # Tiles are solid cubes
        "ALLOW_FUSE": False,  # Do not boolean union tiles
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": True,
    },
}


class MASSA_OT_PrimScale(Massa_OT_Base):
    bl_idname = "massa.gen_prim_15_scale"
    bl_label = "PRIM_15: Scales"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    tile_size: FloatVectorProperty(
        name="Tile Size", default=(0.2, 0.3, 0.02), min=0.001
    )

    # --- 2. ARRAY ---
    rows: IntProperty(name="Rows (Y)", default=10, min=1)
    cols: IntProperty(name="Cols (X)", default=10, min=1)
    overlap_y: FloatProperty(name="Overlap Y %", default=0.2, min=0.0, max=0.9)
    gap_x: FloatProperty(name="Gap X", default=0.005, min=0.0)
    stagger: BoolProperty(name="Stagger Rows", default=True)

    # --- 3. VARIATION ---
    tilt: FloatProperty(name="Tilt Angle", default=5.0, min=-90.0, max=90.0)
    jitter_rot: FloatProperty(name="Jitter Rot", default=1.0, min=0.0)
    jitter_pos: FloatProperty(name="Jitter Pos", default=0.005, min=0.0)
    seed: IntProperty(name="Seed", default=101)

    # --- 4. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        """
        V2 Standard:
        Slot 0 (Shingle) -> SKIP.
        We apply local box mapping so textures follow the tile's rotation/tilt.
        """
        return {
            0: {"name": "Shingles", "uv": "SKIP", "phys": "WOOD_PINE"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Tile Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        # Horizontal XYZ
        row = col.row(align=True)
        row.prop(self, "tile_size", index=0, text="X")
        row.prop(self, "tile_size", index=1, text="Y")
        row.prop(self, "tile_size", index=2, text="Z")

        layout.separator()
        layout.label(text="Array Pattern", icon="MOD_ARRAY")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "cols")
        row.prop(self, "rows")
        col.prop(self, "overlap_y", slider=True)
        col.prop(self, "gap_x")
        col.prop(self, "stagger")

        layout.separator()
        layout.label(text="Chaos & Variation", icon="RNDCURVE")
        col = layout.column(align=True)
        col.prop(self, "tilt")
        col.prop(self, "jitter_rot")
        col.prop(self, "jitter_pos")
        col.prop(self, "seed")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh):
        rng = random.Random(self.seed)

        # 1. SETUP
        w, l, h = self.tile_size

        # Calculate Steps
        step_x = w + self.gap_x
        step_y = l * (1.0 - self.overlap_y)

        # Center the array
        total_w = self.cols * step_x
        if self.stagger:
            total_w += step_x * 0.5

        total_l = (self.rows * step_y) + (l * self.overlap_y)

        start_x = -total_w / 2
        start_y = -total_l / 2

        uv_layer = bm.loops.layers.uv.verify()

        # Noise Mask Layer
        noise_layer = bm.verts.layers.float.get("massa_noise_mask")
        if not noise_layer:
            noise_layer = bm.verts.layers.float.new("massa_noise_mask")

        # 2. GENERATION LOOP
        for r in range(self.rows):
            row_off_x = 0.0
            if self.stagger and (r % 2 != 0):
                row_off_x = step_x * 0.5

            z_base = r * h * 0.2

            for c in range(self.cols):
                # A. CREATE SINGLE TILE AT ORIGIN
                res = bmesh.ops.create_cube(bm, size=1.0)
                verts = res["verts"]

                # Derive faces from verts (FIX FOR KEYERROR)
                new_faces = list({f for v in verts for f in v.link_faces})

                # Apply Scale
                bmesh.ops.scale(bm, vec=(w, l, h), verts=verts)

                # B. APPLY LOCAL UVs (Before Rotation)
                for f in new_faces:
                    f.material_index = 0
                    f.smooth = False

                    n = f.normal
                    nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

                    for loop in f.loops:
                        co = loop.vert.co
                        u, v = 0.0, 0.0

                        # Box Projection
                        if nz > nx and nz > ny:  # Top/Bottom
                            u, v = co.x, co.y
                            if self.fit_uvs:
                                u = (u + w / 2) / w
                                v = (v + l / 2) / l
                        elif nx > ny and nx > nz:  # Side X
                            u, v = co.y, co.z
                            if self.fit_uvs:
                                u = (u + l / 2) / l
                                v = (v + h / 2) / h
                        else:  # Side Y (Front/Back)
                            u, v = co.x, co.z
                            if self.fit_uvs:
                                u = (u + w / 2) / w
                                v = (v + h / 2) / h

                        if not self.fit_uvs:
                            u *= self.uv_scale
                            v *= self.uv_scale

                        loop[uv_layer].uv = (u, v)

                # C. APPLY TRANSFORMATIONS
                # -------------------------------------
                # 1. Random Jitter (Rotation)
                j_rot_z = 0.0
                if self.jitter_rot > 0:
                    j_rot_z = math.radians(
                        rng.uniform(-self.jitter_rot, self.jitter_rot)
                    )

                # 2. Base Tilt (X Axis)
                base_tilt = math.radians(self.tilt)
                j_tilt = 0.0
                if self.jitter_rot > 0:
                    j_tilt = math.radians(
                        rng.uniform(-self.jitter_rot, self.jitter_rot) * 0.5
                    )

                mat_rot = Matrix.Rotation(base_tilt + j_tilt, 4, "X") @ Matrix.Rotation(
                    j_rot_z, 4, "Z"
                )

                # 3. Position
                px = start_x + (c * step_x) + row_off_x + (w / 2)
                py = start_y + (r * step_y) + (l / 2)
                pz = z_base + (h / 2)

                if self.jitter_pos > 0:
                    px += rng.uniform(-self.jitter_pos, self.jitter_pos)
                    py += rng.uniform(-self.jitter_pos, self.jitter_pos)
                    pz += rng.uniform(-self.jitter_pos * 0.1, self.jitter_pos * 0.1)

                mat_trans = Matrix.Translation((px, py, pz))

                bmesh.ops.transform(bm, matrix=mat_trans @ mat_rot, verts=verts)

                # D. WRITE NOISE MASK
                tile_noise_seed = rng.uniform(0.2, 1.0)
                for v in verts:
                    v[noise_layer] = tile_noise_seed

        # 3. MARK SEAMS
        # ----------------------------------------------------------------------
        for e in bm.edges:
            if len(e.link_faces) >= 2:
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True
                    continue
                
                # Sharp Edges (Tiles are cubes, so 90 deg is sharp)
                n1 = e.link_faces[0].normal
                n2 = e.link_faces[1].normal
                if n1.dot(n2) < 0.5:
                    e.seam = True

        # 4. FINAL CLEANUP
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
