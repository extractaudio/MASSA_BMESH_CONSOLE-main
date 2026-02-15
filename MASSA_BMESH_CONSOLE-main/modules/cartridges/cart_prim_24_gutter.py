import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_24: Gutter (K-Style)",
    "id": "prim_24_gutter",
    "icon": "MOD_FLUID",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
    },
}

class MASSA_OT_PrimGutter(Massa_OT_Base):
    bl_idname = "massa.gen_prim_24_gutter"
    bl_label = "PRIM_24: Gutter"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Width (X)", default=0.12, min=0.05)
    height: FloatProperty(name="Height (Z)", default=0.10, min=0.05)
    length: FloatProperty(name="Length (Y)", default=2.0, min=0.1)
    thickness: FloatProperty(name="Thickness", default=0.002, min=0.001)
    
    uv_scale: FloatProperty(name="UV Scale", default=1.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Gutter Metal", "uv": "BOX", "phys": "METAL_ALUMINUM"},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "length")
        col.prop(self, "thickness")
        layout.prop(self, "uv_scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, h, l = self.width, self.height, self.length
        t = self.thickness
        
        # K-Style Profile (XZ plane)
        # Back wall vertical
        # Bottom flat
        # Front has curves/steps
        # Simplified K-Style:
        #
        #   |               |
        #   |               \
        #   |                |
        #   |________________|
        
        # Points (Clockwise for solid, or create line and solidify?)
        # Let's create thin solid profile
        
        # Outer Profile
        p_out = [
            (-w/2, h),       # Back Top
            (-w/2, 0),       # Back Bot
            (w/2 - w*0.2, 0),# Front Bot corner
            (w/2, h*0.3),    # Front step 1
            (w/2 - w*0.1, h*0.3), # Inset
            (w/2 - w*0.05, h*0.7), # Next step
            (w/2, h),        # Front Top
        ]
        
        # Offset for Inner Profile (Simple offset)
        p_in = []
        for x, z in reversed(p_out):
            # approximate inner
            p_in.append((x - t if x > 0 else x + t, z + t if z < h else z))
            
        # Simplified: Just extrude a line edge and use Solidify modifier?
        # No, cartridge should produce mesh.
        # Let's just make the profile robust.
        
        verts = []
        # Back Wall
        verts.append((-w/2, h)) # 0
        verts.append((-w/2, 0)) # 1
        # Bottom
        verts.append((w/2 - 0.02, 0)) # 2
        # Front Detail (K curve approx)
        verts.append((w/2, h * 0.3)) # 3
        verts.append((w/2 - 0.01, h * 0.3)) # 4
        verts.append((w/2 + 0.01, h * 0.8)) # 5
        verts.append((w/2, h)) # 6
        
        # Inner (Shifted)
        offs_verts = []
        for x, z in reversed(verts):
            offs_verts.append((x - t if x > 0 else x + t, z + t))
            
        # Combine
        # Need to close top
        all_verts = verts + offs_verts
        
        # Create Face
        bm_verts = [bm.verts.new((v[0], 0, v[1])) for v in all_verts]
        try:
            f = bm.faces.new(bm_verts)
            # Extrude
            res = bmesh.ops.extrude_face_region(bm, geom=[f])
            ext_verts = [v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=ext_verts, vec=(0, l, 0))
        except ValueError:
            pass

        # Mat
        for f in bm.faces:
            f.material_index = 0
            
        # 2. MARK SEAMS
        # ----------------------------------------------------------------------
        for e in bm.edges:
            if len(e.link_faces) >= 2:
                # Sharp Edges
                n1 = e.link_faces[0].normal
                n2 = e.link_faces[1].normal
                if n1.dot(n2) < 0.5:
                    e.seam = True

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        # UVs
        scale = self.uv_scale
        uv_layer = bm.loops.layers.uv.verify()
        for f in bm.faces:
            for l_ in f.loops:
                v = l_.vert.co
                nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                if nz > nx and nz > ny:
                    u, v_ = v.x, v.y
                elif nx > ny:
                    u, v_ = v.y, v.z
                else:
                    u, v_ = v.x, v.z
                l_[uv_layer].uv = (u * scale, v_ * scale)
