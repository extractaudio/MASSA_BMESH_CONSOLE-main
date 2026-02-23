import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_11: HVAC Unit",
    "id": "urb_11_hvac",
    "icon": "MOD_FLUID",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbHVAC(Massa_OT_Base):
    bl_idname = "massa.gen_urb_11_hvac"
    bl_label = "URB HVAC"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    width: FloatProperty(name="Width", default=1.5, min=0.5)
    depth: FloatProperty(name="Depth", default=1.5, min=0.5)
    height: FloatProperty(name="Height", default=1.0, min=0.5)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("ROOFTOP", "Rooftop", "Large commercial unit"),
            ("WALL_MOUNT", "Wall Mount", "Residential AC unit"),
            ("INDUSTRIAL", "Industrial", "Heavy duty with duct ports"),
        ],
        default="ROOFTOP"
    )

    # Details
    fan_count: IntProperty(name="Fan Count", default=1, min=1, max=4)
    grill_inset: FloatProperty(name="Grill Inset", default=0.05, min=0.01)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Casing", "uv": "BOX", "phys": "METAL_PAINTED"},
            1: {"name": "Details", "uv": "BOX", "phys": "METAL_DARK"},
            3: {"name": "Vent/Grill", "uv": "BOX", "phys": "METAL_GRILL"},
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
        col.prop(self, "fan_count")
        col.prop(self, "grill_inset")

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

        # 1. Base Geometry
        # Center Z at h/2 so bottom is at Z=0
        builder.create_box(w, d, h, center=Vector((0, 0, h/2)))
        builder.tag_slot(0) # Casing

        # Tag Edges as Perimeter (Slot 1) for UV Seams
        builder.select_all_faces().tag_edge_role(1)

        # 2. Style Logic
        if self.style == 'ROOFTOP':
            # Fan on Top
            builder.select_faces_by_normal(Vector((0,0,1))) \
                   .inset(0.1) \
                   .extrude(0.05) \
                   .tag_slot(1) \
                   .tag_edge_role(1) # Rim

            # Fan Grills
            # Re-select top faces of the extrusion
            # We can use height heuristic: z > h
            builder.select_faces_by_height(min_z=h+0.01) \
                   .inset(self.grill_inset) \
                   .extrude(-0.05) \
                   .tag_slot(3) \
                   .tag_edge_role(1) # Grill

            # Add Socket on Top
            builder.select_faces_by_height(min_z=h) \
                   .tag_socket(1)

        elif self.style == 'WALL_MOUNT':
            # Fan on Front (Y-)
            builder.select_faces_by_normal(Vector((0,-1,0))) \
                   .inset(0.1) \
                   .extrude(0.02) \
                   .tag_slot(1) \
                   .tag_edge_role(1)

            # Re-select the front face of the extrusion
            # Y < -d/2
            builder.select_faces_by_normal(Vector((0,-1,0))) \
                   .inset(self.grill_inset) \
                   .extrude(-0.02) \
                   .tag_slot(3) \
                   .tag_edge_role(1) # Grill

            # Brackets on Back (Y+)
            builder.select_faces_by_normal(Vector((0,1,0))) \
                   .inset(0.1, depth=0.05) \
                   .tag_slot(1) \
                   .tag_edge_role(1)

        elif self.style == 'INDUSTRIAL':
            # Duct Ports on Sides
            for vec in [Vector((1,0,0)), Vector((-1,0,0))]:
                builder.select_faces_by_normal(vec) \
                       .inset(0.2) \
                       .extrude(0.1) \
                       .tag_slot(1) \
                       .tag_edge_role(1)

                # Port Hole
                # Select the face facing 'vec' that is part of the extrusion
                # Using a strict normal check should work if extrusion is straight
                builder.select_faces_by_normal(vec) \
                       .inset(0.05) \
                       .extrude(-0.05) \
                       .tag_slot(3) \
                       .tag_edge_role(1) # Open Port

        # 4. Anchor Socket
        builder.select_faces_by_normal(Vector((0,0,-1))) \
               .tag_socket(9).tag_slot(9) # Anchor

        # 5. UVs
        # Slot 0: Box
        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Slot 1: Box
        builder.select_faces_by_slot(1) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Slot 3: Box (Grill)
        builder.select_faces_by_slot(3) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        builder._update()
