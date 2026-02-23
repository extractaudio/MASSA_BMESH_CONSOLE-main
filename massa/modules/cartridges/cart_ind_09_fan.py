import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_09: Ventilation Fan",
    "id": "ind_09_fan",
    "icon": "FORCE_WIND",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_IndFan(Massa_OT_Base):
    bl_idname = "massa.gen_ind_09_fan"
    bl_label = "IND_09: Fan"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    style: EnumProperty(
        name="Style",
        items=[
            ("WALL", "Wall Mount", "Square housing"),
            ("INLINE", "Inline Duct", "Cylindrical tube"),
            ("ROOF", "Roof Top", "Mushroom cowl"),
        ],
        default="WALL",
    )

    size: FloatProperty(name="Size", default=1.0, min=0.3)
    depth: FloatProperty(name="Depth", default=0.5, min=0.1)

    blade_count: IntProperty(name="Blades", default=6, min=2, max=12)

    # New Parameters
    hub_radius: FloatProperty(name="Hub Radius", default=0.2, min=0.1, description="Size of center hub")
    blade_pitch: FloatProperty(name="Blade Pitch", default=20.0, min=-45.0, max=45.0)
    casing_thickness: FloatProperty(name="Casing Thick", default=0.05, min=0.01)
    grill_bars: IntProperty(name="Grill Bars", default=5, min=2, max=10)

    has_grill: BoolProperty(name="Add Grill", default=True)

    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Housing", "uv": "BOX", "phys": "METAL_PAINTED"},
            1: {"name": "Fan Blades", "uv": "BOX", "phys": "PLASTIC_HARD"},
            2: {"name": "Grill/Motor", "uv": "BOX", "phys": "METAL_DARK"},
            9: {"name": "Socket", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.label(text="STYLE", icon="FORCE_WIND")
        layout.prop(self, "style", text="")

        layout.separator()
        layout.label(text="DIMENSIONS", icon="Driver")
        col = layout.column(align=True)
        col.prop(self, "size")
        col.prop(self, "depth")

        layout.separator()
        layout.label(text="COMPONENTS", icon="MOD_PARTICLES")
        col = layout.column(align=True)
        col.prop(self, "hub_radius")
        col.prop(self, "casing_thickness")

        layout.prop(self, "blade_count")
        col.prop(self, "blade_pitch")

        layout.prop(self, "has_grill")
        if self.has_grill:
            col.prop(self, "grill_bars")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        s = self.size
        d = self.depth

        # Helper: Create Fan Assembly (Hub + Blades)
        def create_fan(center, radius, axis_vec):
            # Hub
            hub_r = radius * self.hub_radius
            hub_d = 0.1
            builder.create_cylinder(radius=hub_r, depth=hub_d, segments=12, center=Vector((0,0,0)))
            # Safe UVs
            cyl_faces = builder.active_faces[:]
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            caps = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
            builder.active_faces = caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            # Move Hub
            builder.active_faces = cyl_faces
            builder.align_normal_to_vector(axis_vec)
            builder.translate(center.x, center.y, center.z)

            # Blades
            blade_len = radius - hub_r - 0.02
            blade_w = radius * 0.3
            blade_thick = 0.02

            for i in range(self.blade_count):
                angle = (2 * math.pi / self.blade_count) * i

                # Create blade at X axis
                builder.create_box(blade_w, blade_thick, blade_len, center=Vector((0, 0, hub_r + blade_len/2)))
                # Pitch
                builder.rotate(self.blade_pitch, 'Y')
                # Rotate around Hub Z to position
                builder.rotate(math.degrees(angle), 'Z')

                # Align Hub Z to actual Axis
                # Wait, align_normal_to_vector rotates entire selection.
                # If I want to align the "Fan Assembly" Z to `axis_vec`, I should construct in Z and rotate at end.
                # But I am building piece by piece.
                # So I must apply the final transform to each piece.

                # Current state: Blade is around (0,0,0) aligned with Z.
                # I need to align Z to `axis_vec` and move to `center`.

                # But 'align_normal_to_vector' uses selection normal. Blade normal is complex.
                # Better: Construct Rotation Matrix from Z to axis_vec.
                rot_quat = Vector((0,0,1)).rotation_difference(axis_vec)
                rot_mat = rot_quat.to_matrix().to_4x4()

                builder.transform(rot_mat)
                builder.translate(center.x, center.y, center.z)

                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        if self.style == 'WALL':
            # Box Housing
            builder.create_box(s, d, s, center=Vector((0, d/2, s/2))) \
                   .tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Cutout? Or simplified: Just place fan on surface.
            # Add Rim
            rim_r = s * 0.45
            builder.create_cylinder(radius=rim_r, depth=d+0.02, segments=24, center=Vector((0,0,0)))

            # Use safe UVs for rim cylinder
            cyl_faces = builder.active_faces[:]
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            caps = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
            builder.active_faces = caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')

            builder.active_faces = cyl_faces
            builder.rotate(90, 'X').translate(0, d/2, s/2)

            # Fan inside
            create_fan(Vector((0, d/2, s/2)), rim_r * 0.9, Vector((0, 1, 0))) # Axis Y

            # Grill
            if self.has_grill:
                # Simple bars
                gb = self.grill_bars
                for i in range(gb):
                    offset = (i - (gb-1)/2) * (rim_r * 1.5 / gb)
                    builder.create_box(0.02, 0.02, s*0.9, center=Vector((offset, 0, s/2))) \
                           .tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Socket (Back)
            builder.create_grid(1, 1, size=s*0.8).rotate(90, 'X').translate(0, d, s/2) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        elif self.style == 'INLINE':
            # Cylinder Housing
            r = s / 2
            builder.create_cylinder(radius=r, depth=d, segments=24, center=Vector((0,0,0)))

            cyl_faces = builder.active_faces[:]
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            # Caps open? "Inline duct".
            # Usually hollow. But we make solid volume.
            # Just mark caps as "Hollow/Socket"?
            # Let's keep caps solid for simplicity, maybe inset slightly.

            caps = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
            builder.active_faces = caps
            builder.inset(0.05, depth=-0.05)
            builder.tag_uvs(scale=self.uv_scale, projection='BOX') # Inset faces

            # Transform Housing (Align to Y)
            # Select Linked to capture all geometry (rims, insets, outer)
            if builder.active_faces:
                res = bmesh.ops.select_linked(bm, faces=[builder.active_faces[0]])
                builder.active_faces = [f for f in res['geom'] if isinstance(f, bmesh.types.BMFace)]

            builder.rotate(90, 'X').translate(0, d/2, s/2)

            # Fan inside
            create_fan(Vector((0, d/2, s/2)), r * 0.9, Vector((0, 1, 0)))

            # Flanges
            flange_r = r * 1.2
            builder.create_cylinder(radius=flange_r, depth=0.05, segments=24, center=Vector((0,0,0))) \
                   .rotate(90, 'X').translate(0, 0, s/2).tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            builder.create_cylinder(radius=flange_r, depth=0.05, segments=24, center=Vector((0,0,0))) \
                   .rotate(90, 'X').translate(0, d, s/2).tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Sockets
            builder.create_grid(1, 1, size=r*1.5).rotate(90, 'X').translate(0, d, s/2) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')
            builder.create_grid(1, 1, size=r*1.5).rotate(-90, 'X').translate(0, 0, s/2) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        elif self.style == 'ROOF':
            # Mushroom Cowl
            # Base Box
            base_h = d * 0.5
            builder.create_box(s, s, base_h, center=Vector((0, 0, base_h/2))) \
                   .tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Cowl (Cap)
            # Cylinder top
            cap_r = s * 0.6
            cap_h = d * 0.3
            builder.create_cylinder(radius=cap_r, depth=cap_h, segments=24, center=Vector((0,0,0)))
            cyl_faces = builder.active_faces[:]
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            caps = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
            builder.active_faces = caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.active_faces = cyl_faces
            builder.translate(0, 0, base_h + cap_h + 0.1) # Gap

            # Fan visible in gap
            create_fan(Vector((0, 0, base_h + 0.05)), cap_r * 0.8, Vector((0, 0, 1)))

            # Socket (Bottom)
            builder.create_grid(1, 1, size=s*0.8).translate(0, 0, 0) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        # Anchor
        builder.create_grid(1, 1, size=0.1).translate(0, 0, 0) \
               .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        builder.clean()
