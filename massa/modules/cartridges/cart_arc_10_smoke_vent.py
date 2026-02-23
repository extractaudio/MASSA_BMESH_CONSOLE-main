import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_10: Smoke Vent",
    "id": "arc_10_smoke_vent",
    "icon": "MOD_WIND",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_ArcSmokeVent(Massa_OT_Base):
    bl_idname = "massa.gen_arc_10_smoke_vent"
    bl_label = "ARC Smoke Vent"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("LOUVERED", "Louvered Penthouse", "Slatted air intake"),
            ("GRAVITY", "Gravity / Mushroom", "Round hooded vent"),
            ("BUTTERFLY", "Butterfly Damper", "Split opening exhaust"),
        ],
        default="LOUVERED"
    )

    # Dimensions
    width: FloatProperty(name="Width/Dia", default=1.5, min=0.5)
    length: FloatProperty(name="Length", default=1.5, min=0.5)
    height: FloatProperty(name="Housing Height", default=1.0, min=0.2)

    # Base
    base_height: FloatProperty(name="Curb Height", default=0.3, min=0.0)
    flange_width: FloatProperty(name="Flange Width", default=0.1, min=0.0)

    # Details
    blade_count: IntProperty(name="Blades", default=6, min=1, max=20)
    blade_angle: FloatProperty(name="Blade Angle", default=45.0, min=0.0, max=90.0)

    hood_ratio: FloatProperty(name="Hood Size Ratio", default=1.5, min=1.0)
    damper_angle: FloatProperty(name="Open Angle", default=30.0, min=0.0, max=90.0)

    motor_box: BoolProperty(name="Motor Housing", default=True)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Housing", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            1: {"name": "Blades/Mech", "uv": "BOX", "phys": "METAL_STEEL"},
            2: {"name": "Base Curb", "uv": "BOX", "phys": "CONCRETE"},
            3: {"name": "Screen/Mesh", "uv": "BOX", "phys": "WIRE_MESH"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions", icon='MESH_CUBE')
        col = box.column(align=True)
        col.prop(self, "width")
        if self.style != "GRAVITY":
            col.prop(self, "length")
        col.prop(self, "height")

        box = layout.box()
        box.label(text="Base", icon='MOD_BUILD')
        col = box.column(align=True)
        col.prop(self, "base_height")
        col.prop(self, "flange_width")

        box = layout.box()
        box.label(text="Mechanism", icon='PHYSICS')
        col = box.column(align=True)
        if self.style == "LOUVERED":
            col.prop(self, "blade_count")
            col.prop(self, "blade_angle")
        elif self.style == "GRAVITY":
            col.prop(self, "hood_ratio")
        elif self.style == "BUTTERFLY":
            col.prop(self, "damper_angle")
            col.prop(self, "motor_box")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        w = self.width
        l = self.length
        h = self.height
        bh = self.base_height
        fw = self.flange_width

        if self.style == "GRAVITY":
            l = w # Force square/round base logic

        # 1. Base Curb
        # Solid box or cylinder depending on style?
        # Usually curbs are rectangular for rectangular vents, circular for gravity.

        if self.style == "GRAVITY":
            # Circular base
            builder.create_cylinder(radius=w/2 + 0.05, depth=bh, center=Vector((0,0,bh/2)))
        else:
            builder.create_box(w + 0.1, l + 0.1, bh, center=Vector((0,0,bh/2)))

        builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Flange
        if fw > 0:
            fz = 0.05
            if self.style == "GRAVITY":
                builder.create_cylinder(radius=w/2 + fw + 0.05, depth=fz, center=Vector((0,0,fz/2)))
            else:
                builder.create_box(w + fw*2 + 0.1, l + fw*2 + 0.1, fz, center=Vector((0,0,fz/2)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        start_z = bh

        if self.style == "LOUVERED":
            # Rectangular Penthouse
            # Frame
            corner_w = 0.1

            # 4 Corner Posts
            builder.create_box(corner_w, corner_w, h, center=Vector((-w/2, -l/2, start_z + h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(corner_w, corner_w, h, center=Vector((w/2, -l/2, start_z + h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(corner_w, corner_w, h, center=Vector((w/2, l/2, start_z + h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(corner_w, corner_w, h, center=Vector((-w/2, l/2, start_z + h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Top Cap (Lid)
            # Pitched?
            cap_h = 0.2
            builder.create_box(w + 0.2, l + 0.2, 0.05, center=Vector((0,0,start_z + h))) # Flat rim
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Pyramid top?
            builder.create_box(w, l, 0.01, center=Vector((0,0,start_z + h + 0.02)))
            builder.select_faces_by_normal(Vector((0,0,1)))
            builder.extrude(cap_h)
            builder.scale(0.01, 0.01, 1.0) # Peak
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Louvers (Blades)
            # Along all 4 sides?
            # Horizontal blades.

            bc = self.blade_count
            ba = self.blade_angle

            step = h / (bc + 1)

            # We create blades as thin boxes, rotated.
            # 4 sets: Front, Back, Left, Right.

            def create_blade(cx, cy, bw, bl, z, angle_x):
                # Create box
                builder.create_box(bw, bl, 0.02, center=Vector((0,0,0)))
                # Rotate X
                builder.rotate(ba, axis='X')
                # Translate
                builder.translate(cx, cy, z)
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            for i in range(bc):
                z = start_z + (i+1)*step

                # Front (Y-)
                # Blade runs along X (width w)
                create_blade(0, -l/2, w - 0.1, 0.15, z, ba)

                # Back (Y+)
                # Rotate blade?
                # Angle should slope down-out.
                # Front: Y- is out. Slope down towards Y-.
                # Rotate X positive? (Y -> Z -> -Y). No.
                # Check rotation.

                # Let's assume create_blade handles Front correctly.
                # For Back, we need to rotate 180 around Z?
                builder.create_box(w - 0.1, 0.15, 0.02, center=Vector((0,0,0)))
                builder.rotate(-ba, axis='X') # Slope other way
                builder.translate(0, l/2, z)
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Sides (Left/Right)
                # Run along Y (length l)
                # Left (X-)
                builder.create_box(0.15, l - 0.1, 0.02, center=Vector((0,0,0)))
                builder.rotate(ba, axis='Y') # Rotate Y axis
                builder.translate(-w/2, 0, z)
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Right (X+)
                builder.create_box(0.15, l - 0.1, 0.02, center=Vector((0,0,0)))
                builder.rotate(-ba, axis='Y')
                builder.translate(w/2, 0, z)
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Internal Screen (Mesh)
            builder.create_box(w - 0.2, l - 0.2, h - 0.1, center=Vector((0,0,start_z + h/2)))
            builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')

        elif self.style == "GRAVITY":
            # Mushroom Vent
            # Throat (Cylinder)
            builder.create_cylinder(radius=w/2, depth=h, center=Vector((0,0,start_z + h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER')

            # Hood
            hood_r = (w/2) * self.hood_ratio
            hood_base_z = start_z + h + 0.1

            # Cone
            builder.create_cone(radius_bottom=hood_r, radius_top=0.0, depth=w*0.3, center=Vector((0,0,hood_base_z + w*0.15)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER')

            # Inner structure?
            # Supports for hood
            for ang in [0, 90, 180, 270]:
                rad = math.radians(ang)
                x = math.cos(rad) * (w/2 + 0.05)
                y = math.sin(rad) * (w/2 + 0.05)

                builder.create_box(0.05, 0.05, 0.3, center=Vector((x, y, start_z + h)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        elif self.style == "BUTTERFLY":
            # Throat (Box)
            builder.create_box(w, l, h, center=Vector((0,0,start_z + h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Dampers (Split Lengthwise)
            # Axis Y=0.
            # Two flaps.
            # Left Flap (X < 0). Hinge at X=0? No, hinge at center strut.
            # Flap width = w/2.

            damper_w = w/2 + 0.1
            damper_l = l + 0.2
            open_ang = self.damper_angle

            # Center Gutter/Strut
            builder.create_box(0.1, l+0.2, 0.1, center=Vector((0,0,start_z + h)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Left Flap
            # Create at origin
            builder.create_box(damper_w, damper_l, 0.05, center=Vector((-damper_w/2, 0, 0)))
            # Rotate Y (Open Up)
            # Hinge at X=0.
            # X- flap rotates Y positive (Left side goes Up).
            # No, Right Hand Rule. Y axis points back.
            # Thumb Y. Fingers curl Z to X.
            # Rotate +Y moves +Z to +X.
            # We want -X side to go +Z.
            # So -X, 0 -> ?
            # Rotate -Y?

            # Pivot is at (0,0,0) relative to flap?
            # Flap center is (-w/4, 0, 0).
            # Hinge is at (0,0,0).
            # We created flap relative to hinge (Hinge at Origin, flap extends -X).

            builder.rotate(-open_ang, axis='Y')
            builder.translate(0, 0, start_z + h)
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Right Flap
            builder.create_box(damper_w, damper_l, 0.05, center=Vector((damper_w/2, 0, 0)))
            builder.rotate(open_ang, axis='Y')
            builder.translate(0, 0, start_z + h)
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Windbands / Stack?
            # Often vertical sheets on sides to direct smoke.

            if self.motor_box:
                builder.create_box(0.3, 0.3, 0.4, center=Vector((0, -l/2 - 0.2, start_z + h/2)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 4. Sockets
        # Base
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1)
        bases = [f for f in builder.active_faces if abs(f.calc_center_median().z) < 0.1]
        builder.active_faces = bases
        builder.tag_socket(9)

        builder.clean()

    def execute(self, context):
        return super().execute(context)
