import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_13: Dumpster",
    "id": "urb_13_dumpster",
    "icon": "MOD_FLUID",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbDumpster(Massa_OT_Base):
    bl_idname = "massa.gen_urb_13_dumpster"
    bl_label = "URB Dumpster"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    width: FloatProperty(name="Width", default=2.0, min=1.0)
    depth: FloatProperty(name="Depth", default=1.5, min=1.0)
    height: FloatProperty(name="Height", default=1.2, min=0.5)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("FRONT_LOAD", "Front Load", "Standard Commercial"),
            ("ROLL_OFF", "Roll Off", "Construction Skip"),
            ("RECYCLE", "Recycle Bin", "Public Collection"),
        ],
        default="FRONT_LOAD"
    )

    # Details
    lid_open: FloatProperty(name="Lid Open", default=0.0, min=0.0, max=1.0)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Body", "uv": "BOX", "phys": "METAL_RUST"},
            1: {"name": "Lid/Plastic", "uv": "BOX", "phys": "PLASTIC_HARD"},
            2: {"name": "Detail", "uv": "BOX", "phys": "METAL_DARK"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")
        layout.separator()
        col.prop(self, "lid_open")

    def build_shape(self, bm):
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        w = self.width
        d = self.depth
        h = self.height

        # 1. Base Geometry
        # Center Z at h/2
        builder.create_box(w, d, h, center=Vector((0, 0, h/2)))
        builder.tag_slot(0) # Body
        builder.select_all_faces().tag_edge_role(1)

        # 2. Style Logic
        if self.style == 'FRONT_LOAD':
            # Plane defined by:
            # Point at (0, -d/2, h*0.8) (Lower Front)
            # Point at (0, d/2, h) (Full Height Back)

            p1 = Vector((0, -d/2, h*0.8))
            p2 = Vector((0, d/2, h))
            vec = p2 - p1
            normal = Vector((1,0,0)).cross(vec).normalized()

            # Bisect and remove top
            bmesh.ops.bisect_plane(
                bm,
                geom=bm.faces[:]+bm.edges[:]+bm.verts[:],
                dist=0.001,
                plane_co=p1,
                plane_no=normal,
                clear_outer=True # Remove the part above
            )

            # Hollow out
            builder.select_faces_by_normal(normal, tolerance=0.1) \
                   .inset(0.05) \
                   .extrude(-h*0.8) \
                   .tag_slot(0) \
                   .tag_edge_role(1) # Interior

            # Rim/Lid area
            # Re-select the top rim (which was created by inset)
            # It faces 'normal'
            # Filter by area or something?
            # Or just use the fact it's on the plane
            builder.select_faces_by_normal(normal, tolerance=0.1).tag_slot(1)

        elif self.style == 'ROLL_OFF':
            # Large open skip
            # Just hollow it out
            builder.select_faces_by_normal(Vector((0,0,1))) \
                   .inset(0.1) \
                   .extrude(-h*0.9) \
                   .tag_slot(0) \
                   .tag_edge_role(1)

            # Ribs on side
            builder.select_faces_by_normal(Vector((1,0,0))) \
                   .inset(0.05, relative=False) \
                   .extrude(0.05) \
                   .tag_slot(2) \
                   .tag_edge_role(1)

        elif self.style == 'RECYCLE':
            # Dome top
            builder.select_faces_by_normal(Vector((0,0,1))) \
                   .extrude(0.2) \
                   .scale(0.8) \
                   .tag_slot(1) \
                   .tag_edge_role(1) # Plastic Top

            # Holes
            builder.select_faces_by_height(min_z=h) \
                   .inset(0.1) \
                   .extrude(-0.1) \
                   .tag_slot(2) \
                   .tag_edge_role(1) # Hole

        # 4. Anchor Socket
        builder.select_faces_by_normal(Vector((0,0,-1))) \
               .tag_socket(9).tag_slot(9)

        # 5. UVs
        # Slot 0: Box
        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Slot 1: Box
        builder.select_faces_by_slot(1) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Slot 2: Box
        builder.select_faces_by_slot(2) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        builder._update()
