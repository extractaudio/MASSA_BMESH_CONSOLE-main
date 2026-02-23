import bpy
import bmesh
import random
import mathutils
from mathutils import Vector
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty, FloatVectorProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "PRIM_ROCK: Boulder Generator",
    "id": "prim_rock_boulder",
    "icon": "MESH_ICOSPHERE",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": True,
        "FIX_DEGENERATE": True, # Rocks need cleanup
        "ALLOW_SOLIDIFY": True, 
        "ALLOW_CHAMFER": False, 
    },
}

class MASSA_OT_PrimRockBoulder(Massa_OT_Base):
    bl_idname = "massa.gen_prim_rock_boulder"
    bl_label = "PRIM_ROCK: Boulder"
    bl_description = "Procedural Rock & Boulder Generator"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- 1. ARCHETYPE ---
    rock_type: EnumProperty(
        name="Type",
        items=[
            ("BOULDER", "Boulder", "Standard round rock"),
            ("RIVER", "River Stone", "Synthetically smooth and flattened"),
            ("ASTEROID", "Asteroid", "Jagged, heavily chipped"),
            ("SLATE", "Slate", "Flat, layered sheets"),
        ],
        default="BOULDER",
    )

    # --- 2. DIMENSIONS ---
    radius: FloatProperty(name="Radius", default=1.0, min=0.1)
    scale_x: FloatProperty(name="Scale X", default=1.0)
    scale_y: FloatProperty(name="Scale Y", default=1.0)
    scale_z: FloatProperty(name="Scale Z", default=1.0)

    # --- 3. NOISE ENGINE ---
    noise_type: EnumProperty(
        name="Noise",
        items=[
            ("STANDARD", "Standard", "Fractal Perlin Noise"),
            ("VORONOI", "Voronoi", "Cellular / Cracked"),
            ("STRATA", "Strata", "Layered Sedimentary"),
        ],
        default="STANDARD",
    )
    
    seed: IntProperty(name="Seed", default=123)
    subdivisions: IntProperty(name="Res", default=2, min=1, max=5)
    
    noise_strength: FloatProperty(name="Noise Amp", default=0.5, min=0.0)
    noise_scale: FloatProperty(name="Noise Freq", default=1.5, min=0.1)
    
    noise_detail: IntProperty(name="Detail", default=3, min=1, max=8, description="Number of noise octaves")
    noise_roughness: FloatProperty(name="Roughness", default=0.5, min=0.0, max=1.0, description="Amplitude decay (Persistence)")
    noise_lacunarity: FloatProperty(name="Lacunarity", default=2.0, min=1.0, max=4.0, description="Frequency multiplier per octave")
    
    # --- 4. EROSION (Chipping) ---
    erosion_type: EnumProperty(
        name="Method",
        items=[
            ("PLANAR", "Planar", "Flat slice (Chisel)"),
            ("SPHERICAL", "Spherical", "Concave scoop (Crater)"),
        ],
        default="PLANAR",
    )
    chip_count: IntProperty(name="Chips", default=5, min=0)
    chip_scale: FloatProperty(name="Chip Size", default=0.8, min=0.1)

    # --- 5. UV PROTOCOLS ---
    uv_scale: FloatProperty(name="UV Scale", default=1.0, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Cortex (Outer)", "uv": "SKIP", "phys": "ROCK_GRANITE"},
            1: {"name": "Core (Inner)", "uv": "SKIP", "phys": "ROCK_SEDIMENT"},
        }

    def draw_shape_ui(self, layout):
        layout.label(text="Archetype", icon="OUTLINER_OB_META")
        layout.prop(self, "rock_type", text="")
        
        layout.separator()
        layout.label(text="Base Geometry", icon="MESH_ICOSPHERE")
        row = layout.row(align=True)
        row.prop(self, "radius")
        row.prop(self, "subdivisions", text="LOD")
        
        row = layout.row(align=True)
        row.prop(self, "scale_x")
        row.prop(self, "scale_y")
        row.prop(self, "scale_z")

        layout.separator()
        layout.label(text="Noise Engine", icon="FORCE_TURBULENCE")
        layout.prop(self, "noise_type", text="")
        layout.prop(self, "noise_strength")
        layout.prop(self, "noise_scale")
        
        # [DEFENSIVE] Check attributes for hot-reload safety
        if hasattr(self, "noise_detail"):
            row = layout.row(align=True)
            row.prop(self, "noise_detail")
            row.prop(self, "noise_roughness")
            row.prop(self, "noise_lacunarity")
        
        layout.prop(self, "seed")

        if self.rock_type in {'ASTEROID', 'SLATE', 'BOULDER', 'RIVER'}:
            layout.separator()
            layout.label(text="Erosion System", icon="MOD_BOOLEAN")
            if hasattr(self, "erosion_type"):
                layout.prop(self, "erosion_type", text="")
            
            row = layout.row(align=True)
            if hasattr(self, "chip_count"):
                row.prop(self, "chip_count")
            if hasattr(self, "chip_scale"):
                row.prop(self, "chip_scale")

        layout.separator()
        layout.label(text="Surface", icon="GROUP_UVS")
        layout.prop(self, "uv_scale")

    def build_shape(self, bm: bmesh.types.BMesh):
        rng = random.Random(self.seed)

        # A. GENERATE BASE HULL
        bmesh.ops.create_icosphere(bm, subdivisions=self.subdivisions, radius=self.radius)

        # Tag Initial Faces as Cortex (Slot 0)
        for f in bm.faces:
            f.material_index = 0
            f.smooth = True

        # B. TYPE PRE-PROCESSING (Deformation)
        if self.rock_type == 'RIVER':
            bmesh.ops.scale(bm, vec=(1.2, 1.2, 0.4), verts=bm.verts)
        elif self.rock_type == 'SLATE':
            bmesh.ops.scale(bm, vec=(1.5, 1.0, 0.15), verts=bm.verts)

        # Apply General Scale Vector
        s_vec = Vector((self.scale_x, self.scale_y, self.scale_z))
        bmesh.ops.scale(bm, vec=s_vec, verts=bm.verts)
        bmesh.ops.transform(bm, matrix=mathutils.Matrix.Identity(4), verts=bm.verts)

        # C. NOISE DISPLACEMENT
        # ----------------------------------------------------------------------
        # Seed offsets
        offset_x = rng.uniform(-100, 100)
        offset_y = rng.uniform(-100, 100)
        offset_z = rng.uniform(-100, 100)
        seed_vec = Vector((offset_x, offset_y, offset_z))

        # [DEFENSIVE] Get props with defaults for hot-reload safety
        n_detail = getattr(self, "noise_detail", 3)
        n_rough = getattr(self, "noise_roughness", 0.5)
        n_lacun = getattr(self, "noise_lacunarity", 2.0)
        n_type = getattr(self, "noise_type", "STANDARD")

        for v in bm.verts:
            total_noise = 0.0
            amplitude = 1.0
            frequency = 1.0
            
            # Initial coordinate
            base_co = (v.co * self.noise_scale) + seed_vec
            
            try:
                # --- STRATA LOGIC ---
                if n_type == 'STRATA':
                    # Layered noise based on Z height
                    # High frequency bands
                    z_freq = 10.0 * self.noise_scale
                    bands = mathutils.noise.noise(Vector((0, 0, v.co.z * z_freq))) 
                    # Add some XY perturbation
                    xy_noise = mathutils.noise.noise(base_co) * 0.2
                    total_noise = bands + xy_noise
                
                # --- VORONOI LOGIC ---
                elif n_type == 'VORONOI':
                    # Inverted Voronoi for "Cracked" look (F1)
                    # output is [dist, color, position]
                    # [Adjustment]: Voronoi cells are visually large compared to Perlin.
                    # We multiply frequency by 3.5 to align with "Standard" noise scale expectations.
                    
                    v_scale_adjusted = base_co * 3.5
                    v_dat = mathutils.noise.voronoi(v_scale_adjusted)
                    
                    if len(v_dat) > 0:
                        d1 = v_dat[0]
                        # Invert d1 to make cell centers high (cobblestone) or low (cracked)
                        # Let's create "Cracks": 1.0 - d1
                        total_noise = 1.0 - d1
                    else:
                        total_noise = 0.0
                
                # --- STANDARD (FRACTAL) LOGIC ---
                else: 
                    for i in range(n_detail):
                        n_val = mathutils.noise.noise(base_co * frequency)
                        total_noise += n_val * amplitude
                        amplitude *= n_rough
                        frequency *= n_lacun
                    
            except:
                total_noise = 0.5 # Fallback
            
            # Displacement Intensity based on type
            intensity = self.noise_strength
            if self.rock_type == 'RIVER':
                intensity *= 0.3 # River rocks are smoother

            # Apply
            if self.rock_type == 'SLATE' or n_type == 'STRATA':
                # Strata/Slate displaces mostly Z? No, strata creates ridges OUTWARD.
                # Actually, strata varies the radius at Z-heights.
                # Project along Normal (XY mainly)
                n_xy = Vector((v.normal.x, v.normal.y, 0)).normalized()
                if n_xy.length > 0:
                    v.co += n_xy * total_noise * intensity
            else:
                v.co += v.normal * total_noise * intensity

        # Re-calc normals after deformation
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # D. EROSION (CHIPPING)
        # ----------------------------------------------------------------------
        active_chips = self.chip_count
        if self.rock_type == 'RIVER':
            active_chips = max(1, self.chip_count // 2)

        if active_chips > 0:
            bound_rad = self.radius * max(self.scale_x, self.scale_y, self.scale_z)
            e_type = getattr(self, "erosion_type", "PLANAR")

            for i in range(active_chips):
                if not bm.verts: break

                # Random slicing plane / Sphere center
                nx = rng.uniform(-1.0, 1.0)
                ny = rng.uniform(-1.0, 1.0)
                nz = rng.uniform(-1.0, 1.0)
                vec_dir = Vector((nx, ny, nz)).normalized()
                
                # Distance controls how "deep" the cut is relative to surface
                # 1.0 is at the boundary, 0.0 is center
                dist_factor = 1.0 - (self.chip_scale * (0.8 if e_type == 'PLANAR' else 0.4) * rng.uniform(0.5, 1.0))
                dist = bound_rad * dist_factor
                
                origin_co = vec_dir * dist
                
                if e_type == 'SPHERICAL':
                    # Scoop Mode: Find verts near origin_co and push them IN
                    # Radius of the scoop
                    scoop_rad = bound_rad * self.chip_scale * 0.5
                    
                    # Simple distance check (can be slow for high poly, but manageable for rocks)
                    # Optimization: Only check verts in octant? No, iterate all is fine for <10k verts
                    
                    # We want to create a "Concave" impression.
                    # We push verts towards the center of the scoop sphere if they are inside it?
                    # Or we project them onto the BACK of the scoop sphere?
                    
                    # Improved Scoop: Push verts towards origin_co
                    for v in bm.verts:
                        d_vec = v.co - origin_co
                        d_len = d_vec.length
                        if d_len < scoop_rad:
                            # It's inside the scoop crater
                            # Push it "down" into the crater.
                            # We want the surface to become the bottom hemisphere of the scoop sphere.
                            # Target surface is at distance 'scoop_rad' from origin_co? No, that's convex.
                            # We want it to look like a bite was taken out.
                            # So we want the surface to conform to the sphere surface, but "inside" the mesh.
                            
                            # Actually, boolean diff is best, but slow.
                            # Fake it: Push vert ALONG the vector from origin_co to v.co?
                            # If we push it away, we make a bubble.
                            # If we push it towards origin_co, we make a spike.
                            
                            # Correct "Inv-Spherical" shape:
                            # We want to project v.co onto the surface of the sphere defined by (origin_co, scoop_rad).
                            # THIS MAKES A CONVEX BUMP usually.
                            
                            # To make a HOLE, we effectively want to flatten the area?
                            # Simple Planar Flattening is easiest: project onto plane.
                            # But that's PLANAR mode.
                            
                            # Let's try "Crater": Push vertices radially INWARDS from the rock center?
                            # No, push them towards the Scoop Center?
                            
                            # Let's use `bmesh.ops.pointmerge`? No.
                            # Let's just use Gaussian Falloff displacement INWARDS along normal.
                            force = (1.0 - (d_len / scoop_rad)) # 1 at center, 0 at rim
                            # Displace inwards (negative normal)
                            v.co -= v.normal * force * scoop_rad * 0.8
                            
                            # Mark as Inner Core
                            # Find face? It's vertex based. We need to mark faces.
                            for f in v.link_faces:
                                f.material_index = 1
                                f.smooth = (self.rock_type == 'RIVER')

                else:
                    # PLANAR Mode (Bisect)
                    try:
                        res = bmesh.ops.bisect_plane(
                            bm,
                            geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                            dist=0.0001,
                            plane_co=origin_co,
                            plane_no=vec_dir,
                            clear_outer=True,
                            clear_inner=False,
                        )
                        
                        edges_cut = [e for e in bm.edges if e.is_boundary]
                        if edges_cut:
                            res_fill = bmesh.ops.holes_fill(bm, edges=edges_cut, sides=0) # fan fill
                            new_faces = [f for f in res_fill["faces"] if isinstance(f, bmesh.types.BMFace)]
                            for f in new_faces:
                                f.material_index = 1 
                                f.smooth = (self.rock_type == 'RIVER')
                    except:
                        pass

        # E. CLEANUP
        # ----------------------------------------------------------------------
        bmesh.ops.dissolve_degenerate(bm, dist=0.0001, edges=bm.edges[:])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # F. UV MAPPING (Tri-Planar)
        # ----------------------------------------------------------------------
        # Identical to Shard logic
        uv_layer = bm.loops.layers.uv.verify()
        scale_val = self.uv_scale
        
        for f in bm.faces:
            n = f.normal
            nx, ny, nz = abs(n.x), abs(n.y), abs(n.z)

            for l in f.loops:
                co = l.vert.co
                u, v = 0.0, 0.0

                if nz > nx and nz > ny:
                    u, v = co.x, co.y
                elif nx > ny and nx > nz:
                    u, v = co.y, co.z
                else:
                    u, v = co.x, co.z

                l[uv_layer].uv = (u * scale_val, v * scale_val)

        # G. HARD 10 LOGIC (Edge Roles)
        # ----------------------------------------------------------------------
        # We need to assign MASSA_EDGE_SLOTS
        # 1 = Perimeter (where Smooth meets Flat?) or just sharp edges?
        # For rocks, "Perimeter" is ambiguous. We'll define it as "Sharp Edges" (Chipped areas)
        # OR loops that are boundaries (none here since closed manifold).
        
        slot_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not slot_layer:
            slot_layer = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
        
        for e in bm.edges:
            # Default to 2 (Contour)
            e[slot_layer] = 2
            
            # If edge is sharp (angle check), make it 1 (Perimeter/Sharp)
            # or if it borders a Flat face (Chip) and a Smooth face (Cortex)
            f0 = e.link_faces[0] if len(e.link_faces) > 0 else None
            f1 = e.link_faces[1] if len(e.link_faces) > 1 else None
            
            if f0 and f1:
                # Material Boundary Check
                if f0.material_index != f1.material_index:
                    e[slot_layer] = 1 # Perimeter of the chip
                    e.smooth = False
                elif not f0.smooth or not f1.smooth:
                    # If inside a chip (flat), it's a detail
                    e[slot_layer] = 4
                else:
                    # Smooth interface
                    e[slot_layer] = 3 # Guide/Flow (Organic)
