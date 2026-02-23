import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_02: HVAC Duct",
    "id": "ind_02_duct",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": True,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndDuct(Massa_OT_Base):
    bl_idname = "massa.gen_ind_02_duct"
    bl_label = "IND Duct"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=2.0, min=0.1)
    width: FloatProperty(name="Width", default=0.6, min=0.1)
    height: FloatProperty(name="Height", default=0.4, min=0.1)

    # Details
    segment_length: FloatProperty(name="Segment L", default=1.0, min=0.1)
    cross_break: FloatProperty(name="Cross Break", default=0.015, min=0.0) # Depth of X pattern
    flange_width: FloatProperty(name="Flange W", default=0.03, min=0.0)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Sheet Metal", "uv": "SKIP", "phys": "METAL_ALUMINUM"},
            2: {"name": "Flanges", "uv": "BOX", "phys": "METAL_STEEL"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")
        layout.separator()
        col.prop(self, "segment_length")
        col.prop(self, "cross_break")
        col.prop(self, "flange_width")

    def build_shape(self, bm):
        # Ensure Layers exist upfront to prevent pointer invalidation
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        l, w, h = self.length, self.width, self.height
        cb = self.cross_break
        fw = self.flange_width

        # Calculate segments
        segs = int(l / self.segment_length)
        if segs < 1: segs = 1
        seg_len = l / segs

        curr_x = -l/2

        for i in range(segs):
            cx = curr_x + seg_len/2

            # 1. Duct Body Segment
            builder.create_box(seg_len, w, h, center=Vector((cx, 0, 0)))
            builder.tag_slot(0)

            # Cross Break (Poke & Pull)
            if cb > 0:
                # Select Side faces (Normals Y and Z)
                # Filter active_faces
                side_faces = []
                for f in builder.active_faces:
                    # Not ends (Normal X)
                    if abs(f.normal.x) < 0.1:
                        side_faces.append(f)

                if side_faces:
                    ret_poke = bmesh.ops.poke(bm, faces=side_faces)
                    center_verts = [v for v in ret_poke['verts']]

                    # Pull centers inward
                    # Vector is -Normal * cb
                    # But each face has different normal.
                    # Center vert connects 4 faces.
                    # We can use the normal of original face? No it's gone.
                    # Use average normal of linked faces.

                    for v in center_verts:
                        avg_n = Vector((0,0,0))
                        for f in v.link_faces:
                            avg_n += f.normal
                        if avg_n.length > 0:
                            avg_n.normalize()

                        bmesh.ops.translate(bm, vec=avg_n * -cb, verts=[v])

                        # Tag edges as Detail (2)
                        for e in v.link_edges:
                            # Mark edge role
                            # We can't use builder.tag_edge_role easily on specific edges unless selected
                            # Manual tag
                            layer_edge = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
                            if not layer_edge:
                                layer_edge = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
                            e[layer_edge] = 2

            # 2. Flanges
            if fw > 0:
                flange_thick = 0.01
                # Left of segment
                # If i > 0, we might duplicate flanges?
                # Usually flanges are at connections.
                # Let's put flange at Start of this segment.
                # And at End of this segment?
                # If segments are joined, we'd have double flanges.
                # Usually duct segments are bolted. So yes, double flanges.

                # Left Flange
                builder.create_box(flange_thick, w + fw*2, h + fw*2, center=Vector((curr_x, 0, 0)))
                builder.tag_slot(2) # Flange Material
                builder.select_boundary().tag_edge_role(1)

                # Right Flange
                builder.create_box(flange_thick, w + fw*2, h + fw*2, center=Vector((curr_x + seg_len, 0, 0)))
                builder.tag_slot(2)
                builder.select_boundary().tag_edge_role(1)

            curr_x += seg_len

        # 3. Clean
        # builder.clean() # Merge segments?
        # If we merge, we lose the seam between segments which might be desired detail.
        # But for "Solid" geometry, maybe we want one mesh?
        # Ducts are usually separate segments.
        # I will SKIP clean to preserve segment detail (flanges etc).

        builder._update()

        # 4. Sockets
        # Tag faces at ends (-L/2 and +L/2)
        # If flanges exist, these are the flange outer faces.
        # If not, these are the duct body ends.

        # Left End (-L/2)
        builder.select_faces_by_normal(Vector((-1, 0, 0)), tolerance=0.1)
        # Filter by position to ensure we pick the outermost face
        # Centered at -L/2
        target_x = -l/2
        final_faces = []
        for f in builder.active_faces:
            c = f.calc_center_median()
            if abs(c.x - target_x) < 0.05:
                final_faces.append(f)

        # Manually update active faces and tag
        builder.active_faces = final_faces
        builder.tag_socket(9).tag_slot(9)

        # Right End (+L/2)
        builder.select_faces_by_normal(Vector((1, 0, 0)), tolerance=0.1)
        target_x = l/2
        final_faces = []
        for f in builder.active_faces:
            c = f.calc_center_median()
            if abs(c.x - target_x) < 0.05:
                final_faces.append(f)

        builder.active_faces = final_faces
        builder.tag_socket(9).tag_slot(9)

        # 5. Manual UVs
        # Apply Box Mapping to everything EXCEPT Socket 9 (Slot 9)
        # builder.tag_uvs applies to active selection.

        # Select all non-socket faces
        all_valid_faces = [f for f in bm.faces if f.material_index != 9]
        builder.active_faces = all_valid_faces
        builder.tag_uvs(scale=self.uv_scale, projection='BOX')

