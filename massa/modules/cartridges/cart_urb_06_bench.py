import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_06: Bench",
    "id": "urb_06_bench",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbBench(Massa_OT_Base):
    bl_idname = "massa.gen_urb_06_bench"
    bl_label = "URB Bench"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=2.0, min=0.5)
    depth: FloatProperty(name="Depth", default=0.6, min=0.3)
    height: FloatProperty(name="Height", default=0.45, min=0.2)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("STANDARD", "Standard", "Wood Slats & Metal Legs"),
            ("MODERN", "Modern", "Sleek Ribbon Design"),
            ("BLOCK", "Block", "Solid Concrete Mass"),
        ],
        default="STANDARD"
    )

    # Details
    slat_count: FloatProperty(name="Slat Count", default=5, min=1)
    leg_thickness: FloatProperty(name="Leg Thickness", default=0.1, min=0.02)
    backrest: BoolProperty(name="Has Backrest", default=False)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Seat Surface", "uv": "BOX", "phys": "WOOD_OAK"},
            1: {"name": "Frame / Legs", "uv": "BOX", "phys": "METAL_IRON"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "MASSA_DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "length")
        col.prop(self, "depth")
        col.prop(self, "height")
        layout.separator()
        if self.style == 'STANDARD':
            col.prop(self, "slat_count")
            col.prop(self, "leg_thickness")
            col.prop(self, "backrest")
        elif self.style == 'MODERN':
            col.prop(self, "leg_thickness")

    def build_shape(self, bm):
        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        l = self.length
        d = self.depth
        h = self.height

        if self.style == 'STANDARD':
            # 1. Legs (2)
            leg_w = self.leg_thickness
            leg_d = d * 0.8
            leg_h = h

            # Leg 1 (Left)
            builder.create_box(leg_w, leg_d, leg_h, center=Vector((-l/2 + leg_w, 0, h/2))) \
                   .tag_slot(1)

            # Leg 2 (Right)
            builder.create_box(leg_w, leg_d, leg_h, center=Vector((l/2 - leg_w, 0, h/2))) \
                   .tag_slot(1)

            # 2. Slats (Seat)
            # Create slats spanning the length
            slat_w = l
            slat_h = 0.05
            slat_d = (d * 0.9) / self.slat_count
            gap = (d * 0.1) / (self.slat_count + 1) if self.slat_count > 0 else 0

            start_y = -d/2 + gap + slat_d/2

            for i in range(int(self.slat_count)):
                y = start_y + i * (slat_d + gap)
                builder.create_box(slat_w, slat_d, slat_h, center=Vector((0, y, h + slat_h/2))) \
                       .tag_slot(0) # Wood

            # 3. Backrest (Optional)
            if self.backrest:
                back_h = h * 0.8
                back_support_h = h + back_h

                # Extend rear legs up? Or add supports.
                # Simplest: Add back supports attached to legs

                # Support Left
                builder.create_box(leg_w, 0.05, back_h, center=Vector((-l/2 + leg_w, d/2, h + back_h/2))) \
                       .tag_slot(1)

                # Support Right
                builder.create_box(leg_w, 0.05, back_h, center=Vector((l/2 - leg_w, d/2, h + back_h/2))) \
                       .tag_slot(1)

                # Slats for back
                # Usually 2-3 slats
                back_slat_count = 2
                back_slat_h = (back_h * 0.6) / back_slat_count
                back_start_z = h + back_h * 0.3

                for i in range(back_slat_count):
                    z = back_start_z + i * (back_slat_h + 0.05)
                    builder.create_box(l, 0.05, back_slat_h, center=Vector((0, d/2 - 0.05, z))) \
                           .tag_slot(0)

        elif self.style == 'MODERN':
            # Z-Shape or U-Shape Ribbon
            # Let's do a C-Shape extrusion

            thickness = self.leg_thickness

            # Profile in Side View (YZ)
            # Bottom, Back, Top (Seat), Front Lip?
            # Let's do a simple inverted U (Bench)

            # Top Seat
            builder.create_box(l, d, thickness, center=Vector((0, 0, h - thickness/2))) \
                   .tag_slot(0) # Seat Surface

            # Legs (Solid panels at ends)
            builder.create_box(thickness, d, h - thickness, center=Vector((-l/2 + thickness/2, 0, (h - thickness)/2))) \
                   .tag_slot(0)

            builder.create_box(thickness, d, h - thickness, center=Vector((l/2 - thickness/2, 0, (h - thickness)/2))) \
                   .tag_slot(0)

        elif self.style == 'BLOCK':
            # Solid Block
            builder.create_box(l, d, h, center=Vector((0, 0, h/2))) \
                   .tag_slot(0) # Concrete

            # Inset Base for "Floating" effect?
            # Or just Chamfer top edges

            # Select Top Face
            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1) \
                   .inset(0.05, relative=False) \
                   .tag_slot(0) # Top Surface

            # Maybe differ material?
            # No, all concrete.

        # 4. Sockets
        # Anchor (Bottom)
        # Select faces pointing DOWN and at Z ~ 0
        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.1)

        # Manually filter for height (Filter current selection)
        # Since select_faces_by_height resets selection, we filter the active_faces list directly
        builder.active_faces = [
            f for f in builder.active_faces
            if -0.1 <= f.calc_center_median().z <= 0.1
        ]

        if not builder.active_faces:
             # Fallback: Just select anything at Z=0 if normal check failed
             builder.select_faces_by_height(min_z=-0.1, max_z=0.1)

        builder.tag_socket(9).tag_slot(9) # Anchor

        # 5. UVs
        builder.select_all_faces() \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Cleanup
        builder._update()
