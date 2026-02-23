import bpy
import bmesh
import math
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "URB_07: Trash Bin",
    "id": "urb_07_trash_bin",
    "icon": "MOD_SOLIDIFY",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_UrbTrashBin(Massa_OT_Base):
    bl_idname = "massa.gen_urb_07_trash_bin"
    bl_label = "URB Trash Bin"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    width: FloatProperty(name="Width", default=0.6, min=0.3)
    depth: FloatProperty(name="Depth", default=0.6, min=0.3)
    height: FloatProperty(name="Height", default=1.0, min=0.5)

    # Style
    style: EnumProperty(
        name="Style",
        items=[
            ("STANDARD", "Standard", "Vertical Slats / Mesh"),
            ("DOME", "Dome Top", "Classic Park Bin"),
            ("RECYCLER", "Recycler", "Modern Boxy Unit"),
        ],
        default="STANDARD"
    )

    # Details
    opening_radius: FloatProperty(name="Opening Radius", default=0.2, min=0.05)
    wall_thickness: FloatProperty(name="Wall Thickness", default=0.05, min=0.01)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Body", "uv": "BOX", "phys": "METAL_IRON"},
            1: {"name": "Lid / Rim", "uv": "BOX", "phys": "SYNTH_PLASTIC"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "MASSA_DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "style")
        layout.separator()
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")
        layout.separator()
        col.prop(self, "opening_radius")
        col.prop(self, "wall_thickness")

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
        t = self.wall_thickness

        if self.style == 'STANDARD':
            # Cylinder / Round Bin
            radius = min(w, d) / 2.0

            # Main Body (Cylinder)
            # Center at Z=h/2
            builder.create_cylinder(radius=radius, depth=h, segments=24, cap_ends=True, center=Vector((0,0,h/2))) \
                   .tag_slot(0) # Body

            # Select Top Face for Opening
            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1)

            # Inset for Rim
            builder.inset(amount=t, relative=False)

            # Select Inner Face (The Opening)
            # Inset returns all modified faces. The inner one is the smaller one.
            # Or we can select by normal again and area?
            # Or assume inset leaves inner face active?
            # MassaBuilder.inset: "self.active_faces = [f for f in ret['faces'] if f.is_valid]"
            # This includes the ring (if created?) and the inner face.
            # bmesh.ops.inset_individual replaces original face with inner face and creates ring faces around it.
            # So ret['faces'] contains the inner face.
            # But the ring faces are newly created too? No, usually inset_individual returns just the inner face in 'faces'?
            # Actually, `bmesh.ops.inset_individual` doc says: "faces: (list of BMFace) Output faces."
            # These are the center faces.

            builder.tag_slot(1) # Rim (actually Inner Face, we will extrude down)

            # Extrude Down (Hollow)
            builder.extrude(distance=-(h - t), axis=Vector((0,0,1))) \
                   .tag_slot(0) # Inside Wall

            # Tag the Rim Ring?
            # The rim ring faces are adjacent to the top faces.
            # Finding them is tricky without stored selection.
            # Select faces at top height:
            builder.select_faces_by_height(min_z=h-0.01, max_z=h+0.01)
            builder.tag_slot(1) # Lid/Rim

        elif self.style == 'DOME':
            # Round Bin with Dome Lid
            radius = min(w, d) / 2.0
            body_h = h * 0.7
            lid_h = h - body_h

            # Body
            builder.create_cylinder(radius=radius, depth=body_h, segments=24, cap_ends=True, center=Vector((0,0,body_h/2))) \
                   .tag_slot(0)

            # Lid (Hemisphere-ish)
            # Use Cone/Sphere logic or lathed profile?
            # Simple approach: Create Sphere, squash bottom, translate.

            builder.create_cylinder(radius=radius*1.05, depth=lid_h*0.5, segments=24, cap_ends=True, center=Vector((0,0,body_h + lid_h*0.25))) \
                   .tag_slot(1) # Lid Base Ring

            # Dome Top
            # Create cone?
            builder.create_cone(radius_bottom=radius*1.05, radius_top=0, depth=lid_h*0.8, segments=24, cap_ends=True, center=Vector((0,0,body_h + lid_h*0.5 + lid_h*0.4))) \
                   .tag_slot(1)

            # Opening (Side hole?)
            # Usually Domes have a flap or hole.
            # Let's Boolean a hole? Or just inset a face on the side.
            # Select a side face of the dome cone?
            # Hard to pick procedural face index.
            # Let's just assume it's a solid lid for now (Swing top).

        elif self.style == 'RECYCLER':
            # Boxy
            builder.create_box(w, d, h, center=Vector((0,0,h/2))) \
                   .tag_slot(0)

            # Recessed Top
            builder.select_faces_by_normal(Vector((0,0,1)), tolerance=0.1) \
                   .inset(amount=t, relative=False) \
                   .extrude(-0.1) \
                   .tag_slot(1) # Inner tray

            # Split into bins? (Texture detail usually)

        # 4. Sockets
        # Anchor (Bottom)
        builder.select_faces_by_normal(Vector((0, 0, -1)), tolerance=0.1)
        builder.active_faces = [f for f in builder.active_faces if -0.1 <= f.calc_center_median().z <= 0.1]

        if not builder.active_faces:
             builder.select_faces_by_height(min_z=-0.1, max_z=0.1)

        builder.tag_socket(9).tag_slot(9) # Anchor

        # 5. UVs
        builder.select_all_faces() \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Cleanup
        builder._update()
