import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_04: Barrier",
    "id": "urb_04_barrier",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbBarrier(Massa_OT_Base):
    bl_idname = "massa.gen_urb_04_barrier"
    bl_label = "URB Barrier"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=2.0, min=0.5)
    width: FloatProperty(name="Width", default=0.6, min=0.1)
    height: FloatProperty(name="Height", default=0.9, min=0.3)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("JERSEY", "Jersey", "Concrete Highway Barrier"),
            ("PLANTER", "Planter", "Concrete Box Planter"),
            ("BOLLARD_ROW", "Bollards", "Row of Posts"),
        ],
        default="JERSEY"
    )

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Concrete", "uv": "SKIP", "phys": "CONCRETE"},
            1: {"name": "Soil/Detail", "uv": "SKIP", "phys": "DIRT"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "height")

    def build_shape(self, bm):
        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        l, w, h = self.length, self.width, self.height

        if self.style == 'JERSEY':
            # Jersey Barrier Profile
            # Extrude Y. Profile XZ.
            # Base width: w. Top width: w/3.
            # Vertical step at base? usually sloped.
            # Profile points:
            # (-w/2, 0) -> (-w/2, h_base) -> (-w/6, h) -> (w/6, h) -> (w/2, h_base) -> (w/2, 0)

            h_base = 0.15 # Vertical base lip
            w_top = w * 0.3

            # Create Verts for Face at Y = -l/2
            pts = [
                Vector((-w/2, -l/2, 0)),
                Vector((-w/2, -l/2, h_base)),
                Vector((-w_top/2, -l/2, h)),
                Vector((w_top/2, -l/2, h)),
                Vector((w/2, -l/2, h_base)),
                Vector((w/2, -l/2, 0))
            ]

            # Create Face
            f = bm.faces.new([bm.verts.new(p) for p in pts])
            f.material_index = 0

            # Extrude
            builder.active_faces = [f]
            builder.extrude(l, axis=Vector((0,1,0)))

            # Tag all as Concrete
            builder.tag_slot(0)

            # Mark sharp edges on the extrusion?
            # Edges parallel to Y.
            # Auto-detect might handle it.

        elif self.style == 'PLANTER':
            # Box with Inset Top
            builder.create_box(w, l, h, center=Vector((0,0,h/2)))
            builder.tag_slot(0)

            # Inset Top
            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1)
            builder.inset(amount=0.1, depth=-0.3)
            # Inner face is Soil
            builder.tag_slot(1)

        elif self.style == 'BOLLARD_ROW':
            # Row of cylinders
            # Spacing ~ 1.5m
            count = int(l / 1.5)
            if count < 2: count = 2

            step = l / (count - 1)
            start_y = -l/2

            b_rad = w * 0.3
            if b_rad > 0.15: b_rad = 0.15

            for i in range(count):
                y = start_y + i * step
                builder.create_cylinder(radius=b_rad, depth=h, segments=12, center=Vector((0, y, h/2)))
                builder.tag_slot(0)
                # Domed Top?
                builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1)
                # Bevel top edge?
                builder.select_boundary().bevel(offset=0.03)

        # 4. Sockets
        # Ends (-L/2, +L/2)
        # Select faces near ends

        # Left (-Y)
        builder.select_faces_by_normal(Vector((0, -1, 0)), tolerance=0.1)
        # Filter by position Y approx -l/2
        valid = [f for f in builder.active_faces if abs(f.calc_center_median().y + l/2) < 0.1]
        builder.active_faces = valid
        builder.tag_socket(9).tag_slot(9)

        # Right (+Y)
        builder.select_faces_by_normal(Vector((0, 1, 0)), tolerance=0.1)
        valid = [f for f in builder.active_faces if abs(f.calc_center_median().y - l/2) < 0.1]
        builder.active_faces = valid
        builder.tag_socket(9).tag_slot(9)

        # 5. Manual UVs
        # Slot 0: Box
        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Slot 1: Planar Z (Soil)
        builder.select_faces_by_slot(1) \
               .tag_uvs(scale=self.uv_scale, projection='VIEW')

        builder._update()
