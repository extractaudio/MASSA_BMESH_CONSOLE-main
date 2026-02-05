"""
Filename: modules/cartridges/prim_con_doorway.py
Content: Parametric Doorway Generator with Trim and Hardware
Status: NEW (v1.0)
"""

import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector

CARTRIDGE_META = {
    "name": "Con: Doorway",
    "id": "prim_con_doorway",
    "icon": "DOOR",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": False,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}

DOOR_STANDARDS = {
    "STD_INT": (0.9, 2.1),   # Standard Interior
    "STD_EXT": (1.0, 2.1),   # Standard Exterior
    "DBL_PATIO": (1.8, 2.1), # Double Patio
    "CLOSET": (0.75, 2.1),   # Small Closet
}

def update_door_dims(self, context):
    if self.standard_type in DOOR_STANDARDS:
        w, h = DOOR_STANDARDS[self.standard_type]
        self.width = w
        self.height = h

class MASSA_OT_prim_con_doorway(Massa_OT_Base):
    bl_idname = "massa.gen_prim_con_doorway"
    bl_label = "Construction Doorway"
    bl_description = "Door with Frame, Trim, Stop, and Hardware"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- PRESETS ---
    standard_type: EnumProperty(
        name="Standard",
        items=[
            ("CUSTOM", "Custom", "Manual Dimensions"),
            ("STD_INT", "Interior (0.9 x 2.1m)", "Standard Room"),
            ("STD_EXT", "Exterior (1.0 x 2.1m)", "Main Entry"),
            ("DBL_PATIO", "Double (1.8 x 2.1m)", "Patio/French"),
            ("CLOSET", "Closet (0.75 x 2.1m)", "Small Utility"),
        ],
        default="CUSTOM",
        update=update_door_dims,
    )

    # --- DIMENSIONS ---
    width: FloatProperty(name="Width", default=0.9, min=0.5, unit="LENGTH")
    height: FloatProperty(name="Height", default=2.1, min=1.0, unit="LENGTH")
    depth: FloatProperty(name="Frame Depth", default=0.15, min=0.05, unit="LENGTH")
    frame_width: FloatProperty(name="Frame Thickness", default=0.05, min=0.01, unit="LENGTH")

    # --- DOOR PANEL ---
    door_inset: FloatProperty(name="Door Inset", default=0.02, min=0.0, unit="LENGTH")
    panel_thick: FloatProperty(name="Panel Thickness", default=0.04, min=0.01, unit="LENGTH")

    # --- TRIM ---
    use_trim: BoolProperty(name="Use Trim", default=True)
    trim_width: FloatProperty(name="Trim Width", default=0.08, min=0.01, unit="LENGTH")
    trim_depth: FloatProperty(name="Trim Depth", default=0.02, min=0.005, unit="LENGTH")

    # --- HARDWARE ---
    use_stop: BoolProperty(name="Floor Stop", default=True)
    stop_height: FloatProperty(name="Stop Height", default=0.01, min=0.001, unit="LENGTH")

    use_hinges: BoolProperty(name="Hinges", default=True)
    hinge_count: IntProperty(name="Hinge Count", default=3, min=2, max=5)

    handle_type: EnumProperty(
        name="Handle",
        items=[
            ("NONE", "None", "No Handle"),
            ("KNOB", "Knob", "Round Knob"),
            ("LEVER", "Lever", "Linear Lever"),
            ("PULL", "Pull", "Vertical Pull"),
        ],
        default="LEVER"
    )
    handle_height: FloatProperty(name="Handle Height", default=1.0, min=0.5, max=1.5, unit="LENGTH")

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.prop(self, "standard_type", text="Preset")

        col = box.column()
        col.active = self.standard_type == "CUSTOM"
        col.prop(self, "width")
        col.prop(self, "height")

        box = layout.box()
        box.label(text="Frame & Panel", icon="MOD_BUILD")
        box.prop(self, "depth", text="Frame Depth")
        box.prop(self, "frame_width", text="Frame Thick")
        box.prop(self, "panel_thick")
        box.prop(self, "door_inset")

        box = layout.box()
        box.label(text="Extras", icon="PLUS")

        row = box.row()
        row.prop(self, "use_trim", icon="CHECKBOX_HLT")
        if self.use_trim:
            sub = box.column(align=True)
            sub.prop(self, "trim_width")
            sub.prop(self, "trim_depth")

        row = box.row()
        row.prop(self, "use_stop", icon="CHECKBOX_HLT")
        if self.use_stop:
            box.prop(self, "stop_height")

        box = layout.box()
        box.label(text="Hardware", icon="EMPTY_AXIS")
        box.prop(self, "use_hinges")
        if self.use_hinges:
            box.prop(self, "hinge_count")

        box.prop(self, "handle_type")
        if self.handle_type != 'NONE':
            box.prop(self, "handle_height")

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "WOOD_PAINTED"},
            1: {"name": "Door", "uv": "BOX", "phys": "WOOD_PAINTED"},
            2: {"name": "Trim", "uv": "BOX", "phys": "WOOD_PAINTED"},
            3: {"name": "Handle", "uv": "BOX", "phys": "METAL_ROUGH"},
            4: {"name": "Hinges", "uv": "BOX", "phys": "METAL_ROUGH"},
            5: {"name": "FloorStop", "uv": "BOX", "phys": "METAL_ROUGH"},
            6: {"name": "Socket_A", "uv": "SKIP", "sock": True},
            7: {"name": "Socket_B", "uv": "SKIP", "sock": True},
            8: {"name": "Socket_C", "uv": "SKIP", "sock": True},
            9: {"name": "Socket_D", "uv": "SKIP", "sock": True},
        }

    def build_shape(self, bm):
        # 0. DEFAULTS & LAYERS
        tag_layer = bm.faces.layers.int.new("MAT_TAG")

        w, h = self.width, self.height
        fd, fw = self.depth, self.frame_width

        # 1. FRAME GENERATION (Tag 0)
        # 3 parts: Left Jamb, Right Jamb, Header

        frames = []

        # Left
        ret_l = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(fw, fd, h), verts=ret_l["verts"])
        bmesh.ops.translate(bm, verts=ret_l["verts"], vec=(-w/2 + fw/2, 0, h/2))
        frames.extend(ret_l["verts"])

        # Right
        ret_r = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(fw, fd, h), verts=ret_r["verts"])
        bmesh.ops.translate(bm, verts=ret_r["verts"], vec=(w/2 - fw/2, 0, h/2))
        frames.extend(ret_r["verts"])

        # Header
        ret_t = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w - 2*fw, fd, fw), verts=ret_t["verts"])
        bmesh.ops.translate(bm, verts=ret_t["verts"], vec=(0, 0, h - fw/2))
        frames.extend(ret_t["verts"])

        # Tag Frame
        for v in frames:
            for f in v.link_faces:
                f[tag_layer] = 0

        # 2. DOOR PANEL (Tag 1)
        dw = w - 2*fw
        dh = h - fw
        dt = self.panel_thick
        inset_z = self.door_inset

        # Check valid size
        if dw > 0.01 and dh > 0.01:
            ret_d = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(dw - 0.004, dt, dh - 0.004), verts=ret_d["verts"]) # Slight gap
            # Center of door is at 0,0,0 initially. Need to move up by dh/2 and back by inset
            bmesh.ops.translate(bm, verts=ret_d["verts"], vec=(0, -fd/2 + dt/2 + inset_z, dh/2))

            for v in ret_d["verts"]:
                for f in v.link_faces:
                    f[tag_layer] = 1

        # 3. TRIM (Tag 2)
        if self.use_trim:
            tw = self.trim_width
            td = self.trim_depth

            # Helper for trim pieces
            def create_trim_piece(size, pos):
                r = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=size, verts=r["verts"])
                bmesh.ops.translate(bm, verts=r["verts"], vec=pos)
                for v in r["verts"]:
                    for f in v.link_faces:
                        f[tag_layer] = 2

            # Left Trim (Front)
            create_trim_piece((tw, td, h + tw), (-w/2 - tw/2 + fw, fd/2 + td/2, h/2 + tw/2))
            # Right Trim (Front)
            create_trim_piece((tw, td, h + tw), (w/2 + tw/2 - fw, fd/2 + td/2, h/2 + tw/2))
            # Top Trim (Front)
            create_trim_piece((w + 2*tw, td, tw), (0, fd/2 + td/2, h + tw/2))

            # Left Trim (Back)
            create_trim_piece((tw, td, h + tw), (-w/2 - tw/2 + fw, -fd/2 - td/2, h/2 + tw/2))
            # Right Trim (Back)
            create_trim_piece((tw, td, h + tw), (w/2 + tw/2 - fw, -fd/2 - td/2, h/2 + tw/2))
            # Top Trim (Back)
            create_trim_piece((w + 2*tw, td, tw), (0, -fd/2 - td/2, h + tw/2))

        # 4. FLOOR STOP (Tag 5)
        if self.use_stop:
            sw = w - 2*fw
            sh = self.stop_height
            sd = dt + 0.02 # Slightly wider than door

            ret_s = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(sw, sd, sh), verts=ret_s["verts"])
            bmesh.ops.translate(bm, verts=ret_s["verts"], vec=(0, 0, sh/2))

            for v in ret_s["verts"]:
                for f in v.link_faces:
                    f[tag_layer] = 5

        # 5. HARDWARE - HINGES (Tag 4)
        if self.use_hinges and self.hinge_count > 0:
            h_rad = 0.01
            h_len = 0.08

            spacing = (h - 0.4) / (self.hinge_count - 1) if self.hinge_count > 1 else 0
            start_z = 0.2

            for i in range(self.hinge_count):
                z_pos = start_z + (i * spacing)
                # Left side hinge
                ret_h = bmesh.ops.create_cube(bm, size=1.0) # Simple block hinge
                bmesh.ops.scale(bm, vec=(h_rad*2, h_rad*2, h_len), verts=ret_h["verts"])
                # Position at seam between frame and door
                bmesh.ops.translate(bm, verts=ret_h["verts"], vec=(-w/2 + fw, -fd/2 + dt + inset_z, z_pos))

                for v in ret_h["verts"]:
                    for f in v.link_faces:
                        f[tag_layer] = 4

        # 6. HARDWARE - HANDLE (Tag 3)
        if self.handle_type != 'NONE':
            # Position logic
            hx = w/2 - fw - 0.06 # Inset from right edge
            hz = self.handle_height
            hy = -fd/2 + dt + inset_z # Door surface

            if self.handle_type == 'KNOB':
                ret_k = bmesh.ops.create_cube(bm, size=1.0) # Placeholder for sphere/knob
                bmesh.ops.scale(bm, vec=(0.05, 0.06, 0.05), verts=ret_k["verts"])
                bmesh.ops.translate(bm, verts=ret_k["verts"], vec=(hx, hy + 0.03, hz))

            elif self.handle_type == 'LEVER':
                ret_k = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=(0.12, 0.02, 0.02), verts=ret_k["verts"])
                bmesh.ops.translate(bm, verts=ret_k["verts"], vec=(hx - 0.03, hy + 0.04, hz))

            elif self.handle_type == 'PULL':
                 ret_k = bmesh.ops.create_cube(bm, size=1.0)
                 bmesh.ops.scale(bm, vec=(0.02, 0.04, 0.2), verts=ret_k["verts"])
                 bmesh.ops.translate(bm, verts=ret_k["verts"], vec=(hx, hy + 0.02, hz))
            else:
                 ret_k = {'verts': []} # Safety

            if 'verts' in ret_k:
                for v in ret_k["verts"]:
                    for f in v.link_faces:
                        f[tag_layer] = 3

        # 7. ASSIGN MATERIALS
        for f in bm.faces:
            if f[tag_layer] in self.get_slot_meta():
                f.material_index = f[tag_layer]

        # 8. MARK EDGES
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for e in bm.edges:
            if e.is_boundary:
                e[edge_slots] = 1 # Perimeter
            elif e.calc_face_angle(0) > 0.5:
                e[edge_slots] = 2 # Hard Edge
