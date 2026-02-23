import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_10: Generator",
    "id": "ind_10_generator",
    "icon": "MOD_EXPLODE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_IndGenerator(Massa_OT_Base):
    bl_idname = "massa.gen_ind_10_generator"
    bl_label = "IND_10: Generator"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    style: EnumProperty(
        name="Style",
        items=[
            ("DIESEL", "Diesel Gen", "Large industrial box"),
            ("TURBINE", "Gas Turbine", "Cylindrical power unit"),
            ("PORTABLE", "Portable", "Small frame generator"),
        ],
        default="DIESEL",
    )

    length: FloatProperty(name="Length (Y)", default=2.5, min=0.5)
    width: FloatProperty(name="Width (X)", default=1.2, min=0.5)
    height: FloatProperty(name="Height (Z)", default=1.5, min=0.5)

    # New Parameters
    exhaust_height: FloatProperty(name="Exhaust Height", default=0.5, min=0.1)
    panel_inset: FloatProperty(name="Panel Inset", default=0.05, min=0.0)
    skid_width: FloatProperty(name="Skid Width", default=0.2, min=0.05)
    frame_tube_radius: FloatProperty(name="Tube Radius", default=0.05, min=0.01)

    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Body/Frame", "uv": "BOX", "phys": "METAL_PAINTED"},
            1: {"name": "Engine/Details", "uv": "BOX", "phys": "METAL_DARK"},
            2: {"name": "Pipes/Vents", "uv": "CYLINDER", "phys": "METAL_STEEL"},
            9: {"name": "Socket", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.label(text="TYPE", icon="MOD_EXPLODE")
        layout.prop(self, "style", text="")

        layout.separator()
        layout.label(text="DIMENSIONS", icon="Driver")
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")

        layout.separator()
        layout.label(text="DETAILS", icon="MOD_BUILD")
        col = layout.column(align=True)
        col.prop(self, "exhaust_height")
        col.prop(self, "panel_inset")
        col.prop(self, "skid_width")

        if self.style == 'PORTABLE':
            col.prop(self, "frame_tube_radius")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        l, w, h = self.length, self.width, self.height

        if self.style == 'DIESEL':
            # Boxy housing
            # Base/Skid
            skid_h = self.skid_width
            builder.create_box(w, l, skid_h, center=Vector((0, l/2, skid_h/2))) \
                   .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Main Box
            box_h = h - skid_h
            builder.create_box(w*0.95, l*0.9, box_h, center=Vector((0, l/2, skid_h + box_h/2))) \
                   .tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Vents (Inset on sides)
            vent_w = 0.05
            vent_h = box_h * 0.6
            vent_l = l * 0.3

            # Left Vent
            builder.create_box(vent_w, vent_l, vent_h, center=Vector((-w*0.48, l*0.7, h/2))) \
                   .tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Right Vent
            builder.create_box(vent_w, vent_l, vent_h, center=Vector((w*0.48, l*0.7, h/2))) \
                   .tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Exhaust Pipe (Top)
            pipe_r = 0.1
            pipe_h = self.exhaust_height
            builder.create_cylinder(radius=pipe_r, depth=pipe_h, segments=12, center=Vector((0,0,0)))

            cyl_faces = builder.active_faces[:]
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            caps = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
            builder.active_faces = caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.active_faces = cyl_faces
            builder.translate(0, l*0.8, h + pipe_h/2)

            # Control Panel (Front)
            # Use panel_inset to inset front face instead of new box if possible?
            # Or just position new box.
            panel_w = w * 0.6
            panel_h = h * 0.4
            # If panel_inset is large, maybe negative extrude?
            # Let's stick to additive for now, or inset logic.
            # "Panel Inset" usually implies sunken.
            # Select Front Face of Main Box? Hard to target specifically among all boxes.
            # Additive Panel Box slightly protruded or sunk.

            # Let's make a sunken frame if inset > 0
            if self.panel_inset > 0.01:
                # Create frame
                builder.create_box(panel_w, self.panel_inset, panel_h, center=Vector((0, l*0.05, h*0.6))) \
                       .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
            else:
                # Flush/Protruding
                builder.create_box(panel_w, 0.05, panel_h, center=Vector((0, l*0.05, h*0.6))) \
                       .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Sockets
            # Power Output (Front Panel)
            builder.create_grid(1, 1, size=0.3).rotate(90, 'X').translate(-panel_w*0.3, 0, h*0.5) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')
            # Fuel (Side)
            builder.create_grid(1, 1, size=0.2).rotate(90, 'Y').translate(w/2, l*0.2, h*0.3) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        elif self.style == 'TURBINE':
            # Cylindrical Body
            r = w / 2
            builder.create_cylinder(radius=r, depth=l, segments=24, center=Vector((0,0,0)))

            cyl_faces = builder.active_faces[:]
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            # Caps
            caps = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
            builder.active_faces = caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            # Rotate
            builder.active_faces = cyl_faces
            builder.rotate(90, 'X').translate(0, l/2, r + 0.2) # Lifted

            # Base
            builder.create_box(w*1.2, l, 0.2, center=Vector((0, l/2, 0.1))) \
                   .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Intake (Front Cone)
            # Cone from Y=0 facing -Y
            # Create cone at origin (Z), rotate -90 X.
            builder.create_cone(radius_bottom=r*1.2, radius_top=r, depth=0.5, segments=24, center=Vector((0,0,0)))
            cyl_faces = builder.active_faces[:]
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            builder.rotate(-90, 'X').translate(0, -0.25, r + 0.2)

            # Exhaust (Back Box)
            builder.create_box(w, 0.5, w, center=Vector((0, l + 0.25, r + 0.2))) \
                   .tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Sockets
            # Exhaust (Back)
            builder.create_grid(1, 1, size=r).rotate(90, 'X').translate(0, l + 0.5, r + 0.2) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        elif self.style == 'PORTABLE':
            # Open Frame (Red/Black tubes)
            frame_thick = self.frame_tube_radius

            corners = [
                Vector((-w/2, 0, 0)),
                Vector((w/2, 0, 0)),
                Vector((w/2, l, 0)),
                Vector((-w/2, l, 0)),
                Vector((-w/2, 0, h)),
                Vector((w/2, 0, h)),
                Vector((w/2, l, h)),
                Vector((-w/2, l, h))
            ]

            # Helper for frame strut
            def strut(p1, p2):
                vec = p2 - p1
                dist = vec.length
                mid = (p1 + p2) / 2

                builder.create_cylinder(radius=frame_thick, depth=dist, segments=8, center=Vector((0,0,0)))
                # Safe UVs (Simplified, skip caps box map for thin struts)
                builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER')

                builder.align_normal_to_vector(vec)
                builder.translate(mid.x, mid.y, mid.z)

            # Build Frame (12 edges)
            # Bottom Loop
            strut(corners[0], corners[1])
            strut(corners[1], corners[2])
            strut(corners[2], corners[3])
            strut(corners[3], corners[0])
            # Top Loop
            strut(corners[4], corners[5])
            strut(corners[5], corners[6])
            strut(corners[6], corners[7])
            strut(corners[7], corners[4])
            # Verticals
            strut(corners[0], corners[4])
            strut(corners[1], corners[5])
            strut(corners[2], corners[6])
            strut(corners[3], corners[7])

            # Engine Block inside
            eng_w = w * 0.6
            eng_l = l * 0.6
            eng_h = h * 0.5
            builder.create_box(eng_w, eng_l, eng_h, center=Vector((0, l/2, h/2))) \
                   .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Fuel Tank on top
            builder.create_box(w*0.8, l*0.8, 0.2, center=Vector((0, l/2, h - 0.2))) \
                   .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Sockets
            # Panel socket
            builder.create_grid(1, 1, size=0.2).rotate(90, 'X').translate(w/4, 0, h/2) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        # Anchor
        builder.create_grid(1, 1, size=0.1).translate(0, 0, 0) \
               .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        builder.clean()
