import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "URB_02: Railing",
    "id": "urb_02_railing",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbRailing(Massa_OT_Base):
    bl_idname = "massa.gen_urb_02_railing"
    bl_label = "URB Railing"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=2.0, min=0.1)
    height: FloatProperty(name="Height", default=1.1, min=0.1)

    # Details
    rail_thick: FloatProperty(name="Rail Thick", default=0.05, min=0.01)
    post_thick: FloatProperty(name="Post Thick", default=0.04, min=0.01)
    baluster_spacing: FloatProperty(name="Baluster Space", default=0.15, min=0.05)
    baluster_thick: FloatProperty(name="Baluster Thick", default=0.02, min=0.01)

    bottom_gap: FloatProperty(name="Bottom Gap", default=0.1, min=0.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Metal", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        l, h = self.length, self.height
        rt, pt, bt = self.rail_thick, self.post_thick, self.baluster_thick
        bg = self.bottom_gap
        bs = self.baluster_spacing

        # 2. Top Rail (Length X)
        # Create at Z=h
        # Use create_cube
        res_TR = bmesh.ops.create_cube(bm, size=1.0)
        verts_TR = res_TR['verts']
        # Scale: (l, rt, rt)
        bmesh.ops.scale(bm, vec=Vector((l, rt, rt)), verts=verts_TR)
        # Translate: (0, 0, h - rt/2)
        bmesh.ops.translate(bm, vec=Vector((0, 0, h - rt/2)), verts=verts_TR)

        # 3. Bottom Rail
        if bg < h - rt:
            res_BR = bmesh.ops.create_cube(bm, size=1.0)
            verts_BR = res_BR['verts']
            # Scale: (l, pt, pt) ? Or smaller. Same as top rail maybe.
            bmesh.ops.scale(bm, vec=Vector((l, pt, pt)), verts=verts_BR)
            # Translate: (0, 0, bg + pt/2)
            bmesh.ops.translate(bm, vec=Vector((0, 0, bg + pt/2)), verts=verts_BR)

        # 4. Posts (Ends)
        # Left Post
        res_PL = bmesh.ops.create_cube(bm, size=1.0)
        verts_PL = res_PL['verts']
        bmesh.ops.scale(bm, vec=Vector((pt, pt, h)), verts=verts_PL)
        bmesh.ops.translate(bm, vec=Vector((-l/2 + pt/2, 0, h/2)), verts=verts_PL)

        # Right Post
        res_PR = bmesh.ops.create_cube(bm, size=1.0)
        verts_PR = res_PR['verts']
        bmesh.ops.scale(bm, vec=Vector((pt, pt, h)), verts=verts_PR)
        bmesh.ops.translate(bm, vec=Vector((l/2 - pt/2, 0, h/2)), verts=verts_PR)

        # 5. Balusters (Vertical pickets)
        # Space between posts: L - 2*pt
        # Start X = -l/2 + pt
        # End X = l/2 - pt
        # Range = l - 2*pt

        range_x = l - 2*pt
        num_b = int(range_x / bs)

        start_x = -l/2 + pt + (range_x - (num_b-1)*bs)/2 # Center them

        # Baluster height: From Bottom Rail Top to Top Rail Bottom
        # Z_bot = bg + pt
        # Z_top = h - rt
        # H_bal = Z_top - Z_bot

        z_bot = bg + pt
        z_top = h - rt
        h_bal = z_top - z_bot

        if h_bal > 0 and num_b > 0:
            for i in range(num_b):
                x = start_x + i * bs

                # Create Baluster
                res_bal = bmesh.ops.create_cube(bm, size=1.0)
                verts_bal = res_bal['verts']

                # Scale: (bt, bt, h_bal)
                bmesh.ops.scale(bm, vec=Vector((bt, bt, h_bal)), verts=verts_bal)

                # Translate: (x, 0, z_bot + h_bal/2)
                bmesh.ops.translate(bm, vec=Vector((x, 0, z_bot + h_bal/2)), verts=verts_bal)

        # 6. Sockets
        # Ends of posts (Left/Right)
        for f in bm.faces:
            n = f.normal
            c = f.calc_center_median()
            # If on Left End (-l/2) or Right End (l/2)
            if abs(c.x + l/2) < 0.1 and n.x < -0.9:
                f.material_index = 9
            elif abs(c.x - l/2) < 0.1 and n.x > 0.9:
                f.material_index = 9

        # 7. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)
        for f in bm.faces:
            if f.material_index == 9: continue
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
        col.prop(self, "height")
        layout.separator()
        col.prop(self, "rail_thick")
        col.prop(self, "post_thick")
        col.prop(self, "baluster_spacing")
        col.prop(self, "baluster_thick")
        col.prop(self, "bottom_gap")
