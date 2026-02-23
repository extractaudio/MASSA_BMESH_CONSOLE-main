import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_12: Overhead Door",
    "id": "arc_12_overhead_door",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_ArcOverheadDoor(Massa_OT_Base):
    bl_idname = "massa.gen_arc_12_overhead_door"
    bl_label = "ARC Overhead Door"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("SECTIONAL", "Sectional", "Panel door on tracks"),
            ("ROLLING", "Rolling Steel", "Coiling slat door"),
            ("HIGH_SPEED", "High Speed", "Fabric roll-up door"),
        ],
        default="SECTIONAL"
    )

    # Dimensions
    width: FloatProperty(name="Width", default=3.0, min=1.0)
    height: FloatProperty(name="Height", default=3.5, min=1.5)

    # Frame
    frame_width: FloatProperty(name="Jamb Width", default=0.15, min=0.05)
    frame_depth: FloatProperty(name="Jamb Depth", default=0.2, min=0.05)

    # Door Details
    panel_count: IntProperty(name="Panel Count", default=6, min=1, max=12) # For Sectional
    slat_height: FloatProperty(name="Slat Height", default=0.1, min=0.05) # For Rolling

    # Features
    window_row: IntProperty(name="Window Row", default=3, min=0, max=12) # 0 = None
    track_depth: FloatProperty(name="Track Depth", default=3.0, min=0.5)
    coil_diameter: FloatProperty(name="Coil Dia", default=0.4, min=0.2)
    motor_mount: BoolProperty(name="Motor Op", default=True)

    open_pct: FloatProperty(name="Open %", default=0.0, min=0.0, max=100.0)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame/Track", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Door Panels", "uv": "BOX", "phys": "METAL_PAINTED"},
            2: {"name": "Windows", "uv": "BOX", "phys": "GLASS_IND"},
            3: {"name": "Motor/Mech", "uv": "BOX", "phys": "METAL_DARK"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions", icon='Length')
        col = box.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "open_pct")

        box = layout.box()
        box.label(text="Frame & Track", icon='MOD_WIREFRAME')
        col = box.column(align=True)
        col.prop(self, "frame_width")
        col.prop(self, "frame_depth")
        if self.style == "SECTIONAL":
            col.prop(self, "track_depth")

        box = layout.box()
        box.label(text="Door Leaf", icon='MESH_GRID')
        col = box.column(align=True)
        if self.style == "SECTIONAL":
            col.prop(self, "panel_count")
            col.prop(self, "window_row")
        elif self.style == "ROLLING":
            col.prop(self, "slat_height")
            col.prop(self, "coil_diameter")
            col.prop(self, "motor_mount")
        elif self.style == "HIGH_SPEED":
            col.prop(self, "coil_diameter")
            col.prop(self, "window_row", text="Vision Panel Row")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        w = self.width
        h = self.height
        fw = min(self.frame_width, w * 0.4) # Clamp
        fd = min(self.frame_depth, 1.0)

        # Origin: Center of bottom opening? Or corner?
        # Standard: Center X, Bottom Z (0).
        # Y=0 is the wall plane.
        # Door usually mounts on inside face (Y > 0 or Y < 0?).
        # Let's say Y=0 is outside face of wall. Door frame creates depth.
        # Frame goes from Y=0 to Y=-fd (Into building).

        # 1. Frame (Jambs)
        # Left Jamb
        builder.create_box(fw, fd, h, center=Vector((-w/2 - fw/2, -fd/2, h/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Right Jamb
        builder.create_box(fw, fd, h, center=Vector((w/2 + fw/2, -fd/2, h/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # Header (Top)
        header_h = fw # same as width
        builder.create_box(w + 2*fw, fd, header_h, center=Vector((0, -fd/2, h + header_h/2)))
        builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 2. Tracks / Guides
        track_offset = 0.05
        track_w = 0.05

        if self.style == "SECTIONAL":
            # Vertical Tracks
            builder.create_box(track_w, track_w, h, center=Vector((-w/2 - track_offset, -fd - track_w/2, h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(track_w, track_w, h, center=Vector((w/2 + track_offset, -fd - track_w/2, h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Horizontal Tracks (Overhead)
            td = max(self.track_depth, 0.5)
            # Curve radius
            tr = 0.3
            track_z = h + tr

            # Horizontal run
            builder.create_box(track_w, td, track_w, center=Vector((-w/2 - track_offset, -fd - td/2 - tr, track_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(track_w, td, track_w, center=Vector((w/2 + track_offset, -fd - td/2 - tr, track_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Curve (Fake with diagonal box for now)
            # Start: (x, -fd, h) End: (x, -fd-tr, h+tr)
            # Just put a 45 deg strut
            diag_len = math.sqrt(tr**2 + tr**2)

            # Left Curve
            cx = -w/2 - track_offset
            cz = h + tr/2
            cy = -fd - tr/2
            builder.create_box(track_w, diag_len, track_w, center=Vector((cx, cy, cz)))
            builder.rotate(45, axis='X') # Rotate around X to angle back/up
            # Center of rotation? create_box uses center.
            # 45 deg slope.
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Right Curve
            cx = w/2 + track_offset
            builder.create_box(track_w, diag_len, track_w, center=Vector((cx, cy, cz)))
            builder.rotate(45, axis='X')
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Torsion Spring Shaft
            builder.create_cylinder(radius=0.05, depth=w + 0.5, center=Vector((0, -fd - 0.2, h + 0.3)))
            builder.rotate(90, axis='Y')
            builder.bm.normal_update()

            # Fix Spring UVs
            all_spring = builder.active_faces[:]
            caps = [f for f in all_spring if abs(f.normal.x) > 0.9]
            walls = [f for f in all_spring if f not in caps]

            builder.active_faces = all_spring
            builder.tag_slot(3)

            if caps:
                builder.active_faces = caps
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls:
                builder.active_faces = walls
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER', axis='X')

        elif self.style in ["ROLLING", "HIGH_SPEED"]:
            # Vertical Guides (Deep channels)
            guide_d = 0.1
            guide_w = 0.08

            builder.create_box(guide_w, guide_d, h, center=Vector((-w/2 - guide_w/2, -fd/2, h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(guide_w, guide_d, h, center=Vector((w/2 + guide_w/2, -fd/2, h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Coil / Hood
            cd = max(self.coil_diameter, 0.2)
            hood_y = -fd/2
            hood_z = h + cd/2

            # Hood Box (Square or Round)
            builder.create_box(w + 2*guide_w, cd, cd, center=Vector((0, hood_y, hood_z)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Motor
            if self.motor_mount:
                builder.create_box(0.3, 0.3, 0.4, center=Vector((w/2 + fw + 0.2, hood_y, hood_z)))
                builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 3. Door Panels
        # Calculate closed height
        closed_h = h * (1.0 - self.open_pct / 100.0)

        door_thick = 0.05
        door_y = -fd/2 # Centered in jambs

        if self.style == "SECTIONAL":
            pc = max(self.panel_count, 1)
            ph = h / pc

            # Only draw panels up to closed_h
            # Actually, panels should be visible in the open position (horizontal) too?
            # That's complex. Let's just draw the closed portion for now, or stack them?
            # If open_pct > 0, bottom panels move up?
            # Let's implement: Draw panels from Top down? Or Bottom up?
            # If open, bottom panels disappear (go into track).
            # For simplicity: Draw panels from (h - closed_h) to h?
            # No, standard door opens by sliding UP.
            # So bottom is at Z = (h * open_pct/100)? No, bottom moves up.

            current_z = (h - closed_h) # If 10% open, starts at 0.1h? No.
            # If 100% open, current_z = h. Closed_h = 0.
            # If 0% open, current_z = 0. Closed_h = h.

            lift = h * (self.open_pct / 100.0)

            for i in range(pc):
                # Panel position in closed state
                pz_center = (i + 0.5) * ph

                # Actual position
                actual_z = pz_center + lift

                # If actual_z > h, it's in the horizontal track.
                # Simplified: If > h, don't draw or draw horizontal?
                # Let's just clip and not draw if > h + ph/2

                if actual_z < h + ph/2:
                    # Draw panel
                    # If it's crossing the curve, it should rotate.
                    # Simplified: Only draw vertical panels for now.

                    if actual_z < h:
                        builder.create_box(w, door_thick, ph - 0.01, center=Vector((0, door_y, actual_z)))

                        # Slot 1 (Panel) or 2 (Window)
                        slot = 1
                        if self.window_row > 0 and (i + 1) == self.window_row:
                            # Window Panel
                            # Frame it?
                            # Just tag slot 2?
                            # Let's inset and tag.
                            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

                            # Select Front/Back faces
                            builder.select_faces_by_normal(Vector((0,1,0)))
                            # Filter for Y approx door_y +/- door_thick/2
                            # Actually just Front (Y+)
                            fronts = [f for f in builder.active_faces if f.normal.y > 0.5]
                            if fronts:
                                builder.active_faces = fronts
                                # Clamp inset to prevent inversion on small panels
                                ins_amt = min(0.1, ph * 0.45, w * 0.45)
                                builder.inset(ins_amt, depth=0.0)
                                builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
                        else:
                            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

        elif self.style == "ROLLING":
            # Just a big sheet with ridges
            if closed_h > 0.1:
                # Draw sheet
                # Center z = h - closed_h/2 ? No.
                # Top is fixed at h? No, top unrolls.
                # Bottom is at lift. Top is at h.

                lift = h - closed_h
                sheet_h = closed_h

                # Create sheet
                builder.create_box(w, 0.02, sheet_h, center=Vector((0, door_y, lift + sheet_h/2)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Add horizontal cuts for slats visual?
                # Texture is safer.

        elif self.style == "HIGH_SPEED":
            # Fabric sheet
            if closed_h > 0.1:
                lift = h - closed_h
                sheet_h = closed_h

                builder.create_box(w, 0.01, sheet_h, center=Vector((0, door_y, lift + sheet_h/2)))

                # Vision Panel?
                if self.window_row > 0:
                    # Slice or just tag?
                    # Tag entire middle section?
                    # Let's rely on texture or simple geometry.
                    builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
                else:
                    builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

                # Bottom Bar (Weighted)
                builder.create_box(w, 0.05, 0.1, center=Vector((0, door_y, lift + 0.05)))
                builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

        # 4. Sockets
        # Base (Ground) - use Jamb bottoms
        builder.select_faces_by_normal(Vector((0,0,-1)))
        bases = [f for f in builder.active_faces if abs(f.calc_center_median().z) < 0.1]
        builder.active_faces = bases
        builder.tag_socket(9)

        builder.clean()

    def execute(self, context):
        return super().execute(context)
