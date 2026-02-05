import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_23: Cable Tray (Ladder)",
    "id": "prim_23_cable_tray",
    "icon": "MOD_LATTICE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": False,
    },
}

class MASSA_OT_PrimCableTray(Massa_OT_Base):
    bl_idname = "massa.gen_prim_23_cable_tray"
    bl_label = "PRIM_23: Cable Tray"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    width: FloatProperty(name="Width (X)", default=0.6, min=0.1)
    height: FloatProperty(name="Height (Z)", default=0.1, min=0.02)
    length: FloatProperty(name="Length (Y)", default=2.0, min=0.1)
    
    rail_thick: FloatProperty(name="Rail Thickness", default=0.01, min=0.002)
    flange_size: FloatProperty(name="Rail Flange", default=0.015, min=0.0)
    
    rung_spacing: FloatProperty(name="Rung Spacing", default=0.3, min=0.1)
    rung_width: FloatProperty(name="Rung Width", default=0.03, min=0.01)
    rung_height: FloatProperty(name="Rung Height", default=0.015, min=0.005)
    
    uv_scale: FloatProperty(name="UV Scale", default=1.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Tray Metal", "uv": "BOX", "phys": "METAL_ALUMINUM"},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "height")
        col.prop(self, "length")
        
        layout.separator()
        layout.label(text="RAILS")
        col.prop(self, "rail_thick")
        col.prop(self, "flange_size")
        
        layout.separator()
        layout.label(text="RUNGS")
        col.prop(self, "rung_spacing")
        col.prop(self, "rung_width")
        col.prop(self, "rung_height")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, h, l = self.width, self.height, self.length
        rt, rf = self.rail_thick, self.flange_size
        
        # 1. Side Rails (C-Channel Profile pointing inwards)
        # Profile on XZ plane
        # Left Rail (at -w/2): Open to +X
        # Right Rail (at +w/2): Open to -X
        
        def create_rail(x_pos, scale_x):
            # Profile:
            #   Top Flange
            #   |
            #   Web
            #   |
            #   Bottom Flange
            
            # Verts (relative to center of rail web)
            # Center of rail wall is x_pos
            # Flanges extend inwards by rf
            
            # Simple C shape
            #    0____1
            #    |5__4|
            #    | |
            #    | |
            #    |6__7|
            #    3____2
            
            # Just use 2 boxes per rail? Or extrude profile?
            # Extrude profile is cleaner.
            
            # Local coords
            l_verts = []
            l_verts.append((-rt, h/2))    # 0
            l_verts.append((rf, h/2))     # 1
            l_verts.append((rf, h/2 - rt))# 2
            l_verts.append((0, h/2 - rt)) # 3
            l_verts.append((0, -h/2 + rt))# 4
            l_verts.append((rf, -h/2 + rt))# 5
            l_verts.append((rf, -h/2))    # 6
            l_verts.append((-rt, -h/2))   # 7
            
            # Flip X if right rail
            final_verts = []
            for vx, vy in l_verts:
                final_verts.append((vx * scale_x + x_pos, 0, vy))
                
            # Create Face
            bm_verts = [bm.verts.new(v) for v in final_verts]
            # Ensure correct winding?
            # Left Rail (scale_x=1): CCW
            # Right Rail (scale_x=-1): Points flipped X, winding might flip
            if scale_x < 0:
                bm_verts.reverse()
                
            try:
                f = bm.faces.new(bm_verts)
                # Extrude
                res = bmesh.ops.extrude_face_region(bm, geom=[f])
                ext_verts = [v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, verts=ext_verts, vec=(0, l, 0))
            except ValueError:
                pass

        # Create Rails
        create_rail(-w/2 + rt/2, 1) # Left
        create_rail(w/2 - rt/2, -1) # Right
        
        # 2. Rungs
        if self.rung_spacing > 0:
            count = int(l / self.rung_spacing)
            step = l / (count + 1)
            rw, rh_ = self.rung_width, self.rung_height
            
            # Rung width: spans between rails
            # Distance: w - 2*rt
            rung_len = w - 2*rt # Overlap slightly?
            
            for i in range(1, count + 1):
                y = i * step
                # Box
                res = bmesh.ops.create_cube(bm, size=1.0)
                rv = res["verts"]
                bmesh.ops.scale(bm, vec=(rung_len, rw, rh_), verts=rv)
                # Pos: Z at bottom usually
                z_pos = -h/2 + rh_/2
                bmesh.ops.translate(bm, vec=(0, y, z_pos), verts=rv)

        # Mat
        for f in bm.faces:
            f.material_index = 0
            
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
