import bpy
import bmesh
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ..massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_19: Phone Booth",
    "id": "urb_19_phone_booth",
    "icon": "MESH_CUBE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_UrbPhoneBooth(Massa_OT_Base):
    bl_idname = "massa.gen_urb_19_phone_booth"
    bl_label = "URB_19: Phone Booth"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    style: EnumProperty(
        name="Style",
        items=[
            ("CLASSIC_RED", "Classic Red", "Iconic London style"),
            ("MODERN_GLASS", "Modern Glass", "Sleek glass enclosure"),
            ("WALL_MOUNT", "Wall Mount / Hood", "Open hood style"),
        ],
        default="CLASSIC_RED",
    )

    width: FloatProperty(name="Width", default=1.0, min=0.8)
    depth: FloatProperty(name="Depth", default=1.0, min=0.8)
    height: FloatProperty(name="Height", default=2.2, min=1.5)

    def get_slot_meta(self):
        return {
            0: {"name": "Structure", "uv": "BOX", "phys": "METAL_IRON"},
            1: {"name": "Trim/Roof", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            2: {"name": "Interior/Phone", "uv": "BOX", "phys": "PLASTIC"},
            3: {"name": "Glass", "uv": "SKIP", "phys": "GLASS"},
            9: {"name": "Socket Anchor", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")

    def build_shape(self, bm: bmesh.types.BMesh):
        builder = MassaBuilder(bm)

        w, d, h = self.width, self.depth, self.height

        if self.style == "CLASSIC_RED":
            # Main Box
            builder.create_box(w, d, h) \
                   .tag_slot(0) # Red Structure

            # Windows on 3 sides (Left, Right, Front)
            # Assuming -Y is Front
            dirs = [Vector((0, -1, 0)), Vector((-1, 0, 0)), Vector((1, 0, 0))]
            for normal in dirs:
                builder.select_faces_by_normal(normal) \
                       .inset(0.1, relative=False) \
                       .tag_slot(1) \
                       .extrude(-0.05) \
                       .tag_slot(3) \
                       .tag_uvs(projection='FIT') # Glass

            # Door (Usually Front) - Let's assume Front is open or door
            # Actually classic booths have a door.
            # Let's inset the door more

            # Roof (Domed)
            builder.select_faces_by_normal(Vector((0, 0, 1))) \
                   .extrude(0.1) \
                   .tag_slot(1) \
                   .inset(-0.1, relative=False) \
                   .extrude(0.2) \
                   .scale(0.8, 0.8, 1.0) \
                   .tag_slot(1)

        elif self.style == "MODERN_GLASS":
            # Thin Frame
            builder.create_box(w, d, h) \
                   .tag_slot(0) # Frame

            # Large Glass Panels
            dirs = [Vector((0, -1, 0)), Vector((-1, 0, 0)), Vector((1, 0, 0))]
            for normal in dirs:
                builder.select_faces_by_normal(normal) \
                       .inset(0.05, relative=False) \
                       .tag_slot(3) \
                       .tag_uvs(projection='FIT') \
                       .extrude(-0.02)

            # Flat Roof
            builder.select_faces_by_normal(Vector((0, 0, 1))) \
                   .extrude(0.05) \
                   .tag_slot(1)

        elif self.style == "WALL_MOUNT":
            # Back Panel
            builder.create_box(w, 0.1, h*0.6, center=(0, d/2, h*0.6)) \
                   .tag_slot(0)

            # Curved Hood / Canopy
            # Extrude top forward
            builder.select_faces_by_height(min_z=h*0.8) \
                   .select_faces_by_normal(Vector((0, -1, 0))) \
                   .extrude(d*0.6) \
                   .tag_slot(1) # Canopy

            # Phone Panel
            builder.select_faces_by_normal(Vector((0, -1, 0))) \
                   .inset(0.1, relative=False) \
                   .tag_slot(2) # Panel

        # Anchor
        builder.select_faces_by_height(min_z=-0.1, max_z=0.1) \
               .select_faces_by_normal(Vector((0, 0, -1))) \
               .tag_slot(9) \
               .tag_socket(9)
