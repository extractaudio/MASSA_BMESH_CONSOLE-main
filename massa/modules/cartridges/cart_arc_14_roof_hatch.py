import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_14: Roof Hatch",
    "id": "arc_14_roof_hatch",
    "icon": "MOD_BOOLEAN",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_ArcRoofHatch(Massa_OT_Base):
    bl_idname = "massa.gen_arc_14_roof_hatch"
    bl_label = "ARC Roof Hatch"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("SINGLE_LEAF", "Single Leaf", "One hinged cover"),
            ("DOUBLE_LEAF", "Double Leaf", "Split opening"),
            ("SLIDING", "Sliding", "Horizontal rail slide"),
        ],
        default="SINGLE_LEAF"
    )

    # Dimensions
    width: FloatProperty(name="Width", default=1.0, min=0.6)
    length: FloatProperty(name="Length", default=1.0, min=0.6)
    curb_height: FloatProperty(name="Curb Height", default=0.3, min=0.1)

    # Lid
    lid_thickness: FloatProperty(name="Lid Thickness", default=0.05, min=0.02)
    open_pct: FloatProperty(name="Open %", default=0.0, min=0.0, max=100.0)

    # Details
    safety_rail: BoolProperty(name="Safety Rail", default=False)
    piston_vis: BoolProperty(name="Pistons", default=True)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Curb", "uv": "BOX", "phys": "CONCRETE"},
            1: {"name": "Lid/Cover", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            2: {"name": "Hardware", "uv": "BOX", "phys": "METAL_STEEL"},
            3: {"name": "Safety Rail", "uv": "BOX", "phys": "METAL_YELLOW"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions", icon='Length')
        col = box.column(align=True)
        col.prop(self, "width")
        col.prop(self, "length")
        col.prop(self, "curb_height")

        box = layout.box()
        box.label(text="Operation", icon='DRIVER')
        col = box.column(align=True)
        col.prop(self, "lid_thickness")
        col.prop(self, "open_pct")

        box = layout.box()
        box.label(text="Options", icon='MOD_PHYSICS')
        col = box.column(align=True)
        col.prop(self, "safety_rail")
        col.prop(self, "piston_vis")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        w = self.width
        l = self.length
        ch = self.curb_height
        lt = self.lid_thickness
        op = self.open_pct / 100.0

        # Origin: Bottom Center (Z=0).

        # 1. Curb (Hollow box)
        curb_thick = 0.05
        # Front
        builder.create_box(w + 2*curb_thick, curb_thick, ch, center=Vector((0, -l/2 - curb_thick/2, ch/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
        # Back
        builder.create_box(w + 2*curb_thick, curb_thick, ch, center=Vector((0, l/2 + curb_thick/2, ch/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
        # Left
        builder.create_box(curb_thick, l, ch, center=Vector((-w/2 - curb_thick/2, 0, ch/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
        # Right
        builder.create_box(curb_thick, l, ch, center=Vector((w/2 + curb_thick/2, 0, ch/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Flange at bottom
        fw = 0.1
        builder.create_box(w + 2*curb_thick + 2*fw, l + 2*curb_thick + 2*fw, 0.02, center=Vector((0, 0, 0.01)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        lid_z = ch

        # 2. Lid
        if self.style == "SINGLE_LEAF":
            # Hinge at Back (Y+)
            # Lid Size
            lw = w + 2*curb_thick + 0.05
            ll = l + 2*curb_thick + 0.05

            # Rotation
            angle = -op * 85.0 # Open UP (Rotate X negative?)
            # Y+ is Back. Hinge at Y = ll/2 (relative to lid center).
            # We want Back edge to stay fixed.
            # Front edge (Y-) lifts up (+Z).
            # Axis is parallel to X.
            # Pivot is (0, l/2 + curb_thick, lid_z).

            # Create Lid at Origin relative to hinge
            # Hinge at (0,0,0). Lid extends forward (-Y).
            # Center of lid is (0, -ll/2, lt/2) relative to hinge.
            builder.create_box(lw, ll, lt, center=Vector((0, -ll/2, lt/2)))

            # Rotate
            builder.rotate(angle, axis='X')

            # Translate to position
            # Hinge pos: (0, l/2 + curb_thick, lid_z)
            builder.translate(0, l/2 + curb_thick, lid_z)
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Piston?
            if self.piston_vis and op > 0.1:
                # Simple cylinder from Curb side to Lid
                # Start: (w/2, 0, ch-0.1). End: Lid side.
                # Just draw a vertical prop for simplicity or angled
                pass

        elif self.style == "DOUBLE_LEAF":
            # Split along X axis? Or Y axis?
            # Typically long side is hinged. If L > W, hinges on L sides.
            # Let's assume hinges on Left/Right (X).

            lw = (w + 2*curb_thick)/2 + 0.02
            ll = l + 2*curb_thick + 0.05
            angle = op * 85.0

            # Left Leaf (Hinge at X = -w/2 - curb_thick)
            # Extends +X. Center (lw/2, 0, lt/2) relative to hinge.
            builder.create_box(lw, ll, lt, center=Vector((lw/2, 0, lt/2)))
            builder.rotate(-angle, axis='Y') # Rotate Up-Out (Left goes up -> -Y rot? No. Y rot moves +X to -Z. -Y moves +X to +Z)
            builder.translate(-w/2 - curb_thick, 0, lid_z)
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Right Leaf (Hinge at X = +w/2 + curb_thick)
            # Extends -X. Center (-lw/2, 0, lt/2)
            builder.create_box(lw, ll, lt, center=Vector((-lw/2, 0, lt/2)))
            builder.rotate(angle, axis='Y') # Rotate Up-Out
            builder.translate(w/2 + curb_thick, 0, lid_z)
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        elif self.style == "SLIDING":
            # Slide along Length (Y)
            slide_dist = l * op

            lw = w + 2*curb_thick + 0.05
            ll = l + 2*curb_thick + 0.05

            # Rails
            rw = 0.05
            rl = l * 2
            builder.create_box(rw, rl, 0.05, center=Vector((-w/2 - curb_thick - rw, 0, lid_z - 0.02)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(rw, rl, 0.05, center=Vector((w/2 + curb_thick + rw, 0, lid_z - 0.02)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Lid
            builder.create_box(lw, ll, lt, center=Vector((0, slide_dist, lid_z + lt/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 3. Safety Rail
        if self.safety_rail:
            # Yellow railing around curb
            rail_h = 1.1
            rail_off = 0.1

            # Top Rail Loop
            # 4 segments
            rw = w + 2*curb_thick + 2*rail_off
            rl = l + 2*curb_thick + 2*rail_off

            # Front
            builder.create_box(rw, 0.05, 0.05, center=Vector((0, -rl/2, rail_h)))
            builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Back (Leave gap for exit if Single Leaf? No, usually Gate)
            builder.create_box(rw, 0.05, 0.05, center=Vector((0, rl/2, rail_h)))
            builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Left
            builder.create_box(0.05, rl, 0.05, center=Vector((-rw/2, 0, rail_h)))
            builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Right
            builder.create_box(0.05, rl, 0.05, center=Vector((rw/2, 0, rail_h)))
            builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Posts (Corners)
            for cx in [-rw/2, rw/2]:
                for cy in [-rl/2, rl/2]:
                    builder.create_box(0.05, 0.05, rail_h, center=Vector((cx, cy, rail_h/2)))
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
