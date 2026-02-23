import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_04: Ladder",
    "id": "ind_04_ladder",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndLadder(Massa_OT_Base):
    bl_idname = "massa.gen_ind_04_ladder"
    bl_label = "IND Ladder"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    height: FloatProperty(name="Height", default=4.0, min=0.1)
    width: FloatProperty(name="Width", default=0.5, min=0.1)
    rail_thick: FloatProperty(name="Rail Thick", default=0.03, min=0.01)
    rung_spacing: FloatProperty(name="Rung Spacing", default=0.3, min=0.1)
    rung_radius: FloatProperty(name="Rung Radius", default=0.015, min=0.005)

    # Cage
    has_cage: BoolProperty(name="Safety Cage", default=True)
    cage_start_height: FloatProperty(name="Cage Start H", default=2.2, min=0.0)
    cage_radius: FloatProperty(name="Cage Radius", default=0.4, min=0.1)
    cage_strips: IntProperty(name="Cage Strips", default=5, min=3)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Metal", "uv": "SKIP", "phys": "METAL_STEEL"},
            6: {"name": "Warning Paint", "uv": "SKIP", "phys": "PAINT"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "height")
        col.prop(self, "width")
        col.prop(self, "rail_thick")
        col.prop(self, "rung_spacing")
        col.prop(self, "rung_radius")
        layout.separator()
        col.prop(self, "has_cage")
        if self.has_cage:
            col.prop(self, "cage_start_height")
            col.prop(self, "cage_radius")
            col.prop(self, "cage_strips")

    def build_shape(self, bm):
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        h = self.height
        w = self.width
        rt = self.rail_thick
        rr = self.rung_radius

        # 1. Rails (Vertical)
        # Left (-w/2)
        # Using Square rails for industrial look
        builder.create_box(rt, rt, h, center=Vector((-w/2, 0, h/2)))
        builder.tag_slot(0).select_boundary().tag_edge_role(1)

        # Right (w/2)
        builder.create_box(rt, rt, h, center=Vector((w/2, 0, h/2)))
        builder.tag_slot(0).select_boundary().tag_edge_role(1)

        # 2. Rungs
        # Create cylinder connecting rails
        # Oriented X
        num_rungs = int(h / self.rung_spacing)

        # Pre-calculate rotation for X-aligned cylinder
        # create_cylinder makes Z-aligned. rotate 90 deg on Y.
        rot_mat = Matrix.Rotation(math.radians(90), 4, 'Y')

        for i in range(num_rungs):
            z = (i + 0.5) * self.rung_spacing
            if z > h - 0.1: continue

            # Rung length = w - rt (fits between rails)
            # Center = (0, 0, z)

            # Create cylinder at origin, rotate, translate
            builder.create_cylinder(radius=rr, depth=w - rt, segments=8, center=Vector((0,0,0)))
            builder.transform(rot_mat)
            builder.translate(0, 0, z)

            builder.tag_slot(0)
            # Mark ends as Seams?
            builder.select_boundary().tag_edge_role(1)

        # 3. Cage
        if self.has_cage and h > self.cage_start_height:
            c_rad = self.cage_radius
            c_start = self.cage_start_height

            # Cage Hoops
            hoop_dist = 1.0 # Spacing

            # Calculate hoop positions
            z_positions = []
            curr_z = c_start
            while curr_z < h:
                z_positions.append(curr_z)
                curr_z += hoop_dist
            # Always add one at top if not close
            if z_positions and (h - z_positions[-1]) > 0.3:
                z_positions.append(h)
            elif not z_positions:
                z_positions.append(h)

            # Helper for Hoop Segment
            # Arc from angle Pi (Left) to 2Pi (Right) via 1.5Pi (Back/Front?)
            # Ladder at Y=0. User climbs on -Y side (Front)? Or +Y (Back)?
            # Usually ladder is mounted to wall at +Y. User climbs on -Y side.
            # Cage encloses user on -Y side.
            # So Arc is in -Y half.
            # Angles: 180 (Left/ -X) -> 270 (Front / -Y) -> 360/0 (Right / +X).
            # So range 180 to 360 degrees.

            # We construct hoop from small straight segments (pipe approximations)
            # Or simplified: use torus segment logic?
            # Let's use pipe segments for "Solid" geometry.

            steps = 8
            angle_start = math.pi
            angle_end = 0 # 2*pi
            angle_span = -math.pi # Clockwise?
            # Math:
            # Angle 180 is (-1, 0).
            # Angle 270 is (0, -1).
            # Angle 360 is (1, 0).
            # Standard cos/sin:
            # 180 -> x=-1, y=0.
            # 270 -> x=0, y=-1.
            # 0 -> x=1, y=0.

            for z in z_positions:
                prev_pt = None

                # Create arc points
                for s in range(steps + 1):
                    t = s / steps
                    angle = angle_start + t * angle_span # 180 -> 0 (via negative?)
                    # Wait, 180 + (-180) = 0.
                    # Range is Pi to 0.

                    # x = cos(angle) * r
                    # y = sin(angle) * r
                    # This gives semi-circle in -Y if we go 180 -> 0 via 270?
                    # 180 -> (-1, 0)
                    # 90 -> (0, 1) -- Wrong side
                    # 270 -> (0, -1) -- Correct side
                    # 0 -> (1, 0)

                    # We need to go 180 -> 270 -> 360 (0).
                    # 180 is Pi. 360 is 2Pi.
                    # So range Pi to 2Pi.

                    angle = math.pi + t * math.pi

                    lx = math.cos(angle) * c_rad
                    ly = math.sin(angle) * c_rad

                    curr_pt = Vector((lx, ly, z))

                    if prev_pt:
                        # Create segment from prev_pt to curr_pt
                        # Thickness of hoop = 0.02
                        hoop_thick = 0.02

                        # Use create_strut logic (inline here)
                        vec = curr_pt - prev_pt
                        dist = vec.length
                        mid = (prev_pt + curr_pt) / 2

                        direction = vec.normalized()
                        q = Vector((0,0,1)).rotation_difference(direction)
                        m = Matrix.Translation(mid) @ q.to_matrix().to_4x4()

                        builder.create_cylinder(radius=hoop_thick/2, depth=dist, segments=6, center=Vector((0,0,0)))
                        builder.transform(m)
                        builder.tag_slot(6) # Paint

                    prev_pt = curr_pt

            # Cage Vertical Strips
            # Connect hoops vertically
            num_strips = self.cage_strips
            for i in range(num_strips):
                # Distribute along the arc
                t = i / (num_strips - 1)
                angle = math.pi + t * math.pi

                lx = math.cos(angle) * c_rad
                ly = math.sin(angle) * c_rad

                # Strip goes from c_start to h
                # Create Box/Cylinder
                strip_len = h - c_start
                if strip_len > 0:
                    center_z = c_start + strip_len/2
                    pos = Vector((lx, ly, center_z))

                    # Flat strip oriented to normal?
                    # Normal is (lx, ly, 0).normalized()
                    # Tangent Z.

                    # Box 0.04 wide, 0.005 thick
                    strip_w = 0.04
                    strip_t = 0.005

                    builder.create_box(strip_w, strip_t, strip_len, center=Vector((0,0,0)))

                    # Rotate to face center
                    # Default box faces Y (depth).
                    # We want depth (Y) to align with radius vector (lx, ly).
                    # Or width (X) to align with tangent.

                    normal = Vector((lx, ly, 0)).normalized()
                    # Box Front is -Y.
                    # We want -Y to point to Center (0,0)? Or +Y to Center?
                    # Usually strips are flat against the hoop.
                    # So normal of strip face (Y) should align with radius (normal).

                    q = Vector((0,1,0)).rotation_difference(normal)
                    m = Matrix.Translation(pos) @ q.to_matrix().to_4x4()

                    builder.transform(m)
                    builder.tag_slot(6)

        # 4. Sockets
        # Top/Bottom of rails
        # Since rails are boxes, we can select faces.
        # Bottom (-Z? No, Z=0)
        # Rails start at 0, go to h.
        # But rail box created at center h/2.
        # So bottom is at 0.

        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.1) \
               .tag_socket(9).tag_slot(9)

        builder.select_faces_by_normal(Vector((0, 0, 1)), tolerance=0.1) \
               .tag_socket(9).tag_slot(9)

        # 5. Manual UVs
        # Slot 0 (Metal): Box
        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Slot 6 (Paint): Box
        builder.select_faces_by_slot(6) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        builder._update()
