import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_04: Universal Portal",
    "id": "arc_04_doorway",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcDoorway(Massa_OT_Base):
    bl_idname = "massa.gen_arc_04_doorway"
    bl_label = "ARC Doorway"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    door_width: FloatProperty(name="Width", default=1.0, min=0.1)
    door_height: FloatProperty(name="Height", default=2.1, min=0.1)
    frame_width: FloatProperty(name="Frame W", default=0.1, min=0.01)
    frame_depth: FloatProperty(name="Frame D", default=0.15, min=0.01)

    # Leaf
    leaf_thick: FloatProperty(name="Leaf T", default=0.05, min=0.01)
    open_angle: FloatProperty(name="Open Angle", default=0.0, min=-180, max=180)

    # Hardware
    handle_height: FloatProperty(name="Handle H", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Door Leaf", "uv": "BOX", "phys": "WOOD"},
            1: {"name": "Frame", "uv": "BOX", "phys": "WOOD"},
            7: {"name": "Hardware", "uv": "BOX", "phys": "METAL_BRASS"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        dw = self.door_width
        dh = self.door_height
        fw = self.frame_width
        fd = self.frame_depth
        lt = self.leaf_thick

        uv_s1 = getattr(self, "uv_scale_1", 1.0)
        uv_s0 = getattr(self, "uv_scale_0", 1.0)
        uv_s7 = getattr(self, "uv_scale_7", 1.0)

        # 1. Frame
        # Side Jambs (Height dh)
        # Left
        builder.create_box(fw, fd, dh) \
               .translate(-dw/2 - fw/2, 0, dh/2) \
               .tag_slot(1) \
               .tag_uvs(uv_s1, 'BOX')

        # Right
        builder.create_box(fw, fd, dh) \
               .translate(dw/2 + fw/2, 0, dh/2) \
               .tag_slot(1) \
               .tag_uvs(uv_s1, 'BOX')

        # Header (Top). Width dw + 2*fw. Height fw.
        # Sits on top of Jambs (dh + fw/2)
        builder.create_box(dw + 2*fw, fd, fw) \
               .translate(0, 0, dh + fw/2) \
               .tag_slot(1) \
               .tag_uvs(uv_s1, 'BOX')

        # Stops
        stop_thick = 0.02
        stop_width = 0.03
        stop_y_offset = lt/2 + stop_width/2
        
        # Left Stop
        builder.create_box(stop_thick, stop_width, dh) \
               .translate(-dw/2 + stop_thick/2, stop_y_offset, dh/2) \
               .tag_slot(1) \
               .tag_uvs(uv_s1, 'BOX')

        # Right Stop
        builder.create_box(stop_thick, stop_width, dh) \
               .translate(dw/2 - stop_thick/2, stop_y_offset, dh/2) \
               .tag_slot(1) \
               .tag_uvs(uv_s1, 'BOX')

        # Header Stop
        builder.create_box(dw, stop_width, stop_thick) \
               .translate(0, stop_y_offset, dh - stop_thick/2) \
               .tag_slot(1) \
               .tag_uvs(uv_s1, 'BOX')

        # 2. Door Leaf
        # Initial Leaf Box
        builder.create_box(dw, lt, dh) \
               .translate(0, 0, dh/2) \
               .tag_slot(0) \
               .tag_uvs(uv_s0, 'BOX')

        # Panels (Inset)
        leaf_faces = [f for f in builder.active_faces if abs(f.normal.y) > 0.9]
        builder.active_faces = leaf_faces
        
        if leaf_faces:
            builder.inset(0.1, relative=False) \
                   .inset(0.03, depth=-0.015, relative=False) \
                   .tag_uvs(uv_s0, 'BOX')

        # 3. Hardware (Handle)
        h_h = self.handle_height
        h_x = dw/2 - 0.1
        h_y = lt/2 + 0.005
        
        builder.create_box(0.12, 0.04, 0.02) \
               .translate(h_x, h_y + 0.02, h_h) \
               .tag_slot(7) \
               .tag_uvs(uv_s7, 'BOX')

        # 4. Rotation Logic
        if abs(self.open_angle) > 0.001:
            pivot = Vector((-dw/2, 0, 0))
            
            # Select Leaf (0) and Hardware (7)
            target_verts = set()
            bm.verts.ensure_lookup_table()
            for f in bm.faces:
                if f.material_index in (0, 7):
                    for v in f.verts:
                        target_verts.add(v)

            if target_verts:
                builder.active_verts = list(target_verts)
                builder.translate(-pivot.x, -pivot.y, -pivot.z)
                builder.rotate(self.open_angle, 'Z')
                builder.translate(pivot.x, pivot.y, pivot.z)

        # 5. Sockets
        builder.create_grid(size=0.1) \
               .rotate(90, 'X') \
               .translate(0, -0.1, 0) \
               .tag_slot(9) \
               .tag_socket(1)

        builder.clean()

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Dimensions", icon='MESH_CUBE')
        col = box.column(align=True)
        col.prop(self, "door_width")
        col.prop(self, "door_height")
        col.prop(self, "frame_width")
        col.prop(self, "frame_depth")

        box_leaf = layout.box()
        box_leaf.label(text="Leaf & Hardware", icon='MOD_BUILD')
        col = box_leaf.column(align=True)
        col.prop(self, "leaf_thick")
        col.prop(self, "handle_height")

        box_anim = layout.box()
        box_anim.label(text="State", icon='FILE_REFRESH')
        box_anim.prop(self, "open_angle")
