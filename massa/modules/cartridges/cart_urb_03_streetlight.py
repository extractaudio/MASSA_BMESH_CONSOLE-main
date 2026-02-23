import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_03: Streetlight",
    "id": "urb_03_streetlight",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbStreetlight(Massa_OT_Base):
    bl_idname = "massa.gen_urb_03_streetlight"
    bl_label = "URB Streetlight"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    height: FloatProperty(name="Height", default=6.0, min=2.0)
    overhang: FloatProperty(name="Overhang", default=1.5, min=0.1)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("CLASSIC", "Classic", "Ornate Single Arm"),
            ("MODERN_LED", "Modern LED", "Sleek Angled"),
            ("CYBERPUNK", "Cyberpunk", "Industrial Tech"),
        ],
        default="MODERN_LED"
    )

    # Details
    base_radius: FloatProperty(name="Base Radius", default=0.2, min=0.1)
    pole_radius: FloatProperty(name="Pole Radius", default=0.1, min=0.02)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Pole Metal", "uv": "SKIP", "phys": "METAL_PAINTED"},
            4: {"name": "Light Emitter", "uv": "SKIP", "phys": "EMISSIVE"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "height")
        col.prop(self, "overhang")
        col.prop(self, "base_radius")
        col.prop(self, "pole_radius")

    def build_shape(self, bm):
        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        h = self.height
        oh = self.overhang
        pr = self.pole_radius
        br = self.base_radius

        # 1. Base
        # Cylinder at origin
        base_h = 0.5
        builder.create_cylinder(radius=br, depth=base_h, segments=12, center=Vector((0,0,base_h/2)))
        builder.tag_slot(0)

        # 2. Pole
        pole_h = h - base_h
        # Tapered?
        builder.create_cylinder(radius=pr, depth=pole_h, segments=12, center=Vector((0,0,base_h + pole_h/2)))
        # Mark vertical seam
        builder.tag_slot(0)

        top_z = h

        # 3. Arm & Head (Style Dependent)

        if self.style == 'CLASSIC':
            # Curved Arm
            # Use Torus segment or approximate with cylinder segments.
            # "Overhang" is horizontal reach.

            # Simple Arc
            steps = 6
            start_p = Vector((0, 0, top_z - 0.5)) # Attach slightly below top
            end_p = Vector((oh, 0, top_z + 0.5)) # Rise slightly

            # Bezier-ish points
            p0 = start_p
            p1 = Vector((0, 0, top_z + 0.5)) # Up
            p2 = Vector((oh*0.5, 0, top_z + 1.0)) # Peak
            p3 = end_p

            # Just segmented connection p0 -> p3
            # Linear for now, curve is hard without spline lib in builder.
            # Let's do 2 segments: Vertical then Horizontal? Or Angled.

            # Angled Arm
            builder.create_cylinder(radius=pr*0.8, depth=math.hypot(oh, 1.0), segments=8, center=Vector((0,0,0)))
            # Rotate to angle
            angle = math.atan2(1.0, oh) # Rise 1.0 over run oh
            # Vector is (oh, 0, 1.0)
            target = Vector((oh, 0, 1.0)).normalized()
            q = Vector((0,0,1)).rotation_difference(target)
            mid = (start_p + end_p) / 2

            mat = Matrix.Translation(mid) @ q.to_matrix().to_4x4()
            builder.transform(mat)
            builder.tag_slot(0)

            # Head (Lantern)
            head_pos = end_p
            # Lantern box
            builder.create_box(0.3, 0.3, 0.5, center=head_pos)
            builder.tag_slot(4) # Emissive (Glass)
            # Cap
            builder.create_cylinder(radius=0.25, depth=0.1, segments=6, center=head_pos + Vector((0,0,0.3)))
            builder.tag_slot(0)

        elif self.style == 'MODERN_LED':
            # Sleek 90 degree arm or angled
            # Arm
            arm_thick = pr * 0.8

            # Horizontal Arm
            builder.create_box(oh + pr, arm_thick, arm_thick, center=Vector((oh/2, 0, top_z)))
            builder.tag_slot(0)

            # LED Panel (Underneath)
            # Thin plate under the arm tip
            # Tip is at X = oh.
            panel_len = 0.6
            panel_w = 0.25
            panel_center = Vector((oh - panel_len/2, 0, top_z - arm_thick/2 - 0.01))

            builder.create_box(panel_len, panel_w, 0.02, center=panel_center)
            builder.tag_slot(4) # Emissive

        elif self.style == 'CYBERPUNK':
            # Techy, chunky, maybe multiple heads
            # Angled support strut

            # Main Arm
            builder.create_box(oh, pr*2, pr*2, center=Vector((oh/2, 0, top_z)))
            builder.tag_slot(0)

            # Support Strut (Diagonal under)
            # From (0,0,top_z - 1) to (oh/2, 0, top_z)
            p1 = Vector((0,0,top_z - 1.0))
            p2 = Vector((oh/2, 0, top_z))
            vec = p2 - p1
            l_strut = vec.length
            mid = (p1 + p2) / 2

            builder.create_cylinder(radius=pr*0.5, depth=l_strut, segments=6, center=Vector((0,0,0)))
            q = Vector((0,0,1)).rotation_difference(vec.normalized())
            builder.transform(Matrix.Translation(mid) @ q.to_matrix().to_4x4())
            builder.tag_slot(0)

            # Light Bar
            # Vertical drop? Or horizontal strip?
            # Horizontal strip with "Glow"
            strip_center = Vector((oh - 0.5, 0, top_z - pr - 0.05))
            builder.create_box(1.0, 0.1, 0.05, center=strip_center)
            builder.tag_slot(4)

        # 4. Sockets
        # Base Bottom
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1) \
               .tag_socket(9).tag_slot(9)

        # Pole Top (for stacking?)
        # Only if needed.

        # 5. Manual UVs
        # Slot 0 (Metal): Cylinder Projection for vertical parts?
        # But we have horizontal arms too.
        # Box Projection is safest for complex assemblies.

        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        builder.select_faces_by_slot(4) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        builder._update()
