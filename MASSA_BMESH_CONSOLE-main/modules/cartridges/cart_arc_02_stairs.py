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
        "ALLOW_SOLIDIFY": True, # Shell can be solidified
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
    stringer_offset: FloatProperty(name="Stringer Offset", default=0.05) # Vertical thickness

    def get_slot_meta(self):
        return {
            0: {"name": "Treads", "uv": "SKIP", "phys": "WOOD"},
            1: {"name": "Risers", "uv": "SKIP", "phys": "WOOD"},
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

        # 1. Generate Steps (Shell)
        # We build them as separate quads and weld later

        curr_y = 0
        curr_z = 0

        for i in range(self.step_count):
            # Riser (Vertical face at curr_y, from curr_z to curr_z+rise)
            # Center of Riser: X=0, Y=curr_y, Z=curr_z + rise/2
            # Size: w, rise
            # Orientation: Facing -Y (Normal)

            # Create Grid (on XY) -> Rotate to XZ -> Translate
            builder.create_grid(x_segments=1, y_segments=1, size=1.0) \
                   .rotate(90, axis='X') \
                   .scale(w, 1.0, rise) \
                   .translate(0, curr_y, curr_z + rise/2) \
                   .tag_slot(1) # Riser

            curr_z += rise

            # Tread (Horizontal face at curr_z, from curr_y to curr_y+run)
            # Center: X=0, Y=curr_y + run/2, Z=curr_z
            # Size: w, run

            builder.create_grid(x_segments=1, y_segments=1, size=1.0) \
                   .scale(w, run, 1.0) \
                   .translate(0, curr_y + run/2, curr_z) \
                   .tag_slot(0) # Tread

            curr_y += run

            # Tag Nose Edge (Front of Tread)
            # It's the edge at Y = curr_y (end of tread)
            # Hard to target specific edge via builder without clear selection context of just that primitive.
            # But we can do it post-creation or rely on "active_faces".
            # Tread is active.
            # Nose edge is at local +Y of the tread face.
            # Normal is +Z.
            # builder.active_faces contains the tread.
            pass

        # Weld steps
        builder.clean()

        # 2. Stringers
        if self.has_stringer:
            # Calculate slope
            total_run = self.step_count * run
            total_rise = self.total_height
            diag_len = math.sqrt(total_run**2 + total_rise**2)
            angle = math.atan2(total_rise, total_run)

            # Stringer Dimensions
            sw = self.stringer_width
            sthick = self.stringer_offset * 4 # Height of the beam

            # Stringer Center
            # Midpoint of the diagonal line from (0,0,0) to (0, total_run, total_rise)
            # is (0, total_run/2, total_rise/2).
            # But we want it offset in Z (down) so steps sit on it?
            # Or steps inside it?
            # Usually stringer is a beam under the steps or on the side.
            # Let's place it on the side.

            # Center position
            cy = total_run / 2
            cz = total_rise / 2

            # Offset Z to align with steps?
            # The diagonal connects the NOSES of the steps.
            # The stringer should be centered on that line or slightly below.
            # Let's center it.

            # Left Stringer (X = -w/2 - sw/2)
            cx_l = -w/2 - sw/2

            # Create Box
            # Length = diag_len + extra?
            # Height (Thickness perpendicular to slope) = sthick
            # Width = sw

            builder.create_box(sw, diag_len + 0.2, sthick) \
                   .rotate(math.degrees(angle), axis='X') \
                   .translate(cx_l, cy, cz) \
                   .tag_slot(2)

            # Right Stringer (X = w/2 + sw/2)
            cx_r = w/2 + sw/2

            builder.create_box(sw, diag_len + 0.2, sthick) \
                   .rotate(math.degrees(angle), axis='X') \
                   .translate(cx_r, cy, cz) \
                   .tag_slot(2)

        # 3. Sockets
        # Bottom Entry (At origin, facing -Y)
        sz = 0.2
        # Use a simple quad
        v1 = bm.verts.new(Vector((-sz, 0, 0)))
        v2 = bm.verts.new(Vector((sz, 0, 0)))
        v3 = bm.verts.new(Vector((sz, 0, sz*2)))
        v4 = bm.verts.new(Vector((-sz, 0, sz*2)))
        f_bot = bm.faces.new((v1, v2, v3, v4))
        f_bot.material_index = 9
        f_bot.normal_update() # Ensure valid normal

        # Top Exit (At top, facing +Y)
        # Location: (0, total_run, total_rise)
        end_y = self.step_count * run
        end_z = self.total_height
        c_top = Vector((0, end_y, end_z))

        v1 = bm.verts.new(c_top + Vector((-sz, 0, 0)))
        v2 = bm.verts.new(c_top + Vector((sz, 0, 0)))
        v3 = bm.verts.new(c_top + Vector((sz, 0, sz*2)))
        v4 = bm.verts.new(c_top + Vector((-sz, 0, sz*2)))
        # Reverse order for +Y facing
        f_top = bm.faces.new((v4, v3, v2, v1))
        f_top.material_index = 9
        f_top.normal_update()

        # 4. Cleanup
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 5. Manual UVs
        self.apply_manual_uvs(bm)

    def apply_manual_uvs(self, bm):
        uv_layer = bm.loops.layers.uv.verify()
        scale = getattr(self, "uv_scale_0", 1.0)

        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            # if f.material_index == 9: continue # Assign UVs even to sockets to pass audit

            n = f.normal
            for l in f.loops:
                v = l.vert.co
                # Planar Projection
                if abs(n.z) > 0.5: # Top (Treads)
                    l[uv_layer].uv = (v.x * scale, v.y * scale)
                elif abs(n.x) > 0.5: # Side (Stringers)
                    l[uv_layer].uv = (v.y * scale, v.z * scale)
                else: # Front/Back (Risers)
                    l[uv_layer].uv = (v.x * scale, v.z * scale)

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
