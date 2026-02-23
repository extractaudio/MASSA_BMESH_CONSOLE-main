import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_15: Guard Booth",
    "id": "arc_15_guard_booth",
    "icon": "HOME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_ArcGuardBooth(Massa_OT_Base):
    bl_idname = "massa.gen_arc_15_guard_booth"
    bl_label = "ARC Guard Booth"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("RECTANGULAR", "Rectangular", "Standard box booth"),
            ("OCTAGONAL", "Octagonal", "8-sided view"),
            ("ROUNDED", "Rounded Ends", "Capsule shape"),
        ],
        default="RECTANGULAR"
    )

    # Dimensions
    width: FloatProperty(name="Width", default=2.0, min=1.2)
    length: FloatProperty(name="Length", default=2.0, min=1.2) # Ignored for Octagonal (uses Width/2 radius)
    height: FloatProperty(name="Total Height", default=2.5, min=2.2)

    # Details
    sill_height: FloatProperty(name="Sill Height", default=1.0, min=0.5)
    header_height: FloatProperty(name="Header Height", default=0.3, min=0.1)
    roof_overhang: FloatProperty(name="Roof Overhang", default=0.2, min=0.0)

    # Features
    door_width: FloatProperty(name="Door Width", default=0.9, min=0.6)
    hvac_unit: BoolProperty(name="HVAC Unit", default=True)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Walls/Structure", "uv": "BOX", "phys": "METAL_PANEL"},
            1: {"name": "Glass", "uv": "BOX", "phys": "GLASS_SAFETY"},
            2: {"name": "Roof/Fascia", "uv": "BOX", "phys": "METAL_DARK"},
            3: {"name": "Base/Floor", "uv": "BOX", "phys": "CONCRETE"},
            4: {"name": "Door", "uv": "BOX", "phys": "METAL_PAINTED"},
            5: {"name": "Mullions", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions", icon='Length')
        col = box.column(align=True)
        col.prop(self, "width")
        if self.style != "OCTAGONAL":
            col.prop(self, "length")
        col.prop(self, "height")

        box = layout.box()
        box.label(text="Design", icon='MOD_BUILD')
        col = box.column(align=True)
        col.prop(self, "sill_height")
        col.prop(self, "header_height")
        col.prop(self, "roof_overhang")

        box = layout.box()
        box.label(text="Features", icon='MOD_PHYSICS')
        col = box.column(align=True)
        col.prop(self, "door_width")
        col.prop(self, "hvac_unit")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        w = self.width
        l = self.length
        h = self.height
        sill_h = min(self.sill_height, h * 0.6)
        head_h = min(self.header_height, h * 0.2)
        win_h = h - sill_h - head_h
        if win_h < 0.1: win_h = 0.1 # Clamp logic

        oh = self.roof_overhang
        dw = min(self.door_width, w * 0.8)

        # Origin: Center Bottom.

        # Helper to create wall sections
        wall_thick = 0.1

        # 1. Base / Floor
        base_h = 0.15

        if self.style == "RECTANGULAR":
            builder.create_box(w, l, base_h, center=Vector((0, 0, base_h/2)))
            builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Walls
            # 4 Corners (Posts)? Or continuous lower wall?
            # Continuous lower wall with door gap.
            # Door on Front (Y-)?

            # Lower Walls (U shape)
            # Back
            builder.create_box(w, wall_thick, sill_h, center=Vector((0, l/2 - wall_thick/2, sill_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Left
            builder.create_box(wall_thick, l - 2*wall_thick, sill_h, center=Vector((-w/2 + wall_thick/2, 0, sill_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Right
            builder.create_box(wall_thick, l - 2*wall_thick, sill_h, center=Vector((w/2 - wall_thick/2, 0, sill_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Front (Door Gap)
            side_panel_w = (w - dw)/2
            if side_panel_w > 0.05:
                # Left Front
                builder.create_box(side_panel_w, wall_thick, sill_h, center=Vector((-w/2 + side_panel_w/2, -l/2 + wall_thick/2, sill_h/2)))
                builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Right Front
                builder.create_box(side_panel_w, wall_thick, sill_h, center=Vector((w/2 - side_panel_w/2, -l/2 + wall_thick/2, sill_h/2)))
                builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Upper Header (Ring)
            # Front
            builder.create_box(w, wall_thick, head_h, center=Vector((0, -l/2 + wall_thick/2, h - head_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Back
            builder.create_box(w, wall_thick, head_h, center=Vector((0, l/2 - wall_thick/2, h - head_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Left
            builder.create_box(wall_thick, l - 2*wall_thick, head_h, center=Vector((-w/2 + wall_thick/2, 0, h - head_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Right
            builder.create_box(wall_thick, l - 2*wall_thick, head_h, center=Vector((w/2 - wall_thick/2, 0, h - head_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Windows
            # Glass box inset
            glass_thick = 0.02
            # Back
            builder.create_box(w - 2*wall_thick, glass_thick, win_h, center=Vector((0, l/2 - wall_thick, sill_h + win_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Sides
            builder.create_box(glass_thick, l - 2*wall_thick, win_h, center=Vector((-w/2 + wall_thick, 0, sill_h + win_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(glass_thick, l - 2*wall_thick, win_h, center=Vector((w/2 - wall_thick, 0, sill_h + win_h/2)))
            builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
            # Front (Door side windows?)
            if side_panel_w > 0.1:
                # Left Win
                builder.create_box(side_panel_w - wall_thick, glass_thick, win_h, center=Vector((-w/2 + side_panel_w/2, -l/2 + wall_thick, sill_h + win_h/2)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
                # Right Win
                builder.create_box(side_panel_w - wall_thick, glass_thick, win_h, center=Vector((w/2 - side_panel_w/2, -l/2 + wall_thick, sill_h + win_h/2)))
                builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Door
            builder.create_box(dw, wall_thick/2, h - head_h, center=Vector((0, -l/2 + wall_thick/2, (h - head_h)/2)))
            builder.tag_slot(4).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Roof
            builder.create_box(w + 2*oh, l + 2*oh, 0.1, center=Vector((0, 0, h + 0.05)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')

        elif self.style == "OCTAGONAL":
            # 8 Sides.
            radius = w / 2.0
            side_len = radius * 2 * math.tan(math.pi/8) # approx

            # Base
            builder.create_cylinder(radius=radius, depth=base_h, segments=8, center=Vector((0, 0, base_h/2)))
            # Rotate 22.5 deg to have flat sides aligned with axes? 360/8 = 45.
            # Default cylinder usually has vertex at X.
            # Rotate 22.5 aligns face with X.
            builder.rotate(22.5, axis='Z')
            builder.bm.normal_update() # Update normals for UVs

            # Fix UVs on cylinder caps/walls
            # Similar logic to previous
            all_base = builder.active_faces[:]
            caps = [f for f in all_base if abs(f.normal.z) > 0.9]
            walls = [f for f in all_base if f not in caps]
            builder.active_faces = caps
            builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.active_faces = walls
            builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX') # Octagon walls are flat

            # Build Walls
            # 7 sides of Lower Wall + Glass + Header. 1 side Door.
            # Iterate 8 sides.
            # Side 0 (Front, -Y) is Door.

            for i in range(8):
                angle = i * 45 - 90 # Start at -90 (Front)
                is_door = (i == 0)

                # Position logic
                # Center of side face is at radius distance.
                rad_dist = radius - wall_thick/2
                rad = math.radians(angle)
                cx = math.cos(rad) * rad_dist
                cy = math.sin(rad) * rad_dist

                # Width of side
                sw = radius * 0.82 # 2*R*tan(22.5) roughly 0.828 R
                sw = 2 * radius * math.tan(math.pi/8)

                # Rotate box to face out
                # Box size: (sw, wall_thick, height)

                if is_door:
                    # Door
                    builder.create_box(sw, wall_thick/2, h - head_h, center=Vector((0,0,0)))
                    builder.rotate(angle + 90, axis='Z') # Box aligns X by default. Rotate to face normal.
                    builder.translate(cx, cy, (h - head_h)/2)
                    builder.tag_slot(4).tag_uvs(scale=self.uv_scale, projection='BOX')

                    # Header above door
                    builder.create_box(sw, wall_thick, head_h, center=Vector((0,0,0)))
                    builder.rotate(angle + 90, axis='Z')
                    builder.translate(cx, cy, h - head_h/2)
                    builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
                else:
                    # Wall + Window + Header
                    # Lower
                    builder.create_box(sw, wall_thick, sill_h, center=Vector((0,0,0)))
                    builder.rotate(angle + 90, axis='Z')
                    builder.translate(cx, cy, sill_h/2)
                    builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

                    # Header
                    builder.create_box(sw, wall_thick, head_h, center=Vector((0,0,0)))
                    builder.rotate(angle + 90, axis='Z')
                    builder.translate(cx, cy, h - head_h/2)
                    builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

                    # Window
                    builder.create_box(sw - 0.05, 0.02, win_h, center=Vector((0,0,0)))
                    builder.rotate(angle + 90, axis='Z')
                    builder.translate(cx, cy, sill_h + win_h/2)
                    builder.tag_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')

                    # Mullion (Corners)
                    # Add vertical post at corner?
                    # MassaBuilder clean() will not merge if slightly overlapping or separated.

            # Roof
            builder.create_cylinder(radius=radius + oh, depth=0.1, segments=8, center=Vector((0, 0, h + 0.05)))
            builder.rotate(22.5, axis='Z')
            # UVs
            builder.bm.normal_update()
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX') # Box for faceted roof

        elif self.style == "ROUNDED":
            # Capsule: Box middle, Cylinder ends.
            # Simplified: Cylinder ends at Left/Right? Or Front/Back?
            # Usually Ends. (Length)
            # Center box: Width w, Length l - w.
            # Cylinder caps: Radius w/2.

            mid_len = max(l - w, 0.1)
            radius = w/2.0

            # Base
            # Box
            builder.create_box(w, mid_len, base_h, center=Vector((0, 0, base_h/2)))
            builder.tag_slot(3).tag_uvs(scale=self.uv_scale, projection='BOX')
            # End Caps
            # Cylinder 1
            builder.create_cylinder(radius=radius, depth=base_h, center=Vector((0, mid_len/2, base_h/2)))
            builder.bm.normal_update()
            caps = [f for f in builder.active_faces if abs(f.normal.z) > 0.9]
            walls = [f for f in builder.active_faces if f not in caps]
            builder.tag_slot(3)
            if caps:
                builder.active_faces = caps
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls:
                builder.active_faces = walls
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

            # Cylinder 2
            builder.create_cylinder(radius=radius, depth=base_h, center=Vector((0, -mid_len/2, base_h/2)))
            builder.bm.normal_update()
            caps = [f for f in builder.active_faces if abs(f.normal.z) > 0.9]
            walls = [f for f in builder.active_faces if f not in caps]
            builder.tag_slot(3)
            if caps:
                builder.active_faces = caps
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls:
                builder.active_faces = walls
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

            # Walls (Similar mix)
            # Straight walls (Left/Right)
            builder.create_box(wall_thick, mid_len, sill_h, center=Vector((-w/2 + wall_thick/2, 0, sill_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(wall_thick, mid_len, sill_h, center=Vector((w/2 - wall_thick/2, 0, sill_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Curved Walls (Ends)
            # Front (Door?)
            # Let's put door on flat side (Left/Right)?
            # No, door usually on front/back flat part if it's a kiosk.
            # Or door on curved end.

            # Let's put Door on +Y Curved End.
            # Need to cut cylinder? Or just embed door box?
            # Embed box.
            builder.create_box(dw, wall_thick, h, center=Vector((0, mid_len/2 + radius, h/2)))
            builder.tag_slot(4).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Rear Curved Wall
            builder.create_cylinder(radius=radius, depth=sill_h, center=Vector((0, -mid_len/2, sill_h/2)))
            builder.bm.normal_update()
            caps = [f for f in builder.active_faces if abs(f.normal.z) > 0.9]
            walls = [f for f in builder.active_faces if f not in caps]
            builder.tag_slot(0)
            if caps:
                builder.active_faces = caps
                builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls:
                builder.active_faces = walls
                builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

            # Header Ring
            builder.create_box(wall_thick, mid_len, head_h, center=Vector((-w/2 + wall_thick/2, 0, h - head_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_box(wall_thick, mid_len, head_h, center=Vector((w/2 - wall_thick/2, 0, h - head_h/2)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')

            # Roof
            builder.create_box(w + 2*oh, mid_len, 0.1, center=Vector((0, 0, h + 0.05)))
            builder.tag_slot(2).tag_uvs(scale=self.uv_scale, projection='BOX')
            builder.create_cylinder(radius=radius + oh, depth=0.1, center=Vector((0, mid_len/2, h + 0.05)))
            # Fix UVs
            builder.bm.normal_update()
            caps = [f for f in builder.active_faces if abs(f.normal.z) > 0.9]
            walls = [f for f in builder.active_faces if f not in caps]
            builder.tag_slot(2)
            if caps: builder.active_faces = caps; builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls: builder.active_faces = walls; builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

            builder.create_cylinder(radius=radius + oh, depth=0.1, center=Vector((0, -mid_len/2, h + 0.05)))
            # Fix UVs
            builder.bm.normal_update()
            caps = [f for f in builder.active_faces if abs(f.normal.z) > 0.9]
            walls = [f for f in builder.active_faces if f not in caps]
            builder.tag_slot(2)
            if caps: builder.active_faces = caps; builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls: builder.active_faces = walls; builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        # HVAC
        if self.hvac_unit:
            builder.create_box(0.6, 0.6, 0.4, center=Vector((0, 0, h + 0.25)))
            builder.tag_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX') # Metal

            builder.create_cylinder(radius=0.2, depth=0.1, center=Vector((0, 0, h + 0.45)))
            builder.bm.normal_update()
            caps = [f for f in builder.active_faces if abs(f.normal.z) > 0.9]
            walls = [f for f in builder.active_faces if f not in caps]
            builder.tag_slot(2)
            if caps: builder.active_faces = caps; builder.tag_uvs(scale=self.uv_scale, projection='BOX')
            if walls: builder.active_faces = walls; builder.tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        # 4. Sockets
        # Base
        builder.select_faces_by_normal(Vector((0,0,-1)))
        bases = [f for f in builder.active_faces if abs(f.calc_center_median().z) < 0.1]
        builder.active_faces = bases
        builder.tag_socket(9)

        builder.clean()

    def execute(self, context):
        return super().execute(context)
