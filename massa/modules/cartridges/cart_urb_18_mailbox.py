import bpy
import bmesh
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ..massa_builder import MassaBuilder
import math

CARTRIDGE_META = {
    "name": "URB_18: Mailbox",
    "id": "urb_18_mailbox",
    "icon": "MESH_CUBE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_UrbMailbox(Massa_OT_Base):
    bl_idname = "massa.gen_urb_18_mailbox"
    bl_label = "URB_18: Mailbox"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    style: EnumProperty(
        name="Style",
        items=[
            ("STANDARD_BLUE", "Standard Blue", "Classic street mailbox"),
            ("WALL_MOUNT", "Wall Mount", "Residential wall box"),
            ("CLUSTER_BOX", "Cluster Box", "Multi-unit pedestal"),
        ],
        default="STANDARD_BLUE",
    )

    width: FloatProperty(name="Width", default=0.6, min=0.3)
    depth: FloatProperty(name="Depth", default=0.6, min=0.3)
    height: FloatProperty(name="Height", default=1.2, min=0.5)

    def get_slot_meta(self):
        return {
            0: {"name": "Body", "uv": "BOX", "phys": "METAL_IRON"},
            1: {"name": "Flap/Lid", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            2: {"name": "Legs/Base", "uv": "CYLINDER", "phys": "CONCRETE"},
            3: {"name": "Detail", "uv": "BOX", "phys": "PLASTIC"},
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

        if self.style == "STANDARD_BLUE":
            # Legs
            leg_h = h * 0.3
            builder.create_cylinder(radius=w*0.3, depth=leg_h, segments=8, center=(0,0,leg_h/2)) \
                   .tag_slot(2) # Legs

            # Box Body (Box + Cylinder Top)
            box_h = h * 0.4
            # We want a curved top.
            # Create a box for the bottom part
            box_center_z = leg_h + box_h/2
            builder.create_box(w, d, box_h, center=(0, 0, box_center_z)) \
                   .tag_slot(0) # Body

            # Curved Top: Cylinder rotated on X axis
            # Radius = w/2? Or d/2? Depth is usually the curved part axis for mailboxes.
            # For standard blue box, the curve is front-to-back? No, top is usually curved side-to-side or front-to-back depending on design.
            # USPS boxes have a curved top (front-to-back arch).
            # So cylinder axis is X.

            radius = d / 2.0
            # Center of cylinder should be at top of box
            cyl_z = leg_h + box_h

            # Manual Cylinder creation for top arch
            # Or just use a box and bevel? No bevel in MassaBuilder easily.
            # Let's use a box for the top and just chamfer it manually if we could,
            # or just put a half-cylinder on top.

            # Create horizontal cylinder along X axis? No, along Y axis (front to back arch)?
            # If arch is side-to-side (like a tunnel), axis is Y.
            # If arch is front-to-back, axis is X.
            # USPS boxes are usually rectangular with a slight dome.
            # Let's simplify: A box with a pyramid top (chamfered).

            # Add Top Cap
            builder.select_faces_by_height(min_z=cyl_z - 0.01) \
                   .select_faces_by_normal(Vector((0, 0, 1))) \
                   .extrude(h * 0.2) \
                   .scale(0.8, 0.8, 1.0) \
                   .tag_slot(0)

            # Flap / Slot
            builder.select_faces_by_normal(Vector((0, -1, 0))) \
                   .select_faces_by_height(min_z=leg_h + box_h*0.5) \
                   .inset(0.05, relative=False) \
                   .tag_slot(1) \
                   .extrude(0.02)

        elif self.style == "WALL_MOUNT":
            # Flat box
            builder.create_box(w, d*0.3, h*0.5, center=(0, 0, h*0.5)) \
                   .tag_slot(0)

            # Lid on top
            builder.select_faces_by_normal(Vector((0, 0, 1))) \
                   .extrude(0.02) \
                   .tag_slot(1) \
                   .translate(0, -0.01, 0) # Overhang front

        elif self.style == "CLUSTER_BOX":
            # Pedestal
            ped_h = h * 0.3
            builder.create_cylinder(radius=w*0.15, depth=ped_h, segments=8, center=(0,0,ped_h/2)) \
                   .tag_slot(2)

            # Main Cabinet
            cab_h = h * 0.7
            builder.create_box(w, d, cab_h, center=(0, 0, ped_h + cab_h/2)) \
                   .tag_slot(0)

            # Grid of doors (simulated by texture usually, but we can inset main face)
            builder.select_faces_by_normal(Vector((0, -1, 0))) \
                   .inset(0.05, relative=False) \
                   .tag_slot(1) \
                   .tag_uvs(projection='BOX')

            # Roof Cap
            builder.select_faces_by_normal(Vector((0, 0, 1))) \
                   .extrude(0.05) \
                   .scale(1.1, 1.1, 1.0) \
                   .tag_slot(1)

        # Tag Anchor
        builder.select_faces_by_height(min_z=-0.1, max_z=0.1) \
               .select_faces_by_normal(Vector((0, 0, -1))) \
               .tag_slot(9) \
               .tag_socket(9)
