import bpy
import bmesh
import math
from mathutils import Vector, Matrix
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty
from ...operators.massa_base import Massa_OT_Base
from ...modules.massa_builder import MassaBuilder

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

class MASSA_OT_ArchMobileHome(Massa_OT_Base):
    bl_idname = "massa.gen_arch_mobile_home"
    bl_label = "ARCH: Mobile Home"
    bl_description = "Mobile Home Generator (Single/Double Wide)"
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
            0: {"name": "Skirting/Fdn", "phys": "SYNTH_PLASTIC", "uv": "UNWRAP"},
            1: {"name": "Floor", "phys": "WOOD_PLANKS", "uv": "UNWRAP"},
            2: {"name": "Siding", "phys": "VINYL_SIDING", "uv": "UNWRAP"},
            3: {"name": "Wall Int", "phys": "GYPSUM_PAINTED", "uv": "UNWRAP"},
            4: {"name": "Framing", "phys": "WOOD_RAW", "uv": "UNWRAP"},
            5: {"name": "Roof", "phys": "METAL_ROOF", "uv": "UNWRAP"},
            6: {"name": "Trim", "phys": "ALUMINUM_PAINTED", "uv": "UNWRAP"},
            7: {"name": "Glass", "phys": "GLASS_CLEAR", "uv": "FIT"},
            8: {"name": "Door", "phys": "METAL_PAINTED", "uv": "UNWRAP"},
            9: {"name": "Details", "phys": "PLASTIC_ROUGH", "uv": "UNWRAP", "sock": True}, # Also Sockets
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
        builder = MassaBuilder(bm)

        w = self.prop_width
        l = self.prop_length
        h = self.prop_height
        fh = self.prop_foundation_height
        
        # 1. FOUNDATION
        beam_off = w * 0.3
        builder.create_box(0.1, l, fh).translate(-beam_off, 0, fh/2).tag_slot(4).select_boundary().tag_edge_role(1)
        builder.create_box(0.1, l, fh).translate(beam_off, 0, fh/2).tag_slot(4).select_boundary().tag_edge_role(1)
        
        if self.prop_skirting:
            skirt_th = 0.02
            builder.create_box(skirt_th, l, fh).translate(-w/2, 0, fh/2).tag_slot(0).select_boundary().tag_edge_role(1)
            builder.create_box(skirt_th, l, fh).translate(w/2, 0, fh/2).tag_slot(0).select_boundary().tag_edge_role(1)
            builder.create_box(w, skirt_th, fh).translate(0, -l/2, fh/2).tag_slot(0).select_boundary().tag_edge_role(1)
            builder.create_box(w, skirt_th, fh).translate(0, l/2, fh/2).tag_slot(0).select_boundary().tag_edge_role(1)
        else:
            piers_y = int(l / 2.0)
            for iy in range(piers_y + 1):
                y_pos = -l/2 + (l * (iy / piers_y))
                builder.create_box(0.4, 0.4, fh).translate(-beam_off, y_pos, fh/2).tag_slot(0).select_boundary().tag_edge_role(1)
                builder.create_box(0.4, 0.4, fh).translate(beam_off, y_pos, fh/2).tag_slot(0).select_boundary().tag_edge_role(1)

        # 2. FLOOR
        f_h = 0.2
        floor_z = fh + f_h/2
        builder.create_box(w, l, f_h).translate(0, 0, floor_z).tag_slot(1).select_boundary().tag_edge_role(1)
        floor_top = fh + f_h

        # 3. WALLS
        wall_th = 0.1
        wall_h = h
        
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

            base_mat = 4 if self.prop_geo_siding else 2

            # Helper for walls
            def build_wall_side(start, end, holes, mat, siding_mode=False):
                self.create_segmented_wall(builder, start, end, wall_h, wall_th if not siding_mode else 0.02,
                                           holes, floor_top, mat, siding_mode, self.prop_siding_size)

            # Left (-X)
            start_L = Vector((-w/2 + wall_th/2, -l/2 + wall_th/2, 0))
            end_L = Vector((-w/2 + wall_th/2, l/2 - wall_th/2, 0))
            
            build_wall_side(start_L, end_L, holes_left, base_mat)
            if self.prop_geo_siding:
                build_wall_side(Vector((-w/2 - 0.01, -l/2, 0)), Vector((-w/2 - 0.01, l/2, 0)), holes_left, 2, True)
            
            # Left Interior
            build_wall_side(Vector((-w/2 + wall_th + 0.01, -l/2, 0)), Vector((-w/2 + wall_th + 0.01, l/2, 0)), holes_left, 3)

            # Right (+X)
            start_R = Vector((w/2 - wall_th/2, -l/2 + wall_th/2, 0))
            end_R = Vector((w/2 - wall_th/2, l/2 - wall_th/2, 0))
            build_wall_side(start_R, end_R, holes_right, base_mat)
            if self.prop_geo_siding:
                build_wall_side(Vector((w/2 + 0.01, -l/2, 0)), Vector((w/2 + 0.01, l/2, 0)), holes_right, 2, True)
            
            # Right Interior
            build_wall_side(Vector((w/2 - wall_th - 0.01, -l/2, 0)), Vector((w/2 - wall_th - 0.01, l/2, 0)), holes_right, 3)
                    
            # Ends (Front/Back)
            # Simplified for Ends (No holes for now)
            # -Y
            builder.create_box(w - 2*wall_th, wall_th, wall_h).translate(0, -l/2 + wall_th/2, floor_top + wall_h/2) \
                   .tag_slot(base_mat).select_boundary().tag_edge_role(1)
            # +Y
            builder.create_box(w - 2*wall_th, wall_th, wall_h).translate(0, l/2 - wall_th/2, floor_top + wall_h/2) \
                   .tag_slot(base_mat).select_boundary().tag_edge_role(1)
            
            # 3B. CEILING
            ceil_z = floor_top + wall_h - 0.02
            builder.create_box(w - 2*wall_th, l - 2*wall_th, 0.02).translate(0, 0, ceil_z) \
                   .tag_slot(3).select_boundary().tag_edge_role(1)

        # GENERATE WINDOW/DOOR GEO
        if self.prop_vis_openings:
            if self.prop_door_active:
                self.create_window_geo(builder, Vector((w/2 - 0.05, -l/4, floor_top + self.prop_door_height/2)),
                                       self.prop_door_width, self.prop_door_height, 6, 8)
                
            if self.prop_win_count > 0:
                side_x = -w/2 + 0.05
                win_y_start = -l/2 + 1.0
                win_space = (l - 2.0) / max(1, self.prop_win_count)
                w_width = 0.9 if self.prop_win_standard == 'DOUBLE' else 1.5
                w_height = 1.5 if self.prop_win_standard == 'DOUBLE' else 1.2
                win_z = floor_top + 0.8 + w_height/2
                
                for i in range(self.prop_win_count):
                    wy = win_y_start + (i * win_space) + win_space/2
                    self.create_window_geo(builder, Vector((side_x, wy, win_z)), w_width, w_height, 6, 7)
        
        # 4. ROOF
        if self.prop_vis_roof:
            roof_z = floor_top + h
            overhang = self.prop_roof_overhang
            rise = self.prop_roof_height

            # Simple Gable Roof using Prism (Cylinder 3 segments)
            # Or manually building it.
            # Let's create two slanted boxes.

            roof_l = l + 2*overhang
            roof_w = w + 2*overhang
            slope_len = math.sqrt((roof_w/2)**2 + rise**2)
            angle = math.atan2(rise, roof_w/2)

            # Left Slope
            builder.create_box(slope_len + 0.2, roof_l, 0.1) \
                   .rotate(math.degrees(-angle), 'Y') \
                   .translate(-roof_w/4, 0, roof_z + rise/2) \
                   .tag_slot(5).select_boundary().tag_edge_role(1)

            # Right Slope
            builder.create_box(slope_len + 0.2, roof_l, 0.1) \
                   .rotate(math.degrees(angle), 'Y') \
                   .translate(roof_w/4, 0, roof_z + rise/2) \
                   .tag_slot(5).select_boundary().tag_edge_role(1)

            # Gable Ends (Triangles)
            # Create a box and rotate? Or just a box for the wall part up to peak.
            # Simplified: Box centered.
            # Ideally we fill the triangle.
            # Can use a box rotated 45 deg cut?
            # Let's stick to simple box filling the gap roughly.
            builder.create_box(w, wall_th, rise).translate(0, -l/2 + wall_th/2, roof_z + rise/2) \
                   .tag_slot(2).select_boundary().tag_edge_role(1) # Gable wall
            builder.create_box(w, wall_th, rise).translate(0, l/2 - wall_th/2, roof_z + rise/2) \
                   .tag_slot(2).select_boundary().tag_edge_role(1)

        # 5. PORCH
        if self.prop_add_porch and self.prop_vis_porch:
            p_w, p_d, p_off = self.prop_porch_width, self.prop_porch_depth, self.prop_porch_offset
            
            p_x, p_y = (p_off, -l/2 - p_d/2) if self.prop_porch_loc == 'END' else (w/2 + p_d/2, p_off)
            p_dim_actual = (p_w, p_d, fh) if self.prop_porch_loc == 'END' else (p_d, p_w, fh)
            
            builder.create_box(p_dim_actual[0], p_dim_actual[1], fh) \
                   .translate(p_x, p_y, floor_top - fh/2) \
                   .tag_slot(1).select_boundary().tag_edge_role(1)
            
            # Calculate corners
            if self.prop_porch_loc == 'END':
                px_min, px_max = p_x - p_w/2, p_x + p_w/2
                py_min, py_max = p_y - p_d/2, p_y + p_d/2
            else:
                px_min, px_max = p_x - p_dim_actual[0]/2, p_x + p_dim_actual[0]/2
                py_min, py_max = p_y - p_dim_actual[1]/2, p_y + p_dim_actual[1]/2
                
            # Railing
            post_h = h if self.prop_porch_roof else 1.0
            
            corners = [
                Vector((px_min+0.1, py_min+0.1, floor_top + post_h/2)),
                Vector((px_max-0.1, py_min+0.1, floor_top + post_h/2)),
                Vector((px_max-0.1, py_max-0.1, floor_top + post_h/2)),
                Vector((px_min+0.1, py_max-0.1, floor_top + post_h/2))
            ]

            for c in corners:
                builder.create_box(0.08, 0.08, post_h, center=c).tag_slot(6).select_boundary().tag_edge_role(1)
            
            if self.prop_porch_roof:
                beam_z = floor_top + post_h - 0.1
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
                
                builder.create_box(r_dim_x, r_dim_y, 0.1).translate(r_loc_x, r_loc_y, beam_z + 0.15) \
                       .tag_slot(5).select_boundary().tag_edge_role(1)

        # 7. CLEANUP
        builder.clean()

        # Sockets
        builder.select_faces_by_normal(Vector((0,0,-1)), tolerance=0.1).tag_socket(9) # Bottom Anchor

    def create_segmented_wall(self, builder, start, end, height, thickness, holes, floor_z, mat_idx, siding_mode=False, siding_size=0.2):
        vec = end - start
        length = vec.length
        u = vec.normalized()
        
        holes_sorted = sorted(holes, key=lambda x: x['dist'])
        cursor = 0.0
        wall_angle = math.atan2(u.y, u.x)

        def place_segment(s_dist, e_dist, h_base, h_top):
            seg_len = e_dist - s_dist
            if seg_len < 0.001: return

            seg_h = h_top - h_base
            if seg_h < 0.001: return

            mid_dist = (s_dist + e_dist) / 2
            mid_z = (h_base + h_top) / 2

            # Position relative to start
            pos = start + u * mid_dist
            pos.z = mid_z

            if siding_mode:
                # Tiled Siding
                k_start = math.ceil((h_base - floor_z) / siding_size)
                k_end = math.floor((h_top - floor_z) / siding_size)

                if k_end >= k_start:
                    for i in range(k_start, k_end + 1):
                        pz = floor_z + i*siding_size + siding_size/2
                        if pz < h_base - 0.01 or pz > h_top + 0.01: continue

                        ppos = start + u * mid_dist
                        ppos.z = pz

                        builder.create_box(seg_len, thickness * 1.2, siding_size * 0.9) \
                               .rotate(math.degrees(wall_angle), 'Z') \
                               .translate(ppos.x, ppos.y, ppos.z) \
                               .tag_slot(mat_idx).select_boundary().tag_edge_role(1)
            else:
                # Solid Panel
                builder.create_box(seg_len, thickness, seg_h) \
                       .rotate(math.degrees(wall_angle), 'Z') \
                       .translate(pos.x, pos.y, pos.z) \
                       .tag_slot(mat_idx).select_boundary().tag_edge_role(1)

        for h in holes_sorted:
            h_center_dist = h['dist']
            h_w = h['width']
            h_h = h['height']
            h_z = h['z_sill'] # Bottom of window

            h_start = h_center_dist - h_w/2
            h_end = h_center_dist + h_w/2
            h_top = h_z + h_h

            if h_start > cursor:
                place_segment(cursor, h_start, floor_z, floor_z + height)

            if (h_z - floor_z) > 0.01:
                place_segment(h_start, h_end, floor_z, h_z)

            if (floor_z + height - h_top) > 0.01:
                place_segment(h_start, h_end, h_top, floor_z + height)

            cursor = h_end

        if cursor < length:
            place_segment(cursor, length, floor_z, floor_z + height)

    def create_window_geo(self, builder, loc, width, height, mat_frame, mat_glass):
        f_th = 0.1
        f_w = 0.08

        # Outer Frame Top
        builder.create_box(f_th+0.02, width, f_w).translate(loc.x, loc.y, loc.z + height/2 - f_w/2) \
               .tag_slot(mat_frame).select_boundary().tag_edge_role(1)
        # Bot
        builder.create_box(f_th+0.02, width, f_w).translate(loc.x, loc.y, loc.z - height/2 + f_w/2) \
               .tag_slot(mat_frame).select_boundary().tag_edge_role(1)
        # Sides
        builder.create_box(f_th+0.02, f_w, height - 2*f_w).translate(loc.x, loc.y - width/2 + f_w/2, loc.z) \
               .tag_slot(mat_frame).select_boundary().tag_edge_role(1)
        builder.create_box(f_th+0.02, f_w, height - 2*f_w).translate(loc.x, loc.y + width/2 - f_w/2, loc.z) \
               .tag_slot(mat_frame).select_boundary().tag_edge_role(1)

        # Glass
        builder.create_box(0.02, width - 2*f_w, height - 2*f_w, center=loc) \
               .tag_slot(mat_glass).tag_uvs(1.0, 'FIT') # Glass is FIT
