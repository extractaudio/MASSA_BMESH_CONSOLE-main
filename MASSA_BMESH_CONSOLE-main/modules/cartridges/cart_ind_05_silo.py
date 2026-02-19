import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "IND_05: Silo",
    "id": "ind_05_silo",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndSilo(Massa_OT_Base):
    bl_idname = "massa.gen_ind_05_silo"
    bl_label = "IND Silo"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    height: FloatProperty(name="Tank Height", default=4.0, min=0.5)
    radius: FloatProperty(name="Radius", default=1.5, min=0.5)
    leg_height: FloatProperty(name="Leg Height", default=1.0, min=0.0)

    # Details
    segments: IntProperty(name="Segments", default=24, min=6)
    cap_height: FloatProperty(name="Cap Height", default=0.5, min=0.0)

    # Legs
    num_legs: IntProperty(name="Leg Count", default=4, min=3)
    leg_width: FloatProperty(name="Leg Width", default=0.2, min=0.05)

    def get_slot_meta(self):
        return {
            0: {"name": "Tank Body", "uv": "SKIP", "phys": "METAL_STEEL"},
            1: {"name": "Legs", "uv": "BOX", "phys": "METAL_RUST"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 2. Tank Body (Cylinder)
        r = self.radius
        h = self.height
        lh = self.leg_height
        ch = self.cap_height
        segs = self.segments

        # Create Cylinder
        ret = bmesh.ops.create_cone(bm, cap_ends=True, radius1=r, radius2=r, depth=h, segments=segs)
        verts_tank = ret['verts']
        bmesh.ops.translate(bm, vec=Vector((0, 0, lh + h/2)), verts=verts_tank)

        # Identify Caps
        top_face = None
        bottom_face = None

        for f in bm.faces:
            if f.normal.z > 0.9 and abs(f.calc_center_median().z - (lh + h)) < 0.1:
                top_face = f
            elif f.normal.z < -0.9 and abs(f.calc_center_median().z - lh) < 0.1:
                bottom_face = f

        # 3. Top Cap (Cone/Dome)
        if ch > 0 and top_face:
            ret_poke = bmesh.ops.poke(bm, faces=[top_face])
            center_vert = ret_poke['verts'][0]
            bmesh.ops.translate(bm, vec=Vector((0, 0, ch)), verts=[center_vert])

        # 4. Bottom Cap (Cone/Dome)
        if ch > 0 and bottom_face:
            ret_poke = bmesh.ops.poke(bm, faces=[bottom_face])
            center_vert = ret_poke['verts'][0]
            bmesh.ops.translate(bm, vec=Vector((0, 0, -ch)), verts=[center_vert])

        # 5. Legs (I-Beams)
        if lh > 0:
            leg_angle_step = (2 * math.pi) / self.num_legs
            lw = self.leg_width

            for i in range(self.num_legs):
                angle = i * leg_angle_step

                lx = math.cos(angle) * r
                ly = math.sin(angle) * r

                res_leg = bmesh.ops.create_cube(bm, size=1.0)
                verts_leg = res_leg['verts']

                bmesh.ops.scale(bm, vec=Vector((lw, lw, lh)), verts=verts_leg)
                bmesh.ops.translate(bm, vec=Vector((lx, ly, lh/2)), verts=verts_leg)

                rot_mat = Matrix.Rotation(angle, 3, 'Z')
                bmesh.ops.rotate(bm, cent=Vector((lx, ly, lh/2)), matrix=rot_mat, verts=verts_leg)

                for v in verts_leg:
                    for f in v.link_faces:
                        f.material_index = 1

        # 6. Edge Seam (Guide)
        for e in bm.edges:
            v1, v2 = e.verts
            if abs(v1.co.x) < 0.1 and abs(v2.co.x) < 0.1:
                if v1.co.y > 0 and v2.co.y > 0:
                    if abs(v1.co.z - v2.co.z) > 0.1: # Vertical
                        e[edge_slots] = 3
                        e.seam = True

        # 7. Sockets (Cardinal Directions at Mid-Height)
        mid_z = lh + h/2

        # Create 4 small faces
        directions = [
            (r, 0, 0), # +X
            (-r, 0, 0), # -X
            (0, r, 0), # +Y
            (0, -r, 0) # -Y
        ]

        sz = 0.1

        for dx, dy, dz in directions:
            c = Vector((dx, dy, mid_z))
            # Orient face normal to direction
            # +X face: YZ plane
            if abs(dx) > 0:
                v1 = bm.verts.new(c + Vector((0, -sz, -sz)))
                v2 = bm.verts.new(c + Vector((0, sz, -sz)))
                v3 = bm.verts.new(c + Vector((0, sz, sz)))
                v4 = bm.verts.new(c + Vector((0, -sz, sz)))
                # Order for normal: +X
                if dx > 0:
                    f = bm.faces.new((v4, v3, v2, v1))
                else:
                    f = bm.faces.new((v1, v2, v3, v4))
            else: # +Y face: XZ plane
                v1 = bm.verts.new(c + Vector((-sz, 0, -sz)))
                v2 = bm.verts.new(c + Vector((sz, 0, -sz)))
                v3 = bm.verts.new(c + Vector((sz, 0, sz)))
                v4 = bm.verts.new(c + Vector((-sz, 0, sz)))
                # Order for normal: +Y
                if dy > 0:
                    f = bm.faces.new((v1, v2, v3, v4))
                else:
                    f = bm.faces.new((v4, v3, v2, v1))

            f.material_index = 9

        # 8. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)

        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue
            if mat_idx == 1: # Legs
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
            else: # Tank
                for l in f.loops:
                    angle = math.atan2(l.vert.co.y, l.vert.co.x)
                    u = (angle / (2*math.pi)) * r * 3.14
                    v = l.vert.co.z
                    l[uv_layer].uv = (u * scale, v * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "height")
        col.prop(self, "radius")
        col.prop(self, "segments")
        layout.separator()
        col.prop(self, "leg_height")
        col.prop(self, "cap_height")
        col.prop(self, "num_legs")
