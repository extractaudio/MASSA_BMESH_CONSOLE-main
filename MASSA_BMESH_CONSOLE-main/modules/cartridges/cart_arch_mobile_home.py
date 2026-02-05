import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ARCH: Mobile Home",
    "id": "arch_mobile_home",
    "icon": "HOME",
    "scale_class": "MACRO",
    "flags": {
        "USE_WELD": False,
        "FIX_DEGENERATE": True,
        "ALLOW_SOLIDIFY": False,
    },
}

def create_cube_helper(bm, loc, size, mat_idx, subdivide=False, rotation_z=0.0, seam_axis='AREA'):
    """
    Creates a cube, scales, rotates, translates, assigns slots, and optionally subdivides.
    seam_axis: 'AREA' (Snippet A), 'X', 'Y', 'Z' (Force Normals).
    """
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res["verts"]
    safe_size = [max(0.001, s) for s in size]
    
    # 1. Scale
    bmesh.ops.scale(bm, vec=Vector(safe_size), verts=verts)
    
    # --- PHASE 2: UV SEAM LOGIC ---
    new_faces = list({f for v in verts for f in v.link_faces})
    for f in new_faces: f.material_index = mat_idx
    
    edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
    if not edge_slots: edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
    
    caps = []
    
    if seam_axis == 'AREA':
        # SNIPPET A: Smallest Area
        sorted_faces = sorted(new_faces, key=lambda f: f.calc_area())
        caps = sorted_faces[:2]
    else:
        # NORMAL BASED AXIS FORCE
        target_axis = 0 # X
        if seam_axis == 'Y': target_axis = 1
        if seam_axis == 'Z': target_axis = 2
        
        for f in new_faces:
            n = f.normal
            # Check axis alignment (abs value close to 1.0)
            if abs(n[target_axis]) > 0.9:
                caps.append(f)

    # Apply Seams
    for f in caps:
        for e in f.edges:
            e.seam = True
            e[edge_slots] = 2 # CONTOUR

    # 2. Rotate (Local Z)
    if abs(rotation_z) > 0.001:
        bmesh.ops.rotate(bm, cent=Vector((0,0,0)), matrix=Matrix.Rotation(rotation_z, 3, 'Z'), verts=verts)
        
    # 3. Translate
    bmesh.ops.translate(bm, vec=loc, verts=verts)
    
    if subdivide:
        max_len = 1.2
        cuts_x = int(safe_size[0] / max_len)
        cuts_y = int(safe_size[1] / max_len)
        cuts_z = int(safe_size[2] / max_len)
        
        if cuts_x > 0 or cuts_y > 0 or cuts_z > 0:
            edges_to_cut = list({e for f in new_faces for e in f.edges})
            bmesh.ops.subdivide_edges(bm, edges=edges_to_cut, cuts=1, use_grid_fill=True)

    return verts, new_faces

def create_window_geo(bm, loc, width, height, mat_frame, mat_glass):
    # Simple Frame
    f_th = 0.1 
    f_w = 0.08 
    
    # Outer Frame 
    create_cube_helper(bm, Vector((loc.x, loc.y, loc.z + height/2 - f_w/2)), (f_th+0.02, width, f_w), mat_frame, seam_axis='X') # Top
    create_cube_helper(bm, Vector((loc.x, loc.y, loc.z - height/2 + f_w/2)), (f_th+0.02, width, f_w), mat_frame, seam_axis='X') # Bot
    
    # Sides
    create_cube_helper(bm, Vector((loc.x, loc.y - width/2 + f_w/2, loc.z)), (f_th+0.02, f_w, height - 2*f_w), mat_frame, seam_axis='Z') # Left
    create_cube_helper(bm, Vector((loc.x, loc.y + width/2 - f_w/2, loc.z)), (f_th+0.02, f_w, height - 2*f_w), mat_frame, seam_axis='Z') # Right
    
    # Glass 
    create_cube_helper(bm, loc, (0.02, width - 2*f_w, height - 2*f_w), mat_glass, seam_axis='AREA')

    # Sash 
    create_cube_helper(bm, loc, (0.04, width - 2*f_w, f_w/2), mat_frame, seam_axis='X')

