import bpy
import bmesh
import math
from bpy.props import FloatProperty, BoolProperty, EnumProperty, IntProperty, IntVectorProperty
import random
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector

# ==============================================================================
# MASSA CARTRIDGE: CONSTRUCTION FLOORING (Stability Patch)
# ID: prim_con_flooring
# ==============================================================================

CARTRIDGE_META = {
    "name": "Con: Flooring",
    "id": "prim_con_flooring",
    "icon": "GRID",
    "scale_class": "MACRO",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": False,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": False,
        "LOCK_PIVOT": True,
    },
}


class MASSA_OT_prim_con_flooring(Massa_OT_Base):
    bl_idname = "massa.gen_prim_con_flooring"
    bl_label = "Construction Flooring"
    bl_description = "Stable Per-Tile Chamfer"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- Properties ---
    area_size: FloatProperty(name="Area Size", default=4.0, unit="LENGTH")
    tile_w: FloatProperty(name="Tile Width", default=0.3, unit="LENGTH")
    tile_l: FloatProperty(name="Tile Length", default=0.3, unit="LENGTH")
    gap: FloatProperty(name="Grout Gap", default=0.005, min=0.001, max=0.05, unit="LENGTH", precision=3, step=0.1)
    
    # --- Types ---
    floor_style: EnumProperty(name="Style", items=[('TILE', "Tile", "Grid/Hex"), ('WOOD', "Wood", "Planks")], default='TILE')
    tile_shape: EnumProperty(name="Shape", items=[('RECT', "Rectangle", ""), ('HEX', "Hexagon", "")], default='RECT')
    
    # --- Randomness (Wood) ---
    seed: IntProperty(name="Seed", default=101)
    rand_len: FloatProperty(name="Rand Length", default=0.2, min=0.0, max=1.0)
    rand_stagger: FloatProperty(name="Rand Stagger", default=0.5, min=0.0, max=1.0)
    
    stagger: FloatProperty(name="Stagger", default=0.5, min=0.0, max=1.0)
    
    # --- Detail (Wood) ---
    wood_subdiv: IntVectorProperty(name="Segments", default=(1, 1, 1), min=1, size=3)
    use_noise: BoolProperty(name="Use Noise", default=False)
    noise_str: FloatProperty(name="Noise Str", default=0.005, min=0.0, max=0.05, unit="LENGTH")

    # Dimensions
    tile_height: FloatProperty(name="Extrusion Height", default=0.01, min=0.001, max=0.1, unit="LENGTH", precision=3, step=0.001)

    # Chamfer Control
    use_chamfer: BoolProperty(name="Chamfer Top", default=True)
    chamfer_width: FloatProperty(
        name="Chamfer Width", min=0.001, max=0.5, default=0.05, step=1, precision=3
    )
    chamfer_height: FloatProperty(
        name="Chamfer Height", min=0.001, max=0.5, default=0.02, step=1, precision=3
    )
    chamfer_segments: IntProperty(
        name="Segments", min=1, max=10, default=1, description="Roundness of the chamfer"
    )

    # --- UI Layout ---
    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Flooring Settings", icon="MOD_BUILD")

        row = box.row()
        row.prop(self, "floor_style", expand=True)
        
        box.separator()
        
        col = box.column(align=True)
        col.prop(self, "tile_w", text="Tile Width")
        col.prop(self, "tile_l", text="Tile Length")
        col.prop(self, "tile_height", text="Extrusion Height")
        col.prop(self, "gap")
        
        box.separator()
        
        if self.floor_style == 'TILE':
            box = layout.box()
            box.label(text="Tile Specific", icon="GRID")
            col = box.column(align=True)
            col.prop(self, "tile_shape", text="Shape")
            col.prop(self, "stagger")
        else: # WOOD
            box = layout.box()
            box.label(text="Wood Specific", icon="OUTLINER_OB_LATTICE")
            col = box.column(align=True)
            col.label(text="Randomness:")
            col.prop(self, "seed")
            col.prop(self, "rand_len", text="Len Var")
            col.prop(self, "rand_stagger", text="Stagger Var")
            col.separator()
            col.label(text="Surface:")
            col.prop(self, "wood_subdiv", text="Segs")
            col.prop(self, "use_noise", text="Noise")
            if self.use_noise:
                 col.prop(self, "noise_str", text="Str")

        box.separator()

        # Chamfer UI (Button Style) - Moved to Bottom
        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "use_chamfer", toggle=True, text="Chamfer Top", icon='MOD_BEVEL')
        
        if self.use_chamfer:
            col = box.column(align=True)
            col.prop(self, "chamfer_width")
            col.prop(self, "chamfer_height")
            col.prop(self, "chamfer_segments")

    # --- Slot Protocol ---
    def get_slot_meta(self):
        return {
            0: {"name": "Tile_Top", "uv": "BOX", "phys": "CERAMIC_TILE"},
            1: {"name": "Grout", "uv": "SKIP", "phys": "CONCRETE_RAW"},
            2: {"name": "Wood_Plank", "uv": "BOX_LONG", "phys": "WOOD_OAK"},
        }

    # --- Generation Logic ---
    def build_shape(self, bm):
        # 0. Initialize Layers
        uv_layer = bm.loops.layers.uv.verify()
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # TAGGING LAYER (1=Grout, 0=Tile, 2=Wood)
        tag_layer = bm.faces.layers.int.new("MASSA_TYPE_TAG")
        
        # Seed Randomness (Local Scope)
        rng = random.Random(self.seed)

        # ==========================
        # STEP 1: CREATE FLOOR BASE
        # ==========================
        # Always create a base floor (Grout/Subfloor)
        s = self.area_size / 2
        grout_verts = [
            bm.verts.new((-s, -s, 0.0)),
            bm.verts.new((s, -s, 0.0)),
            bm.verts.new((s, s, 0.0)),
            bm.verts.new((-s, s, 0.0)),
        ]
        grout_face = bm.faces.new(grout_verts)
        grout_face[tag_layer] = 1  # ID: GROUT
        
        # Tag Grout Edges
        for e in grout_face.edges: e[edge_slots] = 1

        # Grout UVs
        grout_uvs = [(0, 0), (self.area_size, 0), (self.area_size, self.area_size), (0, self.area_size)]
        for loop, uv in zip(grout_face.loops, grout_uvs): loop[uv_layer].uv = uv

        # ==========================
        # STEP 2: GENERATE TILES/PLANKS
        # ==========================
        z_base = 0.001
        tiles = [] # List of faces

        # Helper: Create Hexagon
        def make_hex(cx, cy, radius):
            verts = []
            for i in range(6):
                ang = math.radians(60 * i + 30) # Pointy Top
                vx = cx + radius * math.cos(ang)
                vy = cy + radius * math.sin(ang)
                verts.append(bm.verts.new((vx, vy, z_base)))
            return bm.faces.new(verts)

        # --- BRANCH A: WOOD PLANKS (Row-Based) ---
        if self.floor_style == 'WOOD':
            # Horizontal Rows
            row_h = self.tile_w + self.gap
            # Generate extra rows to ensure coverage (Over-fill)
            rows = int(self.area_size / row_h) + 2 
            start_y = -self.area_size / 2 - row_h # Start slightly outside
            
            for r in range(rows):
                y = start_y + (r * row_h)
                
                # Loop Stagger
                stag_base = (r % 2) * self.stagger * self.tile_l
                stag_var = (rng.random() - 0.5) * self.tile_l * self.rand_stagger
                # Start Cursor far left to ensure fill
                x_cursor = -self.area_size/2 - self.tile_l + stag_base + stag_var 
                
                # Fill Row logic
                # Go until we pass the right edge completely
                while x_cursor < self.area_size/2 + self.tile_l:
                    # Determine Length
                    var = (rng.random() - 0.5) * self.tile_l * self.rand_len
                    plank_len = self.tile_l + var
                    if plank_len < 0.1: plank_len = 0.1
                    
                    x = x_cursor
                    
                    # Create Grid (for Subdivision) instead of simple face
                    # Using bmesh.ops.create_grid gives us internal vertices directly
                    # segments=(x, y)
                    seg_x = max(1, self.wood_subdiv[0])
                    seg_y = max(1, self.wood_subdiv[1])
                    
                    # Center of this plank
                    cx = x + plank_len/2
                    cy = y + self.tile_w/2
                    
                    plank_geom = bmesh.ops.create_grid(bm, x_segments=seg_x, y_segments=seg_y, size=0.5) # Size 0.5 spans -0.5 to 0.5 (Len 1)
                    p_verts = plank_geom['verts']
                    
                    # Scale to dimensions
                    bmesh.ops.scale(bm, vec=(plank_len, self.tile_w, 1), verts=p_verts)
                    # Move to Z base + XY Position
                    bmesh.ops.translate(bm, vec=(cx, cy, z_base), verts=p_verts)
                    
                    # Collect Faces
                    new_faces = []
                    for v in p_verts:
                        for f in v.link_faces:
                            f[tag_layer] = 2 # WOOD
                            new_faces.append(f)
                    tiles.extend(list(set(new_faces)))

                    x_cursor += plank_len + self.gap

        # --- BRANCH B: TILE (Grid/Hex) ---
        else:
            if self.tile_shape == 'HEX':
                # Hex Grid
                rad = self.tile_w / 2
                space_x = rad * math.sqrt(3) + self.gap
                space_y = rad * 1.5 + self.gap
                
                # Expand grid by 2-3 extra cols/rows to ensure coverage
                cols = int(self.area_size / space_x) + 4
                rows = int(self.area_size / space_y) + 4
                
                start_x = -self.area_size/2 - space_x
                start_y = -self.area_size/2 - space_y
                
                for r in range(rows):
                    y = start_y + r * space_y
                    offset = (space_x / 2) if r % 2 != 0 else 0
                    
                    for c in range(cols):
                        x = start_x + c * space_x + offset
                        f = make_hex(x, y, rad)
                        f[tag_layer] = 0 # TILE
                        tiles.append(f)
                            
            else: # RECT
                # Grid Overshoot
                rows = int(self.area_size / (self.tile_l + self.gap)) + 2
                cols = int(self.area_size / (self.tile_w + self.gap)) + 2
                start_x = -self.area_size / 2 - self.tile_w
                start_y = -self.area_size / 2 - self.tile_l

                for r in range(rows):
                    y = start_y + (r * (self.tile_l + self.gap))
                    offset_x = (self.tile_w + self.gap) * self.stagger if r % 2 != 0 else 0

                    for c in range(cols + 1):
                        x = start_x + (c * (self.tile_w + self.gap)) + offset_x - (self.tile_w * self.stagger)
                        
                        v1 = bm.verts.new((x, y, z_base))
                        v2 = bm.verts.new((x + self.tile_w, y, z_base))
                        v3 = bm.verts.new((x + self.tile_w, y + self.tile_l, z_base))
                        v4 = bm.verts.new((x, y + self.tile_l, z_base))
                        f = bm.faces.new((v1, v2, v3, v4))
                        f[tag_layer] = 0 # TILE
                        tiles.append(f)
        
        # ==========================
        # STEP 2.5: BOUNDARY TRIM (CUT LOGIC)
        # ==========================
        # Bisect at +/- bounds and remove OUTER geometry
        # Bounds: +/- self.area_size/2
        
        limit = self.area_size / 2
        
        # Planes: (Point, Normal)
        # Normals point OUTWARD from the valid center area.
        # clear_outer=True will remove the side the normal points to.
        planes = [
            (Vector((limit, 0, 0)), Vector((1, 0, 0))),   # Right (+X), Norm Right (+X) -> Remove > Limit
            (Vector((-limit, 0, 0)), Vector((-1, 0, 0))), # Left (-X), Norm Left (-X) -> Remove < -Limit
            (Vector((0, limit, 0)), Vector((0, 1, 0))),   # Back (+Y), Norm Back (+Y) -> Remove > Limit
            (Vector((0, -limit, 0)), Vector((0, -1, 0))), # Front (-Y), Norm Front (-Y) -> Remove < -Limit
        ]
        
        # We process 'tiles' (all 2D faces)
        # bmesh.ops.bisect_plane returns geom_cut (new verts/edges)
        # But we need to DELETE the stuff on the 'wrong' side.
        # Wait, bisect doesn't delete. It just cuts.
        # And bisect_plane with 'clear_check' or similar?
        # No, 'clear_outer' and 'clear_inner'.
        # We want to keep INNER. So clear_outer=True.
        # But we must be careful with Normals. 
        # If plane normal points OUT (away from center), then "Inner" is Center?
        # Let's standardize: Normal points INTO valid area.
        # Then clear_outer=True means "Remove stuff behind the normal".
        # Correct.
        
        # Collect all geoms (verts/edges/faces) relative to tiles
        # Actually, tiles is a list of FACES.
        # Just grab all geometry in the list.
        
        # The 'tiles' list might become invalid after bisect?
        # Yes, face references die.
        # Strategy: Select all generated verts, apply cut, then re-gather faces.
        
        valid_verts = list(set(v for f in tiles for v in f.verts))
        valid_edges = list(set(e for f in tiles for e in f.edges))
        valid_faces = list(set(tiles))
        valid_geom = valid_verts + valid_edges + valid_faces
        
        for pt, no in planes:
             ret = bmesh.ops.bisect_plane(
                bm, 
                geom=valid_geom, 
                dist=0.0001, 
                plane_co=pt, 
                plane_no=no, 
                clear_outer=True, # Remove stuff 'behind' normal
                clear_inner=False
            )
             # Update valid_geom because old refs might be dead or new ones created?
             # bisect_plane returns 'geom_cut' (new stuff).
             # But 'clear_outer' deletes stuff.
             # We should probably re-grab all relevant geometry.
             # Or just pass ALL (including deleted) and let bmesh handle it?
             # Better: refresh 'valid_geom' from the surviving faces with tag.
             
             # Re-finding geom:
             # Just assume we operate on the whole bmesh? 
             # No, we have Grout (Tag 1). We don't want to cut Grout (it matches area anyway).
             # But actually Grout IS the area. So cutting it doesn't hurt.
             # For safety, let's limit to Tile/Wood geometry if possible.
             # But bisecting subset of mesh is tricky if connected?
             # Tiles are disconnected from Grout (floating above z_base).
             # So we can filtering by Tag.
             
             current_geom = [f for f in bm.faces if f[tag_layer] in [0, 2]]
             current_edges = [e for f in current_geom for e in f.edges]
             current_verts = [v for f in current_geom for v in f.verts]
             valid_geom = list(set(current_geom + current_edges + current_verts))
             
             # If nothing left, break
             if not valid_geom: break
        
        # Re-populate 'tiles' list from surviving faces
        tiles = [f for f in bm.faces if f[tag_layer] in [0, 2]]
        
        # ==========================
        # STEP 2.6: NOISE (Wood Only)
        # ==========================
        if self.floor_style == 'WOOD' and self.use_noise and self.noise_str > 0:
            # Random Z displacement
            # Iterate unique verts in tiles
            wood_verts = list(set(v for f in tiles for v in f.verts))
            for v in wood_verts:
                # noise = rng range -0.5 to 0.5 * str
                nz = (rng.random() - 0.5) * self.noise_str
                v.co.z += nz

        # ==========================
        # STEP 3: UV MAPPING (Base Faces)
        # ==========================
        for f in tiles:
            for loop in f.loops:
                v_co = loop.vert.co
                # Simple Planar Map
                u = (v_co.x + self.area_size/2)
                v = (v_co.y + self.area_size/2)
                loop[uv_layer].uv = (u, v)

        # ==========================
        # STEP 4: EXTRUDE BODY
        # ==========================
        # Re-calc normals to ensure all point UP before extruding
        bmesh.ops.recalc_face_normals(bm, faces=tiles)
        
        # Verify direction: If normal is down, flip it?
        # Actually simplest is just to extrude, then filter 'Side' faces.
        
        ret = bmesh.ops.extrude_face_region(bm, geom=tiles)
        verts_ext = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
        faces_side = [f for f in ret["geom"] if isinstance(f, bmesh.types.BMFace)]
        
        # Tag Sides
        for f in faces_side:
            # Sides copy tag from neighbors? Or generic?
            # Let's check a linked face
            # Just default to 0 (Tile) or 2 (Wood) based on mode
            f[tag_layer] = 2 if self.floor_style == 'WOOD' else 0

        # Move up to height
        bmesh.ops.translate(bm, verts=verts_ext, vec=(0, 0, self.tile_height))
        
        # Identify Top Faces for Chamfer
        top_faces = []
        for f in bm.faces:
            # Must be Tile(0) or Wood(2) and Up-Pointing
            if f[tag_layer] in [0, 2] and f.normal.z > 0.5:
                top_faces.append(f)
        
        # Update tiles list to tops only
        tiles = top_faces

        # ==========================
        # STEP 4.1: UV SEAMS (Perimeter Only)
        # ==========================
        # Only mark outer perimeter if we are NOT chamfering.
        # If chamfering, the outer loop should be smooth (connected to side), 
        # and we seam the INNER loop instead.
        if not self.use_chamfer:
            # Convert top_faces to a set for fast lookup
            top_set = set(top_faces)
            
            for f in top_faces:
                for e in f.edges:
                    # Check neighbors
                    is_perimeter = False
                    if e.is_boundary:
                        is_perimeter = True
                    else:
                        # If any linked face is NOT in top_set, it's a boundary edge for the top group
                        if any(lf not in top_set for lf in e.link_faces):
                            is_perimeter = True
                    
                    if is_perimeter:
                        e.seam = True
                        e[edge_slots] = 2 # CONTOUR

        # ==========================
        # STEP 4.2: SEAM VERTICAL CORNERS
        # ==========================
        # Seam the 4 vertical corners of the tile block
        for f in top_faces:
             for v in f.verts:
                 for e in v.link_edges:
                     if e not in f.edges:
                         # Check verticality
                         vec = e.verts[1].co - e.verts[0].co
                         if abs(vec.z) > 0.01:
                             e.seam = True
                             e[edge_slots] = 2 

        # ==========================
        # STEP 4: STABLE CHAMFER LOOP
        # ==========================
        if self.use_chamfer:
            # 1. SAFETY CLAMP
            # Prevent Inset from crossing over itself (Math Explosion)
            safe_width = min(
                self.chamfer_width, (self.tile_w / 2) - 0.001, (self.tile_l / 2) - 0.001
            )

            # 2. ISOLATED PROCESSING
            # Instead of passing ALL faces to one operator, we loop.
            # This forces Blender to calculate each tile's inset locally and cleanly.

            # Ensure normals are perfect before we begin
            bmesh.ops.recalc_face_normals(bm, faces=top_faces)

            if self.floor_style == 'WOOD':
                # BATCH MODE for Wood (Grid)
                # Pass all faces together so internal seams are ignored
                # use_boundary=True is default, which is what we want (outer plank boundary only)
                ret = bmesh.ops.inset_region(
                    bm,
                    faces=top_faces,
                    thickness=safe_width,
                    depth=self.chamfer_height,
                    use_even_offset=True,
                    use_boundary=True,
                )
                # For Wood, we want to seam the CORNERS of the chamfer to break the frame?
                # Actually, effectively just seaming the Inner Top face works well.
                # Inspect return geom? 'faces' are the new ring faces? No, documentation varies.
                # Safer: Seam the edges of the NEW top faces (the inset result).
                
                # Identify the inner faces. They are the ones still pointing Up, and are subsets of original?
                # Actually, checking 'select' state or geometry tagging is best.
                # But let's look for edges that are part of the "Chamfer Slope" and are "Diagonal"?
                # Too complex.
                
                # SIMPLE FIX: Seam the INNER loop of the chamfer too.
                # This detaches the Top Face from the Chamfer Ring.
                # Then we have: Outer Seam (Done), Inner Seam (New).
                # The Chamfer Ring is now a separate "Frame".
                # User said "i dont want a bunch of hallow frames".
                # So we MUST cut the frame at the corners.
                
                # Strategy: Find edges that connect Outer Boundary to Inner Boundary.
                # These are edges with Length ~= chamfer_width (roughly).
                # And they are on top.
                
                # Re-evaluate top faces (Inner) using Normal and Tag
                # (Inset faces usually retain tag if input had it? Or we detect by Up Normal)
                current_tops = [f for f in bm.faces if f.normal.z > 0.9 and f[tag_layer] == 2]

                for f in current_tops:
                    # Seam Inner Loop
                    for e in f.edges:
                        e.seam = True
                        e[edge_slots] = 2

                    # Seam Connector Edges (Corners of the chamfer strip)
                    # Edges connected to f that slope down?
                    for v in f.verts:
                        for e in v.link_edges:
                            # If edge is NOT part of f (it goes out)
                            if e not in f.edges:
                                # It's a slope edge. Seam it.
                                e.seam = True
                                e[edge_slots] = 2

            else:
                # LOOP MODE for Tiles (Safe for islands)
                for f in top_faces:
                    # Capture face verts before inset isn't needed with Robust Logic
                    
                    ret = bmesh.ops.inset_region(
                        bm,
                        faces=[f],
                        thickness=safe_width,
                        depth=self.chamfer_height,
                        use_even_offset=True,
                        use_boundary=True,
                    )
                    
                    # f remains the Inner Face (Top)
                    
                    # Seam Inner Loop
                    for e in f.edges:
                        e.seam = True
                        e[edge_slots] = 2
                        
                    # Seam Corners (Robust Method)
                    for v in f.verts:
                        for e in v.link_edges:
                            if e not in f.edges:
                                # This is the chamfer corner
                                e.seam = True
                                e[edge_slots] = 2

        # ==========================
        # STEP 5: CLEANUP & ASSIGNMENT
        # ==========================
        # Delete Bottoms
        faces_to_delete = []
        for f in bm.faces:
            if (
                f[tag_layer] == 0
                and f.normal.z < -0.5
                and f.calc_center_median().z < (z_base + 0.001)
            ):
                faces_to_delete.append(f)
        bmesh.ops.delete(bm, geom=faces_to_delete, context="FACES")

        # SLOT ASSIGNMENT
        for f in bm.faces:
            type_id = f[tag_layer]

            if type_id == 1:
                # GROUT
                f.material_index = 1
            else:
                # TILE
                f.material_index = 0

                # Check normal for UV Mapping
                nz = f.normal.z

                if nz < 0.99:  # Side or Sloped Chamfer
                    # Mark Sharp
                    for e in f.edges:
                        e[edge_slots] = 2

                    # Box Map
                    is_x = abs(f.normal.y) > 0.5
                    for loop in f.loops:
                        v_co = loop.vert.co
                        u = v_co.x if is_x else v_co.y
                        v = v_co.z
                        loop[uv_layer].uv = (u, v)

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
