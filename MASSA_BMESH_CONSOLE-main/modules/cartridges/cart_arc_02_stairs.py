import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_02: Procedural Staircase",
    "id": "arc_02_stairs",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False, # Volumetric now
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcStairs(Massa_OT_Base):
    bl_idname = "massa.gen_arc_02_stairs"
    bl_label = "ARC Stairs"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    stair_width: FloatProperty(name="Width", default=1.2, min=0.1)
    total_height: FloatProperty(name="Height", default=3.0, min=0.1)
    step_count: IntProperty(name="Count", default=12, min=1)

    # Details
    tread_depth: FloatProperty(name="Tread Depth", default=0.28, min=0.1)

    has_stringer: BoolProperty(name="Stringers", default=True)
    stringer_width: FloatProperty(name="Stringer W", default=0.05)
    stringer_offset: FloatProperty(name="Stringer Offset", default=0.05) # Vertical thickness

    def get_slot_meta(self):
        return {
            0: {"name": "Treads", "uv": "BOX", "phys": "WOOD"},
            1: {"name": "Risers", "uv": "BOX", "phys": "WOOD"},
            2: {"name": "Stringers", "uv": "BOX", "phys": "METAL_IRON"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        w = self.stair_width
        h = self.total_height
        count = self.step_count
        depth = self.tread_depth
        rise = h / count

        tread_thick = 0.05
        riser_thick = 0.02
        nosing = 0.02

        uv_s0 = getattr(self, "uv_scale_0", 1.0)
        uv_s1 = getattr(self, "uv_scale_1", 1.0)
        uv_s2 = getattr(self, "uv_scale_2", 1.0)

        # 1. Steps
        for i in range(count):
            y_pos = i * depth
            z_pos = i * rise

            # Riser (Vertical)
            # From z_pos to z_pos + rise
            builder.create_box(w, riser_thick, rise) \
                   .translate(0, y_pos + riser_thick/2, z_pos + rise/2) \
                   .tag_slot(1) \
                   .tag_uvs(uv_s1, 'BOX')

            # Tread (Horizontal)
            # Sits at z_pos + rise
            # Centers on y_pos + depth/2 (roughly)
            # We want tread front to be at y_pos + depth (+ nosing)
            # Riser is at y_pos.
            # So Tread covers y_pos to y_pos + depth.
            builder.create_box(w, depth + nosing, tread_thick) \
                   .translate(0, y_pos + (depth + nosing)/2, z_pos + rise + tread_thick/2) \
                   .tag_slot(0) \
                   .tag_uvs(uv_s0, 'BOX')

        # 2. Stringers
        if self.has_stringer:
            total_y = count * depth
            total_z = h

            vec = Vector((0, total_y, total_z))
            length = vec.length
            angle = math.atan2(total_z, total_y)

            sw = self.stringer_width
            # Beam height/depth
            sh = self.stringer_offset * 6.0
            if sh < 0.2: sh = 0.2

            # Center of the diagonal
            cy = total_y / 2
            cz = total_z / 2

            # Adjust Z to be under the steps
            # Steps are roughly on the diagonal. Stringer should support them.
            # Shift down by sh/2?
            cz_shift = cz - (sh * 0.3)

            # Left Stringer
            builder.create_box(sw, length + 0.5, sh) \
                   .rotate(math.degrees(angle), 'X') \
                   .translate(-w/2 - sw/2, cy, cz_shift) \
                   .tag_slot(2) \
                   .tag_uvs(uv_s2, 'BOX')

            # Right Stringer
            builder.create_box(sw, length + 0.5, sh) \
                   .rotate(math.degrees(angle), 'X') \
                   .translate(w/2 + sw/2, cy, cz_shift) \
                   .tag_slot(2) \
                   .tag_uvs(uv_s2, 'BOX')

        # 3. Sockets
        # Bottom
        builder.create_grid(size=0.5) \
               .rotate(90, 'X') \
               .translate(0, -0.1, 0) \
               .tag_slot(9) \
               .tag_socket(1)

        # Top
        end_y = count * depth
        builder.create_grid(size=0.5) \
               .rotate(90, 'X') \
               .translate(0, end_y + 0.1, h) \
               .tag_slot(9) \
               .tag_socket(2)

        # Cleanup
        builder.clean()

    def draw_shape_ui(self, layout):
        box_dim = layout.box()
        box_dim.label(text="Dimensions", icon='MESH_PLANE')
        col_dim = box_dim.column(align=True)
        col_dim.prop(self, "stair_width")
        col_dim.prop(self, "total_height")
        col_dim.prop(self, "step_count")

        box_det = layout.box()
        box_det.label(text="Details", icon='LINCURVE')
        col_det = box_det.column(align=True)
        col_det.prop(self, "tread_depth")

        box_str = layout.box()
        box_str.label(text="Stringers", icon='MOD_BUILD')
        col_str = box_str.column(align=True)
        col_str.prop(self, "has_stringer")
        if self.has_stringer:
            col_str.prop(self, "stringer_width")
            col_str.prop(self, "stringer_offset")
