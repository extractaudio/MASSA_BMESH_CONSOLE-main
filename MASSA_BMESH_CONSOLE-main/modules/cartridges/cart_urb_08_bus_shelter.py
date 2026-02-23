import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_08: Bus Shelter",
    "id": "urb_08_bus_shelter",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbBusShelter(Massa_OT_Base):
    bl_idname = "massa.gen_urb_08_bus_shelter"
    bl_label = "URB Bus Shelter"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=4.0, min=2.0)
    depth: FloatProperty(name="Depth", default=2.0, min=1.0)
    height: FloatProperty(name="Height", default=2.5, min=2.0)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("CANTILEVER", "Cantilever", "Modern floating roof"),
            ("KIOSK", "Kiosk", "Ad Panel Support"),
            ("SHED", "Shed", "3-Sided Enclosure"),
        ],
        default="CANTILEVER"
    )

    # Details
    roof_thickness: FloatProperty(name="Roof Thickness", default=0.2, min=0.05)
    glass_thickness: FloatProperty(name="Glass Thickness", default=0.02, min=0.01)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_STEEL"},
            3: {"name": "Glass", "uv": "SKIP", "phys": "SYNTH_GLASS"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "MASSA_DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "length")
        col.prop(self, "depth")
        col.prop(self, "height")
        layout.separator()
        col.prop(self, "roof_thickness")
        col.prop(self, "glass_thickness")

    def build_shape(self, bm):
        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        l = self.length
        d = self.depth
        h = self.height
        rt = self.roof_thickness
        gt = self.glass_thickness

        if self.style == 'CANTILEVER':
            # L-Shape profile (Side View) extruded along Length
            # Actually, usually columns at back, roof extending forward.

            # Back Wall / Columns
            col_w = 0.3
            col_d = 0.3

            # 2 Columns
            builder.create_box(col_w, col_d, h - rt, center=Vector((-l/3, d/2 - col_d/2, (h-rt)/2))) \
                   .tag_slot(0)
            builder.create_box(col_w, col_d, h - rt, center=Vector((l/3, d/2 - col_d/2, (h-rt)/2))) \
                   .tag_slot(0)

            # Roof
            builder.create_box(l, d, rt, center=Vector((0, 0, h - rt/2))) \
                   .tag_slot(0)

            # Glass Panels between columns and usually side panels
            # Back Glass
            glass_h = h - rt - 0.2 # Clearance
            # Between columns
            # builder.create_box(l*0.6, gt, glass_h, center=Vector((0, d/2 - col_d/2, glass_h/2 + 0.1))) \
            #        .tag_slot(3)

            # Let's make continuous back glass
            builder.create_box(l - 0.2, gt, glass_h, center=Vector((0, d/2 - col_d - 0.05, glass_h/2 + 0.1))) \
                   .tag_slot(3)

            # Manual UVs for Glass
            builder.select_faces_by_slot(3).tag_uvs(scale=1.0, projection='FIT')

        elif self.style == 'KIOSK':
            # Large side panel (Ad box) supporting roof
            kiosk_w = 0.3
            kiosk_d = d * 0.8

            # Kiosk Left
            builder.create_box(kiosk_w, kiosk_d, h, center=Vector((-l/2 + kiosk_w/2, 0, h/2))) \
                   .tag_slot(0)

            # Post Right
            post_w = 0.15
            builder.create_box(post_w, post_w, h - rt, center=Vector((l/2 - post_w/2, 0, (h-rt)/2))) \
                   .tag_slot(0)

            # Roof
            builder.create_box(l, d, rt, center=Vector((0, 0, h - rt/2))) \
                   .tag_slot(0)

            # Back Glass
            glass_l = l - kiosk_w - post_w - 0.1
            glass_h = h - rt - 0.2
            builder.create_box(glass_l, gt, glass_h, center=Vector(( (kiosk_w - post_w)/2, d/2 - 0.2, glass_h/2 + 0.1))) \
                   .tag_slot(3)

            builder.select_faces_by_slot(3).tag_uvs(scale=1.0, projection='FIT')

        elif self.style == 'SHED':
            # 3 Sided Frame
            frame_th = 0.1

            # Roof
            builder.create_box(l, d, rt, center=Vector((0, 0, h - rt/2))) \
                   .tag_slot(0)

            # Back Wall Frame
            # Top Beam
            # builder.create_box(l, frame_th, frame_th, center=Vector((0, d/2 - frame_th/2, h - rt - frame_th/2))).tag_slot(0)
            # Bottom Beam
            # builder.create_box(l, frame_th, frame_th, center=Vector((0, d/2 - frame_th/2, frame_th/2))).tag_slot(0)
            # Columns
            # Let's just make panels

            # Back Panel
            builder.create_box(l, gt, h - rt, center=Vector((0, d/2 - frame_th, (h-rt)/2))) \
                   .tag_slot(3) # Glass

            # Side Panels
            builder.create_box(gt, d - frame_th*2, h - rt, center=Vector((-l/2 + frame_th, 0, (h-rt)/2))) \
                   .tag_slot(3)
            builder.create_box(gt, d - frame_th*2, h - rt, center=Vector((l/2 - frame_th, 0, (h-rt)/2))) \
                   .tag_slot(3)

            # Frames (Corners)
            # 4 Corner Posts
            for x in [-l/2 + frame_th/2, l/2 - frame_th/2]:
                for y in [-d/2 + frame_th/2, d/2 - frame_th/2]:
                    # Only back corners? Shed usually open front.
                    # Front corners
                    if y < 0: # Front
                        pass
                    # Actually standard shed has 4 posts
                    builder.create_box(frame_th, frame_th, h - rt, center=Vector((x, y, (h-rt)/2))) \
                           .tag_slot(0)

            builder.select_faces_by_slot(3).tag_uvs(scale=1.0, projection='FIT')

        # 4. Sockets
        # Anchor (Bottom)
        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.1)
        # Filter Z ~ 0
        builder.active_faces = [f for f in builder.active_faces if -0.1 <= f.calc_center_median().z <= 0.1]

        if not builder.active_faces:
             # Just select faces at 0
             builder.select_faces_by_height(min_z=-0.1, max_z=0.1)

        builder.tag_socket(9).tag_slot(9) # Anchor

        # 5. UVs (Frame)
        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Cleanup
        builder._update()
