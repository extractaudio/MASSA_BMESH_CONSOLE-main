import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_08: Pipe Support Rack",
    "id": "arc_08_pipe_support",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_ArcPipeSupport(Massa_OT_Base):
    bl_idname = "massa.gen_arc_08_pipe_support"
    bl_label = "ARC Pipe Rack"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("H_BEAM", "H-Beam Steel", "Heavy structural steel"),
            ("UNISTRUT", "Unistrut / Channel", "Lightweight modular channel"),
            ("CONCRETE", "Concrete Pier", "Heavy concrete supports"),
        ],
        default="H_BEAM"
    )

    # Dimensions
    width: FloatProperty(name="Rack Width", default=3.0, min=1.0)
    height: FloatProperty(name="Total Height", default=4.0, min=1.0)
    depth: FloatProperty(name="Length (Depth)", default=6.0, min=0.5)

    # Levels
    levels: IntProperty(name="Levels", default=2, min=1, max=10)
    level_spacing: FloatProperty(name="Level Spacing", default=1.5, min=0.5)
    first_level_h: FloatProperty(name="First Level H", default=2.0, min=0.5)

    # Structure
    col_width: FloatProperty(name="Column Width", default=0.25, min=0.05)
    beam_height: FloatProperty(name="Beam Height", default=0.25, min=0.05)
    bay_spacing: FloatProperty(name="Bay Spacing", default=3.0, min=1.0)

    # Details
    brace_type: EnumProperty(
        name="Bracing",
        items=[
            ("NONE", "None", ""),
            ("X_BRACE", "X-Brace", ""),
            ("K_BRACE", "K-Brace", ""),
        ],
        default="X_BRACE"
    )

    base_plate_size: FloatProperty(name="Base Plate", default=0.4, min=0.0)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Structure", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Fittings", "uv": "BOX", "phys": "METAL_IRON"},
            2: {"name": "Foundation", "uv": "BOX", "phys": "CONCRETE"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions", icon='MESH_CUBE')
        col = box.column(align=True)
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")

        box = layout.box()
        box.label(text="Levels", icon='MOD_ARRAY')
        col = box.column(align=True)
        col.prop(self, "levels")
        col.prop(self, "first_level_h")
        col.prop(self, "level_spacing")

        box = layout.box()
        box.label(text="Structure", icon='MOD_BUILD')
        col = box.column(align=True)
        col.prop(self, "col_width")
        col.prop(self, "beam_height")
        col.prop(self, "bay_spacing")
        col.prop(self, "brace_type")
        col.prop(self, "base_plate_size")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        w = self.width
        d = self.depth
        h_total = self.height # Actually height is driven by levels usually? Or Clamped?
        # Let's say H is max height of columns.

        lvl_cnt = self.levels
        lvl_h = self.level_spacing
        start_h = self.first_level_h

        cw = self.col_width
        bh = self.beam_height
        bs = self.bay_spacing

        # Clamp inputs
        cw = min(cw, w/2)
        bh = min(bh, start_h)

        # Calculate Grid
        # Bays along Depth
        num_bays = max(1, int(d / bs))
        actual_bay_len = d / num_bays

        # Structure Frame:
        # Two rows of columns at +/- w/2
        # Columns at each bay grid line (0 to num_bays)

        # 1. Columns
        # Z range: 0 to h_total? Or top level?
        # Top level Z = start_h + (lvl_cnt-1)*lvl_h.
        # Column Height = max(h_total, top_level + 0.5)

        top_level_z = start_h + (lvl_cnt-1)*lvl_h
        col_h = max(h_total, top_level_z + bh)

        for i in range(num_bays + 1):
            y = -d/2 + i*actual_bay_len

            # Left Col
            builder.create_box(cw, cw, col_h, center=Vector((-w/2, y, col_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Right Col
            builder.create_box(cw, cw, col_h, center=Vector((w/2, y, col_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Base Plates
            if self.base_plate_size > cw:
                bp = self.base_plate_size
                builder.create_box(bp, bp, 0.05, center=Vector((-w/2, y, 0.025)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
                builder.create_box(bp, bp, 0.05, center=Vector((w/2, y, 0.025)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Cross Beams (Connecting Left-Right Columns at this bay line)
            # At each level
            for l_idx in range(lvl_cnt):
                z = start_h + l_idx * lvl_h
                # Beam center Z?
                # Usually beam top is the level. So center = z - bh/2.
                # Let's say z param is top of steel.

                bz = z - bh/2

                # Beam width = w + cw? Or between cols?
                # Steel connects to face of flange or web.
                # Let's run it full width w + cw.

                builder.create_box(w + cw, cw*0.8, bh, center=Vector((0, y, bz)))
                builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 2. Longitudinal Beams (Stringers)
        # Connecting columns along Y
        # At each level

        for l_idx in range(lvl_cnt):
            z = start_h + l_idx * lvl_h
            bz = z - bh/2

            # Left Stringer
            # From -d/2 to d/2
            # Center X = -w/2

            # Offset X slightly or same?
            # If same size, Z-fighting.
            # Usually stringers are framed into cross beams or vice versa.
            # Let's make stringers slightly smaller or inset.

            sw = cw * 0.8 # Width of stringer beam

            # Left
            builder.create_box(sw, d, bh, center=Vector((-w/2, 0, bz)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Right
            builder.create_box(sw, d, bh, center=Vector((w/2, 0, bz)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 3. Bracing
        # Between columns along Y (Longitudinal bracing)
        # Or between columns along X (Transverse)?
        # Transverse is usually moment frame (rigid). Longitudinal needs bracing.

        if self.brace_type != "NONE":
            # Brace bays along Y
            for i in range(num_bays):
                y1 = -d/2 + i*actual_bay_len
                y2 = -d/2 + (i+1)*actual_bay_len
                mid_y = (y1 + y2) / 2
                dist_y = y2 - y1

                # Brace each level interval? Or ground to first level?
                # Usually every bay or alternating. Let's do every bay for simplicity.

                # Height segments: Ground to L1, L1 to L2...
                # Iterate levels
                # Ground (0) is implicit.
                prev_z = 0
                for l_idx in range(lvl_cnt):
                    curr_z = start_h + l_idx * lvl_h - bh # Bottom of beam

                    if curr_z > prev_z + 0.5: # Min height for brace
                        # Create Brace
                        # X Bracing: (y1, prev_z) -> (y2, curr_z) AND (y1, curr_z) -> (y2, prev_z)

                        # Left Side (X = -w/2)
                        if self.brace_type == "X_BRACE":
                            p1 = Vector((-w/2, y1, prev_z))
                            p2 = Vector((-w/2, y2, curr_z))
                            p3 = Vector((-w/2, y1, curr_z))
                            p4 = Vector((-w/2, y2, prev_z))

                            _create_brace(builder, p1, p2, self.uv_scale)
                            _create_brace(builder, p3, p4, self.uv_scale)

                            # Right Side (X = w/2)
                            p1.x = w/2; p2.x = w/2; p3.x = w/2; p4.x = w/2
                            _create_brace(builder, p1, p2, self.uv_scale)
                            _create_brace(builder, p3, p4, self.uv_scale)

                        elif self.brace_type == "K_BRACE":
                            # K Brace: (y1, prev_z) -> (mid_y, curr_z) <- (y2, prev_z) ?
                            # Or A brace.
                            # Standard K: Midpoint of column to Midpoint of Beam?
                            # Let's do Chevron (Inverted V): (mid_y, curr_z) -> (y1, prev_z) and (y2, prev_z)

                            # Left
                            apex = Vector((-w/2, mid_y, curr_z))
                            b1 = Vector((-w/2, y1, prev_z))
                            b2 = Vector((-w/2, y2, prev_z))

                            _create_brace(builder, b1, apex, self.uv_scale)
                            _create_brace(builder, b2, apex, self.uv_scale)

                            # Right
                            apex.x = w/2; b1.x = w/2; b2.x = w/2
                            _create_brace(builder, b1, apex, self.uv_scale)
                            _create_brace(builder, b2, apex, self.uv_scale)

                    prev_z = start_h + l_idx * lvl_h # Top of beam approx

        # 4. Sockets
        # Base Socket (0,0,0)
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1)
        bases = [f for f in builder.active_faces if abs(f.calc_center_median().z) < 0.1]
        builder.active_faces = bases
        builder.tag_socket(9)

        builder.clean()

def _create_brace(builder, p1, p2, uv_scale):
    # Create a thin box/cylinder from p1 to p2
    vec = p2 - p1
    dist = vec.length
    if dist < 0.1: return

    mid = (p1 + p2) / 2

    # Create at Origin to allow rotation
    builder.create_box(0.1, 0.1, dist, center=Vector((0,0,0)))

    # Calculate Angle (Rotation around X axis for YZ plane braces)
    angle = math.atan2(vec.y, vec.z)

    builder.rotate(math.degrees(-angle), axis='X')

    # Translate to final position
    builder.translate(mid.x, mid.y, mid.z)

    builder.tag_slot(1).tag_uvs(scale=uv_scale, projection='BOX')
