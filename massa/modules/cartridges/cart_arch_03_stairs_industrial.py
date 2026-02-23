import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "Industrial Stairs",
    "id": "arch_03_stairs_industrial",
    "icon": "MESH_STAIRS",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "FIX_DEGENERATE": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArchStairsIndustrial(Massa_OT_Base):
    bl_idname = "massa.gen_arch_03_stairs_industrial"
    bl_label = "Industrial Stairs"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    stair_width: FloatProperty(name="Width", default=1.2, min=0.5)
    stair_height: FloatProperty(name="Height", default=3.0, min=0.5)
    stair_run: FloatProperty(name="Run Length", default=4.0, min=0.5)
    step_count: IntProperty(name="Steps", default=12, min=2)

    # Details
    channel_width: FloatProperty(name="Channel Width", default=0.05, min=0.01)
    channel_height: FloatProperty(name="Channel Height", default=0.25, min=0.1)
    tread_thick: FloatProperty(name="Tread Thickness", default=0.05, min=0.01)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "UNWRAP", "phys": "METAL_STEEL"}, # Stringers
            1: {"name": "Grate", "uv": "UNWRAP", "phys": "METAL_GRATE"}, # Tread Top
            2: {"name": "Nosing", "uv": "UNWRAP", "phys": "RUBBER"},    # Tread Front
            3: {"name": "Warning", "uv": "UNWRAP", "phys": "PAINT"},    # Safety Yellow
            4: {"name": "Scaffold", "uv": "UNWRAP", "phys": "METAL_ALUM"},
            8: {"name": "Anchor Bottom", "uv": "SKIP", "phys": "GENERIC", "sock": True},
            9: {"name": "Anchor Top", "uv": "SKIP", "phys": "GENERIC", "sock": True},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions", icon="FIXED_SIZE")
        col.prop(self, "stair_width")
        col.prop(self, "stair_height")
        col.prop(self, "stair_run")
        col.prop(self, "step_count")

        col.separator()
        col.label(text="Details", icon="MESH_DATA")
        col.prop(self, "channel_width")
        col.prop(self, "channel_height")
        col.prop(self, "tread_thick")

        # Info
        rise = self.stair_height / max(1, self.step_count)
        run = self.stair_run / max(1, self.step_count)
        col.label(text=f"Rise: {rise:.2f}m | Run: {run:.2f}m", icon="INFO")

    def build_shape(self, bm: bmesh.types.BMesh):
        builder = MassaBuilder(bm)

        w = self.stair_width
        h = self.stair_height
        l = self.stair_run
        count = max(1, self.step_count)

        rise = h / count
        run = l / count

        # 1. STRINGERS (C-Channels)
        # We construct them flat then rotate pitch.
        stair_len = math.sqrt(l**2 + h**2)
        pitch = math.atan2(h, l)

        cw = self.channel_width
        ch = self.channel_height
        flange_t = 0.01

        # Build 2 Stringers
        for side in [-1, 1]:
            # Center X pos
            cx = side * (w/2 - cw/2)

            # Construct C-Channel parts aligned to Y (length)
            # Web (Vertical side)
            # Create box at origin, move to side
            builder.create_box(flange_t, stair_len, ch) \
                   .translate(side * (cw/2 - flange_t/2), 0, 0) # Offset relative to stringer center

            # Flanges (Top/Bottom)
            # Top
            builder.create_box(cw, stair_len, flange_t) \
                   .translate(0, 0, ch/2 - flange_t/2)
            # Bottom
            builder.create_box(cw, stair_len, flange_t) \
                   .translate(0, 0, -ch/2 + flange_t/2)

            # Combine parts into stringer selection (active_faces updated by last call)
            # We need to rotate ALL parts just created.
            # Best way: Group them? Or apply transform to last 3 creations.
            # MassaBuilder accumulates selection? No, create_box REPLACES selection.
            # So we must transform each part immediately or select all slot-0 faces?
            # Or build the whole stringer at origin then move/rotate.

            # Let's fix the logic:
            # The builder methods operate on active selection.
            # But I need to rotate the composite object.

            # Alternative: Calculate transformations first.
            rot_mat = Matrix.Rotation(pitch, 4, 'X')

            # Re-do with correct transform immediately
            # Web
            builder.create_box(flange_t, stair_len, ch) \
                   .translate(side * (cw/2 - flange_t/2), 0, 0) \
                   .transform(rot_mat) \
                   .translate(cx, l/2, h/2) \
                   .tag_slot(0).select_boundary().tag_edge_role(1)

            # Top Flange
            builder.create_box(cw, stair_len, flange_t) \
                   .translate(0, 0, ch/2 - flange_t/2) \
                   .transform(rot_mat) \
                   .translate(cx, l/2, h/2) \
                   .tag_slot(0).select_boundary().tag_edge_role(1)

            # Bottom Flange
            builder.create_box(cw, stair_len, flange_t) \
                   .translate(0, 0, -ch/2 + flange_t/2) \
                   .transform(rot_mat) \
                   .translate(cx, l/2, h/2) \
                   .tag_slot(0).select_boundary().tag_edge_role(1)

        # 2. TREADS
        tread_w = w - (cw * 2) - 0.02
        tread_d = run + 0.05 # Overlap
        tt = self.tread_thick

        for i in range(count):
            y_pos = (i + 1) * run - (run / 2)
            z_pos = (i + 1) * rise

            # Create Tread Box
            builder.create_box(tread_w, tread_d, tt) \
                   .translate(0, y_pos, z_pos) \
                   .tag_slot(0) # Default Frame

            # Tag Top Face as Grate (Slot 1)
            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1) \
                   .tag_slot(1).select_boundary().tag_edge_role(1)

            # Tag Front Face as Nosing/Warning (Slot 3)
            # Front face points -Y (steps go up +Y/+Z?)
            # Wait, run goes 0 to L (Y). Front face points -Y.
            # Original code said: if abs(f.normal.y) > 0.9: material 3
            builder.select_faces_by_normal(Vector((0, -1, 0)), tolerance=0.1) \
                   .tag_slot(3).select_boundary().tag_edge_role(1)

            # Tag Back Face (Slot 3 too?)
            builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.1) \
                   .tag_slot(3).select_boundary().tag_edge_role(1)

        # 3. CLEANUP & SOCKETS
        builder.clean()

        # Anchors
        # Bottom: 0,0,0
        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.1).tag_socket(8)

        # Top: 0, L, H
        # Find faces near top? Or just select faces at ends of stringers.
        # Stringer ends are angled.
        # Let's try to tag faces with normal ~ Y (end of stringer)
        builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.1).tag_socket(9)

