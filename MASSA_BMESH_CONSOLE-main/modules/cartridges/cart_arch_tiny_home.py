import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

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

class MASSA_OT_ArchTinyHome(Massa_OT_Base):
    bl_idname = "massa.gen_arch_tiny_home"
    bl_label = "ARCH: Tiny Home"
    bl_description = "Tiny Home Generator with Structural Framing"
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
            0: {"name": "Foundation", "phys": "CONCRETE_RAW", "uv": "UNWRAP"},
            1: {"name": "Floor", "phys": "WOOD_PLANKS", "uv": "UNWRAP"},
            2: {"name": "Wall Ext", "phys": "WOOD_PAINTED", "uv": "UNWRAP"},
            3: {"name": "Wall Int", "phys": "GYPSUM_PAINTED", "uv": "UNWRAP"},
            4: {"name": "Framing", "phys": "WOOD_RAW", "uv": "UNWRAP"},
            5: {"name": "Roof", "phys": "METAL_ROOF", "uv": "UNWRAP"},
            6: {"name": "Trim", "phys": "WOOD_VARNISH", "uv": "UNWRAP"},
            7: {"name": "Glass", "phys": "GLASS_CLEAR", "uv": "FIT"},
            8: {"name": "Door", "phys": "WOOD_VARNISH", "uv": "UNWRAP"},
            9: {"name": "Fixtures", "phys": "CERAMIC_WHITE", "uv": "UNWRAP"},
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
        builder = MassaBuilder(bm)

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
                builder.create_box(pier_size, pier_size, fh).translate(x_pos, y_pos, fh/2) \
                       .tag_slot(0).select_boundary().tag_edge_role(1)
        
        # House Floor Frame
        if self.prop_vis_framing:
            # Joists
            num_joists = int(l / 0.4) + 1 
            for i in range(num_joists):
                y_j = -l/2 + (i * (l / max(1, num_joists-1)))
                builder.create_box(w, joist_w, joist_h).translate(0, y_j, fh + joist_h/2) \
                       .tag_slot(4).select_boundary().tag_edge_role(1)

            # Rims
            builder.create_box(joist_w, l, joist_h).translate(-w/2, 0, fh + joist_h/2).tag_slot(4).select_boundary().tag_edge_role(1)
            builder.create_box(joist_w, l, joist_h).translate(w/2, 0, fh + joist_h/2).tag_slot(4).select_boundary().tag_edge_role(1)

        # Flooring
        builder.create_box(w, l, floor_thick).translate(0, 0, fh + joist_h + floor_thick/2) \
               .tag_slot(1).select_boundary().tag_edge_role(1)

        # ------------------------------------------------------------------
        # PORCH SYSTEM
        # ------------------------------------------------------------------
        porch_w = self.prop_porch_width
        porch_off = self.prop_porch_offset_x
        porch_d = self.prop_porch_depth
        
        p_x_min = porch_off - porch_w/2
        p_x_max = porch_off + porch_w/2
        p_y_end = -l/2 - porch_d
        
        if self.prop_add_porch:
            # Piers
            piers_p = max(2, int(porch_w / 2.0))
            for ix in range(piers_p + 1):
                x_pos = p_x_min + (porch_w * (ix / piers_p))
                builder.create_box(pier_size, pier_size, fh).translate(x_pos, p_y_end, fh/2) \
                       .tag_slot(0).select_boundary().tag_edge_role(1)
            
            if self.prop_vis_framing:
                # Joists
                p_joists = int(porch_d / 0.4) + 1
                for i in range(p_joists):
                    ratio = i / max(1, p_joists - 1)
                    y_j = -l/2 - (ratio * porch_d)
                    builder.create_box(porch_w, joist_w, joist_h).translate(porch_off, y_j, fh + joist_h/2) \
                           .tag_slot(4).select_boundary().tag_edge_role(1)
                
                # Rims
                builder.create_box(joist_w, porch_d, joist_h).translate(p_x_min + joist_w/2, -l/2 - porch_d/2, fh + joist_h/2).tag_slot(4).select_boundary().tag_edge_role(1)
                builder.create_box(joist_w, porch_d, joist_h).translate(p_x_max - joist_w/2, -l/2 - porch_d/2, fh + joist_h/2).tag_slot(4).select_boundary().tag_edge_role(1)
                builder.create_box(porch_w, joist_w, joist_h).translate(porch_off, p_y_end + joist_w/2, fh + joist_h/2).tag_slot(4).select_boundary().tag_edge_role(1)

            # Decking
            builder.create_box(porch_w, porch_d, floor_thick).translate(porch_off, -l/2 - porch_d/2, fh + joist_h + floor_thick/2) \
                   .tag_slot(1).select_boundary().tag_edge_role(1)

        floor_top_z = fh + joist_h + floor_thick
        
        # ------------------------------------------------------------------
        # 3. WALLS
        # ------------------------------------------------------------------
        stud_d = 0.1
        stud_w = 0.05

        # Helpers
        def build_stud_wall_complex(start_p, end_p, spacing, openings):
            if not self.prop_vis_framing: return
            vec = end_p - start_p
            wall_len = vec.length
            if wall_len < 0.01: return
            unit = vec.normalized()
            center_wall = (start_p + end_p)/2
            plate_z = floor_top_z + 0.025
            top_plate_z = floor_top_z + h - 0.025
            stud_h = h - 0.1
            stud_z = floor_top_z + 0.05 + stud_h/2
            
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
            
            # Bottom Plate
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
                    builder.create_box(*p_dim, center=Vector((seg_pos.x, seg_pos.y, plate_z))).tag_slot(4).select_boundary().tag_edge_role(1)
            
            # Top Plate
            tp_dim = (wall_len, stud_d, 0.05) if is_x_aligned else (stud_d, wall_len, 0.05)
            builder.create_box(*tp_dim, center=Vector((center_wall.x, center_wall.y, top_plate_z))).tag_slot(4).select_boundary().tag_edge_role(1)
            
            # Studs & Openings
            count = int(wall_len / spacing)
            for k in range(count + 1):
                dist = k * wall_len / max(1, count)
                hit_op = False
                for op in ops_processed:
                    if dist > (op['min']+0.02) and dist < (op['max']-0.02):
                        hit_op = True
                        if op['sill'] > 0.1: # Below
                            crip_h = op['sill'] - 0.05
                            pos = start_p + (unit * dist)
                            s_dim = (stud_w, stud_d, crip_h) if is_x_aligned else (stud_d, stud_w, crip_h)
                            builder.create_box(*s_dim, center=Vector((pos.x, pos.y, floor_top_z + 0.05 + crip_h/2))).tag_slot(4).select_boundary().tag_edge_role(1)
                        
                        header_bot = floor_top_z + op['sill'] + op['height']
                        space_top = (top_plate_z - 0.025) - header_bot
                        if space_top > 0.1: # Above
                            crip_st = header_bot + 0.1
                            c_h = (top_plate_z - 0.025) - crip_st
                            if c_h > 0:
                                pos = start_p + (unit * dist)
                                s_dim = (stud_w, stud_d, c_h) if is_x_aligned else (stud_d, stud_w, c_h)
                                builder.create_box(*s_dim, center=Vector((pos.x, pos.y, crip_st + c_h/2))).tag_slot(4).select_boundary().tag_edge_role(1)
                        break
                if not hit_op:
                    pos = start_p + (unit * dist)
                    s_dim = (stud_w, stud_d, stud_h) if is_x_aligned else (stud_d, stud_w, stud_h)
                    builder.create_box(*s_dim, center=Vector((pos.x, pos.y, stud_z))).tag_slot(4).select_boundary().tag_edge_role(1)
            
            for op in ops_processed:
                # Kings
                s_dim = (stud_w, stud_d, stud_h) if is_x_aligned else (stud_d, stud_w, stud_h)
                p_l = start_p + (unit * op['min'])
                p_r = start_p + (unit * op['max'])
                builder.create_box(*s_dim, center=Vector((p_l.x, p_l.y, stud_z))).tag_slot(4).select_boundary().tag_edge_role(1)
                builder.create_box(*s_dim, center=Vector((p_r.x, p_r.y, stud_z))).tag_slot(4).select_boundary().tag_edge_role(1)
                # Header
                h_z = floor_top_z + op['sill'] + op['height'] + 0.05
                h_dim = (op['width'], stud_d, 0.1) if is_x_aligned else (stud_d, op['width'], 0.1)
                p_c = start_p + (unit * op['center_dist'])
                builder.create_box(*h_dim, center=Vector((p_c.x, p_c.y, h_z))).tag_slot(4).select_boundary().tag_edge_role(1)
                # Sill
                if op['type'] == 'WIN':
                    si_z = floor_top_z + op['sill'] - 0.025
                    si_dim = (op['width'], stud_d, 0.05) if is_x_aligned else (stud_d, op['width'], 0.05)
                    builder.create_box(*si_dim, center=Vector((p_c.x, p_c.y, si_z))).tag_slot(4).select_boundary().tag_edge_role(1)
                # Geo
                if self.prop_vis_openings:
                    mat = 8 if op['type'] == 'DOOR' else 7
                    z_geo = floor_top_z + op['sill'] + op['height']/2
                    dim_geo = (op['width']-0.02, 0.05, op['height']-0.02) if is_x_aligned else (0.05, op['width']-0.02, op['height']-0.02)
                    builder.create_box(*dim_geo, center=Vector((p_c.x, p_c.y, z_geo))).tag_slot(mat).select_boundary().tag_edge_role(1)
                    if mat == 7: # Glass FIT
                        builder.tag_uvs(1.0, 'FIT')

        build_stud_wall_complex(Vector((-w/2, -l/2 + stud_d/2, 0)), Vector((w/2, -l/2 + stud_d/2, 0)), self.prop_stud_spacing, opening_data["FRONT"])
        build_stud_wall_complex(Vector((w/2, l/2 - stud_d/2, 0)), Vector((-w/2, l/2 - stud_d/2, 0)), self.prop_stud_spacing, opening_data["BACK"])
        build_stud_wall_complex(Vector((-w/2 + stud_d/2, l/2, 0)), Vector((-w/2 + stud_d/2, -l/2, 0)), self.prop_stud_spacing, opening_data["LEFT"])
        build_stud_wall_complex(Vector((w/2 - stud_d/2, -l/2, 0)), Vector((w/2 - stud_d/2, l/2, 0)), self.prop_stud_spacing, opening_data["RIGHT"])

        # Sheathing
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
                    builder.create_box(*sz, center=Vector((pos.x, pos.y, sheath_z))).tag_slot(2).select_boundary().tag_edge_role(1)
                if op['sill'] > 0.05:
                    pos = start_p + (unit * ((op['min']+op['max'])/2)) + offset_vec
                    sz = (op['max']-op['min'], ext_thick, op['sill']) if is_x else (ext_thick, op['max']-op['min'], op['sill'])
                    builder.create_box(*sz, center=Vector((pos.x, pos.y, floor_top_z + op['sill']/2))).tag_slot(2).select_boundary().tag_edge_role(1)
                top = op['sill'] + op['height']
                if top < h:
                    rem = h - top
                    pos = start_p + (unit * ((op['min']+op['max'])/2)) + offset_vec
                    sz = (op['max']-op['min'], ext_thick, rem) if is_x else (ext_thick, op['max']-op['min'], rem)
                    builder.create_box(*sz, center=Vector((pos.x, pos.y, floor_top_z + top + rem/2))).tag_slot(2).select_boundary().tag_edge_role(1)
                curr_d = op['max']
            if curr_d < wall_len:
                sl = wall_len - curr_d
                pos = start_p + (unit * (curr_d + sl/2)) + offset_vec
                sz = (sl, ext_thick, h) if is_x else (ext_thick, sl, h)
                builder.create_box(*sz, center=Vector((pos.x, pos.y, sheath_z))).tag_slot(2).select_boundary().tag_edge_role(1)

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
                builder.create_box(w - 2*stud_d, joist_w, joist_h).translate(0, y_j, lz + joist_h/2).tag_slot(4).select_boundary().tag_edge_role(1)
            builder.create_box(w - 2*stud_d, loft_len, floor_thick).translate(0, l/2 - loft_len/2, lz + joist_h + floor_thick/2).tag_slot(1).select_boundary().tag_edge_role(1)

        # 5. ROOF & POSTS
        if self.prop_add_roof:
            roof_z = floor_top_z + h
            overhang = self.prop_roof_overhang
            rise = self.prop_roof_height
            
            rb_1 = Vector((-w/2 - overhang, -l/2 - overhang, roof_z))
            rb_2 = Vector((w/2 + overhang, -l/2 - overhang, roof_z))
            rb_3 = Vector((w/2 + overhang, l/2 + overhang, roof_z))
            rb_4 = Vector((-w/2 - overhang, l/2 + overhang, roof_z))
            
            if self.prop_add_porch and self.prop_vis_framing:
                deck_x_min = p_x_min
                deck_x_max = p_x_max
                deck_y = p_y_end
                
                porch_roof_y = deck_y - overhang
                if porch_roof_y < rb_1.y:
                    rb_1.y = porch_roof_y
                    rb_2.y = porch_roof_y
                
                if (deck_x_min - overhang) < rb_1.x:
                    rb_1.x = deck_x_min - overhang
                    rb_4.x = deck_x_min - overhang
                if (deck_x_max + overhang) > rb_2.x:
                    rb_2.x = deck_x_max + overhang
                    rb_3.x = deck_x_max + overhang

                p_h = roof_z - floor_top_z
                post_dim = 0.09
                post_z = floor_top_z + p_h/2
                inset = post_dim / 2
                
                builder.create_box(post_dim, post_dim, p_h).translate(deck_x_min + inset, deck_y + inset, post_z).tag_slot(4).select_boundary().tag_edge_role(1)
                builder.create_box(post_dim, post_dim, p_h).translate(deck_x_max - inset, deck_y + inset, post_z).tag_slot(4).select_boundary().tag_edge_role(1)
                
                beam_z = roof_z - 0.1
                bw = (deck_x_max - deck_x_min) + 2*overhang
                builder.create_box(bw, post_dim, 0.2).translate(porch_off, deck_y + inset, beam_z).tag_slot(4).select_boundary().tag_edge_role(1)

            if self.prop_vis_roof:
                if self.prop_roof_type == 'SHED':
                    # Single slanted box
                    pass # Keep manual or approximate with slanted box?
                    # Manual construction of roof shape is cleaner for specific angles
                    rh_3 = rb_3 + Vector((0, 0, rise))
                    rh_4 = rb_4 + Vector((0, 0, rise))
                    # Use manual vertices
                    v_list = [bm.verts.new(rb_1), bm.verts.new(rb_2), bm.verts.new(rh_3), bm.verts.new(Vector((rh_4.x, rh_4.y, rh_4.z)))]
                    f = bm.faces.new(v_list)
                    f.material_index = 5
                    # Update builder active faces to this face
                    builder.active_faces = [f]
                    builder.extrude(0.1, axis=Vector((0,0,1))).tag_slot(5).select_boundary().tag_edge_role(1)
                    
                elif self.prop_roof_type == 'GABLE':
                    # Triangular Prism
                    rp_front = Vector(((rb_1.x+rb_2.x)/2, rb_1.y, roof_z + rise))
                    rp_back = Vector(((rb_3.x+rb_4.x)/2, rb_3.y, roof_z + rise))
                    
                    # Create two slanted boxes like in mobile home
                    roof_l_val = rb_3.y - rb_1.y
                    roof_w_val = rb_2.x - rb_1.x
                    slope_len = math.sqrt((roof_w_val/2)**2 + rise**2)
                    angle = math.atan2(rise, roof_w_val/2)
                    center_y = (rb_1.y + rb_3.y)/2
                    
                    builder.create_box(slope_len + 0.2, roof_l_val, 0.1) \
                           .rotate(math.degrees(-angle), 'Y') \
                           .translate(rb_1.x + roof_w_val/4, center_y, roof_z + rise/2) \
                           .tag_slot(5).select_boundary().tag_edge_role(1)

                    builder.create_box(slope_len + 0.2, roof_l_val, 0.1) \
                           .rotate(math.degrees(angle), 'Y') \
                           .translate(rb_2.x - roof_w_val/4, center_y, roof_z + rise/2) \
                           .tag_slot(5).select_boundary().tag_edge_role(1)
                    
                    if self.prop_vis_sheathing:
                        # Gable Ends
                        builder.create_box(w, wall_th, rise).translate(0, -l/2 + wall_th/2, roof_z + rise/2).tag_slot(2).select_boundary().tag_edge_role(1)
                        builder.create_box(w, wall_th, rise).translate(0, l/2 - wall_th/2, roof_z + rise/2).tag_slot(2).select_boundary().tag_edge_role(1)

        # 6. CLEANUP
        builder.clean()
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1).tag_socket(9) # Anchor
