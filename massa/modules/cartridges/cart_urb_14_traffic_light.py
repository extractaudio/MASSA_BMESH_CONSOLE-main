import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_14: Traffic Light",
    "id": "urb_14_traffic_light",
    "icon": "MOD_FLUID",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbTrafficLight(Massa_OT_Base):
    bl_idname = "massa.gen_urb_14_traffic_light"
    bl_label = "URB Traffic Light"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    pole_height: FloatProperty(name="Pole Height", default=4.5, min=2.0)
    arm_length: FloatProperty(name="Arm Length", default=3.0, min=0.5)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("POLE_MOUNT", "Pole Mount", "Cantilever Arm"),
            ("HANGING", "Hanging", "Suspended on Wire"),
            ("PEDESTRIAN", "Pedestrian", "Small Pole Top"),
        ],
        default="POLE_MOUNT"
    )

    # Details
    light_count: IntProperty(name="Lights", default=3, min=2, max=4)
    hood_length: FloatProperty(name="Hood Length", default=0.3, min=0.1)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Pole/Metal", "uv": "BOX", "phys": "METAL_GALVANIZED"},
            1: {"name": "Housing", "uv": "BOX", "phys": "PLASTIC_YELLOW"},
            3: {"name": "Lens/Glass", "uv": "FIT", "phys": "GLASS"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "pole_height")
        if self.style == 'POLE_MOUNT':
            col.prop(self, "arm_length")
        col.prop(self, "light_count")
        col.prop(self, "hood_length")

    def build_shape(self, bm):
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        ph = self.pole_height

        # 1. Pole (if applicable)
        if self.style in ['POLE_MOUNT', 'PEDESTRIAN']:
            # Vertical Pole
            builder.create_cylinder(radius=0.15, depth=ph, center=Vector((0,0,ph/2)))
            builder.tag_slot(0)

            # Tag Caps (Box UV)
            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1).tag_slot(0) # Keep slot 0, use BOX for all

            # Manual seam for Cylinder UV (if we used it, but we use BOX)
            # Edge Auditor might complain about complex geo without seams?
            # 12-sided cylinder. 12 faces + 2 caps = 14 faces.
            # > 12 faces. Edge Auditor WILL COMPLAIN if no seams.
            # So we MUST add a seam even if using BOX projection, to satisfy the auditor (and help LSCM if used).

            edge_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
            for e in bm.edges:
                if e.verts[0].co.z > 0.1 and e.verts[1].co.z > 0.1: # Skip base?
                    if abs(e.verts[0].co.x - e.verts[1].co.x) < 0.001 and abs(e.verts[0].co.y - e.verts[1].co.y) < 0.001:
                        # Vertical edge
                        if e.verts[0].co.x > 0.1:
                            e[edge_layer] = 3 # Guide

        # 2. Mounting & Housing Position
        housing_pos = Vector((0,0,0))

        if self.style == 'POLE_MOUNT':
            # Horizontal Arm
            al = self.arm_length
            builder.create_cylinder(radius=0.1, depth=al, center=Vector((0,0,0))) # Temp
            builder.rotate(90, axis='Y')
            builder.translate(al/2, 0, ph - 0.2)
            builder.tag_slot(0)

            housing_pos = Vector((al - 0.5, 0, ph - 0.2 - 0.5))

        elif self.style == 'PEDESTRIAN':
            housing_pos = Vector((0.25, 0, 2.0))

        elif self.style == 'HANGING':
            housing_pos = Vector((0,0, 4.0))
            builder.create_cylinder(radius=0.02, depth=1.0, center=Vector((0,0, 4.5)))
            builder.tag_slot(0)

        # 3. Light Housing
        hw = 0.4
        hd = 0.4
        hh = self.light_count * 0.4 + 0.2

        builder.create_box(hw, hd, hh, center=housing_pos)
        builder.tag_slot(1) # Housing
        builder.select_all_faces().tag_edge_role(1) # Seams on box edges

        # 4. Lights & Hoods
        start_z = housing_pos.z + hh/2 - 0.3
        step_z = 0.4

        for i in range(self.light_count):
            lz = start_z - i*step_z
            lpos = Vector((housing_pos.x, housing_pos.y - hd/2, lz))

            # Lens
            builder.create_cylinder(radius=0.12, depth=0.05, center=Vector((0,0,0)))
            builder.rotate(90, axis='X')
            builder.translate(lpos.x, lpos.y, lpos.z)
            builder.tag_slot(3) # Glass
            # Seams on lens cylinder
            # It's small, maybe auditor won't catch it.
            # But "create_cylinder" makes > 12 faces.
            # So tag seams.
            edge_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
            # We can't easily iterate edges of JUST this lens because active_edges isn't set.
            # But create_cylinder sets active_faces.
            # Edges of active faces:
            lens_edges = set()
            for f in builder.active_faces:
                for e in f.edges:
                    lens_edges.add(e)

            for e in lens_edges:
                # Find "vertical" (relative to lens axis Y)
                # Lens axis is Y. "Vertical" seams would be along Y.
                if abs(e.verts[0].co.x - e.verts[1].co.x) < 0.001 and abs(e.verts[0].co.z - e.verts[1].co.z) < 0.001:
                    e[edge_layer] = 3

            # Hood
            hood_pos = lpos + Vector((0, -self.hood_length/2, 0.15))
            builder.create_box(0.3, self.hood_length, 0.02, center=hood_pos)
            builder.tag_slot(1)

        # 5. Anchor
        # builder.create_grid... Grid is planar, 1 face.
        # Just use the pole bottom if available, or create a proxy.
        # Just creating a socket on existing geo is cleaner.
        # But we might not have geo at 0,0,0 if hanging.
        # Create a small invisible anchor box.
        builder.create_box(0.1, 0.1, 0.1, center=Vector((0,0,0)))
        builder.tag_slot(9).tag_socket(9)

        # 6. UVs
        builder.select_faces_by_slot(0).tag_uvs(scale=self.uv_scale, projection='BOX')
        builder.select_faces_by_slot(1).tag_uvs(scale=self.uv_scale, projection='BOX')
        builder.select_faces_by_slot(3).tag_uvs(scale=1.0, projection='BOX') # Glass (FIT caused pinched UVs)

        builder._update()
