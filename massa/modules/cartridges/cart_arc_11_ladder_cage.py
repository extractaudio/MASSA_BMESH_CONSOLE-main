import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_11: Ladder Cage",
    "id": "arc_11_ladder_cage",
    "icon": "LADDER", # Custom or Generic? MOD_LATTICE works
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_ArcLadderCage(Massa_OT_Base):
    bl_idname = "massa.gen_arc_11_ladder_cage"
    bl_label = "ARC Ladder Cage"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("SIMPLE", "Simple Ladder", "Basic wall ladder"),
            ("CAGED", "Safety Cage", "Ladder with protective cage"),
            ("ACCESS", "Platform Access", "Ladder with top landing platform"),
        ],
        default="CAGED"
    )

    # Dimensions
    height: FloatProperty(name="Height", default=4.0, min=1.0)
    width: FloatProperty(name="Width", default=0.6, min=0.4, max=1.2)
    standoff_dist: FloatProperty(name="Wall Distance", default=0.2, min=0.1)

    # Rungs
    rung_spacing: FloatProperty(name="Rung Spacing", default=0.3, min=0.2, max=0.5)
    rung_thickness: FloatProperty(name="Rung Dia", default=0.03, min=0.01)
    rail_thickness: FloatProperty(name="Rail Thickness", default=0.05, min=0.02)

    # Cage
    cage_start: FloatProperty(name="Cage Start H", default=2.2, min=0.0)
    cage_diameter: FloatProperty(name="Cage Dia", default=0.75, min=0.6)
    hoop_spacing: FloatProperty(name="Hoop Spacing", default=1.0, min=0.5)
    vertical_bars: IntProperty(name="Vert Bars", default=5, min=3, max=12)

    # Platform (Access Style)
    platform_depth: FloatProperty(name="Plat Depth", default=1.0, min=0.5)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Rails/Structure", "uv": "BOX", "phys": "METAL_PAINTED"},
            1: {"name": "Rungs", "uv": "CYLINDER", "phys": "METAL_ROUGH"},
            2: {"name": "Cage/Safety", "uv": "BOX", "phys": "METAL_THIN"},
            3: {"name": "Platform", "uv": "BOX", "phys": "METAL_GRATE"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions", icon='Length')
        col = box.column(align=True)
        col.prop(self, "height")
        col.prop(self, "width")
        col.prop(self, "standoff_dist")

        box = layout.box()
        box.label(text="Structure", icon='MOD_LATTICE')
        col = box.column(align=True)
        col.prop(self, "rung_spacing")
        col.prop(self, "rung_thickness")
        col.prop(self, "rail_thickness")

        if self.style in ["CAGED", "ACCESS"]:
            box = layout.box()
            box.label(text="Safety Cage", icon='MESH_CIRCLE')
            col = box.column(align=True)
            col.prop(self, "cage_start")
            col.prop(self, "cage_diameter")
            col.prop(self, "hoop_spacing")
            col.prop(self, "vertical_bars")

        if self.style == "ACCESS":
            box = layout.box()
            box.label(text="Platform", icon='MESH_GRID')
            col = box.column(align=True)
            col.prop(self, "platform_depth")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        h = self.height
        w = self.width
        s_dist = self.standoff_dist

        # Clamp parameters to prevent geometry explosions during fuzzing
        rail_t = min(self.rail_thickness, w * 0.45, 0.5)
        rung_t = min(self.rung_thickness, self.rung_spacing * 0.8, 0.5)
        rung_s = max(self.rung_spacing, 0.1) # Prevent infinite loop

        c_dia = self.cage_diameter
        c_rad = c_dia / 2.0
        # Ensure cage doesn't intersect rails too badly or invert
        if c_rad < w/2 + 0.1:
            c_rad = w/2 + 0.1
            c_dia = c_rad * 2

        # Ladder starts at Z=0 (Ground/Floor)
        # Rails are offset from Origin (0,0) by standoff_dist in Y?
        # Let's assume Wall is at Y=0. Ladder is at Y = -s_dist (if ladder climbs up wall)
        # Or Ladder at Origin, Wall at +Y?
        # Standard: Object Origin is base of ladder on ground. Wall is usually "Back".
        # Let's put ladder rails at Y=0. Standoff brackets go to Y = s_dist (Wall).

        # 1. Rails
        # Left Rail
        builder.create_box(rail_t, rail_t, h, center=Vector((-w/2, 0, h/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Right Rail
        builder.create_box(rail_t, rail_t, h, center=Vector((w/2, 0, h/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 2. Rungs
        # Iterate from bottom to top
        # Start first rung at rung_s/2 or just rung_s? Usually ~30cm up.
        current_z = rung_s
        while current_z < h - 0.1:
            builder.create_cylinder(radius=rung_t/2, depth=w - rail_t, center=Vector((0, 0, current_z)))
            builder.rotate(90, axis='Y')

            # Explicit Normal Update needed after rotation for accurate normal checks
            builder.bm.normal_update()

            # 1. Store all faces (cylinder)
            all_rung_faces = builder.active_faces[:]

            # 2. Identify Caps (Normal X+ / X-)
            caps = [f for f in all_rung_faces if abs(f.normal.x) > 0.9]
            walls = [f for f in all_rung_faces if f not in caps]

            # 3. Apply Slots
            builder.active_faces = all_rung_faces
            builder.tag_slot(1)

            # 4. Apply UVs
            if caps:
                builder.active_faces = caps
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')

            if walls:
                builder.active_faces = walls
                # For horizontal cylinder along X, axis='X' maps U around X
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

            current_z += rung_s

        # 3. Brackets (Standoffs)
        # Every 1.5m approx?
        bracket_spacing = 1.5
        b_z = bracket_spacing
        while b_z < h:
            # Left Bracket
            builder.create_box(rail_t, s_dist, rail_t, center=Vector((-w/2, s_dist/2, b_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Right Bracket
            builder.create_box(rail_t, s_dist, rail_t, center=Vector((w/2, s_dist/2, b_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Wall Plate (Small)
            builder.create_box(rail_t*2, 0.02, rail_t*3, center=Vector((-w/2, s_dist, b_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(rail_t*2, 0.02, rail_t*3, center=Vector((w/2, s_dist, b_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            b_z += bracket_spacing

        # 4. Cage
        if self.style in ["CAGED", "ACCESS"] and h > self.cage_start:
            c_start = self.cage_start
            # Use clamped values from top
            # c_rad and c_dia are already defined at top of build_shape

            # Cage height logic
            # If Access, cage goes higher?
            c_end = h
            if self.style == "ACCESS":
                c_end = h + 1.0 # Extend above ladder top for platform safety?

            # Hoops
            # Half-circle or 3/4 circle around the ladder?
            # Usually starts from one rail, goes around back of user, to other rail.
            # Center of cage is somewhere in front of ladder (Y-).
            # Ladder is at Y=0. User climbs on Y side.
            # User center is approx Y = -0.3.

            cage_center_y = -0.35 # Approx user center

            # Create Hoops
            hoop_z = c_start
            while hoop_z <= c_end:
                # Create Hoop geometry.
                # Let's verify if we can make a hoop.
                # Torus is complex. Let's make a "C" shape using segments.
                # Or just a box strip bent?

                # Let's use 5 segments for a semi-circle.
                steps = 7
                angle_span = 240 # degrees (Not full 360, attaches to rails)
                start_ang = -angle_span / 2 - 90 # Start from right side?
                # 0 is +X, 90 is +Y.
                # We want the cage to be on -Y side.
                # So angles around 270 (-90).

                # Let's construct a hoop using `create_cylinder` for each segment? Heavy.
                # Better: create a ring, delete back part.

                # Let's keep it simpler for robust BMesh:
                # Create a thin box strip, rotate it.

                hoop_radius = c_rad
                hoop_thick = 0.03
                hoop_width = 0.01 # Flat strip

                # Build hoop points
                verts = []
                for i in range(steps + 1):
                    # Angle from (1,0)
                    # We want -Y direction. That is 270 deg.
                    # Span 210 degrees? (From angle 185 to 355?)
                    # Let's say -30 to -150 (covers -90).
                    # Actually, ladder rails are at +/- w/2.
                    # We need the hoop to connect to rails or near them.

                    # Parametric angle:
                    # Normalized t from 0 to 1
                    t = i / steps
                    # Angle range: starts at right rail, goes around -Y, ends at left rail.
                    # Right rail is (+w/2, 0). Left is (-w/2, 0).
                    # Circle center is (0, cage_center_y).
                    # We need to calculate intersection angles or just fudge it.

                    # Let's just do a 270 degree arc centered at (0, -c_rad + rail_t/2)

                    base_angle = -90 # -Y axis
                    arc = 200 # degrees
                    ang = base_angle + (t - 0.5) * arc

                    rad = math.radians(ang)
                    px = math.cos(rad) * c_rad
                    py = math.sin(rad) * c_rad + cage_center_y

                    # If px > w/2 or px < -w/2 we might clamp or just let it be.
                    # Actually, let's just make full hoops for simplicity and then boolean?
                    # No booleans.

                    # Just create 5 straight segments connecting these points.
                    verts.append(Vector((px, py, hoop_z)))

                # Extrude segments
                for j in range(len(verts) - 1):
                    p1 = verts[j]
                    p2 = verts[j+1]

                    mid = (p1 + p2) / 2
                    vec = p2 - p1
                    length = vec.length
                    angle_z = math.atan2(vec.y, vec.x)

                    builder.create_box(length, hoop_width, hoop_thick, center=mid)
                    builder.rotate(math.degrees(angle_z), axis='Z')
                    builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

                hoop_z += self.hoop_spacing

            # Vertical Bars
            # Run from c_start to c_end at specific angles
            vb_count = self.vertical_bars
            for i in range(vb_count):
                t = i / (vb_count - 1)
                arc = 200
                base_angle = -90
                ang = base_angle + (t - 0.5) * arc

                rad = math.radians(ang)
                vx = math.cos(rad) * c_rad
                vy = math.sin(rad) * c_rad + cage_center_y

                builder.create_box(0.02, 0.02, c_end - c_start, center=Vector((vx, vy, (c_start + c_end)/2)))
                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 5. Platform (Access)
        if self.style == "ACCESS":
            pd = self.platform_depth
            ph = h # Height of platform floor

            # Platform Floor (Grating)
            # Extends from ladder (Y=0) towards Wall (+Y) or Away (-Y)?
            # Usually ladder leads to a platform at the top, usually "behind" the ladder (between ladder and wall? or on top of roof).
            # If ladder is standoff 0.2, platform usually goes 'in' to the roof.
            # Let's assume platform is at Y > 0 (towards building).

            builder.create_box(w + 0.4, pd, 0.05, center=Vector((0, pd/2, ph)))
            builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Guardrails on platform
            # Sides and Front (far side)
            # Sides
            gr_h = 1.0
            builder.create_box(0.05, pd, 0.05, center=Vector((-w/2 - 0.2, pd/2, ph + gr_h))) # Top rail
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            builder.create_box(0.05, pd, 0.05, center=Vector((w/2 + 0.2, pd/2, ph + gr_h))) # Top rail
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Posts
            builder.create_box(0.05, 0.05, gr_h, center=Vector((-w/2 - 0.2, pd, ph + gr_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(0.05, 0.05, gr_h, center=Vector((w/2 + 0.2, pd, ph + gr_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')


        # 6. Sockets
        # Base Socket (Anchor)
        # Identify faces at Z=0?
        # Or explicitly create a small sensor face at (0,0,0)?
        # Let's search for faces pointing -Z near 0.

        # Or better, use the rails bottom faces.
        builder.select_faces_by_normal(Vector((0,0,-1)))
        # Filter for Z approx 0
        bases = [f for f in builder.active_faces if abs(f.calc_center_median().z) < 0.1]
        builder.active_faces = bases
        builder.tag_socket(9)

        # Top Socket (Exit)
        # Pointing +Z or +Y?
        # If Access, +Y (walk off).
        # If Simple, +Z (climb off).

        builder.clean()

    def execute(self, context):
        return super().execute(context)
