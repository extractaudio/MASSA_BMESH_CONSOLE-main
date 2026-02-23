import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

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

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            3: {"name": "Glass", "uv": "SKIP", "phys": "GLASS"}, # Mandate: Manual UV Fit
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # Ensure Layers exist
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        # 1. Create Base Grid
        # Create on XY (size 1), rotate to XZ, scale
        builder.create_grid(x_segments=self.mullion_x, y_segments=self.mullion_y, size=1.0) \
               .rotate(90, axis='X') \
               .scale(self.win_width, 1.0, self.win_height) \
               .translate(0, 0, self.win_height/2) \
               .tag_slot(3) # Initial faces are Glass

        # 2. Inset to create Frame
        # Inset active faces (Glass). Result active faces are the inner Glass faces.
        # Original faces (Frame + Glass area) are split.
        # We need to select the Frame (Outer Rim).
        
        # Track Glass faces
        glass_faces_before = set(builder.active_faces) # Actually this is all faces
        
        builder.inset(self.frame_width/2, relative=False)
        
        glass_faces_after = set(builder.active_faces)

        # Frame faces are faces that are NOT in glass_faces_after
        # But wait, create_grid creates faces. inset modifies them?
        # inset_individual usually REPLACES faces or modifies them.
        # If I want to find the frame faces, they are the faces adjacent to glass but not glass?
        # Or I can just select everything and subtract glass.

        all_faces = set(bm.faces)
        frame_faces = list(all_faces - glass_faces_after)

        builder.active_faces = frame_faces
        builder.tag_slot(0) # Frame

        # 3. Extrude Frame
        # Extrude Frame Backward (-Y) or Forward?
        # Window frame usually protrudes or glass is recessed.
        # Let's extrude Frame +Y (Forward) and -Y (Back)?
        # Or just extrude it out.
        # Original logic: Extrude -Y (Backwards).

        builder.extrude(self.mullion_thick, axis=Vector((0, -1, 0)))

        # 4. Sockets
        # Center of window: (0, 0, win_height/2)
        # Add Socket Geometry
        c = Vector((0, 0, self.win_height/2))
        sz = 0.2
        v1 = bm.verts.new(c + Vector((-sz, 0, -sz)))
        v2 = bm.verts.new(c + Vector((sz, 0, -sz)))
        v3 = bm.verts.new(c + Vector((sz, 0, sz)))
        v4 = bm.verts.new(c + Vector((-sz, 0, sz)))
        f_sock = bm.faces.new((v1, v2, v3, v4))
        f_sock.material_index = 9
        f_sock.normal_update()

        # 5. Manual UVs
        self.apply_manual_uvs(bm)

    def apply_manual_uvs(self, bm):
        uv_layer = bm.loops.layers.uv.verify()
        scale = getattr(self, "uv_scale_0", 1.0)

        bm.faces.ensure_lookup_table()
        for f in bm.faces:
            # if f.material_index == 9: continue # Pass audit

            mat_idx = f.material_index

            if mat_idx == 3: # Glass (Fit UVs)
                 # Find Bounds
                min_x = min(v.co.x for v in f.verts)
                max_x = max(v.co.x for v in f.verts)
                min_z = min(v.co.z for v in f.verts)
                max_z = max(v.co.z for v in f.verts)

                w = max_x - min_x
                h = max_z - min_z

                for l in f.loops:
                    u = (l.vert.co.x - min_x) / w if w > 0.001 else 0
                    v = (l.vert.co.z - min_z) / h if h > 0.001 else 0
                    l[uv_layer].uv = (u, v)

            else: # Frame, Socket (Box Map)
                n = f.normal
                for l in f.loops:
                    v = l.vert.co
                    if abs(n.x) > 0.5:
                        l[uv_layer].uv = (v.y * scale, v.z * scale)
                    elif abs(n.z) > 0.5:
                        l[uv_layer].uv = (v.x * scale, v.y * scale)
                    else: # Y
                        l[uv_layer].uv = (v.x * scale, v.z * scale)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Configuration", icon='MESH_GRID')
        col = box.column(align=True)
        col.prop(self, "win_width")
        col.prop(self, "win_height")

        box_grid = layout.box()
        box_grid.label(text="Grid & Frame", icon='MOD_WIREFRAME')
        col = box_grid.column(align=True)
        col.prop(self, "mullion_x")
        col.prop(self, "mullion_y")
        col.prop(self, "frame_width")
        col.prop(self, "mullion_thick")
