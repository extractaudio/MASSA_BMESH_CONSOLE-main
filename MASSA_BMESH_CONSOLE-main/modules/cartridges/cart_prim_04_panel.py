import bpy
import bmesh
import random
import math
from mathutils import Vector
from bpy.props import FloatProperty, IntProperty, FloatVectorProperty, BoolProperty
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
    # --- 2. PATTERN ---
    cuts_x: IntProperty(name="Grid X", default=4, min=1)
    cuts_y: IntProperty(name="Grid Y", default=4, min=1)
    gap: FloatProperty(name="Frame Gap", default=0.015, min=0.0, unit="LENGTH")

    # --- 3. PROFILE ---
    inset_amt: FloatProperty(name="Inset Margin", default=0.05, min=0.001)
    inset_height: FloatProperty(name="Inset Height", default=0.05, description="Height offset for the inner tile")

    # --- 4. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self) -> dict:
        return {
            0: {
                "name": "Edge Banding",
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

        layout.separator()
        layout.label(text="Profile", icon="MOD_BEVEL")
        col = layout.column(align=True)
        col.prop(self, "inset_amt")
        col.prop(self, "inset_height", text="Tile Offset (+/-)")



    def build_shape(self, bm: bmesh.types.BMesh) -> None:
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
        # 3. INSET & EXTRUDE LOGIC
        # ----------------------------------------------------------------------
        if valid_top_faces:
            # A. Inset
            # Safety: Ensure we don't inset more than the face allows
            safe_limit = min(cell_w / 2.01, cell_l / 2.01)
            safe_inset = min(self.inset_amt, safe_limit)
            
            # Clamp to minimum to avoid zero-area faces/crashes
            if safe_inset < 0.0001:
                safe_inset = 0.0001

            # Perform Inset (Individual is safer for disjoint grid faces)
            res_inset = bmesh.ops.inset_individual(
                bm, faces=valid_top_faces, thickness=safe_inset, use_even_offset=True
            )
            
            # In inset_individual, the original faces become the "inner" faces.
            # We don't need to hunt for them in a dict if we track the original objects,
            # BUT bmesh operators often replace/invalidating Python objects.
            # Use the return dict.
            faces_inner = res_inset["faces"]

            # B. Extrude / Move Inner Tile
            if abs(self.inset_height) > 0.0001:
                res_ext = bmesh.ops.extrude_face_region(bm, geom=faces_inner)
                
                verts_ext = [v for v in res_ext["geom"] if isinstance(v, bmesh.types.BMVert)]
                faces_ext_top = [f for f in res_ext["geom"] if isinstance(f, bmesh.types.BMFace)]
                
                # Move Extruded Face
                bmesh.ops.translate(bm, verts=verts_ext, vec=(0, 0, self.inset_height))

                # Assign Materials
                # 1. Top Face -> Trim (Slot 1)
                for f in faces_ext_top:
                    f.material_index = 1 
                
                # 2. Side Walls -> Edge Banding (Slot 0) or Frame (Slot 3)?
                # The user calls this "inset tile", implying the side wall belongs to the tile.
                # Let's check faces attached to verts_ext that are NOT the top face.
                for f in faces_ext_top:
                    for loop in f.loops:
                        # The edge of the top face connects to a side face
                        # The loop.edge.link_faces has usually 2 faces: Top and Side.
                        for linked_face in loop.edge.link_faces:
                            if linked_face != f:
                                linked_face.material_index = 0 # Edge Banding style for the "cut"
                                
            else:
                # No Extrusion, just flat inset. 
                # The "inner" faces are the ones we inset.
                for f in faces_inner:
                    f.material_index = 1

        # ----------------------------------------------------------------------
        # 4. FINAL CLEANUP & NORMAL ENFORCEMENT
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
        # 5. MARK SEAMS
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
                    mat_idx = e.link_faces[0].material_index
                    
                    # Special Rule for Edge Banding (Slot 0)
                    if mat_idx == 0:
                        # Only ONE vertical seam per Box loop
                        # Box side faces are approx vertical.
                        # We want to unwrap as a strip.
                        
                        # Check verticality
                        v1, v2 = e.verts
                        is_vertical = abs(v1.co.x - v2.co.x) < 0.001 and abs(v1.co.y - v2.co.y) < 0.001
                        
                        if is_vertical:
                            # We need a consistent rule to pick ONE edge per box.
                            
                            # Fallback: Just look at normal directions.
                            # If normals are (-1,0,0) and (0,-1,0), that's a corner.
                            n1 = e.link_faces[0].normal
                            n2 = e.link_faces[1].normal
                            
                            # If it's the corner between Left (-X) and Back (-Y)?
                            if n1.x < -0.9 or n2.x < -0.9:
                                if n1.y < -0.9 or n2.y < -0.9:
                                    e.seam = True
                        else:
                            # Horizontal edges (top/bottom rim)
                            # These are already handled by Material Boundary (Slot 0 vs Slot 3/2)
                            pass
                            
                    else:
                        # Standard Box Logic
                        n1 = e.link_faces[0].normal
                        n2 = e.link_faces[1].normal
                        if n1.dot(n2) < 0.5:  # 60 degrees
                            e.seam = True

        # ----------------------------------------------------------------------
        # 6. UV MAPPING
        # ----------------------------------------------------------------------
        uv_layer = bm.loops.layers.uv.verify()
        s = 1.0 if self.fit_uvs else self.uv_scale

        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            # Special Strip Map for Edge Banding (Slot 0)
            if f.material_index == 0:
                # Standard Box Map Logic for now to ensure clean islands
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

            else:
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
            (-hw, -hl, h),
            (hw, -hl, h),
            (hw, hl, h),
            (-hw, hl, h),  # Top Ring (Z=h)
            (-hw, -hl, 0),
            (hw, -hl, 0),
            (hw, hl, 0),
            (-hw, hl, 0),  # Bottom Ring (Z=0)
        ]
        verts = [bm.verts.new(Vector(c) + center) for c in coords]

        # Faces
        f_top = bm.faces.new([verts[0], verts[1], verts[2], verts[3]])
        f_top.material_index = 3  # Frame Surface

        f_bot = bm.faces.new([verts[4], verts[7], verts[6], verts[5]])
        f_bot.material_index = 2  # Backing

        # Sides
        side_indices = [(0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        for idxs in side_indices:
            f = bm.faces.new([verts[i] for i in idxs])
            f.material_index = 0  # Edge Banding

        return f_top