def create_segmented_wall(bm, start, end, height, thickness, holes, floor_z, mat_idx, siding_mode=False, siding_size=0.2, seam_mode='Z'):
    """
    Procedurally builds a wall with holes by tiling geometric patches.
    seam_mode: 'Z' for Walls (Vertical Room Wrap), 'X' for Siding (Horizontal Plank Wrap).
    """
    vec = end - start
    length = vec.length
    u = vec.normalized()
    
    # Normalize holes relative to start
    holes.sort(key=lambda x: x['dist'])
    
    cursor = 0.0
    
    # Calculate Angle for rotation
    wall_angle = math.atan2(u.y, u.x)

    def place_segment(s_dist, e_dist, h_base, h_top):
        seg_len = e_dist - s_dist
        if seg_len < 0.001: return
        
        seg_h = h_top - h_base
        if seg_h < 0.001: return
        
        mid_dist = (s_dist + e_dist) / 2
        mid_z = (h_base + h_top) / 2
        
        pos = start + u * mid_dist
        pos.z = mid_z
        
        # Size vector (X=Length, Y=Thickness, Z=Height)
        size = (seg_len, thickness, seg_h)
        
        # CREATE
        if siding_mode:
            # GLOBAL SIDING ALIGNMENT
            k_start = math.ceil((h_base - floor_z) / siding_size)
            k_end = math.floor((h_top - floor_z) / siding_size)
            
            if k_end >= k_start:
                k_count = k_end - k_start + 1
                if k_count > 1000: k_count = 1000 
                
                for i in range(k_count):
                    k = k_start + i
                    pz = floor_z + k*siding_size + siding_size/2
                    
                    if pz < h_base - 0.01 or pz > h_top + 0.01: continue
                         
                    ppos = start + u * mid_dist
                    ppos.z = pz
                    # SIDING: Force X Seams (Horizontal)
                    create_cube_helper(bm, ppos, (seg_len, thickness * 1.2, siding_size * 0.9), mat_idx, rotation_z=wall_angle, seam_axis='X')

        else:
            # Base Wall
            # WALL: Respect seam_mode (Likely 'Z' for vertical)
            create_cube_helper(bm, pos, size, mat_idx, subdivide=True, rotation_z=wall_angle, seam_axis=seam_mode)


    for h in holes:
        h_center_dist = h['dist']
        h_w = h['width']
        h_h = h['height']
        h_z = h['z_sill'] # Bottom of window
        
        h_start = h_center_dist - h_w/2
        h_end = h_center_dist + h_w/2
        h_top = h_z + h_h
        
        # 1. Solid Column before hole
        if h_start > cursor:
            place_segment(cursor, h_start, floor_z, floor_z + height)
            
        # 2. Hole Column (Footer)
        if (h_z - floor_z) > 0.01:
            place_segment(h_start, h_end, floor_z, h_z)
            
        # 3. Hole Column (Header)
        if (floor_z + height - h_top) > 0.01:
            place_segment(h_start, h_end, h_top, floor_z + height)
            
        cursor = h_end
        
    # Final Segment
    if cursor < length:
        place_segment(cursor, length, floor_z, floor_z + height)


