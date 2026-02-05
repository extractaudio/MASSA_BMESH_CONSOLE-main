"""
Filename: modules/cartridges/prim_con_cabinet.py
Content: Parametric Cabinet Generator with Drawers/Rails
Status: NEW (v1.0)
"""

import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector

CARTRIDGE_META = {
    "name": "Con: Cabinet",
    "id": "prim_con_cabinet",
    "icon": "CUBE",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": False,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}

CABINET_STANDARDS = {
    "BASE_STD": (0.6, 0.9, 0.6),    # W, H, D
    "WALL_STD": (0.6, 0.75, 0.3),   # W, H, D
    "VANITY": (0.9, 0.85, 0.55),    # W, H, D
    "TALL": (0.6, 2.1, 0.6),        # W, H, D
}

def update_cab_dims(self, context):
    if self.standard_type in CABINET_STANDARDS:
        w, h, d = CABINET_STANDARDS[self.standard_type]
        self.width = w
        self.height = h
        self.depth = d

class MASSA_OT_prim_con_cabinet(Massa_OT_Base):
    bl_idname = "massa.gen_prim_con_cabinet"
    bl_label = "Construction Cabinet"
    bl_description = "Modular Cabinet with Runners"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- PRESETS ---
    standard_type: EnumProperty(
        name="Standard",
        items=[
            ("CUSTOM", "Custom", "Manual Dimensions"),
            ("BASE_STD", "Base (60x90x60)", "Kitchen Base"),
            ("WALL_STD", "Wall (60x75x30)", "Kitchen Upper"),
            ("VANITY", "Vanity (90x85x55)", "Bathroom"),
            ("TALL", "Tall (60x210x60)", "Pantry"),
        ],
        default="CUSTOM",
        update=update_cab_dims,
    )

    # --- DIMS ---
    width: FloatProperty(name="Width", default=0.6, min=0.3, unit="LENGTH")
    height: FloatProperty(name="Height", default=0.9, min=0.3, unit="LENGTH")
    depth: FloatProperty(name="Depth", default=0.6, min=0.3, unit="LENGTH")

    # --- OPTS ---
    has_toe_kick: BoolProperty(name="Toe Kick", default=True)
    toe_height: FloatProperty(name="Toe Height", default=0.1, min=0.0)
    toe_depth: FloatProperty(name="Toe Depth", default=0.05, min=0.0)

    has_counter: BoolProperty(name="Countertop", default=True)
    counter_th: FloatProperty(name="Counter Thick", default=0.03)
    counter_over: FloatProperty(name="Counter Overhang", default=0.02)

    # --- FACE ---
    cols: IntProperty(name="Columns", default=1, min=1)
    rows: IntProperty(name="Rows", default=1, min=1)
    gap: FloatProperty(name="Gap", default=0.003)

    show_rails: BoolProperty(name="Show Rails", default=True)

    handle_type: EnumProperty(
        name="Handle",
        items=[('NONE', "None", ""), ('KNOB', "Knob", ""), ('BAR', "Bar", "")],
        default='BAR'
    )

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.prop(self, "standard_type")
        col = box.column()
        col.active = self.standard_type == "CUSTOM"
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "depth")

        box = layout.box()
        box.label(text="Structure", icon="MOD_BUILD")
        box.prop(self, "has_toe_kick")
        if self.has_toe_kick:
            row = box.row()
            row.prop(self, "toe_height")
            row.prop(self, "toe_depth")

        box.prop(self, "has_counter")
        if self.has_counter:
            row = box.row()
            row.prop(self, "counter_th")
            row.prop(self, "counter_over")

        box = layout.box()
        box.label(text="Fronts", icon="GRID")
        row = box.row()
        row.prop(self, "cols")
        row.prop(self, "rows")
        box.prop(self, "gap")
        box.prop(self, "show_rails")
        box.prop(self, "handle_type")

    def get_slot_meta(self):
        return {
            0: {"name": "Carcass", "uv": "BOX", "phys": "WOOD_VENEER"},
            1: {"name": "Fronts", "uv": "BOX", "phys": "PLASTIC_GLOSS"},
            2: {"name": "Counter", "uv": "BOX", "phys": "STONE_POLISHED"},
            3: {"name": "Hardware", "uv": "BOX", "phys": "METAL_ROUGH"},
            4: {"name": "Rails", "uv": "BOX", "phys": "METAL_PAINTED"},
            5: {"name": "Kick", "uv": "BOX", "phys": "PLASTIC_ROUGH"},
        }

    def build_shape(self, bm):
        # 0. INIT
        tag_layer = bm.faces.layers.int.new("MAT_TAG")

        w = self.width
        h = self.height
        d = self.depth

        # Helper
        def make_box(size, pos, tag):
            r = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=size, verts=r["verts"])
            bmesh.ops.translate(bm, verts=r["verts"], vec=pos)
            for v in r["verts"]:
                for f in v.link_faces:
                    f[tag_layer] = tag
            return r["verts"]

        # 1. CARCASS (Tag 0)
        # Adjust height for toe kick and counter
        eff_h = h
        start_z = 0

        if self.has_toe_kick:
            eff_h -= self.toe_height
            start_z += self.toe_height
            # Make Kick (Tag 5)
            k_d = d - self.toe_depth
            make_box((w, k_d, self.toe_height), (0, -self.toe_depth/2, self.toe_height/2), 5)

        if self.has_counter:
            eff_h -= self.counter_th

        # Main Box
        make_box((w, d, eff_h), (0, 0, start_z + eff_h/2), 0)

        # 2. COUNTER (Tag 2)
        if self.has_counter:
            cw = w + self.counter_over * 2
            cd = d + self.counter_over
            ct = self.counter_th
            cz = start_z + eff_h + ct/2
            # Offset forward for overhang
            cy = -self.counter_over/2
            make_box((cw, cd, ct), (0, cy, cz), 2)

        # 3. FRONTS (Tag 1) + RAILS (Tag 4)
        # Divide the front face volume
        # Front face area: W x H (eff_h)
        # Center Z of front area: start_z + eff_h/2

        f_thick = 0.02
        f_y = -d/2 - f_thick/2 # Front of carcass

        # Grid
        col_w = w / self.cols
        row_h = eff_h / self.rows

        g = self.gap

        for c in range(self.cols):
            for r in range(self.rows):
                # Center coords
                cx = -w/2 + (c * col_w) + col_w/2
                cz = start_z + (r * row_h) + row_h/2

                # Size
                sw = col_w - g
                sh = row_h - g

                # Front Panel
                make_box((sw, f_thick, sh), (cx, f_y, cz), 1)

                # Handle (Tag 3)
                if self.handle_type != 'NONE':
                    hx, hy, hz = cx, f_y - 0.03, cz + sh/3
                    make_box((0.1, 0.02, 0.02), (hx, hy, hz), 3)

                # Rails (Tag 4) - Internal Runners visual
                if self.show_rails:
                    # Side rails for this "unit"
                    # Right Rail
                    rx = cx + col_w/2 - 0.01 # Inside wall of this unit approx
                    ry = 0
                    rz = cz # Center of drawer
                    make_box((0.01, d - 0.05, 0.04), (rx, ry, rz), 4)

                    # Left Rail
                    lx = cx - col_w/2 + 0.01
                    make_box((0.01, d - 0.05, 0.04), (lx, ry, rz), 4)

        # 4. ASSIGN
        for f in bm.faces:
             if f[tag_layer] in self.get_slot_meta():
                f.material_index = f[tag_layer]

        # 5. EDGES
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
        for e in bm.edges:
            if e.is_boundary:
                e[edge_slots] = 1
            elif e.calc_face_angle(0) > 0.5:
                e[edge_slots] = 2
