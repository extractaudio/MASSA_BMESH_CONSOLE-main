import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_14: Loading Dock",
    "id": "asm_14_loading_dock",
    "icon": "MOD_BUILD",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}


class MASSA_OT_AsmLoadingDock(Massa_OT_Base):
    bl_idname = "massa.gen_asm_14_loading_dock",
    bl_label = "ASM_14 Loading Dock"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    width: FloatProperty(name="Bay Width", default=4.0, min=2.0, unit="LENGTH")
    height: FloatProperty(name="Dock Height", default=1.2, min=0.5, unit="LENGTH")
    depth: FloatProperty(name="Floor Depth", default=3.0, min=1.0, unit="LENGTH")

    # --- 2. DOOR ---
    door_width: FloatProperty(name="Door Width", default=2.8, min=1.0, unit="LENGTH")
    door_height: FloatProperty(name="Door Height", default=3.0, min=1.5, unit="LENGTH")

    # --- 3. RAMP ---
    ramp_width: FloatProperty(name="Ramp Width", default=2.0, min=1.0, unit="LENGTH")
    ramp_length: FloatProperty(name="Ramp Length", default=2.5, min=1.0, unit="LENGTH")

    # --- 4. BUMPERS ---
    bumper_width: FloatProperty(name="Bump Width", default=0.25, min=0.1, unit="LENGTH")
    bumper_height: FloatProperty(name="Bump Height", default=0.5, min=0.1, unit="LENGTH")
    bumper_thick: FloatProperty(name="Bump Thick", default=0.15, min=0.05, unit="LENGTH")

    # --- 5. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Concrete", "uv": "BOX", "phys": "CONCRETE"},
            1: {"name": "Ramp", "uv": "BOX", "phys": "METAL_STEEL"},
            2: {"name": "Door", "uv": "BOX", "phys": "METAL_CORRUGATED"}, # Uses PRIM_03 logic (Corrugated)
            3: {"name": "Wall", "uv": "BOX", "phys": "CONCRETE"},
            5: {"name": "Rubber", "uv": "BOX", "phys": "RUBBER"},
            9: {"name": "Sockets", "uv": "BOX", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "depth")

        col.separator()
        col.label(text="Door")
        col.prop(self, "door_width")
        col.prop(self, "door_height")

        col.separator()
        col.label(text="Ramp")
        col.prop(self, "ramp_width")
        col.prop(self, "ramp_length")

        col.separator()
        col.label(text="Bumpers")
        col.prop(self, "bumper_width")
        col.prop(self, "bumper_height")
        col.prop(self, "bumper_thick")

    def build_shape(self, bm: bmesh.types.BMesh):
        w = self.width
        h = self.height
        d = self.depth
        dw = self.door_width
        dh = self.door_height
        rw = self.ramp_width
        rl = self.ramp_length
        bw = self.bumper_width
        bh = self.bumper_height
        bt = self.bumper_thick

        uv_layer = bm.loops.layers.uv.verify()
        scale = self.uv_scale

        # 1. PLATFORM (Floor)
        # From Y=0 to Y=-d. Z=h.
        # Wall is at Y=0.
        # But wait, usually we want the Dock Face at Y=0.
        # So Floor is Y < 0.
        # Wall rises from Y=0.

        # Floor Slab
        res_floor = bmesh.ops.create_cube(bm, size=1.0)
        verts_floor = res_floor['verts']
        bmesh.ops.scale(bm, vec=(w, d, h), verts=verts_floor)
        bmesh.ops.translate(bm, vec=(0, -d/2, h/2), verts=verts_floor)

        # Assign Material
        for f in list({f for v in verts_floor for f in v.link_faces}):
            f.material_index = 0
            self.apply_box_map(f, uv_layer, scale)

        # 2. RAMP (Leveler)
        # Inset in floor.
        # Centered at X=0. Y start at 0? Or slightly inset?
        # Usually starts at dock edge (Y=0).
        # Box slightly recessed or angled.
        # Let's make it a separate plate on top for simplicity, or boolean?
        # Simpler: Create plate at Z=h.

        res_ramp = bmesh.ops.create_cube(bm, size=1.0)
        verts_ramp = res_ramp['verts']
        bmesh.ops.scale(bm, vec=(rw, rl, 0.05), verts=verts_ramp)
        # Position: Center X, Y = -rl/2 (starts at 0, goes in). Z = h
        bmesh.ops.translate(bm, vec=(0, -rl/2, h + 0.025), verts=verts_ramp)
        # Rotate slightly to simulate slope?
        # bmesh.ops.rotate(bm, cent=(0,0,h), matrix=Matrix.Rotation(math.radians(-5), 4, 'X'), verts=verts_ramp)

        for f in list({f for v in verts_ramp for f in v.link_faces}):
            f.material_index = 1 # Metal Ramp
            self.apply_box_map(f, uv_layer, scale)

        # 3. WALL / DOOR FRAME
        # Wall at Y=0. Z from h to h+dh+something.
        # Or from 0 to h+dh?
        # Usually Dock Wall is the full height.
        # Let's create a wall with a door hole.
        # Wall dimensions: Width w, Height dh+1.0 (header).
        # Position Y=0.

        # Left Pillar
        res_w1 = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=((w-dw)/2, 0.3, dh + 1.0), verts=res_w1['verts'])
        # Pos: X = -dw/2 - (w-dw)/4
        x_pos = -dw/2 - (w-dw)/4
        z_pos = h + (dh+1.0)/2
        bmesh.ops.translate(bm, vec=(x_pos, 0, z_pos), verts=res_w1['verts'])

        # Right Pillar
        res_w2 = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=((w-dw)/2, 0.3, dh + 1.0), verts=res_w2['verts'])
        x_pos = dw/2 + (w-dw)/4
        bmesh.ops.translate(bm, vec=(x_pos, 0, z_pos), verts=res_w2['verts'])

        # Header
        res_w3 = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(dw, 0.3, 1.0), verts=res_w3['verts'])
        bmesh.ops.translate(bm, vec=(0, 0, h + dh + 0.5), verts=res_w3['verts'])

        wall_verts = res_w1['verts'] + res_w2['verts'] + res_w3['verts']
        for f in list({f for v in wall_verts for f in v.link_faces}):
            f.material_index = 3 # Wall
            self.apply_box_map(f, uv_layer, scale)

        # 4. DOOR (Corrugated Strips)
        # Fill the portal: -dw/2 to dw/2, h to h+dh.
        # Corrugated: Horizontal strips.
        # Simple plane with normal map? Or geometry?
        # "Generate... horizontal corrugated strips (PRIM_03 logic)".
        # PRIM_03 uses sine wave geometry or triangular strips.
        # I'll use simple triangular ridges.

        strips = 10
        strip_h = dh / strips

        # Create a single face and subdivide?
        # Or loop create strips.

        for i in range(strips):
            z_start = h + i * strip_h
            z_end = z_start + strip_h

            # Simple wedge/box per strip
            res_d = bmesh.ops.create_cube(bm, size=1.0)
            verts_d = res_d['verts']
            bmesh.ops.scale(bm, vec=(dw, 0.05, strip_h * 0.9), verts=verts_d)
            bmesh.ops.translate(bm, vec=(0, 0, z_start + strip_h/2), verts=verts_d)

            # Offset every other strip slightly for "roll-up" look?
            # Or make them corrugated (zigzag in Z).

            for f in list({f for v in verts_d for f in v.link_faces}):
                f.material_index = 2 # Door
                self.apply_box_map(f, uv_layer, scale)

        # 5. BUMPERS
        # Two vertical blocks.
        # Pos: Y=0 (Front face). X +/- (dw/2 + bw/2 + gap).
        # Z: Centered around h? Or just below h?
        # Usually buffers are at truck bed height (approx h).
        # So centered at Z=h.

        # Left Bumper
        res_b1 = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(bw, bt, bh), verts=res_b1['verts'])
        bmesh.ops.translate(bm, vec=(-dw/2 - bw, bt/2, h), verts=res_b1['verts'])

        # Right Bumper
        res_b2 = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(bw, bt, bh), verts=res_b2['verts'])
        bmesh.ops.translate(bm, vec=(dw/2 + bw, bt/2, h), verts=res_b2['verts'])

        for f in list({f for v in res_b1['verts'] + res_b2['verts'] for f in v.link_faces}):
            f.material_index = 5 # Rubber
            self.apply_box_map(f, uv_layer, scale)

        # 6. SOCKET
        # Outward Socket for Truck.
        # At (0,0,0) facing +Y.
        # Note: (0,0,0) is ground level, below the dock (Z=h).
        # Truck wheels are at Z=0.

        res_s = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.2)
        # Rotate to face +Y
        # Plane normal +Z. Rot -90 X -> +Y.
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(-90), 4, 'X'), verts=res_s['verts'])
        bmesh.ops.translate(bm, vec=(0, 0.5, 0), verts=res_s['verts']) # Slightly in front? Or at 0.
        # If bumpers are at Y=0 to Y=bt. Truck backs to Y=bt.
        # So socket should be at Y=bt (bumper face)?
        # If truck snaps to socket, its rear touches socket.
        # Let's place socket at Y=bt + 0.1 (tolerance).
        bmesh.ops.translate(bm, vec=(0, bt + 0.1, 0), verts=res_s['verts'])

        for f in res_s['faces']:
            f.material_index = 9
            # Normal is +Y.
            # No flip needed if rotated -90 X.
            pass

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    def apply_box_map(self, face, uv_layer, scale):
        n = face.normal
        nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)
        for l in face.loops:
            co = l.vert.co
            if nz > nx and nz > ny:
                u, v = co.x, co.y
            elif nx > ny and nx > nz:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            l[uv_layer].uv = (u * scale, v * scale)
