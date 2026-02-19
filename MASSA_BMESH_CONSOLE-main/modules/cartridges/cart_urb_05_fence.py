import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "URB_05: Chainlink Fence",
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
    length: FloatProperty(name="Panel Length", default=3.0, min=0.1)
    height: FloatProperty(name="Panel Height", default=2.0, min=0.1)
    pipe_radius: FloatProperty(name="Frame Radius", default=0.04, min=0.01)

    uv_tile_x: FloatProperty(name="UV Tile X", default=3.0, min=0.1)
    uv_tile_y: FloatProperty(name="UV Tile Y", default=2.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Frame", "uv": "BOX", "phys": "METAL_GALVANIZED"},
            8: {"name": "Chainlink Mesh", "uv": "SKIP", "phys": "METAL_CHAINLINK"}, # Transparent
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()

        l = self.length
        h = self.height
        pr = self.pipe_radius

        # 2. Frame (Cylinders)
        # 4 Pipes: Top, Bottom, Left, Right

        # Top Rail (Length L)
        # Create Cylinder
        res_TR = bmesh.ops.create_cone(bm, cap_ends=True, radius1=pr, radius2=pr, depth=l, segments=8)
        # Rotate 90 Y (Cylinder is Z by default).
        bmesh.ops.rotate(bm, cent=Vector((0,0,0)), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=res_TR['verts'])
        # Translate to (0, 0, h - pr)
        bmesh.ops.translate(bm, vec=Vector((0, 0, h - pr)), verts=res_TR['verts'])

        # Bottom Rail
        res_BR = bmesh.ops.create_cone(bm, cap_ends=True, radius1=pr, radius2=pr, depth=l, segments=8)
        bmesh.ops.rotate(bm, cent=Vector((0,0,0)), matrix=Matrix.Rotation(math.radians(90), 3, 'Y'), verts=res_BR['verts'])
        bmesh.ops.translate(bm, vec=Vector((0, 0, pr)), verts=res_BR['verts'])

        # Left Post (Height H)
        res_PL = bmesh.ops.create_cone(bm, cap_ends=True, radius1=pr, radius2=pr, depth=h, segments=8)
        bmesh.ops.translate(bm, vec=Vector((-l/2 + pr, 0, h/2)), verts=res_PL['verts'])

        # Right Post
        res_PR = bmesh.ops.create_cone(bm, cap_ends=True, radius1=pr, radius2=pr, depth=h, segments=8)
        bmesh.ops.translate(bm, vec=Vector((l/2 - pr, 0, h/2)), verts=res_PR['verts'])

        # Assign Frame Material
        for f in bm.faces:
            f.material_index = 0

        # 3. Chainlink Mesh (Plane)
        # XZ Plane inside frame
        # Verts
        vx_min = -l/2 + pr
        vx_max = l/2 - pr
        vz_min = pr
        vz_max = h - pr

        v1 = bm.verts.new(Vector((vx_min, 0, vz_min)))
        v2 = bm.verts.new(Vector((vx_max, 0, vz_min)))
        v3 = bm.verts.new(Vector((vx_max, 0, vz_max)))
        v4 = bm.verts.new(Vector((vx_min, 0, vz_max)))

        f_mesh = bm.faces.new((v1, v2, v3, v4))
        f_mesh.material_index = 8

        # 4. Sockets
        # Posts ends (usually at bottom to ground, or sides to connect)
        # Bottom faces of posts? Z=0.
        # Top faces?
        # Let's add side sockets.
        for f in bm.faces:
            c = f.calc_center_median()
            # If approx on Left End or Right End
            if abs(c.x + l/2) < 0.1 or abs(c.x - l/2) < 0.1:
                # Check normal X
                if abs(f.normal.x) > 0.9:
                    f.material_index = 9

        # 5. Manual UVs
        scale = getattr(self, "uv_scale_0", 1.0)

        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue

            if mat_idx == 8: # Mesh
                # Fit 0-1 scaled by tiling params
                # Verts order: v1(BL), v2(BR), v3(TR), v4(TL)
                # U: X, V: Z
                for l in f.loops:
                    u = (l.vert.co.x - vx_min) / (vx_max - vx_min)
                    v = (l.vert.co.z - vz_min) / (vz_max - vz_min)

                    l[uv_layer].uv = (u * self.uv_tile_x, v * self.uv_tile_y)
            else: # Frame
                # Box or Cylinder
                n = f.normal
                # Simple Box
                if abs(n.x) > 0.5:
                    l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)
                elif abs(n.y) > 0.5:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
                else:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "length")
        col.prop(self, "height")
        col.prop(self, "pipe_radius")
        layout.separator()
        col.prop(self, "uv_tile_x")
        col.prop(self, "uv_tile_y")
