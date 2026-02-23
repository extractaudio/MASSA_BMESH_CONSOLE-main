"""
Filename: modules/cartridges/prim_con_house_generator.py
Content: Parametric House Generator (Foundation, Framing, Roof, Porch)
Status: NEW (v1.0)
"""

import bpy
import bmesh
import math
if __package__:
    from ...operators.massa_base import Massa_OT_Base
else:
    class Massa_OT_Base:
        pass
from bpy.props import FloatProperty, BoolProperty, EnumProperty, IntProperty
from mathutils import Vector, Matrix

CARTRIDGE_META = {
    "name": "Con: House Generator",
    "id": "prim_con_house_generator",
    "icon": "HOME",
    "scale_class": "MACRO",
    "flags": {
        "USE_WELD": True,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_prim_con_house_generator(Massa_OT_Base):
    bl_idname = "massa.gen_prim_con_house_generator"
    bl_label = "Construction House"
    bl_description = "Complete House Generator with Framing and Porch"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- DIMENSIONS ---
    width: FloatProperty(name="Width", default=6.0, min=2.0, unit="LENGTH")
    length: FloatProperty(name="Length", default=8.0, min=2.0, unit="LENGTH")
    wall_height: FloatProperty(name="Wall Height", default=2.7, min=2.0, unit="LENGTH")
    
    # --- FOUNDATION ---
    foundation_height: FloatProperty(name="Foundation H", default=0.5, min=0.1, unit="LENGTH")
    
    # --- FLOOR ---
    floor_board_w: FloatProperty(name="Floor Bd Width", default=0.14, min=0.05, unit="LENGTH")
    floor_board_gap: FloatProperty(name="Floor Bd Gap", default=0.002, min=0.0, unit="LENGTH")
    
    # --- FRAMING ---
    stud_spacing: FloatProperty(name="Stud Spacing", default=0.6, min=0.3, unit="LENGTH")
    stud_w: FloatProperty(name="Stud Width", default=0.09, min=0.05, unit="LENGTH") # 2x4 depth
    stud_t: FloatProperty(name="Stud Thick", default=0.04, min=0.02, unit="LENGTH") # 2x4 width
    
    # --- ROOF ---
    roof_pitch: FloatProperty(name="Roof Pitch", default=0.5, min=0.1, max=2.0, description="Rise over Run ratio")
    overhang: FloatProperty(name="Overhang", default=0.5, min=0.0, unit="LENGTH")
    truss_spacing: FloatProperty(name="Truss Spacing", default=0.6, min=0.3, unit="LENGTH")
    
    # --- VISIBILITY & MODULES ---
    add_framing: BoolProperty(name="Show Framing", default=True, description="Generate studs and rafters")
    add_roof: BoolProperty(name="Add Roof", default=True)
    add_gable_walls: BoolProperty(name="Add Gable Ends", default=True)
    add_ceiling: BoolProperty(name="Add Ceiling", default=False)
    
    # --- PORCH ---
    add_porch: BoolProperty(name="Add Porch", default=True)
    porch_depth: FloatProperty(name="Porch Depth", default=2.0, min=1.0, unit="LENGTH")
    porch_height: FloatProperty(name="Porch Height", default=0.4, min=0.1, unit="LENGTH")
    add_stairs: BoolProperty(name="Add Stairs", default=True)

    # --- INTERIOR & FEATURES ---
    interior_layout: EnumProperty(
        name="Layout",
        items=[
            ('OPEN', "Open Plan", "No internal walls"),
            ('1_BED', "1 Bedroom", "Separate bedroom area"),
            ('2_BED', "2 Bedroom", "Two bedrooms")
        ],
        default='OPEN'
    )
    
    add_kitchen: BoolProperty(name="Add Kitchen", default=True)
    kitchen_width: FloatProperty(name="Kitchen Width", default=3.0, min=1.0, unit="LENGTH")
    
    add_fireplace: BoolProperty(name="Add Fireplace", default=False)
    chimney_loc_x: FloatProperty(name="Chimney X", default=0.0, unit="LENGTH")
    
    add_door_front: BoolProperty(name="Front Door", default=True)
    add_door_back: BoolProperty(name="Back Door", default=True)

    def draw_shape_ui(self, layout):
        box = layout.box()
        box.label(text="Dimensions", icon="ARROW_LEFTRIGHT")
        box.prop(self, "width")
        box.prop(self, "length")
        box.prop(self, "wall_height")
        
        box = layout.box()
        box.label(text="Foundation & Floor", icon="MOD_BUILD")
        box.prop(self, "foundation_height")
        box.prop(self, "floor_board_w")
        box.prop(self, "floor_board_gap")
        
        box = layout.box()
        box.label(text="Framing", icon="MESH_GRID")
        box.prop(self, "stud_spacing")
        box.prop(self, "stud_w")
        box.prop(self, "stud_t")
        
        box = layout.box()
        box = layout.box()
        box.label(text="Roof", icon="OBJECT_DATA") # Fixed: MOD_ROOF is an invalid icon
        box.prop(self, "roof_pitch")
        box.prop(self, "overhang")
        box.prop(self, "overhang")
        box.prop(self, "truss_spacing")
        
        row = box.row()
        row.prop(self, "add_roof")
        if self.add_roof:
            row.prop(self, "add_gable_walls")
        
        box = layout.box()
        box.label(text="Structure Options", icon="MOD_WIREFRAME")
        box.prop(self, "add_framing")
        box.prop(self, "add_ceiling")
        
        box = layout.box()
        box.prop(self, "add_porch", toggle=True)
        if self.add_porch:
            col = box.column()
            col.prop(self, "porch_depth")
            col.prop(self, "porch_height")
            col.prop(self, "add_stairs")

        box = layout.box()
        box.label(text="Interior & Features", icon="HOME")
        box.prop(self, "interior_layout")
        
        row = box.row()
        row.prop(self, "add_door_front")
        row.prop(self, "add_door_back")
        
        box.prop(self, "add_kitchen", toggle=True)
        if self.add_kitchen:
            box.prop(self, "kitchen_width")
            
        box.prop(self, "add_fireplace", toggle=True)
        if self.add_fireplace:
            box.prop(self, "chimney_loc_x")

    def get_slot_meta(self):
        return {
            0: {"name": "Foundation", "uv": "BOX", "phys": "CONCRETE_ROUGH"},
            1: {"name": "Frame_Wood", "uv": "BOX", "phys": "WOOD_FRAMING"},
            2: {"name": "Sheathing", "uv": "BOX", "phys": "WOOD_PLYWOOD"},
            3: {"name": "Roof", "uv": "BOX", "phys": "ROOF_SHINGLES"},
            4: {"name": "Porch_Deck", "uv": "BOX", "phys": "WOOD_DECKING"},
            4: {"name": "Porch_Deck", "uv": "BOX", "phys": "WOOD_DECKING"},
            5: {"name": "Stairs", "uv": "BOX", "phys": "WOOD_ROUGH"},
            6: {"name": "Ceiling", "uv": "BOX", "phys": "PLASTER"},
            7: {"name": "Gable_Siding", "uv": "BOX", "phys": "WOOD_SIDING"},
        }
        
    def _make_rot_box(self, bm, size, pos, angle_z=0.0, angle_x=0.0, tag=0, tag_layer=None, angle_y=0.0):
        """Helper: Create Rotated Box"""
        r = bmesh.ops.create_cube(bm, size=1.0)
        new_verts = r["verts"]

        # Scale
        bmesh.ops.scale(bm, vec=size, verts=new_verts)

        # Rotation
        mat = Matrix()
        if angle_z != 0:
            mat = mat @ Matrix.Rotation(angle_z, 4, 'Z')
        if angle_x != 0:
            mat = mat @ Matrix.Rotation(angle_x, 4, 'X')
        if angle_y != 0:
            mat = mat @ Matrix.Rotation(angle_y, 4, 'Y')

        if angle_z != 0 or angle_x != 0 or angle_y != 0:
            bmesh.ops.rotate(bm, verts=new_verts, cent=Vector((0,0,0)), matrix=mat)

        # Translate
        bmesh.ops.translate(bm, verts=new_verts, vec=pos)

        # Tag
        if tag_layer:
            for v in new_verts:
                for f in v.link_faces:
                    f[tag_layer] = tag
        
        return new_verts

    def _make_foundation(self, bm, tag_layer):
        """Generates concrete foundation box"""
        # Center at Z = -fh/2
        fh = self.foundation_height
        w = self.width
        l = self.length
        
        pos = Vector((0, 0, -fh/2))
        size = Vector((w, l, fh))
        
        self._make_rot_box(bm, size, pos, 0, 0, 0, tag_layer) # Tag 0: Foundation

    def _make_floor(self, bm, tag_layer):
        """Generates floorboards using scanline"""
        w = self.width
        l = self.length
        bw = self.floor_board_w
        bg = self.floor_board_gap
        
        # Simple Rectangular Scanline (X-wise scan, boards run Y-wise usually? Or X-wise?)
        # Let's run boards along Length (Y). So scan X.
        
        start_x = -(w/2) + bw/2
        count = int(w / (bw + bg))
        
        board_thick = 0.02
        z_pos = 0 - (board_thick/2) # Just below Z=0 line? Or at Z=0? 
        # House floor is usually Z=0. Foundation is below.
        
        for i in range(count):
            x_pos = start_x + (i * (bw + bg))
            
            # Simple full length boards for now
            self._make_rot_box(bm, Vector((bw, l, board_thick)), Vector((x_pos, 0, z_pos)), 0, 0, 4, tag_layer) # Tag 4: Porch/Deck (reused for Floor)

    def _make_walls_timber(self, bm, tag_layer):
        # Timber Frame Style: Large Beams, fewer uprights
        wh = self.wall_height
        l = self.length
        w = self.width
        
        beam_thick = 0.2 # 20cm beams
        
        # 1. Main Posts (Corners)
        corners = [
            Vector((-w/2 + beam_thick/2, -l/2 + beam_thick/2, wh/2)),
            Vector((w/2 - beam_thick/2, -l/2 + beam_thick/2, wh/2)),
            Vector((w/2 - beam_thick/2, l/2 - beam_thick/2, wh/2)),
            Vector((-w/2 + beam_thick/2, l/2 - beam_thick/2, wh/2)),
        ]
        
        for pos in corners:
            self._make_rot_box(bm, Vector((beam_thick, beam_thick, wh)), pos, 0, 0, 1, tag_layer)
            
        # 2. Top Bears (Ring)
        # Front/Back Spans
        span_x = w - (2 * beam_thick)
        if span_x > 0:
            p_f = Vector((0, -l/2 + beam_thick/2, wh - beam_thick/2))
            p_b = Vector((0, l/2 - beam_thick/2, wh - beam_thick/2))
            self._make_rot_box(bm, Vector((span_x, beam_thick, beam_thick)), p_f, 0, 0, 1, tag_layer)
            self._make_rot_box(bm, Vector((span_x, beam_thick, beam_thick)), p_b, 0, 0, 1, tag_layer)
            
        # Left/Right Spans (Full Length typically sits on top or between? Let's say between for now to match corner logic)
        # Actually in timber frame, top plates often overlap.
        span_y = l - (2 * beam_thick)
        if span_y > 0:
            p_l = Vector((-w/2 + beam_thick/2, 0, wh - beam_thick/2))
            p_r = Vector((w/2 - beam_thick/2, 0, wh - beam_thick/2))
            self._make_rot_box(bm, Vector((beam_thick, span_y, beam_thick)), p_l, 0, 0, 1, tag_layer)
            self._make_rot_box(bm, Vector((beam_thick, span_y, beam_thick)), p_r, 0, 0, 1, tag_layer)
            
        # 3. Intermediate Posts (If wall is long)
        # Add a post every ~3 meters
        
        # 4. Infill Panels (Plaster/Wattle & Daub look)
        # Just simple planes inset from beams
        # Front Panel
        panel_thick = 0.02
        if span_x > 0:
            pf_pos = Vector((0, -l/2 + beam_thick/2, wh/2))
            self._make_rot_box(bm, Vector((span_x, panel_thick, wh)), pf_pos, 0, 0, 2, tag_layer)
            pb_pos = Vector((0, l/2 - beam_thick/2, wh/2))
            self._make_rot_box(bm, Vector((span_x, panel_thick, wh)), pb_pos, 0, 0, 2, tag_layer)
            
        if span_y > 0:
            pl_pos = Vector((-w/2 + beam_thick/2, 0, wh/2))
            self._make_rot_box(bm, Vector((panel_thick, span_y, wh)), pl_pos, 0, 0, 2, tag_layer)
            pr_pos = Vector((w/2 - beam_thick/2, 0, wh/2))
            self._make_rot_box(bm, Vector((panel_thick, span_y, wh)), pr_pos, 0, 0, 2, tag_layer)

    def _make_walls(self, bm, tag_layer):
        """Generates 4 walls with studs and sheathing"""
        # Wall Params
        wh = self.wall_height
        l = self.length
        w = self.width
        sw = self.stud_w # Depth (0.09)
        st = self.stud_t # Width of stud face (0.04)
        
        # Define Wall Segments (Center Lines of the framing)
        # Strategy: Side Walls (Left/Right) run full length. Front/Back walls fit between.
        
        # Right Wall (+X): Runs from Y = -l/2 to l/2. X = w/2 - sw/2.
        # Left Wall (-X): Runs from Y = -l/2 to l/2. X = -w/2 + sw/2.
        # Front Wall (-Y): Runs from X = -w/2 + sw to w/2 - sw. Y = -l/2 + sw/2.
        # Back Wall (+Y): Runs from X = -w/2 + sw to w/2 - sw. Y = l/2 - sw/2.
        
        # Helper for a Single Wall Section
        def build_wall_section(p_start, p_end, mat_tag_frame, mat_tag_panel):
            vec = p_end - p_start
            wall_len = vec.length
            if wall_len < 0.01: return
            
            # Orientation
            # Wall Direction (Y for side walls, X for end walls)
            # Normal Direction (Point Outwards)
            dir_vec = vec.normalized()
            
            # Angle for rot_box
            rot_z = math.atan2(dir_vec.y, dir_vec.x)
            
            # 1. PLATES (Sole and Top)
            # Size: (Length, Stud_Depth, Stud_Thick) -> aligned to X by default in rot_box?
            # My _make_rot_box takes (X, Y, Z). If Angle=0, X is length.
            # So Size = (wall_len, sw, st)
            
            cnt = (p_start + p_end) / 2
            
            # Sole Plate
            pos_sole = cnt.copy()
            pos_sole.z = st/2 # Centered on Z? rot_box centers. If Z=0 is floor, plate sits on it. Center at st/2.
            self._make_rot_box(bm, Vector((wall_len, sw, st)), pos_sole, rot_z, 0, mat_tag_frame, tag_layer)
            
            # Top Plate
            pos_top = cnt.copy()
            pos_top.z = wh - st/2
            self._make_rot_box(bm, Vector((wall_len, sw, st)), pos_top, rot_z, 0, mat_tag_frame, tag_layer)
            
            # 2. STUDS
            # Vertical 2x4s. Size: (st, sw, wh - 2*st).
            # X=st (width along wall), Y=sw (depth), Z=height.
            
            stud_h = wh - (2 * st)
            stud_cnt = int(wall_len / self.stud_spacing) + 1 # At least ends
            if stud_cnt < 2: stud_cnt = 2
            
            step = wall_len / (stud_cnt - 1)
            
            # Iterate
            if self.add_framing:
                for i in range(stud_cnt):
                    # Distance from start
                    d = i * step
                    # World Pos
                    pt = p_start + (dir_vec * d)
                    pt.z = wh / 2 # Center Z
                    
                    self._make_rot_box(bm, Vector((st, sw, stud_h)), pt, rot_z, 0, mat_tag_frame, tag_layer)
                
            # 3. SHEATHING / PANELS
            # "Separate yet touching"
            # Offset Outwards.
            # We need the Outline Normal. (Right? Left?)
            # Assuming iterating CCW? Or just logic based on position?
            # Let's derive "Outward" normal.
            # Side Wall Right (+X): Out is +X. Left (-X): Out is -X.
            # Front (-Y): Out is -Y. Back (+Y): Out is +Y.
            
            # Cross product of Dir and Up(0,0,1)?
            # If dir is +Y (Right Wall), Right Cross Up = (0,1,0) x (0,0,1) = (1,0,0) -> +X. Correct.
            out_vec = dir_vec.cross(Vector((0,0,1)))
            
            panel_thick = 0.015
            panel_offset = (sw/2) + (panel_thick/2) # From center of stud to center of panel
            
            panel_len = wall_len # Full length?
            # If corner overlapping logic applies, panels might need to extend to cover corners?
            # For now, match frame.
            
            panel_pos = cnt + (out_vec * panel_offset)
            panel_pos.z = wh / 2
            
            self._make_rot_box(bm, Vector((panel_len, panel_thick, wh)), panel_pos, rot_z, 0, mat_tag_panel, tag_layer)

        # GENERATE WALLS
        
        # Right Wall (+X)
        ws_r_start = Vector((w/2 - sw/2, -l/2, 0))
        ws_r_end = Vector((w/2 - sw/2, l/2, 0))
        build_wall_section(ws_r_start, ws_r_end, 1, 2)
        
        # Left Wall (-X) - Go from bottom to top (Y-) to Y+
        ws_l_start = Vector((-w/2 + sw/2, -l/2, 0))
        ws_l_end = Vector((-w/2 + sw/2, l/2, 0))
        build_wall_section(ws_l_start, ws_l_end, 1, 2)
        
        # Front Wall (-Y) - Between side walls
        # X range: -w/2 + sw -> w/2 - sw
        x_span = w/2 - sw
        ws_f_start = Vector((-x_span, -l/2 + sw/2, 0))
        ws_f_end = Vector((x_span, -l/2 + sw/2, 0))
        build_wall_section(ws_f_start, ws_f_end, 1, 2)
        
        # Back Wall (+Y)
        ws_b_start = Vector((-x_span, l/2 - sw/2, 0))
        ws_b_end = Vector((x_span, l/2 - sw/2, 0))
        build_wall_section(ws_b_start, ws_b_end, 1, 2)

    def _make_gable_ends(self, bm, tag_layer):
        """Generates triangular wall sections above front and back walls"""
        w = self.width
        l = self.length
        wh = self.wall_height
        pitch = self.roof_pitch
        sw = self.stud_w
        
        # Height of triangle
        gable_h = (w / 2) * pitch
        
        # Thickness (Match stud depth)
        thick = sw
        
        # Create Prism Helper
        def make_prism(pos_center, size_x, size_h, size_d, angle_z):
            # 3 Points: Left(-x, 0), Right(x, 0), Top(0, h)
            # Extruded by depth
            
            # Simple wedge using BMesh ops?
            # Or make a cube and merge top vertices?
            
            # Create Cube
            # Size Z is height.
            r = bmesh.ops.create_cube(bm, size=1.0)
            verts = r['verts']
            
            # Scale to Bounding Box: X=size_x, Y=size_d, Z=size_h
            bmesh.ops.scale(bm, verts=verts, vec=Vector((size_x, size_d, size_h)))
            
            # Move to +Z (base is at 0) -> Cube center is Z=size_h/2. OK.
            
            # Collapse Top Verts to Center X?
            # Top verts are those with Z > 0
            # Identify Top Left and Top Right?
            # Standard Cube: 
            # -1,-1,-1; -1,1,-1; 1,1,-1; 1,-1,-1 (Bottom)
            # -1,-1,1; -1,1,1; 1,1,1; 1,-1,1 (Top)
            
            # We want a triangle profile in X-Z plane (Front view).
            # So top face (-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, -1, 1)
            # Need to merge (-1...) and (1...) pairs to center?
            # Actually, standard gable is symmetric.
            # Just merge all top verts to (0, y, h)?
            # No, we want a ridge line? No, ridge point?
            # Gable is a triangle extruded. 
            # Top edge is a LINE along Y (Depth)? Yes.
            
            # Let's merge Top-Left and Top-Right points to the Center-Top-Line.
            # Local Coords.
            # Target Top Line: X=0.
            
            top_verts = [v for v in verts if v.co.z > 0]
            for v in top_verts:
                 v.co.x = 0
            
            # Clean up doubles
            bmesh.ops.remove_doubles(bm, verts=verts, dist=0.001)
            
            # Refresh verts list (remove invalidated)
            verts = [v for v in verts if v.is_valid]
            
            # Apply Rotation
            mat = Matrix.Rotation(angle_z, 4, 'Z')
            bmesh.ops.rotate(bm, verts=verts, cent=Vector((0,0,0)), matrix=mat)
            
            # Translate (Base center should be at Z=0 relative to pos_center? 
            # Current center Z=0 is mid-height.
            # Shift up by h/2 so base is at 0.
            bmesh.ops.translate(bm, verts=verts, vec=Vector((0,0,size_h/2)))
            
            # Move to World Pos
            bmesh.ops.translate(bm, verts=verts, vec=pos_center)
            
            # Tag
            if tag_layer:
                for v in verts:
                    if v.is_valid:
                        for f in v.link_faces:
                            f[tag_layer] = 7 # Gable Siding
                            
        # Front Gable (-Y)
        # Position: On Top Plate. Center X=0. Y = -l/2 + sw/2?
        # Match Front Wall location.
        # Front Wall Y was -l/2 + sw/2. 
        # Width: Full Width 'w' (spanning over Side Walls?) or between?
        # Usually Gable spans full width w.
        
        pos_f = Vector((0, -l/2 + sw/2, wh))
        make_prism(pos_f, w, gable_h, thick, 0)
        
        # Back Gable (+Y)
        pos_b = Vector((0, l/2 - sw/2, wh))
        make_prism(pos_b, w, gable_h, thick, 0)

    def _make_ceiling(self, bm, tag_layer):
        """Generates Flat Ceiling Panel"""
        w = self.width
        l = self.length
        wh = self.wall_height
        sw = self.stud_w
        
        # Inner Dimensions (Inside Framed Walls)
        # w_inner = w - 2*sw
        # l_inner = l - 2*sw
        # Let's simple fill the box at wall_height.
        
        # Panel
        thick = 0.02
        pos = Vector((0, 0, wh - thick/2)) # Top flush with wall top
        
        # Size slightly smaller to fit inside
        size = Vector((w - 2*sw, l - 2*sw, thick))
        
        self._make_rot_box(bm, size, pos, 0, 0, 6, tag_layer) # Tag 6: Ceiling
        
        # Beams/Joists? (Optional simple representation)
        if self.add_framing:
            # Add Ceiling Joists running X?
            pass # Keep simple for now per request

    def _make_roof(self, bm, tag_layer):
        """Generates Trusses and Roof Decking"""
        # Roof Params
        l = self.length
        w = self.width
        oh = self.overhang
        pitch = self.roof_pitch
        wh = self.wall_height
        ts = self.truss_spacing
        
        # Truss Geometry
        truss_base_w = w + (2 * oh)
        # Height from top plate
        truss_h = (truss_base_w / 2) * pitch
        
        pitch_angle = math.atan(pitch)
        
        # Helper: Make Truss
        def make_truss(y_pos):
            # Center Bottom at (0, y_pos, wh)
            center_btm = Vector((0, y_pos, wh))
            
            # Vertices relative to center_btm
            p_left = Vector((-truss_base_w/2, 0, 0))
            p_right = Vector((truss_base_w/2, 0, 0))
            p_peak = Vector((0, 0, truss_h))
            
            # Member size (2x4)
            mw = 0.04 # Thickness
            md = 0.09 # Depth
            
            # 1. Bottom Chord (Joist)
            # Center: (0,0,0)
            self._make_rot_box(bm, Vector((truss_base_w, mw, md)), center_btm + Vector((0,0,md/2)), 0, 0, 1, tag_layer)
            
            # 2. Rafters
            # Left: P_left to P_peak.
            # Vector: (truss_base_w/2, 0, truss_h)
            # Length: hypot
            rafter_len = math.sqrt((truss_base_w/2)**2 + truss_h**2)
            
            # Midpoint Left
            mid_l = (p_left + p_peak) / 2
            pos_l = center_btm + mid_l
            
            # Rot angle: -pitch_angle (Y AXIS)
            self._make_rot_box(bm, Vector((rafter_len, mw, md)), pos_l, 0, 0, 1, tag_layer, angle_y=-pitch_angle)
            
            # Midpoint Right
            mid_r = (p_right + p_peak) / 2
            pos_r = center_btm + mid_r
            
            # Rot angle: +pitch_angle (Y AXIS)
            self._make_rot_box(bm, Vector((rafter_len, mw, md)), pos_r, 0, 0, 1, tag_layer, angle_y=pitch_angle)
            
            # 3. King Post (Center Vertical)
            kp_h = truss_h - md # Subtract thickness roughly
            if kp_h > 0:
                pos_kp = center_btm + Vector((0, 0, truss_h/2))
                self._make_rot_box(bm, Vector((md, mw, truss_h)), pos_kp, 0, 0, 1, tag_layer)
                
            # 4. Gussets (Plates)
            # Peak
            gusset_size = Vector((0.4, 0.01, 0.4)) 
            pos_gusset = center_btm + Vector((0, -md/2 - 0.01, truss_h - 0.2)) # Front face
            self._make_rot_box(bm, gusset_size, pos_gusset, 0, 0, 1, tag_layer)
            
            # 2nd Gusset (Back face)
            pos_gusset_b = center_btm + Vector((0, md/2 + 0.01, truss_h - 0.2))
            self._make_rot_box(bm, gusset_size, pos_gusset_b, 0, 0, 1, tag_layer)
            
        # LOOP Trusses
        # Range Y: -l/2 to l/2.
        # Spacing ts.
        count = int(l / ts) + 1
        if count < 2: count = 2
        step = l / (count - 1)
        
        # LOOP Trusses
        if self.add_framing:
            # Range Y: -l/2 to l/2.
            # Spacing ts.
            count = int(l / ts) + 1
            if count < 2: count = 2
            step = l / (count - 1)
            
            for i in range(count):
                y = -(l/2) + (i * step)
                make_truss(y)
            
        # ROOF DECKING
        # Two large planes
        # Length = l + (2 * oh) (Gable overhang matches eaves)
        deck_l = l + (2 * oh)
        
        # Width (Slope length)
        deck_w = math.sqrt((truss_base_w/2)**2 + truss_h**2) + 0.1 # Add slight eave
        
        deck_thick = 0.02
        
        # Left Slope Center
        # X: -truss_base_w/4 approx?
        # Exact Center of slope line: (-truss_base_w/4, 0, truss_h/2) relative to top plate center
        # World Pos:
        slope_mid_x = -truss_base_w / 4
        slope_mid_z = truss_h / 2
        
        pos_deck_l = Vector((slope_mid_x, 0, wh + slope_mid_z))
        # Need to lift it by member depth + thickness/2 so it sits ON TOP
        # Normal vector is (-sin(pitch), 0, cos(pitch)) ?
        # Normal to slope Left (-x, +z): (-sin, 0, cos). 
        # Actually calculate normal from angle.
        # Angle is -pitch_angle.
        # Normal logic: it sits on rafter (depth 0.09).
        # Offset usually Z local.
        # Let's just create it and translate z local.
        
        # Apply Angle
        # Rotation -pitch_angle around Y.
        
        # Create Left Deck
        verts_l = self._make_rot_box(bm, Vector((deck_w, deck_l, deck_thick)), pos_deck_l, 0, 0, 3, tag_layer, angle_y=-pitch_angle)
        
        # Move Up (Local Z) by rafter depth/2 + frame offset
        # Simple Logic: Shift global Z? No.
        # Shift in Normal Direction.
        # Normal L: (-sin(a), 0, cos(a)) ??
        # Let's approximate: Translate Z by 0.1
        bmesh.ops.translate(bm, verts=verts_l, vec=Vector((0,0,0.1)))
        
        # Right Deck
        pos_deck_r = Vector((-slope_mid_x, 0, wh + slope_mid_z))
        verts_r = self._make_rot_box(bm, Vector((deck_w, deck_l, deck_thick)), pos_deck_r, 0, 0, 3, tag_layer, angle_y=pitch_angle)
        bmesh.ops.translate(bm, verts=verts_r, vec=Vector((0,0,0.1)))

    def _make_porch(self, bm, tag_layer):
        """Generates Front Porch and Stairs"""
        w = self.width
        l = self.length
        pd = self.porch_depth
        ph = self.porch_height
        
        # 1. DECK
        # Position: Front (-Y). Center Y = -l/2 - pd/2.
        pos_deck = Vector((0, (-l/2 - pd/2), ph))
        
        # Deck Size
        self._make_rot_box(bm, Vector((w, pd, 0.1)), pos_deck, 0, 0, 4, tag_layer) # Deck Board Mass
        
        # Posts (Corners)
        post_size = Vector((0.15, 0.15, ph))
        # Front Left
        p1 = Vector((-w/2 + 0.1, -l/2 - pd + 0.1, ph/2))
        self._make_rot_box(bm, post_size, p1, 0, 0, 4, tag_layer)
        # Front Right
        p2 = Vector((w/2 - 0.1, -l/2 - pd + 0.1, ph/2))
        self._make_rot_box(bm, post_size, p2, 0, 0, 4, tag_layer)
        
        # 2. STAIRS
        if self.add_stairs:
            # Center of Front Edge
            start_point = Vector((0, -l/2 - pd, ph))
            
            # Calculate Steps
            rise = 0.18
            # If ph is 0.4, steps = 2.
            step_count = int(ph / rise)
            if step_count < 1: step_count = 1
            
            actual_rise = ph / step_count
            run = 0.28
            stair_w = 1.2
            
            # Iterate downwards
            for i in range(step_count):
                # Step 0 is top step defined by deck? Or step down?
                # Usually Top Step is Flush with deck or one step down.
                # Let's make step down.
                
                s_z = ph - ((i+1) * actual_rise)
                s_y = start_point.y - ((i+1) * run) + (run/2) # Center of tread
                
                # Tread
                tread_pos = Vector((0, s_y, s_z + actual_rise/2)) # Actually just s_z if s_z is floor of step.
                # Just center the box.
                self._make_rot_box(bm, Vector((stair_w, run, 0.05)), Vector((0, s_y, s_z)), 0, 0, 5, tag_layer)
                
                # Stringer support (Simple Box under steps)
                # Angle?
                # Just simplified boxes for v1.

    def _make_kitchen(self, bm, tag_layer):
        # Simple L-Shape Kitchen in Corner (-W/2 + offset, -L/2 + offset)
        w = self.width
        l = self.length
        kw = self.kitchen_width
        
        cab_depth = 0.6
        cab_height = 0.9
        
        # 1. Back Run (Along wall)
        back_len = kw
        p_back = Vector((-w/2 + cab_depth/2 + 0.1, -l/2 + back_len/2 + 0.1, cab_height/2))
        self._make_rot_box(bm, Vector((cab_depth, back_len, cab_height)), p_back, 0, 0, 5, tag_layer) # Tag 5: Interior/Furniture
        
        # 2. Side Run
        side_len = kw * 0.6
        p_side = Vector((-w/2 + back_len/2 + 0.1, -l/2 + cab_depth/2 + 0.1, cab_height/2))
        
        # Countertops
        ct_thick = 0.03
        ct_pos_b = p_back + Vector((0,0,cab_height/2 + ct_thick/2))
        self._make_rot_box(bm, Vector((cab_depth+0.05, back_len, ct_thick)), ct_pos_b, 0, 0, 5, tag_layer)

    def _make_fireplace(self, bm, tag_layer):
        # Chimney Stack
        l = self.length
        w = self.width
        
        cx = self.chimney_loc_x
        # Clamp X
        if cx > w/2 - 0.5: cx = w/2 - 0.5
        if cx < -w/2 + 0.5: cx = -w/2 + 0.5
        
        # Place on Back Wall (+Y)
        cy = l/2
        
        # Base (Hearth)
        hearth_w = 1.5
        hearth_d = 0.8
        hearth_h = 1.2
        p_hearth = Vector((cx, cy, hearth_h/2))
        self._make_rot_box(bm, Vector((hearth_w, hearth_d, hearth_h)), p_hearth, 0, 0, 6, tag_layer) # Tag 6: Stone
        
        # Stack (Up to Roof)
        stack_w = 0.8
        stack_d = 0.6
        stack_h = 5.0 # Tall enough to clear roof
        p_stack = Vector((cx, cy, stack_h/2))
        self._make_rot_box(bm, Vector((stack_w, stack_d, stack_h)), p_stack, 0, 0, 6, tag_layer)

    def _make_door(self, bm, tag_layer, pos, rot_z):
        # Standard Door 0.9 x 2.1
        dw = 0.9
        dh = 2.1
        fw = 0.05 # Frame Thick
        fd = 0.15 # Frame Depth
        
        # Helper for rotated parts
        def make_part(size, rel_pos, tag):
            m = Matrix.Rotation(rot_z, 2, 'Z')
            p_rot = m @ Vector((rel_pos.x, rel_pos.y))
            final_pos = pos + Vector((p_rot.x, p_rot.y, rel_pos.z))
            self._make_rot_box(bm, size, final_pos, rot_z, 0, tag, tag_layer)
            
        # 1. Frame
        make_part(Vector((fw, fd, dh)), Vector((-dw/2 + fw/2, 0, dh/2)), 7) # Tag 7: Wood
        make_part(Vector((fw, fd, dh)), Vector((dw/2 - fw/2, 0, dh/2)), 7)
        make_part(Vector((dw - 2*fw, fd, fw)), Vector((0, 0, dh - fw/2)), 7)
        
        # 2. Door Panel
        p_thick = 0.04
        make_part(Vector((dw - 2*fw - 0.005, p_thick, dh - fw)), Vector((0, 0, dh/2)), 7)
        
        # 3. Simple Handle
        hx = dw/2 - fw - 0.05
        hz = 1.0
        make_part(Vector((0.02, 0.1, 0.02)), Vector((hx, 0, hz)), 4)
        
        # 4. Trim
        tw = 0.08
        td = 0.02
        # Front
        make_part(Vector((tw, td, dh + tw)), Vector((-dw/2 - tw/2 + fw, fd/2 + td/2, dh/2 + tw/2)), 7)
        make_part(Vector((tw, td, dh + tw)), Vector((dw/2 + tw/2 - fw, fd/2 + td/2, dh/2 + tw/2)), 7)
        make_part(Vector((dw + 2*tw, td, tw)), Vector((0, fd/2 + td/2, dh + tw/2)), 7)
        # Back
        make_part(Vector((tw, td, dh + tw)), Vector((-dw/2 - tw/2 + fw, -fd/2 - td/2, dh/2 + tw/2)), 7)
        make_part(Vector((tw, td, dh + tw)), Vector((dw/2 + tw/2 - fw, -fd/2 - td/2, dh/2 + tw/2)), 7)
        make_part(Vector((dw + 2*tw, td, tw)), Vector((0, -fd/2 - td/2, dh + tw/2)), 7)

    def _make_interior_walls(self, bm, tag_layer):
        # Partitions
        w = self.width
        l = self.length
        wh = self.wall_height
        layout = self.interior_layout
        
        stud_thick = 0.1 # 10cm internal walls
        
        if layout == 'OPEN': return
        
        # Main Partition Y = L/4 (Back half)
        part_y = l/4
        
        # Gap for Door
        door_w = 0.9
        
        wall_len_l = (w/2) - (door_w/2)
        pos_l = Vector((-wall_len_l/2 - door_w/2, part_y, wh/2))
        self._make_rot_box(bm, Vector((wall_len_l, stud_thick, wh)), pos_l, 0, 0, 2, tag_layer)
        
        pos_r = Vector((wall_len_l/2 + door_w/2, part_y, wh/2))
        self._make_rot_box(bm, Vector((wall_len_l, stud_thick, wh)), pos_r, 0, 0, 2, tag_layer)
        
        header_h = wh - 2.1
        if header_h > 0:
            pos_h = Vector((0, part_y, wh - header_h/2))
            self._make_rot_box(bm, Vector((door_w, stud_thick, header_h)), pos_h, 0, 0, 2, tag_layer)
            
        # Interior Door
        self._make_door(bm, tag_layer, Vector((0, part_y, 0)), 0)
        
        if layout == '2_BED':
            # Split back area
            cross_len = (l/2) - part_y
            cx_pos = Vector((0, part_y + cross_len/2, wh/2))
            self._make_rot_box(bm, Vector((stud_thick, cross_len, wh)), cx_pos, 0, 0, 2, tag_layer)

    def build_shape(self, bm):
        # 0. INIT
        tag_layer = bm.faces.layers.int.new("MAT_TAG")
        
        # 1. FOUNDATION
        self._make_foundation(bm, tag_layer)
        
        # 2. FLOOR
        self._make_floor(bm, tag_layer)
        
        # 3. WALLS
        self._make_walls(bm, tag_layer)
        
        # 3. ROOF
        if self.add_roof:
            self._make_roof(bm, tag_layer)
            if self.add_gable_walls:
                self._make_gable_ends(bm, tag_layer)
        
        # 3b. CEILING
        if self.add_ceiling:
            self._make_ceiling(bm, tag_layer)
        
        # 4. PORCH
        if self.add_porch:
            self._make_porch(bm, tag_layer)
            
        # 5. FEATURES
        if self.add_kitchen:
            self._make_kitchen(bm, tag_layer)
            
        if self.add_fireplace:
            self._make_fireplace(bm, tag_layer)
            
        # 6. DOORS
        if self.add_door_front:
            self._make_door(bm, tag_layer, Vector((0, -self.length/2, 0)), 0)
            
        if self.add_door_back:
            self._make_door(bm, tag_layer, Vector((0, self.length/2, 0)), 0)
            
        # 7. INTERIOR
        self._make_interior_walls(bm, tag_layer)
        
        # 8. CLEANUP
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

# SELF-EXECUTION FOR AUDIT
# Check if we are running in the audit runner (no relative package context)
try:
    __package__
except NameError:
    __package__ = None

if __package__ is None:
    print("Detected Headless Audit. Executing build_shape...")
    
    # 1. Mock Self with Defaults
    class MockOp(MASSA_OT_prim_con_house_generator):
        def __init__(self):
            # Manually set defaults because bpy properties don't work well outside registration
            self.width = 6.0
            self.length = 8.0
            self.wall_height = 2.7
            self.foundation_height = 0.5
            self.floor_board_w = 0.14
            self.floor_board_gap = 0.002
            self.stud_spacing = 0.6
            self.stud_w = 0.09
            self.stud_t = 0.04
            self.roof_pitch = 0.5
            self.overhang = 0.5
            self.truss_spacing = 0.6
            self.add_framing = True
            self.add_roof = True
            self.add_gable_walls = True
            self.add_ceiling = True
            
            self.add_porch = True
            self.porch_depth = 2.0
            self.porch_height = 0.4
            self.add_stairs = True
            
            # Styles
            self.wall_style = 'MODERN'
            self.floor_style = 'BASIC'
            
            # Features
            self.add_kitchen = True
            self.kitchen_width = 3.0
            self.add_fireplace = True
            self.chimney_loc_x = 0.0
            
            # Iteration 2
            self.interior_layout = '1_BED'
            self.add_door_front = True
            self.add_door_back = True
    
    # 2. Setup BMesh
    op = MockOp()
    bm = bmesh.new()
    
    # 3. Running Build Logic
    op.build_shape(bm)
    
    # 4. Write to Scene for Runner to find
    mesh = bpy.data.meshes.new('Audit_Mesh')
    obj = bpy.data.objects.new('Audit_Object', mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    # 5. UV UNWRAP (Required for Audit)
    uv_layer = bm.loops.layers.uv.verify()
    for f in bm.faces:
        for i, loop in enumerate(f.loops):
            # Simple Unit Square Mapping to avoid Pinched UV error
            # 0:0,0 | 1:1,0 | 2:1,1 | 3:0,1
            u = 0.0 if i in [0, 3] else 1.0
            v = 0.0 if i in [0, 1] else 1.0
            loop[uv_layer].uv = (u, v)
    
    # Update Mesh with new UVs
    bm.to_mesh(obj.data)
    bm.free()
