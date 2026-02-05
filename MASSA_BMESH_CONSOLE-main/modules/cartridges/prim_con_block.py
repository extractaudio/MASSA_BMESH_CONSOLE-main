import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty
from ...operators.massa_base import Massa_OT_Base

# ==============================================================================
# MASSA CARTRIDGE: CONSTRUCTION BLOCK (Y-AXIS ORIENTATION)
# ID: prim_con_block
# ==============================================================================

CARTRIDGE_META = {
    "name": "Con: Block",
    "id": "prim_con_block",
    "icon": "MESH_GRID",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_prim_con_block(Massa_OT_Base):
    """
    Operator to generate a primitive construction block (CMU style) with configurable cores,
    dimensions, and segmentation.
    """

    bl_idname = "massa.gen_prim_con_block"
    bl_label = "Construction Block"
    bl_description = "CMU with Holes along Y-Axis"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- Properties ---
    length: FloatProperty(name="Length", default=0.4, unit="LENGTH")
    width: FloatProperty(name="Width", default=0.2, unit="LENGTH")
    height: FloatProperty(name="Height", default=0.2, unit="LENGTH")
    wall_th: FloatProperty(name="Wall Thickness", default=0.035, unit="LENGTH")
    cores: IntProperty(name="Cores", default=2, min=1, max=3)

    # --- Topology / SubD Controls ---
    seg_x: IntProperty(name="Seg X", default=4, min=1, description="Length Cuts")
    seg_y: IntProperty(name="Seg Y", default=2, min=1, description="Width Cuts")
    seg_z: IntProperty(name="Seg Z", default=2, min=1, description="Height Cuts")

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Block Size", icon="CUBE")
        box.prop(self, "length")
        box.prop(self, "width")
        box.prop(self, "height")

        box = layout.box()
        box.label(text="Structure", icon="MOD_WIREFRAME")
        box.prop(self, "wall_th")
        box.prop(self, "cores")

        box = layout.box()
        box.label(text="SubD Topology", icon="MESH_GRID")
        row = box.row(align=True)
        row.prop(self, "seg_x", text="X")
        row.prop(self, "seg_y", text="Y")
        row.prop(self, "seg_z", text="Z")

    def get_slot_meta(self):
        # Update UV mode to UNWRAP for custom seaming
        return {0: {"name": "Concrete", "uv": "UNWRAP", "phys": "CONCRETE_BLOCK"}}

    def build_shape(self, bm):
        # 1. SETUP PARAMETERS
        l = getattr(self, "length", 0.4)
        w = getattr(self, "width", 0.2)  # Extrusion Depth (Y)
        h = getattr(self, "height", 0.2)  # Grid Height (Z)
        th = getattr(self, "wall_th", 0.035)

        cores = getattr(self, "cores", 2)
        seg_x = getattr(self, "seg_x", 4)
        seg_y = getattr(self, "seg_y", 2)
        seg_z = getattr(self, "seg_z", 2)

        # Calculate Core Dimensions (Along X)
        total_void_l = l - (th * (cores + 1))
        core_l = total_void_l / cores

        # 2. DEFINE BASE GRID (XZ Plane at Y=0)
        z_coords = [
            -h / 2,  # Bottom
            -h / 2 + th,  # Inner Bottom
            0.0,  # CENTERLINE (Z-Axis Slice)
            h / 2 - th,  # Inner Top
            h / 2,  # Top
        ]

        x_coords = []
        current_x = -l / 2
        x_coords.append(current_x)

        for i in range(cores):
            current_x += th
            x_coords.append(current_x)
            current_x += core_l
            x_coords.append(current_x)

        current_x += th
        x_coords.append(current_x)

        # 3. GENERATE VERTEX GRID (XZ Plane)
        grid_verts = []
        for x_val in x_coords:
            col = []
            for z_val in z_coords:
                col.append(bm.verts.new((x_val, 0, z_val)))
            grid_verts.append(col)

        # 4. SKINNING (XZ Faces)
        base_faces = []
        for i in range(len(x_coords) - 1):
            for j in range(len(z_coords) - 1):
                # Void Logic: X odd = Hole, Z middle (1,2) = Hole
                x_is_hole = i % 2 != 0
                z_is_hole = j == 1 or j == 2

                if not (x_is_hole and z_is_hole):
                    v1 = grid_verts[i][j]
                    v2 = grid_verts[i + 1][j]
                    v3 = grid_verts[i + 1][j + 1]
                    v4 = grid_verts[i][j + 1]
                    base_faces.append(bm.faces.new((v1, v2, v3, v4)))

        # 5. EXTRUDE (Y-Axis)
        ret = bmesh.ops.extrude_face_region(bm, geom=base_faces)
        geom_generated = ret["geom"]
        verts_extruded = [
            v for v in geom_generated if isinstance(v, bmesh.types.BMVert)
        ]

        # Move BASE verts to start position (-w/2)
        base_verts = [v for col in grid_verts for v in col]
        bmesh.ops.translate(bm, verts=base_verts, vec=(0, -w / 2, 0))

        # Move EXTRUDED verts to end position (+w/2)
        bmesh.ops.translate(bm, verts=verts_extruded, vec=(0, w, 0))

        # 6. SUBD SEGMENTATION PASS
        # Slice Length (X)
        if seg_x > 1:
            step = l / seg_x
            start = -l / 2
            for i in range(1, seg_x):
                bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    plane_co=(start + i * step, 0, 0),
                    plane_no=(1, 0, 0),
                )

        # Slice Width (Y)
        if seg_y > 1:
            step = w / seg_y
            start = -w / 2
            for i in range(1, seg_y):
                bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    plane_co=(0, start + i * step, 0),
                    plane_no=(0, 1, 0),
                )

        # Slice Height (Z)
        if seg_z > 1:
            step = h / seg_z
            start = -h / 2
            for i in range(1, seg_z):
                bmesh.ops.bisect_plane(
                    bm,
                    geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
                    plane_co=(0, 0, start + i * step),
                    plane_no=(0, 0, 1),
                )

        # 7. CLEANUP & NORMALS
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        # 8. SEAMING STRATEGY
        # Clear all seams first
        for e in bm.edges:
            e.seam = False

        # A. CAP IDENTIFICATION (Normal Y)
        # Caps are the Front (-Y) and Back (+Y) Faces.
        # We mark the perimeter of these faces as seams.
        # Note: Bisect might have split caps, so we look for any face with dominant Y normal.
        caps = [f for f in bm.faces if abs(f.normal.y) > 0.9]
        for f in caps:
            f.material_index = 1  # Standard specific slot? 1 is usually perimeter/secondary.
            for e in f.edges:
                e.seam = True

        # B. SMART LONGITUDINAL SPLIT
        # We bisect the entire geometry vertically (Plane X=0).
        # We ONLY mark the resulting edges as Seams if they are on "Downward" facing surfaces.
        # Effect:
        # - Outer Bottom Seal: Split (Hidden).
        # - Inner Void Ceilings: Split (Hidden inside top).
        # - Top Faces: Preserved (Clean).
        # - Void Floors: Preserved (Clean).
        
        ret = bmesh.ops.bisect_plane(
            bm,
            geom=bm.faces[:] + bm.edges[:] + bm.verts[:],
            plane_co=(0, 0, 0),
            plane_no=(1, 0, 0),
            clear_inner=False,
            clear_outer=False
        )
        
        cut_edges = [e for e in ret["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        
        for e in cut_edges:
            # Check adjacent faces. If ANY linked face is pointing DOWN (Z < -0.1), seam it.
            # Usually bisect edge links 2 faces.
            is_downward = False
            for f in e.link_faces:
                if f.normal.z < -0.1:
                    is_downward = True
                    break
            
            if is_downward:
                e.seam = True
        
        # 8C. FINAL CLEANUP
        # Remove doubles and zero-area faces before seaming
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        faces_small = [f for f in bm.faces if f.calc_area() < 0.000001]
        if faces_small:
             bmesh.ops.delete(bm, geom=faces_small, context='FACES')
        
        # 9. SEAMING STRATEGY (User Defined "Zipper & Rim")
        
        # A. CLEAR ALL
        for e in bm.edges:
            e.seam = False
            
        # B. RIMS (Top/Bottom Separation) - Full Island Separation
        # Mark ALL edges of Top Faces (Z-Up) and Bottom Faces (Z-Down)
        top_faces = [f for f in bm.faces if f.normal.z > 0.9]
        bot_faces = [f for f in bm.faces if f.normal.z < -0.9]
        
        for f in top_faces + bot_faces:
            for e in f.edges:
                e.seam = True
                
        # C. ZIPPER (Vertical Cut)
        # Find Vertical Edges (Z-aligned)
        # We need to cut at least one vertical line to unroll the "Wall Belt".
        # Heuristic: Find the Vertical Edge column with the LOWEST X (and Y).
        
        # 1. Collect all valid vertical edges
        vert_edges = []
        for e in bm.edges:
            # Check for Z-alignment (dx=0, dy=0, dz>0)
            dx = abs(e.verts[0].co.x - e.verts[1].co.x)
            dy = abs(e.verts[0].co.y - e.verts[1].co.y)
            dz = abs(e.verts[0].co.z - e.verts[1].co.z)
            
            if dx < 0.001 and dy < 0.001 and dz > 0.001:
                vert_edges.append(e)
                
        # 2. Group by location (XY) to identify "Pillars"
        # We want to seam the whole pillar (if segmented).
        # We use a simple Key: (round(x,4), round(y,4))
        pillars = {}
        for e in vert_edges:
            mid = (e.verts[0].co + e.verts[1].co) / 2
            key = (round(mid.x, 4), round(mid.y, 4))
            if key not in pillars:
                pillars[key] = []
            pillars[key].append(e)
            
        # 3. Select the "Zipper" Pillar (Lowest X, then Lowest Y)
        # We actually need one per loop (Outer + Inner Voids).
        # Current Heuristic: Select pillars that seem to be "Start" points.
        # Ideally, we cut 1 pillar for every connected component of the "Wall Projection"?
        # For now, adhering to user prompt: "Find the vertical edge with lowest X/Y... mark it Red".
        # We will sort all pillar keys and pick the absolute first one. 
        # CAUTION: This might leave inner voids closed. 
        # IMPROVEMENT: We pick the lowest X/Y pillar *for each unique X*? No.
        # Let's try to pick the "Bottom-Left" corner of EVERY rectangular structure.
        # This roughly maps to: For every unique X, pick the min Y? Or for every unique Y pick min X?
        # A generic Cinder block (2 cores) has:
        # Outer Box: 4 corners.
        # Inner Box 1: 4 corners.
        # Inner Box 2: 4 corners.
        # If we sort pillars, we can try to pick specific ones.
        # But for robustness, let's just pick the GLOBAL lowest X/Y for the outer, 
        # and maybe heuristic for inner?
        # Actually, let's just do the GLOBAL one as explicitly requested first. 
        
        if pillars:
            # Sort by X, then Y
            sorted_keys = sorted(pillars.keys(), key=lambda k: (k[0], k[1]))
            
            # Mark the "Winner" (Lowest X, then Y)
            zipper_key = sorted_keys[0]
            for e in pillars[zipper_key]:
                e.seam = True
                
            # AUTO-FIX: If we have Cores, we likely need to seam them too.
            # Cores usually start at slightly higher X than global min.
            # We can try to identify "Inner Loops" by checking for pillars that are corners > 90 deg?
            # Or just rely on the user's "Vertical Edge 1" instruction applying to the main form.
            # We will additionally seam any legacy bisect seams if they help? 
            # No, 'CLEAR ALL' removed them.
            
            # Let's add a heuristic for Inner Voids: Seam the "First Pillar" of any defined hole structure?
            # Logic: If we encounter a pillar that hasn't been seamed, and it belongs to a new "Zone"?
            # Complexity risk. Sticking to single zipper for now. 
            pass

        # 10. ASSIGN SLOTS (Colors)
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        for e in bm.edges:
            # SLOT 1 (RED): Seams
            if e.seam:
                e[edge_slots] = 1
            # SLOT 2 (CYAN): Sharp Edges (90 deg) that are NOT seams
            elif e.calc_face_angle() > math.radians(80):
                e[edge_slots] = 2
            # SLOT 3: Other
            else:
                 e[edge_slots] = 3

                
        # 10. UV UNWRAP
        headless_classic_unwrap(bm)


def headless_classic_unwrap(bm):
    """
    Flushes the BMesh to a temporary object / mesh, performs
    a standard bpy.ops.uv.unwrap (using the Context Override),
    and loads the result back into the BMesh.
    """
    # 1. Create Temp Mesh & Object
    me = bpy.data.meshes.new("_temp_unwrap_mesh_block")
    bm.to_mesh(me)
    
    obj = bpy.data.objects.new("_temp_unwrap_obj_block", me)
    col = bpy.data.collections.get("Collection")
    if not col:
        col = bpy.data.collections.new("Collection")
        bpy.context.scene.collection.children.link(col)
    col.objects.link(obj)
    
    # 2. Set Context
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    # 3. Enter Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    # 4. Unwrap
    # 'ANGLE_BASED' or 'CONFORMAL'. Margin 0.001 is standard.
    try:
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    except Exception as e:
        print(f"UNWRAP ERROR: {e}")
        
    # 5. Read Back
    bpy.ops.object.mode_set(mode='OBJECT')
    bm.clear()
    bm.from_mesh(me)
    
    # 6. Cleanup
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(me, do_unlink=True)
