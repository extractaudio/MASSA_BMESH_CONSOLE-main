import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "IND_02: HVAC Duct",
    "id": "ind_02_duct",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndDuct(Massa_OT_Base):
    bl_idname = "massa.gen_ind_02_duct"
    bl_label = "IND Duct"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=2.0, min=0.1)
    width: FloatProperty(name="Width", default=0.6, min=0.1)
    height: FloatProperty(name="Height", default=0.4, min=0.1)

    # Details
    segment_length: FloatProperty(name="Segment L", default=1.0, min=0.1)
    cross_break: FloatProperty(name="Cross Break", default=0.015, min=0.0) # Depth of X pattern
    flange_width: FloatProperty(name="Flange W", default=0.03, min=0.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Sheet Metal", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
            2: {"name": "Flanges", "uv": "BOX", "phys": "METAL_STEEL"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 2. Main Body
        segs = int(self.length / self.segment_length)
        if segs < 1: segs = 1
        seg_len = self.length / segs

        l, w, h = self.length, self.width, self.height
        cb = self.cross_break
        fw = self.flange_width

        # Start at -L/2
        curr_x = -l/2

        for i in range(segs):
            # Center of this segment: curr_x + seg_len/2
            cx = curr_x + seg_len/2

            # Create Cube
            ret = bmesh.ops.create_cube(bm, size=1.0)
            verts = ret['verts']
            bmesh.ops.scale(bm, vec=Vector((seg_len, w, h)), verts=verts)
            bmesh.ops.translate(bm, vec=Vector((cx, 0, 0)), verts=verts)

            # Identify Faces for Cross Break
            # Top/Bottom (Normal Z), Sides (Normal Y)
            faces = list({f for v in verts for f in v.link_faces})
            side_faces = []

            for f in faces:
                n = f.normal
                # Sides and Top/Bottom (not Ends)
                if abs(n.x) < 0.1:
                    side_faces.append(f)

            # Cross Break Logic
            if cb > 0:
                ret_poke = bmesh.ops.poke(bm, faces=side_faces)
                center_verts = [v for v in ret_poke['verts']]

                for v in center_verts:
                    # Average normal of linked faces
                    avg_normal = Vector((0,0,0))
                    for f in v.link_faces:
                        avg_normal += f.normal
                    if avg_normal.length > 0:
                        avg_normal.normalize()

                    # Move inward (sheet metal stiffness usually pulls in)
                    bmesh.ops.translate(bm, vec=avg_normal * -cb, verts=[v])

                    # Mark edges as Detail (2)
                    for e in v.link_edges:
                        e[edge_slots] = 2

            # Flanges (At ends of segment)
            if fw > 0:
                flange_thick = 0.01
                # Left Flange (at curr_x)
                # Box of size (flange_thick, w + fw, h + fw)
                res_fl = bmesh.ops.create_cube(bm, size=1.0)
                verts_fl = res_fl['verts']
                bmesh.ops.scale(bm, vec=Vector((flange_thick, w + fw*2, h + fw*2)), verts=verts_fl)
                bmesh.ops.translate(bm, vec=Vector((curr_x, 0, 0)), verts=verts_fl)

                # Right Flange (at curr_x + seg_len)
                res_fr = bmesh.ops.create_cube(bm, size=1.0)
                verts_fr = res_fr['verts']
                bmesh.ops.scale(bm, vec=Vector((flange_thick, w + fw*2, h + fw*2)), verts=verts_fr)
                bmesh.ops.translate(bm, vec=Vector((curr_x + seg_len, 0, 0)), verts=verts_fr)

                # Assign Material 2
                for v in verts_fl + verts_fr:
                    for f in v.link_faces:
                        f.material_index = 2

            curr_x += seg_len

        # 3. Clean up
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)

        # 4. Sockets
        # Cap Faces at Ends
        # Add a specific socket face at +/- l/2
        # Or just mark the end faces.
        # Since we added flanges, the end faces are flanges.
        # Let's create a dedicated socket face.

        # Left Socket (-l/2)
        sz = 0.1
        v1 = bm.verts.new(Vector((-l/2 - 0.01, -sz, -sz)))
        v2 = bm.verts.new(Vector((-l/2 - 0.01, sz, -sz)))
        v3 = bm.verts.new(Vector((-l/2 - 0.01, sz, sz)))
        v4 = bm.verts.new(Vector((-l/2 - 0.01, -sz, sz)))
        f_sock_l = bm.faces.new((v4, v3, v2, v1))
        f_sock_l.material_index = 9

        # Right Socket (l/2)
        v1 = bm.verts.new(Vector((l/2 + 0.01, -sz, -sz)))
        v2 = bm.verts.new(Vector((l/2 + 0.01, sz, -sz)))
        v3 = bm.verts.new(Vector((l/2 + 0.01, sz, sz)))
        v4 = bm.verts.new(Vector((l/2 + 0.01, -sz, sz)))
        f_sock_r = bm.faces.new((v1, v2, v3, v4)) # Face +X
        f_sock_r.material_index = 9

        # 5. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)
        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue

            n = f.normal
            for l in f.loops:
                if abs(n.x) > 0.5:
                    l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)
                elif abs(n.y) > 0.5:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
                else:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")
        layout.separator()
        col.prop(self, "segment_length")
        col.prop(self, "cross_break")
        col.prop(self, "flange_width")
