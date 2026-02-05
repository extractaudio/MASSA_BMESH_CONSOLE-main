import bpy
import bmesh
from bpy.props import FloatProperty, IntProperty, EnumProperty, BoolProperty
from mathutils import Vector, Matrix
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_21: Structural Column",
    "id": "prim_21_column",
    "icon": "MESH_CUBE",
    "scale_class": "STANDARD",
    "flags": {
        "ALLOW_SOLIDIFY": False,
        "USE_WELD": True,
        "ALLOW_CHAMFER": True,
    },
}


class MASSA_OT_PrimColumn(Massa_OT_Base):
    bl_idname = "massa.gen_prim_21_column"
    bl_label = "PRIM_21: Column"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- DIMENSIONS (Z-Up Standard) ---
    width: FloatProperty(name="Width (X)", default=0.4, min=0.1, unit="LENGTH")
    depth: FloatProperty(name="Depth (Y)", default=0.4, min=0.1, unit="LENGTH")
    height: FloatProperty(name="Height (Z)", default=3.0, min=0.1, unit="LENGTH")
    
    # --- STYLE ---
    profile: EnumProperty(
        name="Profile",
        items=[
            ("BOX", "Box / Rect", "Standard rectangular column"),
            ("ROUND", "Circular", "Cylindrical column"),
            ("H_BEAM", "H-Beam", "Structural steel H/I profile"),
        ],
        default="BOX",
    )
    
    # Specific props
    web_thick: FloatProperty(name="Web/Wall Thick", default=0.02, min=0.005)
    resolution: IntProperty(name="Resolution", default=16, min=4, max=64)

    # --- DETAILING ---
    has_base: BoolProperty(name="Base Plate", default=True)
    base_height: FloatProperty(name="Base Height", default=0.02, min=0.005)
    base_margin: FloatProperty(name="Base Margin", default=0.05, min=0.0)
    
    has_cap: BoolProperty(name="Cap Plate", default=True)
    cap_height: FloatProperty(name="Cap Height", default=0.02, min=0.005)
    cap_margin: FloatProperty(name="Cap Margin", default=0.05, min=0.0)

    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Column Surface", "uv": "BOX", "phys": "CONSTR_CONCRETE"},
            1: {"name": "Plates", "uv": "BOX", "phys": "METAL_IRON"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="DIMENSIONS", icon="arrow_up_down")
        col = layout.column(align=True)
        col.prop(self, "width")
        col.prop(self, "depth")
        col.prop(self, "height")
        
        layout.separator()
        layout.label(text="PROFILE", icon="MESH_DATA")
        layout.prop(self, "profile", text="")
        if self.profile == "H_BEAM":
            layout.prop(self, "web_thick")
        elif self.profile == "ROUND":
            layout.prop(self, "resolution")
            
        layout.separator()
        layout.label(text="PLATES", icon="MOD_BUILD")
        r = layout.row(align=True)
        r.prop(self, "has_base", toggle=True)
        r.prop(self, "has_cap", toggle=True)
        
        if self.has_base:
            row = layout.row(align=True)
            row.prop(self, "base_height", text="B.Height")
            row.prop(self, "base_margin", text="B.Margin")
        if self.has_cap:
            row = layout.row(align=True)
            row.prop(self, "cap_height", text="C.Height")
            row.prop(self, "cap_margin", text="C.Margin")

        layout.separator()
        layout.prop(self, "uv_scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        w, d, h = self.width, self.depth, self.height
        
        # 1. Main Column
        # Define profile
        verts = []
        if self.profile == "BOX":
            hw, hd = w / 2, d / 2
            verts = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
        elif self.profile == "ROUND":
            import math
            rad = min(w, d) / 2
            for i in range(self.resolution):
                ang = (i / self.resolution) * 2 * math.pi
                verts.append((math.cos(ang) * rad, math.sin(ang) * rad))
        elif self.profile == "H_BEAM":
            # Simple H shape
            hw, hd = w / 2, d / 2
            t = self.web_thick
            # H profile (assume X is Web direction)
            # Actually H beam usually has flanges at top/bottom (Y)
            # Let's do Flanges along Y (Depth)
            #      | |
            #      | |
            #      | |
            #   ---------
            #   ---------
            #      | |
            #      | |
            # No wait, I beam is:
            #  _______
            #     |
            #  _______
            #
            # H beam is similar.
            # Flanges at +/- Y (Depth). Web along X.
            
            # Simple 12-point profile
            ft = t # Flange thickness
            wt = t # Web thickness
            
            # Top Flange (Y+)
            verts.extend([
                (-hw, hd), (hw, hd), (hw, hd - ft), (wt / 2, hd - ft)
            ])
            # Web
            verts.extend([
                (wt / 2, -hd + ft)
            ])
            # Bottom Flange (Y-)
            verts.extend([
                (hw, -hd + ft), (hw, -hd), (-hw, -hd), (-hw, -hd + ft)
            ])
            # Web other side
            verts.extend([
                (-wt / 2, -hd + ft), (-wt / 2, hd - ft), (-hw, hd - ft)
            ])
            # Wait, order must be CCW
            verts = [
                (-hw, hd), (hw, hd), (hw, hd - ft), (wt / 2, hd - ft),
                (wt / 2, -hd + ft), (hw, -hd + ft), (hw, -hd),
                (-hw, -hd), (-hw, -hd + ft), (-wt / 2, -hd + ft),
                (-wt / 2, hd - ft), (-hw, hd - ft)
            ]

        # Create Profile
        bm_verts = [bm.verts.new((v[0], v[1], 0)) for v in verts]
        bm.verts.ensure_lookup_table()
        try:
            face = bm.faces.new(bm_verts)
        except ValueError:
            return # Failed geometry

        # Extrude Height
        res = bmesh.ops.extrude_face_region(bm, geom=[face])
        ext_verts = [v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, verts=ext_verts, vec=(0, 0, h))
        
        # Assign Mat
        for f in bm.faces:
            f.material_index = 0
            
        # 2. Plates
        def add_plate(z_pos, tick, margin):
            pw, pd = w + margin * 2, d + margin * 2
            res = bmesh.ops.create_cube(bm, size=1.0)
            p_verts = res["verts"]
            bmesh.ops.scale(bm, vec=(pw, pd, tick), verts=p_verts)
            # Move to position (center is 0,0,0)
            # if z_pos is bottom (0), we want plate centered at tick/2 ?
            # User passes Start Z of plate
            bmesh.ops.translate(bm, vec=(0, 0, z_pos + tick / 2), verts=p_verts)
            
            # Mat
            p_faces = list({f for v in p_verts for f in v.link_faces})
            for f in p_faces:
                f.material_index = 1
                
        if self.has_base:
            add_plate(0, self.base_height, self.base_margin)
            # Move Column Up? No, usually column sits ON plate or plate is part of column height.
            # Let's keep column overlapping or starting at 0.
            # User expects 'Height' to be total? Or column height?
            # Let's keep column starting at 0.
            
        if self.has_cap:
            add_plate(h - self.cap_height, self.cap_height, self.cap_margin)
            
        # 3. Recalc Normals
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        # 4. UVs (Simple Box)
        scale = self.uv_scale
        uv_layer = bm.loops.layers.uv.verify()
        for f in bm.faces:
            for l in f.loops:
                v = l.vert.co
                # Box mapping approx
                nx, ny, nz = abs(f.normal.x), abs(f.normal.y), abs(f.normal.z)
                if nz > nx and nz > ny:
                    u, v_ = v.x, v.y
                elif nx > ny:
                    u, v_ = v.y, v.z
                else:
                    u, v_ = v.x, v.z
                l[uv_layer].uv = (u * scale, v_ * scale)
