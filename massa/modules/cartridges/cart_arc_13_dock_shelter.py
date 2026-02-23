import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_13: Dock Shelter",
    "id": "arc_13_dock_shelter",
    "icon": "MOD_CLOTH",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_ArcDockShelter(Massa_OT_Base):
    bl_idname = "massa.gen_arc_13_dock_shelter"
    bl_label = "ARC Dock Shelter"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("RIGID", "Rigid Frame", "Standard fixed frame shelter"),
            ("INFLATABLE", "Inflatable", "Air seal system"),
            ("CURTAIN", "Curtain Frame", "Collapsible frame"),
        ],
        default="RIGID"
    )

    # Dimensions
    width: FloatProperty(name="Overall Width", default=3.4, min=2.0)
    height: FloatProperty(name="Overall Height", default=3.6, min=2.0)
    projection: FloatProperty(name="Projection", default=0.6, min=0.2)

    # Curtains
    header_height: FloatProperty(name="Header Height", default=1.0, min=0.2)
    side_curtain_width: FloatProperty(name="Side Curt Width", default=0.6, min=0.2)

    # Details
    stripe_width: FloatProperty(name="Guide Stripe W", default=0.1, min=0.0)
    bumper_depth: FloatProperty(name="Bumper Depth", default=0.3, min=0.1)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame/Housing", "uv": "BOX", "phys": "METAL_PAINTED"},
            1: {"name": "Curtains/Seal", "uv": "BOX", "phys": "FABRIC_VINYL"},
            2: {"name": "Guide Stripes", "uv": "BOX", "phys": "PLASTIC_YELLOW"},
            3: {"name": "Bumpers", "uv": "BOX", "phys": "RUBBER_HARD"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions", icon='Length')
        col = box.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "projection")

        box = layout.box()
        box.label(text="Sealing", icon='MOD_CLOTH')
        col = box.column(align=True)
        col.prop(self, "header_height")
        col.prop(self, "side_curtain_width")
        col.prop(self, "stripe_width")

        box = layout.box()
        box.label(text="Bumpers", icon='MOD_PHYSICS')
        col = box.column(align=True)
        col.prop(self, "bumper_depth")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        w = self.width
        h = self.height
        d = self.projection

        # Clamps
        head_h = min(self.header_height, h * 0.4)
        side_w = min(self.side_curtain_width, w * 0.4)
        stripe_w = min(self.stripe_width, side_w * 0.5)
        bump_d = min(self.bumper_depth, d + 0.5)

        # Origin: Center Bottom (X=0, Z=0). Y=0 is Wall.
        # Shelter projects to -Y (Outwards)? Or +Y?
        # Standard: +Y is forward/out. Wall is at Y=0.

        # 1. Frame
        frame_thick = 0.05
        # Top Frame
        builder.create_box(w, d, frame_thick, center=Vector((0, d/2, h + frame_thick/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Side Frames (Left/Right)
        builder.create_box(frame_thick, d, h, center=Vector((-w/2 + frame_thick/2, d/2, h/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
        builder.create_box(frame_thick, d, h, center=Vector((w/2 - frame_thick/2, d/2, h/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Header Box (Front face)?
        # Usually shelter has a head frame.
        if self.style == "RIGID":
            # Header Box
            builder.create_box(w, frame_thick, head_h, center=Vector((0, d, h - head_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Side Curtains
            # Hang from Top, attached to Sides.
            curt_h = h - 0.2 # Slightly off ground

            # Left Curtain
            builder.create_box(side_w, 0.02, curt_h, center=Vector((-w/2 + side_w/2, d - 0.02, curt_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Right Curtain
            builder.create_box(side_w, 0.02, curt_h, center=Vector((w/2 - side_w/2, d - 0.02, curt_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Guide Stripes (Yellow)
            if stripe_w > 0.01:
                stripe_h = curt_h * 0.6
                stripe_z = curt_h/2

                # Left Stripe
                builder.create_box(stripe_w, 0.005, stripe_h, center=Vector((-w/2 + side_w/2, d, stripe_z)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Right Stripe
                builder.create_box(stripe_w, 0.005, stripe_h, center=Vector((w/2 - side_w/2, d, stripe_z)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        elif self.style == "INFLATABLE":
            # Bags instead of curtains
            bag_rad = side_w

            # Top Bag
            builder.create_cylinder(radius=head_h/2, depth=w - 0.2, center=Vector((0, d, h - head_h/2)))
            builder.rotate(90, axis='Y')

            # Fix UVs on cylinder
            builder.bm.normal_update()
            all_faces = builder.active_faces[:]
            caps = [f for f in all_faces if abs(f.normal.x) > 0.9]
            walls = [f for f in all_faces if f not in caps]
            builder.active_faces = all_faces
            builder.tag_slot(1)
            if caps:
                builder.active_faces = caps
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls:
                builder.active_faces = walls
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

            # Side Bags
            # Vertical cylinders
            bag_h = h - head_h
            builder.create_cylinder(radius=side_w/2, depth=bag_h, center=Vector((-w/2 + side_w/2, d, bag_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='CYLINDER') # Z axis default

            builder.create_cylinder(radius=side_w/2, depth=bag_h, center=Vector((w/2 - side_w/2, d, bag_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        elif self.style == "CURTAIN":
            # Collapsible Frame (X-frame scissors?)
            # Just create visible struts on the side
            strut_thick = 0.05
            builder.create_box(strut_thick, d, strut_thick, center=Vector((-w/2, d/2, h/2)))
            builder.rotate(45, axis='X') # Fake scissor
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            builder.create_box(strut_thick, d, strut_thick, center=Vector((w/2, d/2, h/2)))
            builder.rotate(45, axis='X')
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Curtains same as Rigid but thinner/wavier?
            # Use Rigid logic for simplicity
            builder.create_box(w, 0.01, head_h, center=Vector((0, d, h - head_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            builder.create_box(side_w, 0.01, h, center=Vector((-w/2 + side_w/2, d, h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            builder.create_box(side_w, 0.01, h, center=Vector((w/2 - side_w/2, d, h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 2. Bumpers (Bottom)
        # Rectangular blocks
        bump_h = 0.5
        bump_w = 0.25

        # Left Bumper
        builder.create_box(bump_w, bump_d, bump_h, center=Vector((-w/2 + bump_w/2, bump_d/2, bump_h/2)))
        builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Right Bumper
        builder.create_box(bump_w, bump_d, bump_h, center=Vector((w/2 - bump_w/2, bump_d/2, bump_h/2)))
        builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 4. Sockets
        # Base
        builder.select_faces_by_normal(Vector((0,0,-1)))
        bases = [f for f in builder.active_faces if abs(f.calc_center_median().z) < 0.1]
        builder.active_faces = bases
        builder.tag_socket(9)

        builder.clean()

    def execute(self, context):
        return super().execute(context)
