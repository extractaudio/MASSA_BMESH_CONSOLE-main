import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ARC_03: Curtain Wall",
    "id": "arc_03_window",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcWindow(Massa_OT_Base):
    bl_idname = "massa.gen_arc_03_window"
    bl_label = "ARC Window"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    win_width: FloatProperty(name="Width", default=2.0, min=0.1)
    win_height: FloatProperty(name="Height", default=2.5, min=0.1)

    # Grid
    mullion_x: IntProperty(name="Mullion X", default=2, min=1)
    mullion_y: IntProperty(name="Mullion Y", default=3, min=1)
    frame_width: FloatProperty(name="Frame Width", default=0.1, min=0.01)
    mullion_thick: FloatProperty(name="Frame Depth", default=0.1, min=0.01)

    # === REDO-PANEL SAFE UI ELEMENTS ===
    massa_hide_ui: bpy.props.BoolProperty(name="Hide UI (Redo Trap)", default=False)
    massa_scene_proxy: bpy.props.StringProperty(name="Scene Proxy", default="null")


    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            3: {"name": "Glass", "uv": "SKIP", "phys": "GLASS"}, # Mandate: Manual UV Fit
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # 2. Create Grid of Faces
        bmesh.ops.create_grid(bm, x_segments=self.mullion_x, y_segments=self.mullion_y, size=1)
        
        # Scale to size
        bmesh.ops.scale(bm, vec=Vector((self.win_width, self.win_height, 1)), verts=bm.verts)
        
        # Rotate to upright (facing Y-)
        bmesh.ops.rotate(bm, cent=Vector((0,0,0)), matrix=Matrix.Rotation(math.radians(90), 3, 'X'), verts=bm.verts)
        
        # Translate to sit on Z=0
        bmesh.ops.translate(bm, vec=Vector((0, 0, self.win_height/2)), verts=bm.verts)

        # 3. Create Frames via Inset
        original_faces = bm.faces[:]
        for f in original_faces:
            f.material_index = 3  # Set all original faces to glass (3)

        # Inset individual to create the frame outer rim (thickness is half because it's double on shared edges)
        ret = bmesh.ops.inset_individual(bm, faces=original_faces, thickness=self.frame_width/2.0, use_even_offset=True)

        # 4. Separate Frame and Glass
        # bmesh inset_individual modifies original faces to be the inner faces
        glass_faces = set(original_faces)
        frame_faces = [f for f in bm.faces if f not in glass_faces]

        for f in frame_faces:
            f.material_index = 0  # Frame (0)

        # 5. Extrude Frame
        # Extrude the frame faces backward (-Y) to give them depth
        ret = bmesh.ops.extrude_face_region(bm, geom=frame_faces)
        verts_to_move = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, -self.mullion_thick, 0)), verts=verts_to_move)

        # 6. Manual UVs
        for f in bm.faces:
            mat_idx = f.material_index

            if mat_idx == 3: # Glass
                # Bounds of this face
                min_x = min(v.co.x for v in f.verts)
                max_x = max(v.co.x for v in f.verts)
                min_z = min(v.co.z for v in f.verts)
                max_z = max(v.co.z for v in f.verts)

                w = max_x - min_x
                h = max_z - min_z

                for l in f.loops:
                    u = (l.vert.co.x - min_x) / w if w > 0 else 0
                    v = (l.vert.co.z - min_z) / h if h > 0 else 0
                    l[uv_layer].uv = (u, v)

            elif mat_idx == 0: # Frame
                # Box mapping
                scale = getattr(self, "uv_scale_0", 1.0)
                n = f.normal
                for l in f.loops:
                    # Simple box projection
                    if abs(n.x) > 0.5:
                        l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)
                    elif abs(n.z) > 0.5:
                        l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)
                    else:
                        l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)

    def draw_shape_ui(self, layout):
        if self.massa_hide_ui:
            layout.label(text="UI Hidden (Redo Trap)", icon='ERROR')
            layout.prop(self, "massa_hide_ui", toggle=True, text="Show UI", icon='RESTRICT_VIEW_OFF')
            return

        box = layout.box()
        row = box.row()
        row.prop(self, "massa_hide_ui", text="Lock UI", icon='LOCKED')
        row.label(text="Window Configuration")
        
        col = layout.column(align=True)
        col.prop(self, "win_width")
        col.prop(self, "win_height")
        layout.separator()
        col.prop(self, "mullion_x")
        col.prop(self, "mullion_y")
        col.prop(self, "frame_width")
        col.prop(self, "mullion_thick")
