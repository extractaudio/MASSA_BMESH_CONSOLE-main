import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_03: Fluid Manifold",
    "id": "asm_03_manifold",
    "icon": "MOD_FLUID",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_AsmManifold(Massa_OT_Base):
    bl_idname = "massa.gen_asm_03_manifold"
    bl_label = "ASM_03: Fluid Manifold"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    block_radius: FloatProperty(name="Block Radius", default=1.0, min=0.5)
    block_height: FloatProperty(name="Block Height", default=0.8, min=0.2)

    valve_count: IntProperty(name="Valves", default=4, min=2, soft_max=8)
    valve_length: FloatProperty(name="Valve Length", default=0.5, min=0.1)

    motor_height: FloatProperty(name="Motor Height", default=1.2, min=0.5)

    def get_slot_meta(self):
        return {
            0: {"name": "Base Block", "uv": "SKIP", "phys": "METAL_IRON"},
            1: {"name": "Motor Housing", "uv": "SKIP", "phys": "METAL_PAINTED"},
            2: {"name": "Valves", "uv": "SKIP", "phys": "METAL_IRON"},
            3: {"name": "Handwheels", "uv": "SKIP", "phys": "METAL_RED"},
            4: {"name": "Valve Socket", "uv": "SKIP", "phys": "METAL_IRON", "sock": True},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "block_radius")
        col.prop(self, "block_height")

        layout.separator()
        layout.label(text="DETAILS", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "valve_count")
        col.prop(self, "valve_length")
        col.prop(self, "motor_height")

    def build_shape(self, bm: bmesh.types.BMesh):
        r, h = self.block_radius, self.block_height

        # 1. Base Block
        segs = max(8, self.valve_count * 4)
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            segments=segs,
            diameter1=r*2,
            diameter2=r*2,
            depth=h,
            matrix=Matrix.Translation((0, 0, h/2))
        )

        # 2. Motor Housing
        motor_r = r * 0.6
        mh = self.motor_height

        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            segments=16,
            diameter1=motor_r*2,
            diameter2=motor_r*2,
            depth=mh,
            matrix=Matrix.Translation((0, 0, h + mh/2))
        )

        # 3. Radial Valves
        valve_z = h * 0.5
        valve_r = r * 0.15 # Slightly smaller relative to block
        vl = self.valve_length

        for i in range(self.valve_count):
            angle = (i / self.valve_count) * 2 * math.pi
            dir_vec = Vector((math.cos(angle), math.sin(angle), 0))

            start_pos = dir_vec * (r - 0.1)
            start_pos.z = valve_z

            # Rotation
            rot_z = Vector((0, 0, 1))
            rot_axis = rot_z.cross(dir_vec)
            if rot_axis.length < 0.001:
                 rot_axis = Vector((1,0,0)) # Fallback
            rot_angle = rot_z.angle(dir_vec)
            rot_mat = Matrix.Rotation(rot_angle, 4, rot_axis)

            # Valve Stem
            valve_center = start_pos + dir_vec * (vl/2)
            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                segments=12,
                diameter1=valve_r*2,
                diameter2=valve_r*2,
                depth=vl,
                matrix=Matrix.Translation(valve_center) @ rot_mat
            )

            # Flange
            flange_pos = start_pos + dir_vec * vl
            flange_r = valve_r * 1.5
            flange_thick = 0.1
            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                segments=12,
                diameter1=flange_r*2,
                diameter2=flange_r*2,
                depth=flange_thick,
                matrix=Matrix.Translation(flange_pos) @ rot_mat
            )

            # Handwheel Stem
            wheel_stem_pos = start_pos + dir_vec * (vl * 0.5)
            wheel_stem_h = 0.3
            wheel_center = wheel_stem_pos + Vector((0, 0, wheel_stem_h))

            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                segments=6,
                diameter1=0.05,
                diameter2=0.05,
                depth=wheel_stem_h,
                matrix=Matrix.Translation(wheel_center - Vector((0,0,wheel_stem_h/2)))
            )

            # Handwheel Disk
            wheel_r = 0.25
            bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                segments=12,
                diameter1=wheel_r*2,
                diameter2=wheel_r*2,
                depth=0.05,
                matrix=Matrix.Translation(wheel_center)
            )

        # 4. Material Assignment
        bm.faces.ensure_lookup_table()

        for f in bm.faces:
            center = f.calc_center_median()
            dist_xy = math.hypot(center.x, center.y)

            if center.z > h + 0.01:
                f.material_index = 1 # Motor
            elif dist_xy < r + 0.05: # Slight tolerance
                f.material_index = 0 # Base Block
            else:
                # Valves or Handwheels
                # Check height relative to valve axis
                # Handwheel is at valve_z + 0.3 (stem) or higher.
                # Valve is around valve_z with radius valve_r.
                # If valve_r is large, they might overlap in Z range, but handwheel is physically separate.
                # But here we are just tagging faces.
                # Let's use a relative threshold.
                if center.z > valve_z + valve_r * 0.8:
                     f.material_index = 3 # Handwheel
                else:
                    f.material_index = 2 # Valve

                    # Socket Detection (Flange Tip)
                    # Must be far out and facing out
                    if dist_xy > r + vl - 0.05:
                        # Check normal
                        pos_vec = Vector((center.x, center.y, 0)).normalized()
                        norm_vec = Vector((f.normal.x, f.normal.y, 0)).normalized()
                        if pos_vec.dot(norm_vec) > 0.9:
                            f.material_index = 4 # Socket

        # 5. UV Mapping
        uv_layer = bm.loops.layers.uv.verify()
        for f in bm.faces:
             for l in f.loops:
                 # Box Projection
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