class MASSA_OT_ArchMobileHome(Massa_OT_Base):
    bl_idname = "massa.gen_arch_mobile_home"
    bl_label = "ARCH: Mobile Home"
    bl_description = "Mobile Home Generator (Single/Double Wide)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- PROPERTIES ---
    prop_width: FloatProperty(name="Width", default=4.3, min=3.0, description="14ft (4.3m) Single, 24ft (7.3m) Double")
    prop_length: FloatProperty(name="Length", default=15.0, min=8.0, description="40-70ft (12-21m)")
    prop_height: FloatProperty(name="Wall Height", default=2.4, min=2.1)
    
    # Structural Toggles
    prop_toggle_structure: BoolProperty(name="Structure & Foundation", default=True)
    prop_foundation_height: FloatProperty(name="Lift Height", default=0.6, min=0.1)
    prop_skirting: BoolProperty(name="Add Skirting", default=True)
    prop_under_supports: BoolProperty(name="Add Under-Supports", default=True)

    # Porch Toggle
    prop_toggle_porch: BoolProperty(name="Porch & Features", default=True)
    prop_add_porch: BoolProperty(name="Add Porch", default=True)
    prop_porch_loc: EnumProperty(name="Location", items=[("END", "End", ""), ("SIDE", "Side", "")], default="SIDE")
    prop_porch_depth: FloatProperty(name="Porch Depth", default=1.5, min=0.5)
    prop_porch_width: FloatProperty(name="Porch Width", default=3.0, min=1.0)
    prop_porch_offset: FloatProperty(name="Offset", default=0.0)
    prop_porch_roof: BoolProperty(name="Porch Roof", default=True)
    prop_porch_stairs: BoolProperty(name="Add Stairs", default=True)
    prop_stair_offset: FloatProperty(name="Stair Offset", default=0.0)
    
    # Openings Toggle
    prop_toggle_openings: BoolProperty(name="Windows & Doors", default=True)
    prop_door_active: BoolProperty(name="Main Door", default=True)
    prop_door_width: FloatProperty(name="Door Width", default=0.9, min=0.6)
    prop_door_height: FloatProperty(name="Door Height", default=2.1, min=1.8)
    prop_win_count: IntProperty(name="Side Windows", default=3, min=0, max=8)
    prop_win_standard: EnumProperty(name="Win Type", items=[("DOUBLE", "Double Hung", ""), ("PICTURE", "Picture", "")], default="DOUBLE")

    # Siding Toggle
    prop_toggle_siding: BoolProperty(name="Cladding & Siding", default=True)
    prop_geo_siding: BoolProperty(name="Geo Siding", default=True)
    prop_siding_size: FloatProperty(name="Siding Size", default=0.2, min=0.1)

    # Visibility (Global)
    prop_vis_walls: BoolProperty(name="Show Walls", default=True)
    prop_vis_roof: BoolProperty(name="Show Roof", default=True)
    prop_vis_openings: BoolProperty(name="Show Openings", default=True)
    prop_vis_porch: BoolProperty(name="Show Porch", default=True)
    
    prop_roof_overhang: FloatProperty(name="Overhang", default=0.15, min=0.0)
    prop_roof_height: FloatProperty(name="Roof Peak", default=0.6, min=0.1)

    def get_slot_meta(self):
        return {
            0: {"name": "Skirting/Fdn", "phys": "SYNTH_PLASTIC", "uv": "BOX"}, 
            1: {"name": "Floor", "phys": "WOOD_PLANKS", "uv": "BOX"},
            2: {"name": "Siding", "phys": "VINYL_SIDING", "uv": "BOX"},
            3: {"name": "Wall Int", "phys": "GYPSUM_PAINTED", "uv": "BOX"},
            4: {"name": "Framing", "phys": "WOOD_RAW", "uv": "BOX"},
            5: {"name": "Roof", "phys": "METAL_ROOF", "uv": "BOX"},
            6: {"name": "Trim", "phys": "ALUMINUM_PAINTED", "uv": "BOX"},
            7: {"name": "Glass", "phys": "GLASS_CLEAR", "uv": "FIT"},
            8: {"name": "Door", "phys": "METAL_PAINTED", "uv": "BOX"},
            9: {"name": "Details", "phys": "PLASTIC_ROUGH", "uv": "BOX"},
        }

    def draw_shape_ui(self, layout):
        # PHASE 1: UI BUTTONS (Collapsible)
        box = layout.box()
        box.label(text="Mobile Home Dimensions", icon="HOME")
        box.prop(self, "prop_width")
        box.prop(self, "prop_length")
        box.prop(self, "prop_height")
        
        # Structure Panel
        box = layout.box()
        head = box.row()
        head.prop(self, "prop_toggle_structure", icon="TRIA_DOWN" if self.prop_toggle_structure else "TRIA_RIGHT", emboss=False)
        if self.prop_toggle_structure:
            col = box.column(align=True)
            col.prop(self, "prop_foundation_height")
            col.prop(self, "prop_skirting")
            col.prop(self, "prop_under_supports")
            col.prop(self, "prop_roof_overhang")
            col.prop(self, "prop_roof_height")
            
        # Siding Panel
        box = layout.box()
        head = box.row()
        head.prop(self, "prop_toggle_siding", icon="TRIA_DOWN" if self.prop_toggle_siding else "TRIA_RIGHT", emboss=False)
        if self.prop_toggle_siding:
            col = box.column(align=True)
            col.prop(self, "prop_geo_siding")
            if self.prop_geo_siding:
                col.prop(self, "prop_siding_size")

        # Porch Panel
        box = layout.box()
        head = box.row()
        head.prop(self, "prop_toggle_porch", icon="TRIA_DOWN" if self.prop_toggle_porch else "TRIA_RIGHT", emboss=False)
        if self.prop_toggle_porch:
            col = box.column(align=True)
            col.prop(self, "prop_add_porch")
            if self.prop_add_porch:
                col.prop(self, "prop_porch_loc", text="")
                row = col.row(align=True)
                row.prop(self, "prop_porch_width")
                row.prop(self, "prop_porch_depth")
                col.prop(self, "prop_porch_offset")
                row = col.row()
                row.prop(self, "prop_porch_roof")
                row.prop(self, "prop_porch_stairs")
                if self.prop_porch_stairs:
                    col.prop(self, "prop_stair_offset")

        # Openings Panel
        box = layout.box()
        head = box.row()
        head.prop(self, "prop_toggle_openings", icon="TRIA_DOWN" if self.prop_toggle_openings else "TRIA_RIGHT", emboss=False)
        if self.prop_toggle_openings:
            col = box.column(align=True)
            col.prop(self, "prop_door_active")
            col.prop(self, "prop_win_count")
            col.prop(self, "prop_win_standard")

        # Visibility
        box = layout.box()
        box.label(text="Visibility", icon="RESTRICT_VIEW_OFF")
        row = box.row()
        row.prop(self, "prop_vis_walls", text="Walls")
        row.prop(self, "prop_vis_roof", text="Roof")
        row.prop(self, "prop_vis_openings", text="Openings")
        row.prop(self, "prop_vis_porch", text="Porch")


    def build_shape(self, bm):
        w = self.prop_width
        l = self.prop_length
        h = self.prop_height
        fh = self.prop_foundation_height
        
        # 1. FOUNDATION
        beam_off = w * 0.3
        create_cube_helper(bm, Vector((-beam_off, 0, fh/2)), (0.1, l, fh), 4, seam_axis='X') 
        create_cube_helper(bm, Vector((beam_off, 0, fh/2)), (0.1, l, fh), 4, seam_axis='X') 
        
        if self.prop_skirting:
            skirt_th = 0.02
            create_cube_helper(bm, Vector((-w/2, 0, fh/2)), (skirt_th, l, fh), 0, seam_axis='Z')
            create_cube_helper(bm, Vector((w/2, 0, fh/2)), (skirt_th, l, fh), 0, seam_axis='Z')
            create_cube_helper(bm, Vector((0, -l/2, fh/2)), (w, skirt_th, fh), 0, seam_axis='Z')
            create_cube_helper(bm, Vector((0, l/2, fh/2)), (w, skirt_th, fh), 0, seam_axis='Z')
        else:
            piers_y = int(l / 2.0)
            for iy in range(piers_y + 1):
                y_pos = -l/2 + (l * (iy / piers_y))
                create_cube_helper(bm, Vector((-beam_off, y_pos, fh/2)), (0.4, 0.4, fh), 0, seam_axis='Z')
                create_cube_helper(bm, Vector((beam_off, y_pos, fh/2)), (0.4, 0.4, fh), 0, seam_axis='Z')

        # 2. FLOOR
        f_h = 0.2
        floor_z = fh + f_h/2
        create_cube_helper(bm, Vector((0, 0, floor_z)), (w, l, f_h), 1, seam_axis='X')
        floor_top = fh + f_h

        # 3. WALLS (SEGMENTED)
        wall_th = 0.1
        wall_h = h
        wall_cen_z = floor_top + wall_h/2
        
        if self.prop_vis_walls:
            holes_left = [] 
            holes_right = [] 
            
            if self.prop_win_count > 0:
                win_y_start = -l/2 + 1.0
                win_space = (l - 2.0) / max(1, self.prop_win_count)
                w_width = 0.9 if self.prop_win_standard == 'DOUBLE' else 1.5
                w_height = 1.5 if self.prop_win_standard == 'DOUBLE' else 1.2
                win_sill = floor_top + 0.8
                for i in range(self.prop_win_count):
                    wy = win_y_start + (i * win_space) + win_space/2
                    dist = wy + l/2
                    holes_left.append({'dist': dist, 'width': w_width, 'height': w_height, 'z_sill': win_sill})
                    
            if self.prop_door_active:
                    dy = -l/4
                    dist = dy + l/2
                    d_w = self.prop_door_width
                    d_h = self.prop_door_height
                    holes_right.append({'dist': dist, 'width': d_w, 'height': d_h, 'z_sill': floor_top})

            # BUILD WALLS
            # Left (-X)
            start_L = Vector((-w/2 + wall_th/2, -l/2 + wall_th/2, 0))
            end_L = Vector((-w/2 + wall_th/2, l/2 - wall_th/2, 0))
            base_mat = 4 if self.prop_geo_siding else 2
            
            create_segmented_wall(bm, start_L, end_L, wall_h, wall_th, holes_left, floor_top, base_mat, seam_mode='Z')
            if self.prop_geo_siding:
                s_start = Vector((-w/2 - 0.01, -l/2, 0))
                s_end = Vector((-w/2 - 0.01, l/2, 0))
                create_segmented_wall(bm, s_start, s_end, wall_h, 0.02, holes_left, floor_top, 2, True, self.prop_siding_size, seam_mode='X')
            
            # Left Interior Panel (NEW)
            create_segmented_wall(bm, 
                                  Vector((-w/2 + wall_th + 0.01, -l/2, 0)), 
                                  Vector((-w/2 + wall_th + 0.01, l/2, 0)), 
                                  wall_h, 0.01, holes_left, floor_top, 3, seam_mode='Z')

            # Right (+X)
            start_R = Vector((w/2 - wall_th/2, -l/2 + wall_th/2, 0))
            end_R = Vector((w/2 - wall_th/2, l/2 - wall_th/2, 0))
            create_segmented_wall(bm, start_R, end_R, wall_h, wall_th, holes_right, floor_top, base_mat, seam_mode='Z')
            if self.prop_geo_siding:
                    s_start = Vector((w/2 + 0.01, -l/2, 0))
                    s_end = Vector((w/2 + 0.01, l/2, 0))
                    create_segmented_wall(bm, s_start, s_end, wall_h, 0.02, holes_right, floor_top, 2, True, self.prop_siding_size, seam_mode='X')
            
            # Right Interior Panel (NEW) - at w/2 - wall_th - 0.01
            create_segmented_wall(bm, 
                                  Vector((w/2 - wall_th - 0.01, -l/2, 0)), 
                                  Vector((w/2 - wall_th - 0.01, l/2, 0)), 
                                  wall_h, 0.01, holes_right, floor_top, 3, seam_mode='Z')
                    
            # Ends (Solid for now) -> Make them Panels too? YES.
            # -Y
            create_cube_helper(bm, Vector((0, -l/2 + wall_th/2, wall_cen_z)), (w - 2*wall_th, wall_th, wall_h), base_mat, subdivide=True, seam_axis='Z')
            if self.prop_geo_siding:
                    s_start = Vector((-w/2, -l/2 - 0.01, 0))
                    s_end = Vector((w/2, -l/2 - 0.01, 0))
                    create_segmented_wall(bm, s_start, s_end, wall_h, 0.02, [], floor_top, 2, True, self.prop_siding_size, seam_mode='X')
            
            # -Y Interior Panel (at -l/2 + wall_th + 0.01)
            create_segmented_wall(bm,
                                  Vector((-w/2 + wall_th, -l/2 + wall_th + 0.01, 0)),
                                  Vector((w/2 - wall_th, -l/2 + wall_th + 0.01, 0)),
                                  wall_h, 0.01, [], floor_top, 3, seam_mode='Z')
                    
            # +Y
            create_cube_helper(bm, Vector((0, l/2 - wall_th/2, wall_cen_z)), (w - 2*wall_th, wall_th, wall_h), base_mat, subdivide=True, seam_axis='Z')
            if self.prop_geo_siding:
                    s_start = Vector((-w/2, l/2 + 0.01, 0))
                    s_end = Vector((w/2, l/2 + 0.01, 0))
                    create_segmented_wall(bm, s_start, s_end, wall_h, 0.02, [], floor_top, 2, True, self.prop_siding_size, seam_mode='X')

            # +Y Interior Panel (at l/2 - wall_th - 0.01)
            create_segmented_wall(bm,
                                  Vector((-w/2 + wall_th, l/2 - wall_th - 0.01, 0)),
                                  Vector((w/2 - wall_th, l/2 - wall_th - 0.01, 0)),
                                  wall_h, 0.01, [], floor_top, 3, seam_mode='Z')
            
            # 3B. CEILING
            ceil_z = floor_top + wall_h - 0.02
            ceil_w = w - 2*wall_th
            ceil_l = l - 2*wall_th
            create_cube_helper(bm, Vector((0, 0, ceil_z)), (ceil_w, ceil_l, 0.02), 3, seam_axis='X') # Ceiling: X seams usually fine

                
        # GENERATE WINDOW/DOOR GEO (FILL)
        if self.prop_vis_openings:
            if self.prop_door_active:
                create_window_geo(bm, Vector((w/2 - 0.05, -l/4, floor_top + self.prop_door_height/2)), self.prop_door_width, self.prop_door_height, 6, 8)
                
            if self.prop_win_count > 0:
                side_x = -w/2 + 0.05
                win_y_start = -l/2 + 1.0
                win_space = (l - 2.0) / max(1, self.prop_win_count)
                w_width = 0.9 if self.prop_win_standard == 'DOUBLE' else 1.5
                w_height = 1.5 if self.prop_win_standard == 'DOUBLE' else 1.2
                win_z = floor_top + 0.8 + w_height/2
                
                for i in range(self.prop_win_count):
                    wy = win_y_start + (i * win_space) + win_space/2
                    create_window_geo(bm, Vector((side_x, wy, win_z)), w_width, w_height, 6, 7)
        
        # 4. ROOF (Standard)
        if self.prop_vis_roof:
            roof_z = floor_top + h
            overhang = self.prop_roof_overhang
            rise = self.prop_roof_height
            rb_1 = Vector((-w/2 - overhang, -l/2 - overhang, roof_z))
            rb_2 = Vector((w/2 + overhang, -l/2 - overhang, roof_z))
            rb_3 = Vector((w/2 + overhang, l/2 + overhang, roof_z))
            rb_4 = Vector((-w/2 - overhang, l/2 + overhang, roof_z))
            rp_front = Vector(((rb_1.x+rb_2.x)/2, rb_1.y, roof_z + rise))
            rp_back = Vector(((rb_3.x+rb_4.x)/2, rb_3.y, roof_z + rise))
            v1, v2, v3, v4 = bm.verts.new(rb_1), bm.verts.new(rb_2), bm.verts.new(rb_3), bm.verts.new(rb_4)
            vp1, vp2 = bm.verts.new(rp_front), bm.verts.new(rp_back)
            fL = bm.faces.new([v1, vp1, vp2, v4])
            fL.material_index = 5
            v1.link_edges[0].seam=True # Fix logic if needed, but manual for now
            fR = bm.faces.new([v2, v3, vp2, vp1])
            fR.material_index = 5
            if self.prop_vis_walls:
                fG1 = bm.faces.new([v1, v2, vp1])
                fG1.material_index = 2
                fG2 = bm.faces.new([v4, vp2, v3])
                fG2.material_index = 2

        # 5. PORCH
        if self.prop_add_porch and self.prop_vis_porch:
            p_w, p_d, p_off = self.prop_porch_width, self.prop_porch_depth, self.prop_porch_offset
            
            p_x, p_y = (p_off, -l/2 - p_d/2) if self.prop_porch_loc == 'END' else (w/2 + p_d/2, p_off)
            p_dim_actual = (p_w, p_d, fh) if self.prop_porch_loc == 'END' else (p_d, p_w, fh)
            
            create_cube_helper(bm, Vector((p_x, p_y, floor_top - fh/2)), p_dim_actual, 1, seam_axis='Z')
            
            # Calculate corners
            if self.prop_porch_loc == 'END':
                px_min, px_max = p_x - p_w/2, p_x + p_w/2
                py_min, py_max = p_y - p_d/2, p_y + p_d/2
            else:
                px_min, px_max = p_x - p_dim_actual[0]/2, p_x + p_dim_actual[0]/2
                py_min, py_max = p_y - p_dim_actual[1]/2, p_y + p_dim_actual[1]/2
                
            # Railing
            post_h = h if self.prop_porch_roof else 1.0
            c1 = Vector((px_min+0.1, py_min+0.1, floor_top + post_h/2))
            c2 = Vector((px_max-0.1, py_min+0.1, floor_top + post_h/2))
            c3 = Vector((px_max-0.1, py_max-0.1, floor_top + post_h/2))
            c4 = Vector((px_min+0.1, py_max-0.1, floor_top + post_h/2))
            
            for c in [c1, c2, c3, c4]:
                create_cube_helper(bm, c, (0.08, 0.08, post_h), 6, seam_axis='Z') 
            
            if self.prop_porch_roof:
                beam_z = floor_top + post_h - 0.1
                # PORCH FUSE LOGIC (User Request)
                fuse_amt = 0.2
                r_dim_x = p_dim_actual[0] + 0.2
                r_dim_y = p_dim_actual[1] + 0.2
                r_loc_x = p_x
                r_loc_y = p_y
                
                if self.prop_porch_loc == 'SIDE':
                    r_dim_x += fuse_amt
                    r_loc_x -= fuse_amt/2
                else: # END
                    r_dim_y += fuse_amt
                    r_loc_y += fuse_amt/2
                
                create_cube_helper(bm, Vector((r_loc_x, r_loc_y, beam_z + 0.15)), (r_dim_x, r_dim_y, 0.1), 5, seam_axis='X')


        # 7. CLEANUP
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        # Perimeter Force
        slot_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        min_z = min([v.co.z for v in bm.verts])
        for e in bm.edges:
            if e.verts[0].co.z < (min_z + 0.1) and e.verts[1].co.z < (min_z + 0.1):
                e[slot_layer] = 1
            elif e.is_boundary:
                e[slot_layer] = 1
            elif e[slot_layer] == 0:
                e[slot_layer] = 4

# Module-level checker
def build_shape(self, bm):
    MASSA_OT_ArchMobileHome.build_shape(self, bm)
