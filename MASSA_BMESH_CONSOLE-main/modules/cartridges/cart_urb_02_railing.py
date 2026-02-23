import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_02: Railing",
    "id": "urb_02_railing",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbRailing(Massa_OT_Base):
    bl_idname = "massa.gen_urb_02_railing"
    bl_label = "URB Railing"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=2.0, min=0.5)
    height: FloatProperty(name="Height", default=1.1, min=0.5)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("MODERN", "Modern", "Horizontal Cables/Bars"),
            ("ORNATE", "Ornate", "Classic Vertical Pickets"),
            ("INDUSTRIAL", "Industrial", "Pipe Railing"),
        ],
        default="MODERN"
    )

    # Details
    post_spacing: FloatProperty(name="Post Spacing", default=1.5, min=0.5)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Metal", "uv": "SKIP", "phys": "METAL_CHROME"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "length")
        col.prop(self, "height")
        col.prop(self, "post_spacing")

    def build_shape(self, bm):
        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        l = self.length
        h = self.height

        # Calculate Posts
        num_posts = int(l / self.post_spacing) + 1
        if num_posts < 2: num_posts = 2

        spacing = l / (num_posts - 1)
        start_y = -l/2

        # 1. Posts
        post_size = 0.05

        for i in range(num_posts):
            y = start_y + i * spacing
            if self.style == 'INDUSTRIAL':
                # Round Posts
                builder.create_cylinder(radius=post_size/2, depth=h, segments=12, center=Vector((0, y, h/2)))
            else:
                # Square Posts
                builder.create_box(post_size, post_size, h, center=Vector((0, y, h/2)))

            builder.tag_slot(0)

        # 2. Rails / Infill
        if self.style == 'MODERN':
            # Top Handrail (Rectangular or Round)
            builder.create_box(0.08, l, 0.03, center=Vector((0, 0, h)))
            builder.tag_slot(0)

            # Horizontal Cables (Thin cylinders)
            num_cables = 4
            cable_rad = 0.005

            # Rotate for Y-alignment
            rot = Matrix.Rotation(math.radians(90), 4, 'X')

            for i in range(num_cables):
                z = 0.2 + (i / num_cables) * (h - 0.3)
                # create_cylinder is Z aligned. Rotate X 90 -> Y aligned.
                builder.create_cylinder(radius=cable_rad, depth=l, segments=6, center=Vector((0,0,0)))
                builder.transform(rot)
                builder.translate(0, 0, z)
                builder.tag_slot(0)

        elif self.style == 'ORNATE':
            # Top and Bottom Rails
            rail_size = 0.04
            builder.create_box(rail_size, l, rail_size, center=Vector((0, 0, h - 0.05)))
            builder.tag_slot(0)
            builder.create_box(rail_size, l, rail_size, center=Vector((0, 0, 0.1)))
            builder.tag_slot(0)

            # Vertical Pickets
            picket_gap = 0.12
            num_pickets = int(l / picket_gap)
            p_step = l / num_pickets
            p_size = 0.015

            for i in range(num_pickets):
                y = start_y + i * p_step + p_step/2
                builder.create_box(p_size, p_size, h - 0.2, center=Vector((0, y, h/2)))
                builder.tag_slot(0)

        elif self.style == 'INDUSTRIAL':
            # Top Pipe
            pipe_rad = 0.03
            rot = Matrix.Rotation(math.radians(90), 4, 'X')

            builder.create_cylinder(radius=pipe_rad, depth=l, segments=8, center=Vector((0,0,0)))
            builder.transform(rot)
            builder.translate(0, 0, h)
            builder.tag_slot(0)

            # Mid Pipe
            builder.create_cylinder(radius=pipe_rad, depth=l, segments=8, center=Vector((0,0,0)))
            builder.transform(rot)
            builder.translate(0, 0, h/2)
            builder.tag_slot(0)

        # 3. Sockets
        # Ends of Posts (-L/2, +L/2) at Bottom?
        # Usually attach to floor.
        # So Bottom faces of posts.
        
        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.1)
        # Filter for bottom of posts (Z ~ 0)
        valid = [f for f in builder.active_faces if abs(f.calc_center_median().z) < 0.1]
        builder.active_faces = valid
        builder.tag_socket(9).tag_slot(9)

        # Also Side connections? Railing to Railing.
        # Ends of top rail.
        # Normals +/- Y.
        builder.select_faces_by_normal(Vector((0, -1, 0)), tolerance=0.1)
        # Filter near ends
        valid = [f for f in builder.active_faces if abs(f.calc_center_median().y + l/2) < 0.1]
        builder.active_faces = valid
        builder.tag_socket(9).tag_slot(9)

        builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.1)
        valid = [f for f in builder.active_faces if abs(f.calc_center_median().y - l/2) < 0.1]
        builder.active_faces = valid
        builder.tag_socket(9).tag_slot(9)

        # 4. Manual UVs
        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        builder._update()
