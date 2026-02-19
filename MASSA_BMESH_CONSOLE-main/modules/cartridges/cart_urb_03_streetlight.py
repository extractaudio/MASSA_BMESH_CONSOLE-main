import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "URB_03: Streetlight",
    "id": "urb_03_streetlight",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbStreetlight(Massa_OT_Base):
    bl_idname = "massa.gen_urb_03_streetlight"
    bl_label = "URB Streetlight"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    mast_height: FloatProperty(name="Mast Height", default=6.0, min=1.0)
    mast_base_r: FloatProperty(name="Base R", default=0.15, min=0.05)
    mast_top_r: FloatProperty(name="Top R", default=0.08, min=0.05)

    arm_length: FloatProperty(name="Arm Length", default=2.0, min=0.5)
    arm_angle: FloatProperty(name="Arm Angle", default=15.0, min=0.0) # Upward tilt
    arm_curve: BoolProperty(name="Curved Arm", default=True)

    lamp_size: FloatProperty(name="Lamp Size", default=0.3, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Metal Mast", "uv": "SKIP", "phys": "METAL_GALVANIZED"},
            4: {"name": "Light Bulb", "uv": "SKIP", "phys": "GLASS_EMISSIVE"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()

        h = self.mast_height
        br = self.mast_base_r
        tr = self.mast_top_r
        al = self.arm_length
        aa = math.radians(self.arm_angle)

        # 2. Mast (Tapered Cylinder)
        ret = bmesh.ops.create_circle(bm, cap_ends=True, radius=br, segments=12)
        verts_mast = ret['verts']
        base_face = list(verts_mast[0].link_faces)[0]

        ret_ext = bmesh.ops.extrude_face_region(bm, geom=[base_face])
        verts_ext = [e for e in ret_ext['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, 0, h)), verts=verts_ext)

        sf = tr / br if br > 0 else 1.0
        bmesh.ops.scale(bm, vec=Vector((sf, sf, 1.0)), space=Matrix.Translation(Vector((0,0,h))), verts=verts_ext)

        top_face = None
        for f in ret_ext['geom']:
            if isinstance(f, bmesh.types.BMFace):
                top_face = f
                break

        if not top_face: return

        # 3. Arm (Extrusion / Spin)
        # Elbow/Joint
        ret_j = bmesh.ops.extrude_face_region(bm, geom=[top_face])
        verts_j = [e for e in ret_j['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, 0, 0.2)), verts=verts_j)

        joint_face = [f for f in ret_j['geom'] if isinstance(f, bmesh.types.BMFace)][0]

        rot_deg = -90 + self.arm_angle
        c = joint_face.calc_center_median()
        bmesh.ops.rotate(bm, cent=c, matrix=Matrix.Rotation(math.radians(rot_deg), 3, 'X'), verts=verts_j)

        # Extrude Arm
        ret_arm = bmesh.ops.extrude_face_region(bm, geom=[joint_face])
        verts_arm = [e for e in ret_arm['geom'] if isinstance(e, bmesh.types.BMVert)]

        norm = joint_face.normal
        bmesh.ops.translate(bm, vec=norm * al, verts=verts_arm)

        arm_end_face = [f for f in ret_arm['geom'] if isinstance(f, bmesh.types.BMFace)][0]

        # 4. Lamp Housing
        c_end = arm_end_face.calc_center_median()
        bmesh.ops.rotate(bm, cent=c_end, matrix=Matrix.Rotation(math.radians(-90 - self.arm_angle), 3, 'X'), verts=verts_arm)

        ret_house = bmesh.ops.extrude_face_region(bm, geom=[arm_end_face])
        verts_house = [e for e in ret_house['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, 0, -0.2)), verts=verts_house)

        bmesh.ops.scale(bm, vec=Vector((2.0, 2.0, 1.0)), space=Matrix.Translation(c_end - Vector((0,0,0.2))), verts=verts_house)

        bulb_face = [f for f in ret_house['geom'] if isinstance(f, bmesh.types.BMFace)][0]
        bulb_face.material_index = 4 # Emission

        # 5. Sockets (Back of Joint)
        # Z = h + 0.1
        # Back is -Y side of mast. (Arm goes +Y)
        # Create small face at (0, -tr, h + 0.1)
        # Facing -Y

        c_sock = Vector((0, -tr - 0.05, h + 0.1))
        sz = 0.05

        v1 = bm.verts.new(c_sock + Vector((-sz, 0, -sz)))
        v2 = bm.verts.new(c_sock + Vector((sz, 0, -sz)))
        v3 = bm.verts.new(c_sock + Vector((sz, 0, sz)))
        v4 = bm.verts.new(c_sock + Vector((-sz, 0, sz)))
        f_sock = bm.faces.new((v4, v3, v2, v1))
        f_sock.material_index = 9

        # 6. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)
        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue

            if mat_idx == 4: # Bulb
                # Planar XY
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x, l.vert.co.y)
            else:
                # Cylinder Mapping
                for l in f.loops:
                    angle = math.atan2(l.vert.co.y, l.vert.co.x)
                    u = (angle / (2*math.pi)) * br * 3.14
                    v = l.vert.co.z
                    l[uv_layer].uv = (u * scale, v * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "mast_height")
        col.prop(self, "mast_base_r")
        col.prop(self, "mast_top_r")
        layout.separator()
        col.prop(self, "arm_length")
        col.prop(self, "arm_angle")
