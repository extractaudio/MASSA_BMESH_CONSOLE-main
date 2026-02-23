import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_08: Storage Tank",
    "id": "ind_08_tank",
    "icon": "MESH_UVSPHERE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_IndTank(Massa_OT_Base):
    bl_idname = "massa.gen_ind_08_tank"
    bl_label = "IND_08: Tank"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    style: EnumProperty(
        name="Style",
        items=[
            ("VERTICAL", "Vertical", "Standing Cylinder"),
            ("HORIZONTAL", "Horizontal", "Laying Cylinder"),
            ("SPHERICAL", "Spherical", "Gas Tank"),
        ],
        default="VERTICAL",
    )

    radius: FloatProperty(name="Radius", default=1.5, min=0.5)
    height: FloatProperty(name="Height (Z/Length)", default=4.0, min=1.0)

    leg_height: FloatProperty(name="Leg Height", default=1.0, min=0.1)

    has_ladder: BoolProperty(name="Add Ladder", default=True)

    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Tank Body", "uv": "CYLINDER", "phys": "METAL_PAINTED"},
            1: {"name": "Structure", "uv": "BOX", "phys": "METAL_STEEL"}, # Legs
            2: {"name": "Details", "uv": "BOX", "phys": "METAL_DARK"}, # Ladder/Caps
            9: {"name": "Socket", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.label(text="STYLE", icon="MESH_UVSPHERE")
        layout.prop(self, "style", text="")

        layout.separator()
        layout.label(text="DIMENSIONS", icon="Driver")
        col = layout.column(align=True)
        col.prop(self, "radius")
        if self.style != 'SPHERICAL':
            col.prop(self, "height", text="Length/Height")

        layout.separator()
        layout.label(text="SUPPORTS", icon="OUTLINER_OB_ARMATURE")
        col = layout.column(align=True)
        col.prop(self, "leg_height")
        layout.prop(self, "has_ladder")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        r = self.radius
        h = self.height # Used as Length for Horizontal
        lh = self.leg_height

        tank_z_base = lh # Bottom of tank

        # Helper: Ladder
        def create_ladder(base_pos, top_z):
            # Simple ladder attached to tank
            # Vertical rails
            lad_w = 0.5
            rail_thick = 0.05
            lad_h = top_z - base_pos.z

            # Left Rail
            builder.create_box(rail_thick, rail_thick, lad_h, center=Vector((base_pos.x - lad_w/2, base_pos.y, base_pos.z + lad_h/2))) \
                   .tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Right Rail
            builder.create_box(rail_thick, rail_thick, lad_h, center=Vector((base_pos.x + lad_w/2, base_pos.y, base_pos.z + lad_h/2))) \
                   .tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Rungs
            rung_spacing = 0.3
            rungs = int(lad_h / rung_spacing)
            for i in range(rungs):
                z = base_pos.z + (i * rung_spacing) + 0.1
                builder.create_box(lad_w, rail_thick*0.8, rail_thick*0.8, center=Vector((base_pos.x, base_pos.y, z))) \
                       .tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        if self.style == 'VERTICAL':
            # Cylinder standing up
            # Create at origin
            builder.create_cylinder(radius=r, depth=h, segments=24, center=Vector((0,0,0)))

            cyl_faces = builder.active_faces[:]
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            caps = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
            builder.active_faces = caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')

            builder.active_faces = cyl_faces
            builder.translate(0, 0, tank_z_base + h/2)

            # Legs (4)
            leg_w = 0.15
            for i in range(4):
                angle = (math.pi/2) * i + (math.pi/4)
                lx = (r - 0.2) * math.cos(angle)
                ly = (r - 0.2) * math.sin(angle)

                builder.create_box(leg_w, leg_w, lh, center=Vector((lx, ly, lh/2))) \
                       .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Ladder (Side)
            if self.has_ladder:
                # Attached to X+ side, offset by R
                lad_pos = Vector((r + 0.1, 0, 0))
                create_ladder(lad_pos, tank_z_base + h)

            # Sockets
            # Top
            builder.create_grid(1, 1, size=0.5).translate(0, 0, tank_z_base + h) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')
            # Side (Bottom)
            builder.create_grid(1, 1, size=0.5).rotate(90, 'Y').translate(r, 0, tank_z_base + h*0.1) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        elif self.style == 'HORIZONTAL':
            # Cylinder laying down (Y axis)
            builder.create_cylinder(radius=r, depth=h, segments=24, center=Vector((0,0,0)))

            cyl_faces = builder.active_faces[:]
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            caps = [f for f in cyl_faces if abs(f.normal.z) > 0.8]
            builder.active_faces = caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')

            builder.active_faces = cyl_faces
            builder.rotate(90, 'X').translate(0, 0, tank_z_base + r)

            # Cradles (2)
            cradle_w = r * 2.2
            cradle_thick = 0.3
            cradle_h = lh + r * 0.5 # Cradle goes up sides a bit

            y_offsets = [-h/3, h/3]
            for y in y_offsets:
                # Box for base
                builder.create_box(cradle_w, cradle_thick, lh, center=Vector((0, y, lh/2))) \
                       .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Cutout? Or simplified U-shape.
                # Just add side pillars
                pillar_h = r * 0.8
                px = r + 0.1
                builder.create_box(0.2, cradle_thick, pillar_h, center=Vector((-px, y, lh + pillar_h/2))) \
                       .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
                builder.create_box(0.2, cradle_thick, pillar_h, center=Vector((px, y, lh + pillar_h/2))) \
                       .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            if self.has_ladder:
                lad_pos = Vector((0, -h/2 - 0.5, 0)) # End ladder
                create_ladder(lad_pos, tank_z_base + r) # Up to top

            # Sockets
            # Top Center
            builder.create_grid(1, 1, size=0.5).translate(0, 0, tank_z_base + r + r) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')
            # End Cap
            builder.create_grid(1, 1, size=0.5).rotate(90, 'X').translate(0, h/2, tank_z_base + r) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        elif self.style == 'SPHERICAL':
            # Sphere
            ret = bmesh.ops.create_icosphere(bm, subdivisions=2, diameter=r*2)
            verts = ret['verts']
            # Move to height
            bmesh.ops.translate(bm, vec=(0, 0, tank_z_base + r), verts=verts)

            builder.active_verts = verts
            builder.active_faces = [f for f in ret['faces']] # Correct way?
            # Actually create_icosphere returns faces.

            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX') # BOX for sphere to avoid poles

            # Legs (3 or 4)
            leg_w = 0.2
            for i in range(3):
                angle = (2*math.pi/3) * i
                lx = (r * 0.8) * math.cos(angle)
                ly = (r * 0.8) * math.sin(angle)

                # Leg length depends on sphere curvature? No, simple vertical legs.
                # Intersection is hidden inside sphere.
                leg_len = lh + (r * 0.2) # Embed slightly

                builder.create_box(leg_w, leg_w, leg_len, center=Vector((lx, ly, leg_len/2))) \
                       .tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            if self.has_ladder:
                lad_pos = Vector((r + 0.2, 0, 0))
                create_ladder(lad_pos, tank_z_base + r) # To equator

            # Sockets
            builder.create_grid(1, 1, size=0.5).translate(0, 0, tank_z_base + r*2) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        # Anchor
        builder.create_grid(1, 1, size=0.1).translate(0, 0, 0) \
               .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        builder.clean()
