import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_05: Conveyor Segment",
    "id": "asm_05_conveyor",
    "icon": "MOD_ARRAY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_AsmConveyor(Massa_OT_Base):
    bl_idname = "massa.gen_asm_05_conveyor"
    bl_label = "ASM_05: Conveyor Belt"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Width (X)", default=0.8, min=0.3)
    length: FloatProperty(name="Length (Y)", default=3.0, min=0.5)
    height: FloatProperty(name="Height (Z)", default=0.8, min=0.2)

    roller_radius: FloatProperty(name="Roller Radius", default=0.05, min=0.01)
    roller_spacing: FloatProperty(name="Roller Spacing", default=0.3, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame Rails", "uv": "SKIP", "phys": "METAL_PAINTED"},
            1: {"name": "Rollers", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
            2: {"name": "Legs", "uv": "SKIP", "phys": "METAL_PAINTED"},
            5: {"name": "Rubber Belt", "uv": "SKIP", "phys": "RUBBER"},
            6: {"name": "Cargo Socket", "uv": "SKIP", "phys": "MECHANICAL", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "length")
        col.prop(self, "height")

        layout.separator()
        layout.label(text="DETAILS", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "roller_radius")
        col.prop(self, "roller_spacing")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, l, h = self.width, self.length, self.height
        rr = self.roller_radius
        rs = self.roller_spacing

        # 1. Rails (C-Channel)
        rail_h = rr * 2.5
        rail_w = 0.05

        # Left Rail
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation((-w/2, 0, h - rail_h/2)) @ Matrix.Scale(rail_w, 4, (1,0,0)) @ Matrix.Scale(l, 4, (0,1,0)) @ Matrix.Scale(rail_h, 4, (0,0,1))
        )
        # Right Rail
        bmesh.ops.create_cube(
            bm,
            size=1.0,
            matrix=Matrix.Translation((w/2, 0, h - rail_h/2)) @ Matrix.Scale(rail_w, 4, (1,0,0)) @ Matrix.Scale(l, 4, (0,1,0)) @ Matrix.Scale(rail_h, 4, (0,0,1))
        )

        # 2. Legs
        leg_w = 0.05
        leg_inset = 0.2
        leg_positions = [
            (-w/2, -l/2 + leg_inset),
            (w/2, -l/2 + leg_inset),
            (-w/2, l/2 - leg_inset),
            (w/2, l/2 - leg_inset)
        ]

        for lx, ly in leg_positions:
            bmesh.ops.create_cube(
                bm,
                size=1.0,
                matrix=Matrix.Translation((lx, ly, h/2)) @ Matrix.Scale(leg_w, 4, (1,0,0)) @ Matrix.Scale(leg_w, 4, (0,1,0)) @ Matrix.Scale(h, 4, (0,0,1))
            )

        # 3. Rollers
        roller_y_start = -l/2 + rr
        roller_y_end = l/2 - rr
        current_y = roller_y_start

        roller_z = h - rail_h/2
        roller_width = w - rail_w * 2 - 0.02

        roller_tops = []

        while current_y < roller_y_end:
            bmesh.ops.create_cylinder(
                bm,
                cap_ends=True,
                radius1=rr,
                radius2=rr,
                depth=roller_width,
                segments=12,
                matrix=Matrix.Translation((0, current_y, roller_z)) @ Matrix.Rotation(math.radians(90), 4, 'Y')
            )
            roller_tops.append(current_y)
            current_y += rs

        # 4. Rubber Belt
        belt_width = roller_width - 0.02
        belt_thick = 0.01

        if not roller_tops:
            roller_tops = [0]

        last_roller_y = roller_tops[-1]
        first_roller_y = roller_tops[0]

        # Middle Box
        box_len = last_roller_y - first_roller_y
        box_center_y = (last_roller_y + first_roller_y) / 2

        if box_len > 0:
            bmesh.ops.create_cube(
                bm,
                size=1.0,
                matrix=Matrix.Translation((0, box_center_y, roller_z)) @ Matrix.Scale(belt_width, 4, (1,0,0)) @ Matrix.Scale(box_len, 4, (0,1,0)) @ Matrix.Scale((rr + belt_thick)*2, 4, (0,0,1))
            )

        # End Cylinders
        for y_pos in [first_roller_y, last_roller_y]:
            bmesh.ops.create_cylinder(
                bm,
                cap_ends=True,
                radius1=rr + belt_thick,
                radius2=rr + belt_thick,
                depth=belt_width,
                segments=16,
                matrix=Matrix.Translation((0, y_pos, roller_z)) @ Matrix.Rotation(math.radians(90), 4, 'Y')
            )

        # 5. Sockets
        socket_z = roller_z + rr + belt_thick + 0.05
        num_sockets = int(l)
        step = 1.0
        start_y = -l/2 + 0.5

        for i in range(num_sockets):
            sy = start_y + i * step
            if sy > l/2: break

            bmesh.ops.create_grid(
                bm,
                x_segments=1,
                y_segments=1,
                size=0.2,
                matrix=Matrix.Translation((0, sy, socket_z))
            )

        # 6. Material Assignment
        bm.faces.ensure_lookup_table()

        for f in bm.faces:
            center = f.calc_center_median()

            # Sockets: High Z
            if center.z > roller_z + rr + belt_thick + 0.01:
                f.material_index = 6
                # Force Up Normal
                if f.normal.z < 0.5:
                     # Side of socket plate?
                     pass

            # Belt vs Rollers
            elif abs(center.x) < belt_width/2 + 0.01 and abs(center.z - roller_z) < rr + belt_thick + 0.02:
                 # Check outer shell
                 if abs(center.z - roller_z) > rr + 0.005:
                     f.material_index = 5 # Belt
                 elif abs(center.x) > belt_width/2 - 0.005:
                     f.material_index = 1 # Roller Ends
                 else:
                     f.material_index = 1 # Inner Roller (Hidden)

            # Frame/Legs
            elif abs(center.x) > belt_width/2 + 0.01:
                if center.z > h - rail_h - 0.01:
                    f.material_index = 0 # Frame
                else:
                    f.material_index = 2 # Legs

        # UVs
        uv_layer = bm.loops.layers.uv.verify()
        for f in bm.faces:
             for l in f.loops:
                 nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                 if nz > 0.5:
                     u, v = l.vert.co.x, l.vert.co.y
                 elif ny > 0.5:
                     u, v = l.vert.co.x, l.vert.co.z
                 else:
                     u, v = l.vert.co.y, l.vert.co.z
                 l[uv_layer].uv = (u * 0.5, v * 0.5)

    def execute(self, context):
        return super().execute(context)
