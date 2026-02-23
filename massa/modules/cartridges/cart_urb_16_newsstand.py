import bpy
import bmesh
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ..massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_16: Newsstand",
    "id": "urb_16_newsstand",
    "icon": "MESH_CUBE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_UrbNewsstand(Massa_OT_Base):
    bl_idname = "massa.gen_urb_16_newsstand"
    bl_label = "URB_16: Newsstand"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    style: EnumProperty(
        name="Style",
        items=[
            ("STANDARD", "Standard", "Classic rectangular newsstand"),
            ("MODERN", "Modern", "Sleek glass and metal design"),
            ("KIOSK", "Kiosk", "Hexagonal stand"),
        ],
        default="STANDARD",
    )

    width: FloatProperty(name="Width", default=2.0, min=0.5)
    depth: FloatProperty(name="Depth", default=1.5, min=0.5)
    height: FloatProperty(name="Height", default=2.2, min=1.0)

    roof_overhang: FloatProperty(name="Roof Overhang", default=0.2, min=0.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Body", "uv": "BOX", "phys": "WOOD"},
            1: {"name": "Trim/Roof", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            2: {"name": "Interior", "uv": "BOX", "phys": "WOOD"},
            3: {"name": "Glass", "uv": "SKIP", "phys": "GLASS"}, # Use FIT projection manually
            9: {"name": "Socket Anchor", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")
        layout.prop(self, "roof_overhang")

    def build_shape(self, bm: bmesh.types.BMesh):
        builder = MassaBuilder(bm)

        w, d, h = self.width, self.depth, self.height

        # 1. ANCHOR SOCKET (Bottom Center)
        # Create a tiny invisible plane or just tag the bottom face of the main shape later.
        # We'll tag the bottom of the main shape.

        if self.style == "STANDARD":
            self.build_standard(builder, w, d, h)
        elif self.style == "MODERN":
            self.build_modern(builder, w, d, h)
        elif self.style == "KIOSK":
            self.build_kiosk(builder, w, d, h)

        # 2. FINAL CLEANUP & SOCKETS
        # Tag Bottom as Anchor (Slot 9)
        builder.select_faces_by_normal(Vector((0, 0, -1))).tag_slot(9).tag_socket(9)

    def build_standard(self, builder, w, d, h):
        # Main Box
        builder.create_box(w, d, h).tag_slot(0) # Body

        # Front Opening (Inset & Extrude In)
        # Front is usually -Y in Blender standard (or +Y). Let's assume -Y is front.
        # Architecture standard: usually Y is Depth.

        # Select Front Face (-Y)
        builder.select_faces_by_normal(Vector((0, -1, 0)))
        builder.inset(0.1, relative=False).tag_slot(1) # Trim Frame
        builder.extrude(-d * 0.8).tag_slot(2) # Interior

        # Roof
        builder.select_faces_by_normal(Vector((0, 0, 1)))
        builder.extrude(0.1).tag_slot(1).inset(-self.roof_overhang, relative=False).extrude(0.05).tag_slot(1)

    def build_modern(self, builder, w, d, h):
        # Frame Structure
        builder.create_box(w, d, h).tag_slot(1) # Metal Frame

        # Glass Panels (Front and Sides)
        # Front (-Y)
        builder.select_faces_by_normal(Vector((0, -1, 0)))
        builder.inset(0.05, relative=False).tag_slot(3).tag_uvs(projection='FIT')

        # Side (-X)
        builder.select_faces_by_normal(Vector((-1, 0, 0)))
        builder.inset(0.05, relative=False).tag_slot(3).tag_uvs(projection='FIT')

        # Side (+X)
        builder.select_faces_by_normal(Vector((1, 0, 0)))
        builder.inset(0.05, relative=False).tag_slot(3).tag_uvs(projection='FIT')

        # Simple Flat Roof
        builder.select_faces_by_normal(Vector((0, 0, 1)))
        builder.extrude(0.05).inset(-0.1, relative=False).tag_slot(1)

    def build_kiosk(self, builder, w, d, h):
        # Hexagonal Cylinder
        radius = w / 2.0
        builder.create_cylinder(radius=radius, depth=h, segments=6).tag_slot(0) # Body

        # Opening on one face (Hexagon faces are at angles)
        # Face normals: (1,0), (0.5, 0.866), (-0.5, 0.866), (-1,0)...
        # Let's select by facing -Y.

        builder.select_faces_by_normal(Vector((0, -1, 0)), tolerance=0.5)
        builder.inset(0.1, relative=False).tag_slot(1).extrude(-radius * 0.5).tag_slot(2) # Interior

        # Conical Roof
        builder.select_faces_by_normal(Vector((0, 0, 1)))
        builder.extrude(0.1).tag_slot(1).inset(-self.roof_overhang, relative=False).extrude(0.5).scale(0.1, 0.1, 1.0).tag_slot(1)
