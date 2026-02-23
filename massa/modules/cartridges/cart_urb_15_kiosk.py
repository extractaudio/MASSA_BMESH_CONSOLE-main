import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_15: Kiosk",
    "id": "urb_15_kiosk",
    "icon": "MOD_FLUID",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbKiosk(Massa_OT_Base):
    bl_idname = "massa.gen_urb_15_kiosk"
    bl_label = "URB Kiosk"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    width: FloatProperty(name="Width", default=2.0, min=1.5)
    depth: FloatProperty(name="Depth", default=2.0, min=1.5)
    height: FloatProperty(name="Height", default=2.5, min=2.0)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("NEWSSTAND", "Newsstand", "Open Front"),
            ("VENDING", "Vending", "Enclosed with Glass"),
            ("INFO_BOOTH", "Info Booth", "Hexagonal/Octagonal"),
        ],
        default="NEWSSTAND"
    )

    # Details
    roof_overhang: FloatProperty(name="Roof Overhang", default=0.2, min=0.0)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Walls", "uv": "BOX", "phys": "CONCRETE"},
            1: {"name": "Roof", "uv": "BOX", "phys": "ROOF_TILES"},
            3: {"name": "Glass/Open", "uv": "BOX", "phys": "GLASS"},
            4: {"name": "Frame/Detail", "uv": "BOX", "phys": "METAL_DARK"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")
        col.prop(self, "roof_overhang")

    def build_shape(self, bm):
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        w = self.width
        d = self.depth
        h = self.height

        # 1. Base Geometry
        if self.style == 'INFO_BOOTH':
            # Hexagonal
            builder.create_cylinder(radius=w/2, depth=h, segments=6, center=Vector((0,0,h/2)))
            builder.tag_slot(0)
            builder.select_all_faces().tag_edge_role(1)
            # Rotate to align flat side to Y
            builder.rotate(30)
        else:
            # Box
            builder.create_box(w, d, h, center=Vector((0,0,h/2)))
            builder.tag_slot(0)
            builder.select_all_faces().tag_edge_role(1)

        # 2. Style Logic
        if self.style == 'NEWSSTAND':
            # Open Front (Y-)
            builder.select_faces_by_normal(Vector((0,-1,0))) \
                   .inset(0.1, relative=False) \
                   .extrude(-d*0.8) \
                   .tag_slot(4) \
                   .tag_edge_role(1) # Interior/Frame

            # Counter
            counter_h = 1.0
            builder.create_box(w-0.2, 0.4, 0.05, center=Vector((0, -d/2+0.2, counter_h)))
            builder.tag_slot(4)

        elif self.style == 'VENDING':
            # Glass Front
            builder.select_faces_by_normal(Vector((0,-1,0))) \
                   .inset(0.1) \
                   .extrude(-0.05) \
                   .tag_slot(4) \
                   .tag_edge_role(1) \
                   .select_faces_by_normal(Vector((0,-1,0))) \
                   .tag_slot(3) # Glass

        elif self.style == 'INFO_BOOTH':
            # Windows all around except back
            windows = [f for f in bm.faces if abs(f.normal.z) < 0.1 and f.normal.y < 0.9]
            builder.active_faces = windows
            builder.inset(0.1).extrude(-0.05).tag_slot(4).tag_edge_role(1)
            # Glass
            # Re-select "windows" faces?
            # Inset modifies faces in place or returns new ones.
            # MassaBuilder updates active_faces to new inner faces.
            # So just tag them.
            builder.tag_slot(3)

        # 3. Roof
        rw = w + self.roof_overhang*2
        rd = d + self.roof_overhang*2
        rh = 0.2

        if self.style == 'INFO_BOOTH':
            # Hex roof
            builder.create_cone(radius_bottom=rw/2, radius_top=0, depth=0.5, segments=6, center=Vector((0,0,h+0.25)))
            builder.rotate(30)
            builder.tag_slot(1)
            # Seams on cone?
            # > 6 faces. Tag seams on edges.
            builder.select_all_faces().tag_edge_role(1)
        else:
            # Flat/Slanted roof
            builder.create_box(rw, rd, rh, center=Vector((0,0,h+rh/2)))
            builder.tag_slot(1)
            builder.select_all_faces().tag_edge_role(1)

        # 4. Anchor Socket
        builder.create_box(0.1, 0.1, 0.1, center=Vector((0,0,0))) # Hidden anchor
        builder.tag_slot(9).tag_socket(9)

        # 5. UVs
        builder.select_faces_by_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
        builder.select_faces_by_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
        builder.select_faces_by_slot(3).tag_uvs(scale=1.0, projection='BOX')
        builder.select_faces_by_slot(4).tag_uvs(scale=self.uv_scale, projection='BOX')

        builder._update()
