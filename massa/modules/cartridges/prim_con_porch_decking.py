"""
Filename: modules/cartridges/prim_con_porch_decking.py
Content: Parametric Porch Decking with Supports, Stairs, and Details
Status: NEW (v1.2)
"""

import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from ...operators.massa_base import Massa_OT_Base
from mathutils import Vector, Matrix

CARTRIDGE_META = {
    "name": "Con: Porch Decking",
    "id": "prim_con_porch_decking",
    "icon": "GRID",
    "scale_class": "MACRO",
    "flags": {
        "USE_WELD": False,
        "ALLOW_FUSE": True,
        "ALLOW_SOLIDIFY": False,
        "FIX_DEGENERATE": True,
        "LOCK_PIVOT": True,
    },
}

class MASSA_OT_prim_con_porch_decking(Massa_OT_Base):
    bl_idname = "massa.gen_prim_con_porch_decking"
    bl_label = "Construction Porch Deck"
    bl_description = "Detailed Western Decking with Footings and Brackets"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- DIMENSIONS ---
    width: FloatProperty(name="Width", default=4.0, min=1.0, unit="LENGTH")
    length: FloatProperty(name="Length", default=3.0, min=1.0, unit="LENGTH")
    height: FloatProperty(name="Deck Height", default=1.0, min=0.2, unit="LENGTH")

    shape_type: EnumProperty(
        name="Shape",
        items=[
            ('RECT', "Rectangle", "Standard"),
            ('TRAP', "Trapezoid", "Tapered End"),
            ('HEX', "Hexagon", "Double Taper"),
        ],
        default='RECT'
    )
    shape_taper: FloatProperty(name="Taper Ratio", default=0.6, min=0.1, max=1.5)

    post_spacing: FloatProperty(name="Post Spacing", default=2.0, min=1.0, unit="LENGTH")
    post_size: FloatProperty(name="Post Size", default=0.15, min=0.05, unit="LENGTH")

    # --- DECKING ---
    board_width: FloatProperty(name="Board Width", default=0.14, min=0.05, unit="LENGTH")
    board_gap: FloatProperty(name="Board Gap", default=0.005, min=0.0, unit="LENGTH")
    overhang: FloatProperty(name="Overhang", default=0.05, min=0.0, unit="LENGTH")

    # --- STAIRS ---
    add_stairs: BoolProperty(name="Add Stairs", default=False)
    stair_loc: EnumProperty(
        name="Location",
        items=[('FRONT', "Front (-Y)", ""), ('LEFT', "Left (-X)", ""), ('RIGHT', "Right (+X)", ""), ('BACK', "Back (+Y)", "")],
        default='FRONT'
    )
    stair_pos: FloatProperty(name="Stair Pos", default=0.5, min=0.1, max=0.9, subtype='FACTOR', description="Position along the side (0-1)")
    stair_width: FloatProperty(name="Stair Width", default=1.2, min=0.5, unit="LENGTH")
    stair_tread_nose: FloatProperty(name="Tread Nosing", default=0.03, min=0.0)
    stair_cleat: BoolProperty(name="Add Cleats", default=True)
    stringer_thick: FloatProperty(name="Stringer Thick", default=0.05, min=0.02)

    # --- RAILING ---
    add_rail: BoolProperty(name="Add Railing", default=True)
    rail_style: EnumProperty(
        name="Style",
        items=[
            ('MINIMAL', "Minimal", "Rails Only"),
            ('VERTICAL', "Vertical", "Pickets"),
            ('HORIZONTAL', "Horizontal", "Modern Boards"),
            ('CABLE', "Cable", "Thin Wires"),
        ],
        default='VERTICAL'
    )
    rail_height: FloatProperty(name="Rail Height", default=1.0, unit="LENGTH")
    rail_density: FloatProperty(name="Density", default=0.12, min=0.05, description="Picket spacing or Rail Count")
    post_cap_size: FloatProperty(name="Cap Overhang", default=0.02, min=0.0)

    # Exclusions
    rail_rem_front: BoolProperty(name="No Front", default=False)
    rail_rem_back: BoolProperty(name="No Back", default=False)
    rail_rem_left: BoolProperty(name="No Left", default=False)
    rail_rem_right: BoolProperty(name="No Right", default=False)

    # --- ADVANCED / NEW ---
    board_orient: EnumProperty(name="Board Dir", items=[('X', "Width-wise", ""), ('Y', "Length-wise", "")], default='X')
    rail_lift: FloatProperty(name="Rail Lift", default=0.0, min=0.0, max=0.5, description="Raise railing off deck")
    rail_bottom_b: BoolProperty(name="Bottom Rail", default=True, description="Add bottom rail frame")
    stringer_beam_h: FloatProperty(name="Stringer H", default=0.25, min=0.1, unit="LENGTH")
    stair_rail: BoolProperty(name="Stair Railing", default=True)

    def draw_shape_ui(self, layout):
        box = layout.box()
        row = box.row()
        row.label(text="Dimensions", icon="ARROW_LEFTRIGHT")

        col = box.column(align=True)
        col.prop(self, "width")
        col.prop(self, "length")
        col.prop(self, "height")

        col.separator()
        col.prop(self, "shape_type")
        if self.shape_type != 'RECT':
            col.prop(self, "shape_taper")

        box.prop(self, "post_spacing")

        box = layout.box()
        box.label(text="Structure", icon="MOD_BUILD")
        box.prop(self, "board_orient")
        box.prop(self, "board_width")
        box.prop(self, "board_gap")
        box.prop(self, "overhang")
        box.prop(self, "post_size")

        box = layout.box()
        # Header Toggle
        row = box.row()
        row.prop(self, "add_stairs", text="Add Stairs", icon="MOD_REMESH")

        if self.add_stairs:
            col = box.column(align=True)
            row = col.row(align=True)
            row.prop(self, "stair_loc")
            row.prop(self, "stair_pos", text="Pos")

            col.prop(self, "stair_width")

            row = col.row(align=True)
            row.prop(self, "stair_tread_nose", text="Nosing")
            row.prop(self, "stringer_thick", text="Thick")
            row.prop(self, "stringer_beam_h", text="Height")

            row = col.row(align=True)
            row.prop(self, "stair_cleat")
            row.prop(self, "stair_rail")

        box = layout.box()
        row = box.row()
        row.prop(self, "add_rail", text="Add Railing", icon="MOD_WIREFRAME")
        if self.add_rail:
            box.prop(self, "rail_style")
            box.prop(self, "rail_height")
            box.prop(self, "rail_density", text="Spacing/Scale")
            box.prop(self, "post_cap_size")

            row = box.row(align=True)
            row.prop(self, "rail_lift")
            row.prop(self, "rail_bottom_b", text="Bot Rail")

            col = box.column(align=True)
            col.label(text="Remove Railing:")
            row = col.row(align=True)
            row.prop(self, "rail_rem_front")
            row.prop(self, "rail_rem_back")
            row = col.row(align=True)
            row.prop(self, "rail_rem_left")
            row.prop(self, "rail_rem_right")

    def get_slot_meta(self):
        return {
            0: {"name": "Boards", "uv": "BOX", "phys": "WOOD_ROUGH"},
            1: {"name": "Frame", "uv": "BOX", "phys": "WOOD_TREATED"},
            2: {"name": "Posts", "uv": "BOX", "phys": "WOOD_PAINTED"},
            3: {"name": "Railing", "uv": "BOX", "phys": "WOOD_PAINTED"},
            4: {"name": "Stairs", "uv": "BOX", "phys": "WOOD_ROUGH"},
            5: {"name": "Footings", "uv": "BOX", "phys": "CONCRETE_ROUGH"},
            6: {"name": "Brackets", "uv": "BOX", "phys": "METAL_ROUGH"},
            7: {"name": "Socket_A", "uv": "SKIP", "sock": True},
            8: {"name": "Socket_B", "uv": "SKIP", "sock": True},
            9: {"name": "Socket_C", "uv": "SKIP", "sock": True},
        }

    # --- HELPERS ---

    def _make_rot_box(self, bm, size, pos, angle_z=0.0, angle_x=0.0, tag=0, tag_layer=None, seam_mode='PRISM'):
        """Helper: Create Rotated Box with Auto-Seams (Snippet A)
        seam_mode: 'PRISM' (Seam Smallest/Ends), 'SLAB' (Seam Largest/TopBot)
        """
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

        if angle_z != 0 or angle_x != 0:
            bmesh.ops.rotate(bm, verts=new_verts, cent=Vector((0,0,0)), matrix=mat)

        # Translate
        bmesh.ops.translate(bm, verts=new_verts, vec=pos)

        # Tag
        if tag_layer:
            for v in new_verts:
                for f in v.link_faces:
                    f[tag_layer] = tag

        # --- SEAM LOGIC ---
        # Get faces from new_verts
        new_faces = list(set(f for v in new_verts for f in v.link_faces))

        if new_faces:
            target_faces = []

            if seam_mode == 'SLAB':
                # Seam the Largest Faces (Front/Back or Top/Bot)
                # Good for Footings, Caps, Stringers
                sorted_faces = sorted(new_faces, key=lambda f: f.calc_area(), reverse=True)
                target_faces = sorted_faces[:2]
            else:
                # 'PRISM' (Default): Seam the Smallest Faces (Caps/Ends)
                # Good for Beams, Boards, Posts
                sorted_faces = sorted(new_faces, key=lambda f: f.calc_area())
                target_faces = sorted_faces[:2]

            # Mark Seams & Edge Roles
            edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")

            for f in target_faces:
                for e in f.edges:
                    e.seam = True
                    if edge_slots:
                        e[edge_slots] = 2 # CONTOUR

        return new_verts

    def _get_x_bounds(self, y):
        w = self.width
        l = self.length
        t = self.shape_taper
        st = self.shape_type

        if st == 'RECT':
            return -w/2, w/2

        # Normalized Y from -1 (Front) to 1 (Back) or 0 to 1
        # Range is -l/2 to l/2.
        # Let's map to 0..1 where 0 is Front (-l/2) and 1 is Back (l/2)
        norm_y = (y + (l/2)) / l
        if norm_y < 0: norm_y = 0
        if norm_y > 1: norm_y = 1

        if st == 'TRAP':
            # Front (-Y) is Tapered (w*t). Back (+Y) is w.
            # User might want the opposite, but this is a reasonable default.
            wf = w * t
            wb = w
            cw = wf + (wb - wf) * norm_y
            return -cw/2, cw/2

        if st == 'HEX':
            # Center (y=0) is Max Width (w). Ends are Tapered (w*t).
            # dist from center
            dist = abs(y) / (l/2) # 0 at center, 1 at ends
            if dist > 1: dist = 1

            # Linear taper from Center to Tip
            cw = w + ((w * t) - w) * dist
            return -cw/2, cw/2

        return -w/2, w/2

    def _get_y_bounds(self, x):
        """Inverse of X bounds for Y-scanline (Length-wise boards).
        For complex shapes (Trap/Hex), we act as if we scan X and find Y limits.
        """
        w = self.width
        l = self.length
        t = self.shape_taper
        st = self.shape_type

        # Ranges: X is -w/2 to w/2 (usually).
        # Y is -l/2 to l/2.

        if st == 'RECT':
            return -l/2, l/2

        # For Trap/Hex, width varies by Y.
        # So finding Y bounds for a given X is solving: X_bound(y) = x
        # TRAP: w(y) = w_front + (w_back - w_front) * norm_y
        # We know x is within [-w(y)/2, w(y)/2].
        # Max width is w. If abs(x) > w/2, no solution.

        if abs(x) > w/2: return 0, 0 # Out of bounds

        # Solving is complex because it's an inequality |x| <= w(y)/2
        # For decking, we just want the valid Y range where the board exists.

        # TRAP: Width increases linearly from Front (-l/2) to Back (l/2).
        # w_min = w*t, w_max = w.
        # If abs(x) < w_min/2, then board exists for ALL Y (-l/2 to l/2).
        # If abs(x) > w_max/2, board exists NOWHERE.
        # If in between, board exists from some y_start to l/2.

        if st == 'TRAP':
            wf = w * t
            if abs(x) <= wf/2: return -l/2, l/2 # Fits in narrowest part

            # Find y where width == 2*abs(x)
            # w_y = wf + (w - wf) * norm_y
            # 2*|x| = wf + (w - wf) * norm_y
            # norm_y = (2*|x| - wf) / (w - wf)
            # norm_y is 0..1. y = (norm_y * l) - l/2

            norm_y = (2*abs(x) - wf) / (w - wf + 0.0001)
            y_start = (norm_y * l) - (l/2)
            # Valid from y_start to Back (+l/2)
            return y_start, l/2

        if st == 'HEX':
            # Tapers at both ends.
            # Max width at y=0. Min width at ends.
            wf = w * t
            if abs(x) <= wf/2: return -l/2, l/2 # Fits everywhere

            # Symmetrical. Finds cutoffs +/- y.
            # w_y = w + (wf - w) * dist  (dist = |y|/(l/2))
            # 2*|x| = w + (wf - w) * (|y|/(l/2))
            # |y|/(l/2) = (2*|x| - w) / (wf - w)
            # |y| = (l/2) * (...)

            ratio = (2*abs(x) - w) / (wf - w + 0.0001)
            # ratio is "dist".
            y_lim = (l/2) * ratio

            # Valid between -y_lim and y_lim?
            # Wait, wf < w. (wf-w) is negative.
            # If x is large (near w/2), ratio is small (near 0).
            # If x is small (near wf/2), ratio is large (near 1).
            # So valid Y is [-y_lim, y_lim].
            return -y_lim, y_lim

        return -l/2, l/2

    def _get_boundary_segments(self):
        """Generates perimeter segments for Rails and Rim Joists."""
        w = self.width
        l = self.length
        t = self.shape_taper
        st = self.shape_type

        pts = []

        # Define Points CCW (Top-Left start, going Right) -> Back Edge First
        # Y+ is Back.

        if st == 'RECT':
            pts = [
                Vector((-w/2, l/2, 0)),  # TL
                Vector((w/2, l/2, 0)),   # TR
                Vector((w/2, -l/2, 0)),  # BR
                Vector((-w/2, -l/2, 0))  # BL
            ]
        elif st == 'TRAP':
            # Back (Top, +Y) is Wide (w). Front (Bot, -Y) is Narrow (w*t)
            wf = w * t
            pts = [
                Vector((-w/2, l/2, 0)),
                Vector((w/2, l/2, 0)),
                Vector((wf/2, -l/2, 0)),
                Vector((-wf/2, -l/2, 0))
            ]
        elif st == 'HEX':
            # Coffin.
            wt = w * t
            pts = [
                Vector((-wt/2, l/2, 0)),  # TL Tip
                Vector((wt/2, l/2, 0)),   # TR Tip
                Vector((w/2, 0, 0)),      # Right Mid
                Vector((wt/2, -l/2, 0)),  # BR Tip
                Vector((-wt/2, -l/2, 0)), # BL Tip
                Vector((-w/2, 0, 0))      # Left Mid
            ]

        segs = []
        for i in range(len(pts)):
            p1 = pts[i]
            p2 = pts[(i+1)%len(pts)]
            vec = p2 - p1

            # Normal (2D XY) pointing OUT.
            # CCW Winding: Tangent is vec. Normal is (-y, x).
            # Verify: Back Edge (Right direction 1,0). Normal (0, 1) -> +Y. Correct.
            n = Vector((-vec.y, vec.x, 0)).normalized()

            # Identify "Side" for Stair logic
            # Normals: +Y=BACK, -Y=FRONT, +X=RIGHT, -X=LEFT
            s_name = 'GENERIC'
            if n.y > 0.7: s_name = 'BACK'
            elif n.y < -0.7: s_name = 'FRONT'
            elif n.x > 0.7: s_name = 'RIGHT'
            elif n.x < -0.7: s_name = 'LEFT'

            segs.append({'p1': p1, 'p2': p2, 'vec': vec, 'len': vec.length, 'norm': n, 'name': s_name})

        return segs

    def _build_stairs_geo(self, bm, anchor_pos, direction, tag_layer):
        """Builds Stairs with Stringers, Cleats, Treads.
        Uses vector math to align geometry to the 'out' direction.
        """
        # vectors
        fwd = direction.normalized()
        right = fwd.cross(Vector((0,0,1)))
        up = Vector((0,0,1))

        # Params
        sw = self.stair_width
        sh = self.height
        rise = 0.18
        run = 0.28
        nosing = self.stair_tread_nose
        cleat_mode = self.stair_cleat
        st_thick = self.stringer_thick

        step_count = int(sh / rise)
        if step_count < 1: return

        # Calculate Pitch for Stringer Rotation
        total_run = step_count * run
        stringer_vec = (fwd * total_run) - (up * sh)
        stringer_len = stringer_vec.length
        # Angle from Horizontal? atan2(z, xy_len) => atan2(-sh, total_run)
        pitch_angle = math.atan2(sh, total_run) # Positive angle of simple triangle

        # Stringer Rotation (Align Box Y to Stringer Vector)
        # We start with a Box along Y. We pitch it DOWN by pitch_angle.
        # But we need to align it to the specific 'fwd' direction.
        # Orientation Matrix:
        # Z points relative 'up' (normal to stringer top)? No, simple box rotation.
        # Let's construct the rotation matrix from the stringer vector.

        str_rot_mat = stringer_vec.to_track_quat('Y', 'Z').to_matrix().to_4x4()

        # Center of Stringer System
        # Start: anchor_pos + (fwd * overhang)  <- Top
        # End: anchor_pos + (fwd * (overhang + total_run)) - (0,0,sh) <- Bottom
        # Midpoint for box creation

        mid_run = (self.overhang + (total_run / 2))
        mid_z = sh / 2

        str_mid_pos = anchor_pos + (fwd * mid_run)
        str_mid_pos.z = mid_z - (rise/2) # Shift down slightly to catch steps?
        # Actually usually stringer top cut aligns with deck rim.

        # TREAD ORIENTATION
        # Tread Y aligns with FWD. X aligns with RIGHT.
        # Box default matches this if we rotate Z to FWD.
        tread_rot_z = math.atan2(fwd.y, fwd.x) - (math.pi/2)
        # Wait, Box Y is depth. FWD is direction.
        # If FWD is (0, -1) [Front], atan2 is -pi/2.
        # Box Y (0,1). We want (0,-1). Rotate 180 (pi).
        # -pi/2 - pi/2 = -pi. Correct.

        # Iterate Steps
        for i in range(step_count):
            # 1. TREADS
            # Z position: Deck Height - (i+1)*rise
            step_z = sh - ((i+1) * rise)
            if step_z < 0: step_z = 0

            # XY Position: Anchor + Fwd * (Overhang + i*Run + Run/2)
            # Center of tread
            dist = self.overhang + (i * run) + (run / 2)
            t_pos = anchor_pos + (fwd * dist)
            t_pos.z = step_z + 0.02 # Add thickness offset

            # Size
            # Y = Run + Nosing
            ty = run + nosing

            # Tag 4 (Stairs)
            # We align the box to the global FWD vector directly?
            # Or use _make_rot_box with Z rotation.
            # Using Z rotation is safer for simple boxes.
            self._make_rot_box(bm, (sw, ty, 0.04), t_pos, tread_rot_z, 0, 4, tag_layer)

            # 2. CLEATS
            if cleat_mode:
                # Under tread, attached to stringer path
                # Pos: Back from tread center by (run/2)? No, center of cleat.
                # Cleat width 0.04.
                # Z: step_z - 0.02 (under tread) - 0.1 (half height of cleat)

                c_z = step_z - 0.1
                c_dist = dist # Same Y
                c_pos_base = anchor_pos + (fwd * c_dist)
                c_pos_base.z = c_z

                # Offset X for L/R stringers
                x_off = (sw/2) - (st_thick/2) - 0.02 # Inside stringer

                c_size = Vector((0.04, 0.2, 0.2)) # Block cleat

                self._make_rot_box(bm, c_size, c_pos_base + (right * -x_off), tread_rot_z, 0, 6, tag_layer)
                self._make_rot_box(bm, c_size, c_pos_base + (right * x_off), tread_rot_z, 0, 6, tag_layer)

        # 3. STRINGERS (Custom Geometry for flat cuts)
        # We need a profile that has a vertical start (top) and horizontal end (bottom).
        # Thickness = st_thick. Depth = beam_h.

        # Calculate local vectors
        # Side view (2D in Plane defined by Fwd/Up)
        # Top Point: str_top (Back/Top)
        # Bot Point: str_bot (Front/Bottom)

        # We want the stringer to be a beam connecting these.
        # Top face cut: Vertical (against rim joist). Normal -Fwd.
        # Bottom face cut: Horizontal (on ground). Normal -Z.

        # Let's define the 4 corners of the stringer profile in the Side plane, then extrude by Thickness.

        # Geometric helpers
        # Top-Inner Corner: str_top
        # Top-Outer Corner: str_top - (0,0,bh)? No.
        # The stringer has a pitch.

        # Construct vertices explicitly relative to anchor

        # Top-Back (Meeting Deck Rim): str_top.
        # We want the "Cut" to be vertical. So the face is defined by Z.
        # But wait, stringer thickness is X. Depth is Z-ish.

        bh = self.stringer_beam_h

        # DEFINITIONS
        str_top = anchor_pos + (fwd * self.overhang)
        str_top.z = sh - 0.2 # Below deck

        str_bot = anchor_pos + (fwd * (self.overhang + total_run))
        str_bot.z = 0

        vec_s = str_bot - str_top

        # Pitch Vector: vec_s = str_bot - str_top.
        # Normal to Pitch (in Fwd/Up plane):
        # fwd is (x,y,0). pitch is (x,y,-z).
        # Cross product of Right and Pitch?

        pitch_n = right.cross(vec_s.normalized()).normalized() # Points "Up/Back" perpendicular to slope

        # Bottom Edge Line starts at: str_top - (pitch_n * bh)
        # Ends at: str_bot - (pitch_n * bh)

        # NOW, we intersect these Ideal Lines with the Cut Planes.
        # Plane 1 (Top): Vertical Plane at str_top position? Or Deck Rim line?
        # Usually rests against Rim. So Plane Normal = -Fwd. Point = str_top.
        # Plane 2 (Bottom): Horizontal Plane at Z=0. Normal = +Z. Point = (0,0,0).

        # Let's just create points manually.
        # P1 = str_top (Top-Back corner)
        # P2 = Ground intersect of Top Edge line.
        #      Top Line: P = str_top + t * vec_s.
        #      Find t where P.z = 0.
        #      str_top.z + t * vec_s.z = 0  => t = -str_top.z / vec_s.z
        t_ground_top = -str_top.z / vec_s.z
        p2 = str_top + (vec_s * t_ground_top)

        # P3 = Ground intersect of Bottom Edge line.
        #      Bot Line Start: B_start = str_top - (pitch_n * bh)
        #      Bot Edge Vector is same: vec_s.
        #      P = B_start + t * vec_s.
        #      Find t where P.z = 0.
        B_start = str_top - (pitch_n * bh)
        t_ground_bot = -B_start.z / vec_s.z
        p3 = B_start + (vec_s * t_ground_bot)

        # P4 = Deck intersect of Bottom Edge line?
        #      Vertical cut at str_top plane?
        #      Plane defined by normal FWD, point str_top.
        #      Line: P = B_start + t * vec_s.
        #      (P - str_top) dot FWD = 0?
        #      Usually simplified: The cut is Vertical. Z changes, XY is fixed.
        #      XY of P4 should match XY of str_top.
        #      P4 = B_start + t * vec_s
        #      P4.xy = str_top.xy?
        #      This implies vertical cut.
        #      We need t such that (B_start + t*vec_s).xy = str_top.xy essentially (projected on fwd).

        # Simplified Poly Construction:
        # V1: str_top
        # V2: p2 (Tip on ground)
        # V3: p3 (Heel on ground)
        # V4: ... The point under V1.
        #     V4 = V1 - (0,0, vertical_cut_len).
        #     Geometry trig: vertical_cut_len = bh / cos(pitch) approx.
        #     Let's manually find V4 by projecting Bottom Edge Line to the vertical plane of V1.

        # Project B_start along vec_s until it hits Plane(Point=str_top, Normal=Fwd).
        # dist to plane = (str_top - B_start) dot Fwd / (vec_s dot fwd)

        b_start = str_top - (pitch_n * bh)

        # But wait, if pitch_n points Up/Back, B_start is "Lower".
        # Let's verify normal direction.
        # vec_s goes Down-Forward. Right is Right.
        # Right cross Pitch = (1,0,0) x (0,1,-1) -> (0, 1, 1). Points Up/Forward.
        # So pitch_n points "Away" from the stringer meat?
        # If we want thickness *below* the line, we subtract pitch_n * bh?
        # Let's assume yes.

        # Intersect Logic
        def intersect_line_plane(l_start, l_dir, p_co, p_no):
            denom = l_dir.dot(p_no)
            if abs(denom) < 1e-6: return l_start # Parallel
            t = (p_co - l_start).dot(p_no) / denom
            return l_start + (l_dir * t)

        # Top-Edge is segment P1->P2.
        # Bot-Edge is segment P4->P3.

        # P1 = str_top
        p1 = str_top
        # P2 (Ground Toe) = intersect_line_plane(str_top, vec_s, Vector((0,0,0)), Vector((0,0,1)))
        p2 = intersect_line_plane(str_top, vec_s.normalized(), Vector((0,0,0)), Vector((0,0,1)))

        # P4 (Top Heel) = intersect_line_plane(b_start, vec_s, str_top, fwd) (Vertical Cut)
        # Actually normal is FWD (cut plane faces Back).
        p4 = intersect_line_plane(b_start, vec_s.normalized(), str_top, fwd)

        # P3 (Ground Heel) = intersect_line_plane(b_start, vec_s, Vector((0,0,0)), Vector((0,0,1)))
        p3 = intersect_line_plane(b_start, vec_s.normalized(), Vector((0,0,0)), Vector((0,0,1)))

        # Function to build stringer from these 4 points
        def make_custom_stringer(offset_vec):
            # Convert 4 points to 3D with offset
            # 4 points are on the "Center Plane" of the stringer?
            # Or one side? Let's assume center.

            verts = [p1, p4, p3, p2] # CW or CCW.
            # Extrude thick.

            # Create Face
            # Shift by offset
            vs = []
            for v in verts:
                vs.append(bm.verts.new(v + offset_vec))

            # Face expects CCW.
            # P1(TopFront), P4(TopBack-Low), P3(BotBack), P2(BotFront).
            # Let's just make face vs[0], vs[1], vs[2], vs[3]
            f = bm.faces.new(vs)
            f[tag_layer] = 1

            # Extrude
            # Extrude direction: 'right' * st_thick?
            # We want centered thickness.
            # So move face by -right * th/2. Extrude by right * th.

            bmesh.ops.translate(bm, verts=vs, vec=(-right * st_thick/2))

            r = bmesh.ops.extrude_face_region(bm, geom=[f])

            # Move extruded verts
            verts_extruded = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=verts_extruded, vec=(right * st_thick))

            # Tag all faces
            all_faces = [f] + [e for e in r['geom'] if isinstance(e, bmesh.types.BMFace)]
            for af in all_faces: af[tag_layer] = 1

            # --- SEAMS (Snippet A Variant: Large Sides) ---
            # For shapes like stringers, we want to isolate the two large sides.
            # Caps are the thickness strip? No, usually we want to unwind the strip.
            # So seaming the PERIMETER of the two large faces works best.
            # Face 'f' is Side 1.
            # There is another large face in 'all_faces' that is parallel to 'f'.

            # Let's find the two largest faces (The Sides)
            sorted_sides = sorted(all_faces, key=lambda face: face.calc_area(), reverse=True)
            sides = sorted_sides[:2]

            edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")

            for s in sides:
                for e in s.edges:
                    e.seam = True
                    if edge_slots:
                        e[edge_slots] = 2 # CONTOUR

        x_shift = (sw/2) - (st_thick/2)
        make_custom_stringer(right * x_shift)
        make_custom_stringer(right * -x_shift)

        # 4. STAIR RAILING FIXED
        if self.stair_rail:
            rh = self.rail_height

            # Rail Vector (Parallel to Pitch)
            # Just lift the Top Edge line (P1->P2) by Normal * offset?
            # Or simply +Z.
            # Rail usually has vertical posts. Handrail follows pitch Z+rh.
            # Picket posts are vertical.

            # Let's use the exact same P1->P2 line from stringer, shifted UP by rh.
            # P1 = str_top. P2 = Ground Toe.
            # Offset Z by rh.

            # Also apply X/Y offset for spacing (Left/Right)

            for mul in [-1, 1]:
                side_offset = right * (sw/2 * mul)

                # Start/End of Handrail
                # Align with stringer top/bot
                r_start = p1 + side_offset + Vector((0,0,rh))
                r_end = p2 + side_offset + Vector((0,0,rh))

                # Handrail Mesh (Box along vector)
                r_vec = r_end - r_start
                r_len = r_vec.length
                r_mid = (r_start + r_end) / 2

                # Orientation
                # Z should align with r_vec? No, Y usually aligns with length in our helper.
                # r_vec is the Y axis for the box.
                # Construct matrix
                rx = right
                ry = r_vec.normalized()
                rz = rx.cross(ry).normalized()

                mat_r = Matrix.Identity(4)
                mat_r[0][0], mat_r[1][0], mat_r[2][0] = rx
                mat_r[0][1], mat_r[1][1], mat_r[2][1] = ry
                mat_r[0][2], mat_r[1][2], mat_r[2][2] = rz

                # Create Handrail
                r_box = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=Vector((0.06, r_len, 0.06)), verts=r_box["verts"])
                bmesh.ops.rotate(bm, verts=r_box["verts"], cent=Vector((0,0,0)), matrix=mat_r)
                bmesh.ops.translate(bm, verts=r_box["verts"], vec=r_mid)
                for v in r_box["verts"]:
                    for f in v.link_faces: f[tag_layer] = 3

                # Pickets
                if self.rail_style == 'VERTICAL':
                    p_count = step_count * 2
                    for p in range(p_count):
                        t = p / p_count
                        # Base on Stringer Top Line (P1->P2)
                        # Real P1 is str_top + side_offset
                        base_line_pt = p1.lerp(p2, t) + side_offset

                        # Height is rh.
                        # Center Z = base.z + rh/2
                        pick_pos = Vector((base_line_pt.x, base_line_pt.y, base_line_pt.z + rh/2))

                        self._make_rot_box(bm, (0.04, 0.04, rh), pick_pos, 0, 0, 3, tag_layer)

    def build_shape(self, bm):
        # 0. INIT
        tag_layer = bm.faces.layers.int.new("MAT_TAG")

        h = self.height
        bw = self.board_width
        bg = self.board_gap

        # 1. DECK BOARDS (Tag 0)
        # Scanline algorithm
        # Orientation logic:
        # If board_orient == 'X' (Width-wise, Standard), we scan Y.
        # If board_orient == 'Y' (Length-wise), we scan X.

        do_scan_x = (self.board_orient == 'Y')

        if not do_scan_x:
            # SCAN Y (Standard)
            start_y = -(self.length/2) + bw/2
            count = int(self.length / (bw + bg))
            for i in range(count):
                y_pos = start_y + (i * (bw + bg))
                x_min, x_max = self._get_x_bounds(y_pos)
                row_w = x_max - x_min + (self.overhang * 2)
                center_x = (x_min + x_max) / 2

                if row_w > 0.05:
                    self._make_rot_box(bm, (row_w, bw, 0.03), Vector((center_x, y_pos, h)), 0, 0, 0, tag_layer)
        else:
            # SCAN X (Length-wise boards)
            start_x = -(self.width/2) + bw/2
            count = int(self.width / (bw + bg))
            for i in range(count):
                x_pos = start_x + (i * (bw + bg))
                y_min, y_max = self._get_y_bounds(x_pos)
                if y_min == 0 and y_max == 0: continue # Invalid

                row_l = y_max - y_min + (self.overhang * 2)
                center_y = (y_min + y_max) / 2

                if row_l > 0.05:
                     self._make_rot_box(bm, (bw, row_l, 0.03), Vector((x_pos, center_y, h)), 0, 0, 0, tag_layer)

        # 2. FRAMING (Rim Joists) & RAILING BOUNDARY
        segments = self._get_boundary_segments()

        # Stair Placement Logic
        stair_seg_idx = -1
        stair_int = None

        if self.add_stairs:
            # Find best segment matching 'stair_loc'
            target_map = {'FRONT': 'FRONT', 'BACK': 'BACK', 'LEFT': 'LEFT', 'RIGHT': 'RIGHT'}
            req_side = target_map.get(self.stair_loc, 'FRONT')

            # Fallback for Hex (match nearest normal)
            # Already computed in 'name'
            candidates = [i for i, s in enumerate(segments) if s['name'] == req_side]
            if candidates:
                stair_seg_idx = candidates[0] # Take first match

                # Calc interval
                seg = segments[stair_seg_idx]
                slen = seg['len']

                center_d = slen * self.stair_pos
                half_w = self.stair_width / 2
                stair_int = (center_d - half_w, center_d + half_w)

                # Build Stairs
                anchor_pt = seg['p1'] + (seg['vec'].normalized() * center_d)
                # Adjust anchor to rim edge
                anchor_pt.z = h
                self._build_stairs_geo(bm, anchor_pt, seg['norm'], tag_layer)

        # Generates Rim & Rails
        for i, seg in enumerate(segments):
            p1, p2 = seg['p1'], seg['p2']
            vec = seg['vec']
            slen = seg['len']
            norm = seg['norm']
            mid = (p1 + p2) / 2

            # Angle Z
            ang_z = math.atan2(vec.y, vec.x)

            # Rim Joist (Tag 1)
            # Box centered at mid, rotated.
            # Size: Length=slen, Thickness=0.04, Height=0.2
            # Offset: Inward by thickness/2?
            # Rim sits under deck.

            rim_pos = Vector((mid.x, mid.y, h - 0.115))
            # Shift inward? Rim usually flush with board end (minus overhang).
            # Our bounds were "Deck Surface". Rim is usually inset by overhang.
            # Simple: Just place it.
            self._make_rot_box(bm, (slen, 0.04, 0.2), rim_pos, ang_z, 0, 1, tag_layer)

            # Posts & Railing
            # Structural posts should generate regardless of railing.

            # Check exclusions (applies to Railing mainly)
            is_rem = False
            sname = seg['name']

            # Helper to check removal
            def check_rem(n):
                if n == 'FRONT' and self.rail_rem_front: return True
                if n == 'BACK' and self.rail_rem_back: return True
                if n == 'LEFT' and self.rail_rem_left: return True
                if n == 'RIGHT' and self.rail_rem_right: return True
                return False

            is_rem = check_rem(sname)

            # Check Next Segment removal (for Corner Post logic)
            next_seg = segments[(i + 1) % len(segments)]
            is_next_rem = check_rem(next_seg['name'])

            # Subdivide
            num_posts = max(1, int(slen / self.post_spacing))
            interval = slen / num_posts

            pts_d = [j * interval for j in range(num_posts + 1)]

            # Filter Stair Zone
            active_d = []
            is_stair_side = (i == stair_seg_idx)

            for d in pts_d:
                ok = True
                if is_stair_side and stair_int:
                    if stair_int[0] + 0.05 < d < stair_int[1] - 0.05:
                        ok = False
                if ok: active_d.append(d)

            # Force Stair Posts
            if is_stair_side and stair_int:
                active_d.append(stair_int[0])
                active_d.append(stair_int[1])

            # CRITICAL FIX: Sort active_d!
            # Appending stair points breaks order, causing railing gaps/jumps.
            active_d = sorted(list(set(active_d)))

            # Deduplicate points carefully (floating point tol)
            # Fixes "Doubling the post at the end caps" logic.
            # Especially for Trapezoid/Hex where segments meet.
            # But this loop is per-segment.
            # Doubling usually happens at vertices where two segments meet.
            # P2 of Seg A is P1 of Seg B.
            # We place posts at D=0 and D=len.
            # If we do D=0 for every segment, we duplicate at corners.
            # OPTION: Only place D=0. Don't place D=len?
            # Or unique list of global points?

            # Simple fix: Skip the last point if it's the start of next?
            # But we are iterating segments.
            # Let's filter active_d.
            # If d is near slen, we skip IF it's not the very last segment of an open loop?
            # This is a closed loop.
            # Let's skip the END point of each segment (d=slen).
            # The START point (d=0) of the *next* segment will cover it.

            # Filter active_d
            final_d = []
            for d in active_d:
                # If d is close to slen (End Point)
                if abs(d - slen) < 0.01:
                    # Logic:
                    # If Next Segment is Active (Not Removed) -> It will draw the post at 0. So We SKIP.
                    # If Next Segment is REMOVED -> It won't draw. So We MUST DRAW.
                    if not is_next_rem:
                        continue

                final_d.append(d)

            # Ensure sorting
            final_d = sorted(list(set(final_d)))

            # Draw Posts (Tag 2)
            ps = self.post_size
            rh = self.rail_height

            for d in final_d:
                pt = p1 + (vec.normalized() * d)

                # Check Stair Zone for Structural Posts?
                # Usually stairs need posts too at the top.
                # If d is exactly at stair gap start/end, we keep it.

                # 1. Structural Post (Ground to Deck)
                # Tag 2 (Posts)
                # Height = h - 0.2 (From Top of Footing to Deck)
                # Center Z = 0.2 + (Height / 2)
                p_h = h - 0.2
                if p_h > 0:
                    spos = Vector((pt.x, pt.y, 0.2 + p_h/2))
                    self._make_rot_box(bm, (ps, ps, p_h), spos, ang_z, 0, 2, tag_layer)

                # 2. Footing (Tag 5)
                # At Z=0. Size slightly larger than post.
                f_size = ps * 2.0
                f_pos = Vector((pt.x, pt.y, 0.1)) # 0.2 height
                self._make_rot_box(bm, (f_size, f_size, 0.2), f_pos, ang_z, 0, 5, tag_layer, seam_mode='SLAB')

                # 3. Railing Post (Deck to Rail Top)
                # Only if Railing Enabled and Not Removed
                if self.add_rail and not is_rem:
                    # FIX: Cap Overhang Issue.
                    # Stop Post at Rail Height.
                    ppos = Vector((pt.x, pt.y, h + rh/2))
                    self._make_rot_box(bm, (ps, ps, rh), ppos, ang_z, 0, 2, tag_layer)

                    # Add Cap?
                    if self.post_cap_size > 0.001:
                        cap_s = ps + (self.post_cap_size * 2)
                        cap_pos = Vector((pt.x, pt.y, h + rh + 0.02)) # Sit on top
                        self._make_rot_box(bm, (cap_s, cap_s, 0.04), cap_pos, ang_z, 0, 2, tag_layer, seam_mode='SLAB')

            # Draw Rail Segments (Tag 3)
            # Only if Railing Enabled and Not Removed
            # Use active_d (which contains ALL points including start/end)
            # NOT final_d (which has deduplication applied)
            if self.add_rail and not is_rem:
                # Between active_d points
                for k in range(len(active_d)-1):
                    d_s = active_d[k]
                    d_e = active_d[k+1]

                # Gap Check (Stairs)
                mid_d = (d_s + d_e) / 2
                if is_stair_side and stair_int:
                    if stair_int[0] <= mid_d <= stair_int[1]:
                        continue

                seg_l = d_e - d_s
                if seg_l < 0.1: continue

                seg_mid_pt = p1 + (vec.normalized() * mid_d)

                # Top Rail
                tr_pos = Vector((seg_mid_pt.x, seg_mid_pt.y, h + rh))
                self._make_rot_box(bm, (seg_l, 0.08, 0.06), tr_pos, ang_z, 0, 3, tag_layer)

                # Bottom Rail (New)
                lift = self.rail_lift
                if self.rail_bottom_b:
                    br_pos = Vector((seg_mid_pt.x, seg_mid_pt.y, h + lift + 0.1))
                    self._make_rot_box(bm, (seg_l, 0.06, 0.04), br_pos, ang_z, 0, 3, tag_layer)

                # Infill Start Height
                # Fix: Overlap to close gaps
                z_start = h + lift + 0.1 if self.rail_bottom_b else h + lift
                z_end = h + rh - 0.04 # Top Rail Bottom (approx)

                # Extend into rails
                if self.rail_bottom_b: z_start -= 0.02
                z_end += 0.02

                inf_h = z_end - z_start
                if inf_h < 0.1: inf_h = 0.1
                z_mid = (z_start + z_end) / 2

                # Infill
                if self.rail_style == 'VERTICAL':
                    p_count = int(seg_l / self.rail_density)
                    for p in range(p_count):
                        # Lerp
                        t = (p + 0.5) / p_count
                        lp = p1 + (vec.normalized() * (d_s + (t * seg_l)))
                        self._make_rot_box(bm, (0.04, 0.04, inf_h), Vector((lp.x, lp.y, z_mid)), ang_z, 0, 3, tag_layer)

                # Other styles (Horizontal/Cable) similar logic...
                elif self.rail_style == 'HORIZONTAL':
                    r_count = 3
                    step = inf_h / (r_count + 1)

                    for r in range(r_count):
                        rz = z_start + (step * (r+1))
                        self._make_rot_box(bm, (seg_l, 0.04, 0.04), Vector((seg_mid_pt.x, seg_mid_pt.y, rz)), ang_z, 0, 3, tag_layer)

                elif self.rail_style == 'CABLE':
                    # Thin wire strands
                    num_rails = max(3, int(1.0 / self.rail_density))
                    v_step = inf_h / (num_rails + 1)

                    for r in range(num_rails):
                        rz = z_start + (v_step * (r+1))
                        self._make_rot_box(bm, (seg_l, 0.01, 0.01), Vector((seg_mid_pt.x, seg_mid_pt.y, rz)), ang_z, 0, 3, tag_layer)

        # 3. CENTER STRUCTURE PRO (Under Supports)
        # Grid loop for posts and beams under the deck
        # We use post_spacing as a guide.
        # Beams run perpendicular to Joists?
        # For simplicity, Beams run Length-wise (Y for Rect) or Width-wise depending on framing.
        # Let's assume Beams run along Y (Main Girder), Joists run along X.
        # Existing Rim Joist is already perimeter.

        # Center Supports:
        # Loop X and Y.

        # Spacing
        sp = self.post_spacing

        # Grid X
        if self.width > sp:
            nx = int(self.width / sp)
            # if width=4, sp=2 -> nx=2. Points at -1, 1?
            # If even, at +/- 1.
            # Let's standardise grid.
            x_pts = []
            if nx > 0:
                step_x = self.width / (nx + 1)
                for k in range(nx):
                    x_pts.append(-(self.width/2) + step_x * (k+1))

            # Grid Y
            ny = int(self.length / sp)
            y_pts = []
            if ny > 0:
                step_y = self.length / (ny + 1)
                for k in range(ny):
                    y_pts.append(-(self.length/2) + step_y * (k+1))

            # Place Posts & Beams
            # Beams run along Y at X locations.

            for x in x_pts:
                # Beam Start/End
                # Need to intersect with Shape Y-Bounds for this X.
                y_min, y_max = self._get_y_bounds(x)

                # Inset beam from rim?
                b_y_min = y_min + 0.1
                b_y_max = y_max - 0.1
                b_len = b_y_max - b_y_min

                if b_len > 0.5:
                    # Place Beam (Tag 1)
                    # FIX: Beam Height. Rise to support deck frame.
                    # Rim Joist Center Z is h - 0.115 (Height 0.2). Top is h - 0.015.
                    # We want Beam Flush with Rim Joist.
                    b_pos = Vector((x, (b_y_min + b_y_max)/2, h - 0.115))
                    self._make_rot_box(bm, (0.1, b_len, 0.2), b_pos, 0, 0, 1, tag_layer)

                    # Place Posts along this beam
                    # Use y_pts that fall within range

                    # Also enforce start/end posts for the beam?
                    # Or just grid points.
                    active_y = [y for y in y_pts if b_y_min < y < b_y_max]

                    # Add beam ends as supports if internal grid is sparse?
                    # User said "Support posts... in center".
                    # Let's sticky to grid.

                    for y in active_y:
                        # Post (Tag 2)
                        # Ground to Beam Bottom.
                        # Beam Center Z: h - 0.115. Height 0.2.
                        # Beam Bottom Z: h - 0.215.

                        pz_top = h - 0.215
                        if pz_top > 0:
                            ppos = Vector((x, y, pz_top/2))
                            self._make_rot_box(bm, (self.post_size, self.post_size, pz_top), ppos, 0, 0, 2, tag_layer)

                            # Footing (Tag 5)
                            fpos = Vector((x, y, 0.1))
                            self._make_rot_box(bm, (self.post_size*2, self.post_size*2, 0.2), fpos, 0, 0, 5, tag_layer, seam_mode='SLAB')

                            # Bracket (Tag 6)
                            # Top of Post. Secure Beam to Post.
                            # Size slightly larger than post.
                            # Height 0.1 centered at pz_top (Beam Bottom)
                            # Actually, Bracket cups the beam.
                            # Let's put it at pz_top.
                            br_pos = Vector((x, y, pz_top))
                            br_size = (self.post_size + 0.02, self.post_size + 0.02, 0.1)
                            self._make_rot_box(bm, br_size, br_pos, 0, 0, 6, tag_layer, seam_mode='SLAB')

        # 4. ASSIGN
        for f in bm.faces:
             if f[tag_layer] in self.get_slot_meta():
                f.material_index = f[tag_layer]

        # 4. EDGE TAGS
        edge_slots = bm.edges.layers.int.get("MASSA_EDGE_SLOTS")
        if not edge_slots: edge_slots = bm.edges.layers.int.new("MASSA_EDGE_SLOTS")
        for e in bm.edges:
            if e.is_boundary: e[edge_slots] = 1
            elif e.calc_face_angle(0) > 0.5: e[edge_slots] = 2
