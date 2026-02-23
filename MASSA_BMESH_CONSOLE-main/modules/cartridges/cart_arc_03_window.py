import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_03: Curtain Wall",
    "id": "arc_03_window",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcWindow(Massa_OT_Base):
    bl_idname = "massa.gen_arc_03_window"
    bl_label = "ARC Window"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    win_width: FloatProperty(name="Width", default=2.0, min=0.1)
    win_height: FloatProperty(name="Height", default=2.5, min=0.1)

    # Grid
    mullion_x: IntProperty(name="Mullion X", default=2, min=1)
    mullion_y: IntProperty(name="Mullion Y", default=3, min=1)
    frame_width: FloatProperty(name="Frame Width", default=0.1, min=0.01)
    mullion_thick: FloatProperty(name="Frame Depth", default=0.1, min=0.01)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            3: {"name": "Glass", "uv": "FIT", "phys": "GLASS"}, # Fit UVs
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        builder = MassaBuilder(bm)
        
        W = self.win_width
        H = self.win_height
        
        cols = self.mullion_x
        rows = self.mullion_y

        ft = self.frame_width
        fd = self.mullion_thick

        # Calculate Pane Sizes
        # W = (cols * pane_w) + (cols + 1) * ft
        # pane_w = (W - (cols+1)*ft) / cols

        if W <= (cols + 1) * ft:
            pane_w = 0.001
        else:
            pane_w = (W - (cols + 1) * ft) / cols

        if H <= (rows + 1) * ft:
            pane_h = 0.001
        else:
            pane_h = (H - (rows + 1) * ft) / rows

        uv_s0 = getattr(self, "uv_scale_0", 1.0)

        # 1. Vertical Mullions
        for i in range(cols + 1):
            x_left = i * (pane_w + ft)
            cx = x_left + ft/2

            builder.create_box(ft, fd, H) \
                   .translate(cx, fd/2, H/2) \
                   .tag_slot(0) \
                   .tag_uvs(uv_s0, 'BOX')

        # 2. Horizontal Transoms (Segments)
        for j in range(rows + 1):
            z_bot = j * (pane_h + ft)
            cz = z_bot + ft/2

            for i in range(cols):
                px = (i * (pane_w + ft)) + ft + pane_w/2

                builder.create_box(pane_w, fd, ft) \
                       .translate(px, fd/2, cz) \
                       .tag_slot(0) \
                       .tag_uvs(uv_s0, 'BOX')

        # 3. Glass Panes
        gt = 0.02 # Glass Thickness
        for i in range(cols):
            for j in range(rows):
                px = (i * (pane_w + ft)) + ft + pane_w/2
                pz = (j * (pane_h + ft)) + ft + pane_h/2

                builder.create_box(pane_w, gt, pane_h) \
                       .translate(px, fd/2, pz) \
                       .tag_slot(3) \
                       .tag_uvs(1.0, 'FIT')
        
        # 4. Sockets
        # Center of window
        builder.create_grid(size=0.5) \
               .rotate(90, 'X') \
               .translate(W/2, 0, H/2) \
               .tag_slot(9) \
               .tag_socket(1)

        builder.clean()

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Configuration", icon='MESH_GRID')
        col = box.column(align=True)
        col.prop(self, "win_width")
        col.prop(self, "win_height")

        box_grid = layout.box()
        box_grid.label(text="Grid & Frame", icon='MOD_WIREFRAME')
        col = box_grid.column(align=True)
        col.prop(self, "mullion_x")
        col.prop(self, "mullion_y")
        col.prop(self, "frame_width")
        col.prop(self, "mullion_thick")
