import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "URB_01: Sidewalk",
    "id": "urb_01_sidewalk",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbSidewalk(Massa_OT_Base):
    bl_idname = "massa.gen_urb_01_sidewalk"
    bl_label = "URB Sidewalk"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=4.0, min=0.1)
    width: FloatProperty(name="Width", default=2.0, min=0.1)
    curb_height: FloatProperty(name="Curb Height", default=0.15, min=0.01)
    curb_width: FloatProperty(name="Curb Width", default=0.15, min=0.01)

    # Details
    joint_spacing: FloatProperty(name="Joint Spacing", default=2.0, min=0.1)
    paint_curb: BoolProperty(name="Paint Curb", default=False)

    def get_slot_meta(self):
        return {
            0: {"name": "Concrete", "uv": "SKIP", "phys": "CONCRETE"},
            6: {"name": "Paint Accent", "uv": "SKIP", "phys": "PAINT"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        l, w, ch, cw = self.length, self.width, self.curb_height, self.curb_width

        # 2. Profile Generation (L-Shape on XZ plane, Extrude Y)
        # Actually standard: Extrude along Y usually means Length is Y. Width is X.
        # Profile is in XZ plane.

        # Profile Points (Clockwise or CCW)
        # 1. Back/Top (Left): (-w/2, 0)
        # 2. Front/Top (Right before curb): (w/2 - cw, 0)
        # 3. Curb Top (Right): (w/2, 0) ? No, curb drops down or goes up?
        # Sidewalk is usually raised above street.
        # So "Curb Height" is the thickness of the slab visible from street.
        # Let's say Z=0 is the street level.
        # Sidewalk surface is at Z=ch.

        # Profile at Y = -l/2

        # Verts:
        # 0: Back Bottom (-w/2, 0) -> Z=0? Or is it a slab? Usually slab has thickness.
        # Let's assume slab thickness = ch.
        # 0: Back Bottom (-w/2, 0)
        # 1: Back Top (-w/2, ch)
        # 2: Curb Top Edge (w/2, ch) -> Wait, curb usually has a slope or radius.
        # Let's keep it simple: Square Curb.
        # 3: Curb Front Top (w/2, ch)
        # 4: Curb Front Bottom (w/2, 0)
        # 5: Bottom connects back to 0.

        # But wait, "Curb Strip" implies the curb is the edge.
        # Is the sidewalk the full width? Yes.

        # Create Profile Face
        v0 = bm.verts.new(Vector((-w/2, -l/2, 0)))
        v1 = bm.verts.new(Vector((-w/2, -l/2, ch)))
        v2 = bm.verts.new(Vector((w/2, -l/2, ch)))
        v3 = bm.verts.new(Vector((w/2, -l/2, 0)))

        face_profile = bm.faces.new((v0, v1, v2, v3))
        face_profile.material_index = 0

        # Extrude along Y (Length)
        ret = bmesh.ops.extrude_face_region(bm, geom=[face_profile])
        verts_extruded = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=Vector((0, l, 0)), verts=verts_extruded)

        # Delete End Caps? Usually keep them solid.

        # 3. Curb Paint
        # Select faces on the Curb (Right side, +X)
        # Top face near X max? No, usually curb face is vertical or top edge.
        # "Paint Accent" usually means Red Curb (No Parking).
        # Which faces? The vertical face at +X (Street side) and maybe top strip.
        if self.paint_curb:
            for f in bm.faces:
                n = f.normal
                c = f.calc_center_median()
                # Right Vertical Face
                if n.x > 0.9:
                    f.material_index = 6
                # Top Strip near edge?
                elif n.z > 0.9 and c.x > (w/2 - cw):
                    f.material_index = 6

        # 4. Expansion Joints (Bisect)
        # Cut every joint_spacing along Y
        # Range Y: -l/2 to l/2

        num_joints = int(l / self.joint_spacing)
        start_y = -l/2

        for i in range(1, num_joints + 1):
            y = start_y + i * self.joint_spacing
            if y >= l/2 - 0.01: continue

            # Bisect
            ret_bisect = bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:]+bm.verts[:], plane_co=Vector((0,y,0)), plane_no=Vector((0,1,0)))

            # Mark Edges created by bisect as Detail (4)
            # The edges in `geom_cut` (if returned) or we identify them.
            # bmesh.ops.bisect_plane returns `geom_cut` (edges and verts) and `geom` (faces split).
            # Wait, `geom_cut` contains the new geometry (edges along the cut).

            cut_edges = [e for e in ret_bisect['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
            for e in cut_edges:
                e[edge_slots] = 4 # Detail
                # Also mark as sharp? No, detail is soft bevel.

            # Optional: Bevel these edges physically? Mandate says "Mark ... for soft procedural bevels". So marking is enough.

        # 5. Sockets
        # Ends (Front/Back)
        for f in bm.faces:
            n = f.normal
            if abs(n.y) > 0.9:
                f.material_index = 9 # Socket Anchor

        # 6. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)

        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue

            n = f.normal
            for l in f.loops:
                if abs(n.x) > 0.5:
                    l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)
                elif abs(n.y) > 0.5:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
                else:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "curb_height")
        col.prop(self, "curb_width")
        layout.separator()
        col.prop(self, "joint_spacing")
        col.prop(self, "paint_curb")
