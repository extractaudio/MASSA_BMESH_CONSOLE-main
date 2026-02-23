import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_02: Procedural Staircase",
    "id": "arc_02_stairs",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False, # Now solid geometry
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
    tread_thick: FloatProperty(name="Tread Thick", default=0.04, min=0.01)
    riser_thick: FloatProperty(name="Riser Thick", default=0.02, min=0.01)
    nosing: FloatProperty(name="Nosing", default=0.03, min=0.0)

    has_stringer: BoolProperty(name="Stringers", default=True)
    stringer_width: FloatProperty(name="Stringer W", default=0.05)
    stringer_offset: FloatProperty(name="Stringer Offset", default=0.05) # Vertical thickness

    def get_slot_meta(self):
        return {
            0: {"name": "Treads", "uv": "BOX", "phys": "WOOD"},
            1: {"name": "Risers", "uv": "BOX", "phys": "WOOD"},
            2: {"name": "Stringers", "uv": "BOX", "phys": "METAL_IRON"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # Ensure Layers exist
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        rise = self.total_height / self.step_count
        run = self.tread_depth
        w = self.stair_width
        tt = self.tread_thick
        rt = self.riser_thick
        nose = self.nosing

        # 1. Generate Steps (Solid)
        curr_y = 0
        curr_z = 0

        for i in range(self.step_count):
            # RISER
            # Vertical board.
            # Center: X=0
            # Y = curr_y + rt/2 (Push forward by half thickness)
            # Z = curr_z + rise/2
            # Size: w, rt, rise

            builder.create_box(w, rt, rise) \
                   .translate(0, curr_y + rt/2, curr_z + rise/2) \
                   .tag_slot(1)

            # TREAD
            # Horizontal board.
            # Sit on top of riser?
            # Z = curr_z + rise - tt/2 (Align top with next level? No, tread is usually ADDED to rise height or INCLUDED?)
            # Standard: Floor to Floor is total_height.
            # Top of Tread i should be at (i+1)*rise.
            # So Tread Center Z = (curr_z + rise) - tt/2.

            tread_z = (curr_z + rise) - tt/2

            # Y Position:
            # Starts at curr_y. Length = run + nose.
            # Center Y = curr_y + (run + nose)/2 - nose?
            # Tread front is at curr_y + run + nose.
            # Back is at curr_y?
            # Actually, standard run is horizontal distance.
            # Riser is at curr_y. Tread extends from curr_y to curr_y + run + nose.

            tread_len = run + nose
            tread_y = curr_y + tread_len/2

            # Adjust for Nosing overlap relative to riser
            # Riser front face is at curr_y + rt.
            # Tread back face should be at curr_y? Or at riser front?
            # Usually tread touches riser.

            # Let's verify positions:
            # Riser front: Y = curr_y + rt.
            # Tread front: Y = curr_y + rt + run + nose.
            # Tread center: Y = curr_y + rt + (run + nose)/2 - (nose overlap logic?)

            # Simplified:
            # Riser at `curr_y`.
            # Tread sits on riser.

            builder.create_box(w, tread_len, tt) \
                   .translate(0, tread_y, tread_z) \
                   .tag_slot(0)

            curr_y += run
            curr_z += rise

        # 2. Stringers
        if self.has_stringer:
            # Calculate slope based on NOSES
            total_run = self.step_count * run
            total_rise = self.total_height
            angle = math.atan2(total_rise, total_run)
            diag_len = math.sqrt(total_run**2 + total_rise**2) + 0.5 # Extra length

            sw = self.stringer_width
            sthick = 0.3 # Beam Height

            # Center of the staircase volume
            cy = total_run / 2
            cz = total_rise / 2 - sthick/4 # Shift down slightly

            cx_l = -w/2 - sw/2
            cx_r = w/2 + sw/2

            # Left
            builder.create_box(sw, diag_len, sthick) \
                   .rotate(math.degrees(angle), axis='X') \
                   .translate(cx_l, cy, cz) \
                   .tag_slot(2)

            # Right
            builder.create_box(sw, diag_len, sthick) \
                   .rotate(math.degrees(angle), axis='X') \
                   .translate(cx_r, cy, cz) \
                   .tag_slot(2)

        # 3. Sockets
        sz = 0.2
        # Bottom
        v1 = bm.verts.new(Vector((-sz, 0, 0)))
        v2 = bm.verts.new(Vector((sz, 0, 0)))
        v3 = bm.verts.new(Vector((sz, 0, sz*2)))
        v4 = bm.verts.new(Vector((-sz, 0, sz*2)))
        f_bot = bm.faces.new((v1, v2, v3, v4))
        f_bot.material_index = 9
        f_bot.normal_update()

        # Top
        c_top = Vector((0, self.step_count * run, self.total_height))
        v1 = bm.verts.new(c_top + Vector((-sz, 0, 0)))
        v2 = bm.verts.new(c_top + Vector((sz, 0, 0)))
        v3 = bm.verts.new(c_top + Vector((sz, 0, sz*2)))
        v4 = bm.verts.new(c_top + Vector((-sz, 0, sz*2)))
        f_top = bm.faces.new((v4, v3, v2, v1))
        f_top.material_index = 9
        f_top.normal_update()

        # 4. Manual UVs
        self.apply_manual_uvs(bm)

    def apply_manual_uvs(self, bm):
        uv_layer = bm.loops.layers.uv.verify()
        scale = getattr(self, "uv_scale_0", 1.0)

        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            # if f.material_index == 9: continue # Pass audit

            n = f.normal
            for l in f.loops:
                v = l.vert.co
                if abs(n.z) > 0.5: # Top
                    l[uv_layer].uv = (v.x * scale, v.y * scale)
                elif abs(n.x) > 0.5: # Side
                    l[uv_layer].uv = (v.y * scale, v.z * scale)
                else: # Front
                    l[uv_layer].uv = (v.x * scale, v.z * scale)

    def draw_shape_ui(self, layout):
        box = layout.box()
        col = box.column(align=True)
        col.prop(self, "stair_width")
        col.prop(self, "total_height")
        col.prop(self, "step_count")

        box_d = layout.box()
        col = box_d.column(align=True)
        col.prop(self, "tread_depth")
        col.prop(self, "tread_thick")
        col.prop(self, "riser_thick")
        col.prop(self, "nosing")

        box_s = layout.box()
        col = box_s.column(align=True)
        col.prop(self, "has_stringer")
        if self.has_stringer:
            col.prop(self, "stringer_width")
            col.prop(self, "stringer_offset")
