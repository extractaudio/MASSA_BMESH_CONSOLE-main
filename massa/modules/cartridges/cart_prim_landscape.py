import bmesh
import random
import mathutils
from mathutils import Vector
from bpy.props import FloatProperty, IntProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "Landscape",
    "id": "prim_landscape",
    "icon": "MESH_GRID", 
    "scale_class": "MACRO",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": True,
        "FIX_DEGENERATE": True,
    },
}

class MASSA_OT_PrimLandscape(Massa_OT_Base):
    bl_idname = "massa.gen_prim_landscape"
    bl_label = "Landscape"
    bl_options = {"REGISTER", "UNDO", "PRESET"}
    
    # --- DIMENSIONS ---
    subdivision_x: IntProperty(name="Subdivisions X", default=64, min=4, description="Resolution X")
    subdivision_y: IntProperty(name="Subdivisions Y", default=64, min=4, description="Resolution Y")
    
    mesh_size_x: FloatProperty(name="Size X", default=2.0, min=0.01)
    mesh_size_y: FloatProperty(name="Size Y", default=2.0, min=0.01)
    
    # --- NOISE SETTINGS ---
    noise_type: EnumProperty(
        name="Noise Type",
        items=[
            ("hetero_terrain", "Hetero Terrain", "Hetero Terrain"),
            ("fBm", "fBm", "Fractal Brownian Motion"),
            ("hybrid_multi_fractal", "Hybrid Multi Fractal", "Hybrid Multi Fractal"),
            ("ridged_multi_fractal", "Ridged Multi Fractal", "Ridged Multi Fractal"),
            ("multifractal", "Multifractal", "Multifractal"),
            ("marble", "Marble", "Marble"),
            ("shattered_h_terrain", "Shattered hTerrain", "Shattered hTerrain"),
            ("vl_noise_turbulence", "Turbulence", "Turbulence"),
            ("vl_noise_voronoi", "Voronoi", "Voronoi"),
        ],
        default="hetero_terrain"
    )
    
    basis_type: EnumProperty(
        name="Basis Type",
        items=[
            ("BLENDER", "Blender", "Blender"),
            ("PERLIN", "Perlin", "Perlin"),
            ("VORONOI_F1", "Voronoi F1", "Voronoi F1"),
            ("VORONOI_F2", "Voronoi F2", "Voronoi F2"),
            ("VORONOI_F3", "Voronoi F3", "Voronoi F3"),
            ("VORONOI_F4", "Voronoi F4", "Voronoi F4"),
            ("VORONOI_F2F1", "Voronoi F2-F1", "Voronoi F2-F1"),
            ("VORONOI_CRACKLE", "Voronoi Crackle", "Voronoi Crackle"),
            ("CELL_NOISE", "Cell Noise", "Cell Noise"),
        ],
        default="BLENDER"
    )

    random_seed: IntProperty(name="Seed", default=0)
    noise_offset_x: FloatProperty(name="Offset X", default=0.0)
    noise_offset_y: FloatProperty(name="Offset Y", default=0.0)
    noise_offset_z: FloatProperty(name="Offset Z", default=0.0)
    
    noise_detail: IntProperty(name="Detail (Octaves)", default=4, min=1, max=16)
    
    noise_size: FloatProperty(name="Noise Scale", default=1.0)
    
    height: FloatProperty(name="Height", default=1.5)
    height_offset: FloatProperty(name="Height Offset", default=0.0)
    falloff_x: FloatProperty(name="Falloff X", default=0.0, min=0.0)
    falloff_y: FloatProperty(name="Falloff Y", default=0.0, min=0.0)
    
    distortion: FloatProperty(name="Distortion", default=1.0)
    lacunarity: FloatProperty(name="Lacunarity", default=2.0)
    offset: FloatProperty(name="Offset", default=1.0)
    gain: FloatProperty(name="Gain", default=1.0)
    
    # --- SLOT LOGIC PARAMS ---
    water_level: FloatProperty(name="Water Level", default=0.05, description="Height below which faces are tagged as Water/Transparent")
    rock_slope: FloatProperty(name="Rock Slope", default=0.7, min=0.0, max=1.57, description="Angle in radians for rock slope")
    peak_factor: FloatProperty(name="Peak Factor", default=0.8, min=0.0, max=1.0, description="Height percentage defining peaks")

    def get_slot_meta(self):
        return {
            0: {"name": "Ground", "uv": "BOX", "phys": "GENERIC"},
            1: {"name": "Cliffs", "uv": "BOX", "phys": "GENERIC"},
            2: {"name": "Peaks", "uv": "BOX", "phys": "GENERIC"},
            3: {"name": "Shore", "uv": "BOX", "phys": "GENERIC"},
            8: {"name": "Water", "uv": "BOX", "phys": "GENERIC"},
            9: {"name": "Socket", "uv": "SKIP", "sock": True},
        }

    def draw_shape_ui(self, layout):
        box=layout.box()
        box.label(text="Grid & Size")
        row = box.row()
        row.prop(self, "subdivision_x", text="X Res")
        row.prop(self, "subdivision_y", text="Y Res")
        row = box.row()
        row.prop(self, "mesh_size_x", text="Size X")
        row.prop(self, "mesh_size_y", text="Size Y")
        
        box = layout.box()
        box.label(text="Noise Settings")
        box.prop(self, "noise_type")
        box.prop(self, "basis_type")
        box.prop(self, "random_seed")
        box.prop(self, "noise_detail")
        box.prop(self, "noise_size")
        
        col = box.column(align=True)
        col.prop(self, "noise_offset_x", text="Off X")
        col.prop(self, "noise_offset_y", text="Off Y")
        col.prop(self, "noise_offset_z", text="Off Z")

        box = layout.box()
        box.label(text="Height & Falloff")
        box.prop(self, "height")
        box.prop(self, "height_offset")
        row = box.row()
        row.prop(self, "falloff_x", text="Fall X")
        row.prop(self, "falloff_y", text="Fall Y")
        
        box = layout.box()
        box.label(text="Advanced Noise")
        box.prop(self, "distortion")
        box.prop(self, "lacunarity")
        box.prop(self, "offset")
        box.prop(self, "gain")
        
        box = layout.box()
        box.label(text="Slot Logic")
        box.prop(self, "water_level")
        box.prop(self, "rock_slope")
        box.prop(self, "peak_factor")

    def build_shape(self, bm):
        # 1. Native Grid Generation
        # ----------------------------------------------------------------------
        res_x = max(2, self.subdivision_x)
        res_y = max(2, self.subdivision_y)
        size_x = self.mesh_size_x
        size_y = self.mesh_size_y
        
        bmesh.ops.create_grid(
            bm, 
            x_segments=res_x, 
            y_segments=res_y, 
            size=max(size_x, size_y) / 2.0 # create_grid size is radius-like? No, it's diameter.
        )
        
        # Scale to match non-square aspect ratio if needed
        scale_vec = Vector((size_x / max(size_x, size_y), size_y / max(size_x, size_y), 1.0))
        # Wait, create_grid uses 'size' as total width.
        # If size_x=10, size_y=5. create_grid(size=10).
        # We need to scale Y by 0.5.
        
        if abs(size_x - size_y) > 0.001:
            scale_x = size_x
            scale_y = size_y
            # We generated a square of max(size_x, size_y)
            base_s = max(size_x, size_y)
            s_vec = Vector((scale_x / base_s, scale_y / base_s, 1.0))
            bmesh.ops.scale(bm, vec=s_vec, verts=bm.verts)

        # 2. Noise Engine
        # ----------------------------------------------------------------------
        rng = random.Random(self.random_seed)
        seed_offset = Vector((
            rng.uniform(-1000, 1000) + self.noise_offset_x, 
            rng.uniform(-1000, 1000) + self.noise_offset_y, 
            rng.uniform(-1000, 1000) + self.noise_offset_z
        ))

        # Capture props for speed
        n_size = max(0.001, self.noise_size)
        n_height = self.height
        n_type = self.noise_type
        n_lacun = self.lacunarity
        n_gain = self.gain
        n_dist = self.distortion
        n_offset = self.offset
        n_detail = self.noise_detail
        
        # 2a. Resolve Noise Function & Params (OPTIMIZATION)
        # ----------------------------------------------------------------------
        noise_func = None
        noise_kwargs = {}
        
        # Standard Params
        # Note: Some functions take 'octaves', others don't.
        # We differentiate here to avoid repeated "if" checks in loop.
        
        if n_type == 'hetero_terrain':
            noise_func = mathutils.noise.hetero_terrain
            # args: position, H, lacunarity, octaves, offset
            noise_args_fixed = (n_gain, n_lacun, n_detail, n_offset)
            
        elif n_type == 'fBm':
            noise_func = mathutils.noise.fractal
            # args: position, H, lacunarity, octaves, noise_basis
            noise_args_fixed = (n_gain, n_lacun, n_detail, mathutils.noise.types.STDPERLIN)
            
        elif n_type == 'hybrid_multi_fractal':
            noise_func = mathutils.noise.hybrid_multi_fractal
            # args: position, H, lacunarity, octaves, offset, gain
            noise_args_fixed = (n_gain, n_lacun, n_detail, n_offset, 1.0)
            
        elif n_type == 'ridged_multi_fractal':
            noise_func = mathutils.noise.ridged_multi_fractal
            # args: position, H, lacunarity, octaves, offset, gain
            noise_args_fixed = (n_gain, n_lacun, n_detail, n_offset, 1.0)
            
        elif n_type == 'vl_noise_turbulence':
            noise_func = mathutils.noise.turbulence
            # args: position, octaves, hard, noise_basis
            noise_args_fixed = (n_detail, False, mathutils.noise.types.STDPERLIN)
        
        # 2b. Execution Loop (Fast)
        # ----------------------------------------------------------------------
        
        # Pre-calc constants
        has_dist = (n_dist != 1.0)
        
        for v in bm.verts:
            p = v.co + seed_offset
            p *= n_size
            
            z_val = 0.0
            
            if noise_func:
                try:
                    z_val = noise_func(p, *noise_args_fixed)
                except:
                    z_val = 0.0
            
            elif n_type == 'vl_noise_voronoi':
                # Voronoi logic
                try:
                    z_val = mathutils.noise.voronoi(p)[0]
                except:
                    z_val = 0.0
            else:
                # Default Perlin
                try:
                     z_val = mathutils.noise.noise(p)
                except:
                     z_val = 0.0

            # Distortion
            if has_dist:
                 z_val *= n_dist
            
            # Apply Height
            v.co.z += (z_val * n_height) + self.height_offset
            
            # 3. Falloff (Optional)
            if self.falloff_x > 0 or self.falloff_y > 0:
                # Distance from center normalized
                dx = abs(v.co.x) / (size_x / 2.0)
                dy = abs(v.co.y) / (size_y / 2.0)
                
                fx = max(0, 1.0 - (dx * self.falloff_x)) if self.falloff_x > 0 else 1.0
                fy = max(0, 1.0 - (dy * self.falloff_y)) if self.falloff_y > 0 else 1.0
                
                v.co.z *= (fx * fy)

        # 4. Slot Logic (Recalculate Normals Required First)
        # ----------------------------------------------------------------------
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        tag_layer = bm.faces.layers.int.new("MAT_TAG")
        edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        z_up = Vector((0,0,1))
        
        for f in bm.faces:
            angle = f.normal.angle(z_up)
            z_avg = sum([v.co.z for v in f.verts]) / len(f.verts)
            
            slot = 0 # Ground
            
            if z_avg < self.water_level:
                slot = 8 # Water
            elif angle > self.rock_slope:
                slot = 1 # Cliffs
            elif z_avg > (self.height * self.peak_factor) + self.height_offset:
                slot = 2 # Peaks
            elif z_avg < (self.water_level + 0.15):
                slot = 3 # Shore
                
            f[tag_layer] = slot
            
        for e in bm.edges:
            if e.is_boundary:
                e[edge_slots] = 1 # Perimeter
