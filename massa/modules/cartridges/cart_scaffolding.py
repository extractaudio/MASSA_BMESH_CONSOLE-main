import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty, BoolProperty
from mathutils import Vector, Matrix
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_properties import MassaPropertiesMixin

# ==============================================================================
# MASSA CARTRIDGE: SCAFFOLDING
# ID: cart_scaffolding
# ==============================================================================


CARTRIDGE_META = {
    "name": "Scaffolding",
    "id": "cart_scaffolding",
    "icon": "VIEW_PERSPECTIVE",
    "scale_class": "STANDARD",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": False,
    },
}


class MASSA_OT_Scaffolding(Massa_OT_Base, MassaPropertiesMixin):
    """
    Operator to generate Construction Scaffolding (H-Frame Towers).
    Uses Vector-aligned Cylinder Instancing.
    """

    bl_idname = "massa.gen_cart_scaffolding"
    bl_label = "Scaffolding"
    bl_description = "Construction Scaffolding Tower"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- Custom Properties ---
    width: FloatProperty(name="Width (X)", default=2.0, min=0.1, unit="LENGTH")
    depth: FloatProperty(name="Depth (Y)", default=1.0, min=0.1, unit="LENGTH")
    height: FloatProperty(name="Height (Z)", default=2.0, min=0.1, unit="LENGTH")
    
    pipe_radius: FloatProperty(name="Pipe Radius", default=0.04, min=0.001, unit="LENGTH")
    floors: IntProperty(name="Floors", default=1, min=1, max=20)
    
    strut_cuts: IntProperty(name="Post Cuts", default=0, min=0, max=10)
    plank_cuts: IntProperty(name="Board Cuts", default=0, min=0, max=10)
    
    use_x_brace: BoolProperty(name="X-Brace", default=True)
    use_planks: BoolProperty(name="Planks", default=True)
    use_wheels: BoolProperty(name="Wheels", default=False)

    # --- UI Draw ---
    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Dimensions", icon="CUBE")
        box.prop(self, "width")
        box.prop(self, "depth")
        box.prop(self, "height")
        box.prop(self, "floors")
        
        box.label(text="Details", icon="MESH_DATA")
        box.prop(self, "pipe_radius")
        box.prop(self, "strut_cuts")
        box.prop(self, "plank_cuts")
        
        box.label(text="Components", icon="MOD_BUILD")
        box.prop(self, "use_x_brace")
        box.prop(self, "use_planks")
        box.prop(self, "use_wheels")

    # --- Slot Protocol ---
    def get_slot_meta(self):
        return {
            0: {"name": "Metal Pipe", "uv": "BOX", "phys": "METAL_PAINTED"},
            1: {"name": "Wood Plank", "uv": "BOX", "phys": "WOOD_ROUGH"},
            2: {"name": "Joints/Details", "uv": "BOX", "phys": "METAL_RUST"},
            3: {"name": "Socket_Top", "uv": "SKIP", "phys": "GENERIC", "sock": True},
            4: {"name": "Rubber Wheel", "uv": "BOX", "phys": "RUBBER"},
            5: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
            6: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
            7: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
            8: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
            9: {"name": "EMPTY", "uv": "SKIP", "phys": "GENERIC"},
        }

    # --- Build Logic ---
    def build_shape(self, bm):
        
        # 0. Initialize Data Layers (Safety First)
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")

        # --- Helper: Create Strut ---
        def make_strut(v_start, v_end, radius, mat_idx=0):
            # 1. Vector Math
            vec = v_end - v_start
            length = vec.length
            if length < 0.001: return
            
            center = (v_start + v_end) * 0.5
            rot = Vector((0,0,1)).rotation_difference(vec)
            
            # 2. Geometry
            res = bmesh.ops.create_cone(
                bm, 
                cap_ends=True, 
                cap_tris=False, 
                segments=8, 
                radius1=radius, 
                radius2=radius, 
                depth=length
            )
            new_verts = res['verts']
            
            # 3. Material (Early Assignment)
            new_faces = {f for v in new_verts for f in v.link_faces}
            for f in new_faces:
                f.material_index = mat_idx
                
            # 4. Transform (BEFORE Subdivision)
            mat_loc = Matrix.Translation(center)
            mat_rot = rot.to_matrix().to_4x4()
            mat_final = mat_loc @ mat_rot
            bmesh.ops.transform(bm, verts=new_verts, matrix=mat_final)
            
            # 5. Segmentation (Manual Count)
            if self.strut_cuts > 0:
                new_edges = {e for v in new_verts for e in v.link_edges}
                v_edges = [e for e in new_edges if e.calc_length() > length * 0.9]
                
                if v_edges:
                    ret_sub = bmesh.ops.subdivide_edges(
                        bm,
                        edges=v_edges,
                        cuts=self.strut_cuts,
                        use_grid_fill=True
                    )
                    
                    # Mark Seams on Loops
                    for ele in ret_sub['geom_inner']:
                        if isinstance(ele, bmesh.types.BMEdge):
                            ele[edge_slots] = 1

        # --- Helper: Create Plank ---
        def make_plank(center, size, mat_idx=1):
            res = bmesh.ops.create_cube(bm, size=1.0)
            verts = res['verts']
            
            # 1. Scale & Move
            bmesh.ops.scale(bm, vec=size, verts=verts)
            bmesh.ops.translate(bm, vec=center, verts=verts)
            
            # 2. Material
            new_faces = {f for v in verts for f in v.link_faces}
            for f in new_faces:
                f.material_index = mat_idx
                
            # 3. Smart Seams & Segmentation
            # Find Longest Axis
            max_len = max(size.x, size.y, size.z)
            axis_idx = 0
            if size.y == max_len: axis_idx = 1
            if size.z == max_len: axis_idx = 2
            
            p_edges = {e for v in verts for e in v.link_edges}
            
            # A. Segmentation
            if self.plank_cuts > 0:
                # Find edges parallel to Long Axis
                # Since created axis-aligned, checking vector component is reliable enough
                long_edges = []
                for e in p_edges:
                    v_e = (e.verts[1].co - e.verts[0].co)
                    if abs(v_e[axis_idx]) > max_len * 0.9:
                        long_edges.append(e)
                
                if long_edges:
                    ret_sub = bmesh.ops.subdivide_edges(
                        bm, 
                        edges=long_edges, 
                        cuts=self.plank_cuts, 
                        use_grid_fill=True
                    )
                    # Add new geometry to p_edges set for seam logic
                    # Simplify: Just re-gather all edges connected to these faces
                    # Or relying on 'geom_inner' for the cuts
                    for ele in ret_sub['geom_inner']:
                        if isinstance(ele, bmesh.types.BMEdge):
                            p_edges.add(ele) # Add inner cuts to potential seam list
            
            # B. Seams (Mark All Perpendicular Edges)
            # This isolates Ends and Segments
            for e in p_edges:
                v_e = (e.verts[1].co - e.verts[0].co)
                # If length along main axis is small -> It's a cross edge -> Seam
                if abs(v_e[axis_idx]) < max_len * 0.1: # Threshold for "perpendicular"
                     e[edge_slots] = 1

        # ======================================================================
        # BUILD LOOP
        # ======================================================================
        
        w = self.width
        d = self.depth
        h = self.height
        r = self.pipe_radius
        
        # Iteration
        for i in range(self.floors):
            base_z = i * h
            
            # --- POINTS ---
            # Frame A (Left: -X)
            p_a_bott_fwd = Vector((-w/2, -d/2, base_z))
            p_a_bott_bck = Vector((-w/2,  d/2, base_z))
            p_a_top_fwd  = Vector((-w/2, -d/2, base_z + h))
            p_a_top_bck  = Vector((-w/2,  d/2, base_z + h))
            
            # Frame B (Right: +X)
            p_b_bott_fwd = Vector(( w/2, -d/2, base_z))
            p_b_bott_bck = Vector(( w/2,  d/2, base_z))
            p_b_top_fwd  = Vector(( w/2, -d/2, base_z + h))
            p_b_top_bck  = Vector(( w/2,  d/2, base_z + h))
            
            # --- STRUCTURE ---
            
            # 1. Vertical Posts (4x)
            make_strut(p_a_bott_fwd, p_a_top_fwd, r, 0) # A Fwd
            make_strut(p_a_bott_bck, p_a_top_bck, r, 0) # A Bck
            make_strut(p_b_bott_fwd, p_b_top_fwd, r, 0) # B Fwd
            make_strut(p_b_bott_bck, p_b_top_bck, r, 0) # B Bck
            
            # 2. Horizontal Rungs (H-Frame connections) (Top and Bottom)
            # Bottom Rungs (at 10% height to avoid ground intersection if needed, or 0)
            # Standard scaffold has bottom rung near ground.
            rung_z_bott = base_z + (h * 0.1)
            rung_z_top  = base_z + (h * 0.9)
            
            # Offsets for rungs to fit Inside verticals? Or simple center-to-center?
            # Center-to-center is easiest for low poly.
            
            # Left Frame Top/Bottom
            make_strut(Vector((-w/2, -d/2, rung_z_bott)), Vector((-w/2, d/2, rung_z_bott)), r*0.8, 0)
            make_strut(Vector((-w/2, -d/2, rung_z_top)), Vector((-w/2, d/2, rung_z_top)), r*0.8, 0)
            
            # Right Frame Top/Bottom
            make_strut(Vector(( w/2, -d/2, rung_z_bott)), Vector(( w/2, d/2, rung_z_bott)), r*0.8, 0)
            make_strut(Vector(( w/2, -d/2, rung_z_top)), Vector(( w/2, d/2, rung_z_top)), r*0.8, 0)
            
            # 3. Cross Braces (Long side X)
            if self.use_x_brace:
                # X on Front Face (-Y) ? Or Side (+X)?
                # Scaffolding connects the two FRAMES (Left/Right) with X braces.
                # Connection is from A to B.
                
                # Front X
                make_strut(Vector((-w/2, -d/2, rung_z_bott)), Vector(( w/2, -d/2, rung_z_top)), r*0.6, 0)
                make_strut(Vector((-w/2, -d/2, rung_z_top)), Vector(( w/2, -d/2, rung_z_bott)), r*0.6, 0)
                
                # Back X
                make_strut(Vector((-w/2,  d/2, rung_z_bott)), Vector(( w/2,  d/2, rung_z_top)), r*0.6, 0)
                make_strut(Vector((-w/2,  d/2, rung_z_top)), Vector(( w/2,  d/2, rung_z_bott)), r*0.6, 0)

            # 4. Planks
            if self.use_planks:
                # Planks rest on the Top Rungs.
                # Span X axis.
                # Size: Width, PlankDepth, Thickness
                # How many planks? Fill the Depth.
                
                plank_thick = 0.05
                plank_gap = 0.02
                usable_depth = d - (r * 4) # inset slightly
                num_planks = 3
                p_depth = (usable_depth / num_planks) - plank_gap
                
                start_y = -usable_depth/2 + p_depth/2
                
                for p in range(num_planks):
                    y_pos = start_y + (p * (p_depth + plank_gap))
                    
                    center = Vector((0, y_pos, rung_z_top + r + plank_thick/2))
                    size = Vector((w + (r*2), p_depth, plank_thick))
                    
                    make_plank(center, size, 1)

        # 5. Wheels (Bottom Floor Only)
        if self.use_wheels:
            # Simple Cylinder Wheels at bottom of 1st floor posts
            # wheel_r = r * 3 (Unused)
            # wheel_w = r * 2 (Unused)
            
            # Centers
            posts = [
                Vector((-w/2, -d/2, 0)),
                Vector((-w/2,  d/2, 0)),
                Vector(( w/2, -d/2, 0)),
                Vector(( w/2,  d/2, 0))
            ]
            
            for p in posts:
                # Wheel Hub
                # Rotate cylinder to lie on Y axis
                # Actually, simplest representation: Vertical cylinder (caster) + Horizontal cylinder (wheel)
                # Just a simple vertical extension for now
                make_strut(p, p - Vector((0,0,0.2)), r, 4) # Stem
                # Wheel TODO

        # 6. EDGE ROLE INTERPRETER
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots:
            edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
            
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        for e in bm.edges:
            # Angle Check for Cylinder Caps
            angle = e.calc_face_angle(0)
            if angle > 1.5: # Sharp edges (Caps/Box edges)
                e[edge_slots] = 1 # Perimeter
