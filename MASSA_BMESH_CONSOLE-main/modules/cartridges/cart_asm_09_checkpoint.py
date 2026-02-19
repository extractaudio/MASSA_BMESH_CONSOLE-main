import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ASM_09: Boom-Gate Checkpoint",
    "id": "asm_09_checkpoint",
    "icon": "MOD_BOOLEAN",
    "scale_class": "MACRO",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}

class MASSA_OT_AsmCheckpoint(Massa_OT_Base):
    bl_idname = "massa.gen_asm_09_checkpoint"
    bl_label = "ASM_09: Boom-Gate Checkpoint"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Shack Width", default=2.0, min=1.5)
    depth: FloatProperty(name="Shack Depth", default=2.0, min=1.5)
    height: FloatProperty(name="Shack Height", default=2.5, min=2.0)

    boom_length: FloatProperty(name="Boom Length", default=4.0, min=2.0)
    open_state: FloatProperty(name="Open State (0-1)", default=0.0, min=0.0, max=1.0)

    window_inset: FloatProperty(name="Window Inset", default=0.2, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Structure (Concrete)", "uv": "SKIP", "phys": "CONCRETE"},
            1: {"name": "Window Frame", "uv": "SKIP", "phys": "METAL_PAINTED"},
            2: {"name": "Boom Hinge", "uv": "SKIP", "phys": "MECHANICAL"},
            6: {"name": "Boom Stripe (Accent)", "uv": "SKIP", "phys": "PLASTIC"}, # Mandate: Slot 6
        }

    def draw_shape_ui(self, layout):
        layout.label(text="SHACK", icon="MESH_DATA")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")
        col.prop(self, "window_inset")

        layout.separator()
        layout.label(text="BOOM GATE", icon="MOD_WIREFRAME")
        col = layout.column(align=True)
        col.prop(self, "boom_length")
        col.prop(self, "open_state")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, d, h = self.width, self.depth, self.height

        # 1. Shack Box
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, 0, h/2), verts=bm.verts)

        # Assign Slot 0 (Structure)
        for f in bm.faces:
            f.material_index = 0

        # 2. Wraparound Window
        # Inset all 4 side walls
        bm.faces.ensure_lookup_table()
        side_faces = []
        for f in bm.faces:
            if abs(f.normal.z) < 0.1: # Side faces
                side_faces.append(f)

        if side_faces:
            res = bmesh.ops.inset_individual(bm, faces=side_faces, thickness=self.window_inset, depth=-0.05)
            # The result 'faces' are the inner faces.
            # Delete them to make windows?
            # Or keep as glass?
            # "Inset all 4 walls and delete the centers to create a wraparound window frame."
            # Mandate says delete.
            bmesh.ops.delete(bm, geom=res['faces'], context='FACES_ONLY')

            # Bridge the gaps? Or leave as frame?
            # If we delete faces only, we leave edges.
            # Usually we want frames.
            # The inset creates a frame around the hole.
            # But we might need to solidify the walls if they are just planes.
            # For now, let's assume thick walls or simple frame.

            # Let's create glass panes instead of deleting?
            # No, mandate says "delete centers". So it's an open frame.
            pass

        # 3. Boom Gate Mechanism
        hinge_x = w/2 + 0.5
        hinge_y = -d/2 + 0.5
        hinge_z = h * 0.4

        # Hinge Post
        ret = bmesh.ops.create_cube(bm, size=1.0)
        h_verts = ret['verts']
        bmesh.ops.scale(bm, vec=(0.3, 0.3, 1.0), verts=h_verts)
        bmesh.ops.translate(bm, vec=(hinge_x, hinge_y, hinge_z), verts=h_verts)
        for v in h_verts:
            for f in v.link_faces:
                f.material_index = 2 # Mechanical

        # Boom Pole
        # Pivot at (hinge_x, hinge_y, hinge_z + 0.5)
        pivot = Vector((hinge_x, hinge_y, hinge_z + 0.5))

        boom_len = self.boom_length
        boom_rad = 0.05

        ret = bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=16,
            diameter1=boom_rad*2,
            diameter2=boom_rad*2,
            depth=boom_len
        )
        b_verts = ret['verts']

        # Rotate 90 deg Y to lie on X axis (Cylinder defaults to Z)
        bmesh.ops.rotate(bm, verts=b_verts, cent=(0,0,0), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'))

        # Position so start is at pivot (Move origin to start)
        bmesh.ops.translate(bm, verts=b_verts, vec=(boom_len/2, 0, 0))

        # Move to pivot position
        bmesh.ops.translate(bm, verts=b_verts, vec=(hinge_x, hinge_y, hinge_z + 0.5))

        # Apply Open State Rotation
        angle = self.open_state * math.radians(90)
        rot_mat = Matrix.Rotation(angle, 4, 'Y') # Rotate up around Y axis (if boom is along X)

        bmesh.ops.rotate(bm, verts=b_verts, cent=pivot, matrix=rot_mat)

        # Assign Slot 6 (Stripes)
        for v in b_verts:
            for f in v.link_faces:
                f.material_index = 6

        # 4. UV Mapping
        uv_layer = bm.loops.layers.uv.verify()

        for f in bm.faces:
            if f.material_index == 6: # Boom Stripes
                # Diagonal stripes logic?
                # Or just fit 0-1 and let texture handle it.
                # "Slot 6 (Accent) for the boom-gate striping".
                # Standard UVs.
                pass

            # Box map all
            for l in f.loops:
                nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                if nz > 0.5:
                    u, v = l.vert.co.x, l.vert.co.y
                elif ny > 0.5:
                    u, v = l.vert.co.x, l.vert.co.z
                else:
                    u, v = l.vert.co.y, l.vert.co.z
                l[uv_layer].uv = (u, v)
