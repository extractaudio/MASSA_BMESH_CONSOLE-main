import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_20: Centrifuge",
    "id": "ind_20_centrifuge",
    "icon": "MOD_SCREW",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_IndCentrifuge(Massa_OT_Base):
    bl_idname = "massa.gen_ind_20_centrifuge"
    bl_label = "IND Centrifuge"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # 1. Style Enum
    style: EnumProperty(
        name="Centrifuge Type",
        items=[
            ("DECANTER", "Decanter", "Horizontal screw centrifuge"),
            ("DISC_STACK", "Disc Stack", "Vertical high-speed separator"),
            ("BASKET", "Basket", "Top-loading industrial centrifuge"),
        ],
        default="DECANTER"
    )

    # 2. Dimensions
    radius: FloatProperty(name="Radius", default=0.6, min=0.2)
    height: FloatProperty(name="Length/Height", default=2.5, min=0.5)
    motor_h: FloatProperty(name="Motor Size", default=0.8, min=0.2)

    # 3. Details
    feet_count: IntProperty(name="Feet Count", default=4, min=3, max=8)
    pipe_connects: IntProperty(name="Pipes", default=2, min=0, max=6)
    lid_thickness: FloatProperty(name="Casing Thick", default=0.1, min=0.01, max=0.2)

    control_box: BoolProperty(name="Control Box", default=True)
    view_port: BoolProperty(name="View Port", default=False)
    rpm_gauge: BoolProperty(name="RPM Gauge", default=True)

    base_height: FloatProperty(name="Base Height", default=0.5, min=0.1)
    base_width_scale: FloatProperty(name="Base Width", default=1.0, min=0.5, max=2.0)
    pipe_length: FloatProperty(name="Pipe Length", default=0.5, min=0.1)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Casing/Body", "uv": "UNWRAP", "phys": "METAL_STEEL"},
            1: {"name": "Motor/Drive", "uv": "BOX", "phys": "METAL_IRON"},
            2: {"name": "Fittings/Pipes", "uv": "BOX", "phys": "METAL_CHROME"},
            3: {"name": "Glass/View", "uv": "FIT", "phys": "GLASS"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions")
        box.prop(self, "radius")
        box.prop(self, "height")
        box.prop(self, "motor_h")

        box = layout.box()
        box.label(text="Base")
        box.prop(self, "base_height")
        box.prop(self, "feet_count")

        box = layout.box()
        box.label(text="Details")
        col = box.column(align=True)
        col.prop(self, "pipe_connects")
        col.prop(self, "lid_thickness")
        col.prop(self, "control_box")
        col.prop(self, "view_port")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        rad = self.radius
        ln = self.height
        mh = self.motor_h
        bh = self.base_height

        if self.style == "DECANTER":
            # Horizontal cylinder with tapered end
            # Base Frame
            frame_w = rad * 2.5 * self.base_width_scale
            frame_l = ln * 1.2
            builder.create_box(frame_w, frame_l, bh, center=Vector((0, 0, bh/2)))
            builder.tag_slot(1) # Iron base

            # Main Bowl (Cylinder)
            bowl_z = bh + rad + 0.1
            bowl_len = ln * 0.7

            # Cylindrical Section
            builder.create_cylinder(radius=rad, depth=bowl_len, center=Vector((0,0,0)))
            builder.rotate(90, axis='X')
            builder.translate(0, -ln*0.1, bowl_z)
            builder.tag_slot(0)

            # Conical Section (Cone)
            cone_len = ln * 0.3
            r1 = rad
            r2 = rad * 0.4

            # MassaBuilder cone is vertical.
            # Create at origin
            builder.create_cone(radius_bottom=r1, radius_top=r2, depth=cone_len, center=Vector((0,0,0)))
            # Rotate -90 X to point +Y ?
            # Cylinder above: center Y = -ln*0.1. Length bowl_len. Ends at +/- bowl_len/2 + center.
            # Y range: -ln*0.1 - bowl/2 to -ln*0.1 + bowl/2.
            # Let's align properly.
            # Cylinder Y-Start: -bowl_len/2. Y-End: +bowl_len/2.
            # Cone attaches at Y-End.

            bowl_y_end = -ln*0.1 + bowl_len/2

            # Cone
            # Default cone: Base at -depth/2, Top at depth/2.
            # Rotate -90 X -> Base at Y-, Top at Y+.
            # So Top (Small) is at +Y.

            builder.rotate(-90, axis='X')
            builder.translate(0, bowl_y_end + cone_len/2, bowl_z)
            builder.tag_slot(0)

            # Motor Housing (Box/Cylinder at other end)
            motor_y = -ln*0.1 - bowl_len/2 - mh/2
            builder.create_box(rad*2.2, mh, rad*2.2, center=Vector((0, motor_y, bowl_z)))
            builder.tag_slot(1)

            # Belt guard?

        elif self.style == "DISC_STACK":
            # Vertical Cylinder/Bulb
            # Base
            builder.create_cylinder(radius=rad*1.2, depth=bh, center=Vector((0,0,bh/2)))
            builder.tag_slot(1)

            # Bowl (Bottom Cone + Mid Cylinder + Top Cone)
            bowl_start = bh

            # Bottom Cone
            h1 = ln * 0.2
            builder.create_cone(radius_bottom=rad*0.5, radius_top=rad, depth=h1, center=Vector((0,0,bowl_start + h1/2)))
            builder.tag_slot(0)

            # Mid Cylinder
            h2 = ln * 0.4
            builder.create_cylinder(radius=rad, depth=h2, center=Vector((0,0,bowl_start + h1 + h2/2)))
            builder.tag_slot(0)

            # Top Dome/Cone
            h3 = ln * 0.2
            builder.create_cone(radius_bottom=rad, radius_top=rad*0.3, depth=h3, center=Vector((0,0,bowl_start + h1 + h2 + h3/2)))
            builder.tag_slot(0)

            # Motor? Usually underneath or side belt drive.
            # Add Side Motor
            mx = rad + mh/2
            builder.create_cylinder(radius=mh/2, depth=bh*1.5, center=Vector((mx, 0, bh*0.75)))
            builder.tag_slot(1)

        elif self.style == "BASKET":
            # Boxy/Cylindrical top loader
            # Legs (Use feet_count)
            leg_h = bh
            cnt = max(3, self.feet_count)
            for i in range(cnt):
                ang = (i / cnt) * 360
                lx = math.cos(math.radians(ang)) * rad
                ly = math.sin(math.radians(ang)) * rad
                builder.create_cylinder(radius=0.1, depth=leg_h, center=Vector((lx,ly,leg_h/2)))
                builder.tag_slot(1)

            # Main Tank
            tank_h = ln * 0.6
            z_tank = leg_h + tank_h/2
            builder.create_cylinder(radius=rad, depth=tank_h, center=Vector((0,0,z_tank)))
            builder.tag_slot(0)

            # View Port
            if self.view_port:
                # Add window on side
                vp_rad = tank_h * 0.3
                builder.create_cylinder(radius=vp_rad, depth=0.1, center=Vector((0,0,0)))
                builder.rotate(90, axis='Y')
                builder.translate(rad, 0, z_tank)
                builder.tag_slot(3) # Glass

            # Lid (Hinged?)
            lid_z = leg_h + tank_h
            builder.create_cylinder(radius=rad + 0.05, depth=self.lid_thickness, center=Vector((0,0,lid_z + self.lid_thickness/2)))
            builder.tag_slot(0)

            # Motor on top (Vertical drive)
            builder.create_cylinder(radius=rad*0.3, depth=mh, center=Vector((0,0,lid_z + self.lid_thickness + mh/2)))
            builder.tag_slot(1)

        # Common Details

        # Pipe Connections
        if self.pipe_connects > 0:
            # Add pipes sticking out
            pr = 0.1
            pl = self.pipe_length
            for i in range(self.pipe_connects):
                ang = (i / self.pipe_connects) * 360
                px = math.cos(math.radians(ang)) * (rad + 0.3)
                py = math.sin(math.radians(ang)) * (rad + 0.3)

                pz = bh + ln*0.5
                if self.style == "DECANTER": pz = bh + rad

                # Cylinder pipe
                builder.create_cylinder(radius=pr, depth=pl, center=Vector((0,0,0)))
                # Rotate to point out?
                # Rotate Z by ang? No, rotate Y 90 then Z?
                # Rotate pipe (which is Z) to point radial.
                # Axis of rotation: (-sin, cos, 0).
                # Angle 90.
                axis = Vector((-math.sin(math.radians(ang)), math.cos(math.radians(ang)), 0))

                # MassaBuilder.rotate takes axis='X' etc or Vector?
                # My implementation passes axis to Matrix.Rotation.
                # Matrix.Rotation supports Vector.

                # Need to import Matrix/Vector in builder if not available?
                # It's imported in cartridge.

                # Create at origin
                # Rotate
                # Translate

                # Correct rotation:
                # Default Cylinder is Z.
                # We want it to point to (px, py, 0).
                # Rotate 90 deg around tangent vector.

                rot_mat = Matrix.Rotation(math.radians(90), 4, axis)
                builder.transform(rot_mat)

                builder.translate(px, py, pz)
                builder.tag_slot(2)

        # Control Box
        if self.control_box:
            # Box attached to side/frame
            bx = rad + 0.2
            bz = bh + 0.5
            builder.create_box(0.3, 0.5, 0.6, center=Vector((bx, 0, bz)))
            builder.tag_slot(1)

            if self.rpm_gauge:
                builder.create_cylinder(radius=0.1, depth=0.05, center=Vector((0,0,0)))
                builder.rotate(90, axis='Y')
                builder.translate(bx + 0.15, 0, bz + 0.1)
                builder.tag_slot(3)

        # Socket (Floor)
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
