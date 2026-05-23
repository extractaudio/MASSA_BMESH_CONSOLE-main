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

    # Styles
    window_style: EnumProperty(
        name="Style",
        items=[
            ("GRID", "Grid", "Standard Mullions"),
            ("PICTURE", "Picture", "Large central pane"),
            ("LOUVER", "Louver", "Horizontal Slats"),
        ],
        default="GRID"
    )

    # §3.1 — Required UV properties
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)
    fit_uvs:  BoolProperty(name="Fit UVs 0-1", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame",         "uv": "SKIP", "phys": "MASSA_DEBUG_1"},
            3: {"name": "Glass",         "uv": "SKIP", "phys": "MASSA_DEBUG_4"},
            4: {"name": "Louver",        "uv": "SKIP", "phys": "MASSA_DEBUG_2"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "MASSA_DEBUG_9"}
        }

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        W = self.win_width
        H = self.win_height
        ft = self.frame_width
        fd = self.mullion_thick

        if self.window_style == 'GRID':
            cols = self.mullion_x
            rows = self.mullion_y

            if W <= (cols + 1) * ft: pane_w = 0.001
            else: pane_w = (W - (cols + 1) * ft) / cols

            if H <= (rows + 1) * ft: pane_h = 0.001
            else: pane_h = (H - (rows + 1) * ft) / rows

            # 1. Vertical Mullions
            for i in range(cols + 1):
                x_left = i * (pane_w + ft)
                cx = x_left + ft/2
                builder.create_box(ft, fd, H) \
                       .translate(cx, fd/2, H/2) \
                       .tag_slot(0) \
                       .select_boundary().tag_edge_role(1)

            # 2. Horizontal Transoms
            for j in range(rows + 1):
                z_bot = j * (pane_h + ft)
                cz = z_bot + ft/2
                for i in range(cols):
                    px = (i * (pane_w + ft)) + ft + pane_w/2
                    builder.create_box(pane_w, fd, ft) \
                           .translate(px, fd/2, cz) \
                           .tag_slot(0) \
                           .select_boundary().tag_edge_role(1)

            # 3. Glass Panes
            gt = 0.02
            for i in range(cols):
                for j in range(rows):
                    px = (i * (pane_w + ft)) + ft + pane_w/2
                    pz = (j * (pane_h + ft)) + ft + pane_h/2
                    builder.create_box(pane_w, gt, pane_h) \
                           .translate(px, fd/2, pz) \
                           .tag_slot(3)

        elif self.window_style == 'PICTURE':
            # Frame Perimeter
            # Left
            builder.create_box(ft, fd, H).translate(ft/2, fd/2, H/2).tag_slot(0).select_boundary().tag_edge_role(1)
            # Right
            builder.create_box(ft, fd, H).translate(W - ft/2, fd/2, H/2).tag_slot(0).select_boundary().tag_edge_role(1)
            # Bottom
            builder.create_box(W - 2*ft, fd, ft).translate(W/2, fd/2, ft/2).tag_slot(0).select_boundary().tag_edge_role(1)
            # Top
            builder.create_box(W - 2*ft, fd, ft).translate(W/2, fd/2, H - ft/2).tag_slot(0).select_boundary().tag_edge_role(1)

            # Glass
            gt = 0.02
            builder.create_box(W - 2*ft, gt, H - 2*ft).translate(W/2, fd/2, H/2).tag_slot(3)

        elif self.window_style == 'LOUVER':
            # Frame Perimeter
            builder.create_box(ft, fd, H).translate(ft/2, fd/2, H/2).tag_slot(0).select_boundary().tag_edge_role(1)
            builder.create_box(ft, fd, H).translate(W - ft/2, fd/2, H/2).tag_slot(0).select_boundary().tag_edge_role(1)
            builder.create_box(W - 2*ft, fd, ft).translate(W/2, fd/2, ft/2).tag_slot(0).select_boundary().tag_edge_role(1)
            builder.create_box(W - 2*ft, fd, ft).translate(W/2, fd/2, H - ft/2).tag_slot(0).select_boundary().tag_edge_role(1)

            # Slats
            rows = self.mullion_y * 2
            slat_h = (H - 2*ft) / rows
            slat_d = fd * 0.8
            for j in range(rows):
                cz = ft + j * slat_h + slat_h/2
                builder.create_box(W - 2*ft, slat_d, slat_h * 0.8) \
                       .translate(W/2, fd/2, cz) \
                       .rotate(-30, 'X') \
                       .tag_slot(4) \
                       .select_boundary().tag_edge_role(1)

        # Sockets (Tag Existing Faces)
        builder.clean()

        # Center Socket (Front/Back)
        builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.1).tag_socket(1)
        builder.select_faces_by_normal(Vector((0, -1, 0)), tolerance=0.1).tag_socket(2)

        # §7.2 — Dual-mode UV pass (respects uv_scale / fit_uvs)
        uv_sc   = 1.0 if self.fit_uvs else self.uv_scale
        uv_proj = 'FIT' if self.fit_uvs else 'BOX'
        builder.select_faces_by_slot(0).tag_uvs(scale=uv_sc, projection=uv_proj)   # Frame
        builder.select_faces_by_slot(3).tag_uvs(scale=1.0, projection='FIT')        # Glass: always FIT regardless of fit_uvs
        builder.select_faces_by_slot(4).tag_uvs(scale=uv_sc, projection=uv_proj)   # Louver

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Configuration", icon='MESH_GRID')
        col = box.column(align=True)
        col.prop(self, "window_style")
        col.prop(self, "win_width")
        col.prop(self, "win_height")

        if self.window_style in {'GRID', 'LOUVER'}:
            box_grid = layout.box()
            box_grid.label(text="Grid & Frame", icon='MOD_WIREFRAME')
            col = box_grid.column(align=True)
            if self.window_style == 'GRID':
                col.prop(self, "mullion_x")
            col.prop(self, "mullion_y") # Used for louvers count too
            col.prop(self, "frame_width")
            col.prop(self, "mullion_thick")
