import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "ARC_05: Arch Column",
    "id": "arc_05_column",
    "icon": "MOD_BUILD",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_ArcColumn(Massa_OT_Base):
    bl_idname = "massa.gen_arc_05_column"
    bl_label = "ARC Column"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    total_height: FloatProperty(name="Height", default=4.0, min=0.1)
    radius_base: FloatProperty(name="Base Radius", default=0.4, min=0.1)
    radius_top: FloatProperty(name="Top Radius", default=0.3, min=0.1)
    segments: IntProperty(name="Segments", default=16, min=4)

    # Details
    plinth_height: FloatProperty(name="Plinth H", default=0.3, min=0.0)
    capital_height: FloatProperty(name="Capital H", default=0.4, min=0.0)

    fluted: BoolProperty(name="Fluted Shaft", default=False)
    flute_depth: FloatProperty(name="Flute Depth", default=0.02, min=0.001)

    def get_slot_meta(self):
        return {
            0: {"name": "Stone", "uv": "CYLINDER", "phys": "STONE"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        builder = MassaBuilder(bm)

        th = self.total_height
        ph = self.plinth_height
        ch = self.capital_height

        # Even segments for grid fill
        segs = self.segments if self.segments % 2 == 0 else self.segments + 1

        shaft_top_z = max(ph, th - ch)

        r_base = self.radius_base
        r_top = self.radius_top
        r_cap = r_base * 1.2

        levels = [
            (0.0, r_base),          # 0: Bottom
            (ph, r_base),           # 1: Plinth Top
            (shaft_top_z, r_top),   # 2: Shaft Top
            (th, r_cap)             # 3: Top
        ]

        loops = []

        # Create Rings (Verts & Edges)
        for z, r in levels:
            ring_verts = []
            # Create verts
            for i in range(segs):
                angle = (i / segs) * 2 * math.pi
                x = r * math.cos(angle)
                y = r * math.sin(angle)
                v = bm.verts.new(Vector((x, y, z)))
                ring_verts.append(v)

            # Create edges for the ring (to allow bridge/grid_fill)
            ring_edges = []
            bm.verts.ensure_lookup_table()
            for i in range(segs):
                v1 = ring_verts[i]
                v2 = ring_verts[(i+1)%segs]
                e = bm.edges.new((v1, v2))
                ring_edges.append(e)

            loops.append(ring_edges)

        bm.edges.ensure_lookup_table()

        # Skinning (Bridge Loops)
        # 0 -> 1 (Plinth)
        bmesh.ops.bridge_loops(bm, edges=loops[0] + loops[1])

        # 1 -> 2 (Shaft)
        ret = bmesh.ops.bridge_loops(bm, edges=loops[1] + loops[2])
        shaft_faces = ret['faces']

        # 2 -> 3 (Capital)
        bmesh.ops.bridge_loops(bm, edges=loops[2] + loops[3])

        # Caps (Grid Fill)
        try:
            bmesh.ops.grid_fill(bm, edges=loops[0])
        except:
            pass # Fallback to open or manual face if needed

        try:
            bmesh.ops.grid_fill(bm, edges=loops[3])
        except:
            pass

        # Fluting
        if self.fluted:
            # Inset alternate faces of shaft
            flute_faces = [f for i, f in enumerate(shaft_faces) if i % 2 == 0]
            if flute_faces:
                builder.active_faces = flute_faces
                builder.inset(0.01, depth=-self.flute_depth, relative=False)

        # Sockets
        # Bottom
        builder.create_grid(size=0.1) \
               .rotate(90, 'X') \
               .translate(0, -0.1, 0) \
               .tag_slot(9) \
               .tag_socket(1)

        # Top
        builder.create_grid(size=0.1) \
               .rotate(90, 'X') \
               .translate(0, 0, th + 0.1) \
               .tag_slot(9) \
               .tag_socket(2)

        # Finalize
        builder.select_all_faces() \
               .tag_slot(0) \
               .tag_uvs(getattr(self, 'uv_scale_0', 1.0), 'CYLINDER')

        # Fix socket slot (overwritten by select_all_faces tag_slot(0))
        # We need to re-tag sockets?
        # Sockets are created AFTER shaft, but select_all_faces selects everything.
        # Actually, create_grid updates active_faces.
        # But select_all_faces overwrites active_faces.
        # So tag_slot(0) applies to EVERYTHING.
        # We must re-apply socket slot.

        # Better: Tag slot 0 explicitly on shaft/plinth/cap faces?
        # Or just re-tag sockets.
        # Sockets are the last created grids.
        # We can find them by tag_socket? No, tag_socket sets data layer.
        # We can just iterate faces and check socket layer.

        sock_layer = bm.faces.layers.int.get("MASSA_SOCKETS")
        if sock_layer:
            for f in bm.faces:
                if f[sock_layer] > 0:
                    f.material_index = 9

        builder.clean()

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "total_height")
        col.prop(self, "radius_base")
        col.prop(self, "radius_top")
        col.prop(self, "segments")
        layout.separator()
        col.prop(self, "plinth_height")
        col.prop(self, "capital_height")
        layout.separator()
        col.prop(self, "fluted")
        if self.fluted:
            col.prop(self, "flute_depth")
