import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_20: Robotic Assembly Arm",
    "id": "asm_20_robotic_arm",
    "icon": "MOD_BUILD",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}


class MASSA_OT_AsmRoboticArm(Massa_OT_Base):
    bl_idname = "massa.gen_asm_20_robotic_arm"
    bl_label = "ASM_20 Robotic Arm"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. DIMENSIONS ---
    base_radius: FloatProperty(name="Base Radius", default=0.4, min=0.1, unit="LENGTH")
    base_height: FloatProperty(name="Base Height", default=0.5, min=0.1, unit="LENGTH")
    bicep_len: FloatProperty(name="Bicep Length", default=1.5, min=0.5, unit="LENGTH")
    forearm_len: FloatProperty(name="Forearm Length", default=1.2, min=0.5, unit="LENGTH")
    arm_thick: FloatProperty(name="Arm Thickness", default=0.2, min=0.05, unit="LENGTH")

    # --- 2. POSING ---
    base_rot: FloatProperty(name="Base Rot (Yaw)", default=0.0, min=-180, max=180, unit="ROTATION")
    joint_1: FloatProperty(name="Shoulder (Pitch)", default=45.0, min=-90, max=90, unit="ROTATION")
    joint_2: FloatProperty(name="Elbow (Pitch)", default=-45.0, min=-135, max=135, unit="ROTATION")

    # --- 3. UV ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Base", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Arms", "uv": "BOX", "phys": "METAL_ALUMINUM"}, # Painted
            2: {"name": "Joints", "uv": "BOX", "phys": "METAL_DARK"},
            9: {"name": "End Effector", "uv": "BOX", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "base_radius")
        col.prop(self, "base_height")
        col.prop(self, "bicep_len")
        col.prop(self, "forearm_len")
        col.prop(self, "arm_thick")

        col.separator()
        col.label(text="Posing")
        col.prop(self, "base_rot")
        col.prop(self, "joint_1")
        col.prop(self, "joint_2")

        col.separator()
        col.prop(self, "uv_scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        br = self.base_radius
        bh = self.base_height
        bl = self.bicep_len
        fl = self.forearm_len
        at = self.arm_thick

        y_rot = math.radians(self.base_rot)
        j1_rot = math.radians(self.joint_1)
        j2_rot = math.radians(self.joint_2)

        uv_layer = bm.loops.layers.uv.verify()
        scale = self.uv_scale

        # Transformations Hierarchy
        # Base (Static at origin) -> Turret (Rotated by Base Rot)
        # Shoulder Joint (Fixed on Turret) -> Bicep (Rotated by J1)
        # Elbow Joint (Fixed on Bicep end) -> Forearm (Rotated by J2 relative to Bicep, or absolute?)
        # Usually robotic arms accumulate transforms.

        # Matrices
        mat_base_rot = Matrix.Rotation(y_rot, 3, 'Z')
        mat_j1 = Matrix.Rotation(j1_rot, 3, 'Y') # Pitch around local Y? Let's say Y is axis of rotation.
        mat_j2 = Matrix.Rotation(j2_rot, 3, 'Y')

        # 1. BASE
        # Cylinder at origin
        res_base = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=br, radius2=br*0.9, depth=bh)
        bmesh.ops.translate(bm, vec=(0, 0, bh/2), verts=res_base['verts'])
        for f in res_base['faces']:
            f.material_index = 0
            self.apply_box_map(f, uv_layer, scale)

        # 2. TURRET (Rotates with Base)
        # Sits on top of base.
        turret_h = bh * 0.5
        res_turret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=br*0.75, radius2=br*0.75, depth=turret_h)
        bmesh.ops.translate(bm, vec=(0, 0, bh + turret_h/2), verts=res_turret['verts'])

        # Add Shoulder Joint Hub (Cylinder sideways)
        # Axis along Y (local to turret).
        # Center at (0, 0, bh + turret_h/2).
        res_shoulder = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=at*0.75, radius2=at*0.75, depth=br*1.8)
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=res_shoulder['verts']) # Cylinder is Z up -> Rotate X 90 -> Y axis.
        bmesh.ops.translate(bm, vec=(0, 0, bh + turret_h/2), verts=res_shoulder['verts'])

        turret_geom = res_turret['verts'] + res_shoulder['verts']
        for f in list({f for v in turret_geom for f in v.link_faces}):
            f.material_index = 0
            self.apply_box_map(f, uv_layer, scale)

        # Apply Base Rotation to Turret
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=mat_base_rot, verts=turret_geom)

        # 3. BICEP (Rotates with J1)
        # Pivot: Shoulder Center (0, 0, bh + turret_h/2) (after base rot).
        # We need pivot in world space to rotate around it, or build at origin, rotate, translate.

        pivot_shoulder_local = Vector((0, 0, bh + turret_h/2))
        # Apply base rot to pivot
        pivot_shoulder = mat_base_rot @ pivot_shoulder_local

        # Build Bicep at origin (pointing Z or X?)
        # Let's say it points Z up initially.
        # Length bl.
        res_bicep = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(at, at, bl), verts=res_bicep['verts'])
        # Move up so pivot is at bottom (0,0,0) -> (0,0,bl/2) center -> move by bl/2
        bmesh.ops.translate(bm, vec=(0, 0, bl/2), verts=res_bicep['verts'])

        # Add Elbow Joint at top (0, 0, bl)
        res_elbow = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=at*0.6, radius2=at*0.6, depth=at*1.5)
        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=res_elbow['verts'])
        bmesh.ops.translate(bm, vec=(0, 0, bl), verts=res_elbow['verts'])

        bicep_geom = res_bicep['verts'] + res_elbow['verts']

        for f in list({f for v in res_bicep['verts'] for f in v.link_faces}):
            f.material_index = 1 # Arm
            self.apply_box_map(f, uv_layer, scale)

        for f in list({f for v in res_elbow['verts'] for f in v.link_faces}):
            f.material_index = 2 # Joint
            self.apply_box_map(f, uv_layer, scale)

        # Transform Bicep:
        # 1. Rotate J1 (Pitch)
        # 2. Rotate Base Rot (Yaw)
        # 3. Translate to Shoulder Pivot

        # Combined rotation for Bicep: Yaw @ Pitch
        mat_bicep_rot = mat_base_rot @ mat_j1

        # Translate logic:
        # Current pivot is (0,0,0).
        # We want (0,0,0) to be at pivot_shoulder.

        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=mat_bicep_rot, verts=bicep_geom)
        bmesh.ops.translate(bm, vec=pivot_shoulder, verts=bicep_geom)

        # 4. FOREARM (Rotates with J2)
        # Pivot: Elbow Center.
        # Elbow center local to Bicep was (0, 0, bl).
        # Elbow center world = pivot_shoulder + mat_bicep_rot @ (0, 0, bl).

        elbow_local_vec = Vector((0, 0, bl))
        pivot_elbow = pivot_shoulder + (mat_bicep_rot @ elbow_local_vec)

        # Build Forearm at origin (pointing Z up)
        res_forearm = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(at*0.8, at*0.8, fl), verts=res_forearm['verts'])
        bmesh.ops.translate(bm, vec=(0, 0, fl/2), verts=res_forearm['verts'])

        # Add Wrist/End Effector Socket
        # At tip (0, 0, fl)
        res_wrist = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8, radius1=at/2, radius2=at*0.4, depth=0.2)
        bmesh.ops.translate(bm, vec=(0, 0, fl), verts=res_wrist['verts'])

        # Add Socket Plane
        res_sock = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.15)
        bmesh.ops.translate(bm, vec=(0, 0, fl + 0.1), verts=res_sock['verts'])

        forearm_geom = res_forearm['verts'] + res_wrist['verts'] + res_sock['verts']

        # Assign materials
        for f in list({f for v in res_forearm['verts'] for f in v.link_faces}):
            f.material_index = 1
            self.apply_box_map(f, uv_layer, scale)
        for f in list({f for v in res_wrist['verts'] for f in v.link_faces}):
            f.material_index = 2
            self.apply_box_map(f, uv_layer, scale)
        for f in res_sock['faces']:
            f.material_index = 9 # Socket
            self.apply_box_map(f, uv_layer, scale)

        # Transform Forearm
        # 1. Rotate J2 (Pitch relative to Bicep? Or absolute?)
        # Usually robotic arms define J2 relative to J1.
        # So total rotation = Yaw @ Pitch1 @ Pitch2.

        mat_forearm_rot = mat_base_rot @ mat_j1 @ mat_j2

        bmesh.ops.rotate(bm, cent=(0,0,0), matrix=mat_forearm_rot, verts=forearm_geom)
        bmesh.ops.translate(bm, vec=pivot_elbow, verts=forearm_geom)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    def apply_box_map(self, face, uv_layer, scale):
        n = face.normal
        nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)
        for l in face.loops:
            co = l.vert.co
            if nz > nx and nz > ny:
                u, v = co.x, co.y
            elif nx > ny and nx > nz:
                u, v = co.y, co.z
            else:
                u, v = co.x, co.z
            l[uv_layer].uv = (u * scale, v * scale)
