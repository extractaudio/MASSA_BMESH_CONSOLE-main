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

    # Styles
    stair_style: EnumProperty(
        name="Style",
        items=[
            ("STANDARD", "Standard", "Treads & Stringers"),
            ("FLOATING", "Floating", "Cantilevered / Center Spine"),
            ("BOX", "Box", "Solid Concrete Steps"),
        ],
        default="STANDARD"
    )

    has_stringer: BoolProperty(name="Stringers", default=True)
    stringer_width: FloatProperty(name="Stringer W", default=0.05)
    stringer_offset: FloatProperty(name="Stringer Offset", default=0.05) # Vertical thickness

    def get_slot_meta(self):
        return {
            0: {"name": "Treads", "uv": "BOX", "phys": "DEBUG_1"},
            1: {"name": "Risers", "uv": "BOX", "phys": "DEBUG_2"},
            2: {"name": "Stringers", "uv": "BOX", "phys": "DEBUG_3"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
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

        # 1. Steps Generation based on Style
        for i in range(count):
            y_pos = i * depth
            z_pos = i * rise

            if self.stair_style == 'BOX':
                # Solid Box Step
                builder.create_box(w, depth, rise) \
                       .translate(0, y_pos + depth/2, z_pos + rise/2) \
                       .tag_slot(0) \
                       .tag_uvs(uv_s0, 'BOX') \
                       .select_boundary().tag_edge_role(1) # Perimeter

            elif self.stair_style == 'FLOATING':
                # Thick Tread Only
                thick_tread = 0.08
                builder.create_box(w, depth, thick_tread) \
                       .translate(0, y_pos + depth/2, z_pos + rise) \
                       .tag_slot(0) \
                       .tag_uvs(uv_s0, 'BOX') \
                       .select_boundary().tag_edge_role(1)

            else: # STANDARD
                # Riser (Vertical)
                builder.create_box(w, riser_thick, rise) \
                       .translate(0, y_pos + riser_thick/2, z_pos + rise/2) \
                       .tag_slot(1) \
                       .tag_uvs(uv_s1, 'BOX')

                # Tread (Horizontal)
                builder.create_box(w, depth + nosing, tread_thick) \
                       .translate(0, y_pos + (depth + nosing)/2, z_pos + rise + tread_thick/2) \
                       .tag_slot(0) \
                       .tag_uvs(uv_s0, 'BOX') \
                       .select_boundary().tag_edge_role(1)

        # 2. Stringers / Supports
        if self.stair_style == 'FLOATING':
            # Central Spine
            spine_w = w * 0.2
            total_y = count * depth
            total_z = h

            vec = Vector((0, total_y, total_z))
            length = vec.length
            angle = math.atan2(total_z, total_y)

            cy = total_y / 2
            cz = total_z / 2

            builder.create_box(spine_w, length + 0.5, 0.2) \
                   .rotate(math.degrees(angle), 'X') \
                   .translate(0, cy, cz - 0.2) \
                   .tag_slot(2) \
                   .tag_uvs(uv_s2, 'BOX') \
                   .select_boundary().tag_edge_role(2) # Contour

        elif self.stair_style == 'STANDARD' and self.has_stringer:
            total_y = count * depth
            total_z = h

            vec = Vector((0, total_y, total_z))
            length = vec.length
            angle = math.atan2(total_z, total_y)

            sw = self.stringer_width
            sh = self.stringer_offset * 6.0
            if sh < 0.2: sh = 0.2

            cy = total_y / 2
            cz = total_z / 2
            cz_shift = cz - (sh * 0.3)

            # Left Stringer
            builder.create_box(sw, length + 0.5, sh) \
                   .rotate(math.degrees(angle), 'X') \
                   .translate(-w/2 - sw/2, cy, cz_shift) \
                   .tag_slot(2) \
                   .tag_uvs(uv_s2, 'BOX') \
                   .select_boundary().tag_edge_role(2)

            # Right Stringer
            builder.create_box(sw, length + 0.5, sh) \
                   .rotate(math.degrees(angle), 'X') \
                   .translate(w/2 + sw/2, cy, cz_shift) \
                   .tag_slot(2) \
                   .tag_uvs(uv_s2, 'BOX') \
                   .select_boundary().tag_edge_role(2)

        # 3. Sockets (Tag Existing Faces)
        builder.clean()

        # Bottom (Front face of first step or stringer)
        # Looking for face at Y ~ 0 with Normal -Y
        builder.select_faces_by_normal(Vector((0, -1, 0)), tolerance=0.2) \
               .tag_socket(1)

        # Top (Back face of last step)
        # Looking for face at Y ~ total_y with Normal +Y
        builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.2) \
               .tag_socket(2)

    def draw_shape_ui(self, layout):
        box_dim = layout.box()
        box_dim.label(text="Dimensions", icon='MESH_PLANE')
        col_dim = box_dim.column(align=True)
        col_dim.prop(self, "stair_style") # Added Style
        col_dim.prop(self, "stair_width")
        col_dim.prop(self, "total_height")
        col_dim.prop(self, "step_count")

        box_det = layout.box()
        box_det.label(text="Details", icon='LINCURVE')
        col_det = box_det.column(align=True)
        col_det.prop(self, "tread_depth")

        if self.stair_style == 'STANDARD':
            box_str = layout.box()
            box_str.label(text="Stringers", icon='MOD_BUILD')
            col_str = box_str.column(align=True)
            col_str.prop(self, "has_stringer")
            if self.has_stringer:
                col_str.prop(self, "stringer_width")
                col_str.prop(self, "stringer_offset")
