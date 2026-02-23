import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_13: Platform",
    "id": "ind_13_platform",
    "icon": "MESH_GRID",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndPlatform(Massa_OT_Base):
    bl_idname = "massa.gen_ind_13_platform"
    bl_label = "IND Platform"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("GRATE", "Metal Grating", "Open metal mesh floor"),
            ("PLATE", "Diamond Plate", "Solid steel floor with texture"),
            ("CONCRETE", "Concrete Slab", "Heavy industrial floor"),
        ],
        default="GRATE",
    )

    # Dimensions
    length: FloatProperty(name="Length (X)", default=4.0, min=1.0)
    width: FloatProperty(name="Width (Y)", default=3.0, min=1.0)
    height: FloatProperty(name="Height (Z)", default=3.0, min=0.5)

    # Structure
    floor_thick: FloatProperty(name="Floor Thickness", default=0.1, min=0.01)
    beam_size: FloatProperty(name="Beam Size", default=0.2, min=0.05)
    leg_size: FloatProperty(name="Leg Size", default=0.15, min=0.05)
    support_spacing: FloatProperty(name="Support Spacing", default=2.0, min=0.5)

    # Railing
    railing_height: FloatProperty(name="Railing Height", default=1.0, min=0.5)
    railing_type: EnumProperty(
        name="Railing Type",
        items=[
            ("NONE", "None", ""),
            ("STANDARD", "Standard", "Two rails"),
            ("INDUSTRIAL", "Industrial", "Mesh/Kickplate"),
        ],
        default="STANDARD",
    )

    # Access
    stair_access: EnumProperty(
        name="Stair Access",
        items=[
            ("NONE", "None", ""),
            ("FRONT", "Front", ""),
            ("SIDE", "Side", ""),
        ],
        default="NONE",
    )
    stair_width: FloatProperty(name="Stair Width", default=1.0, min=0.5)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        floor_mat = "METAL_GRATE" if self.style == "GRATE" else ("METAL_PLATE" if self.style == "PLATE" else "CONCRETE_ROUGH")
        return {
            0: {"name": "Floor", "uv": "SKIP", "phys": floor_mat},
            1: {"name": "Structure", "uv": "SKIP", "phys": "METAL_PAINTED"}, # Beams/Legs
            2: {"name": "Railing", "uv": "SKIP", "phys": "METAL_SAFETY"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style", text="")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Dimensions", icon="FIXED_SIZE")
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Structure", icon="MESH_GRID")
        col.prop(self, "floor_thick")
        col.prop(self, "beam_size")
        col.prop(self, "leg_size")
        col.prop(self, "support_spacing")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Features", icon="MOD_BUILD")
        col.prop(self, "railing_type")
        if self.railing_type != "NONE":
            col.prop(self, "railing_height")

        col.separator()
        col.prop(self, "stair_access")
        if self.stair_access != "NONE":
            col.prop(self, "stair_width")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")

        l = self.length
        w = self.width
        h = self.height # Height is floor level? Or leg height? usually floor Z.
        ft = self.floor_thick
        bs = self.beam_size
        ls = self.leg_size

        # Determine Floor Z
        floor_z = h

        # 1. Floor Deck
        builder.create_box(l, w, ft, center=Vector((0,0,floor_z - ft/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 2. Main Beams (Under floor)
        # Perimeter Frame
        # Front/Back (X)
        builder.create_box(l, bs, bs, center=Vector((0, -w/2 + bs/2, floor_z - ft - bs/2)))
        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        builder.create_box(l, bs, bs, center=Vector((0, w/2 - bs/2, floor_z - ft - bs/2)))
        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Left/Right (Y)
        builder.create_box(bs, w - 2*bs, bs, center=Vector((-l/2 + bs/2, 0, floor_z - ft - bs/2)))
        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        builder.create_box(bs, w - 2*bs, bs, center=Vector((l/2 - bs/2, 0, floor_z - ft - bs/2)))
        builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Cross Beams
        # Based on support spacing
        if self.support_spacing > 0:
            num_x = int(l / self.support_spacing)
            dx = l / (num_x + 1)
            for i in range(1, num_x + 1):
                x = -l/2 + i*dx
                builder.create_box(bs/2, w - 2*bs, bs, center=Vector((x, 0, floor_z - ft - bs/2)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 3. Legs
        # 4 corners
        leg_h = h - ft - bs
        if leg_h > 0:
            corners = [
                (-l/2 + ls/2, -w/2 + ls/2),
                (l/2 - ls/2, -w/2 + ls/2),
                (l/2 - ls/2, w/2 - ls/2),
                (-l/2 + ls/2, w/2 - ls/2)
            ]
            for cx, cy in corners:
                builder.create_box(ls, ls, leg_h, center=Vector((cx, cy, leg_h/2)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Tag bottom socket
                builder.select_faces_by_normal(Vector((0,0,-1))).tag_socket(9)

        # 4. Railing
        if self.railing_type != "NONE":
            rh = self.railing_height
            # Perimeter posts
            # Spacing ~ 1.5m
            perim = 2*l + 2*w
            num_posts = int(perim / 1.5)
            # Simplification: Posts at corners + spaced

            # Helper to place post
            def place_post(x, y):
                builder.create_box(0.05, 0.05, rh, center=Vector((x, y, floor_z + rh/2)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Place posts along perimeter
            # X edges
            posts_x = max(2, int(l / 1.5))
            dx = l / (posts_x - 1) if posts_x > 1 else 0

            for i in range(posts_x):
                x = -l/2 + i*dx
                place_post(x, -w/2 + 0.05)
                place_post(x, w/2 - 0.05)

            # Y edges (excluding corners already done by X loop?)
            # X loop does corners: i=0 and i=last are corners.
            # So just fill Y
            posts_y = max(2, int(w / 1.5))
            dy = w / (posts_y - 1) if posts_y > 1 else 0

            for i in range(1, posts_y - 1): # Skip corners
                y = -w/2 + i*dy
                place_post(-l/2 + 0.05, y)
                place_post(l/2 - 0.05, y)

            # Rails
            # Top Rail
            # 4 segments
            # Front
            builder.create_box(l, 0.05, 0.05, center=Vector((0, -w/2 + 0.05, floor_z + rh)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Back
            builder.create_box(l, 0.05, 0.05, center=Vector((0, w/2 - 0.05, floor_z + rh)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Left
            builder.create_box(0.05, w, 0.05, center=Vector((-l/2 + 0.05, 0, floor_z + rh)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Right
            builder.create_box(0.05, w, 0.05, center=Vector((l/2 - 0.05, 0, floor_z + rh)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Mid Rail (if Standard)
            if self.railing_type == "STANDARD":
                mid_h = rh / 2
                # Front
                builder.create_box(l, 0.04, 0.04, center=Vector((0, -w/2 + 0.05, floor_z + mid_h)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Back
                builder.create_box(l, 0.04, 0.04, center=Vector((0, w/2 - 0.05, floor_z + mid_h)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Left
                builder.create_box(0.04, w, 0.04, center=Vector((-l/2 + 0.05, 0, floor_z + mid_h)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Right
                builder.create_box(0.04, w, 0.04, center=Vector((l/2 - 0.05, 0, floor_z + mid_h)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            elif self.railing_type == "INDUSTRIAL":
                # Kickplate at bottom
                kp_h = 0.15
                # Front
                builder.create_box(l, 0.02, kp_h, center=Vector((0, -w/2 + 0.05, floor_z + kp_h/2)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Back
                builder.create_box(l, 0.02, kp_h, center=Vector((0, w/2 - 0.05, floor_z + kp_h/2)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Left
                builder.create_box(0.02, w, kp_h, center=Vector((-l/2 + 0.05, 0, floor_z + kp_h/2)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Right
                builder.create_box(0.02, w, kp_h, center=Vector((l/2 - 0.05, 0, floor_z + kp_h/2)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 5. Stairs (Simplified Ramp/Steps)
        if self.stair_access != "NONE":
            sw = self.stair_width
            # Determine position
            # FRONT: Center of -Y edge?
            # SIDE: Center of -X edge?

            sx, sy = 0, 0
            if self.stair_access == "FRONT":
                sx, sy = 0, -w/2
                # Stairs go -Y
                # Height h
                # Length approx h * 1.5
                sl = h * 1.5

                # Create Sloped Box (Ramp) or steps
                # Steps better
                num_steps = int(h / 0.2)
                step_h = h / num_steps
                step_d = sl / num_steps

                for i in range(num_steps):
                    # Each step
                    z = i * step_h
                    y = -w/2 - (num_steps - i) * step_d

                    builder.create_box(sw, step_d, step_h, center=Vector((0, y + step_d/2, z + step_h/2)))
                    builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            elif self.stair_access == "SIDE":
                sx, sy = -l/2, 0
                # Stairs go -X
                sl = h * 1.5
                num_steps = int(h / 0.2)
                step_h = h / num_steps
                step_d = sl / num_steps

                for i in range(num_steps):
                    z = i * step_h
                    x = -l/2 - (num_steps - i) * step_d

                    builder.create_box(step_d, sw, step_h, center=Vector((x + step_d/2, 0, z + step_h/2)))
                    builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # FINAL UV FIX: Ensure all horizontal faces use BOX
        builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.6)
        up_faces = builder.active_faces[:]
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.6)
        down_faces = builder.active_faces[:]

        builder.active_faces = up_faces + down_faces
        builder.tag_uvs(scale=self.uv_scale, projection='BOX')

        builder.clean()
