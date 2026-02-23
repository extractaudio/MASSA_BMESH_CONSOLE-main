import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_06: Conveyor Belt",
    "id": "ind_06_conveyor",
    "icon": "MOD_ARRAY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_IndConveyor(Massa_OT_Base):
    bl_idname = "massa.gen_ind_06_conveyor"
    bl_label = "IND_06: Conveyor"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    style: EnumProperty(
        name="Style",
        items=[
            ("ROLLER", "Roller Bed", "Individual gravity rollers"),
            ("BELT", "Flat Belt", "Continuous rubber belt"),
            ("SLAT", "Slat Chain", "Heavy duty metal slats"),
        ],
        default="ROLLER",
    )

    length: FloatProperty(name="Length (Y)", default=4.0, min=0.5)
    width: FloatProperty(name="Width (X)", default=1.0, min=0.3)
    height: FloatProperty(name="Height (Z)", default=0.8, min=0.1)

    rail_height: FloatProperty(name="Rail Height", default=0.15, min=0.05)
    rail_thick: FloatProperty(name="Rail Thickness", default=0.05, min=0.01)

    # New Parameters
    rail_width: FloatProperty(name="Rail Width (Ext)", default=0.0, min=0.0, description="Extra width on rails")
    leg_thickness: FloatProperty(name="Leg Thickness", default=0.1, min=0.02)
    guard_rail_height: FloatProperty(name="Guard Height", default=0.05, min=0.0)
    motor_scale: FloatProperty(name="Motor Scale", default=1.0, min=0.1)

    roller_radius: FloatProperty(name="Roller Radius", default=0.04, min=0.01)
    roller_spacing: FloatProperty(name="Roller Spacing", default=0.15, min=0.05)

    has_legs: BoolProperty(name="Add Legs", default=True)
    leg_spacing: FloatProperty(name="Leg Spacing", default=2.0, min=0.5)

    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame/Structure", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Conveyor Surface", "uv": "BOX", "phys": "PLASTIC_RUBBER"}, # Rollers/Belt
            2: {"name": "Details/Motor", "uv": "BOX", "phys": "METAL_DARK"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.label(text="STYLE & DIMS", icon="MOD_ARRAY")
        layout.prop(self, "style", text="")

        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")

        layout.separator()
        layout.label(text="STRUCTURE", icon="MESH_GRID")
        col = layout.column(align=True)
        col.prop(self, "rail_height")
        col.prop(self, "rail_thick")
        col.prop(self, "rail_width")
        col.prop(self, "guard_rail_height")
        col.prop(self, "motor_scale")

        if self.style == 'ROLLER' or self.style == 'SLAT':
            layout.prop(self, "roller_radius", text="Element Size")
            layout.prop(self, "roller_spacing")

        layout.separator()
        layout.label(text="SUPPORTS", icon="OUTLINER_OB_ARMATURE")
        layout.prop(self, "has_legs")
        if self.has_legs:
            layout.prop(self, "leg_spacing")
            layout.prop(self, "leg_thickness")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        l, w, h = self.length, self.width, self.height
        rh, rt = self.rail_height, self.rail_thick
        rw_ext = self.rail_width

        # 1. Side Rails (Frame) - Slot 0
        # Left Rail
        builder.create_box(rt + rw_ext, l, rh, center=Vector((-w/2 + (rt+rw_ext)/2, l/2, h - rh/2))) \
               .tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Right Rail
        builder.create_box(rt + rw_ext, l, rh, center=Vector((w/2 - (rt+rw_ext)/2, l/2, h - rh/2))) \
               .tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Guard Rails (Top of Side Rails)
        if self.guard_rail_height > 0:
            gh = self.guard_rail_height
            gt = max(0.01, rt * 0.2)
            # Left Guard
            builder.create_box(gt, l, gh, center=Vector((-w/2 + gt/2, l/2, h + gh/2))) \
                   .tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Right Guard
            builder.create_box(gt, l, gh, center=Vector((w/2 - gt/2, l/2, h + gh/2))) \
                   .tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Motor Box (Side)
        if self.motor_scale > 0.1:
            ms = 0.3 * self.motor_scale
            builder.create_box(ms, ms, ms, center=Vector((-w/2 - ms/2, l * 0.1, h - rh/2))) \
                   .tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 2. Conveyor Surface - Slot 1
        inner_w = w - (rt * 2) - 0.02 # Gap
        z_surf = h - (rh * 0.3) # Slightly below top of rail

        if self.style == 'BELT':
            # Continuous Belt Box
            belt_thick = 0.05
            builder.create_box(inner_w, l, belt_thick, center=Vector((0, l/2, z_surf))) \
                   .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # End Pulleys (Cylinders)
            r_pulley = belt_thick * 1.5
            # Front Pulley (Y=0)
            builder.create_cylinder(radius=r_pulley, depth=inner_w, segments=12, center=Vector((0,0,0)))
            cyl_faces = builder.active_faces[:]
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            builder.active_faces = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.active_faces = cyl_faces
            builder.rotate(90, 'Y').translate(0, 0, z_surf)

            # Back Pulley (Y=L)
            builder.create_cylinder(radius=r_pulley, depth=inner_w, segments=12, center=Vector((0,0,0)))
            cyl_faces = builder.active_faces[:]
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            builder.active_faces = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.active_faces = cyl_faces
            builder.rotate(90, 'Y').translate(0, l, z_surf)

        elif self.style == 'ROLLER':
            # Array of Rollers
            spacing = self.roller_spacing
            count = int(l / spacing)
            r = self.roller_radius

            for i in range(count):
                y = (i * spacing) + (spacing / 2)
                if y > l: break

                builder.create_cylinder(radius=r, depth=inner_w, segments=12, center=Vector((0,0,0)))
                cyl_faces = builder.active_faces[:]
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
                builder.active_faces = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')
                builder.active_faces = cyl_faces
                builder.rotate(90, 'Y').translate(0, y, z_surf)

        elif self.style == 'SLAT':
            # Array of Boxes
            spacing = self.roller_spacing
            slat_depth = spacing * 0.9 # Gap
            slat_thick = 0.02
            count = int(l / spacing)

            for i in range(count):
                y = (i * spacing) + (spacing / 2)
                if y > l - (slat_depth/2): break

                builder.create_box(inner_w, slat_depth, slat_thick, center=Vector((0, y, z_surf))) \
                       .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 3. Legs - Slot 0
        if self.has_legs:
            leg_w = self.leg_thickness
            leg_d = self.leg_thickness
            leg_h = h - rh
            if leg_h > 0:
                spacing = self.leg_spacing
                count_legs = int(l / spacing) + 1
                if count_legs < 2: count_legs = 2

                real_spacing = l / (count_legs - 1) if count_legs > 1 else 0

                for i in range(count_legs):
                    y = i * real_spacing

                    # Left Leg
                    builder.create_box(leg_w, leg_d, leg_h, center=Vector((-w/2 + (rt+rw_ext)/2, y, leg_h/2))) \
                           .tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

                    # Right Leg
                    builder.create_box(leg_w, leg_d, leg_h, center=Vector((w/2 - (rt+rw_ext)/2, y, leg_h/2))) \
                           .tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

                    # Cross brace (low)
                    if w > 0.4:
                        brace_z = leg_h * 0.3
                        builder.create_box(w - (rt*2), leg_d*0.8, leg_d*0.8, center=Vector((0, y, brace_z))) \
                               .tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 4. Sockets (Start/End)
        # Start (Y=0)
        builder.create_grid(1, 1, size=0.1).rotate(-90, 'X').translate(0, 0, h/2) \
               .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX') # Socket pointing -Y (Back)

        # End (Y=L)
        builder.create_grid(1, 1, size=0.1).rotate(90, 'X').translate(0, l, h/2) \
               .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX') # Socket pointing +Y (Forward)

        # Anchor (Bottom Center)
        builder.create_grid(1, 1, size=0.1).translate(0, l/2, 0) \
               .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        # 5. Cleanup
        builder.clean() # Merge overlapping geometry if needed
