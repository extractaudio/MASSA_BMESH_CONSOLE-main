import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

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
            0: {"name": "Door Leaf", "uv": "SKIP", "phys": "WOOD"},
            1: {"name": "Frame", "uv": "BOX", "phys": "WOOD"},
            7: {"name": "Hardware", "uv": "BOX", "phys": "METAL_BRASS"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()

        # 2. Frame (3-Sided Architrave)
        # Create U-Shape profile on XZ plane, extrude Y (Depth)

        fw = self.frame_width
        fd = self.frame_depth
        dw = self.door_width
        dh = self.door_height

        # Left Jamb
        bmesh.ops.create_cube(bm, size=1.0)
        # Scale to size: (fw, fd, dh + fw) # extend up to meet header?
        # Let's simplify: 3 boxes.

        # Left Post
        v_left = [
            Vector((-dw/2 - fw/2, -fd/2, 0)),
            Vector((-dw/2 + fw/2, -fd/2, 0)),
            Vector((-dw/2 + fw/2, fd/2, 0)),
            Vector((-dw/2 - fw/2, fd/2, 0)),
            Vector((-dw/2 - fw/2, -fd/2, dh + fw)),
            Vector((-dw/2 + fw/2, -fd/2, dh + fw)),
            Vector((-dw/2 + fw/2, fd/2, dh + fw)),
            Vector((-dw/2 - fw/2, fd/2, dh + fw))
        ]

        # Right Post
        v_right = [v.copy() for v in v_left]
        for v in v_right:
            v.x += (dw + fw) # Shift right by door width + frame width?
            # Current center is -dw/2. Right center should be +dw/2.
            # Shift by dw + fw? No, shift by dw + fw.
            # Left center X is -dw/2. Right center X is +dw/2. Delta is dw.
            # But frame is centered on -dw/2 - fw/2? No.
            pass

        # Let's build cleaner logic using bmesh primitives and transforms.

        # Clear init cube
        bm.clear()

        # Create Left Jamb
        res_L = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((fw, fd, dh + fw)), verts=res_L['verts'])
        bmesh.ops.translate(bm, vec=Vector((-dw/2 - fw/2, 0, (dh + fw)/2)), verts=res_L['verts'])

        # Create Right Jamb
        res_R = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((fw, fd, dh + fw)), verts=res_R['verts'])
        bmesh.ops.translate(bm, vec=Vector((dw/2 + fw/2, 0, (dh + fw)/2)), verts=res_R['verts'])

        # Create Header
        res_H = bmesh.ops.create_cube(bm, size=1.0)
        # Width spans total width + 2*fw? Or just between? Usually header sits on top.
        # Let's make header full width: dw + 2*fw
        bmesh.ops.scale(bm, vec=Vector((dw + 2*fw, fd, fw)), verts=res_H['verts'])
        bmesh.ops.translate(bm, vec=Vector((0, 0, dh + fw/2)), verts=res_H['verts'])

        # Set Frame Material
        for f in bm.faces:
            f.material_index = 1

        # 3. Door Leaf
        # Create Cube
        res_D = bmesh.ops.create_cube(bm, size=1.0)
        # Scale: (dw, leaf_thick, dh)
        lt = self.leaf_thick
        bmesh.ops.scale(bm, vec=Vector((dw, lt, dh)), verts=res_D['verts'])
        # Initial pos: Centered at (0, 0, dh/2).
        # Shift to fit inside frame. Usually flush with one side or centered.
        bmesh.ops.translate(bm, vec=Vector((0, 0, dh/2)), verts=res_D['verts'])

        # Apply Open Rotation
        # Pivot is Hinge Axis. Let's say Left Hinge (-dw/2, -lt/2?, 0)
        # Usually hinge is at side of door.
        pivot = Vector((-dw/2, 0, 0)) # Simple pivot at left edge center depth

        rot_mat = Matrix.Rotation(math.radians(self.open_angle), 3, 'Z')

        bmesh.ops.rotate(bm, cent=pivot, matrix=rot_mat, verts=res_D['verts'])

        # Set Door Material
        for v in res_D['verts']:
            for f in v.link_faces:
                f.material_index = 0

        # 4. Hardware (Handle)
        # Simple Cube/Cylinder attached to door leaf
        # Create Handle Geometry
        res_Hnd = bmesh.ops.create_cube(bm, size=1.0)
        # Scale small
        bmesh.ops.scale(bm, vec=Vector((0.05, 0.1, 0.02)), verts=res_Hnd['verts'])
        # Position relative to door leaf BEFORE rotation
        # Right side: (dw/2 - 0.1, lt/2 + 0.05, handle_height)
        handle_offset = Vector((dw/2 - 0.1, lt/2 + 0.05, self.handle_height))

        # Translate to handle position
        bmesh.ops.translate(bm, vec=handle_offset, verts=res_Hnd['verts'])

        # Rotate with door
        bmesh.ops.rotate(bm, cent=pivot, matrix=rot_mat, verts=res_Hnd['verts'])

        # Set Handle Material
        for v in res_Hnd['verts']:
            for f in v.link_faces:
                f.material_index = 7

        # 5. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)

        for f in bm.faces:
            mat_idx = f.material_index
            n = f.normal

            # Simple Box Mapping for all
            if abs(n.x) > 0.5:
                # Side -> YZ
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)
            elif abs(n.y) > 0.5:
                # Front -> XZ
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
            else:
                # Top -> XY
                for l in f.loops:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "door_width")
        col.prop(self, "door_height")
        col.prop(self, "frame_width")
        col.prop(self, "frame_depth")
        layout.separator()
        col.prop(self, "leaf_thick")
        col.prop(self, "open_angle")
        col.prop(self, "handle_height")
