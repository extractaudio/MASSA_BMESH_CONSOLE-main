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
            0: {"name": "Door Leaf", "uv": "SKIP", "phys": "WOOD"},
            1: {"name": "Frame", "uv": "BOX", "phys": "WOOD"},
            7: {"name": "Hardware", "uv": "BOX", "phys": "METAL_BRASS"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # Ensure Layers exist
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        fw = self.frame_width
        fd = self.frame_depth
        dw = self.door_width
        dh = self.door_height
        lt = self.leaf_thick

        # 1. Frame
        # Left Jamb
        builder.create_box(fw, fd, dh + fw) \
               .translate(-dw/2 - fw/2, 0, (dh + fw)/2) \
               .tag_slot(1)
        
        # Right Jamb
        builder.create_box(fw, fd, dh + fw) \
               .translate(dw/2 + fw/2, 0, (dh + fw)/2) \
               .tag_slot(1)

        # Header
        builder.create_box(dw + 2*fw, fd, fw) \
               .translate(0, 0, dh + fw/2) \
               .tag_slot(1)

        # Stops
        stop_thick = 0.02
        stop_width = 0.03
        
        # Left Stop
        builder.create_box(stop_thick, stop_width, dh) \
               .translate(-dw/2 + stop_thick/2, lt/2 + stop_width/2, dh/2) \
               .tag_slot(1)

        # Right Stop
        builder.create_box(stop_thick, stop_width, dh) \
               .translate(dw/2 - stop_thick/2, lt/2 + stop_width/2, dh/2) \
               .tag_slot(1)

        # Header Stop
        builder.create_box(dw, stop_width, stop_thick) \
               .translate(0, lt/2 + stop_width/2, dh - stop_thick/2) \
               .tag_slot(1)

        # 2. Door Leaf
        # Create separate object logic or just create box
        builder.create_box(dw, lt, dh) \
               .translate(0, 0, dh/2) \
               .tag_slot(0) # Leaf
        
        # Detail: Panels
        # Select Front/Back of the leaf we just created
        # They are at Y = +/- lt/2. Normal Y.
        # We can select by slot 0 and normal Y
        builder.select_faces_by_slot(0)
        leaf_faces = [f for f in builder.active_faces if abs(f.normal.y) > 0.9]
        builder.active_faces = leaf_faces
        
        # Inset for Rail/Stile (0.1)
        builder.inset(0.1, relative=False)
        
        # Inset for Panel Recess (0.03 thick, depth -0.015)
        builder.inset(0.03, depth=-0.015, relative=False)
        
        # 3. Hardware
        plate_y = lt/2 + 0.005
        
        # Plate
        builder.create_box(0.06, 0.01, 0.2) \
               .translate(dw/2 - 0.1, plate_y, self.handle_height) \
               .tag_slot(7) # Hardware
        
        # Handle
        handle_pos = Vector((dw/2 - 0.1, plate_y, self.handle_height))
        builder.create_box(0.12, 0.02, 0.02) \
               .translate(handle_pos.x - 0.03, handle_pos.y + 0.03, handle_pos.z) \
               .tag_slot(7)

        # 4. Opening Rotation
        if abs(self.open_angle) > 0.001:
            pivot = Vector((-dw/2, 0, 0))
            
            # Select Leaf and Hardware (Slots 0 and 7)
            # We iterate all verts and check if they belong to faces with these slots
            target_verts = set()
            bm.verts.ensure_lookup_table()
            for v in bm.verts:
                for f in v.link_faces:
                    if f.material_index in (0, 7):
                        target_verts.add(v)

            if target_verts:
                builder.active_verts = list(target_verts)
                builder.active_faces = [] # Clear faces logic to force vert transform
                
                # Pivot Rotate: Translate -> Rotate -> Untranslate
                builder.translate(-pivot.x, -pivot.y, -pivot.z) \
                       .rotate(self.open_angle, axis='Z') \
                       .translate(pivot.x, pivot.y, pivot.z)

        # 5. Sockets
        # Center bottom (0, 0, 0)
        c = Vector((0, 0, 0))
        sz = 0.2
        v1 = bm.verts.new(c + Vector((-sz, 0, 0)))
        v2 = bm.verts.new(c + Vector((sz, 0, 0)))
        v3 = bm.verts.new(c + Vector((sz, 0, sz*2)))
        v4 = bm.verts.new(c + Vector((-sz, 0, sz*2)))
        f_sock = bm.faces.new((v1, v2, v3, v4))
        f_sock.material_index = 9
        f_sock.normal_update()

        # 6. Manual UVs
        self.apply_manual_uvs(bm)

    def apply_manual_uvs(self, bm):
        uv_layer = bm.loops.layers.uv.verify()
        scale = getattr(self, "uv_scale_0", 1.0)

        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            # if f.material_index == 9: continue # Pass audit
            
            n = f.normal
            # Box Map
            for l in f.loops:
                v = l.vert.co
                if abs(n.x) > 0.5:
                    l[uv_layer].uv = (v.y * scale, v.z * scale)
                elif abs(n.z) > 0.5:
                    l[uv_layer].uv = (v.x * scale, v.y * scale)
                else:
                    l[uv_layer].uv = (v.x * scale, v.z * scale)

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
