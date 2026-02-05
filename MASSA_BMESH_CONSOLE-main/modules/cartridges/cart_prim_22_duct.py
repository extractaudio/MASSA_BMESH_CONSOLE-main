import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_22: Duct (Rect)",
    "id": "prim_22_duct",
    "icon": "MOD_WIREFRAME",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True, 
        "ALLOW_CHAMFER": False,
    },
}

class MASSA_OT_PrimDuct(Massa_OT_Base):
    bl_idname = "massa.gen_prim_22_duct"
    bl_label = "PRIM_22: Duct"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # Dims (Y is Length)
    width: FloatProperty(name="Width (X)", default=0.6, min=0.1)
    height: FloatProperty(name="Height (Z)", default=0.4, min=0.1)
    length: FloatProperty(name="Length (Y)", default=2.0, min=0.1)
    
    wall_thick: FloatProperty(name="Wall Thickness", default=0.01, min=0.001)
    
    # Flanges
    has_flanges: BoolProperty(name="Flanges", default=True)
    flange_width: FloatProperty(name="Flange Width", default=0.03, min=0.01)
    flange_thick: FloatProperty(name="Flange Thick", default=0.005, min=0.001)
    
    # Ribs
    has_ribs: BoolProperty(name="Cross Ribs", default=False)
    rib_spacing: FloatProperty(name="Rib Spacing", default=1.0, min=0.2)
    
    uv_scale: FloatProperty(name="UV Scale", default=1.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Duct Metal", "uv": "BOX", "phys": "METAL_ALUMINUM"},
            1: {"name": "Flanges/Ribs", "uv": "BOX", "phys": "METAL_ALUMINUM"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="arrow_up_down")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "length")
        layout.prop(self, "wall_thick")
        
        layout.separator()
        layout.label(text="DETAILS", icon="MOD_ARRAY")
        layout.prop(self, "has_flanges")
        if self.has_flanges:
            row = layout.row(align=True)
            row.prop(self, "flange_width", text="F.Width")
            row.prop(self, "flange_thick", text="F.Thick")
            
        layout.prop(self, "has_ribs")
        if self.has_ribs:
            layout.prop(self, "rib_spacing")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, h, l = self.width, self.height, self.length
        t = self.wall_thick
        
        # 1. Main Tube (Hollow)
        # Outer Rect
        hw, hh = w / 2, h / 2
        
        # Inner Rect
        iw, ih = hw - t, hh - t
        
        # Combine into face
        # Bridge loops for hollow profile?
        # Easier: Create Outer face, Extrude, then Inset/Delete?
        # Best: Create the 4 walls profile
        
        # Profile vertices
        #   3_______2
        #   | 7___6 |
        #   | |   | |
        #   | 4___5 |
        #   0_______1
        
        pts = [
            (-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh), # Outer
            (-iw, -ih), (iw, -ih), (iw, ih), (-iw, ih)  # Inner
        ]
        
        # Create Loop for walls
        # Manual face creation
        # Bottom (-Y)
        verts = [bm.verts.new((p[0], 0, p[1])) for p in pts]
        bm.verts.ensure_lookup_table()
        
        # Faces connecting outer to inner
        # 0-1-5-4, 1-2-6-5, 2-3-7-6, 3-0-4-7
        idx = [
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7)
        ]
        
        start_faces = []
        for i1, i2, i3, i4 in idx:
            try:
                f = bm.faces.new((verts[i1], verts[i2], verts[i3], verts[i4]))
                start_faces.append(f)
            except ValueError:
                pass
                
        # Extrude walls
        res = bmesh.ops.extrude_face_region(bm, geom=start_faces)
        ext_verts = [v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=ext_verts, vec=(0, l, 0))
        
        # Mat
        for f in bm.faces:
            f.material_index = 0
            
        # 2. Flanges (Start and End)
        if self.has_flanges:
            fw = self.flange_width
            ft = self.flange_thick
            
            # create flange profile
            # Outer Box: w + fw*2
            # Inner Box: w
            flange_y_locs = [0, l - ft]
            
            for y in flange_y_locs:
                # Create Cube
                res = bmesh.ops.create_cube(bm, size=1.0)
                fv = res["verts"]
                # Scale to (w+fw, thick, h+fw)
                bmesh.ops.scale(bm, vec=(w + fw * 2, ft, h + fw * 2), verts=fv)
                # Move
                bmesh.ops.translate(bm, vec=(0, y + ft/2, 0), verts=fv)
                
                # Delete enter? No, simple box is fine, it will clip.
                # Or make it hollow?
                # Simple box is safer for now, low poly.
                # Mark mat
                for f in list({f for v in fv for f in v.link_faces}):
                    f.material_index = 1
                    
        # 3. Ribs (X-Ribs)
        if self.has_ribs and self.rib_spacing > 0:
            import math
            count = int(l / self.rib_spacing)
            if count > 0:
                step = l / (count + 1)
                for i in range(1, count + 1):
                    y = i * step
                    # Create Rib (Cylinder or Box wrapper)
                    # Let's use thin box wrapper
                    res = bmesh.ops.create_cube(bm, size=1.0)
                    rv = res["verts"]
                    bmesh.ops.scale(bm, vec=(w + 0.02, 0.02, h + 0.02), verts=rv)
                    bmesh.ops.translate(bm, vec=(0, y, 0), verts=rv)
                    for f in list({f for v in rv for f in v.link_faces}):
                        f.material_index = 1

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
