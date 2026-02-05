import bpy
import bmesh
import math
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from mathutils import Vector, Matrix
from ...operators.massa_base import Massa_OT_Base

CARTRIDGE_META = {"name": "Industrial Walkway", "id": "walkway", "icon": "MOD_ARRAY"}


class MASSA_OT_Walkway(Massa_OT_Base):
    """Generate Industrial Walkway Section"""

    bl_idname = "massa.gen_walkway"
    bl_label = "Massa Walkway"
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    # --- DIMS ---
    w_length: FloatProperty(name="Length (Y)", default=4.0, min=0.5, unit="LENGTH")
    w_width: FloatProperty(name="Width (X)", default=1.5, min=0.5, unit="LENGTH")
    w_thick: FloatProperty(name="Deck Thick", default=0.05, min=0.01, unit="LENGTH")
    deck_gap: FloatProperty(name="Deck Gap", default=0.02, min=0.001, unit="LENGTH")

    # --- FLOOR ---
    floor_type: EnumProperty(
        name="Floor Type",
        items=[
            ("SOLID", "Solid Plate", "Continuous sheet"),
            ("SPLIT", "Patterned/Grate", "Separated elements"),
        ],
        default="SPLIT",
    )
    floor_axis: EnumProperty(
        name="Axis",
        items=[
            ("Y", "Lengthwise (Y)", "Run along length"),
            ("X", "Widthwise (X)", "Run across width"),
        ],
        default="Y",
    )
    floor_pattern: EnumProperty(
        name="Pattern",
        items=[
            ("BARS", "Standard Bars", "Parallel lines"),
            ("GRID", "Grid Grating", "Cross-hatch"),
            ("TILES", "Floor Tiles", "Square plates"),
            ("CHEVRON", "Chevron", "Angled tread"),
        ],
        default="BARS",
    )
    floor_divs: IntProperty(name="Density", default=8, min=2)

    # --- STRUCTURE ---
    beam_width: FloatProperty(name="Beam Width", default=0.15, min=0.05)
    beam_height: FloatProperty(name="Beam Height", default=0.25, min=0.05)

    struct_density: IntProperty(
        name="Vtx Density", default=2, min=1, max=20, description="Cuts per meter"
    )

    support_type: EnumProperty(
        name="Supports",
        items=[
            ("NONE", "Floating", ""),
            ("FLOOR", "Pillars", "Legs to floor"),
            ("CEILING", "Hangers", "Rods to ceiling"),
        ],
        default="NONE",
    )
    support_h: FloatProperty(name="Supp. Height", default=2.0, min=0.1)

    hangar_style: EnumProperty(
        name="Hanger Style",
        items=[
            ("DIRECT", "Direct Rods", "Vertical rods from beams"),
            ("TRAPEZE", "Trapeze Frame", "Under-deck bar with rods"),
            ("V_SUSP", "V-Suspension", "Angled cables"),
        ],
        default="TRAPEZE",
    )

    # --- SAFETY / CAGE ---
    has_rail: BoolProperty(name="Inner Railing", default=True)
    rail_height: FloatProperty(name="Rail Height", default=1.0, unit="LENGTH")

    rail_thick: FloatProperty(name="Post Thick", default=0.04, min=0.01)
    rail_top_thick: FloatProperty(name="Top Rail Thick", default=0.05, min=0.01)

    rail_profile: EnumProperty(
        name="Profile",
        items=[("BOX", "Square", ""), ("CYL", "Cylinder", "")],
        default="BOX",
    )
    rail_cyl_res: EnumProperty(
        name="Resolution",
        items=[
            ("8", "8 Segments", ""),
            ("16", "16 Segments", ""),
            ("24", "24 Segments", ""),
            ("32", "32 Segments", ""),
        ],
        default="16",
    )

    rail_style: EnumProperty(
        name="Rail Style",
        items=[
            ("STD", "Standard", "Box rails"),
            ("WIRE", "Wire Cable", "Tension cables"),
            ("GLASS", "Modern Glass", "Glass panels"),
        ],
        default="STD",
    )

    has_cage: BoolProperty(name="Full Cage", default=False)
    cage_height: FloatProperty(name="Cage Height", default=2.4, min=1.5, unit="LENGTH")
    cage_offset: FloatProperty(name="Cage Offset", default=0.1, min=0.0)
    cage_thick: FloatProperty(name="Cage Beam Thick", default=0.08, min=0.02)

    cage_panels: BoolProperty(name="Safety Panels", default=False)
    panel_slat_count: IntProperty(name="Slat Count", default=5, min=1)
    panel_slat_height: FloatProperty(name="Slat Height", default=0.1, min=0.01)
    panel_coverage: FloatProperty(name="Coverage %", default=0.5, min=0.1, max=1.0)

    has_roof: BoolProperty(name="Roof", default=False)
    roof_pitch_rise: FloatProperty(name="Pitch Rise", default=0.6, min=0.0)
    roof_style: EnumProperty(
        name="Roof Style",
        items=[
            ("PITCHED", "A-Frame", "Standard peak"),
            ("FLAT", "Flat/Industrial", "Slight slope"),
            ("SHED", "Shed", "Single steep slope"),
        ],
        default="PITCHED",
    )

    rail_seg_len: FloatProperty(name="Post Spacing", default=1.5, min=0.5)

    def get_slot_meta(self):
        return {
            0: {"name": "Deck Surface", "uv": "BOX", "phys": "METAL_IRON"},
            1: {"name": "Main Beams", "uv": "BOX", "phys": "METAL_SS"},
            2: {"name": "Railings/Cage", "uv": "SKIP", "phys": "METAL_SS"},
            3: {"name": "Supports", "uv": "BOX", "phys": "CONSTR_CONCRETE"},
            4: {"name": "Panels/Glass", "uv": "BOX", "phys": "METAL_TITANIUM"},
        }

    def draw_shape_ui(self, layout):
        col = layout.column(align=True)
        col.label(text="Dimensions")
        col.prop(self, "w_length")
        col.prop(self, "w_width")

        col.separator()
        col.label(text="Decking")
        col.prop(self, "floor_type", text="")
        if self.floor_type == "SPLIT":
            col.prop(self, "floor_pattern", text="Pattern")
            col.prop(self, "floor_axis", text="Direction")
            col.prop(self, "floor_divs", text="Density")
        col.prop(self, "w_thick")
        col.prop(self, "deck_gap")

        col.separator()
        col.label(text="Structure")
        col.prop(self, "struct_density", text="Vtx Density")
        col.prop(self, "beam_width", text="Side Beams")
        col.prop(self, "beam_height", text="Height")
        col.prop(self, "support_type", text="")
        if self.support_type != "NONE":
            box = col.box()
            box.prop(self, "support_h", text="Height/Drop")
            if self.support_type == "CEILING":
                box.prop(self, "hangar_style", text="Style")

        col.separator()
        col.label(text="Safety & Enclosure")
        col.prop(self, "rail_seg_len")

        box = col.box()
        box.prop(self, "has_rail")
        if self.has_rail:
            r = box.row()
            r.prop(self, "rail_height", text="H")
            r.prop(self, "rail_thick", text="Post T")
            r.prop(self, "rail_top_thick", text="Rail T")
            box.prop(self, "rail_profile", text="Shape")
            if self.rail_profile == "CYL":
                box.prop(self, "rail_cyl_res", text="Segs")
            box.prop(self, "rail_style", text="Style")

        box = col.box()
        box.prop(self, "has_cage")
        if self.has_cage:
            col_c = box.column(align=True)
            col_c.prop(self, "cage_height", text="Height")
            col_c.prop(self, "cage_offset", text="Width Offset")
            col_c.prop(self, "cage_thick", text="Beam Thick")

            row = col_c.row()
            row.prop(self, "cage_panels", text="Panels")
            if self.cage_panels:
                sub = col_c.box()
                sub.prop(self, "panel_slat_count")
                sub.prop(self, "panel_slat_height")
                sub.prop(self, "panel_coverage")

            row = col_c.row()
            row.prop(self, "has_roof", text="Roof")
            if self.has_roof:
                sub = col_c.box()
                sub.prop(self, "roof_style", text="")
                sub.prop(self, "roof_pitch_rise", text="Pitch Rise")

    def build_shape(self, bm):
        def project_cyl_uvs(verts):
            uv_layer = bm.loops.layers.uv.verify()
            z_vals = [v.co.z for v in verts]
            if not z_vals:
                return
            min_z, max_z = min(z_vals), max(z_vals)
            height = max(0.001, max_z - min_z)
            center = Vector((0, 0, 0))
            for v in verts:
                center += v.co
            center /= len(verts)
            for v in verts:
                vec = v.co - center
                u = (math.atan2(vec.y, vec.x) / (2 * math.pi)) + 0.5
                v_coord = (v.co.z - min_z) / height
                for loop in v.link_loops:
                    loop[uv_layer].uv = (u * 3.0, v_coord * 3.0)

        def add_block(
            dims, loc, mat_idx, rot_x=0.0, rot_y=0.0, rot_z=0.0, apply_topo=False
        ):
            # SAFE UNPACKING: Ensure dims is always 3 floats
            dx, dy, dz = dims
            sx, sy, sz = 1, 1, 1

            if apply_topo and self.struct_density > 1:
                sx = max(1, int(dx * self.struct_density))
                sy = max(1, int(dy * self.struct_density))
                sz = max(1, int(dz * self.struct_density))

            # XY Grid
            res = bmesh.ops.create_grid(bm, x_segments=sx, y_segments=sy, size=1.0)
            verts = res["verts"]
            bmesh.ops.scale(bm, vec=Vector((dx, dy, 1.0)), verts=verts)

            # Extrude Z
            faces = list({f for v in verts for f in v.link_faces})
            ext = bmesh.ops.extrude_face_region(bm, geom=faces)
            ext_verts = [v for v in ext["geom"] if isinstance(v, bmesh.types.BMVert)]

            # Position the slab (Bottom at -dz/2, Top at +dz/2)
            bmesh.ops.translate(bm, vec=Vector((0, 0, -dz / 2)), verts=verts)
            bmesh.ops.translate(bm, vec=Vector((0, 0, dz)), verts=ext_verts)
            all_verts = verts + ext_verts

            # Z Cuts (Bisect)
            if sz > 1:
                block_geom = (
                    list({f for v in all_verts for f in v.link_faces})
                    + list({e for v in all_verts for e in v.link_edges})
                    + all_verts
                )
                step = dz / sz
                start_z = -dz / 2
                for i in range(1, sz):
                    bmesh.ops.bisect_plane(
                        bm,
                        geom=block_geom,
                        dist=0.0001,
                        plane_co=Vector((0, 0, start_z + (i * step))),
                        plane_no=Vector((0, 0, 1)),
                    )

            # Global Transform for the block
            if abs(rot_x) > 0.001:
                bmesh.ops.rotate(
                    bm,
                    verts=all_verts,
                    cent=Vector((0, 0, 0)),
                    matrix=Matrix.Rotation(rot_x, 4, "X"),
                )
            if abs(rot_y) > 0.001:
                bmesh.ops.rotate(
                    bm,
                    verts=all_verts,
                    cent=Vector((0, 0, 0)),
                    matrix=Matrix.Rotation(rot_y, 4, "Y"),
                )
            if abs(rot_z) > 0.001:
                bmesh.ops.rotate(
                    bm,
                    verts=all_verts,
                    cent=Vector((0, 0, 0)),
                    matrix=Matrix.Rotation(rot_z, 4, "Z"),
                )

            bmesh.ops.translate(bm, vec=loc, verts=all_verts)

            final_faces = list({f for v in all_verts for f in v.link_faces})
            for f in final_faces:
                f.material_index = mat_idx

        def add_cyl(
            radius, height, loc, mat_idx, rot_x=0.0, rot_y=0.0, rot_z=0.0, segs=None
        ):
            if segs is None:
                segs = int(self.rail_cyl_res)
            res = bmesh.ops.create_cone(
                bm,
                cap_ends=True,
                cap_tris=False,
                segments=segs,
                radius1=radius,
                radius2=radius,
                depth=height,
            )
            verts = res["verts"]
            if abs(rot_x) > 0.001:
                bmesh.ops.rotate(
                    bm,
                    verts=verts,
                    cent=Vector((0, 0, 0)),
                    matrix=Matrix.Rotation(rot_x, 4, "X"),
                )
            if abs(rot_y) > 0.001:
                bmesh.ops.rotate(
                    bm,
                    verts=verts,
                    cent=Vector((0, 0, 0)),
                    matrix=Matrix.Rotation(rot_y, 4, "Y"),
                )
            if abs(rot_z) > 0.001:
                bmesh.ops.rotate(
                    bm,
                    verts=verts,
                    cent=Vector((0, 0, 0)),
                    matrix=Matrix.Rotation(rot_z, 4, "Z"),
                )
            bmesh.ops.translate(bm, vec=loc, verts=verts)
            faces = list({f for v in verts for f in v.link_faces})
            for f in faces:
                f.material_index = mat_idx
            project_cyl_uvs(verts)

        def add_rail_member(thick, length, loc, mat_idx, align="Z", segs=None):
            if self.rail_profile == "BOX":
                dims = (thick, thick, length)
                if align == "Y":
                    dims = (thick, length, thick)
                elif align == "X":
                    dims = (length, thick, thick)
                add_block(dims, loc, mat_idx)
            else:
                rx, ry = 0.0, 0.0
                if align == "Y":
                    rx = math.radians(90)
                elif align == "X":
                    ry = math.radians(90)
                add_cyl(
                    radius=thick / 2,
                    height=length,
                    loc=loc,
                    mat_idx=mat_idx,
                    rot_x=rx,
                    rot_y=ry,
                    segs=segs,
                )

        # GENERATION
        beam_x_off = (self.w_width / 2) - (self.beam_width / 2)
        for s in [-1, 1]:
            add_block(
                (self.beam_width, self.w_length, self.beam_height),
                (beam_x_off * s, 0, 0),
                1,
                apply_topo=True,
            )

        deck_z = (self.beam_height / 2) - (self.w_thick / 2)
        # Fix: Inset deck by gap so it doesn't clip beams
        deck_w_fill = self.w_width - (self.beam_width * 2) - (self.deck_gap * 2)
        deck_l_fill = self.w_length - (self.deck_gap * 2)

        if self.floor_type == "SOLID":
            add_block(
                (deck_w_fill, deck_l_fill, self.w_thick),
                (0, 0, deck_z),
                0,
                apply_topo=True,
            )
        elif self.floor_type == "SPLIT":
            gap = self.deck_gap
            count = max(2, self.floor_divs)

            def gen_linear(axis_len, cross_len, axis_dir):
                plank_w = (cross_len - (gap * (count - 1))) / count
                start_cross = -(cross_len / 2) + (plank_w / 2)
                for i in range(count):
                    offset = start_cross + (i * (plank_w + gap))
                    if axis_dir == "Y":
                        add_block(
                            (plank_w, axis_len, self.w_thick),
                            (offset, 0, deck_z),
                            0,
                            apply_topo=True,
                        )
                    else:
                        add_block(
                            (axis_len, plank_w, self.w_thick),
                            (0, offset, deck_z),
                            0,
                            apply_topo=True,
                        )

            if self.floor_pattern == "BARS":
                if self.floor_axis == "Y":
                    # Lengthwise: Runs along Y. Width (X) is plank_width (cross_len).
                    # axis_len = deck_l_fill (Y dimension)
                    # cross_len = deck_w_fill (X dimension)
                    gen_linear(deck_l_fill, deck_w_fill, "Y")
                else:
                    # Widthwise: Runs along X. Width (Y) is plank_width (cross_len).
                    # axis_len = deck_w_fill (X dimension)
                    # cross_len = deck_l_fill (Y dimension)
                    gen_linear(deck_w_fill, deck_l_fill, "X")
            elif self.floor_pattern == "GRID":
                cx, cy = (
                    max(2, self.floor_divs),
                    int(deck_l_fill / (deck_w_fill / self.floor_divs)),
                )
                px = (deck_w_fill - (gap * (cx - 1))) / cx
                sx = -(deck_w_fill / 2) + (px / 2)
                for i in range(cx):
                    add_block(
                        (px, deck_l_fill, self.w_thick / 2),
                        (sx + i * (px + gap), 0, deck_z - self.w_thick / 4),
                        0,
                        apply_topo=True,
                    )
                py = (deck_l_fill - (gap * (cy - 1))) / cy
                sy = -(deck_l_fill / 2) + (py / 2)
                for i in range(cy):
                    add_block(
                        (deck_w_fill, py, self.w_thick / 2),
                        (0, sy + i * (py + gap), deck_z + self.w_thick / 4),
                        0,
                        apply_topo=True,
                    )
            elif self.floor_pattern == "TILES":
                ts = (deck_w_fill - (gap * (count - 1))) / count
                cy = max(1, int(deck_l_fill / (ts + gap)))
                sx = -(deck_w_fill / 2) + (ts / 2)
                sy = -((cy * ts + (cy - 1) * gap) / 2) + (ts / 2)
                for ix in range(count):
                    for iy in range(cy):
                        add_block(
                            (ts, ts, self.w_thick),
                            (sx + ix * (ts + gap), sy + iy * (ts + gap), deck_z),
                            0,
                            apply_topo=True,
                        )
            elif self.floor_pattern == "CHEVRON":
                cy = int(deck_l_fill / 0.2)
                sh = (deck_l_fill / cy) - 0.01
                for i in range(cy):
                    y = -(deck_l_fill / 2) + (i * 0.2) + 0.1
                    add_block(
                        (deck_w_fill / 1.5, sh, self.w_thick),
                        (-deck_w_fill / 4, y, deck_z),
                        0,
                        rot_z=math.radians(30),
                        apply_topo=True,
                    )
                    add_block(
                        (deck_w_fill / 1.5, sh, self.w_thick),
                        (deck_w_fill / 4, y, deck_z),
                        0,
                        rot_z=math.radians(-30),
                        apply_topo=True,
                    )

        if self.has_rail:
            pt, tt = self.rail_thick, self.rail_top_thick
            xb, zb = (self.w_width / 2) - (self.beam_width / 2), self.beam_height / 2
            pc = max(2, int(self.w_length / self.rail_seg_len) + 1)
            ys, ye = -(self.w_length / 2) + pt / 2, (self.w_length / 2) - pt / 2
            ystep = (ye - ys) / (pc - 1) if pc > 1 else 0
            for s in [-1, 1]:
                add_rail_member(
                    tt, self.w_length, (xb * s, 0, zb + self.rail_height), 2, align="Y"
                )
                for i in range(pc):
                    add_rail_member(
                        pt,
                        self.rail_height,
                        (xb * s, ys + i * ystep, zb + self.rail_height / 2),
                        2,
                        align="Z",
                    )
                if self.rail_style == "STD":
                    add_rail_member(
                        pt * 0.8,
                        self.w_length,
                        (xb * s, 0, zb + self.rail_height * 0.5),
                        2,
                        align="Y",
                    )
                elif self.rail_style == "WIRE":
                    wr = max(4, int(self.rail_cyl_res) // 2)
                    sp = self.rail_height / 5
                    for k in range(1, 5):
                        add_cyl(
                            0.005,
                            self.w_length,
                            (xb * s, 0, zb + k * sp),
                            2,
                            rot_x=math.radians(90),
                            segs=wr,
                        )
                elif self.rail_style == "GLASS":
                    add_block(
                        (0.02, self.w_length, self.rail_height - 0.15),
                        (xb * s, 0, zb + 0.1 + (self.rail_height - 0.15) / 2),
                        4,
                    )

        if self.has_cage:
            cp, cb = self.cage_thick, self.cage_thick * 0.8
            cx, zb = (self.w_width / 2) + self.cage_offset, self.beam_height / 2
            pc = max(2, int(self.w_length / self.rail_seg_len) + 1)
            ys, ye = -(self.w_length / 2) + cp / 2, (self.w_length / 2) - cp / 2
            ystep = (ye - ys) / (pc - 1) if pc > 1 else 0
            for s in [-1, 1]:
                sx = cx * s
                for i in range(pc):
                    y = ys + i * ystep
                    ph = (zb + self.cage_height) - (-(self.beam_height / 2) - cb)
                    add_block(
                        (cp, cp, ph),
                        (sx, y, (-(self.beam_height / 2) - cb) + ph / 2),
                        2,
                    )
                    if s == 1:
                        add_block((cx * 2, cb, cb), (0, y, zb + self.cage_height), 2)
                        add_block(
                            (cx * 2 + cp * 2, cb, cb),
                            (0, y, -(self.beam_height / 2) - cb / 2),
                            2,
                        )
                add_block((cb, self.w_length, cb), (sx, 0, zb + self.cage_height), 2)
                if self.cage_panels:
                    ph, sh = (
                        self.cage_height * self.panel_coverage,
                        self.panel_slat_height,
                    )
                    cnt = max(1, self.panel_slat_count)
                    gap = (ph - cnt * sh) / (cnt - 1) if cnt > 1 else 0
                    for k in range(cnt):
                        add_block(
                            (0.02, self.w_length, sh),
                            (sx, 0, zb + k * (sh + gap) + sh / 2),
                            4,
                        )

            if self.has_roof:
                th, wt, zs = 0.05, (cx * 2) + 0.6, zb + self.cage_height
                if self.roof_style == "FLAT":
                    add_block((wt, self.w_length, th), (0, 0, zs + th / 2), 4)
                elif self.roof_style == "SHED":
                    rise = max(0.1, self.roof_pitch_rise)
                    ang = math.atan2(rise, wt)
                    ln = (wt**2 + rise**2) ** 0.5
                    add_block(
                        (ln, self.w_length, th), (0, 0, zs + rise / 2), 4, rot_y=ang
                    )
                    wh = (zs + rise / 2 + cx * math.tan(ang)) - zs
                    if wh > 0.01:
                        for i in range(pc):
                            add_block(
                                (cp, cp, wh), (-cx, ys + i * ystep, zs + wh / 2), 2
                            )
                elif self.roof_style == "PITCHED":
                    rise = max(0.1, self.roof_pitch_rise)
                    hw = wt / 2
                    ang = math.atan2(rise, hw)
                    ln = (hw**2 + rise**2) ** 0.5
                    for s in [-1, 1]:
                        add_block(
                            (ln, self.w_length, th),
                            (hw / 2 * s, 0, zs + rise / 2),
                            4,
                            rot_y=ang * s,
                        )
                    add_block(
                        (0.15, self.w_length, 0.15),
                        (0, 0, zs + rise),
                        4,
                        rot_y=math.radians(45),
                    )

        if self.support_type != "NONE":
            th = 0.2 if self.support_type == "FLOOR" else 0.05
            ylocs = [-(self.w_length / 2) + 0.2, (self.w_length / 2) - 0.2]
            for y in ylocs:
                if self.support_type == "FLOOR":
                    add_block(
                        (self.w_width, th, th),
                        (0, y, -(self.beam_height / 2) - th / 2),
                        3,
                    )
                    for s in [-1, 1]:
                        add_block(
                            (th, th, self.support_h),
                            (
                                (self.w_width / 2 - th / 2) * s,
                                y,
                                -(self.beam_height / 2) - th - self.support_h / 2,
                            ),
                            3,
                        )
                elif self.support_type == "CEILING":
                    if self.hangar_style == "DIRECT":
                        for s in [-1, 1]:
                            add_block(
                                (0.04, 0.04, self.support_h),
                                (
                                    (self.w_width / 2 - self.beam_width / 2) * s,
                                    y,
                                    self.beam_height / 2 + self.support_h / 2,
                                ),
                                3,
                            )
                    elif self.hangar_style == "TRAPEZE":
                        bw, bz = self.w_width + 0.4, -(self.beam_height / 2) - 0.05
                        add_block((bw, 0.1, 0.05), (0, y, bz), 3)
                        rh = self.support_h + self.beam_height + 0.1
                        for s in [-1, 1]:
                            add_block(
                                (0.02, 0.02, rh),
                                ((bw / 2 - 0.05) * s, y, bz + rh / 2),
                                3,
                            )
                    elif self.hangar_style == "V_SUSP":
                        cz, sx = self.beam_height / 2 + self.support_h, self.w_width / 2
                        vec = Vector((0, 0, cz)) - Vector((sx, 0, self.beam_height / 2))
                        ang = math.atan2(sx, self.support_h)
                        for s in [-1, 1]:
                            add_block(
                                (0.02, 0.02, vec.length),
                                (
                                    sx / 2 * s,
                                    y,
                                    self.beam_height / 2 + self.support_h / 2,
                                ),
                                3,
                                rot_y=-(ang * s),
                            )

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
