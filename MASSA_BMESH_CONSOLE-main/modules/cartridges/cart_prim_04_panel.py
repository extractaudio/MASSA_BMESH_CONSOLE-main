import bpy
import bmesh
import random
import math
from mathutils import Vector
from bpy.props import FloatProperty, IntProperty, FloatVectorProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_04: Grid Panel",
    "id": "prim_04_panel",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
    },
}


class MASSA_OT_PrimPanel(Massa_OT_Base):
    bl_idname = "massa.gen_prim_04_panel"
    bl_label = "PRIM_04: Panel"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    size: FloatVectorProperty(name="Size", default=(2.0, 2.0, 0.1), min=0.01)

    # --- 2. PATTERN ---
    cuts_x: IntProperty(name="Grid X", default=4, min=1)
    cuts_y: IntProperty(name="Grid Y", default=4, min=1)
    density: FloatProperty(name="Density", default=1.0, min=0.0, max=1.0)
    seed: IntProperty(name="Seed", default=101)
    gap: FloatProperty(name="Frame Gap", default=0.015, min=0.0, unit="LENGTH")

    # --- 3. PROFILE ---
    inset_amt: FloatProperty(name="Inset Margin", default=0.05, min=0.001)
    depth: FloatProperty(name="Recess Depth", default=0.05)

    # --- 4. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self) -> dict:
        return {
            0: {
                "name": "Frame Anchor",
                "uv": "BOX",
                "phys": "METAL_STEEL",
                "sock": True,
            },
            1: {"name": "Trim", "uv": "BOX", "phys": "GENERIC"},
            2: {"name": "Backing", "uv": "BOX", "phys": "GENERIC"},
            3: {"name": "Frame Surface", "uv": "BOX", "phys": "METAL_STEEL"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "size", index=0, text="X")
        row.prop(self, "size", index=1, text="Y")
        row.prop(self, "size", index=2, text="Z")

        layout.separator()
        layout.label(text="Grid Pattern", icon="GRID")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "cuts_x", text="X")
        row.prop(self, "cuts_y", text="Y")
        col.prop(self, "gap")
        col.prop(self, "density")
        col.prop(self, "seed")

        layout.separator()
        layout.label(text="Profile", icon="MOD_BEVEL")
        col = layout.column(align=True)
        col.prop(self, "inset_amt")
        col.prop(self, "depth", text="Depth (+In/-Out)")

        layout.separator()
        layout.label(text="UV Protocols", icon="GROUP_UVS")
        row = layout.row(align=True)
        row.prop(self, "uv_scale")
        row.prop(self, "fit_uvs")

    def build_shape(self, bm: bmesh.types.BMesh) -> None:
        rng = random.Random(self.seed)
        sx, sy, sz = self.size

        # ----------------------------------------------------------------------
        # 1. GRID LOGIC
        # ----------------------------------------------------------------------
        total_w = sx * 2
        total_l = sy * 2

        total_gap_x = self.gap * (self.cuts_x - 1)
        total_gap_y = self.gap * (self.cuts_y - 1)

        cell_w = (total_w - total_gap_x) / self.cuts_x
        cell_l = (total_l - total_gap_y) / self.cuts_y

        start_x = -(total_w / 2) + (cell_w / 2)
        start_y = -(total_l / 2) + (cell_l / 2)

        # ----------------------------------------------------------------------
        # 2. GENERATION LOOP
        # ----------------------------------------------------------------------
        valid_top_faces = []

        for ix in range(self.cuts_x):
            for iy in range(self.cuts_y):
                cx = start_x + (ix * (cell_w + self.gap))
                cy = start_y + (iy * (cell_l + self.gap))
                center = Vector((cx, cy, 0))

                # Create Box
                top_face = self.create_box_cell(bm, center, cell_w, cell_l, sz)
                valid_top_faces.append(top_face)

        # ----------------------------------------------------------------------
        # 3. CREATE FRAME ANCHOR
        # ----------------------------------------------------------------------
        anchor_size = min(sx, sy) * 0.05
        res_anchor = bmesh.ops.create_grid(
            bm, x_segments=1, y_segments=1, size=anchor_size
        )
        anchor_verts = res_anchor["verts"]
        bmesh.ops.translate(bm, verts=anchor_verts, vec=(0, 0, -0.02))

        for v in anchor_verts:
            if v.link_faces:
                v.link_faces[0].material_index = 0
                break

        # ----------------------------------------------------------------------
        # 4. SOCKET LOGIC
        # ----------------------------------------------------------------------
        targets = []
        for f in valid_top_faces:
            if rng.random() < self.density:
                targets.append(f)

        if targets:
            # A. Inset
            safe_inset = min(self.inset_amt, cell_w / 2.1, cell_l / 2.1)
            res_inset = bmesh.ops.inset_individual(
                bm, faces=targets, thickness=safe_inset, use_even_offset=True
            )
            faces_inner = res_inset["faces"]

            # B. Extrude Recess
            if abs(self.depth) > 0.0001:
                res_recess = bmesh.ops.extrude_face_region(bm, geom=faces_inner)

                verts_recess = [
                    v for v in res_recess["geom"] if isinstance(v, bmesh.types.BMVert)
                ]
                faces_walls = [
                    f for f in res_recess["geom"] if isinstance(f, bmesh.types.BMFace)
                ]

                # Move Down
                bmesh.ops.translate(bm, verts=verts_recess, vec=(0, 0, -self.depth))

                # Assign Trim Slot (1) to Walls
                for f in faces_walls:
                    f.material_index = 1

                # The 'faces_inner' list still references the floor faces (caps)
                for f in faces_inner:
                    f.material_index = 1

        # ----------------------------------------------------------------------
        # 5. FINAL CLEANUP & NORMAL ENFORCEMENT
        # ----------------------------------------------------------------------
        bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges[:] )

        # 1. Global Recalc (Fixes walls/boxes)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 2. Force Update to read accurate normals
        bm.normal_update()

        # 3. THE FINAL OVERRIDE
        for f in bm.faces:
            if f.material_index == 1:
                # Check for horizontal alignment (Is it a floor?)
                # We use > 0.5 to be safe, filtering out vertical walls
                if abs(f.normal.z) > 0.5:
                    # STRICT CHECK: If it points down, FLIP IT UP.
                    if f.normal.z < 0:
                        f.normal_flip()

        # ----------------------------------------------------------------------
        # 6. MARK SEAMS
        # ----------------------------------------------------------------------
        for e in bm.edges:
            # 1. Material Boundaries
            if len(e.link_faces) >= 2:
                mats = {f.material_index for f in e.link_faces}
                if len(mats) > 1:
                    e.seam = True
                    continue

                # 2. Sharp Edges (Box Map Seams)
                # If same material, check angle
                if all(m >= 0 for m in mats):
                    n1 = e.link_faces[0].normal
                    n2 = e.link_faces[1].normal
                    if n1.dot(n2) < 0.5:  # 60 degrees
                        e.seam = True

        # ----------------------------------------------------------------------
        # 7. UV MAPPING
        # ----------------------------------------------------------------------
        uv_layer = bm.loops.layers.uv.verify()
        s = 1.0 if self.fit_uvs else self.uv_scale

        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            # Standard Box Map Logic
            loop_uvs = []
            if nz > nx and nz > ny:
                # Top/Bottom -> XY
                for l in f.loops:
                    loop_uvs.append([l, l.vert.co.x, l.vert.co.y])
            elif nx > ny and nx > nz:
                # Side X -> YZ
                for l in f.loops:
                    loop_uvs.append([l, l.vert.co.y, l.vert.co.z])
            else:
                # Side Y -> XZ
                for l in f.loops:
                    loop_uvs.append([l, l.vert.co.x, l.vert.co.z])

            # Apply Scaled UVs
            for l, u, v in loop_uvs:
                l[uv_layer].uv = (u * s, v * s)

    def create_box_cell(self, bm, center, w, l, h):
        """
        Creates a separate box for each grid cell.
        """
        hw, hl = w / 2, l / 2
        coords = [
            (-hw, -hl, 0),
            (hw, -hl, 0),
            (hw, hl, 0),
            (-hw, hl, 0),  # Top Ring
            (-hw, -hl, -h),
            (hw, -hl, -h),
            (hw, hl, -h),
            (-hw, hl, -h),  # Bottom Ring
        ]
        verts = [bm.verts.new(Vector(c) + center) for c in coords]

        # Faces
        f_top = bm.faces.new([verts[3], verts[2], verts[1], verts[0]])
        f_top.material_index = 3  # Frame Surface

        f_bot = bm.faces.new([verts[4], verts[5], verts[6], verts[7]])
        f_bot.material_index = 2  # Backing

        # Sides
        side_indices = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        for idxs in side_indices:
            f = bm.faces.new([verts[i] for i in idxs])
            f.material_index = 2  # Backing

        return f_top
