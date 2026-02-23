import bpy
import bmesh
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ..massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_17: Parking Meter",
    "id": "urb_17_parking_meter",
    "icon": "MESH_CYLINDER",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
    },
}

class MASSA_OT_UrbParkingMeter(Massa_OT_Base):
    bl_idname = "massa.gen_urb_17_parking_meter"
    bl_label = "URB_17: Parking Meter"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    style: EnumProperty(
        name="Style",
        items=[
            ("SINGLE_HEAD", "Single Head", "Classic single meter"),
            ("DUAL_HEAD", "Dual Head", "Classic dual meter"),
            ("PAY_STATION", "Pay Station", "Modern solar pay station"),
        ],
        default="SINGLE_HEAD",
    )

    height: FloatProperty(name="Height", default=1.5, min=1.0)
    head_width: FloatProperty(name="Head Width", default=0.2, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Pole/Body", "uv": "CYLINDER", "phys": "METAL_IRON"},
            1: {"name": "Head/Casing", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            2: {"name": "Details", "uv": "BOX", "phys": "PLASTIC"},
            3: {"name": "Screen/Lens", "uv": "SKIP", "phys": "GLASS"},
            9: {"name": "Socket Anchor", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")
        col = layout.column(align=True)
        col.prop(self, "height")
        if self.style != "PAY_STATION":
            col.prop(self, "head_width")

    def build_shape(self, bm: bmesh.types.BMesh):
        builder = MassaBuilder(bm)

        h = self.height
        hw = self.head_width

        if self.style == "SINGLE_HEAD":
            # Pole
            builder.create_cylinder(radius=0.05, depth=h * 0.8, segments=12) \
                   .tag_slot(0) \
                   .translate(0, 0, h * 0.4) # Move up so base is at 0

            # Head
            # We can create a new primitive at the top or extrude
            # Let's create a new box at the top location
            top_z = h * 0.8
            builder.create_box(hw, hw * 0.6, hw * 1.5, center=(0, 0, top_z + hw * 0.75)) \
                   .tag_slot(1) \
                   .select_faces_by_normal(Vector((0, -1, 0))) \
                   .inset(0.02, relative=False) \
                   .tag_slot(3) \
                   .tag_uvs(projection='FIT') # Screen

        elif self.style == "DUAL_HEAD":
            # Pole
            builder.create_cylinder(radius=0.05, depth=h * 0.8, segments=12) \
                   .tag_slot(0) \
                   .translate(0, 0, h * 0.4)

            # T-Bar
            top_z = h * 0.8
            builder.create_box(hw * 2.5, 0.05, 0.05, center=(0, 0, top_z)) \
                   .tag_slot(0)

            # Left Head
            builder.create_box(hw, hw * 0.6, hw * 1.2, center=(-hw, 0, top_z + hw * 0.6)) \
                   .tag_slot(1) \
                   .select_faces_by_normal(Vector((0, -1, 0))) \
                   .inset(0.02, relative=False) \
                   .tag_slot(3) \
                   .tag_uvs(projection='FIT')

            # Right Head
            builder.create_box(hw, hw * 0.6, hw * 1.2, center=(hw, 0, top_z + hw * 0.6)) \
                   .tag_slot(1) \
                   .select_faces_by_normal(Vector((0, -1, 0))) \
                   .inset(0.02, relative=False) \
                   .tag_slot(3) \
                   .tag_uvs(projection='FIT')

        elif self.style == "PAY_STATION":
            # Rectangular Body
            w, d = 0.4, 0.3
            builder.create_box(w, d, h, center=(0, 0, h/2)) \
                   .tag_slot(0) # Body

            # Screen Area
            builder.select_faces_by_normal(Vector((0, -1, 0))) \
                   .select_faces_by_height(min_z=h*0.6, max_z=h*0.8) \
                   .inset(0.05, relative=False) \
                   .tag_slot(3) \
                   .tag_uvs(projection='FIT') \
                   .extrude(-0.02)

            # Solar Panel Top
            builder.select_faces_by_normal(Vector((0, 0, 1))) \
                   .extrude(0.05) \
                   .inset(0.05, relative=False) \
                   .tag_slot(3) \
                   .tag_uvs(projection='FIT') \
                   .extrude(0.02)

        # 3. TAG ANCHOR (Bottom Z=0)
        # Assuming we built from Z=0 up or centered.
        # Let's find lowest face.
        builder.select_faces_by_height(min_z=-0.1, max_z=0.1) \
               .select_faces_by_normal(Vector((0, 0, -1))) \
               .tag_slot(9) \
               .tag_socket(9)
