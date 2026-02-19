import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "LND_02: Boulder",
    "id": "lnd_02_boulder",
    "icon": "MOD_DISPLACE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_LndBoulder(Massa_OT_Base):
    bl_idname = "massa.gen_lnd_02_boulder"
    bl_label = "LND Boulder"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dimensions
    radius: FloatProperty(name="Radius", default=1.0, min=0.1)

    # Noise
    seed: IntProperty(name="Seed", default=0)
    noise_scale: FloatProperty(name="Noise Scale", default=1.0, min=0.1)
    distortion: FloatProperty(name="Distortion", default=0.5, min=0.0)

    # Detail
    subdivisions: IntProperty(name="Subdivisions", default=2, min=1, max=4)
    flat_bottom: BoolProperty(name="Flat Bottom", default=True)

    def get_slot_meta(self):
        return {
            0: {"name": "Rock", "uv": "SKIP", "phys": "STONE_ROUGH"},
            9: {"name": "Socket Anchor", "sock": True}
        }

    def build_shape(self, bm):
        # 1. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        random.seed(self.seed)

        r = self.radius
        ns = self.noise_scale
        dist = self.distortion

        # 2. Base Icosphere
        ret = bmesh.ops.create_icosphere(bm, subdivisions=self.subdivisions, radius=r)

        # 3. Apply Noise Displacement
        # Use simple sin/cos noise based on vertex position + seed
        for v in bm.verts:
            # Current pos
            p = v.co

            # Simple procedural noise function
            # f(x,y,z) = sin(x*s + seed)*d + cos(y*s)*d ...

            nx = math.sin(p.y * ns + self.seed) * dist + math.cos(p.z * ns * 0.5) * dist * 0.5
            ny = math.cos(p.x * ns + self.seed * 0.3) * dist + math.sin(p.z * ns * 0.7) * dist * 0.5
            nz = math.sin(p.x * ns * 0.8) * dist * 0.8 + math.cos(p.y * ns * 0.4) * dist * 0.4

            # Add random jitter
            jx = (random.random() - 0.5) * dist * 0.2
            jy = (random.random() - 0.5) * dist * 0.2
            jz = (random.random() - 0.5) * dist * 0.2

            # Displace along normal? Or just add vector.
            # Adding vector deforms shape more organically.
            v.co += Vector((nx+jx, ny+jy, nz+jz))

        # Recalculate normals
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 4. Flat Bottom (Bisect)
        if self.flat_bottom:
            # Cut at Z= -r/2 ? Or Z=0 relative to center?
            # Let's cut at Z = min_z + r*0.2 to flatten bottom

            # Find lowest point
            min_z = min(v.co.z for v in bm.verts)
            cut_z = min_z + r * 0.3 # Cut off bottom 30%

            # Bisect
            ret_bisect = bmesh.ops.bisect_plane(bm, geom=bm.faces[:]+bm.edges[:]+bm.verts[:], plane_co=Vector((0,0,cut_z)), plane_no=Vector((0,0,1)), clear_inner=True)
            # clear_inner=True removes geometry "behind" plane (normal direction).
            # Normal is +Z. So it removes everything with Z < cut_z?
            # clear_inner removes the "inner" side. Which side is inner?
            # Usually the side OPPOSITE to normal.
            # So if normal is (0,0,1), inner is below. Correct.

            # Fill the hole?
            # bmesh.ops.edgeloop_fill(bm, edges=...)
            # Find open edges
            open_edges = [e for e in bm.edges if e.is_boundary]
            if open_edges:
                # Fill
                # Simple fan fill or n-gon
                ret_fill = bmesh.ops.contextual_create(bm, geom=open_edges)
                # Assign to material 0
                # Identify new face
                for f in ret_fill.get('faces', []):
                    f.material_index = 0

            # Move to Z=0
            # Find new min z (should be cut_z)
            bmesh.ops.translate(bm, vec=Vector((0, 0, -cut_z)), verts=bm.verts)

        # 5. Faceting (Edge Slots)
        # Mark sharp edges based on angle
        # Edges with sharp angle > threshold
        for e in bm.edges:
            if not e.is_manifold: continue
            angle = e.calc_face_angle_signed()
            # If angle is sharp (e.g. < 150 deg or > 210 deg?)
            # calc_face_angle returns radians between face normals.
            # Flat is 0 (or pi?).
            # Usually sharp edge has high angle.
            # If angle > 45 deg (0.78 rad)
            if abs(e.calc_face_angle()) > 0.6: # Approx 35 deg
                e[edge_slots] = 1 # Sharp/Perimeter
                e.smooth = False
            else:
                e.smooth = True

        # 6. Sockets
        # Top most face
        max_z = -float('inf')
        top_face = None
        for f in bm.faces:
            c = f.calc_center_median()
            if c.z > max_z:
                max_z = c.z
                top_face = f

        if top_face:
            # Create socket anchor on top
            # Or just mark it
            # Let's create small face
            c = top_face.calc_center_median()
            sz = 0.1
            v1 = bm.verts.new(c + Vector((-sz, -sz, 0.05)))
            v2 = bm.verts.new(c + Vector((sz, -sz, 0.05)))
            v3 = bm.verts.new(c + Vector((sz, sz, 0.05)))
            v4 = bm.verts.new(c + Vector((-sz, sz, 0.05)))
            f_sock = bm.faces.new((v1, v2, v3, v4))
            f_sock.material_index = 9

        # 7. Manual UVs
        # Triplanar / Box map or Spherical
        # Let's use simple Box mapping
        scale = getattr(self, "uv_scale_0", 1.0)

        for f in bm.faces:
            mat_idx = f.material_index
            if mat_idx == 9: continue

            n = f.normal
            for l in f.loops:
                if abs(n.z) > 0.5:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.y * scale)
                elif abs(n.y) > 0.5:
                    l[uv_layer].uv = (l.vert.co.x * scale, l.vert.co.z * scale)
                else:
                    l[uv_layer].uv = (l.vert.co.y * scale, l.vert.co.z * scale)

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "radius")
        layout.separator()
        col.prop(self, "seed")
        col.prop(self, "noise_scale")
        col.prop(self, "distortion")
        col.prop(self, "subdivisions")
        col.prop(self, "flat_bottom")
