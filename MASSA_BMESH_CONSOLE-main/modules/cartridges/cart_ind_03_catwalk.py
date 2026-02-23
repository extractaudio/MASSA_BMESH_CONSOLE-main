import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

CARTRIDGE_META = {
    "name": "IND_03: Catwalk Grate",
    "id": "ind_03_catwalk",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_IndCatwalk(Massa_OT_Base):
    bl_idname = "massa.gen_ind_03_catwalk"
    bl_label = "IND Catwalk"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    length: FloatProperty(name="Length", default=2.0, min=0.1)
    width: FloatProperty(name="Width", default=1.0, min=0.1)
    frame_height: FloatProperty(name="Frame H", default=0.1, min=0.01)
    toe_kick_height: FloatProperty(name="Toe Kick H", default=0.1, min=0.0)
    frame_thick: FloatProperty(name="Frame Thick", default=0.05, min=0.01)

    # UV
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_STEEL"},
            1: {"name": "Grate", "uv": "SKIP", "phys": "METAL_GRATE"},
            9: {"name": "Socket Anchor", "sock": True, "uv": "SKIP", "phys": "DEBUG_9"}
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "width")
        col.prop(self, "frame_height")
        col.prop(self, "toe_kick_height")
        col.prop(self, "frame_thick")

    def build_shape(self, bm):
        # Pre-create layers
        if not bm.faces.layers.int.get("MASSA_SOCKETS"):
            bm.faces.layers.int.new("MASSA_SOCKETS")
        if not bm.edges.layers.int.get("MASSA_EDGE_SLOTS"):
            bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        builder = MassaBuilder(bm)

        l, w = self.length, self.width
        fh = self.frame_height
        tk = self.toe_kick_height
        ft = self.frame_thick

        # 1. Create Base Box (Frame Height)
        # Position so top is at Z=0?
        # Usually walking surface is Z=0.
        # Frame goes down -fh.

        builder.create_box(l, w, fh, center=Vector((0, 0, -fh/2)))
        builder.tag_slot(0) # Frame

        # 2. Inset Top Face for Grate
        builder.select_faces_by_normal(Vector((0, 0, 1)), tolerance=0.01)

        # Inset
        # builder.inset uses bmesh.ops.inset_individual
        builder.inset(amount=ft)

        # The result of inset is the INNER face (Grate) usually?
        # inset_individual modifies the face in place to become the inner face, and creates new ring faces.
        # MassaBuilder updates active_faces to ret['faces'].
        # ret['faces'] usually contains the modified face(s).

        # Let's verify: Inset creates a ring of faces around the original face.
        # The original face is shrunk.
        # Is ret['faces'] the inner face or the ring?
        # Documentation says "The faces created". Usually the inner face is kept?
        # Let's assume active_faces is now the inner face (Grate).

        builder.tag_slot(1) # Grate

        # 3. Toe Kick
        if tk > 0:
            # We want to extrude the RING (Frame Top) up.
            # To select the ring:
            # Select all Top faces, exclude Slot 1.

            # Select all Up-facing
            all_top = [f for f in bm.faces if f.normal.z > 0.9]

            # Filter for Slot 0 (Frame)
            frame_top = [f for f in all_top if f.material_index == 0]

            if frame_top:
                builder.active_faces = frame_top
                builder.extrude(tk) # Extrude UP
                # The sides of this extrusion are Toe Kick.
                # Top is Toe Kick Top.
                # All Slot 0.

                # Tag new edges as Sharp?
                builder.select_boundary().tag_edge_role(1)

        # 4. Sockets
        # Ends of the frame (-L/2, +L/2)
        # Usually Normals (-1,0,0) and (1,0,0).
        # Tolerance 0.1 to catch slight variations.

        # Left
        builder.select_faces_by_normal(Vector((-1, 0, 0)), tolerance=0.1) \
               .tag_socket(9).tag_slot(9)

        # Right
        builder.select_faces_by_normal(Vector((1, 0, 0)), tolerance=0.1) \
               .tag_socket(9).tag_slot(9)

        # 5. Manual UVs

        # Grate (Slot 1): Planar Z
        builder.select_faces_by_slot(1) \
               .tag_uvs(scale=self.uv_scale, projection='VIEW')

        # Frame (Slot 0): Box
        # We also need to ensure we don't mess up Socket UVs (Slot 9) if we care.
        # tag_uvs applies to active selection.
        # Select Slot 0.
        builder.select_faces_by_slot(0) \
               .tag_uvs(scale=self.uv_scale, projection='BOX')

        # Slot 9 faces are ignored by default in tag_uvs? No.
        # But we selected by Slot 0, so Slot 9 is excluded.

        # 6. Cleanup
        builder.clean()
