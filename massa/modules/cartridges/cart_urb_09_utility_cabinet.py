import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_09: Utility Cabinet",
    "id": "urb_09_utility_cabinet",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbUtilityCabinet(Massa_OT_Base):
    bl_idname = "massa.gen_urb_09_utility_cabinet"
    bl_label = "URB Utility Cabinet"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    width: FloatProperty(name="Width", default=1.2, min=0.5)
    depth: FloatProperty(name="Depth", default=0.8, min=0.4)
    height: FloatProperty(name="Height", default=1.8, min=1.0)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("TRAFFIC", "Traffic", "Controller Box on Base"),
            ("TELECOM", "Telecom", "Vertical Ribs"),
            ("ELECTRICAL", "Electrical", "Plain with Vents"),
        ],
        default="TRAFFIC"
    )

    # Details
    base_height: FloatProperty(name="Base Height", default=0.2, min=0.0)
    door_inset: FloatProperty(name="Door Inset", default=0.02, min=0.0)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Cabinet Body", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            1: {"name": "Vents / Base", "uv": "BOX", "phys": "CONCRETE_RAW"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "MASSA_DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")
        layout.separator()
        col.prop(self, "base_height")
        col.prop(self, "door_inset")

    def build_shape(self, bm):
        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        w = self.width
        d = self.depth
        h = self.height
        bh = self.base_height

        if self.style == 'TRAFFIC':
            # Concrete Base + Metal Box

            # Base
            if bh > 0:
                builder.create_box(w, d, bh, center=Vector((0,0,bh/2))) \
                       .tag_slot(1) # Concrete

            # Cabinet
            cab_h = h - bh
            builder.create_box(w, d, cab_h, center=Vector((0,0,bh + cab_h/2))) \
                   .tag_slot(0) # Metal

            # Doors (Front)
            # Select Front Face (Y-)
            builder.select_faces_by_normal(Vector((0,-1,0)), tolerance=0.1)
            # Filter by height to pick cabinet face, not base
            builder.active_faces = [f for f in builder.active_faces if f.calc_center_median().z > bh]

            # Inset for Door
            builder.inset(amount=0.05, depth=-self.door_inset)
            # Split door? Usually double doors.
            # Bisect active face vertically (X=0)
            bmesh.ops.bisect_plane(bm, geom=builder.active_faces + builder.active_edges + builder.active_verts,
                                   plane_co=Vector((0,0,0)), plane_no=Vector((1,0,0)))
            # Inset each door slightly
            # Need to re-select doors
            builder.select_faces_by_normal(Vector((0,-1,0)), tolerance=0.1)
            builder.active_faces = [f for f in builder.active_faces if f.calc_center_median().z > bh and f.calc_area() < (w*cab_h*0.4)]
            builder.inset(amount=0.02, depth=0.0)

        elif self.style == 'TELECOM':
            # Ribbed Box
            builder.create_box(w, d, h, center=Vector((0,0,h/2))) \
                   .tag_slot(0)

            # Ribs on Sides
            # Bisect sides? Or just texture.
            # Let's add Vents (Slot 1)
            # Side Vents (Left/Right)
            for x_dir in [-1, 1]:
                builder.select_faces_by_normal(Vector((x_dir,0,0)), tolerance=0.1)
                builder.inset(amount=0.1, depth=-0.02)
                builder.tag_slot(1) # Vent Material

        elif self.style == 'ELECTRICAL':
            # Plain box with warning signs
            builder.create_box(w, d, h, center=Vector((0,0,h/2))) \
                   .tag_slot(0)

            # Base plinth
            # Maybe chamfer top

            # Front Panel
            builder.select_faces_by_normal(Vector((0,-1,0)), tolerance=0.1)
            builder.inset(amount=0.05, depth=0.01)

            # Vents on Top of Sides
            # Bisect top part of side faces
            # Hard to select sub-region without cutting.
            pass

        # 4. Sockets
        # Anchor (Bottom)
        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.1)
        # Filter Z ~ 0
        builder.active_faces = [f for f in builder.active_faces if -0.1 <= f.calc_center_median().z <= 0.1]

        if not builder.active_faces:
             builder.select_faces_by_height(min_z=-0.1, max_z=0.1)

        builder.tag_socket(9).tag_slot(9) # Anchor

        # 5. UVs
        builder.select_all_faces() \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Cleanup
        builder._update()
