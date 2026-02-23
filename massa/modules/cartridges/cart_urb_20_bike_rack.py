import bpy
import bmesh
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ..massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_20: Bike Rack",
    "id": "urb_20_bike_rack",
    "icon": "MESH_CYLINDER",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_UrbBikeRack(Massa_OT_Base):
    bl_idname = "massa.gen_urb_20_bike_rack"
    bl_label = "URB_20: Bike Rack"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    style: EnumProperty(
        name="Style",
        items=[
            ("U_RACK", "Inverted U", "Simple architectural staple"),
            ("WAVE", "Wave / Ribbon", "Continuous metal loop"),
            ("GRID", "Grid / Toast", "Floor mounted slots"),
        ],
        default="U_RACK",
    )

    length: FloatProperty(name="Length", default=2.0, min=0.5)
    width: FloatProperty(name="Width", default=0.6, min=0.2) # Rack Depth/Width
    height: FloatProperty(name="Height", default=0.8, min=0.5)

    tube_radius: FloatProperty(name="Tube Radius", default=0.03, min=0.01)

    def get_slot_meta(self):
        return {
            0: {"name": "Metal", "uv": "CYLINDER", "phys": "METAL_STEEL"},
            1: {"name": "Base/Mount", "uv": "BOX", "phys": "CONCRETE"},
            9: {"name": "Socket Anchor", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")
        layout.prop(self, "tube_radius")

    def build_shape(self, bm: bmesh.types.BMesh):
        builder = MassaBuilder(bm)

        l, w, h = self.length, self.width, self.height
        r = self.tube_radius

        if self.style == "U_RACK":
            # Just one U? Usually these are placed in series.
            # If "Length" is 2.0, maybe we place multiple U's?
            # Let's place (Length / 1.0) U-Racks.
            count = int(l / 1.0)
            if count < 1: count = 1

            spacing = l / count
            start_x = -l/2 + spacing/2

            for i in range(count):
                cx = start_x + i * spacing
                # Left Leg
                builder.create_cylinder(radius=r, depth=h, segments=8, center=(cx, -w/2, h/2)) \
                       .tag_slot(0)
                # Right Leg
                builder.create_cylinder(radius=r, depth=h, segments=8, center=(cx, w/2, h/2)) \
                       .tag_slot(0)
                # Top Bar (Square connect for now)
                builder.create_box(r*2, w, r*2, center=(cx, 0, h)) \
                       .tag_slot(0)

                # Base Plates
                builder.create_cylinder(radius=r*2, depth=0.02, segments=8, center=(cx, -w/2, 0.01)) \
                       .tag_slot(1)
                builder.create_cylinder(radius=r*2, depth=0.02, segments=8, center=(cx, w/2, 0.01)) \
                       .tag_slot(1)

        elif self.style == "WAVE":
            # Angular Wave: Up, Down, Up, Down along X
            # Points: (0,0,0) -> (0.2, 0, h) -> (0.4, 0, 0) ...
            # Actually easier to just make vertical posts and connect them diagonally?
            # Or just a series of U's connected.
            # Let's do M-shape.

            # Points count
            peaks = int(l / 0.4)
            if peaks < 2: peaks = 2
            step = l / peaks

            # Draw as a "Ribbon" using thick edges? No, volumetric.
            # Create a sequence of cylinders.

            # Just do vertical posts for now as simple "Bollard" style wave?
            # No, a Wave rack is a continuous pipe.
            # Since we lack specific path extrusion, we'll approximate with vertical and horizontal segments.
            # Segmented Arch:
            # |__|__|

            x = -l/2
            for i in range(peaks):
                # Vertical Up
                builder.create_cylinder(radius=r, depth=h, segments=8, center=(x, 0, h/2)) \
                       .tag_slot(0)

                # Top Horizontal to next
                next_x = x + step
                if i < peaks - 1:
                    center_x = (x + next_x) / 2
                    builder.create_box(step, r*2, r*2, center=(center_x, 0, h)) \
                           .tag_slot(0)

                x = next_x

        elif self.style == "GRID":
            # Floor frame
            # Side rails
            builder.create_box(l, r*2, r*2, center=(0, -w/2, r)) \
                   .tag_slot(1) # Base
            builder.create_box(l, r*2, r*2, center=(0, w/2, r)) \
                   .tag_slot(1) # Base

            # Cross bars (Wheel slots)
            slot_count = int(l / 0.3)
            step = l / slot_count
            x = -l/2 + step/2

            for i in range(slot_count):
                # Vertical loops for wheel
                # Left Vertical
                builder.create_cylinder(radius=r*0.8, depth=h*0.6, segments=8, center=(x, -w/4, h*0.3)) \
                       .tag_slot(0)
                # Right Vertical
                builder.create_cylinder(radius=r*0.8, depth=h*0.6, segments=8, center=(x, w/4, h*0.3)) \
                       .tag_slot(0)
                # Top
                builder.create_box(r*1.6, w/2, r*1.6, center=(x, 0, h*0.6)) \
                       .tag_slot(0)

                x += step

        # Anchor
        builder.select_faces_by_height(min_z=-0.1, max_z=0.1) \
               .select_faces_by_normal(Vector((0, 0, -1))) \
               .tag_slot(9) \
               .tag_socket(9)
