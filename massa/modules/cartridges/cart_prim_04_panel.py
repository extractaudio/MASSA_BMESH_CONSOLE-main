import bpy
import bmesh
# [Massa Fix] Forced Timestamp Update for Extension Cache
import math
from mathutils import Vector
from bpy.props import FloatProperty, IntProperty, FloatVectorProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_04: Tech Panel",
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
    bl_label = "PRIM_04: Tech Panel"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    size: FloatVectorProperty(name="Size", default=(2.0, 2.0, 0.1), min=0.01)

    # --- 2. GRID PATTERN ---
    cuts_x: IntProperty(name="Grid X", default=4, min=1)
    cuts_y: IntProperty(name="Grid Y", default=4, min=1)
    gap: FloatProperty(name="Tile Gap", default=0.02, min=0.0, unit="LENGTH")

    # --- 3. FRAME ---
    frame_width: FloatProperty(name="Frame Width", default=0.1, min=0.0)
    frame_height: FloatProperty(name="Frame Height", default=0.05, min=0.0)

    # --- 4. TILE PROFILE ---
    tile_height: FloatProperty(name="Tile Height", default=0.05, min=0.0)
    inset_amount: FloatProperty(name="Inset Margin", default=0.05, min=0.0)
    inset_depth: FloatProperty(
        name="Inset Depth",
        default=-0.02,
        description="Depth of the inner detail relative to tile top",
    )

    # --- 5. CUTOUT ---
    use_cutout: BoolProperty(name="Center Cutout", default=False)
    cutout_ratio: FloatProperty(
        name="Cutout Ratio",
        default=0.3,
        min=0.0,
        max=0.9,
        description="Size of cutout relative to grid",
    )

    # --- 6. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs: BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self) -> dict:
        return {
            0: {"name": "Frame", "uv": "SKIP", "phys": "METAL_STEEL"},
            1: {"name": "Backing Plate", "uv": "SKIP", "phys": "GENERIC"},
            2: {"name": "Tile Body", "uv": "SKIP", "phys": "METAL_STEEL"},
            3: {"name": "Tile Inset", "uv": "SKIP", "phys": "METAL_DARK"},
            4: {"name": "Tech Detail", "uv": "SKIP", "phys": "EMISSION"},
            8: {"name": "Anchor (Bottom)", "uv": "SKIP", "phys": "GENERIC", "sock": True},
            9: {"name": "Mount (Top)", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Dimensions", icon="FIXED_SIZE")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "size", index=0, text="X")
        row.prop(self, "size", index=1, text="Y")
        row.prop(self, "size", index=2, text="Z (Base)")

        layout.separator()
        layout.label(text="Grid & Frame", icon="GRID")
        col = layout.column(align=True)
        col.prop(self, "frame_width")
        col.prop(self, "frame_height")
        row = col.row(align=True)
        row.prop(self, "cuts_x", text="X")
        row.prop(self, "cuts_y", text="Y")
        col.prop(self, "gap")

        layout.separator()
        layout.label(text="Tech Tile Profile", icon="MOD_BEVEL")
        col = layout.column(align=True)
        col.prop(self, "tile_height")
        col.prop(self, "inset_amount")
        col.prop(self, "inset_depth")

        layout.separator()
        layout.label(text="Features", icon="MOD_BOOLEAN")
        col = layout.column(align=True)
        col.prop(self, "use_cutout")
        if self.use_cutout:
            col.prop(self, "cutout_ratio")

    def build_shape(self, bm: bmesh.types.BMesh) -> None:
        sx, sy, sz = self.size

        # ----------------------------------------------------------------------
        # 1. SETUP LAYERS
        # ----------------------------------------------------------------------
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # ----------------------------------------------------------------------
        # 2. BACKING PLATE (Base)
        # ----------------------------------------------------------------------
        # Create base box centered at Z=sz/2 (assuming Z=0 is bottom)
        # We'll treat Z=0 as the bottom plane for the Anchor.
        # The backing plate goes from Z=0 to Z=sz

        # Define geometry helper
        def create_box(center, size, mat_idx, return_top=False):
            # Center is Vector((x, y, z_center))
            # Size is Vector((w, l, h))
            w, l, h = size
            hw, hl, hh = w / 2, l / 2, h / 2

            # Local Coords
            coords = [
                (-hw, -hl, -hh), (hw, -hl, -hh), (hw, hl, -hh), (-hw, hl, -hh), # Bot
                (-hw, -hl, hh), (hw, -hl, hh), (hw, hl, hh), (-hw, hl, hh)      # Top
            ]

            verts = [bm.verts.new(Vector(c) + center) for c in coords]

            # Faces: Top, Bot, Front, Right, Back, Left
            # Winding Order: CCW for outward normals
            faces = []
            faces.append(bm.faces.new([verts[4], verts[5], verts[6], verts[7]])) # Top (Z+)
            faces.append(bm.faces.new([verts[0], verts[3], verts[2], verts[1]])) # Bot (Z-)
            faces.append(bm.faces.new([verts[0], verts[1], verts[5], verts[4]])) # Front (Y-)
            faces.append(bm.faces.new([verts[1], verts[2], verts[6], verts[5]])) # Right (X+)
            faces.append(bm.faces.new([verts[2], verts[3], verts[7], verts[6]])) # Back (Y+)
            faces.append(bm.faces.new([verts[3], verts[0], verts[4], verts[7]])) # Left (X-)

            for f in faces:
                f.material_index = mat_idx

            return faces[0] if return_top else faces

        # Create Backing
        # Size: sx, sy, sz
        # Center: 0, 0, sz/2
        create_box(Vector((0, 0, sz / 2)), Vector((sx, sy, sz)), 1) # Slot 1: Backing

        # ----------------------------------------------------------------------
        # 3. FRAME
        # ----------------------------------------------------------------------
        # The frame sits on top of the backing, around the perimeter.
        # Frame Height adds to SZ.
        # It's a hollow rectangle. We can make 4 boxes or extrude a ring.
        # Let's make 4 boxes for cleaner topology separation (Tech style).

        fw = self.frame_width
        fh = self.frame_height

        if fw > 0.001 and fh > 0.001:
            # Top of backing
            base_z = sz + fh / 2
            
            # Top/Bottom Bars (Full Width)
            # Size: sx, fw, fh
            # Pos Y: +/- (sy/2 - fw/2)
            pos_y_top = (sy / 2) - (fw / 2)
            pos_y_bot = -((sy / 2) - (fw / 2))

            create_box(Vector((0, pos_y_top, base_z)), Vector((sx, fw, fh)), 0) # Slot 0: Frame
            create_box(Vector((0, pos_y_bot, base_z)), Vector((sx, fw, fh)), 0) # Slot 0: Frame

            # Side Bars (Between Top/Bot)
            # Length: sy - 2*fw
            # Width: fw
            # Pos X: +/- (sx/2 - fw/2)
            side_len = max(0.001, sy - (2 * fw))
            pos_x_right = (sx / 2) - (fw / 2)
            pos_x_left = -((sx / 2) - (fw / 2))
            
            create_box(Vector((pos_x_right, 0, base_z)), Vector((fw, side_len, fh)), 0)
            create_box(Vector((pos_x_left, 0, base_z)), Vector((fw, side_len, fh)), 0)

        # ----------------------------------------------------------------------
        # 4. GRID TILES
        # ----------------------------------------------------------------------
        # Area available for tiles
        grid_w = sx - (2 * fw)
        grid_l = sy - (2 * fw)

        if grid_w > 0.01 and grid_l > 0.01:
            # Calculate Cell Size
            # We want `cuts_x` tiles.
            # Total Gap Width X = gap * (cuts_x - 1) ... actually gap is between tiles?
            # Let's say gap is margin around each tile effectively.
            # Or gap is between tiles.

            # Effective cell size
            # w = (grid_w - (cuts_x - 1)*gap) / cuts_x ??
            # Simpler: Divide grid_w by cuts_x, then shrink by gap/2 on each side.

            raw_cell_w = grid_w / self.cuts_x
            raw_cell_l = grid_l / self.cuts_y

            # Apply Gap
            cell_w = max(0.001, raw_cell_w - self.gap)
            cell_l = max(0.001, raw_cell_l - self.gap)

            start_x = -(grid_w / 2) + (raw_cell_w / 2)
            start_y = -(grid_l / 2) + (raw_cell_l / 2)

            tile_base_z = sz + (self.tile_height / 2)

            for ix in range(self.cuts_x):
                for iy in range(self.cuts_y):
                    # Cutout Check
                    if self.use_cutout:
                        # Normalize position -1 to 1
                        nx = (ix / (self.cuts_x - 1)) * 2 - 1 if self.cuts_x > 1 else 0
                        ny = (iy / (self.cuts_y - 1)) * 2 - 1 if self.cuts_y > 1 else 0
                        dist = max(abs(nx), abs(ny)) # Box distance
                        if dist < self.cutout_ratio:
                            continue

                    cx = start_x + (ix * raw_cell_w)
                    cy = start_y + (iy * raw_cell_l)

                    # Create Tile Base (Slot 2)
                    center = Vector((cx, cy, tile_base_z))
                    top_face = create_box(center, Vector((cell_w, cell_l, self.tile_height)), 2, return_top=True)

                    # --- Tech Detail Logic ---
                    # Inset Top Face
                    if self.inset_amount > 0.001:
                        top_face.normal_update()
                        # Inset + Depth (Atomic Operation)
                        # Fixes "Lid" issue by handling depth within the inset op
                        res = bmesh.ops.inset_region(
                            bm, 
                            faces=[top_face], 
                            thickness=self.inset_amount, 
                            depth=self.inset_depth, 
                            use_even_offset=True
                        )
                        faces_inner = res["faces"]

                        # Assign Materials (Faces are now the bottom of the inset)
                        # The side faces are usually not in 'faces' list from inset_region directly? 
                        # Actually inset_region returns 'faces' as the inner region.
                        # Side faces are tricky to get from simple inset_region return.
                        # BUT, generally they inherit from original.
                        
                        # Let's check material assignment.
                        # If we used depth, the side faces exist.
                        # We might need to find them if we want to color them different (Slot 3).
                        
                        # Strategy: Select faces_inner. Grow selection? 
                        # Or just set inner to 4 (Detail) and let sides be whatever (likely 2).
                        
                        for f in faces_inner:
                            f.material_index = 4 # Tech Detail / Light (Inner Bottom)
                            
                        # To find side faces, we can look at faces connected to inner faces that are NOT inner faces.
                        # Side faces will have normal roughly perpendicular to Z.
                        
                        # Simple loop to color sides:
                        # We know inner faces.
                        for f in faces_inner:
                            for loop in f.loops:
                                edge = loop.edge
                                for link_face in edge.link_faces:
                                    if link_face not in faces_inner:
                                        # This is likely a side face
                                        link_face.material_index = 3 # Tile Inset (Sides)

                    # --- Socket: Mount (Top) ---
                    # Create a tiny quad at center top of tile
                    # Height: sz + tile_height (top surface)
                    # Use a small offset to avoid Z-fighting if flush, or just flush if mandated.
                    # Mandate says "Socket Anchor" material slot.
                    # Position: cx, cy, sz + tile_height + 0.005
                    sock_z = sz + self.tile_height
                    if self.inset_amount > 0.001:
                        sock_z += self.inset_depth

                    self.create_socket_face(bm, Vector((cx, cy, sock_z + 0.002)), 0.08, 9, up=True)

        # ----------------------------------------------------------------------
        # 5. SOCKET: ANCHOR (Bottom)
        # ----------------------------------------------------------------------
        # Slot 8, Facing Down (Z-)
        self.create_socket_face(bm, Vector((0, 0, -0.002)), 0.1, 8, up=False)

        # ----------------------------------------------------------------------
        # 6. CLEANUP & NORMALS
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # ----------------------------------------------------------------------
        # 7. EDGE ROLES & SEAMS
        # ----------------------------------------------------------------------
        bm.edges.ensure_lookup_table()
        for e in bm.edges:
            # Angle check
            if not e.is_manifold:
                continue
            if len(e.link_faces) < 2:
                continue

            f1, f2 = e.link_faces[0], e.link_faces[1]
            angle = f1.normal.dot(f2.normal)

            # Sharp / Seam for > 45 deg (dot < 0.7)
            if angle < 0.7:
                e.seam = True
                e.smooth = False
                e[edge_slots] = 1 # Perimeter / Hard

            # Material Boundary
            if f1.material_index != f2.material_index:
                e.seam = True
                e[edge_slots] = 2 # Detail

            # Frame edges?
            if f1.material_index == 0 or f2.material_index == 0:
                # Mark frame outer edges as perimeter
                if angle < 0.7:
                    e[edge_slots] = 1

        # ----------------------------------------------------------------------
        # 8. UV MAPPING (Manual Box Map)
        # ----------------------------------------------------------------------
        self.apply_box_uvs(bm, uv_layer)

    def create_socket_face(self, bm, center, size, mat_idx, up=True):
        """Creates a detached quad for socket anchoring."""
        hs = size / 2
        z = center.z

        # Coords
        coords = [
            (center.x - hs, center.y - hs, z),
            (center.x + hs, center.y - hs, z),
            (center.x + hs, center.y + hs, z),
            (center.x - hs, center.y + hs, z),
        ]

        verts = [bm.verts.new(Vector(c)) for c in coords]
        f = bm.faces.new(verts)
        f.material_index = mat_idx

        # If facing down, flip normal (create reversed or flip)
        # Default creation is CCW (Up).
        if not up:
            f.normal_flip()

    def apply_box_uvs(self, bm, uv_layer):
        scale = self.uv_scale

        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            # Determine projection axis
            if nz > nx and nz > ny:
                # Top/Bottom -> XY
                for l in f.loops:
                    u = l.vert.co.x
                    v = l.vert.co.y
                    l[uv_layer].uv = (u * scale, v * scale)
            elif nx > ny and nx > nz:
                # Side X -> YZ
                for l in f.loops:
                    u = l.vert.co.y
                    v = l.vert.co.z
                    l[uv_layer].uv = (u * scale, v * scale)
            else:
                # Side Y -> XZ
                for l in f.loops:
                    u = l.vert.co.x
                    v = l.vert.co.z
                    l[uv_layer].uv = (u * scale, v * scale)

    def execute(self, context):
        # 1. Run Standard Generation
        result = super().execute(context)

        # 2. Post-Process: Socket 0 Orientation
        # Fix: Flip "Frame" Socket (Slot 0) to point Z- (Down)
        if "FINISHED" in result:
            obj = context.active_object
            if obj:
                # Find the socket for Slot 0
                # Slot 0 name is "Frame"
                target_prefix = f"SOCKET_{obj.name}_Frame"
                
                for child in obj.children:
                    if child.name.startswith(target_prefix):
                        # Force Rotation to Point Down (PI, 0, 0)
                        child.rotation_euler = (math.pi, 0, 0)
                        
        return result
