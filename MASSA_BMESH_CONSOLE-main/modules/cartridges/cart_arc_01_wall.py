import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_01: Parametric Wall",
    "id": "arc_01_wall",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False, # Volumetric
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcWall(Massa_OT_Base):
    bl_idname = "massa.gen_arc_01_wall"
    bl_label = "ARC Wall"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    wall_length: FloatProperty(name="Length", default=4.0, min=0.1)
    wall_height: FloatProperty(name="Height", default=3.0, min=0.1)
    wall_thick: FloatProperty(name="Thickness", default=0.2, min=0.01)

    # Hole Parameters (Window/Door)
    hole_enable: BoolProperty(name="Enable Hole", default=False)
    hole_x: FloatProperty(name="Hole X", default=2.0)
    hole_z: FloatProperty(name="Hole Z", default=1.0)
    hole_width: FloatProperty(name="Hole Width", default=1.0)
    hole_height: FloatProperty(name="Hole Height", default=1.5)

    # Baseboard
    baseboard_height: FloatProperty(name="Baseboard H", default=0.15, min=0.0)
    baseboard_depth: FloatProperty(name="Baseboard D", default=0.02, min=0.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Wall Plaster", "uv": "BOX", "phys": "CONCRETE"},
            2: {"name": "Trim", "uv": "BOX", "phys": "WOOD"},  # Baseboard
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        l = self.wall_length
        h = self.wall_height
        t = self.wall_thick

        # Determine segments (Wall Panels)
        rects = []

        if self.hole_enable:
            hx = self.hole_x
            hz = self.hole_z
            hw = self.hole_width
            hh = self.hole_height

            x1 = hx - hw/2
            x2 = hx + hw/2
            z1 = hz - hh/2
            z2 = hz + hh/2

            # Clamp hole
            if x1 < 0: x1 = 0
            if x2 > l: x2 = l
            if z1 < 0: z1 = 0
            if z2 > h: z2 = h

            # Left Panel
            if x1 > 0.001:
                rects.append({'x': 0, 'w': x1, 'z': 0, 'h': h})

            # Right Panel
            if x2 < l - 0.001:
                rects.append({'x': x2, 'w': l - x2, 'z': 0, 'h': h})

            # Bottom Panel (under hole)
            if z1 > 0.001 and (x2 - x1) > 0.001:
                rects.append({'x': x1, 'w': x2-x1, 'z': 0, 'h': z1})

            # Top Panel (above hole)
            if z2 < h - 0.001 and (x2 - x1) > 0.001:
                rects.append({'x': x1, 'w': x2-x1, 'z': z2, 'h': h - z2})

        else:
            rects.append({'x': 0, 'w': l, 'z': 0, 'h': h})

        # Build Wall Segments
        uv_s0 = getattr(self, "uv_scale_0", 1.0)

        for r in rects:
            if r['w'] <= 0.001 or r['h'] <= 0.001: continue

            cx = r['x'] + r['w']/2
            cz = r['z'] + r['h']/2
            cy = t/2

            builder.create_box(r['w'], t, r['h']) \
                   .translate(cx, cy, cz) \
                   .tag_slot(0) \
                   .tag_uvs(uv_s0, 'BOX')

        # Build Baseboards
        bh = self.baseboard_height
        bd = self.baseboard_depth

        if bh > 0.001:
            bb_rects = []

            # Check hole overlap
            hole_cuts = False
            if self.hole_enable:
                hz = self.hole_z
                hh = self.hole_height
                z1 = hz - hh/2
                if z1 < bh:
                    # Hole cuts baseboard
                    hx = self.hole_x
                    hw = self.hole_width
                    x1 = hx - hw/2
                    x2 = hx + hw/2

                    if x1 > 0.001:
                        bb_rects.append({'x': 0, 'w': x1})
                    if x2 < l - 0.001:
                        bb_rects.append({'x': x2, 'w': l - x2})
                else:
                    # Hole is above baseboard
                    bb_rects.append({'x': 0, 'w': l})
            else:
                bb_rects.append({'x': 0, 'w': l})

            uv_s2 = getattr(self, "uv_scale_2", 1.0)

            for r in bb_rects:
                if r['w'] <= 0.001: continue

                cx = r['x'] + r['w']/2
                cz = bh/2

                # Front Baseboard (Y = -bd/2)
                builder.create_box(r['w'], bd, bh) \
                       .translate(cx, -bd/2, cz) \
                       .tag_slot(2) \
                       .tag_uvs(uv_s2, 'BOX')

                # Back Baseboard (Y = t + bd/2)
                builder.create_box(r['w'], bd, bh) \
                       .translate(cx, t + bd/2, cz) \
                       .tag_slot(2) \
                       .tag_uvs(uv_s2, 'BOX')

        # Sockets
        # Start (x=0)
        builder.create_grid(size=0.5) \
               .rotate(90, 'Y') \
               .translate(0, t/2, h/2) \
               .tag_slot(9) \
               .tag_socket(1)

        # End (x=l)
        builder.create_grid(size=0.5) \
               .rotate(90, 'Y') \
               .translate(l, t/2, h/2) \
               .tag_slot(9) \
               .tag_socket(2)

        builder.clean()

    def draw_shape_ui(self, layout):
        box_dim = layout.box()
        box_dim.label(text="Dimensions", icon='MESH_CUBE')
        col = box_dim.column(align=True)
        col.prop(self, "wall_length")
        col.prop(self, "wall_height")
        col.prop(self, "wall_thick")

        box_hole = layout.box()
        box_hole.label(text="Opening", icon='MOD_BOOLEAN')
        col = box_hole.column(align=True)
        col.prop(self, "hole_enable", toggle=True)
        if self.hole_enable:
            col.prop(self, "hole_x")
            col.prop(self, "hole_z")
            col.prop(self, "hole_width")
            col.prop(self, "hole_height")

        box_trim = layout.box()
        box_trim.label(text="Baseboard", icon='MOD_BUILD')
        col = box_trim.column(align=True)
        col.prop(self, "baseboard_height")
        col.prop(self, "baseboard_depth")
