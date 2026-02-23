import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_12: Fire Hydrant",
    "id": "urb_12_fire_hydrant",
    "icon": "MOD_FLUID",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbHydrant(Massa_OT_Base):
    bl_idname = "massa.gen_urb_12_fire_hydrant"
    bl_label = "URB Fire Hydrant"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    height: FloatProperty(name="Height", default=0.8, min=0.3)
    radius_body: FloatProperty(name="Radius", default=0.15, min=0.05)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("CLASSIC", "Classic", "Traditional Cast Iron"),
            ("MODERN", "Modern", "Sleek Industrial"),
            ("FLUSH", "Flush", "Ground Level Access"),
        ],
        default="CLASSIC"
    )

    # Details
    outlet_count: IntProperty(name="Outlets", default=2, min=1, max=4)
    cap_size: FloatProperty(name="Cap Size", default=0.08, min=0.01)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Body", "uv": "CYLINDER", "phys": "METAL_PAINTED"},
            1: {"name": "Caps/Detail", "uv": "BOX", "phys": "METAL_BRASS"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "height")
        col.prop(self, "radius_body")
        col.prop(self, "outlet_count")
        col.prop(self, "cap_size")

    def build_shape(self, bm):
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        h = self.height
        r = self.radius_body

        if self.style == 'FLUSH':
            h = 0.2 # Force low height

        # 1. Main Body
        builder.create_cylinder(radius=r, depth=h, segments=16, center=Vector((0, 0, h/2)))
        builder.tag_slot(0) # Body

        # Tag Caps as Slot 1 to avoid Pinched UVs from Cylinder Projection
        builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1).tag_slot(1)
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1).tag_slot(1)

        # Tag Cylinder Seam (Guide - Slot 3)
        edge_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        for e in bm.edges:
            v1 = e.verts[0].co
            v2 = e.verts[1].co
            # Vertical check
            if abs(v1.x - v2.x) < 0.001 and abs(v1.y - v2.y) < 0.001:
                # Seam at X+ (approx)
                if v1.x > r * 0.9:
                    e[edge_layer] = 3 # Guide/Seam

        # 2. Style Logic
        if self.style == 'CLASSIC':
            # Top Dome
            builder.select_faces_by_normal(Vector((0,0,1))) \
                   .extrude(0.05) \
                   .scale(0.8) \
                   .extrude(0.1) \
                   .scale(0.5) \
                   .tag_slot(1) \
                   .tag_edge_role(1) # Cap

            # Bottom Flange
            builder.select_faces_by_normal(Vector((0,0,-1))) \
                   .extrude(0.05) \
                   .scale(1.2) \
                   .tag_slot(0) \
                   .tag_edge_role(1)

        elif self.style == 'MODERN':
            # Flat Top, Angular
            builder.select_faces_by_normal(Vector((0,0,1))) \
                   .inset(0.02) \
                   .extrude(-0.02) \
                   .tag_slot(1) \
                   .tag_edge_role(1)

        # 3. Outlets
        if self.style != 'FLUSH':
            # Radial outlets
            # Note: MassaBuilder extrusion moves in global coords if axis provided, or avg normal.
            # Here we select regions.

            z_outlet = h * 0.7

            for i in range(self.outlet_count):
                angle = (i / self.outlet_count) * 2 * math.pi
                dx = math.cos(angle)
                dy = math.sin(angle)
                vec = Vector((dx, dy, 0))

                builder.select_faces_by_normal(vec, tolerance=0.2) \
                       .select_faces_by_height(min_z=z_outlet-0.1, max_z=z_outlet+0.1) \
                       .extrude(0.1) \
                       .tag_slot(1) \
                       .tag_edge_role(1) # Outlet Cap

                # Optional: Scale tip (approximation)
                # builder.scale(0.8, 0.8, 0.8) # This scales relative to center of extrusion

        # 4. Anchor Socket
        builder.select_faces_by_normal(Vector((0,0,-1))) \
               .tag_socket(9).tag_slot(9)

        # 5. UVs
        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='CYLINDER')

        builder.select_faces_by_slot(1) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        builder._update()
