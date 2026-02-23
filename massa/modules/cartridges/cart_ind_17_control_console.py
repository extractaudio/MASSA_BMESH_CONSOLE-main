import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_17: Control Console",
    "id": "ind_17_control_console",
    "icon": "OUTLINER_OB_ARMATURE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_IndControlConsole(Massa_OT_Base):
    bl_idname = "massa.gen_ind_17_control_console"
    bl_label = "IND Control Console"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # 1. Style Enum
    style: EnumProperty(
        name="Console Type",
        items=[
            ("DESK", "Floor Console", "Sloped desk-style console"),
            ("WALL", "Wall Unit", "Vertical wall-mounted panel"),
            ("PEDESTAL", "Pedestal Kiosk", "Small standalone podium"),
        ],
        default="DESK"
    )

    # 2. Dimensions
    width: FloatProperty(name="Width", default=1.2, min=0.3)
    height: FloatProperty(name="Height", default=1.2, min=0.5)
    depth: FloatProperty(name="Depth", default=0.8, min=0.3)

    # 3. Shape
    base_height: FloatProperty(name="Base Height", default=0.7, min=0.0)
    slope_angle: FloatProperty(name="Slope Angle", default=30.0, min=0.0, max=80.0)
    top_depth: FloatProperty(name="Top Depth", default=0.2, min=0.05)

    # 4. Details
    screen_count: IntProperty(name="Screens", default=2, min=0, max=5)
    screen_size: FloatProperty(name="Screen Scale", default=0.8, min=0.1, max=1.0)
    button_rows: IntProperty(name="Button Rows", default=3, min=0, max=10)
    keyboard_tray: BoolProperty(name="Keyboard Tray", default=True)
    panel_inset: FloatProperty(name="Panel Inset", default=0.02, min=0.0, max=0.1)

    vent_slots: BoolProperty(name="Rear Vents", default=True)
    foot_height: FloatProperty(name="Foot Height", default=0.05, min=0.0, max=0.5)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Casing", "uv": "BOX", "phys": "PLASTIC_HARD"},
            1: {"name": "Screen Glass", "uv": "FIT", "phys": "GLASS"},
            2: {"name": "Buttons/Controls", "uv": "BOX", "phys": "PLASTIC_SOFT"},
            3: {"name": "Vents/Grill", "uv": "BOX", "phys": "METAL_MESH"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "BOX", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        layout.prop(self, "style")

        box = layout.box()
        box.label(text="Dimensions")
        box.prop(self, "width")
        box.prop(self, "height")
        box.prop(self, "depth")

        box = layout.box()
        box.label(text="Profile")
        box.prop(self, "base_height")
        box.prop(self, "slope_angle")
        box.prop(self, "top_depth")

        box = layout.box()
        box.label(text="Interface")
        col = box.column(align=True)
        col.prop(self, "screen_count")
        col.prop(self, "screen_size")
        col.prop(self, "button_rows")
        col.prop(self, "keyboard_tray")

        box = layout.box()
        box.label(text="Details")
        col = box.column(align=True)
        col.prop(self, "vent_slots")
        col.prop(self, "foot_height")
        col.prop(self, "panel_inset")

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        w = self.width
        h = self.height
        d = self.depth
        bh = min(self.base_height, h - 0.2)

        if self.style == "DESK":
            # 1. Base Cabinet
            cab_h = bh - self.foot_height
            if cab_h > 0.1:
                # Create at origin then move up
                builder.create_box(w, d*0.8, cab_h, center=Vector((0,0,0)))
                builder.translate(0, 0, self.foot_height + cab_h/2)
                builder.tag_slot(0)

            # Feet
            if self.foot_height > 0.01:
                ft_sz = 0.05
                for fx in [-w/2 + 0.1, w/2 - 0.1]:
                    for fy in [-d/2 + 0.1, d/2 - 0.1]:
                         builder.create_box(ft_sz, ft_sz, self.foot_height, center=Vector((0,0,0)))
                         builder.translate(fx, fy, self.foot_height/2)
                         builder.tag_slot(0)

            # 2. Console Top (Sloped)
            top_thick = 0.15
            panel_len = (h - bh) / math.sin(math.radians(self.slope_angle)) if self.slope_angle > 10 else (h-bh)
            if panel_len > d*1.5: panel_len = d*1.5 # Clamp

            # Create Panel Box at origin
            # Rotate -slope_angle around X
            builder.create_box(w, panel_len, top_thick, center=Vector((0, panel_len/2, -top_thick/2)))
            builder.rotate(-self.slope_angle, axis='X')

            # Move to pivot (Front Edge of base)
            pivot = Vector((0, -d/2 + 0.1, bh))
            builder.translate(pivot.x, pivot.y, pivot.z)
            builder.tag_slot(0)

            # 3. Screens on Panel
            if self.screen_count > 0:
                base_scr_w = (w * 0.8) / self.screen_count
                scr_w = base_scr_w * self.screen_size
                scr_h = panel_len * 0.4 * self.screen_size

                for i in range(self.screen_count):
                    # Local Offset
                    # Center of slot i
                    slot_center_x = -w*0.4 + base_scr_w/2 + i*base_scr_w

                    local_pos = Vector((slot_center_x, panel_len*0.6, 0.05))

                    # Create Screen at origin
                    builder.create_box(scr_w, scr_h, 0.05, center=Vector((0,0,0)))

                    # Rotate Screen Locally to match slope
                    builder.rotate(-self.slope_angle, axis='X')

                    # Calculate Global Position for translation
                    # Apply rotation matrix to local_pos offset
                    rot_mat = Matrix.Rotation(math.radians(-self.slope_angle), 4, 'X')
                    glob_offset = rot_mat @ local_pos
                    glob_pos = pivot + glob_offset

                    builder.translate(glob_pos.x, glob_pos.y, glob_pos.z)
                    builder.tag_slot(1)

            # 4. Buttons on Panel
            if self.button_rows > 0:
                btn_area_h = panel_len * 0.3
                local_pos = Vector((0, panel_len*0.2, 0.02))

                builder.create_box(w*0.8, btn_area_h, 0.02, center=Vector((0,0,0)))
                builder.rotate(-self.slope_angle, axis='X')

                rot_mat = Matrix.Rotation(math.radians(-self.slope_angle), 4, 'X')
                glob_offset = rot_mat @ local_pos
                glob_pos = pivot + glob_offset

                builder.translate(glob_pos.x, glob_pos.y, glob_pos.z)
                builder.tag_slot(2)

            # 5. Keyboard Tray
            if self.keyboard_tray:
                 tray_depth = 0.25
                 tray_z = bh - 0.1
                 builder.create_box(w, tray_depth, 0.05, center=Vector((0,0,0)))
                 builder.translate(0, -d/2 - tray_depth/2 + 0.1, tray_z)
                 builder.tag_slot(2)

        elif self.style == "WALL":
            # Wall Box
            box_h = h * 0.6
            box_z = h/2 + 0.4
            builder.create_box(w, d*0.4, box_h, center=Vector((0,0,0)))
            builder.translate(0, 0, box_z)
            builder.tag_slot(0)

            # Screen Face
            builder.create_box(w*0.9, 0.02, box_h*0.8, center=Vector((0,0,0)))
            builder.translate(0, -d*0.2 - 0.01, box_z) # Slight offset front
            builder.tag_slot(1)

        elif self.style == "PEDESTAL":
            # Column
            col_w = w * 0.3
            col_h = h * 0.8
            builder.create_box(col_w, col_w, col_h, center=Vector((0,0,0)))
            builder.translate(0, 0, col_h/2)
            builder.tag_slot(0)

            # Angled Head
            head_size = w * 0.6
            head_thick = 0.15
            pivot = Vector((0, 0, col_h))

            builder.create_box(head_size, head_size, head_thick, center=Vector((0,0,0)))
            builder.rotate(45, axis='X')
            builder.translate(pivot.x, pivot.y, pivot.z)
            builder.tag_slot(1)

        # Vents
        if self.vent_slots:
            slat_w = w * 0.6
            slat_h = 0.05
            slat_d = 0.02

            back_y = d/2 if self.style == "DESK" else 0.1
            center_x = 0
            start_z = bh * 0.2

            for i in range(5):
                z = start_z + i * 0.1
                if z < h:
                    builder.create_box(slat_w, slat_d, slat_h, center=Vector((0,0,0)))
                    builder.translate(center_x, back_y, z)
                    builder.tag_slot(3)

        # Socket (Floor)
        min_z = 1000
        for f in bm.faces:
             z = f.calc_center_median().z
             if z < min_z: min_z = z

        active_faces = [f for f in bm.faces if abs(f.calc_center_median().z - min_z) < 0.05 and f.normal.z < -0.5]
        builder.active_faces = active_faces
        builder.tag_socket(9).tag_slot(9)

        # UV
        builder.select_all_faces().tag_uvs(scale=self.uv_scale, projection='BOX')
        builder.clean()

    def execute(self, context):
        return super().execute(context)
