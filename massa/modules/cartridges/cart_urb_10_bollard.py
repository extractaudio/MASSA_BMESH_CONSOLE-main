import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_10: Bollard",
    "id": "urb_10_bollard",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbBollard(Massa_OT_Base):
    bl_idname = "massa.gen_urb_10_bollard"
    bl_label = "URB Bollard"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    height: FloatProperty(name="Height", default=1.0, min=0.5)
    radius: FloatProperty(name="Radius", default=0.15, min=0.05)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("SPHERE", "Sphere Top", "Cylinder with Ball"),
            ("POST", "Post", "Simple Cylinder"),
            ("COLUMN", "Column", "Square Profile"),
        ],
        default="POST"
    )

    # Details
    detail_ring: BoolProperty(name="Detail Ring", default=True)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Body", "uv": "TUBE_Z", "phys": "CONCRETE_POL"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "MASSA_DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "height")
        col.prop(self, "radius")
        layout.separator()
        col.prop(self, "detail_ring")

    def build_shape(self, bm):
        # Ensure Layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        h = self.height
        r = self.radius

        if self.style == 'POST':
            # Cylinder
            builder.create_cylinder(radius=r, depth=h, segments=16, cap_ends=True, center=Vector((0,0,h/2))) \
                   .tag_slot(0)

            # Top Chamfer
            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1) \
                   .inset(amount=r*0.3, relative=False) \
                   .extrude(distance=0.05, axis=Vector((0,0,1))) # Small cap

            if self.detail_ring:
                # Ring near top
                # Bisect at h*0.8 and h*0.75
                # Hard to select face ring without ID tracking.
                # Instead, build in segments?
                # MassaBuilder.create_cylinder doesn't support stacks.
                # Let's just overlay a Torus? Or Tube.
                # Create Ring
                ring_r = r * 1.1
                ring_h = 0.05
                z = h * 0.8
                builder.create_cylinder(radius=ring_r, depth=ring_h, segments=16, cap_ends=True, center=Vector((0,0,z))) \
                       .tag_slot(0)

        elif self.style == 'SPHERE':
            # Post + Sphere
            post_h = h - r*1.5 # Leave room for sphere
            if post_h < 0.1: post_h = 0.1

            builder.create_cylinder(radius=r, depth=post_h, segments=16, cap_ends=True, center=Vector((0,0,post_h/2))) \
                   .tag_slot(0)

            # Sphere on top
            center = Vector((0,0, post_h + r*0.8)) # Slightly embedded

            # Use bmesh.ops for sphere
            ret = bmesh.ops.create_uvsphere(
                bm,
                u_segments=16, v_segments=16,
                radius=r
            )
            sphere_verts = ret['verts']
            bmesh.ops.translate(bm, vec=center, verts=sphere_verts)

            # Update active faces manually
            # bmesh.ops.create_uvsphere doesn't return faces reliably in all versions, but 'verts' is reliable.
            sphere_faces = list(set(f for v in sphere_verts for f in v.link_faces))
            builder.active_faces = sphere_faces
            builder.tag_slot(0)

        elif self.style == 'COLUMN':
            # Box
            w = r * 2.0
            d = r * 2.0

            builder.create_box(w, d, h, center=Vector((0,0,h/2))) \
                   .tag_slot(0)

            # Chamfer Edges (Vertical)
            # Select vertical edges?
            # MassaBuilder doesn't have select_edges_by_direction.
            # Select side faces, get boundary? No.

            # Bevel Modifier handles it usually.
            # Just add top detail.

            # Pyramid Top
            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1) \
                   .inset(amount=w*0.4, relative=False) \
                   .translate(z=0.1) # Pull up center (Pyramid-ish)

            # Actually inset creates flat face.
            # If we translate the inset face up, we make a pyramid top.

            if self.detail_ring:
                # Ring (Box)
                ring_size = w * 1.1
                ring_h = 0.05
                z = h * 0.8
                builder.create_box(ring_size, ring_size, ring_h, center=Vector((0,0,z))) \
                       .tag_slot(0)

        # 4. Sockets
        # Anchor (Bottom)
        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.1)
        builder.active_faces = [f for f in builder.active_faces if -0.1 <= f.calc_center_median().z <= 0.1]

        if not builder.active_faces:
             builder.select_faces_by_height(min_z=-0.1, max_z=0.1)

        builder.tag_socket(9).tag_slot(9) # Anchor

        # 5. UVs
        builder.select_all_faces() \
               .tag_uvs(scale=self.uv_scale, projection='TUBE_Z')

        # Cleanup
        builder._update()
