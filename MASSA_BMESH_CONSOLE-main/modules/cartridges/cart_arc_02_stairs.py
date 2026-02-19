import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ARC_02: Procedural Staircase",
    "id": "arc_02_stairs",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcStairs(Massa_OT_Base):
    bl_idname = "massa.gen_arc_02_stairs"
    bl_label = "ARC Stairs"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    stair_width: FloatProperty(name="Width", default=1.2, min=0.1)
    total_height: FloatProperty(name="Height", default=3.0, min=0.1)
    step_count: IntProperty(name="Count", default=12, min=1)

    # Details
    tread_depth: FloatProperty(name="Tread Depth", default=0.28, min=0.1)

    has_stringer: BoolProperty(name="Stringers", default=True)
    stringer_width: FloatProperty(name="Stringer W", default=0.05)
    stringer_offset: FloatProperty(name="Stringer Offset", default=0.05) # Above nose

    def get_slot_meta(self):
        return {
            0: {"name": "Treads", "uv": "SKIP", "phys": "WOOD"},
            1: {"name": "Risers", "uv": "SKIP", "phys": "WOOD"},
            2: {"name": "Stringers", "uv": "BOX", "phys": "METAL_IRON"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 2. Calculate Metrics
        rise = self.total_height / self.step_count
        run = self.tread_depth

        # 3. Generate Profile Verts
        # Start at origin (0,0,0)
        curr_y = 0
        curr_z = 0

        for i in range(self.step_count):
            # Riser (Vertical)
            v1 = bm.verts.new(Vector((0, curr_y, curr_z)))
            curr_z += rise
            v2 = bm.verts.new(Vector((0, curr_y, curr_z)))

            # Tread (Horizontal)
            curr_y += run
            v3 = bm.verts.new(Vector((0, curr_y, curr_z)))

            # Create Verts for Width
            v1_r = bm.verts.new(Vector((self.stair_width, v1.co.y, v1.co.z)))
            v2_r = bm.verts.new(Vector((self.stair_width, v2.co.y, v2.co.z)))
            v3_r = bm.verts.new(Vector((self.stair_width, v3.co.y, v3.co.z)))

            # Riser Face
            f_riser = bm.faces.new((v1, v2, v2_r, v1_r))
            f_riser.material_index = 1

            # Tread Face
            f_tread = bm.faces.new((v2, v3, v3_r, v2_r))
            f_tread.material_index = 0

            # Mark Nose Edge (v3-v3_r) for next iteration? No, v3 is the nose.
            # The edge is v2-v2_r? No, v2 is top of riser, back of tread.
            # v3 is front of tread. But we haven't created the next riser yet.
            # The "Nose" is v3 (but v3 is at the end of tread).
            # Actually standard stairs: Riser goes UP, then Tread goes FWD.
            # So v2 is the corner between Riser and Tread.
            # v3 is the nose of this tread.

            # Find edge (v3, v3_r)
            for e in bm.edges:
                if e.verts[0] in (v3, v3_r) and e.verts[1] in (v3, v3_r):
                    e[edge_slots] = 2 # Contour/Detail

        bm.verts.ensure_lookup_table()

        # 4. Stringers (Side Supports)
        if self.has_stringer:
            total_y = self.step_count * run
            total_z = self.total_height
            sw = self.stringer_width
            so = self.stringer_offset

            # Define Points for Side Profile (Parallelogram/Ramp)
            # Left Stringer (X centered on 0)
            # P1: Bottom-Back (0, 0, -so*3)
            # P2: Top-Back (0, total_y, total_z - so*3)
            # P3: Top-Front (0, total_y, total_z + so)
            # P4: Bottom-Front (0, 0, so)

            # Actually better to use create_cube and skew it?
            # Or manually build.

            # Left Stringer
            v_sl = [
                bm.verts.new(Vector((-sw, 0, -so*2))),
                bm.verts.new(Vector((-sw, total_y, total_z - so*2))),
                bm.verts.new(Vector((-sw, total_y, total_z + so))),
                bm.verts.new(Vector((-sw, 0, so))),

                bm.verts.new(Vector((0, 0, -so*2))),
                bm.verts.new(Vector((0, total_y, total_z - so*2))),
                bm.verts.new(Vector((0, total_y, total_z + so))),
                bm.verts.new(Vector((0, 0, so)))
            ]

            # Faces Left
            # 0-1-2-3 (Outer)
            f_out = bm.faces.new((v_sl[0], v_sl[3], v_sl[2], v_sl[1]))
            f_in = bm.faces.new((v_sl[4], v_sl[5], v_sl[6], v_sl[7]))
            # Sides
            bm.faces.new((v_sl[0], v_sl[1], v_sl[5], v_sl[4]))
            bm.faces.new((v_sl[1], v_sl[2], v_sl[6], v_sl[5]))
            bm.faces.new((v_sl[2], v_sl[3], v_sl[7], v_sl[6]))
            bm.faces.new((v_sl[3], v_sl[0], v_sl[4], v_sl[7]))

            # Assign Mat 2
            for v in v_sl:
                for f in v.link_faces:
                    f.material_index = 2

            # Right Stringer (X centered on stair_width)
            v_sr = [
                bm.verts.new(Vector((self.stair_width, 0, -so*2))),
                bm.verts.new(Vector((self.stair_width, total_y, total_z - so*2))),
                bm.verts.new(Vector((self.stair_width, total_y, total_z + so))),
                bm.verts.new(Vector((self.stair_width, 0, so))),

                bm.verts.new(Vector((self.stair_width + sw, 0, -so*2))),
                bm.verts.new(Vector((self.stair_width + sw, total_y, total_z - so*2))),
                bm.verts.new(Vector((self.stair_width + sw, total_y, total_z + so))),
                bm.verts.new(Vector((self.stair_width + sw, 0, so)))
            ]

            # Faces Right
            bm.faces.new((v_sr[0], v_sr[1], v_sr[2], v_sr[3]))
            bm.faces.new((v_sr[4], v_sr[7], v_sr[6], v_sr[5]))
            bm.faces.new((v_sr[0], v_sr[3], v_sr[7], v_sr[4])) # Bottom
            bm.faces.new((v_sr[3], v_sr[2], v_sr[6], v_sr[7])) # Front
            bm.faces.new((v_sr[2], v_sr[1], v_sr[5], v_sr[6])) # Top
            bm.faces.new((v_sr[1], v_sr[0], v_sr[4], v_sr[5])) # Back

            for v in v_sr:
                for f in v.link_faces:
                    f.material_index = 2

        # 5. Sockets (Landings)
        # Bottom Landing: Center at (width/2, 0, 0)
        # Top Landing: Center at (width/2, total_y, total_z)

        # Bottom Socket
        c_bot = Vector((self.stair_width/2, 0, 0))
        sz = 0.1
        v1 = bm.verts.new(c_bot + Vector((-sz, -sz, 0)))
        v2 = bm.verts.new(c_bot + Vector((sz, -sz, 0)))
        v3 = bm.verts.new(c_bot + Vector((sz, sz, 0))) # Flat on ground? Or vertical facing -Y?
        v4 = bm.verts.new(c_bot + Vector((-sz, sz, 0)))
        # Let's make it vertical facing -Y (Entry)
        # v1, v2 at Z=0. v3, v4 at Z=0.2?
        # Actually standard socket is a face.
        # Let's make a vertical face at Y=0 facing -Y.
        v1 = bm.verts.new(c_bot + Vector((-sz, 0, 0)))
        v2 = bm.verts.new(c_bot + Vector((sz, 0, 0)))
        v3 = bm.verts.new(c_bot + Vector((sz, 0, sz*2)))
        v4 = bm.verts.new(c_bot + Vector((-sz, 0, sz*2)))
        f_sock_bot = bm.faces.new((v1, v2, v3, v4))
        f_sock_bot.material_index = 9

        # Top Socket (Exit)
        c_top = Vector((self.stair_width/2, self.step_count * run, self.total_height))
        # Face Y=total_y, facing +Y
        v1 = bm.verts.new(c_top + Vector((-sz, 0, 0)))
        v2 = bm.verts.new(c_top + Vector((sz, 0, 0)))
        v3 = bm.verts.new(c_top + Vector((sz, 0, sz*2)))
        v4 = bm.verts.new(c_top + Vector((-sz, 0, sz*2)))
        f_sock_top = bm.faces.new((v4, v3, v2, v1)) # Face +Y
        f_sock_top.material_index = 9

        # 6. Manual UVs
        scale_u = getattr(self, "uv_scale_0", 1.0)

        for f in bm.faces:
            if f.material_index == 9: continue

            n = f.normal
            # Simple Planar mapping
            if abs(n.z) > 0.5: # Top
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * scale_u, l.vert.co.y * scale_u)
            elif abs(n.x) > 0.5: # Side
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.y * scale_u, l.vert.co.z * scale_u)
            else: # Front/Back
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * scale_u, l.vert.co.z * scale_u)

    def draw_shape_ui(self, layout):
        box_dim = layout.box()
        box_dim.label(text="Dimensions", icon='MESH_PLANE')
        col_dim = box_dim.column(align=True)
        col_dim.prop(self, "stair_width")
        col_dim.prop(self, "total_height")
        col_dim.prop(self, "step_count")

        box_det = layout.box()
        box_det.label(text="Details", icon='LINCURVE')
        col_det = box_det.column(align=True)
        col_det.prop(self, "tread_depth")

        box_str = layout.box()
        box_str.label(text="Stringers", icon='MOD_BUILD')
        col_str = box_str.column(align=True)
        col_str.prop(self, "has_stringer")
        if self.has_stringer:
            col_str.prop(self, "stringer_width")
            col_str.prop(self, "stringer_offset")
