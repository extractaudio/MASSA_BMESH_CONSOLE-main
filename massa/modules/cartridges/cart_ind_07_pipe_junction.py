import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_07: Pipe Junction",
    "id": "ind_07_pipe_junction",
    "icon": "OUTLINER_OB_CURVE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_IndPipeJunction(Massa_OT_Base):
    bl_idname = "massa.gen_ind_07_pipe_junction"
    bl_label = "IND_07: Pipe Junction"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    style: EnumProperty(
        name="Style",
        items=[
            ("T_JOINT", "T-Joint", "Three-way connection"),
            ("CROSS", "Cross", "Four-way connection"),
            ("ELBOW", "Elbow", "90-degree turn"),
        ],
        default="T_JOINT",
    )

    radius: FloatProperty(name="Pipe Radius", default=0.2, min=0.05)
    length: FloatProperty(name="Arm Length", default=0.5, min=0.1)

    flange_radius: FloatProperty(name="Flange Radius", default=0.28, min=0.05)
    flange_thick: FloatProperty(name="Flange Thick", default=0.05, min=0.01)

    bolts: BoolProperty(name="Add Bolts", default=True)

    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Pipe Body", "uv": "CYLINDER", "phys": "METAL_IRON"},
            1: {"name": "Flange", "uv": "BOX", "phys": "METAL_IRON"},
            2: {"name": "Bolts", "uv": "BOX", "phys": "METAL_DARK"},
            9: {"name": "Socket", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.label(text="TYPE", icon="OUTLINER_OB_CURVE")
        layout.prop(self, "style", text="")

        layout.separator()
        layout.label(text="DIMENSIONS", icon="Driver")
        col = layout.column(align=True)
        col.prop(self, "radius")
        col.prop(self, "length")

        layout.separator()
        layout.label(text="DETAILS", icon="MOD_SCREW")
        col = layout.column(align=True)
        col.prop(self, "flange_radius")
        col.prop(self, "flange_thick")
        layout.prop(self, "bolts")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        r = self.radius
        l = self.length # Distance from center to flange face
        fr = self.flange_radius
        ft = self.flange_thick

        # Helper: Create Flange at position with orientation
        def create_flange(pos, direction):
            # Direction is normal vector of flange face
            # Flange is a cylinder
            # We create at origin, align Z to direction, then translate
            builder.create_cylinder(radius=fr, depth=ft, segments=16, center=Vector((0,0,0)))

            # Safe UV Tagging
            all_faces = builder.active_faces[:]
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            caps = [f for f in all_faces if abs(f.normal.z) > 0.8]
            builder.active_faces = caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')

            # Bolts?
            if self.bolts:
                # Add bolts on the face facing AWAY from pipe?
                # Actually simpler: standard flange has bolts around perimeter
                # We can simulate with texture or small cubes/cylinders
                pass

            # Restore and Transform
            builder.active_faces = all_faces
            builder.align_normal_to_vector(direction) # Aligns Z to direction
            builder.translate(pos.x, pos.y, pos.z)

            # Create Socket at this end
            # Socket should point OUTWARD (Direction)
            # Create a grid slightly offset
            sock_pos = pos + (direction * (ft/2 + 0.01))
            builder.create_grid(1, 1, size=r*1.5).align_normal_to_vector(direction).move_center_to(sock_pos) \
                   .tag_slot(9).tag_socket(9).tag_uvs(scale=1.0, projection='BOX')

        # Helper: Create Pipe Arm
        def create_arm(start, end):
            vec = end - start
            dist = vec.length
            if dist < 0.001: return
            mid = (start + end) / 2

            builder.create_cylinder(radius=r, depth=dist, segments=16, center=Vector((0,0,0)))

            all_faces = builder.active_faces[:]
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='CYLINDER')
            # Caps usually hidden inside center or covered by flange, so pinching is ok-ish?
            # But better safe.
            caps = [f for f in all_faces if abs(f.normal.z) > 0.8]
            builder.active_faces = caps
            builder.tag_uvs(scale=self.uv_scale, projection='BOX')

            builder.active_faces = all_faces
            builder.align_normal_to_vector(vec)
            builder.translate(mid.x, mid.y, mid.z)

        # Build Styles
        if self.style == 'ELBOW':
            # 90 deg elbow. Radius of curvature? Let's say R = Length.
            # Start at -X, curve to +Y?
            # Or Start -Y, End +X.

            # Segmented elbow
            segs = 8
            angle_step = (math.pi / 2) / segs
            # Center of curvature at (l, 0, 0)? No.
            # Let's say corner is at (0,0,0).
            # Arm 1 goes -X for length l.
            # Arm 2 goes -Y for length l.
            # Curve connects (-R_curve, 0) to (0, -R_curve)?

            # Simple Elbow:
            # 1. Straight arm from (-l, 0, 0) to (-l + ft, 0, 0) [Flange]
            # No, user expects standard elbow fitting.
            # Let's pivot at (0,0,0).
            # Entrance at (-l, 0, 0). Exit at (0, -l, 0).
            # Curve between (-r, 0, 0) and (0, -r, 0)?

            # Let's use torus segment logic with extrude/rotate.
            # 1. Create initial circle at (-l, 0, 0) facing -X?
            # No, create circle at (radius_curve, 0, 0) then spin?

            # Simpler: Two straight pipes + Sphere in middle? (Cheating)
            # Or strict segments.

            # Let's make a segmented curve from (-l, 0, 0) to (0, -l, 0)
            # Center of turn: (-l, -l, 0). Radius of turn: l.
            # Angle 0 to 90.

            # 1. Create Circle at (-l, 0, 0) normal X.
            # MassaBuilder doesn't have create_circle.
            # But create_cylinder makes a cylinder. We can select top face and extrude.

            # Create a very thin cylinder at start to act as "Face"
            builder.create_cylinder(radius=r, depth=0.01, segments=16, center=Vector((0,0,0)))
            # Align to X (so normal is X)
            builder.rotate(90, 'Y')
            builder.translate(-l, 0, 0)

            # Tag Pipe
            builder.tag_slot(0) # Tag all

            # Select the face facing +X (Normal (1, 0, 0))
            builder.select_faces_by_normal(Vector((1, 0, 0)))

            # Extrude & Rotate loop
            # Turn radius R_turn. If start is (-l,0,0) and end is (0,-l,0),
            # R_turn could be l. Center of turn at (-l, -l, 0)? No.
            # Start (-l, 0), End (0, -l).
            # Tangent at Start is X (1,0). Tangent at End is Y (0,-1)?
            # That's a 90 deg turn.

            steps = 8
            step_angle = 90.0 / steps
            step_dist = (math.pi * l * 0.5) / steps # Arc length for 90 deg

            # Actually extrusion needs to translate AND rotate to form arc.
            # Extrude dist?
            # Chord length for step_angle and radius l?
            # 2 * R * sin(theta/2).
            # But simple extrude + rotate works for visual pipe.

            # We want to turn from X+ direction to Y- direction?
            # Current Normal: (1, 0, 0).
            # Turn right (towards -Y).

            for i in range(steps):
                # Extrude slightly?
                # Actually we want 'Spin'.
                # Builder: extrude -> translate(radius * sin(a), radius * (1-cos(a)))?
                # Too complex math for quick builder.

                # Manual segment placement is easier.
                pass

            # Fallback: Just create straight segments approximating curve.
            curve_radius = l
            center_curve = Vector((0, 0, 0)) # Pivot
            # Start: (-l, 0). End (0, -l).
            # This implies center of curvature is (-l, -l)? No.
            # Let's assume input params: Radius r, Length l.
            # L is usually distance from center intersection to face.

            # For Elbow, L is distance from corner intersection to face.
            # Corner is (0,0,0).
            # Face 1: (-l, 0, 0). Face 2: (0, -l, 0).
            # Path: Line from (-l,0,0) to (-r, 0, 0). Curve (-r,0) to (0,-r). Line (0,-r) to (0,-l).
            # If l < r, just curve.

            # Simplified Elbow: Two cylinders meeting at 45 deg cut?
            # Or 3 segments.

            # Let's generate a path of points and cylinder-them.
            points = []
            steps = 6
            corner_offset = min(l * 0.5, r * 2) # Curve part size

            # Straight part 1
            if l > corner_offset:
                points.append(Vector((-l, 0, 0)))
                points.append(Vector((-corner_offset, 0, 0)))
                create_arm(points[0], points[1])
                create_flange(points[0], Vector((-1, 0, 0)))

            # Curve part
            # 90 deg arc from (-corner_offset, 0) to (0, -corner_offset)
            # Center (-corner_offset, -corner_offset).
            # Angle 90 to 0.

            prev_p = Vector((-corner_offset, 0, 0))
            for i in range(1, steps + 1):
                t = i / steps
                angle = (math.pi / 2) * (1 - t) # 90 down to 0

                # Circle: x = cx + R*cos, y = cy + R*sin
                # Center (-corner_offset, -corner_offset)
                # R = corner_offset
                px = -corner_offset + corner_offset * math.cos(angle) # cos(90)=0 -> -corner; cos(0)=1 -> 0
                py = -corner_offset + corner_offset * math.sin(angle) # sin(90)=1 -> 0; sin(0)=0 -> -corner

                p = Vector((px, py, 0))
                create_arm(prev_p, p)
                prev_p = p

            # Straight part 2
            if l > corner_offset:
                create_arm(Vector((0, -corner_offset, 0)), Vector((0, -l, 0)))
                create_flange(Vector((0, -l, 0)), Vector((0, -1, 0)))
            else:
                 create_flange(Vector((0, -corner_offset, 0)), Vector((0, -1, 0)))

        elif self.style == 'T_JOINT':
            # Horizontal Pipe (-L to +L)
            create_arm(Vector((-l, 0, 0)), Vector((l, 0, 0)))
            create_flange(Vector((-l, 0, 0)), Vector((-1, 0, 0)))
            create_flange(Vector((l, 0, 0)), Vector((1, 0, 0)))

            # Vertical Branch (0 to -L or +L?) T usually has stem.
            # Stem to -Y
            create_arm(Vector((0, 0, 0)), Vector((0, -l, 0)))
            create_flange(Vector((0, -l, 0)), Vector((0, -1, 0)))

        elif self.style == 'CROSS':
            # Horizontal (-L to +L)
            create_arm(Vector((-l, 0, 0)), Vector((l, 0, 0)))
            create_flange(Vector((-l, 0, 0)), Vector((-1, 0, 0)))
            create_flange(Vector((l, 0, 0)), Vector((1, 0, 0)))

            # Vertical (-L to +L)
            create_arm(Vector((0, -l, 0)), Vector((0, l, 0)))
            create_flange(Vector((0, -l, 0)), Vector((0, -1, 0)))
            create_flange(Vector((0, l, 0)), Vector((0, 1, 0)))

        builder.clean()
