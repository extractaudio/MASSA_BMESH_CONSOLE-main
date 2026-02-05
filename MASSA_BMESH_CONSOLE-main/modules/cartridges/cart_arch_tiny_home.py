import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {
    "name": "ARCH: Tiny Home",
    "id": "arch_tiny_home",
    "icon": "HOME",
    "scale_class": "MACRO",
    "flags": {
        "USE_WELD": True,
        "FIX_DEGENERATE": True,
        "ALLOW_SOLIDIFY": False,
    },
}


def create_cube_helper(bm, loc, size, mat_idx, subdivide=False):
    res = bmesh.ops.create_cube(bm, size=1.0)
    verts = res["verts"]
    safe_size = [max(0.001, s) for s in size]
    bmesh.ops.scale(bm, vec=Vector(safe_size), verts=verts)
    bmesh.ops.translate(bm, vec=loc, verts=verts)
    
    new_faces = list({f for v in verts for f in v.link_faces})
    for f in new_faces: f.material_index = mat_idx
    
    # UV Seams Correct: Snippet A - The Plank
    # 1. Identify Caps (Smallest Area)
    sorted_faces = sorted(new_faces, key=lambda f: f.calc_area())
    if len(sorted_faces) >= 2:
        caps = sorted_faces[:2] # The two ends
        
        # 2. Mark Cap Seams
        for f in caps:
            for e in f.edges:
                e.seam = True
                
        # 3. Mark Edge Roles (Contour)
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots: edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
        
        for f in caps:
            for e in f.edges:
                e[edge_slots] = 2 # CONTOUR

    if subdivide:
        # Simple segmentation for large architectural planes
        # We cut anything larger than 1.2m
        max_len = 1.2
        cuts_x = int(safe_size[0] / max_len)
        cuts_y = int(safe_size[1] / max_len)
        cuts_z = int(safe_size[2] / max_len)
        
        if cuts_x > 0 or cuts_y > 0 or cuts_z > 0:
             # Collect edges to cut
             edges_to_cut = list({e for f in new_faces for e in f.edges})
             bmesh.ops.subdivide_edges(bm, edges=edges_to_cut, cuts=1, use_grid_fill=True)

    return verts, new_faces

