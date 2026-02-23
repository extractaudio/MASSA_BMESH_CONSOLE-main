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

    # Styles
    door_style: EnumProperty(
        name="Style",
        items=[
            ("STANDARD", "Standard", "Panel Door"),
            ("SCIFI", "Sci-Fi", "Blast Door / Bulkhead"),
            ("GLASS", "Glass", "Modern Storefront"),
        ],
        default="STANDARD"
    )

    def get_slot_meta(self):
        return {
            0: {"name": "Door Leaf", "uv": "SKIP", "phys": "DEBUG_1"},
            1: {"name": "Frame", "uv": "SKIP", "phys": "DEBUG_2"},
            3: {"name": "Glass", "uv": "SKIP", "phys": "DEBUG_4"}, # FIT is manual
            7: {"name": "Hardware", "uv": "SKIP", "phys": "DEBUG_3"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        dw = self.door_width
        dh = self.door_height
        fw = self.frame_width
        fd = self.frame_depth
        lt = self.leaf_thick

        # 1. Frame Generation
        # Side Jambs
        builder.create_box(fw, fd, dh) \
               .translate(-dw/2 - fw/2, 0, dh/2) \
               .tag_slot(1) \
               .select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')
        builder.create_box(fw, fd, dh) \
               .translate(dw/2 + fw/2, 0, dh/2) \
               .tag_slot(1) \
               .select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')
        # Header
        builder.create_box(dw + 2*fw, fd, fw) \
               .translate(0, 0, dh + fw/2) \
               .tag_slot(1) \
               .select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')

        # 2. Leaf Generation based on Style
        if self.door_style == 'GLASS':
            # Frame around glass
            frame_t = 0.05
            # Top/Bottom Rails
            builder.create_box(dw, lt, frame_t).translate(0, 0, frame_t/2).tag_slot(0).select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')
            builder.create_box(dw, lt, frame_t).translate(0, 0, dh - frame_t/2).tag_slot(0).select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')
            # Side Stiles
            builder.create_box(frame_t, lt, dh).translate(-dw/2 + frame_t/2, 0, dh/2).tag_slot(0).select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')
            builder.create_box(frame_t, lt, dh).translate(dw/2 - frame_t/2, 0, dh/2).tag_slot(0).select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')
            # Glass
            builder.create_box(dw - 2*frame_t, 0.02, dh - 2*frame_t).translate(0, 0, dh/2).tag_slot(3).tag_uvs(1.0, 'FIT')

        elif self.door_style == 'SCIFI':
            # Bulkhead Door (Octagonal-ish or Heavy)
            builder.create_box(dw, lt * 2, dh).translate(0, 0, dh/2).tag_slot(0).tag_uvs(1.0, 'BOX')

            # Inset Detail
            builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.1) \
                   .inset(0.15, depth=-0.05).tag_slot(1) \
                   .select_boundary().tag_edge_role(2).tag_uvs(1.0, 'BOX') # Sharp (inset edges)

            # Mark main leaf boundary
            builder.select_all_faces().select_faces_by_slot(0).select_boundary().tag_edge_role(1)

            # Add some heavy bolts/pads
            builder.create_box(0.2, lt*2.2, 0.4).translate(0, 0, dh/2).tag_slot(7).select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')

        else: # STANDARD
            # Stops
            stop_thick, stop_width = 0.02, 0.03
            stop_y_offset = lt/2 + stop_width/2
            builder.create_box(stop_thick, stop_width, dh).translate(-dw/2 + stop_thick/2, stop_y_offset, dh/2).tag_slot(1).select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')
            builder.create_box(stop_thick, stop_width, dh).translate(dw/2 - stop_thick/2, stop_y_offset, dh/2).tag_slot(1).select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')
            builder.create_box(dw, stop_width, stop_thick).translate(0, stop_y_offset, dh - stop_thick/2).tag_slot(1).select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')

            # Initial Leaf Box
            builder.create_box(dw, lt, dh).translate(0, 0, dh/2).tag_slot(0).tag_uvs(1.0, 'BOX')

            # Panels (Inset)
            leaf_faces = [f for f in builder.active_faces if abs(f.normal.y) > 0.9]
            builder.active_faces = leaf_faces
            if leaf_faces:
                builder.inset(0.1, relative=False).inset(0.03, depth=-0.015, relative=False) \
                       .select_boundary().tag_edge_role(2).tag_uvs(1.0, 'BOX') # Sharp inset

            # Mark main leaf boundary (Select by slot 0 to catch all leaf geometry)
            builder.select_all_faces().select_faces_by_slot(0).select_boundary().tag_edge_role(1)

        # 3. Hardware (Handle) - If not SCIFI (already added detail)
        if self.door_style != 'SCIFI':
            h_h = self.handle_height
            h_x = dw/2 - 0.1
            h_y = lt/2 + 0.005
            builder.create_box(0.12, 0.04, 0.02).translate(h_x, h_y + 0.02, h_h).tag_slot(7).select_boundary().tag_edge_role(1).tag_uvs(1.0, 'BOX')

        # 4. Rotation Logic (Common)
        if abs(self.open_angle) > 0.001:
            pivot = Vector((-dw/2, 0, 0))
            # Select Leaf components (0, 3, 7)
            target_verts = set()
            bm.verts.ensure_lookup_table()
            for f in bm.faces:
                if f.material_index in (0, 3, 7):
                    for v in f.verts: target_verts.add(v)

            if target_verts:
                builder.active_verts = list(target_verts)
                builder.translate(-pivot.x, -pivot.y, -pivot.z)
                builder.rotate(self.open_angle, 'Z')
                builder.translate(pivot.x, pivot.y, pivot.z)

        # 5. Sockets (Tag Existing Faces)
        builder.clean()

        # Front/Back Frame Faces
        builder.select_faces_by_normal(Vector((0, -1, 0)), tolerance=0.1).tag_socket(1)
        builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.1).tag_socket(2)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Dimensions", icon='MESH_CUBE')
        col = box.column(align=True)
        col.prop(self, "door_style")
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
