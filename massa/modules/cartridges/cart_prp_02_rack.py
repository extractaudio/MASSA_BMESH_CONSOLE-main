import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRP_02: Pallet Rack",
    "id": "prp_02_rack",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_PrpRack(Massa_OT_Base):
    bl_idname = "massa.gen_prp_02_rack"
    bl_label = "PRP Rack"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=2.7, min=1.0)
    width: FloatProperty(name="Width", default=1.0, min=0.5)
    height: FloatProperty(name="Height", default=4.0, min=1.0)

    # Levels
    levels: IntProperty(name="Shelf Levels", default=3, min=1)
    bottom_gap: FloatProperty(name="Bottom Gap", default=0.2, min=0.0)

    # Details
    post_size: FloatProperty(name="Post Size", default=0.08, min=0.01)
    beam_height: FloatProperty(name="Beam Height", default=0.1, min=0.01)
    beam_thick: FloatProperty(name="Beam Thick", default=0.05, min=0.01)

    def get_slot_meta(self):
        return {
            0: {"name": "Posts", "uv": "BOX", "phys": "METAL_PAINTED_BLUE"},
            1: {"name": "Beams", "uv": "BOX", "phys": "METAL_PAINTED_ORANGE"},
            2: {"name": "Wire Deck", "uv": "SKIP", "phys": "METAL_GRATE"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()

        l, w, h = self.length, self.width, self.height
        ps = self.post_size
        bh = self.beam_height
        bt = self.beam_thick
        bg = self.bottom_gap
        lvl = self.levels

        # 2. Four Posts (L-Angles or Box Columns)
        # Using Boxes for simplicity
        # Positions: +/- l/2 - ps/2, +/- w/2 - ps/2

        dx = l/2 - ps/2
        dy = w/2 - ps/2

        post_coords = [
            (-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)
        ]

        for px, py in post_coords:
            res_p = bmesh.ops.create_cube(bm, size=1.0)
            verts_p = res_p['verts']
            bmesh.ops.scale(bm, vec=Vector((ps, ps, h)), verts=verts_p)
            bmesh.ops.translate(bm, vec=Vector((px, py, h/2)), verts=verts_p)

            # Assign Material 0 (Posts)
            for v in verts_p:
                for f in v.link_faces:
                    f.material_index = 0

        # 3. Horizontal Beams (Front/Back)
        # Calculate level spacing
        # Start at bg. Remaining space / (levels - 1)? Or evenly spaced.
        # Shelf spacing = (h - bg) / levels?

        spacing = (h - bg - bh) / (lvl - 1) if lvl > 1 else 0

        for i in range(lvl):
            z = bg + i * spacing

            # Front Beam (Y = -w/2 + ps/2 + bt/2 ?)
            # Usually beams connect to face of posts.
            # Posts are at +/- dy. Faces at +/- dy +/- ps/2.
            # Beam Y = -w/2 + ps/2 (Front edge of post)

            # Let's place beams slightly inset or flush.
            # Front Beam
            res_bf = bmesh.ops.create_cube(bm, size=1.0)
            verts_bf = res_bf['verts']
            # Scale: (l, bt, bh)
            bmesh.ops.scale(bm, vec=Vector((l, bt, bh)), verts=verts_bf)
            # Pos: (0, -w/2, z + bh/2)
            bmesh.ops.translate(bm, vec=Vector((0, -w/2, z + bh/2)), verts=verts_bf)

            # Back Beam
            res_bb = bmesh.ops.create_cube(bm, size=1.0)
            verts_bb = res_bb['verts']
            bmesh.ops.scale(bm, vec=Vector((l, bt, bh)), verts=verts_bb)
            bmesh.ops.translate(bm, vec=Vector((0, w/2, z + bh/2)), verts=verts_bb)

            # Assign Material 1 (Beams)
            for v in verts_bf + verts_bb:
                for f in v.link_faces:
                    f.material_index = 1

            # 4. Wire Decking (Shelf Surface)
            # Plane between beams
            v1 = bm.verts.new(Vector((-l/2 + ps, -w/2 + bt, z + bh))) # On top of beams? Or flush top.
            v2 = bm.verts.new(Vector((l/2 - ps, -w/2 + bt, z + bh)))
            v3 = bm.verts.new(Vector((l/2 - ps, w/2 - bt, z + bh)))
            v4 = bm.verts.new(Vector((-l/2 + ps, w/2 - bt, z + bh)))

            f_deck = bm.faces.new((v1, v2, v3, v4))
            f_deck.material_index = 2 # Wire Deck

            # 5. Sockets (Center of Shelf)
            # Create a small face in center for anchor
            # Or just mark the deck face?
            # Mandate: "Generates a massive array of Sockets in the dead center of every shelf".
            # Let's create a specific socket geometry at center.
            c = f_deck.calc_center_median()
            # Create small quad at center
            sz = 0.1
            v_s1 = bm.verts.new(c + Vector((-sz, -sz, 0.01)))
            v_s2 = bm.verts.new(c + Vector((sz, -sz, 0.01)))
            v_s3 = bm.verts.new(c + Vector((sz, sz, 0.01)))
            v_s4 = bm.verts.new(c + Vector((-sz, sz, 0.01)))
            f_sock = bm.faces.new((v_s1, v_s2, v_s3, v_s4))
            f_sock.material_index = 9 # Socket Anchor

            # Also maybe array of sockets along the shelf? "Massive array".
            # Maybe every 1m?
            # Let's stick to one center socket per shelf for simplicity, or 3.
            # Left, Center, Right.

            # Add Left/Right Sockets
            dx_s = l/3
            # Left
            v_l1 = bm.verts.new(c + Vector((-dx_s - sz, -sz, 0.01)))
            v_l2 = bm.verts.new(c + Vector((-dx_s + sz, -sz, 0.01)))
            v_l3 = bm.verts.new(c + Vector((-dx_s + sz, sz, 0.01)))
            v_l4 = bm.verts.new(c + Vector((-dx_s - sz, sz, 0.01)))
            f_sock_l = bm.faces.new((v_l1, v_l2, v_l3, v_l4))
            f_sock_l.material_index = 9

            # Right
            v_r1 = bm.verts.new(c + Vector((dx_s - sz, -sz, 0.01)))
            v_r2 = bm.verts.new(c + Vector((dx_s + sz, -sz, 0.01)))
            v_r3 = bm.verts.new(c + Vector((dx_s + sz, sz, 0.01)))
            v_r4 = bm.verts.new(c + Vector((dx_s - sz, sz, 0.01)))
            f_sock_r = bm.faces.new((v_r1, v_r2, v_r3, v_r4))
            f_sock_r.material_index = 9

        # 6. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)
        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue

            n = f.normal
            if mat_idx == 2: # Wire Deck
                # Planar Z
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)
            else: # Posts/Beams
                # Box
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
        col.prop(self, "levels")
        layout.separator()
        col.prop(self, "post_size")
        col.prop(self, "beam_height")