class MASSA_OT_ArchTinyHome(Massa_OT_Base):
    bl_idname = "massa.gen_arch_tiny_home"
    bl_label = "ARCH: Tiny Home"
    bl_description = "Tiny Home Generator with Structural Framing"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- PROPERTIES ---
    # Dimensions
    prop_width: FloatProperty(name="Width", default=4.0, min=2.0)
    prop_length: FloatProperty(name="Length", default=8.0, min=4.0)
    prop_height: FloatProperty(name="Wall Height", default=3.0, min=2.0)
    
    # Structure
    prop_foundation_height: FloatProperty(name="Fdn Height", default=0.5, min=0.1)
    prop_stud_spacing: FloatProperty(name="Stud Spacing", default=0.6, min=0.3)
    
    # Visibility / Layers
    prop_vis_framing: BoolProperty(name="Show Framing", default=True)
    prop_vis_sheathing: BoolProperty(name="Show Walls", default=True)
    prop_vis_roof: BoolProperty(name="Show Roof", default=True)
    prop_vis_openings: BoolProperty(name="Show Doors/Win", default=True)

    # Roof
    prop_add_roof: BoolProperty(name="Roof System", default=True)
    prop_roof_type: EnumProperty(
        name="Roof",
        items=[
            ("GABLE", "Gable", "Triangular Roof"),
            ("SHED", "Shed", "Sloped Roof"),
        ],
        default="GABLE"
    )
    prop_roof_overhang: FloatProperty(name="Overhang", default=0.4, min=0.0)
    prop_roof_height: FloatProperty(name="Roof Peak/Rise", default=1.5, min=0.1)
    
    # Features
    prop_add_porch: BoolProperty(name="Add Porch", default=True)
    prop_porch_depth: FloatProperty(name="Porch Depth", default=2.0, min=0.5)
    prop_porch_width: FloatProperty(name="Porch Width", default=4.0, min=1.0)
    prop_porch_offset_x: FloatProperty(name="Porch Offset X", default=0.0)
    
    prop_add_loft: BoolProperty(name="Add Loft", default=True)
    prop_loft_height: FloatProperty(name="Loft Height", default=2.2, min=1.5)

    # Openings
    # Door (Front Wall)
    prop_door_active: BoolProperty(name="Front Door", default=True)
    prop_door_width: FloatProperty(name="Door Width", default=0.9, min=0.6)
    prop_door_height: FloatProperty(name="Door Height", default=2.1, min=1.8)
    prop_door_offset_x: FloatProperty(name="Door Center X", default=0.0)

    # Windows
    prop_win_active_list: BoolProperty(name="Windows", default=True) 
    prop_win_width: FloatProperty(name="Win Width", default=1.0, min=0.4)
    prop_win_height: FloatProperty(name="Win Height", default=1.2, min=0.4)
    prop_win_elevation: FloatProperty(name="Win Sill Z", default=0.9, min=0.1)
    
    prop_win_front_active: BoolProperty(name="Front", default=False)
    prop_win_front_offset: FloatProperty(name="X", default=1.5)
    
    prop_win_back_active: BoolProperty(name="Back", default=True)
    prop_win_back_offset: FloatProperty(name="X", default=0.0)
    
    prop_win_left_active: BoolProperty(name="Left", default=True)
    prop_win_left_offset: FloatProperty(name="Y", default=0.0)
    
    prop_win_right_active: BoolProperty(name="Right", default=True)
    prop_win_right_offset: FloatProperty(name="Y", default=0.0)

    def get_slot_meta(self):
        return {
            0: {"name": "Foundation", "phys": "CONCRETE_RAW", "uv": "BOX"},
            1: {"name": "Floor", "phys": "WOOD_PLANKS", "uv": "BOX"},
            2: {"name": "Wall Ext", "phys": "WOOD_PAINTED", "uv": "BOX"},
            3: {"name": "Wall Int", "phys": "GYPSUM_PAINTED", "uv": "BOX"},
            4: {"name": "Framing", "phys": "WOOD_RAW", "uv": "BOX"},
            5: {"name": "Roof", "phys": "METAL_ROOF", "uv": "BOX"},
            6: {"name": "Trim", "phys": "WOOD_VARNISH", "uv": "BOX"},
            7: {"name": "Glass", "phys": "GLASS_CLEAR", "uv": "FIT"},
            8: {"name": "Door", "phys": "WOOD_VARNISH", "uv": "BOX"},
            9: {"name": "Fixtures", "phys": "CERAMIC_WHITE", "uv": "BOX"},
        }

    def draw_shape_ui(self, layout):
        # MAIN
        box = layout.box()
        box.label(text="Dimensions", icon="OUTLINER_OB_META")
        col = box.column(align=True)
        col.prop(self, "prop_width")
        col.prop(self, "prop_length")
        col.prop(self, "prop_height")
        
        # VISIBILITY
        box = layout.box()
        box.label(text="Visibility", icon="RESTRICT_VIEW_OFF")
        row = box.row(align=True)
        row.prop(self, "prop_vis_framing", toggle=True, text="Studs")
        row.prop(self, "prop_vis_sheathing", toggle=True, text="Walls")
        row.prop(self, "prop_vis_roof", toggle=True, text="Roof")
        row.prop(self, "prop_vis_openings", toggle=True, text="Door/Win")
        
        # STRUCTURE
        box = layout.box()
        box.label(text="Structure", icon="MOD_BUILD")
        col = box.column(align=True)
        col.prop(self, "prop_foundation_height")
        col.prop(self, "prop_stud_spacing")

        # PORCH
        box = layout.box()
        row = box.row()
        row.prop(self, "prop_add_porch", toggle=True, icon="MODIFIER", text="Porch System")
        if self.prop_add_porch:
            box.prop(self, "prop_porch_depth")
            box.prop(self, "prop_porch_width")
            box.prop(self, "prop_porch_offset_x")
            
        # LOFT
        box = layout.box()
        row = box.row()
        row.prop(self, "prop_add_loft", toggle=True, icon="MOD_BUILD", text="Loft System")
        if self.prop_add_loft:
            box.prop(self, "prop_loft_height")

        # DOOR
        box = layout.box()
        row = box.row()
        row.prop(self, "prop_door_active", toggle=True, icon="MOD_BOOLEAN", text="Front Door")
        if self.prop_door_active:
            col = box.column(align=True)
            col.prop(self, "prop_door_width")
            col.prop(self, "prop_door_height")
            col.prop(self, "prop_door_offset_x")

        # WINDOWS
        box = layout.box()
        row = box.row()
        row.prop(self, "prop_win_active_list", toggle=True, icon="MOD_MASK", text="Windows")
        if self.prop_win_active_list:
            col = box.column(align=True)
            col.prop(self, "prop_win_width")
            col.prop(self, "prop_win_height")
            col.prop(self, "prop_win_elevation")
            
            box2 = box.box()
            box2.label(text="Placement")
            # Grid layout for placement
            g = box2.grid_flow(row_major=True, columns=2, align=True)
            
            # Front
            r = g.column(align=True)
            r.prop(self, "prop_win_front_active")
            if self.prop_win_front_active: r.prop(self, "prop_win_front_offset")
            
            # Back
            r = g.column(align=True)
            r.prop(self, "prop_win_back_active")
            if self.prop_win_back_active: r.prop(self, "prop_win_back_offset")
            
            # Left
            r = g.column(align=True)
            r.prop(self, "prop_win_left_active")
            if self.prop_win_left_active: r.prop(self, "prop_win_left_offset")
            
            # Right
            r = g.column(align=True)
            r.prop(self, "prop_win_right_active")
            if self.prop_win_right_active: r.prop(self, "prop_win_right_offset")

        # ROOF
        box = layout.box()
        row = box.row()
        row.prop(self, "prop_add_roof", toggle=True, icon="MESH_CONE", text="Roof System")
        if self.prop_add_roof:
            col = box.column(align=True)
            col.prop(self, "prop_roof_type", text="")
            col.prop(self, "prop_roof_overhang")
            col.prop(self, "prop_roof_height")



    def build_shape(self, bm):
        print(f"DEBUG: build_shape running with w={self.prop_width} l={self.prop_length} h={self.prop_height}")
        w = self.prop_width
        l = self.prop_length
        h = self.prop_height
        fh = self.prop_foundation_height
        
        # 0. OPENING LOGIC
        opening_data = {"FRONT": [], "BACK": [], "LEFT": [], "RIGHT": []}
        
        if self.prop_door_active:
            opening_data["FRONT"].append({
                "type": "DOOR", "center": self.prop_door_offset_x,
                "width": self.prop_door_width, "height": self.prop_door_height, "sill": 0.0
            })
            
        if self.prop_win_active_list:
            win_cfg = [
                (self.prop_win_front_active, "FRONT", self.prop_win_front_offset),
                (self.prop_win_back_active, "BACK", self.prop_win_back_offset),
                (self.prop_win_left_active, "LEFT", self.prop_win_left_offset),
                (self.prop_win_right_active, "RIGHT", self.prop_win_right_offset),
            ]
            for active, wall, offset in win_cfg:
                if active:
                    opening_data[wall].append({
                        "type": "WIN", "center": offset,
                        "width": self.prop_win_width, "height": self.prop_win_height, 
                        "sill": self.prop_win_elevation
                    })

        # ------------------------------------------------------------------
        # 1. FOUNDATION & FLOOR SYSTEM
        # ------------------------------------------------------------------
        joist_w = 0.05
        joist_h = 0.2
        floor_thick = 0.04
        
        # House Foundation
        # Grid of piers
        piers_x = max(2, int(w / 2.0))
        piers_y = max(2, int(l / 2.0))
        pier_size = 0.3
        
        for ix in range(piers_x + 1):
            x_pos = -w/2 + (w * (ix / piers_x))
            for iy in range(piers_y + 1):
                y_pos = -l/2 + (l * (iy / piers_y))
                create_cube_helper(bm, Vector((x_pos, y_pos, fh/2)), (pier_size, pier_size, fh), 0)
        
        # House Floor Frame
        if self.prop_vis_framing:
            # Joists
            num_joists = int(l / 0.4) + 1 
            for i in range(num_joists):
                y_j = -l/2 + (i * (l / max(1, num_joists-1)))
                create_cube_helper(bm, Vector((0, y_j, fh + joist_h/2)), (w, joist_w, joist_h), 4)

            # Rims
            create_cube_helper(bm, Vector((-w/2, 0, fh + joist_h/2)), (joist_w, l, joist_h), 4) 
            create_cube_helper(bm, Vector((w/2, 0, fh + joist_h/2)), (joist_w, l, joist_h), 4)

        # Flooring
        create_cube_helper(bm, Vector((0, 0, fh + joist_h + floor_thick/2)), (w, l, floor_thick), 1, subdivide=True)

        # ------------------------------------------------------------------
        # PORCH SYSTEM
        # ------------------------------------------------------------------
        porch_w = self.prop_porch_width
        porch_off = self.prop_porch_offset_x
        porch_d = self.prop_porch_depth
        
        # Porch Bounds
        # Center is at porch_off.
        # X range: [porch_off - porch_w/2, porch_off + porch_w/2]
        # Y range: [-l/2 - porch_d, -l/2]
        
        p_x_min = porch_off - porch_w/2
        p_x_max = porch_off + porch_w/2
        p_y_end = -l/2 - porch_d
        
        if self.prop_add_porch:
            # Piers
            piers_p = max(2, int(porch_w / 2.0))
            for ix in range(piers_p + 1):
                x_pos = p_x_min + (porch_w * (ix / piers_p))
                create_cube_helper(bm, Vector((x_pos, p_y_end, fh/2)), (pier_size, pier_size, fh), 0)
            
            if self.prop_vis_framing:
                # Joists
                p_joists = int(porch_d / 0.4) + 1
                for i in range(p_joists):
                    ratio = i / max(1, p_joists - 1)
                    y_j = -l/2 - (ratio * porch_d)
                    create_cube_helper(bm, Vector((porch_off, y_j, fh + joist_h/2)), (porch_w, joist_w, joist_h), 4)
                
                # Rims (Sides)
                create_cube_helper(bm, Vector((p_x_min + joist_w/2, -l/2 - porch_d/2, fh + joist_h/2)), (joist_w, porch_d, joist_h), 4)
                create_cube_helper(bm, Vector((p_x_max - joist_w/2, -l/2 - porch_d/2, fh + joist_h/2)), (joist_w, porch_d, joist_h), 4)
                # Front Rim
                create_cube_helper(bm, Vector((porch_off, p_y_end + joist_w/2, fh + joist_h/2)), (porch_w, joist_w, joist_h), 4)

            # Decking
            create_cube_helper(bm, Vector((porch_off, -l/2 - porch_d/2, fh + joist_h + floor_thick/2)), (porch_w, porch_d, floor_thick), 1)

        floor_top_z = fh + joist_h + floor_thick
        
        # ------------------------------------------------------------------
        # 3. WALLS
        # ------------------------------------------------------------------
        stud_d = 0.1
        stud_w = 0.05
        # Plates
        plate_z = floor_top_z + 0.025
        top_plate_z = floor_top_z + h - 0.025
        stud_h = h - 0.1
        stud_z = floor_top_z + 0.05 + stud_h/2

        def build_stud_wall_complex(start_p, end_p, spacing, openings):
            if not self.prop_vis_framing: return
            vec = end_p - start_p
            wall_len = vec.length
            if wall_len < 0.01: return
            
            unit = vec.normalized()
            center_wall = (start_p + end_p)/2
            
            # Parse Openings
            plate_cuts = [] 
            ops_processed = []
            for op in openings:
                dist_center = (wall_len/2) + op['center']
                op_min = dist_center - op['width']/2
                op_max = dist_center + op['width']/2
                ops_processed.append({
                    'min': op_min, 'max': op_max, 'sill': op['sill'], 
                    'height': op['height'], 'width': op['width'], 
                    'center_dist': dist_center, 'type': op['type']
                })
                if op['type'] == 'DOOR': plate_cuts.append((op_min, op_max))
            
            is_x_aligned = abs(vec.y) < 0.5 
            
            # Bottom Plate (Cut)
            curr_d = 0.0
            sorted_cuts = sorted(plate_cuts, key=lambda x: x[0])
            final_segs = []
            for cut in sorted_cuts:
                if cut[0] > curr_d: final_segs.append((curr_d, cut[0]))
                curr_d = max(curr_d, cut[1])
            if curr_d < wall_len: final_segs.append((curr_d, wall_len))
            
            for seg in final_segs:
                if (seg[1] - seg[0]) > 0.01:
                    seg_pos = start_p + (unit * ((seg[0]+seg[1])/2))
                    p_dim = (seg[1]-seg[0], stud_d, 0.05) if is_x_aligned else (stud_d, seg[1]-seg[0], 0.05)
                    create_cube_helper(bm, Vector((seg_pos.x, seg_pos.y, plate_z)), p_dim, 4)
            
            # Top Plate
            tp_dim = (wall_len, stud_d, 0.05) if is_x_aligned else (stud_d, wall_len, 0.05)
            create_cube_helper(bm, Vector((center_wall.x, center_wall.y, top_plate_z)), tp_dim, 4)
            
            # Studs & Openings
            count = int(wall_len / spacing)
            for k in range(count + 1):
                dist = k * wall_len / max(1, count)
                hit_op = False
                for op in ops_processed:
                    if dist > (op['min']+0.02) and dist < (op['max']-0.02):
                        hit_op = True
                        # Cripples
                        if op['sill'] > 0.1: # Below
                            crip_h = op['sill'] - 0.05
                            pos = start_p + (unit * dist)
                            s_dim = (stud_w, stud_d, crip_h) if is_x_aligned else (stud_d, stud_w, crip_h)
                            create_cube_helper(bm, Vector((pos.x, pos.y, floor_top_z + 0.05 + crip_h/2)), s_dim, 4)
                        
                        header_bot = floor_top_z + op['sill'] + op['height']
                        space_top = (top_plate_z - 0.025) - header_bot
                        if space_top > 0.1: # Above
                            crip_st = header_bot + 0.1 # header 10cm
                            c_h = (top_plate_z - 0.025) - crip_st
                            if c_h > 0:
                                pos = start_p + (unit * dist)
                                s_dim = (stud_w, stud_d, c_h) if is_x_aligned else (stud_d, stud_w, c_h)
                                create_cube_helper(bm, Vector((pos.x, pos.y, crip_st + c_h/2)), s_dim, 4)
                        break
                if not hit_op:
                    pos = start_p + (unit * dist)
                    s_dim = (stud_w, stud_d, stud_h) if is_x_aligned else (stud_d, stud_w, stud_h)
                    create_cube_helper(bm, Vector((pos.x, pos.y, stud_z)), s_dim, 4)
            
            # Headers/Trimmers/Geo
            for op in ops_processed:
                # Kings
                s_dim = (stud_w, stud_d, stud_h) if is_x_aligned else (stud_d, stud_w, stud_h)
                p_l = start_p + (unit * op['min'])
                p_r = start_p + (unit * op['max'])
                create_cube_helper(bm, Vector((p_l.x, p_l.y, stud_z)), s_dim, 4)
                create_cube_helper(bm, Vector((p_r.x, p_r.y, stud_z)), s_dim, 4)
                
                # Header
                h_z = floor_top_z + op['sill'] + op['height'] + 0.05
                h_dim = (op['width'], stud_d, 0.1) if is_x_aligned else (stud_d, op['width'], 0.1)
                p_c = start_p + (unit * op['center_dist'])
                create_cube_helper(bm, Vector((p_c.x, p_c.y, h_z)), h_dim, 4)
                
                # Sill
                if op['type'] == 'WIN':
                    si_z = floor_top_z + op['sill'] - 0.025
                    si_dim = (op['width'], stud_d, 0.05) if is_x_aligned else (stud_d, op['width'], 0.05)
                    create_cube_helper(bm, Vector((p_c.x, p_c.y, si_z)), si_dim, 4)
                    
                # Geo checks
                if self.prop_vis_openings:
                    mat = 8 if op['type'] == 'DOOR' else 7
                    z_geo = floor_top_z + op['sill'] + op['height']/2
                    dim_geo = (op['width']-0.02, 0.05, op['height']-0.02) if is_x_aligned else (0.05, op['width']-0.02, op['height']-0.02)
                    create_cube_helper(bm, Vector((p_c.x, p_c.y, z_geo)), dim_geo, mat)

        build_stud_wall_complex(Vector((-w/2, -l/2 + stud_d/2, 0)), Vector((w/2, -l/2 + stud_d/2, 0)), self.prop_stud_spacing, opening_data["FRONT"])
        build_stud_wall_complex(Vector((w/2, l/2 - stud_d/2, 0)), Vector((-w/2, l/2 - stud_d/2, 0)), self.prop_stud_spacing, opening_data["BACK"])
        build_stud_wall_complex(Vector((-w/2 + stud_d/2, l/2, 0)), Vector((-w/2 + stud_d/2, -l/2, 0)), self.prop_stud_spacing, opening_data["LEFT"])
        build_stud_wall_complex(Vector((w/2 - stud_d/2, -l/2, 0)), Vector((w/2 - stud_d/2, l/2, 0)), self.prop_stud_spacing, opening_data["RIGHT"])

        # Sheathing (Simplified with tiling)
        ext_thick = 0.02
        sheath_z = floor_top_z + h/2
        
        def build_sheathing_complex(start_p, end_p, openings, offset_vec):
            if not self.prop_vis_sheathing: return
            vec = end_p - start_p
            wall_len = vec.length
            unit = vec.normalized()
            is_x = abs(vec.y) < 0.5
            ops = sorted([{'min': (wall_len/2)+o['center']-o['width']/2, 
                           'max': (wall_len/2)+o['center']+o['width']/2,
                           'sill': o['sill'], 'height': o['height']} for o in openings], key=lambda x: x['min'])
            curr_d = 0.0
            for op in ops:
                if op['min'] > curr_d:
                    sl = op['min'] - curr_d
                    pos = start_p + (unit * (curr_d + sl/2)) + offset_vec
                    sz = (sl, ext_thick, h) if is_x else (ext_thick, sl, h)
                    sz = (sl, ext_thick, h) if is_x else (ext_thick, sl, h)
                    create_cube_helper(bm, Vector((pos.x, pos.y, sheath_z)), sz, 2, subdivide=True)
                # Above/Below
                if op['sill'] > 0.05:
                    pos = start_p + (unit * ((op['min']+op['max'])/2)) + offset_vec
                    sz = (op['max']-op['min'], ext_thick, op['sill']) if is_x else (ext_thick, op['max']-op['min'], op['sill'])
                    create_cube_helper(bm, Vector((pos.x, pos.y, floor_top_z + op['sill']/2)), sz, 2)
                top = op['sill'] + op['height']
                if top < h:
                    rem = h - top
                    pos = start_p + (unit * ((op['min']+op['max'])/2)) + offset_vec
                    sz = (op['max']-op['min'], ext_thick, rem) if is_x else (ext_thick, op['max']-op['min'], rem)
                    create_cube_helper(bm, Vector((pos.x, pos.y, floor_top_z + top + rem/2)), sz, 2)
                curr_d = op['max']
            if curr_d < wall_len:
                sl = wall_len - curr_d
                pos = start_p + (unit * (curr_d + sl/2)) + offset_vec
                sz = (sl, ext_thick, h) if is_x else (ext_thick, sl, h)
                create_cube_helper(bm, Vector((pos.x, pos.y, sheath_z)), sz, 2, subdivide=True)

        build_sheathing_complex(Vector((-w/2 - ext_thick, -l/2, 0)), Vector((w/2 + ext_thick, -l/2, 0)), opening_data["FRONT"], Vector((0, -stud_d/2 - ext_thick/2, 0)))
        build_sheathing_complex(Vector((w/2 + ext_thick, l/2, 0)), Vector((-w/2 - ext_thick, l/2, 0)), opening_data["BACK"], Vector((0, stud_d/2 + ext_thick/2, 0)))
        build_sheathing_complex(Vector((-w/2, l/2, 0)), Vector((-w/2, -l/2, 0)), opening_data["LEFT"], Vector((-stud_d/2 - ext_thick/2, 0, 0)))
        build_sheathing_complex(Vector((w/2, -l/2, 0)), Vector((w/2, l/2, 0)), opening_data["RIGHT"], Vector((stud_d/2 + ext_thick/2, 0, 0)))

        # 4. LOFT
        if self.prop_add_loft and self.prop_vis_framing:
            lz = floor_top_z + self.prop_loft_height
            loft_len = l * 0.4
            num_l = int(loft_len / 0.4) + 1
            for i in range(num_l):
                y_j = (l/2 - loft_len) + (i * (loft_len / max(1, num_l-1)))
                create_cube_helper(bm, Vector((0, y_j, lz + joist_h/2)), (w - 2*stud_d, joist_w, joist_h), 4)
            create_cube_helper(bm, Vector((0, l/2 - loft_len/2, lz + joist_h + floor_thick/2)), (w - 2*stud_d, loft_len, floor_thick), 1)

        # 5. ROOF & POSTS
        if self.prop_add_roof:
            roof_z = floor_top_z + h
            overhang = self.prop_roof_overhang
            rise = self.prop_roof_height
            
            # Base Roof Bounds (House)
            rb_1 = Vector((-w/2 - overhang, -l/2 - overhang, roof_z))
            rb_2 = Vector((w/2 + overhang, -l/2 - overhang, roof_z))
            rb_3 = Vector((w/2 + overhang, l/2 + overhang, roof_z))
            rb_4 = Vector((-w/2 - overhang, l/2 + overhang, roof_z))
            
            # Post Logic
            if self.prop_add_porch and self.prop_vis_framing:
                # Posts adhere to the DECK corners, not the Roof Overhang
                deck_x_min = p_x_min
                deck_x_max = p_x_max
                deck_y = p_y_end
                
                # Check if roof covers posts. If porch is wider than house + overhang, extend roof?
                # For now, just extend roof Y to cover porch Y. X might be independent.
                
                # Extend Y of Roof to cover deck + overhang
                porch_roof_y = deck_y - overhang
                if porch_roof_y < rb_1.y:
                    rb_1.y = porch_roof_y
                    rb_2.y = porch_roof_y
                
                # If Porch is Wide, we might need to flare the roof or just let posts stick out?
                # User likely wants roof to cover porch.
                # Let's expand roof width if porch width > house width
                if (deck_x_min - overhang) < rb_1.x:
                    rb_1.x = deck_x_min - overhang
                    rb_4.x = deck_x_min - overhang
                if (deck_x_max + overhang) > rb_2.x:
                    rb_2.x = deck_x_max + overhang
                    rb_3.x = deck_x_max + overhang

                p_h = roof_z - floor_top_z
                post_dim = 0.09 # 4x4 ~ 90-100mm. User requested smaller than previous.
                post_z = floor_top_z + p_h/2
                
                # Align Posts to Deck Corners (Inset slightly so they stand ON the deck)
                inset = post_dim / 2
                
                # Left Post
                create_cube_helper(bm, Vector((deck_x_min + inset, deck_y + inset, post_z)), (post_dim, post_dim, p_h), 4)
                # Right Post
                create_cube_helper(bm, Vector((deck_x_max - inset, deck_y + inset, post_z)), (post_dim, post_dim, p_h), 4)
                
                # Beam
                beam_z = roof_z - 0.1
                bw = (deck_x_max - deck_x_min) + 2*overhang
                create_cube_helper(bm, Vector((porch_off, deck_y + inset, beam_z)), (bw, post_dim, 0.2), 4)

            # Draw Roof
            if self.prop_vis_roof:
                if self.prop_roof_type == 'SHED':
                    rh_3 = rb_3 + Vector((0, 0, rise))
                    rh_4 = rb_4 + Vector((0, 0, rise))
                    v_list = [bm.verts.new(rb_1), bm.verts.new(rb_2), bm.verts.new(rh_3), bm.verts.new(Vector((rh_4.x, rh_4.y, rh_4.z)))]
                    f = bm.faces.new(v_list)
                    f.material_index = 5
                    res = bmesh.ops.extrude_face_region(bm, geom=[f])
                    verts_ext = [v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]
                    bmesh.ops.translate(bm, vec=Vector((0,0,0.1)), verts=verts_ext)
                    
                elif self.prop_roof_type == 'GABLE':
                    rp_front = Vector(((rb_1.x+rb_2.x)/2, rb_1.y, roof_z + rise))
                    rp_back = Vector(((rb_3.x+rb_4.x)/2, rb_3.y, roof_z + rise))
                    
                    v1, v2, v3, v4 = bm.verts.new(rb_1), bm.verts.new(rb_2), bm.verts.new(rb_3), bm.verts.new(rb_4)
                    vp1, vp2 = bm.verts.new(rp_front), bm.verts.new(rp_back)
                    
                    fL = bm.faces.new([v1, vp1, vp2, v4])
                    fL.material_index = 5
                    fR = bm.faces.new([v2, v3, vp2, vp1])
                    fR.material_index = 5
                    
                    if self.prop_vis_sheathing:
                        fG1 = bm.faces.new([v1, v2, vp1])
                        fG1.material_index = 2
                        fG2 = bm.faces.new([v4, vp2, v3])
                        fG2.material_index = 2

        # 6. CLEANUP & EDGE ROLES
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        slot_layer = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not slot_layer: slot_layer = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
        for e in bm.edges:
            if e.is_boundary: e[slot_layer] = 1 
            elif e.calc_face_angle(0) > 0.5: e[slot_layer] = 2 
            else: e[slot_layer] = 4
        
        # Auditor Requirement: Verify Perimeter (Slot 1)
        count_p = len([e for e in bm.edges if e[slot_layer] == 1])
        if count_p == 0 and len(bm.verts) > 0:
             # Fallback: Mark the ground contact edges as Perimeter
             min_z = min([v.co.z for v in bm.verts])
             for e in bm.edges:
                 if e.verts[0].co.z < (min_z + 0.01) and e.verts[1].co.z < (min_z + 0.01):
                     e[slot_layer] = 1

# HARNESS COMPATIBILITY WRAPPER
# The test harness expects a module-level build_shape function.
def build_shape(self, bm):
    MASSA_OT_ArchTinyHome.build_shape(self, bm)
