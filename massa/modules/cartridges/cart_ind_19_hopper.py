import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_19: Hopper",
    "id": "ind_19_hopper",
    "icon": "MOD_DECIM",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_IndHopper(Massa_OT_Base):
    bl_idname = "massa.gen_ind_19_hopper"
    bl_label = "IND Hopper"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # 1. Style Enum
    style: EnumProperty(
        name="Hopper Type",
        items=[
            ("PYRAMIDAL", "Pyramidal", "Square/Rectangular funnel"),
            ("CONICAL", "Conical", "Round funnel"),
            ("OFFSET", "Offset Chute", "Asymmetric hopper"),
        ],
        default="PYRAMIDAL"
    )

    # 2. Dimensions
    top_width: FloatProperty(name="Top Width", default=1.5, min=0.5)
    top_depth: FloatProperty(name="Top Depth", default=1.5, min=0.5)
    bottom_width: FloatProperty(name="Outlet Size", default=0.4, min=0.1)

    height: FloatProperty(name="Funnel Height", default=1.5, min=0.5)
    chute_length: FloatProperty(name="Chute Length", default=0.5, min=0.0)
    leg_height: FloatProperty(name="Leg Height", default=2.0, min=0.5)

    # 3. Details
    wall_thickness: FloatProperty(name="Wall Thickness", default=0.05, min=0.01, max=0.2)
    rib_count: IntProperty(name="Ribs", default=2, min=0, max=5)
    flange_width: FloatProperty(name="Flange Width", default=0.1, min=0.0, max=0.5)

    gate_box: BoolProperty(name="Gate Housing", default=True)
    ladder: BoolProperty(name="Access Ladder", default=False)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Hopper Body", "uv": "UNWRAP", "phys": "METAL_STEEL"},
            1: {"name": "Frame/Legs", "uv": "BOX", "phys": "METAL_IRON"},
            2: {"name": "Gate/Fittings", "uv": "BOX", "phys": "METAL_IRON"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Funnel")
        box.prop(self, "top_width")
        box.prop(self, "top_depth")
        box.prop(self, "height")
        box.prop(self, "bottom_width")

        box = layout.box()
        box.label(text="Structure")
        box.prop(self, "leg_height")
        box.prop(self, "chute_length")

        box = layout.box()
        box.label(text="Details")
        col = box.column(align=True)
        col.prop(self, "wall_thickness")
        col.prop(self, "rib_count")
        col.prop(self, "flange_width")
        col.prop(self, "gate_box")
        col.prop(self, "ladder")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        tw = self.top_width
        td = self.top_depth
        bw = self.bottom_width
        h = self.height
        cl = self.chute_length
        lh = self.leg_height

        # Calculate Z levels
        # Origin = Ground (0)
        # Chute Outlet = lh
        # Funnel Start (Bottom) = lh + cl
        # Funnel Top = lh + cl + h

        z_outlet = lh
        z_funnel_bot = lh + cl
        z_funnel_top = lh + cl + h

        # 1. Main Hopper Body
        if self.style == "CONICAL":
            # Cylinder (Chute)
            builder.create_cone(radius_bottom=bw/2, radius_top=bw/2, depth=cl, center=Vector((0,0,0)))
            builder.translate(0, 0, lh + cl/2)
            builder.tag_slot(0)

            # Funnel (Cone)
            # Create Cone from z_funnel_bot to z_funnel_top
            builder.create_cone(radius_bottom=bw/2, radius_top=tw/2, depth=h, center=Vector((0,0,0)))
            builder.translate(0, 0, z_funnel_bot + h/2)
            builder.tag_slot(0)

            # Top Flange
            if self.flange_width > 0:
                builder.create_cone(radius_bottom=tw/2 + self.flange_width, radius_top=tw/2 + self.flange_width, depth=0.05, center=Vector((0,0,0)))
                builder.translate(0, 0, z_funnel_top)
                builder.tag_slot(0)

        elif self.style == "PYRAMIDAL":
            # Chute (Box)
            builder.create_box(bw, bw, cl, center=Vector((0,0,0)))
            builder.translate(0, 0, lh + cl/2)
            builder.tag_slot(0)

            # Funnel (Lofted Box?)
            # Use Hull or Bridge?
            # MassaBuilder doesn't have loft.
            # Use Extrude + Scale trick from bottom up.

            # Create base square at funnel bot
            builder.create_box(bw, bw, 0.01, center=Vector((0,0,z_funnel_bot)))
            # Select top face
            builder.select_faces_by_normal(Vector((0,0,1)))

            # Extrude to top
            builder.extrude(h)

            # Scale top face to top dimensions
            # Current size is bw x bw. Target is tw x td.
            sx = tw / bw if bw > 0 else 1
            sy = td / bw if bw > 0 else 1

            # Need Scale Center helper again
            # Or assume centered
            builder.scale(sx, sy, 1.0)
            builder.tag_slot(0)

            # Flange
            if self.flange_width > 0:
                builder.create_box(tw + self.flange_width*2, td + self.flange_width*2, 0.05, center=Vector((0,0,z_funnel_top)))
                builder.tag_slot(0)

        elif self.style == "OFFSET":
            # Chute at side
            # Funnel top centered at 0,0.
            # Chute at -tw/2 + bw/2?
            # Or Chute at 0,0, Top offset?
            # Let's keep chute at 0,0 for discharge alignment.

            # Chute
            builder.create_box(bw, bw, cl, center=Vector((0,0,0)))
            builder.translate(0, 0, lh + cl/2)
            builder.tag_slot(0)

            # Funnel
            # Create base at 0,0, z_bot
            builder.create_box(bw, bw, 0.01, center=Vector((0,0,z_funnel_bot)))
            builder.select_faces_by_normal(Vector((0,0,1)))
            builder.extrude(h)

            # Target Center: Offset X by (tw/2 - bw/2) so one side is vertical?
            # Vertical side is common in offset hoppers.
            # If offset X, the side at X=-bw/2 stays at X=-bw/2.
            # Top X range: -bw/2 to -bw/2 + tw.
            # Center X = -bw/2 + tw/2.

            target_center_x = (tw - bw) / 2.0

            sx = tw / bw
            sy = td / bw

            # Move center then scale?
            # Scale happens around active center (0,0,z_top).
            # If we scale, we get +/- tw/2.
            # Then translate X by target_center_x.

            builder.scale(sx, sy, 1.0)
            builder.translate(target_center_x, 0, 0)
            builder.tag_slot(0)

        # 2. Legs / Frame
        # Frame goes up to z_funnel_top usually
        frame_w = tw + 0.2
        frame_d = (td if self.style != "CONICAL" else tw) + 0.2

        # 4 Legs
        leg_thick = 0.15

        if self.style == "OFFSET":
             # Frame matches top
             frame_w = tw + 0.2
             frame_cx = (tw - bw) / 2.0
        else:
             frame_cx = 0

        for lx in [-1, 1]:
            for ly in [-1, 1]:
                pos_x = frame_cx + lx * (frame_w/2)
                pos_y = ly * (frame_d/2)

                builder.create_box(leg_thick, leg_thick, z_funnel_top, center=Vector((0,0,0)))
                builder.translate(pos_x, pos_y, z_funnel_top/2)
                builder.tag_slot(1)

        # Cross bracing?
        # At mid height

        # 3. Ribs
        if self.rib_count > 0:
            step = h / (self.rib_count + 1)
            for i in range(self.rib_count):
                z = z_funnel_bot + (i+1)*step
                # Interpolate width at Z
                # Linear interpolation
                ratio = (z - z_funnel_bot) / h
                curr_w = bw + (tw - bw) * ratio
                curr_d = (bw + (td - bw) * ratio) if self.style != "CONICAL" else curr_w

                if self.style == "CONICAL":
                    builder.create_cone(radius_bottom=curr_w/2 + 0.05, radius_top=curr_w/2 + 0.05, depth=0.1, center=Vector((0,0,z)))
                else:
                    cx = 0
                    if self.style == "OFFSET":
                        cx = ((tw - bw) / 2.0) * ratio
                    builder.create_box(curr_w + 0.1, curr_d + 0.1, 0.1, center=Vector((cx, 0, z)))
                builder.tag_slot(0)

        # 3.5 Ladder
        if self.ladder:
            lad_h = z_funnel_top
            lad_w = 0.4

            # Position: Front side (Y-)
            lad_y = -frame_d/2 - 0.2

            # Rails
            builder.create_box(0.05, 0.05, lad_h, center=Vector((-lad_w/2, lad_y, lad_h/2)))
            builder.tag_slot(1)
            builder.create_box(0.05, 0.05, lad_h, center=Vector((lad_w/2, lad_y, lad_h/2)))
            builder.tag_slot(1)

            # Rungs
            rung_step = 0.3
            num_rungs = int(lad_h / rung_step)
            for i in range(num_rungs):
                rz = (i+1)*rung_step
                if rz < lad_h:
                    builder.create_box(lad_w, 0.03, 0.03, center=Vector((0, lad_y, rz)))
                    builder.tag_slot(1)

        # 4. Gate Housing
        if self.gate_box:
            # At bottom of chute
            gate_sz = bw * 1.5
            builder.create_box(gate_sz, gate_sz, 0.3, center=Vector((0,0,lh + 0.2)))
            builder.tag_slot(2)
            # Handle?
            builder.create_cylinder(radius=0.02, depth=0.6, center=Vector((0,0,0)))
            builder.rotate(90, axis='Y')
            builder.translate(gate_sz/2 + 0.2, 0, lh + 0.2)
            builder.tag_slot(2)

        # Socket (Ground)
        builder.create_grid(size=frame_w, center=Vector((0,0,0))) # Temp grid to select?
        # Better: Select leg bottoms.
        # min_z search
        min_z = 1000
        for f in bm.faces:
             z = f.calc_center_median().z
             if z < min_z: min_z = z

        active_faces = [f for f in bm.faces if abs(f.calc_center_median().z - min_z) < 0.05 and f.normal.z < -0.5]
        builder.active_faces = active_faces
        builder.tag_socket(9).tag_slot(9)

        # UV
        builder.select_all_faces().tag_uvs(scale=self.uv_scale, projection='BOX')
        builder.clean()

    def execute(self, context):
        return super().execute(context)
