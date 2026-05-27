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
    has_feet: BoolProperty(name="Has Feet", default=True)
    feet_height: FloatProperty(name="Feet Height", default=0.1, min=0.05)
    duct_size: FloatProperty(name="Duct Size", default=0.3, min=0.1)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Casing", "uv": "BOX", "phys": "METAL_PAINTED"},
            1: {"name": "Details", "uv": "BOX", "phys": "METAL_DARK"},
            2: {"name": "Duct Socket", "sock": True, "uv": "SKIP", "phys": "DEBUG_2"},
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
        layout.separator()
        col.prop(self, "has_feet")
        if self.has_feet:
            col.prop(self, "feet_height")
        if self.style == 'INDUSTRIAL':
            col.prop(self, "duct_size")

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

        base_z = self.feet_height if self.has_feet else 0.0

        # 1. Base Geometry
        # Center Z at h/2 + base_z so bottom is at base_z
        builder.create_box(w, d, h, center=Vector((0, 0, base_z + h/2)))
        builder.tag_slot(0) # Casing

        # Tag Edges as Perimeter (Slot 1) for UV Seams
        builder.select_all_faces().tag_edge_role(1)

        # Feet / Rails
        if self.has_feet:
            rail_w = w * 0.1
            rail_d = d * 0.8
            # Rail 1
            builder.create_box(rail_w, rail_d, self.feet_height, center=Vector((w/2 - rail_w, 0, self.feet_height/2)))
            builder.tag_slot(1).tag_edge_role(1)
            # Rail 2
            builder.create_box(rail_w, rail_d, self.feet_height, center=Vector((-w/2 + rail_w, 0, self.feet_height/2)))
            builder.tag_slot(1).tag_edge_role(1)

        # 2. Style Logic
        if self.style == 'ROOFTOP':
            # Distributed Fans on Top
            fan_radius = min(w, d) / (self.fan_count * 2.5)
            spacing_axis = 'X' if w > d else 'Y'
            spacing_dist = w if w > d else d
            
            for i in range(self.fan_count):
                offset = -spacing_dist/2 + (spacing_dist / (self.fan_count + 1)) * (i + 1)
                fan_center = Vector((offset, 0, base_z + h)) if spacing_axis == 'X' else Vector((0, offset, base_z + h))
                
                builder.create_cylinder(radius=fan_radius, depth=0.1, center=fan_center)
                builder.tag_slot(1).tag_edge_role(1)
                
                # Inner Grill
                builder.select_faces_by_normal(Vector((0,0,1))) \
                       .inset(self.grill_inset) \
                       .extrude(-0.05) \
                       .tag_slot(3).tag_edge_role(1)

            # Add Socket on Top of main body
            builder.select_faces_by_height(min_z=base_z + h - 0.01, max_z=base_z + h + 0.01) \
                   .tag_socket(1)

        elif self.style == 'WALL_MOUNT':
            # Distributed Fans on Front (Y-)
            fan_radius = min(w, h) / (self.fan_count * 2.5)
            spacing_axis = 'X' if w > h else 'Z'
            spacing_dist = w if w > h else h
            
            for i in range(self.fan_count):
                offset = -spacing_dist/2 + (spacing_dist / (self.fan_count + 1)) * (i + 1)
                fan_center = Vector((offset, -d/2, base_z + h/2)) if spacing_axis == 'X' else Vector((0, -d/2, base_z + offset))
                
                # We need cylinder aligned to Y- axis. create_cylinder makes it along Z.
                builder.create_cylinder(radius=fan_radius, depth=0.1, center=Vector((0,0,0)))
                # Rotate it 90 degrees around X to point along Y
                builder.rotate(90, axis='X')
                builder.translate(fan_center.x, fan_center.y, fan_center.z)
                builder.tag_slot(1).tag_edge_role(1)
                
                # Inner Grill
                builder.select_faces_by_normal(Vector((0,-1,0))) \
                       .inset(self.grill_inset) \
                       .extrude(-0.02) \
                       .tag_slot(3).tag_edge_role(1)

            # Brackets on Back (Y+)
            builder.create_box(w*0.1, 0.1, h*0.8, center=Vector((w*0.4, d/2 + 0.05, base_z + h/2)))
            builder.tag_slot(1).tag_edge_role(1)
            builder.create_box(w*0.1, 0.1, h*0.8, center=Vector((-w*0.4, d/2 + 0.05, base_z + h/2)))
            builder.tag_slot(1).tag_edge_role(1)

        elif self.style == 'INDUSTRIAL':
            # Fans on Top
            fan_radius = min(w, d) / (self.fan_count * 2.5)
            spacing_axis = 'X' if w > d else 'Y'
            spacing_dist = w if w > d else d
            
            for i in range(self.fan_count):
                offset = -spacing_dist/2 + (spacing_dist / (self.fan_count + 1)) * (i + 1)
                fan_center = Vector((offset, 0, base_z + h)) if spacing_axis == 'X' else Vector((0, offset, base_z + h))
                
                builder.create_cylinder(radius=fan_radius, depth=0.1, center=fan_center)
                builder.tag_slot(1).tag_edge_role(1)
                
                # Inner Grill
                builder.select_faces_by_normal(Vector((0,0,1))) \
                       .inset(self.grill_inset) \
                       .extrude(-0.05) \
                       .tag_slot(3).tag_edge_role(1)
            
            # Duct Ports on Sides
            for vec_x in [1, -1]:
                builder.create_cylinder(radius=self.duct_size, depth=0.2, center=Vector((0,0,0)))
                builder.rotate(90, axis='Y')
                builder.translate(vec_x * (w/2 + 0.1), 0, base_z + h/2)
                builder.tag_slot(1).tag_edge_role(1)
                
                vec = Vector((vec_x, 0, 0))
                # Open Port
                builder.select_faces_by_normal(vec) \
                       .inset(0.05) \
                       .extrude(-0.1) \
                       .tag_slot(3).tag_edge_role(1) \
                       .tag_socket(2) # Duct Socket

        # 4. Anchor Socket (bottom of main body or feet)
        # We'll just grab the lowest facing-down face.
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
