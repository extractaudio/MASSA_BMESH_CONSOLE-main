import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_05: Fence",
    "id": "urb_05_fence",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbFence(Massa_OT_Base):
    bl_idname = "massa.gen_urb_05_fence"
    bl_label = "URB Fence"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=4.0, min=0.1)
    height: FloatProperty(name="Height", default=2.0, min=0.5)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("CHAINLINK", "Chainlink", "Diamond Mesh"),
            ("PICKET", "Picket", "Classic Wood Fence"),
            ("PRIVACY", "Privacy", "Solid Panels"),
        ],
        default="CHAINLINK"
    )

    # Details
    post_spacing: FloatProperty(name="Post Spacing", default=2.0, min=0.5)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Structure", "uv": "SKIP", "phys": "METAL_STEEL"},
            8: {"name": "Infill", "uv": "SKIP", "phys": "CHAINLINK"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "length")
        col.prop(self, "height")
        col.prop(self, "post_spacing")

    def build_shape(self, bm):
        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        l = self.length
        h = self.height

        # Calculate Posts
        num_posts = int(l / self.post_spacing) + 1
        if num_posts < 2: num_posts = 2

        spacing = l / (num_posts - 1)
        start_y = -l/2

        # 1. Posts
        post_size = 0.1

        for i in range(num_posts):
            y = start_y + i * spacing
            builder.create_box(post_size, post_size, h, center=Vector((0, y, h/2)))
            builder.tag_slot(0) # Structure

        # 2. Rails / Infill
        if self.style == 'CHAINLINK':
            # Top Rail
            rail_thick = 0.05
            builder.create_box(rail_thick, l, rail_thick, center=Vector((0, 0, h - rail_thick/2)))
            builder.tag_slot(0)

            # Mesh (Single Plane with Alpha Texture)
            # Or solid geometry? Mandate says solid.
            # But chainlink is wire.
            # If we make wireframe, vert count explodes.
            # Standard: Use Plane with Alpha.
            # Create a thin box for mesh volume?
            # Or just a plane. "Solid volumetric geometry... rather than zero-thickness shells".
            # So creating a thin box (0.01) is better than a plane.

            mesh_thick = 0.01
            builder.create_box(mesh_thick, l, h - rail_thick, center=Vector((0, 0, (h - rail_thick)/2)))
            builder.tag_slot(8) # Infill (Chainlink Material)

        elif self.style == 'PICKET':
            # Rails
            rail_h = 0.1
            rail_thick = 0.05
            # Top Rail
            builder.create_box(rail_thick, l, rail_h, center=Vector((0, 0, h*0.8)))
            builder.tag_slot(0)
            # Bot Rail
            builder.create_box(rail_thick, l, rail_h, center=Vector((0, 0, h*0.2)))
            builder.tag_slot(0)

            # Pickets
            picket_w = 0.1
            picket_gap = 0.1
            picket_thick = 0.02

            num_pickets = int(l / (picket_w + picket_gap))
            p_step = l / num_pickets

            for i in range(num_pickets):
                y = start_y + i * p_step + p_step/2
                # Slightly offset X so they sit on rails
                builder.create_box(picket_thick, picket_w, h, center=Vector((rail_thick/2 + picket_thick/2, y, h/2)))
                builder.tag_slot(0) # Wood? Structure.
                # Pointy Top
                # Select Top Face
                # builder.select_faces_by_normal(Vector((0,0,1))) ... difficult to select specific picket top.
                # But creating them in loop leaves them selected?
                # No, create_box updates active_faces to the NEW box faces.
                # So we can operate immediately.

                builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1)
                # Poke and Pull up
                # Or Bevel
                # Let's just leave flat or simple bevel
                builder.select_boundary().bevel(offset=0.02)

        elif self.style == 'PRIVACY':
            # Solid Panels between posts
            # Inset slightly
            panel_thick = 0.02

            for i in range(num_posts - 1):
                y_start = start_y + i * spacing
                y_end = start_y + (i+1) * spacing

                # Center of panel
                y_mid = (y_start + y_end) / 2
                p_len = spacing - post_size

                builder.create_box(panel_thick, p_len, h - 0.2, center=Vector((0, y_mid, h/2)))
                builder.tag_slot(8) # Infill

        # 3. Sockets
        # Ends of Posts
        # Left End (-L/2)
        builder.select_faces_by_normal(Vector((0, -1, 0)), tolerance=0.1)
        valid = [f for f in builder.active_faces if abs(f.calc_center_median().y + l/2) < 0.2]
        builder.active_faces = valid
        builder.tag_socket(9).tag_slot(9)

        # Right End (+L/2)
        builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.1)
        valid = [f for f in builder.active_faces if abs(f.calc_center_median().y - l/2) < 0.2]
        builder.active_faces = valid
        builder.tag_socket(9).tag_slot(9)

        # 4. Manual UVs
        # All Box
        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        builder.select_faces_by_slot(8) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        builder._update()
