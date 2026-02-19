import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "URB_04: Jersey Barrier",
    "id": "urb_04_barrier",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbBarrier(Massa_OT_Base):
    bl_idname = "massa.gen_urb_04_barrier"
    bl_label = "URB Barrier"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=3.0, min=0.1)
    height: FloatProperty(name="Height", default=0.9, min=0.1)
    width_base: FloatProperty(name="Base Width", default=0.6, min=0.1)
    width_top: FloatProperty(name="Top Width", default=0.2, min=0.05)

    # Profile
    break_height: FloatProperty(name="Slope Break H", default=0.25, min=0.0) # Height of first slope
    break_width: FloatProperty(name="Slope Break W", default=0.4, min=0.1) # Width at break

    def get_slot_meta(self):
        return {
            0: {"name": "Concrete", "uv": "SKIP", "phys": "CONCRETE"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        l = self.length
        h = self.height
        wb = self.width_base
        wt = self.width_top
        bh = self.break_height
        bw = self.break_width

        # 2. Generate Profile (XZ Plane at Y=-l/2)
        # Symmetrical K-Rail profile
        # Points (Left half, then mirror? Or full loop)

        # 0: Base Left (-wb/2, 0)
        # 1: Break Left (-bw/2, bh)
        # 2: Top Left (-wt/2, h)
        # 3: Top Right (wt/2, h)
        # 4: Break Right (bw/2, bh)
        # 5: Base Right (wb/2, 0)
        # 6: Close loop to 0

        start_y = -l/2

        verts = [
            bm.verts.new(Vector((-wb/2, start_y, 0))),
            bm.verts.new(Vector((-bw/2, start_y, bh))),
            bm.verts.new(Vector((-wt/2, start_y, h))),
            bm.verts.new(Vector((wt/2, start_y, h))),
            bm.verts.new(Vector((bw/2, start_y, bh))),
            bm.verts.new(Vector((wb/2, start_y, 0)))
        ]

        # Create Face
        face_prof = bm.faces.new(verts)
        face_prof.material_index = 0

        # 3. Extrude along Y
        ret = bmesh.ops.extrude_face_region(bm, geom=[face_prof])
        verts_ext = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, l, 0)), verts=verts_ext)

        # 4. Interlocking Notches (Male/Female)
        # Male at Front (Y max), Female at Back (Y min)
        # Select Front Face (End Cap)
        # Extrude small protrusion? Or simplify.
        # Let's bevel the top edges or mark them.

        # Mark Top Ridges as Edge Slot 1
        # Edges between Top Face and Side Faces
        # Z approx h.
        for e in bm.edges:
            v1, v2 = e.verts
            if abs(v1.co.z - h) < 0.01 and abs(v2.co.z - h) < 0.01:
                # Top edges
                # Filter for longitudinal ones (Y diff)
                if abs(v1.co.y - v2.co.y) > 0.1:
                    e[edge_slots] = 1 # Perimeter/Sharp

        # 5. Sockets
        # Ends
        for f in bm.faces:
            n = f.normal
            if abs(n.y) > 0.9:
                f.material_index = 9 # Socket

        # 6. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)
        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue

            n = f.normal
            for l in f.loops:
                if abs(n.y) > 0.5: # Ends -> XZ
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
                elif abs(n.z) > 0.8: # Top/Bottom -> XY
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)
                else: # Slopes -> Project on YZ (Length vs Height)
                    # Length is Y. Height (slope) is hypotenuse.
                    # Simple box mapping:
                    if abs(n.x) > 0.5:
                        l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)
                    else:
                        l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale) # Fallback

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "height")
        col.prop(self, "width_base")
        col.prop(self, "width_top")
        layout.separator()
        col.prop(self, "break_height")
        col.prop(self, "break_width")
